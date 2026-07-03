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
3. **`import-bank`** — načíta výpis z banky (CSV) a automaticky spáruje zaplatené platby
   podľa variabilného symbolu a sumy → označí ich ako zaplatené, takže vám ich už nepripomína.
4. **`run`** — `fetch` + `remind` v jednom (ideálne do cronu).

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

### Gmail

Pre Gmail si vytvorte **App Password** (Google účet → Zabezpečenie → Heslá aplikácií)
a použite ho ako `IMAP_PASSWORD` / `SMTP_PASSWORD`.

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
