# VORU — reklamný manuál pre 5 trhov

Praktický návod: čo, kde a v akom poradí spustiť. Každý trh inzeruje
**svoju doménu** (voru.sk / voru.cz / voru.pl / voru.at / voru.hu) —
návštevník pristane rovno vo svojom jazyku.

## 0. Pred spustením čohokoľvek (povinné)

1. **Stripe** — bez platobnej brány sú reklamy vyhodené peniaze
2. Overiť, že všetkých 5 domén beží (otvoriť každú v prehliadači)
3. Facebook Business Manager + stránka „VORU" (jedna globálna, príspevky
   v jazyku trhu)
4. Google Ads účet
5. Do každej reklamy dávať odkaz s UTM parametrami, nech vidno, čo funguje:
   `https://voru.sk/?utm_source=facebook&utm_medium=cpc&utm_campaign=sk-fraud`
   (meň `source`, `campaign` podľa kanála a kreatívy)

## 1. Poradie spúšťania trhov

| Poradie | Trh | Prečo |
|---|---|---|
| 1. | **SK** | domáci trh, plná podpora (PAY by square, daňový kalendár), vieš robiť podporu |
| 2. | **CZ** (o 2–4 týždne) | 2× väčší trh, produkt 100 % funkčný (QR Platba, VS), jazyková bariéra nulová |
| 3. | **PL** (keď SK+CZ platia) | veľký trh, ale bez QR — predáva sa cez ochranu pred podvodom |
| 4. | **AT** | Girocode funguje, ale nemecká podpora zákazníkov = záväzok |
| 5. | **HU** | bez QR, forinty — spustiť ako posledný |

Nespúšťaj viac než 2 trhy naraz — nestíhal by si vyhodnocovať ani odpovedať
záujemcom.

## 2. Rozpočet na štart (mesačne)

- SK: 150 € (100 Google + 50 FB/IG)
- CZ: 150 € (100 Google + 50 FB/IG)
- Ostatné trhy: spúšťať až po vyhodnotení SK+CZ (min. 4 týždne dát)
- TikTok: 0 € — organicky (videá telefónom), platené až keď niečo chytí

Vyhodnocovanie: pri 49 €/rok sa kampaň opláca, ak jeden platiaci klient
stojí v reklame menej než ~35 €. Po mesiaci vypni, čo je drahšie, a posilni,
čo je lacnejšie.

## 3. Google Ads (vyhľadávanie)

Typ kampane: **Search**, cieľ: návštevy webu. Denný limit 3–5 €/trh.
Jedna kampaň na trh, jazyk aj geografia trhu, odkaz na doménu trhu.

### Kľúčové slová

- **SK (voru.sk):** pripomienka platby faktúry · stráženie splatnosti faktúr ·
  evidencia došlých faktúr · QR platba faktúra · ako nezabudnúť zaplatiť faktúru
- **CZ (voru.cz):** hlídání splatnosti faktur · připomínka platby faktury ·
  evidence došlých faktur · QR platba faktura
- **PL (voru.pl):** przypomnienie o płatności faktury · pilnowanie terminów
  płatności · oszustwo na fakturę · ewidencja faktur kosztowych
- **AT (voru.at):** Zahlungserinnerung Rechnungen · Rechnungen verwalten
  Kleinunternehmer · Zahlungsfristen überwachen · Girocode Rechnung
- **HU (voru.hu):** számla fizetési emlékeztető · fizetési határidő figyelés ·
  bejövő számlák kezelése

### Texty inzerátov (nadpisy ↔ kombinuj, popis jeden)

**SK:** „Už nikdy pokuta za faktúru" / „AI prečíta faktúry za vás" /
„14 dní zadarmo, bez karty" — Popis: „VORU číta vašu poštu a ráno pošle,
čo zaplatiť, s QR kódom. Výpis z banky odškrtne zaplatené sám. Od 4,99 €/mes."

**CZ:** „Už nikdy penále za fakturu" / „AI přečte faktury za vás" /
„14 dní zdarma, bez karty" — „VORU čte vaši poštu a ráno pošle, co zaplatit,
s QR Platbou. Výpis z banky odškrtne zaplacené sám. Od 4,99 €/měs."

