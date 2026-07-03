# TMB — AI agent na pripomínanie platieb a úloh

Agent, ktorý za vás sleduje prijaté e-maily (faktúry, upomienky, výzvy na platbu — aj v PDF
prílohách), pomocou Claude AI z nich vytiahne platobné údaje a pošle vám prehľadné
upozornenie: **čo zaplatiť, komu, koľko a dokedy** — vrátane **PAY by square QR kódu**,
ktorý naskenujete v mobilnej bankovej appke a platbu len potvrdíte.

Okrem platieb si všíma aj úlohy a termíny spomenuté v e-mailoch a pripomenie ich.

## Čo agent robí

1. **`fetch`** — stiahne nové e-maily cez IMAP (Gmail, Websupport, čokoľvek s IMAP),
   vrátane PDF príloh. Claude z každého e-mailu extrahuje:
   - platby: dodávateľ, suma, mena, IBAN, variabilný / špecifický / konštantný symbol, splatnosť
   - úlohy: čo treba urobiť a dokedy
2. **`remind`** — pošle vám e-mail so zoznamom platieb **po splatnosti**, **splatných dnes**
   a **splatných v najbližších dňoch** + nadchádzajúce úlohy. Ku každej platbe je priložený
   PAY by square QR kód — naskenujete a zaplatíte.
3. **Ovládanie odpoveďou na e-mail** — na pripomienku stačí odpovedať `zaplatené 3`,
   `zaplatené všetko`, `ignoruj 5` alebo `hotovo 2` a agent si to pri ďalšej kontrole
   pošty odškrtne sám. Príkazy prijíma len z vlastných adries (schránky v accounts.ini
   a REMINDER_TO); citovaný text pôvodnej správy sa ignoruje.
4. **`import-bank`** — načíta výpis z banky (CSV) a automaticky spáruje zaplatené platby
   podľa variabilného symbolu a sumy → označí ich ako zaplatené, takže vám ich už nepripomína.
5. **`run`** — `fetch` + `remind` v jednom (ideálne do cronu).

Ďalšie príkazy: `list` (prehľad platieb a úloh), `paid <id>` / `ignore <id>` (ručné označenie),
`qr <id>` (uloží QR kód platby do PNG).

## Inštalácia

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# vyplňte .env (IMAP, SMTP, ANTHROPIC_API_KEY)
```

## Viac schránok naraz (Gmail, Webhouse, Websupport, Proton, firemné…)

Agent funguje s **ľubovoľným poskytovateľom s IMAP** a vie sledovať **viac schránok
súčasne** — napr. viacero firiem, každá s vlastnou doménou. Stačí vytvoriť
`accounts.ini` (pozri `accounts.ini.example`); jedna sekcia = jedna schránka:

```ini
[firma-gmail]
host = imap.gmail.com
user = obchod@firma.sk
password = heslo-aplikacie

[firma-webhouse]
host = imap.webhouse.sk
user = info@mojadomena.sk
password = tajneheslo

[proton]
host = 127.0.0.1
port = 1143
user = jan@proton.me
password = heslo-z-bridge
security = starttls
```

Pri `fetch` agent prejde všetky schránky a všetko eviduje v jednej databáze
(pri každej platbe si pamätá, z ktorej schránky prišla). Ak `accounts.ini`
neexistuje, použije sa jedna schránka z `IMAP_*` premenných v `.env`.

Nastavenia bežných poskytovateľov:

| Poskytovateľ | host | port | poznámka |
|---|---|---|---|
| Gmail / Google Workspace | `imap.gmail.com` | 993 | treba **App Password** (Google účet → Zabezpečenie → Heslá aplikácií) |
| Webhouse.sk | `imap.webhouse.sk` | 993 | bežné heslo schránky |
| Websupport.sk | `imap.websupport.sk` | 993 | bežné heslo schránky |
| Proton Mail | `127.0.0.1` | 1143 | cez lokálny **Proton Mail Bridge** (platený plán), `security = starttls`, heslo vygeneruje Bridge |
| Outlook / M365 | `outlook.office365.com` | 993 | app password / povolený IMAP |
| iný firemný server | podľa poskytovateľa | 993 | `security = ssl` (predvolené) |

> Proton Mail nemá priamy IMAP — Bridge je oficiálna aplikácia od Protonu,
> ktorá beží na vašom počítači/serveri a sprístupní schránku cez lokálny IMAP.

## Použitie

```bash
python -m bill_agent fetch        # stiahne a spracuje nové e-maily
python -m bill_agent remind       # pošle upozornenie s QR kódmi
python -m bill_agent run          # oboje naraz
python -m bill_agent list         # prehľad evidovaných platieb a úloh
python -m bill_agent paid 3       # označí platbu č. 3 ako zaplatenú
python -m bill_agent qr 3         # uloží QR kód platby č. 3 do payment-3.png
python -m bill_agent import-bank vypis.csv --vs-col VS --amount-col Suma
```

## Automatické spúšťanie (cron)

Každý pracovný deň o 7:30 skontroluje poštu a pošle upozornenie
(e-mail príde len ak je čo pripomenúť):

```cron
30 7 * * 1-5  cd /cesta/k/TMB && .venv/bin/python -m bill_agent run >> agent.log 2>&1
```

Pozri `crontab.example`.

## Konfigurácia (.env)

| Premenná | Význam |
|---|---|
| `ANTHROPIC_API_KEY` | API kľúč pre Claude ([console.anthropic.com](https://console.anthropic.com)) |
| `IMAP_HOST` / `IMAP_USER` / `IMAP_PASSWORD` | prihlásenie do schránky (čítanie) |
| `IMAP_FOLDER` | priečinok, predvolene `INBOX` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | odosielanie upozornení |
| `REMINDER_TO` | kam posielať upozornenia (predvolene `IMAP_USER`) |
| `REMINDER_DAYS_AHEAD` | koľko dní dopredu pripomínať splatnosti (predvolene 7) |
| `EMAIL_LOOKBACK_DAYS` | koľko dní dozadu prehľadávať poštu pri `fetch` (predvolene 7) |
| `CLAUDE_MODEL` | model, predvolene `claude-opus-4-8` |
| `DB_PATH` | cesta k SQLite databáze, predvolene `bill_agent.db` |

## Bezpečnosť

- Agent **nikdy sám neplatí** — len pripraví QR kód a pripomenie. Platbu vždy
  potvrdzujete vy v bankovej appke.
- Prístup do banky nepotrebuje; párovanie platieb robí z CSV výpisu, ktorý mu dáte.
- Údaje ostávajú lokálne v SQLite; do Claude API sa posiela len obsah e-mailov na extrakciu.

## Testy

```bash
pip install pytest
pytest
```
