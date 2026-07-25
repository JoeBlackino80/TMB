# VORU — akčný checklist prvých 30 dní od spustenia

Predpoklad: všetkých 5 domén beží a Stripe je aktívny (viď MARKETING.md,
bod 0). Odhady času sú čisté sústredené hodiny, nie kalendárne dni.

---

## Týždeň 1 — merateľnosť a základy

- [ ] **Plausible Analytics** *(30 min)*
  - Založiť účet na plausible.io (platený, od ~9 €/mes.) a pridať web
    `voru.sk` (+ voru.cz, voru.pl, voru.at, voru.hu ako ďalšie weby,
    alebo jeden web s povolenými subdoménami podľa preferencie reportov).
  - Na serveri doplniť `PLAUSIBLE_DOMAIN=voru.sk` do `/root/TMB/.env.master`
    a reštartovať webapp (skript sa vkladá len na verejné stránky —
    viď DEPLOY-SAAS.md, sekcia Plausible).
  - Overiť v Plausible real-time, že návšteva landing page sa počíta.

- [ ] **Google Search Console — všetkých 5 domén** *(1,5 h)*
  - Pridať properties: voru.sk, voru.cz, voru.pl, voru.at, voru.hu
    (ideálne ako doménové property cez DNS TXT záznam).
  - V každej property odoslať `sitemap.xml`
    (https://voru.sk/sitemap.xml atď.).
  - Skontrolovať, že hreflang väzby medzi doménami GSC vidí bez chýb
    (report „Medzinárodné zacielenie" / pokrytie).
  - O týždeň sa vrátiť a overiť indexáciu všetkých 5 domén.

- [ ] **Google Business Profile** *(45 min)*
  - Založiť profil pre SORB XT s.r.o. (kategória: softvérová spoločnosť),
    web voru.sk, kontakt obchod@sorbxt.sk.
  - Vyplniť popis (AI strážca faktúr…), logo, úvodný príspevok o spustení.
  - Pozn.: overenie firmy môže trvať dni až týždne — spustiť hneď.

## Týždeň 2 — katalógy a zápisy (SEO základ + prvé odkazy)

- [ ] **SK katalógy** *(1 h)*: Azet.sk (katalóg firiem), Firmy.sk;
      bonus: Zoznam.sk katalóg, Podnikatelia.sk.
- [ ] **CZ katalógy** *(1 h)*: Firmy.cz (Seznam — najdôležitejší),
      Zivefirmy.cz; bonus: Najisto.cz.
- [ ] **PL katalógy** *(45 min)*: Panorama Firm (panoramafirm.pl),
      Aleo.com; bonus: pkt.pl.
- [ ] **AT katalógy** *(45 min)*: Herold.at, FirmenABC.at;
      bonus: WKO Firmen A–Z (ak splníte podmienky).
- [ ] **HU katalógy** *(45 min)*: Cylex.hu, Aranyoldalak.hu.
- Tip: všade používať rovnaký názov, popis v jazyku trhu a doménu daného
  trhu (voru.cz do CZ katalógov atď.) — konzistentné NAP údaje.

## Týždeň 2–3 — launch: kde zdieľať (5 miest)

- [ ] **Facebook skupiny SK** *(1 h + odpovedanie)* — napr. „Živnostníci
      a podnikatelia (SK)", „Podnikanie na Slovensku", skupiny pre SZČO
      a malé s.r.o. Najprv prečítať pravidlá; použiť LAUNCH-2 zo
      socialne-siete.md, formulované ako osobný príbeh.
- [ ] **LinkedIn — osobný profil zakladateľa** *(30 min)* — LAUNCH-1;
      firemné stránky majú malý dosah, osobný profil funguje lepšie.
      Požiadať známych o komentár v prvej hodine.
- [ ] **Reddit** *(45 min)* — r/Slovakia (téma podnikanie; dodržať pravidlá
      self-promo — rámcovať ako „spravil som nástroj, feedback vítaný"),
      pre CZ r/czech.
- [ ] **SK/CZ startup médiá a komunity** *(1 h)* — tip do Startitup.sk
      a FinReport.sk (SK), CzechCrunch.cz (CZ): krátky pitch e-mailom
      s 3 vetami a screenshotom; „slovenský AI strážca faktúr" je pre ne
      použiteľná téma.
- [ ] **Product Hunt / Indie Hackers** *(2 h príprava + launch deň)* —
      EN verzia (voru.sk/en); nečakať zázraky na SK produkt, ale prinesie
      spätné odkazy a prvých EN používateľov.

## Týždeň 3–4 — reklama a rytmus

- [ ] **Spustiť Google Ads SK** *(2 h nastavenie)* — podľa
      marketing/google-ads.md (4 €/deň, 3 skupiny, negatívne slová).
- [ ] **Oslovenie účtovníčok — 1. vlna** *(3 h)* — 20–30 účtovných
      kancelárií podľa marketing/email-uctovnikom.md; follow-up po týždni.
      Vyhnúť sa 15.–25. dňu v mesiaci.
- [ ] **Skontrolovať dáta** *(1 h)* — Plausible: odkiaľ chodia registrácie;
      GSC: indexácia; Ads: vyhľadávacie výrazy → doplniť negatívne slová.

## Týždenný rytmus obsahu (od týždňa 1, natrvalo)

Podľa CONTENT-PLAN.md — pripravené texty aj obrázky:

| Deň | Aktivita | Čas |
|---|---|---|
| Po | FB + IG post (7:30) | 15 min |
| Ut | odpovede na komentáre/e-maily, 1 zapojenie sa do diskusie v FB skupine | 30 min |
| St | FB + IG post (8:00–9:00) | 15 min |
| Št | 1 TikTok/Reels video (telefónom, aj na IG a FB) | 45 min |
| Pi | FB + IG post + LinkedIn post (1× za 2 týždne z socialne-siete.md) | 30 min |
| — | odpovedať na komentáre do hodiny (algoritmus + dôvera) | priebežne |

**Spolu: ~2,5 h týždenne na obsah + ~8 h jednorazovej práce v prvom mesiaci.**
