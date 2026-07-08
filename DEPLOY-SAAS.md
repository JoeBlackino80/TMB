# Nasadenie SaaS (webová registrácia + Stripe)

Webová aplikácia beží nad existujúcim enginom: klient sa registruje, pridá si
schránky a nastavenia cez prehliadač; spracovanie pošty ďalej robí cron cez
`bill_agent run-all` nad adresármi `clients/`.

## 1. Inštalácia na serveri

```bash
cd /root/TMB
git pull
.venv/bin/pip install -r requirements-web.txt
```

## 2. Master konfigurácia (`/root/TMB/.env.master`)

Hodnoty zdieľané všetkými klientmi + nastavenia webu:

```bash
cat > /root/TMB/.env.master <<'EOF'
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-opus-4-8
SMTP_HOST=mail.webhouse.sk
# Hetzner blokuje odchádzajúce porty 25 a 465 — používajte 587 (STARTTLS)
SMTP_PORT=587
SMTP_USER=obchod@sorbxt.sk
SMTP_PASSWORD=...
WEBAPP_SECRET=DLHY-NAHODNY-RETAZEC-min-32-znakov
ADMIN_EMAIL=obchod@sorbxt.sk
# adresa webu — zapne jednoklikové tlačidlá (Zaplatené / Odložiť) v e-mailoch
ACTION_BASE_URL=https://voru.sk
STRIPE_LINK_MONTHLY=
STRIPE_LINK_YEARLY=
STRIPE_WEBHOOK_SECRET=
EOF
chmod 600 /root/TMB/.env.master
```

`WEBAPP_SECRET` vygenerujte: `openssl rand -hex 32`.

## 3. Systemd služba webu

```bash
cat > /etc/systemd/system/platby-web.service <<'EOF'
[Unit]
Description=VORU web
After=network.target

[Service]
WorkingDirectory=/root/TMB
EnvironmentFile=/root/TMB/.env.master
ExecStart=/root/TMB/.venv/bin/uvicorn webapp.app:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl enable --now platby-web
```

## 4. Doména + HTTPS (Caddy)

Nasmerujte A záznam domény (produkčne `voru.sk`) na IP servera.
Caddy vybaví HTTPS certifikát sám:

```bash
apt install -y caddy
cat > /etc/caddy/Caddyfile <<'EOF'
voru.sk, www.voru.sk, platby.voru.sk {
    reverse_proxy 127.0.0.1:8000
}
EOF
systemctl restart caddy
```

> Kým doménu nemáte, na testovanie poslúži `http://IP-SERVERA:8000`
> (spustite uvicorn s `--host 0.0.0.0`) — ale heslá cez holé HTTP neposielajte
> reálnym klientom; produkčne vždy len s HTTPS.

## 5. Stripe (4,99 €/mes., 49 €/rok)

