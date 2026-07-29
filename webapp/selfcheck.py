"""Sebakontrola servera — beží z cronu, upozorní správcu, keď niečo nefunguje.

Kontroluje tri veci:
  1. beží web (HTTP GET na /healthz na localhoste),
  2. cron spracovania je čerstvý (agent.log sa nedávno menil),
  3. zostáva rozumné miesto na disku.

Keď nájde problém, pošle správcovi (ADMIN_EMAIL) jeden e-mail so zoznamom
problémov. Best-effort — keď SMTP nie je nastavené, len vypíše na výstup a
skončí nenulovým kódom (aby to prípadne zachytil aj `cron` mail alebo iný
monitoring). Sám seba nemonitoruje: toto je zámerne malý, samostatný skript
bez závislostí na zvyšku aplikácie, aby fungoval aj keď web spadne.

Použitie (cron, napr. každých 15 min):
    */15 * * * * cd /root/TMB && python -m webapp.selfcheck >> selfcheck.log 2>&1
"""

import os
import smtplib
import sys
import time
import urllib.request
from email.message import EmailMessage


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_master_env() -> None:
    """Doplní do prostredia hodnoty z .env.master (cron ich inak nemá)."""
    path = os.path.join(_repo_root(), ".env.master")
    if not os.path.isfile(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def check_web(url: str) -> str | None:
    """Vráti text problému alebo None, keď web odpovedá."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            body = resp.read(64).decode("utf-8", "replace").strip()
            if resp.status != 200:
                return f"Web odpovedal HTTP {resp.status} na {url}."
            if "ok" not in body.lower():
                return f"Web na {url} neodpovedal 'ok' (dostal: {body!r})."
    except Exception as exc:
        return f"Web nedostupný na {url}: {exc}."
    return None


def check_cron(max_age_hours: float) -> str | None:
    """Skontroluje, či sa agent.log nedávno menil (t. j. cron beží)."""
    log_path = os.path.join(_repo_root(), "agent.log")
    try:
        age_h = (time.time() - os.stat(log_path).st_mtime) / 3600
    except OSError:
        return ("agent.log neexistuje — cron spracovania klientov zrejme ešte "
                "nebežal (skontrolujte crontab).")
    if age_h > max_age_hours:
        return (f"agent.log sa nemenil {age_h:.0f} h (limit {max_age_hours:.0f} h) "
                "— cron spracovania klientov možno nebeží.")
    return None


def check_disk(min_free_gb: float) -> str | None:
    import shutil

    try:
        free_gb = shutil.disk_usage(_repo_root()).free / 1e9
    except OSError:
        return None
    if free_gb < min_free_gb:
        return f"Málo miesta na disku: zostáva {free_gb:.1f} GB (limit {min_free_gb:.0f} GB)."
    return None


def _notify_admin(problems: list[str]) -> bool:
    admin = os.environ.get("ADMIN_EMAIL", "")
    host = os.environ.get("SMTP_HOST", "")
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    if not (admin and host and user and password):
        return False
    sender = os.environ.get("SMTP_FROM", "") or user
    msg = EmailMessage()
    msg["Subject"] = f"VORU: sebakontrola našla {len(problems)} problém(ov)"
    msg["From"] = f"VORU monitor <{sender}>"
    msg["To"] = admin
    msg.set_content(
        "Sebakontrola servera VORU zistila tieto problémy:\n\n"
        + "\n".join(f"  • {p}" for p in problems)
        + "\n\nSkontrolujte prosím server (systemctl status platby-web, "
        "crontab -l, agent.log).\n"
    )
    try:
        port = int(os.environ.get("SMTP_PORT", "587") or 587)
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            server.starttls()
        try:
            server.login(user, password)
            server.send_message(msg)
        finally:
            server.quit()
        return True
    except Exception as exc:
        print(f"⚠ Upozornenie správcovi sa nepodarilo odoslať: {exc}", file=sys.stderr)
        return False


def run() -> list[str]:
    _load_master_env()
    url = os.environ.get("SELFCHECK_URL", "http://127.0.0.1:8000/healthz")
    max_age = float(os.environ.get("SELFCHECK_MAX_AGE_HOURS", "26") or 26)
    min_free = float(os.environ.get("SELFCHECK_MIN_FREE_GB", "1") or 1)

    problems = [p for p in (
        check_web(url),
        check_cron(max_age),
        check_disk(min_free),
    ) if p]
    return problems


def main() -> int:
    from datetime import datetime

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    problems = run()
    if not problems:
        print(f"[{stamp}] OK — web beží, cron je čerstvý, disk má miesto.")
        return 0
    for p in problems:
        print(f"[{stamp}] PROBLÉM: {p}")
    if _notify_admin(problems):
        print(f"[{stamp}] Upozornenie odoslané správcovi.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
