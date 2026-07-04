"""Príkazový riadok agenta: fetch / remind / run / digest / list / ... / run-all."""

import argparse
import os
import subprocess
import sys

from .config import Config
from .store import Store


def cmd_fetch(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    from . import commands
    from . import emails as email_mod
    from . import extractor

    accounts = cfg.accounts()
    own_addresses = [a.user.lower() for a in accounts] + [cfg.reminder_to.lower()]

    n_payments = n_tasks = 0
    for account in accounts:
        try:
            mails = email_mod.fetch_recent(account, cfg.email_lookback_days)
        except Exception as exc:
            print(f"⚠ Schránka {account.name}: pripojenie zlyhalo ({exc})", file=sys.stderr)
            continue
        new = [m for m in mails if m.message_id and not store.is_processed(m.message_id)]
        print(f"📬 {account.name}: {len(mails)} e-mailov, nových na spracovanie: {len(new)}")
        for mail in new:
            # odpoveď na pripomienku ("zaplatené 3") — vybavíme bez AI
            if commands.is_command_email(mail, own_addresses):
                for action in commands.apply(store, mail):
                    print(f"  ✉️ {action}")
                store.mark_processed(mail.message_id)
                continue
            # e-mail už v minulosti niečo vytvoril → nespracúvame druhýkrát
            if store.has_records_from(mail.message_id):
                store.mark_processed(mail.message_id)
                continue
            try:
                result = extractor.extract(cfg, mail)
            except Exception as exc:
                print(f"  ⚠ {mail.subject!r}: extrakcia zlyhala ({exc})", file=sys.stderr)
                continue
            for p in result.payments:
                # ochrana pred podvodom: iný IBAN než pri minulých faktúrach
                # toho istého dodávateľa
                note = p.note
                if p.iban:
                    known = store.known_ibans_for_supplier(p.supplier)
                    if known and p.iban not in known:
                        warning = ("⚠️ POZOR: iný IBAN než pri predchádzajúcich "
                                   "platbách tomuto dodávateľovi — overte pravosť faktúry!")
                        note = f"{warning} {note}".strip()
                        print(f"  ⚠️ {p.supplier}: IBAN sa líši od minulých faktúr "
                              f"({p.iban} vs {', '.join(sorted(known))})")
                pid = store.add_payment(
                    supplier=p.supplier, amount=p.amount, currency=p.currency,
                    iban=p.iban, variable_symbol=p.variable_symbol,
                    specific_symbol=p.specific_symbol, constant_symbol=p.constant_symbol,
                    due_date=p.due_date or None, note=note,
                    source_message_id=mail.message_id, source_subject=mail.subject,
                    source_account=account.name,
                )
                n_payments += 1
                print(f"  💸 [{pid}] {p.supplier} {p.amount:.2f} {p.currency}, "
                      f"splatnosť {p.due_date or '—'} (z: {mail.subject!r})")
            for t in result.tasks:
                tid = store.add_task(
                    description=t.description, due_date=t.due_date or None,
                    source_message_id=mail.message_id, source_account=account.name,
                )
                n_tasks += 1
                print(f"  📋 [{tid}] {t.description} (do {t.due_date or '—'})")
            store.log_email(
                message_id=mail.message_id, account=account.name,
                sender=mail.sender, subject=mail.subject,
                summary=result.summary, category=result.category,
            )
            # z výpisov a potvrdení o platbe automaticky odškrtávame zaplatené
            for tr in result.paid_transactions:
                match = store.match_bank_transaction(
                    amount=tr.amount, variable_symbol=tr.variable_symbol,
                    iban=tr.counterparty_iban,
                )
                if match:
                    store.set_payment_status(match.id, "paid")
                    print(f"  ✅ [{match.id}] {match.supplier} {match.amount:.2f} "
                          f"{match.currency} — nájdené vo výpise, označené ako zaplatené")
            store.mark_processed(mail.message_id)
    print(f"Hotovo: {n_payments} platieb, {n_tasks} úloh.")


def cmd_remind(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    from . import reminder

    if getattr(args, "dry_run", False):
        built = reminder.build_reminder(store, cfg.reminder_days_ahead)
        if built is None:
            print("Nie je čo pripomenúť.")
        else:
            print(built[0])
        return
    sent = reminder.send_reminder(cfg, store)
    print(f"Upozornenie odoslané na {cfg.reminder_to}." if sent else "Nie je čo pripomenúť.")


def cmd_run(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    cmd_fetch(cfg, store, args)
    cmd_remind(cfg, store, args)


def cmd_digest(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    from . import digest

    if getattr(args, "dry_run", False):
        built = digest.build_digest(cfg, store, args.days)
        print(built[1] if built else "Nie je čo zhrnúť.")
        return
    sent = digest.send_digest(cfg, store, args.days)
    print(f"Zhrnutie odoslané na {cfg.reminder_to}." if sent else "Nie je čo zhrnúť.")


def cmd_run_all(args: argparse.Namespace) -> None:
    """Spustí príkaz pre každého klienta v adresári clients/ (mini-SaaS režim).

    Každý klient = podadresár s vlastným .env, accounts.ini a databázou.
    Beží v samostatnom procese s cwd v adresári klienta, takže konfigurácie
    aj dáta sú úplne oddelené. Pád jedného klienta nezastaví ostatných.
    """
    base = args.clients_dir
    if not os.path.isdir(base):
        raise SystemExit(
            f"Adresár {base!r} neexistuje. Vytvorte clients/<meno-klienta>/ "
            "s .env a accounts.ini (pozri README)."
        )
    client_dirs = sorted(
        d for d in os.listdir(base)
        if os.path.isfile(os.path.join(base, d, ".env"))
    )
    if not client_dirs:
        raise SystemExit(f"V {base!r} nie je žiadny klient (podadresár s .env).")

    command = [sys.executable, "-m", "bill_agent", args.subcommand]
    if args.subcommand == "digest":
        command += ["--days", str(args.days)]

    failed = []
    for name in client_dirs:
        print(f"\n=== 👤 {name} ===")
        result = subprocess.run(command, cwd=os.path.join(base, name))
        if result.returncode != 0:
            failed.append(name)
    if failed:
        print(f"\n⚠ Zlyhali klienti: {', '.join(failed)}", file=sys.stderr)
        raise SystemExit(1)


def cmd_list(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    payments = store.pending_payments()
    print(f"Nezaplatené platby ({len(payments)}):")
    for p in payments:
        print(f"  [{p.id}] {p.supplier or '(neznámy)'} — {p.amount:.2f} {p.currency}, "
              f"splatnosť {p.due_date or '—'}, IBAN {p.iban or '—'}, "
              f"VS {p.variable_symbol or '—'}")
    tasks = store.pending_tasks()
    print(f"Úlohy ({len(tasks)}):")
    for t in tasks:
        print(f"  [{t.id}] {t.description}" + (f" (do {t.due_date})" if t.due_date else ""))


def cmd_paid(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    if store.set_payment_status(args.id, "paid"):
        print(f"Platba {args.id} označená ako zaplatená.")
    else:
        raise SystemExit(f"Platba {args.id} neexistuje.")


def cmd_ignore(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    if store.set_payment_status(args.id, "ignored"):
        print(f"Platba {args.id} ignorovaná.")
    else:
        raise SystemExit(f"Platba {args.id} neexistuje.")


def cmd_task_done(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    if store.set_task_status(args.id, "done"):
        print(f"Úloha {args.id} hotová.")
    else:
        raise SystemExit(f"Úloha {args.id} neexistuje.")


def cmd_qr(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    from datetime import date

    from . import pay_by_square

    p = store.get_payment(args.id)
    if not p:
        raise SystemExit(f"Platba {args.id} neexistuje.")
    if not p.iban:
        raise SystemExit(f"Platba {args.id} nemá IBAN — QR kód nejde vygenerovať.")
    due = None
    if p.due_date:
        try:
            due = date.fromisoformat(p.due_date)
        except ValueError:
            pass
    code = pay_by_square.generate_code(
        amount=p.amount, iban=p.iban, currency=p.currency, due_date=due,
        variable_symbol=p.variable_symbol, constant_symbol=p.constant_symbol,
        specific_symbol=p.specific_symbol, note=(p.note or p.supplier)[:60],
        beneficiary_name=p.supplier[:70],
    )
    path = args.output or f"payment-{p.id}.png"
    with open(path, "wb") as fh:
        fh.write(pay_by_square.qr_png(code))
    print(f"QR kód uložený do {path}")


def cmd_import_bank(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    from . import bank

    result = bank.import_csv(
        store, args.file,
        amount_col=args.amount_col, vs_col=args.vs_col, iban_col=args.iban_col,
        delimiter=args.delimiter, encoding=args.encoding,
    )
    print(f"Spracovaných riadkov: {result.total_rows}")
    for pid, desc in result.matched:
        print(f"  ✅ platba [{pid}] spárovaná a označená ako zaplatená ({desc})")
    if not result.matched:
        print("  Žiadna transakcia sa nespárovala s evidovanými platbami.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="bill_agent",
        description="AI agent na pripomínanie platieb a úloh z prijatých e-mailov.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="stiahne a spracuje nové e-maily")

    p_remind = sub.add_parser("remind", help="pošle e-mail s prehľadom platieb a úloh")
    p_remind.add_argument("--dry-run", action="store_true", help="len vypíše, neposiela")

    p_run = sub.add_parser("run", help="fetch + remind")
    p_run.add_argument("--dry-run", action="store_true", help="pripomienku len vypíše")

    p_digest = sub.add_parser("digest", help="pošle zhrnutie prijatej pošty (deň/týždeň)")
    p_digest.add_argument("--days", type=int, default=1, help="obdobie v dňoch (1 = deň, 7 = týždeň)")
    p_digest.add_argument("--dry-run", action="store_true", help="len vypíše, neposiela")

    sub.add_parser("list", help="prehľad nezaplatených platieb a úloh")

    p_paid = sub.add_parser("paid", help="označí platbu ako zaplatenú")
    p_paid.add_argument("id", type=int)

    p_ignore = sub.add_parser("ignore", help="označí platbu ako ignorovanú")
    p_ignore.add_argument("id", type=int)

    p_task = sub.add_parser("task-done", help="označí úlohu ako hotovú")
    p_task.add_argument("id", type=int)

    p_qr = sub.add_parser("qr", help="uloží PAY by square QR kód platby do PNG")
    p_qr.add_argument("id", type=int)
    p_qr.add_argument("-o", "--output", default="", help="cesta k PNG súboru")

    p_all = sub.add_parser("run-all", help="spustí príkaz pre všetkých klientov v clients/")
    p_all.add_argument("subcommand", nargs="?", default="run",
                       choices=["run", "fetch", "remind", "digest", "list"],
                       help="čo spustiť pre každého klienta (predvolene run)")
    p_all.add_argument("--days", type=int, default=1, help="obdobie pre digest")
    p_all.add_argument("--clients-dir", default="clients", help="adresár s klientmi")

    p_bank = sub.add_parser("import-bank", help="spáruje platby s CSV výpisom z banky")
    p_bank.add_argument("file", help="cesta k CSV výpisu")
    p_bank.add_argument("--amount-col", required=True, help="názov stĺpca so sumou")
    p_bank.add_argument("--vs-col", default="", help="názov stĺpca s variabilným symbolom")
    p_bank.add_argument("--iban-col", default="", help="názov stĺpca s IBAN protistrany")
    p_bank.add_argument("--delimiter", default="", help="oddeľovač CSV (autodetekcia)")
    p_bank.add_argument("--encoding", default="utf-8-sig", help="kódovanie súboru")

    args = parser.parse_args(argv)

    # run-all si spúšťa podprocesy s vlastnými konfiguráciami — bez cfg/store
    if args.command == "run-all":
        cmd_run_all(args)
        return

    cfg = Config()
    store = Store(cfg.db_path)
    try:
        {
            "fetch": cmd_fetch,
            "remind": cmd_remind,
            "run": cmd_run,
            "digest": cmd_digest,
            "list": cmd_list,
            "paid": cmd_paid,
            "ignore": cmd_ignore,
            "task-done": cmd_task_done,
            "qr": cmd_qr,
            "import-bank": cmd_import_bank,
        }[args.command](cfg, store, args)
    finally:
        store.close()
