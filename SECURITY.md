# Bezpečnosť VORU

Zhrnutie penetračného auditu a bezpečnostných opatrení. Audit prebehol na
celej webovej vrstve (FastAPI) aj engine (spracovanie pošty, šifrovanie,
závislosti). Cez web sa nepodarilo reálne preniknúť — nižšie sú potvrdené
ochrany a spevnenia doplnené auditom.

## Potvrdené ochrany (bez nálezu)

- **SQL injection** — všetky dopyty parametrizované (`?`); f-stringy v SQL len
  s internými konštantami, nie so vstupom používateľa.
- **Path traversal** — `client_dir` je serverom generovaný slug (`[a-z0-9-]`);
  `/a` a `/calendar/{c}` navyše vyžadujú HMAC podpis nad `c`.
- **IDOR** — `/qr`, `/bundle`, `/export`, `/sepa`, `/payments/*` pracujú výhradne
  s databázou prihláseného používateľa; admin trasy sú za `_is_admin`.
- **XSS** — Jinja2 autoescaping; `|safe`/`|tojson` len na statických
  prekladových reťazcoch; systémové e-maily cez `html.escape`.
- **Command injection** — `subprocess.Popen([...])` bez shellu, pevné argumenty.
- **Stripe webhook** — HMAC + replay ochrana (±600 s), `compare_digest`.
- **Heslá** — PBKDF2-SHA256, 200 000 iterácií, náhodná soľ; TOTP s oknom ±1.

## Doplnené spevnenia (implementované)

| Oblasť | Opatrenie |
|--------|-----------|
| Konfigurácia | Fail-fast pri štarte, ak `WEBAPP_SECRET` < 16 znakov |
| Session | Cookie viazaná na heslo (reset/zmena zneplatní relácie) + `Secure` |
| SSRF | Pridanie schránky blokuje privátne/loopback/link-local hosty |
| Rate-limit | `X-Forwarded-For` — posledná (proxy) hodnota; login limit aj podľa IP |
| E-mail príkazy | Odmietnutie pri DKIM/SPF/DMARC = fail |
| Tajomstvá | API kľúč a SMTP heslo sa nekopírujú do klientskych `.env` |
| DoS | IMAP timeout 30 s; ošetrený nenumerický Stripe timestamp |
| Hlavičky | CSP, HSTS, X-Frame-Options DENY, X-Content-Type-Options, Referrer-Policy |
| Závislosti | Pillow ≥ 10.3, pypdf ≥ 4.2, cryptography ≥ 42.0.4, jinja2 ≥ 3.1.5 |

## Prevádzkové pravidlá (dôležité)

- **`WEBAPP_SECRET` NIKDY nerotovať** — okrem session a tokenov ním engine
  odvodzuje kľúč na šifrovanie hesiel schránok (`bill_agent/crypto.py`). Rotácia
  by znefunkčnila dešifrovanie uložených hesiel. Musí mať vysokú entropiu
  (≥ 32 náhodných znakov).
- **Rotovať po expozícii**: `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_SECRET`,
  `TURNSTILE_SECRET`, `SMTP_PASSWORD`, `STRIPE_WEBHOOK_SECRET` — tieto rotovať
  bezpečne možno (nešifrujú dáta na disku).
- **DKIM** — dokončiť u Webhouse; SPF a DMARC sú nastavené.
- **Zálohy** — `/root/backups` synchronizovať mimo server (obsahujú `.env.master`
  a databázu — chrániť prístup).

## Známe zvyškové položky (nižšia priorita, vedomé rozhodnutia)

- **Odvodenie šifrovacieho kľúča** (`crypto.py`) je jednorazové SHA-256 bez soli.
  Fernet samotný (AES-128-CBC + HMAC) je v poriadku; slabinou je len KDF.
  Prechod na PBKDF2/scrypt by vyžadoval migráciu už zašifrovaných hesiel —
  neurobené zámerne, aby sa nezneplatnili existujúce údaje. Riziko je nízke,
  kým má `WEBAPP_SECRET` vysokú entropiu.
- **`PDF_PASSWORDS`** (napr. rodné číslo) sú v klientskom `.env` v plaintexte —
  používajú sa len lokálne na odomknutie výpisov. Kandidát na šifrovanie.
- **Reset token** je v 2-hodinovom okne opakovane použiteľný (nie jednorazový);
  zmena hesla však reláciu zneplatní.
- **Registrácia** prezradí existenciu účtu (`err_exists`) — vedomý UX kompromis;
  login aj `/forgot` sú neutrálne.
- **Prompt injection z obsahu faktúry** — čiastočne krytá detekciou zmeny IBAN
  oproti známym dodávateľom; pri prvom výskyte dodávateľa IBAN vždy overte.

## Rozsah testov

`tests/test_security_hardening.py` pokrýva: revokáciu relácie pri zmene hesla,
odmietnutie sfalšovanej cookie, Secure/HttpOnly príznaky, SSRF blokovanie,
`X-Forwarded-For`, neprítomnosť tajomstiev v klientskych `.env`, bezpečnostné
hlavičky, anti-spoofing e-mailových príkazov a ošetrenie Stripe timestamp.
