"""Jednorazová migrácia: zašifruje heslá schránok vo všetkých accounts.ini.

Používanie (na serveri, s načítaným .env.master):
    set -a; . .env.master; set +a
    .venv/bin/python -m webapp.encrypt_existing
"""

import configparser
import os

from bill_agent import crypto

from . import clientfs


def main() -> None:
    secret = crypto.secret_from_env()
    if not secret:
        raise SystemExit("Chýba CRED_KEY/WEBAPP_SECRET v prostredí — načítajte .env.master.")
    if not os.path.isdir(clientfs.CLIENTS_DIR):
        print("Žiadny adresár clients/ — nie je čo šifrovať.")
        return
    for client in sorted(os.listdir(clientfs.CLIENTS_DIR)):
        ini = os.path.join(clientfs.CLIENTS_DIR, client, "accounts.ini")
        if not os.path.isfile(ini):
            continue
        parser = configparser.ConfigParser()
        parser.read(ini, encoding="utf-8")
        changed = 0
        for section in parser.sections():
            password = parser[section].get("password", "")
            if password and not password.startswith(crypto.PREFIX):
                parser[section]["password"] = crypto.encrypt(password, secret)
                changed += 1
        if changed:
            with open(ini, "w", encoding="utf-8") as fh:
                parser.write(fh)
            print(f"{client}: zašifrovaných hesiel: {changed}")
        else:
            print(f"{client}: nič na šifrovanie")


if __name__ == "__main__":
    main()
