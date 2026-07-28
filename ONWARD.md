# Onward — SaaS na letové rezervácie bez platby (konkurencia OnwardTicket)

Zákazník zaplatí pár eur, dostane e-mailom **skutočnú rezerváciu letu s PNR
kódom** overiteľnú na stránke aerolinky — bez kúpy letenky. Použitie:
**žiadosti o víza** (ambasády bežne samy odporúčajú nekupovať letenku pred
schválením) a **proof of onward travel**.

## Ako to celé funguje (aj u konkurencie)

Služby ako OnwardTicket nič nefalšujú — majú prístup do rezervačného
systému (GDS cez travel-agency akreditáciu, alebo modernejšie API ako
**Duffel**) a vytvárajú **hold orders**: rezervácia vznikne v systéme
aerolinky s reálnym PNR, ale letenka sa nevystaví a nikto aerolinke neplatí.
Aerolinka drží miesto do `payment_required_by` (24–72 h podľa dopravcu)
a potom rezerváciu sama uvoľní.

```
formulár → Stripe Payment Link (poplatok) → webhook →
Duffel hold order (PNR) → itinerár + PDF e-mailom → cron: obnova/expirácia
```

## Čím sme lepší než konkurencia

- **Auto-renew (plány 7/14 dní)** — keď aerolinka hold uvoľní, cron
  automaticky vytvorí novú rezerváciu s čerstvým PNR a pošle aktualizovaný
  itinerár. Zákazník má živý, overiteľný PNR celé vízové okno; konkurencia
  väčšinou predáva len 48-hodinové rezervácie.
- **PDF itinerár v prílohe** + stránka objednávky so živým stavom
  a stiahnutím PDF.
- **1–4 pasažieri v jednej objednávke**, jednosmerné aj spiatočné lety.
- **Poctivá komunikácia** — web, podmienky aj e-maily otvorene hovoria, že
  ide o rezerváciu, nie letenku (dôležité právne aj pre platobné brány).

## Čo je v module

| Súbor | Účel |
|---|---|
| `onward/app.py` | FastAPI: landing, objednávka, Stripe webhook, status, PDF download, admin, FAQ/terms/privacy |
| `onward/booking.py` | vytvorenie + automatická obnova rezervácie (zdieľané appkou a cronom) |
| `onward/duffel.py` | Duffel klient: search (aj spiatočný, multi-pax), hold order, cancel |
| `onward/store.py` | SQLite evidencia objednávok (`onward.db`) |
| `onward/pdf.py` | PDF itinerár (fpdf2) |
| `onward/emails.py` | itinerár / obnova / expirácia |
| `onward/mailer.py` | SMTP s prílohami (ONWARD_SMTP_*, fallback SMTP_*) |
| `onward/expire.py` | cron: obnoví (week/twoweek) alebo expiruje prepadnuté holdy |

## Nasadenie

```bash
pip install -r requirements-onward.txt
export DUFFEL_API_KEY=duffel_test_...       # test kľúč = fiktívne lety zadarmo
uvicorn onward.app:app --port 8100
```

1. **Duffel** — účet na duffel.com; test kľúč (`duffel_test_...`) rezervuje
   fiktívne lety Duffel Airways. Na produkciu treba live kľúč a schválenie
   (verifikácia firmy). Hold orders podporuje podmnožina aeroliniek —
   `pick_hold_offer` vyberá najlacnejšiu ponuku, ktorá hold umožňuje.
   **Pred spustením si písomne over, či sa nezaplatené holdy účtujú
   a či im use-case nevadí** (e-mail máš pripravený v konverzácii).
2. **Stripe** — tri Payment Linky (basic / week / twoweek), webhook
   `checkout.session.completed` na `/stripe/webhook`. Pri linkoch zapni
   „adjustable quantity", ak chceš účtovať za pasažiera.
3. **Cron** — každých 15 minút (obnovy musia chodiť promptne):
   `*/15 * * * * cd /cesta/k/TMB && .venv/bin/python -m onward.expire`

### Premenné prostredia

| Premenná | Význam |
|---|---|
| `DUFFEL_API_KEY` | kľúč Duffel API (test/live) |
| `ONWARD_BRAND` | názov služby (predvolene ValidFlight) |
| `ONWARD_BASE_URL` | verejná URL (do e-mailov, napr. https://validflight.com) |
| `ONWARD_PRICE_EUR` / `_WEEK_EUR` / `_2WEEK_EUR` | zobrazované ceny (9.90 / 16.90 / 24.90) |
| `ONWARD_DB_PATH` | SQLite databáza (predvolene onward.db) |
| `STRIPE_LINK_ONWARD` / `_WEEK` / `_2WEEK` | Stripe Payment Linky plánov |
| `ONWARD_STRIPE_WEBHOOK_SECRET` | signing secret webhooku |
| `ONWARD_ADMIN_KEY` | kľúč pre /admin?key=... |
| `ONWARD_SMTP_HOST/PORT/USER/PASSWORD` | SMTP; ak chýba, použije sa `SMTP_*` |

## Férovosť a právne poznámky

- Predávaš **rezerváciu, nie letenku** — web, podmienky aj e-maily to
  hovoria otvorene. Nič sa nefalšuje: PNR je skutočný a overiteľný, kým
  platí; po obnove platí nový PNR.
- Na víza je to štandard; auto-renew drží živý PNR celé vízové okno.
- GDPR: spracúvaš meno, dátum narodenia a kontakt pasažiera — účel a doba
  uchovávania sú v /privacy; dáta idú Duffelu a aerolinke, platby Stripe.
- Duffel live prístup vyžaduje reálnu firmu — počítaj s onboardingom.

## Testy

```bash
pytest tests/test_onward.py
```
