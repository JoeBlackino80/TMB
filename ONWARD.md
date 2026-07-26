# Onward — SaaS na letové rezervácie bez platby (štýl BestOnwardTicket)

Zákazník zaplatí pár eur, dostane e-mailom **skutočnú rezerváciu letu s PNR
kódom** overiteľnú na stránke aerolinky — bez kúpy letenky. Rezervácia po
24–72 hodinách sama prepadne. Použitie: **žiadosti o víza** (ambasády bežne
samy odporúčajú nekupovať letenku pred schválením) a **proof of onward
travel**.

## Ako to celé funguje (aj u konkurencie)

Služby ako BestOnwardTicket nič nefalšujú — majú prístup do rezervačného
systému (GDS cez travel-agency akreditáciu, alebo modernejšie API ako
**Duffel**) a vytvárajú **hold orders**: rezervácia vznikne v systéme
aerolinky s reálnym PNR, ale letenka sa nevystaví a nikto aerolinke neplatí.
Aerolinka drží miesto do `payment_required_by` (24–72 h podľa dopravcu)
a potom rezerváciu sama uvoľní. Marža služby = celý poplatok (~12–16 €),
lebo náklad na rezerváciu je nula.

Tento modul robí presne to cez [Duffel API](https://duffel.com):

```
formulár → Stripe Payment Link (poplatok) → webhook →
Duffel hold order (PNR) → itinerár e-mailom → cron expirácia
```

## Čo je v module

| Súbor | Účel |
|---|---|
| `onward/app.py` | FastAPI: landing + objednávka + Stripe webhook + status stránka |
| `onward/duffel.py` | Duffel klient: search, výber hold ponuky, hold order, cancel |
| `onward/store.py` | SQLite evidencia objednávok (`onward.db`) |
| `onward/emails.py` | itinerár s PNR + oznam o expirácii |
| `onward/mailer.py` | SMTP (ONWARD_SMTP_*, fallback na SMTP_* z VORU) |
| `onward/expire.py` | cron: označí prepadnuté rezervácie a pošle oznam |

## Nasadenie

```bash
pip install -r requirements-onward.txt
export DUFFEL_API_KEY=duffel_test_...       # test kľúč = fiktívne lety zadarmo
uvicorn onward.app:app --port 8100
```

1. **Duffel** — účet na duffel.com; test kľúč (`duffel_test_...`) rezervuje
   fiktívne lety Duffel Airways, ideálne na vývoj. Na produkciu treba live
   kľúč a schválenie Duffelom (verifikácia firmy). Hold orders podporuje
   podmnožina aeroliniek — `pick_hold_offer` vyberá najlacnejšiu ponuku,
   ktorá hold umožňuje.
2. **Stripe** — Payment Link na poplatok (`STRIPE_LINK_ONWARD`), webhook
   `checkout.session.completed` na `/stripe/webhook`
   (`ONWARD_STRIPE_WEBHOOK_SECRET`). Bez nastaveného Payment Linku appka
   rezervuje hneď po formulári — vývojový režim.
3. **Cron** — každú hodinu:
   `0 * * * * cd /cesta/k/TMB && .venv/bin/python -m onward.expire`

### Premenné prostredia

| Premenná | Význam |
|---|---|
| `DUFFEL_API_KEY` | kľúč Duffel API (test/live) |
| `ONWARD_BRAND` | názov služby (predvolene OnwardPass) |
| `ONWARD_PRICE_EUR` | zobrazovaná cena poplatku (predvolene 14.90) |
| `ONWARD_DB_PATH` | SQLite databáza (predvolene onward.db) |
| `STRIPE_LINK_ONWARD` | Stripe Payment Link na poplatok |
| `ONWARD_STRIPE_WEBHOOK_SECRET` | signing secret webhooku |
| `ONWARD_SMTP_HOST/PORT/USER/PASSWORD` | SMTP; ak chýba, použije sa `SMTP_*` |

## Férovosť a právne poznámky

- Predávaš **rezerváciu, nie letenku** — web aj e-maily to hovoria otvorene
  (nedá sa s ňou letieť, po expirácii ju aerolinka uvoľní). Nič sa
  nefalšuje: PNR je skutočný a overiteľný, kým platí.
- Na víza je to štandard; zákazník si má žiadosť načasovať tak, aby bola
  rezervácia pri kontrole živá, prípadne si objednať novú.
- Obchodné podmienky + refund policy si doplň pred spustením (vzor máš vo
  VORU `terms.html`); GDPR: spracúvaš meno, dátum narodenia a kontakt
  pasažiera — uveď účel a dobu uchovávania.
- Duffel live prístup vyžaduje reálnu firmu — počítaj s onboardingom.

## Testy

```bash
pytest tests/test_onward.py
```
