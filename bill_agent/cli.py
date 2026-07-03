"""Príkazový riadok agenta: fetch / remind / run / list / paid / ignore / qr / import-bank."""

import argparse
import sys

from .config import Config
from .store import Store


def cmd_fetch(cfg: Config, store: Store, args: argparse.Namespace) -> None:
    from . import emails as email_mod
    from . import extractor

    mails = email_mod.fetch_recent(cfg)
    new = [m for m in mails if m.message_id and not store.is_processed(m.message_id)]
    print(f"Stiahnutých e-mailov: {len(mails)}, nových na spracovanie: {len(new)}")
    n_payments = n_tasks = 0
    for mail in new:
        try:
            result = extractor.extract(cfg, mail)
        except Exception as exc:
            print(f"  ⚠ {mail.subject!r}: extrakcia zlyhala ({exc})", file=sys.stderr)
            continue
        for p in result.payments:
            pid = store.add_payment(
                supplier=p.supplier, amount=p.amount, currency=p.currency,
                iban=p.iban, variable_symbol=p.variable_symbol,
                specific_symbol=p.specific_symbol, constant_symbol=p.constant_symbol,
                due_date=p.due_date or None, note=p.note,
                source_message_id=mail.message_id, source_subject=mail.subject,
            )
            n_payments += 1
            print(f"  💸 [{pid}] {p.supplier} {p.amount:.2f} {p.currency}, "
                  f"splatnosť {p.due_date or '—'} (z: {mail.subject!r})")
        for t in result.tasks:
            tid = store.add_task(
                description=t.description, due_date=t.due_date or None,
                source_message_id=mail.message_id,
            )
            n_tasks += 1
            print(f"  📋 [{tid}] {t.description} (do {t.due_date or '—'})")
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

    p_bank = sub.add_parser("import-bank", help="spáruje platby s CSV výpisom z banky")
    p_bank.add_argument("file", help="cesta k CSV výpisu")
    p_bank.add_argument("--amount-col", required=True, help="názov stĺpca so sumou")
    p_bank.add_argument("--vs-col", default="", help="názov stĺpca s variabilným symbolom")
    p_bank.add_argument("--iban-col", default="", help="názov stĺpca s IBAN protistrany")
    p_bank.add_argument("--delimiter", default="", help="oddeľovač CSV (autodetekcia)")
    p_bank.add_argument("--encoding", default="utf-8-sig", help="kódovanie súboru")

    args = parser.parse_args(argv)
    cfg = Config()
    store = Store(cfg.db_path)
    try:
        {
            "fetch": cmd_fetch,
            "remind": cmd_remind,
            "run": cmd_run,
            "list": cmd_list,
            "paid": cmd_paid,
            "ignore": cmd_ignore,
            "task-done": cmd_task_done,
            "qr": cmd_qr,
            "import-bank": cmd_import_bank,
        }[args.command](cfg, store, args)
    finally:
        store.close()