1. Účet na [stripe.com](https://stripe.com) → aktivujte firmu (SORB XT s.r.o.)
2. **Products** → New: „VORU" — cena 4,99 €/mesiac (recurring)
   a druhá cena 49 €/rok
3. **Payment Links** → vytvorte link pre mesačnú aj ročnú cenu
   → URL vložte do `.env.master` (`STRIPE_LINK_MONTHLY/ YEARLY`)
4. **Developers → Webhooks** → Add endpoint:
   `https://voru.sk/stripe/webhook`, events:
   `checkout.session.completed`, `customer.subscription.deleted`
   → „Signing secret" (whsec_...) do `STRIPE_WEBHOOK_SECRET`
5. `systemctl restart platby-web`

Po zaplatení Stripe zavolá webhook a účet klienta sa aktivuje automaticky.
Kým webhook nie je nastavený, klientov aktivujete ručne na `/admin`.

## 6. Cron

Kompletný odporúčaný crontab je v `crontab.example` — ranný beh, kontrola
odpovedí každých 30 minút, zhrnutia, vypínanie vypršaných trialov a denná
záloha. (`run-all` automaticky preskakuje klientov so súborom DISABLED.)

## 6b. Šifrovanie hesiel schránok

Nové heslá schránok sa ukladajú šifrovane automaticky (kľúč = WEBAPP_SECRET,
prípadne samostatný CRED_KEY v `.env.master`). Existujúce nešifrované heslá
zašifrujete jednorazovo:

```bash
cd /root/TMB
set -a; . .env.master; set +a
.venv/bin/python -m webapp.encrypt_existing
```

POZOR: po zašifrovaní si WEBAPP_SECRET/CRED_KEY bezpečne odložte — bez neho
sa heslá schránok nedajú prečítať a klienti by ich museli zadať znova.

## 6c. Preposielacia adresa (voliteľné, odporúčané)

Klienti nemusia zadávať heslo k schránke — môžu faktúry preposielať na svoju
unikátnu adresu (napr. `prijem+a1b2c3d4@voru.sk`).

1. Vo Webhouse vytvorte schránku `prijem@voru.sk` a zapnite pre ňu
   **catch-all / plusové aliasy** (doručovanie `prijem+cokolvek@` do tej istej
   schránky — väčšina hostingov to robí automaticky).
2. Do `.env.master` doplňte:
   ```
   FORWARD_IMAP_HOST=mail.webhouse.sk
   FORWARD_IMAP_PORT=993
   FORWARD_IMAP_USER=prijem@voru.sk
   FORWARD_IMAP_PASSWORD=...
   FORWARD_ADDRESS=prijem+{token}@voru.sk
   ```
3. `systemctl restart platby-web` — klientom sa na stránke Schránky zobrazí
   ich adresa. Cron `bill_agent intake` (v crontab.example) správy roztriedi.

## 6d. Zálohy

`scripts/backup.sh` denne balí `clients/`, `webapp.db` a `.env.master` do
`/root/backups` (drží 14 dní). Odporúčame obsah `/root/backups` synchronizovať
aj mimo servera (Hetzner Storage Box, rsync).

## 6e. Doručiteľnosť pošty (SPF, DKIM, DMARC) — POVINNÉ

Celá služba stojí na e-mailoch — bez týchto DNS záznamov skončia pripomienky
v spame. Nastavte pre doménu, z ktorej odchádza pošta (SMTP_USER):

1. **SPF** — TXT záznam na doméne (hodnotu podľa poskytovateľa SMTP;
   pre Webhouse/Websupport ju nájdete v ich dokumentácii):
   ```
   v=spf1 include:_spf.webhouse.sk ~all
   ```
2. **DKIM** — zapnite podpisovanie v administrácii poštového hostingu
   a pridajte ich DKIM TXT záznam (selektor._domainkey.domena).
3. **DMARC** — TXT záznam `_dmarc.domena`:
   ```
   v=DMARC1; p=quarantine; rua=mailto:obchod@sorbxt.sk
   ```
4. Overenie: pošlite si pripomienku na Gmail → „Zobraziť originál“ —
   SPF, DKIM aj DMARC musia byť `PASS`. Alebo použite mail-tester.com.

Aplikácia pridáva hlavičku `List-Unsubscribe` automaticky (Gmail ju od
pravidelných odosielateľov vyžaduje).

## 6f. Monitoring

- **Uptime**: aplikácia má endpoint `GET /healthz` (vracia `ok`).
  Na [uptimerobot.com](https://uptimerobot.com) (zadarmo) pridajte HTTP
  monitor na `https://voru.sk/healthz` s upozornením na váš e-mail/telefón.
- **Chyby behu**: cron alertuje admina e-mailom (`_alert_admin` v CLI).
  Voliteľne pridajte [Sentry](https://sentry.io) (free tier):
  `pip install sentry-sdk` a v `.env.master` `SENTRY_DSN=...`, potom
  v `webapp/app.py` na začiatok `import sentry_sdk; sentry_sdk.init(...)`.
- **Zálohy mimo servera**: obsah `/root/backups` denne synchronizujte na
  Hetzner Storage Box: `rsync -a /root/backups/ u123456@u123456.your-storagebox.de:voru/`
  (pridajte do crontabu). Záloha na tom istom disku nie je záloha.

## 7. Ekonomika a povinnosti

- náklady: server ~4 €/mes. + Claude API ~1–3 €/klient/mes. → pri 4,99 €
  je marža tesná, pri 49 €/rok počítajte s AI nákladmi ~20–30 €/rok/klient
  pri väčšom objeme pošty — sledujte spotrebu v Anthropic konzole
- **fakturácia predplatného**: Stripe peniaze vyberie, ale faktúru klientovi
  musí vystaviť SORB XT s.r.o. Najjednoduchšie: v Stripe zapnite
  **Invoicing** (automatická faktúra po platbe) + **Stripe Tax** (správna
  DPH podľa krajiny). Alternatíva pre SK účtovníctvo: SuperFaktúra API.
- **DPH / OSS**: predaj digitálnej služby spotrebiteľom do iných štátov EÚ
  (CZ, PL, AT, HU) sa zdaňuje v krajine zákazníka → registrácia do
  **One Stop Shop** na www.financnasprava.sk (jedno štvrťročné priznanie
  za všetky štáty). B2B klientom s IČ DPH fakturujete s prenesenou
  daňovou povinnosťou.
- GDPR: spracúvate poštu klientov → DPA je súčasťou podmienok (stránka
  `/dpa` v aplikácii, súhlas sa udeľuje pri registrácii); klient má
  samoobslužný export dát (`/export`) aj zmazanie účtu (Nastavenia)
- heslá schránok klientov sú uložené na serveri v `clients/*/accounts.ini` —
  server držte aktualizovaný, prístup len cez SSH kľúč, zvážte disk encryption
- odporúčajte klientom **aplikačné heslá** (Gmail App Password a pod.),
  nie hlavné heslá