**PL:** „Koniec z odsetkami za zwłokę" / „AI czyta faktury za Ciebie" /
„14 dni za darmo, bez karty" — „VORU czyta Twoją pocztę i rano wysyła, co
zapłacić, z gotowymi danymi przelewu. Ostrzega przed podmianą konta. Od 4,99 €/mies."

**AT:** „Nie wieder Mahnspesen" / „KI liest Ihre Rechnungen" /
„14 Tage gratis, ohne Karte" — „VORU liest Ihr Postfach und schickt morgens,
was zu zahlen ist — mit Girocode zum Scannen. Ab 4,99 €/Monat."

**HU:** „Soha többé késedelmi kamat" / „AI olvassa a számláit" /
„14 nap ingyen, kártya nélkül" — „A VORU elolvassa postáját és reggel küldi,
mit kell fizetni, kész utalási adatokkal. Havi 4,99 €-tól."

## 4. Facebook / Instagram

Kampaň na trh: cieľ **Návštevnosť** (neskôr Konverzie), umiestnenie feed +
Stories, publikum: 25–55, záujmy podnikanie/účtovníctvo/malé firmy, jazyk
a krajina trhu. Kreatívy máš hotové (PNG):

| Súbor | Použitie |
|---|---|
| `sk-fraud.png`, `cz-fraud.png`, `pl-fraud.png` | hlavný motív — podvodný IBAN (najsilnejší) |
| `sk-qr.png` | druhý motív — ranný prehľad s QR |
| `sk-chaos.png` | tretí motív — pred/po |
| `sk-story.png` | Stories/Reels formát |

(DE/HU varianty kreatív vygenerujem na požiadanie rovnako ako ostatné.)

Text k fraud motívu (SK vzor, preložený je v kreatíve):
> Podvodníci menia IBAN na faktúrach známych dodávateľov. VORU si pamätá
> účty všetkých vašich partnerov a varuje vás skôr, než zaplatíte.
> 14 dní zadarmo → voru.sk

Text k QR motívu:
> Každé ráno o 7:00: čo zaplatiť, komu a dokedy. Naskenuješ QR, zaplatíš,
> hotovo. Faktúry sa už strážia samy. → voru.sk

## 5. TikTok / Reels (organicky, telefónom, 20–30 s)

1. **POV ráno:** káva → jeden e-mail → naskenuješ 3 QR kódy → zavrieš mobil.
   Titulok: „Faktúry vybavené za 40 sekúnd."
2. **Príbeh o podvode:** „Kamarát poslal 4 800 € na podvodný účet…" → ukážka
   varovania VORU. Funguje vo všetkých jazykoch.
3. **Pred/Po:** chaos papierov a upomienok vs. jeden čistý ranný e-mail.

Zverejňuj 2–3× týždenne, vždy s doménou trhu v titulku. Slovenské videá
prekladaj titulkami do CZ (rovnaké video znesie oba trhy).

## 6. Kanály zadarmo (popri reklame)

- **FB skupiny:** SK „Živnostníci a podnikatelia SR", CZ „Podnikatelé a OSVČ",
  PL „Księgowość i podatki JDG" — hodnotné príspevky o IBAN podvodoch, nie spam
- **Účtovníčky/účetní/księgowe:** účet zadarmo + 30 % provízia z privedených
  klientov (Stripe promo kódy) — najlacnejší kanál
- **Médiá:** SK Startitup/Podnikajte.sk, CZ CzechCrunch, PL/AT/HU až po
  lokálnom rozbehu. Príbeh: „Slovenský AI strážca faktúr odhalí aj podvodne
  zmenený IBAN — za cenu kávy."

## 7. Meranie úspechu (týždenne, 10 minút)

1. Google Ads / Meta prehľad: koľko stáli kliky na kampaň
2. `/admin` vo VORU: koľko registrácií pribudlo
3. Stripe: koľko trialov sa zmenilo na platby
4. Vypnúť kampane s cenou za registráciu > 10 €, posilniť tie pod 3 €
