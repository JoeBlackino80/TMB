"""Preklady verejných stránok webu (registrácia, prihlásenie).

Jazyk sa vyberá parametrom ?lang= (posielajú ho tlačidlá z jazykových
mutácií landing page) a nesie sa skrytým poľom formulára.
"""

LANGS = ("sk", "cs", "pl", "de", "hu", "en")

_SK = {
    "err_login": "Nesprávny e-mail alebo heslo.",
    "err_lockout": "Príliš veľa neúspešných pokusov — skúste to znova o 15 minút alebo si obnovte heslo cez „Zabudli ste heslo?“.",
    "err_totp_expired": "Overenie vypršalo — prihláste sa znova.",
    "err_totp_wrong": "Kód nesedí — skúste to znova.",

    "nav_login": "Prihlásiť sa",
    "nav_try": "Vyskúšať zadarmo",
    "reg_title": "Vytvorte si účet",
    "reg_lead": "VORU stráži vaše faktúry, platby a termíny. 14 dní zadarmo — "
                "bez platobnej karty, potom 4,99 €/mesiac alebo 49 €/rok.",
    "use_as": "Používam VORU ako",
    "opt_business": "firma / živnostník",
    "opt_personal": "súkromná osoba",
    "opt_both": "firma aj súkromne",
    "email_label": "Váš e-mail (sem budú chodiť prehľady)",
    "password_label": "Heslo (min. 8 znakov)",
    "consent_html": "Súhlasím s <a href='/podmienky' target='_blank'>obchodnými "
                    "podmienkami</a> a so spracovaním osobných údajov podľa "
                    "<a href='/gdpr' target='_blank'>zásad ochrany údajov</a> "
                    "(vrátane spracovania obsahu pripojenej pošty na účely "
                    "služby).",
    "reg_btn": "Registrovať sa",
    "have_account": "Máte účet?",
    "sign_in": "Prihláste sa",
    "login_title": "Prihlásenie",
    "email": "E-mail",
    "password": "Heslo",
    "login_btn": "Prihlásiť sa",
    "no_account": "Nemáte účet?",
    "register_link": "Registrujte sa",
    "trial_note": "— 14 dní zadarmo.",
    "forgot": "Zabudli ste heslo?",
    "totp_title": "Dvojfaktorové overenie",
    "totp_lead": "Zadajte 6-miestny kód z overovacej aplikácie v telefóne "
                 "(napr. Google Authenticator).",
    "totp_code": "Kód",
    "totp_btn": "Overiť",
    "err_consent": "Registrácia vyžaduje súhlas s obchodnými podmienkami "
                   "a spracovaním údajov.",
    "err_invalid": "Zadajte platný e-mail a heslo dlhé aspoň 8 znakov.",
    "err_exists": "Účet už existuje — prihláste sa.",
    "err_bot": "Nepodarilo sa overiť, že nie ste robot — obnovte stránku "
               "a skúste to znova.",
    "err_expired": "Platnosť formulára vypršala — skúste to znova.",
    "err_ratelimit": "Priveľa registrácií z tejto adresy — skúste to o hodinu, "
                     "alebo nám napíšte na obchod@sorbxt.sk.",
    "err_turnstile": "Overenie, že nie ste robot, zlyhalo — skúste to znova.",
    "err_paused": "Registrácie sú dočasne pozastavené — skúste to neskôr, "
                  "alebo nám napíšte na obchod@sorbxt.sk.",
    "err_disposable": "Použite prosím trvalú e-mailovú adresu — jednorazové "
                      "schránky nie sú podporované.",
}

_CS = {
    "err_login": "Nesprávný e-mail nebo heslo.",
    "err_lockout": "Příliš mnoho neúspěšných pokusů — zkuste to znovu za 15 minut, nebo si obnovte heslo přes „Zapomněli jste heslo?“.",
    "err_totp_expired": "Ověření vypršelo — přihlaste se znovu.",
    "err_totp_wrong": "Nesprávný kód — zkuste to znovu.",

    "nav_login": "Přihlásit se",
    "nav_try": "Vyzkoušet zdarma",
    "reg_title": "Vytvořte si účet",
    "reg_lead": "VORU hlídá vaše faktury, platby a termíny. 14 dní zdarma — "
                "bez platební karty, potom 4,99 €/měsíc nebo 49 €/rok.",
    "use_as": "Používám VORU jako",
    "opt_business": "firma / živnostník",
    "opt_personal": "soukromá osoba",
    "opt_both": "firma i soukromě",
    "email_label": "Váš e-mail (sem budou chodit přehledy)",
    "password_label": "Heslo (min. 8 znaků)",
    "consent_html": "Souhlasím s <a href='/podmienky?lang=cs' target='_blank'>obchodními "
                    "podmínkami</a> a se zpracováním osobních údajů podle "
                    "<a href='/gdpr?lang=cs' target='_blank'>zásad ochrany údajů</a> "
                    "(včetně zpracování obsahu připojené pošty pro účely služby).",
    "reg_btn": "Zaregistrovat se",
    "have_account": "Máte účet?",
    "sign_in": "Přihlaste se",
    "login_title": "Přihlášení",
    "email": "E-mail",
    "password": "Heslo",
    "login_btn": "Přihlásit se",
    "no_account": "Nemáte účet?",
    "register_link": "Zaregistrujte se",
    "trial_note": "— 14 dní zdarma.",
    "forgot": "Zapomněli jste heslo?",
    "totp_title": "Dvoufaktorové ověření",
    "totp_lead": "Zadejte 6místný kód z autentizační aplikace.",
    "totp_code": "Kód",
    "totp_btn": "Ověřit",
    "err_consent": "Registrace vyžaduje souhlas s obchodními podmínkami "
                   "a zpracováním údajů.",
    "err_invalid": "Zadejte platný e-mail a heslo o délce alespoň 8 znaků.",
    "err_exists": "Účet už existuje — přihlaste se.",
    "err_bot": "Registraci se nepodařilo ověřit — zkuste to znovu.",
    "err_expired": "Platnost formuláře vypršela — zkuste to znovu.",
    "err_ratelimit": "Příliš mnoho registrací z této adresy — zkuste to za "
                     "hodinu, nebo nám napište na obchod@sorbxt.sk.",
    "err_turnstile": "Ověření, že nejste robot, selhalo — zkuste to znovu.",
    "err_paused": "Registrace jsou dočasně pozastaveny — zkuste to později, "
                  "nebo nám napište na obchod@sorbxt.sk.",
    "err_disposable": "Použijte prosím trvalou e-mailovou adresu — jednorázové "
                      "schránky nejsou podporovány.",
}

_PL = {
    "err_login": "Nieprawidłowy e-mail lub hasło.",
    "err_lockout": "Zbyt wiele nieudanych prób — spróbuj za 15 minut lub odzyskaj hasło przez „Nie pamiętasz hasła?”.",
    "err_totp_expired": "Weryfikacja wygasła — zaloguj się ponownie.",
    "err_totp_wrong": "Nieprawidłowy kod — spróbuj ponownie.",

    "nav_login": "Zaloguj się",
    "nav_try": "Wypróbuj za darmo",
    "reg_title": "Załóż konto",
    "reg_lead": "VORU pilnuje Twoich faktur, płatności i terminów. 14 dni za "
                "darmo — bez karty płatniczej, potem 4,99 €/mies. lub 49 €/rok.",
    "use_as": "Używam VORU jako",
    "opt_business": "firma / działalność gospodarcza",
    "opt_personal": "osoba prywatna",
    "opt_both": "firma i prywatnie",
    "email_label": "Twój e-mail (tu będą przychodzić zestawienia)",
    "password_label": "Hasło (min. 8 znaków)",
    "consent_html": "Akceptuję <a href='/podmienky?lang=pl' target='_blank'>regulamin</a> "
                    "i zgadzam się na przetwarzanie danych osobowych zgodnie z "
                    "<a href='/gdpr?lang=pl' target='_blank'>polityką prywatności</a> "
                    "(w tym przetwarzanie treści podłączonej poczty na potrzeby "
                    "usługi).",
    "reg_btn": "Zarejestruj się",
    "have_account": "Masz konto?",
    "sign_in": "Zaloguj się",
    "login_title": "Logowanie",
    "email": "E-mail",
    "password": "Hasło",
    "login_btn": "Zaloguj się",
    "no_account": "Nie masz konta?",
    "register_link": "Zarejestruj się",
    "trial_note": "— 14 dni za darmo.",
    "forgot": "Nie pamiętasz hasła?",
    "totp_title": "Weryfikacja dwuskładnikowa",
    "totp_lead": "Wpisz 6-cyfrowy kod z aplikacji uwierzytelniającej.",
    "totp_code": "Kod",
    "totp_btn": "Zweryfikuj",
    "err_consent": "Rejestracja wymaga akceptacji regulaminu i zgody na "
                   "przetwarzanie danych.",
    "err_invalid": "Podaj prawidłowy e-mail i hasło o długości min. 8 znaków.",
    "err_exists": "Konto już istnieje — zaloguj się.",
    "err_bot": "Nie udało się zweryfikować rejestracji — spróbuj ponownie.",
    "err_expired": "Formularz wygasł — spróbuj ponownie.",
    "err_ratelimit": "Zbyt wiele rejestracji z tego adresu — spróbuj za godzinę "
                     "lub napisz do nas na obchod@sorbxt.sk.",
    "err_turnstile": "Weryfikacja, że nie jesteś robotem, nie powiodła się — "
                     "spróbuj ponownie.",
    "err_paused": "Rejestracje są tymczasowo wstrzymane — spróbuj później lub "
                  "napisz do nas na obchod@sorbxt.sk.",
    "err_disposable": "Użyj proszę stałego adresu e-mail — jednorazowe skrzynki "
                      "nie są obsługiwane.",
}

_DE = {
    "err_login": "Falsche E-Mail oder falsches Passwort.",
    "err_lockout": "Zu viele Fehlversuche — versuchen Sie es in 15 Minuten erneut oder setzen Sie das Passwort über „Passwort vergessen?“ zurück.",
    "err_totp_expired": "Die Verifizierung ist abgelaufen — melden Sie sich erneut an.",
    "err_totp_wrong": "Falscher Code — bitte erneut versuchen.",

    "nav_login": "Anmelden",
    "nav_try": "Kostenlos testen",
    "reg_title": "Konto erstellen",
    "reg_lead": "VORU überwacht Ihre Rechnungen, Zahlungen und Fristen. "
                "14 Tage kostenlos — ohne Kreditkarte, danach 4,99 €/Monat "
                "oder 49 €/Jahr.",
    "use_as": "Ich nutze VORU als",
    "opt_business": "Firma / Selbstständige(r)",
    "opt_personal": "Privatperson",
    "opt_both": "Firma und privat",
    "email_label": "Ihre E-Mail (hierhin kommen die Übersichten)",
    "password_label": "Passwort (min. 8 Zeichen)",
    "consent_html": "Ich stimme den <a href='/podmienky?lang=de' target='_blank'>AGB</a> "
                    "und der Verarbeitung personenbezogener Daten gemäß der "
                    "<a href='/gdpr?lang=de' target='_blank'>Datenschutzerklärung</a> zu "
                    "(einschließlich der Verarbeitung der Inhalte des "
                    "verbundenen Postfachs für den Dienst).",
    "reg_btn": "Registrieren",
    "have_account": "Schon ein Konto?",
    "sign_in": "Anmelden",
    "login_title": "Anmeldung",
    "email": "E-Mail",
    "password": "Passwort",
    "login_btn": "Anmelden",
    "no_account": "Noch kein Konto?",
    "register_link": "Registrieren",
    "trial_note": "— 14 Tage kostenlos.",
    "forgot": "Passwort vergessen?",
    "totp_title": "Zwei-Faktor-Authentifizierung",
    "totp_lead": "Geben Sie den 6-stelligen Code aus Ihrer "
                 "Authentifizierungs-App ein.",
    "totp_code": "Code",
    "totp_btn": "Bestätigen",
    "err_consent": "Die Registrierung erfordert die Zustimmung zu den AGB "
                   "und zur Datenverarbeitung.",
    "err_invalid": "Bitte gültige E-Mail und ein Passwort mit mindestens "
                   "8 Zeichen eingeben.",
    "err_exists": "Das Konto existiert bereits — melden Sie sich an.",
    "err_bot": "Die Registrierung konnte nicht verifiziert werden — bitte "
               "erneut versuchen.",
    "err_expired": "Das Formular ist abgelaufen — bitte erneut versuchen.",
    "err_ratelimit": "Zu viele Registrierungen von dieser Adresse — versuchen "
                     "Sie es in einer Stunde oder schreiben Sie an "
                     "obchod@sorbxt.sk.",
    "err_turnstile": "Die Roboter-Prüfung ist fehlgeschlagen — bitte erneut "
                     "versuchen.",
    "err_paused": "Registrierungen sind vorübergehend pausiert — versuchen Sie "
                  "es später oder schreiben Sie an obchod@sorbxt.sk.",
    "err_disposable": "Bitte verwenden Sie eine dauerhafte E-Mail-Adresse — "
                      "Wegwerf-Postfächer werden nicht unterstützt.",
}

_HU = {
    "err_login": "Hibás e-mail-cím vagy jelszó.",
    "err_lockout": "Túl sok sikertelen próbálkozás — próbálja 15 perc múlva, vagy állítsa vissza a jelszavát az „Elfelejtette a jelszavát?” linkkel.",
    "err_totp_expired": "Az ellenőrzés lejárt — jelentkezzen be újra.",
    "err_totp_wrong": "Hibás kód — próbálja újra.",

    "nav_login": "Bejelentkezés",
    "nav_try": "Ingyenes próba",
    "reg_title": "Fiók létrehozása",
    "reg_lead": "A VORU figyeli a számláit, fizetéseit és határidőit. 14 nap "
                "ingyen — bankkártya nélkül, utána 4,99 €/hó vagy 49 €/év.",
    "use_as": "A VORU-t így használom",
    "opt_business": "cég / vállalkozó",
    "opt_personal": "magánszemély",
    "opt_both": "céges és magán",
    "email_label": "Az Ön e-mail-címe (ide érkeznek az áttekintések)",
    "password_label": "Jelszó (min. 8 karakter)",
    "consent_html": "Elfogadom az <a href='/podmienky?lang=hu' target='_blank'>ÁSZF-et</a> "
                    "és hozzájárulok a személyes adatok kezeléséhez az "
                    "<a href='/gdpr?lang=hu' target='_blank'>adatvédelmi tájékoztató</a> "
                    "szerint (beleértve a csatlakoztatott postafiók tartalmának "
                    "kezelését a szolgáltatás céljából).",
    "reg_btn": "Regisztráció",
    "have_account": "Van már fiókja?",
    "sign_in": "Jelentkezzen be",
    "login_title": "Bejelentkezés",
    "email": "E-mail",
    "password": "Jelszó",
    "login_btn": "Bejelentkezés",
    "no_account": "Nincs még fiókja?",
    "register_link": "Regisztráljon",
    "trial_note": "— 14 nap ingyen.",
    "forgot": "Elfelejtette a jelszavát?",
    "totp_title": "Kétlépcsős azonosítás",
    "totp_lead": "Írja be a hitelesítő alkalmazás 6 jegyű kódját.",
    "totp_code": "Kód",
    "totp_btn": "Ellenőrzés",
    "err_consent": "A regisztrációhoz el kell fogadni az ÁSZF-et és az "
                   "adatkezelést.",
    "err_invalid": "Adjon meg érvényes e-mail-címet és legalább 8 karakteres "
                   "jelszót.",
    "err_exists": "A fiók már létezik — jelentkezzen be.",
    "err_bot": "A regisztrációt nem sikerült ellenőrizni — próbálja újra.",
    "err_expired": "Az űrlap érvényessége lejárt — próbálja újra.",
    "err_ratelimit": "Túl sok regisztráció erről a címről — próbálja egy óra "
                     "múlva, vagy írjon nekünk: obchod@sorbxt.sk.",
    "err_turnstile": "A robotellenőrzés sikertelen — próbálja újra.",
    "err_paused": "A regisztráció átmenetileg szünetel — próbálja később, "
                  "vagy írjon nekünk: obchod@sorbxt.sk.",
    "err_disposable": "Kérjük, használjon állandó e-mail-címet — az eldobható "
                      "postafiókok nem támogatottak.",
}

_EN = {
    "err_login": "Incorrect email or password.",
    "err_lockout": "Too many failed attempts — try again in 15 minutes or reset your password via “Forgot your password?”.",
    "err_totp_expired": "Verification expired — please sign in again.",
    "err_totp_wrong": "Wrong code — try again.",

    "nav_login": "Sign in",
    "nav_try": "Try for free",
    "reg_title": "Create your account",
    "reg_lead": "VORU keeps track of your invoices, payments and deadlines. 14 days "
                "free — no credit card, then €4.99/month or €49/year.",
    "use_as": "I'm using VORU as",
    "opt_business": "a business / freelancer",
    "opt_personal": "a private individual",
    "opt_both": "business and personal",
    "email_label": "Your email (your digests will be sent here)",
    "password_label": "Password (min. 8 characters)",
    "consent_html": "I agree to the <a href='/podmienky?lang=en' "
                    "target='_blank'>terms of service</a> and to the "
                    "processing of personal data under the "
                    "<a href='/gdpr?lang=en' target='_blank'>privacy "
                    "policy</a> (including processing the contents of the "
                    "connected mailbox for the service).",
    "reg_btn": "Sign up",
    "have_account": "Already have an account?",
    "sign_in": "Sign in",
    "login_title": "Sign in",
    "email": "Email",
    "password": "Password",
    "login_btn": "Sign in",
    "no_account": "No account yet?",
    "register_link": "Sign up",
    "trial_note": "— 14 days free.",
    "forgot": "Forgot your password?",
    "totp_title": "Two-factor authentication",
    "totp_lead": "Enter the 6-digit code from your authenticator app.",
    "totp_code": "Code",
    "totp_btn": "Verify",
    "err_consent": "Registration requires agreeing to the terms and data "
                   "processing.",
    "err_invalid": "Enter a valid email and a password of at least "
                   "8 characters.",
    "err_exists": "The account already exists — sign in instead.",
    "err_bot": "The registration could not be verified — please try again.",
    "err_expired": "The form has expired — please try again.",
    "err_ratelimit": "Too many registrations from this address — try again in "
                     "an hour or write to us at obchod@sorbxt.sk.",
    "err_turnstile": "We couldn't verify that you're human — please try again.",
    "err_paused": "Registrations are temporarily paused — try again later or "
                  "write to us at obchod@sorbxt.sk.",
    "err_disposable": "Please use a permanent email address — disposable "
                      "inboxes are not supported.",
}

_TABLES = {"sk": _SK, "cs": _CS, "pl": _PL, "de": _DE, "hu": _HU, "en": _EN}


def t(lang: str | None) -> dict:
    return _TABLES.get(lang or "sk", _SK)


# ---------------------------------------------------------------------------
# Vnútro aplikácie (po prihlásení) + akčné/systémové stránky.
# Slovenčina je zdroj pravdy; preklady sú v webapp/translations/<lang>.py
# a chýbajúce kľúče padajú späť na slovenčinu.

_SK_APP = {
    # bočné menu a pätička
    "m_overview": "Prehľad", "m_mailboxes": "Schránky",
    "m_settings": "Nastavenia", "m_billing": "Predplatné",
    "m_logout": "Odhlásiť sa",
    "f_terms": "Podmienky", "f_privacy": "Ochrana osobných údajov",
    # prehľad
    "d_verify": "Potvrďte prosím svoju e-mailovú adresu — poslali sme vám "
                "odkaz. Nič vám neprišlo?",
    "d_verify_btn": "Poslať znova",
    "d_paused": "Služba je pozastavená — skúšobná doba vypršala alebo "
                "predplatné skončilo. <a href='/billing'>Aktivujte si "
                "predplatné</a>.",
    "d_trial": "Skúšobná doba do <b>{date}</b>. <a href='/billing'>Prejsť na "
               "predplatné</a> — 4,99 €/mes. alebo 49 €/rok.",
    "d_start_title": "Začnite pridaním schránky",
    "d_start_body": "VORU potrebuje prístup k schránke, kam vám chodia faktúry.",
    "d_start_btn": "Pridať schránku",
    "d_demo": "Toto sú <b>ukážkové údaje</b>, aby ste videli, ako bude prehľad "
              "vyzerať. Zmiznú automaticky po pridaní schránky.",
    "d_demo_btn": "Zmazať ukážku",
    "d_overdue": "po splatnosti", "d_unpaid": "nezaplatené",
    "d_this_month": "odíde do konca mesiaca", "d_next_month": "budúci mesiac",
    "d_open_tasks": "otvorené úlohy",
    "d_missing_title": "Pravidelné faktúry, ktoré neprišli",
    "d_missing_last": "posledná {d}", "d_missing_exp": "čakala sa do {d}",
    "d_missing_note": "Skontrolujte, či faktúra nezapadla v spame, alebo či "
                      "nechodí na inú adresu.",
    "d_payments_title": "Nezaplatené platby",
    "th_supplier": "Dodávateľ", "th_amount": "Suma", "th_due": "Splatnosť",
    "d_other_iban": "iný IBAN — overiť!", "d_today": "dnes",
    "d_qr_btn": "QR platba", "d_paid_btn": "Zaplatené",
    "d_ignore_btn": "Ignorovať", "d_ignore_confirm": "Ignorovať túto platbu?",
    "d_qr_alt": "QR kód na platbu",
    "d_qr_note": "Naskenujte v aplikácii banky — suma, IBAN aj VS sú "
                 "predvyplnené.",
    "d_pay_note": "QR kódy na zaplatenie nájdete v e-mailových prehľadoch. "
                  "Zaplatené odškrtne aj výpis z banky alebo odpoveď na e-mail "
                  "v tvare „zaplatené 3“ (číslo platby).",
    "d_sepa_btn": "Hromadný príkaz na úhradu (SEPA XML)",
    "d_sepa_note": "Súbor nahráte do internetbankingu a všetky úhrady "
                   "potvrdíte naraz.",
    "d_no_payments": "Žiadne evidované nezaplatené platby.",
    "d_renewals_title": "Končí platnosť", "d_done_btn": "Vybavené",
    "d_add_deadline": "Pridať termín",
    "d_add_kind": "Typ", "d_add_date": "Platí do", "d_add_note": "Popis (napr. ŠPZ)",
    "d_add_save": "Pridať", "d_add_hint": "Pre kúpu bez e-mailu (známka na pumpe, "
                 "papierová STK…). Ostatné VORU zachytí z pošty samo.",
    "k_pzp": "PZP poistenie", "k_havarijne": "Havarijné poistenie",
    "k_stk": "STK", "k_ek": "Emisná kontrola", "k_znamka": "Diaľničná známka",
    "k_poistka": "Poistka", "k_ine": "Iný termín",
    "d_renewals_note": "Poistky, STK, domény a predplatné, ktoré VORU našlo "
                       "vo vašej pošte. Vybavené odškrtnite, aby sme vám ich "
                       "nepripomínali.",
    # pohľadávky (vydané faktúry)
    "d_recv_title": "Pohľadávky — faktúry, ktoré vám majú zaplatiť",
    "d_recv_customer": "Odberateľ",
    "d_recv_paid_btn": "Zaplatené", "d_recv_ignore_btn": "Odstrániť",
    "d_recv_ignore_confirm": "Naozaj odstrániť túto pohľadávku?",
    "d_recv_note": "Faktúry, ktoré ste vystavili a čakáte na úhradu. "
                   "Po splatnosti ich zvýrazníme a pripomenieme v rannom prehľade.",
    "d_recv_add": "Pridať pohľadávku",
    "d_recv_amount": "Suma (€)", "d_recv_save": "Uložiť",
    "d_recv_hint": "Ručne pre faktúry, ktoré neprídu e-mailom. Vydané faktúry "
                   "z pošty (napr. z účtovného softvéru) zachytí VORU aj samo.",
    "d_tax_title": "Daňové termíny (najbližších 30 dní)",
    "d_bundle_title": "Podklady pre účtovníctvo",
    "d_bundle_note": "ZIP s faktúrami (PDF) a prehľadom platieb za mesiac — "
                     "pošlite účtovníkovi či účtovníčke jedným klikom.",
    "d_tasks_title": "Úlohy", "d_task_due": "do {d}", "d_task_done": "Hotovo",
    "d_no_tasks": "Žiadne otvorené úlohy.",
    # schránky
    "mb_title": "Pripojenie pošty",
    "mb_intro": "Pripojte schránku, kde vám chodia faktúry. VORU ich potom "
                "číta samo, vytiahne sumu, číslo účtu aj termín a pošle vám "
                "prehľad s QR kódom na platbu. Nič neprepisujete ručne.",
    "mb_trust_read": "Iba na čítanie — nič neposielame ani nemažeme",
    "mb_trust_enc": "Heslo šifrované, prístup len pre váš účet",
    "mb_trust_revoke": "Odpojíte kedykoľvek jedným klikom",
    "mb_verify_title": "Najprv potvrďte svoj e-mail",
    "mb_verify_body": "Pripojenie schránky sa odomkne po potvrdení vašej "
                      "e-mailovej adresy — kliknite na odkaz v uvítacom "
                      "e-maile (skontrolujte aj priečinok spam).",
    "mb_verify_btn": "Poslať overovací e-mail znova",
    "mb_connected": "Pripojené schránky",
    "mb_active": "Aktívna",
    "mb_choose": "Ako pripojíte poštu",
    "mb_easiest": "Najjednoduchšie",
    "mb_nopass": "Bez hesla",
    "mb_any_provider": "Ktorýkoľvek e-mail",
    "mb_gmail_title": "Gmail jedným klikom",
    "mb_gmail_body": "Prihlásite sa u Googlu a povolíte VORU čítať poštu — "
                     "žiadne heslá, žiadne nastavovanie. Odporúčané.",
    "mb_gmail_btn": "Pripojiť cez Google",
    "mb_fwd_title": "Preposielanie faktúr",
    "mb_fwd_body": "Nechcete pripájať celú schránku? Faktúry len prepošlite "
                   "(alebo si nastavte pravidlo) na túto adresu a VORU ich "
                   "spracuje rovnako.",
    "mb_fwd_warn": "Adresa je unikátna pre váš účet — nezverejňujte ju.",
    "mb_copy": "Kopírovať", "mb_copied": "Skopírované ✓",
    "mb_imap_title": "Iná schránka",
    "mb_imap_lead": "Webhouse, Websupport, Outlook, firemný e-mail či vlastná "
                    "doména — pripojíte cez IMAP za pár sekúnd.",
    "mb_imap_cta": "Pripojiť schránku",
    "th_name": "Názov", "th_server": "Server", "th_login": "Prihlasovací e-mail",
    "mb_remove": "Odpojiť", "mb_remove_confirm": "Naozaj odpojiť túto schránku?",
    "mb_add_title": "Pripojiť schránku cez IMAP",
    "mb_step_1": "Zadajte prihlasovací e-mail a heslo schránky.",
    "mb_step_2": "Server doplníme podľa vašej adresy sami — nič technické neriešite.",
    "mb_step_3": "Klik na „Overiť a pripojiť“ — hneď overíme, že sa dá pripojiť.",
    "mb_where": "Poskytovateľ (nepovinné)",
    "mb_where_hint": "Vyberte, len ak sme server nedoplnili sami alebo ak sa "
                     "pripojenie nepodarí.",
    "mb_pick": "— vyberte poskytovateľa —",
    "mb_other_provider": "Iný / vlastná doména",
    "mb_name_label": "Pomenovanie (nepovinné)",
    "mb_host_label": "IMAP server",
    "mb_port_label": "Port",
    "mb_user_label": "Prihlasovací e-mail",
    "mb_pass_label": "Heslo schránky (alebo heslo aplikácie)",
    "mb_advanced": "Nastavenie servera (vyplníme automaticky)",
    "mb_guess_hint": "Server sme odhadli podľa vašej domény. Ak sa nepripojí, "
                     "upravte ho v časti „Nastavenie servera“.",
    "mb_sec_label": "Zabezpečenie",
    "mb_sec_ssl": "SSL — bezpečné pripojenie (predvolené)",
    "mb_sec_starttls": "STARTTLS (napr. Proton Bridge)",
    "mb_sec_plain": "bez šifrovania (neodporúčame)",
    "mb_submit": "Overiť a pripojiť",
    "mb_add_help": "Neviete si rady? Napíšte nám na "
                   "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a> "
                   "a pomôžeme vám pripojiť sa.",
    "hint_gmail": "Gmail vyžaduje <b>heslo aplikácie</b> (nie bežné heslo): "
                  "zapnite dvojstupňové overenie a vytvorte si ho na "
                  "<a href='https://myaccount.google.com/apppasswords' "
                  "target='_blank' rel='noopener'>myaccount.google.com/"
                  "apppasswords</a>.",
    "hint_webmail": "Použite celú e-mailovú adresu a heslo schránky (to, čo "
                    "zadávate do webmailu).",
    "hint_m365": "Microsoft 365: ak prihlásenie zlyhá, správca musí povoliť "
                 "IMAP a heslá aplikácií v nastaveniach Microsoft 365.",
    "hint_icloud": "iCloud vyžaduje <b>heslo aplikácie</b>: vytvoríte si ho na "
                   "<a href='https://account.apple.com' target='_blank' "
                   "rel='noopener'>account.apple.com</a> → Prihlásenie a "
                   "zabezpečenie → Heslá aplikácií.",
    "hint_simple": "Použite celú adresu a heslo, ktorým sa prihlasujete.",
    "hint_other": "Server býva <b>mail.vasadomena.sk</b> alebo ho nájdete v "
                  "dokumentácii vášho hostingu pod „IMAP“. Ak si neviete rady, "
                  "napíšte nám na <a href='mailto:obchod@sorbxt.sk'>"
                  "obchod@sorbxt.sk</a> — poradíme.",
    # nastavenia
    "s_account_type": "Typ účtu",
    "s_type_business": "firma / živnostník",
    "s_type_personal": "súkromná osoba",
    "s_type_both": "firma aj súkromne",
    "acct_hint_business": "faktúry, dane, podklady pre účtovníčku",
    "acct_hint_personal": "účty za domácnosť, poistky, pripomienky platieb",
    "acct_hint_both": "jedna schránka — spracujem firemné aj domáce položky",
    "ob_title": "Ešte jedna vec",
    "ob_lead": "Ako budete VORU používať? Podľa toho vám prispôsobíme "
               "prehľad a e-maily — zmeniť sa to dá kedykoľvek v "
               "Nastaveniach.",
    "ob_save": "Pokračovať",
    "s_reminder_to": "Kam posielať prehľady a upozornenia",
    "s_pdf": "Heslá k chráneným PDF (výpisy z banky) — viacero hesiel "
             "oddeľte čiarkou",
    "s_pdf_ph": "napr. rodné číslo alebo heslo z banky",
    "s_pdf_note": "Heslo použijeme výlučne na odomknutie PDF výpisov, aby "
                  "VORU vedelo samo odškrtnúť zaplatené platby. Nikam inam "
                  "sa neposiela.",
    "s_iban": "IBAN vášho účtu (pre hromadný príkaz na úhradu)",
    "s_name": "Názov firmy / meno (objaví sa v príkaze)",
    "s_name_ph": "Moja firma s.r.o.",
    "s_accountant": "E-mail účtovníčky (automatické mesačné podklady)",
    "s_accountant_ph": "uctovnicka@example.com",
    "s_accountant_note": "1. deň v mesiaci pošleme účtovníčke ZIP s faktúrami "
                         "(PDF) a CSV prehľadom platieb za predošlý mesiac. "
                         "Nechajte prázdne, ak to nechcete.",
    "s_remind": "Ranný prehľad platieb (s QR kódmi)",
    "s_workdays": "pracovné dni", "s_daily": "každý deň",
    "s_weekly": "raz týždenne (v piatok, za celý týždeň)", "s_off": "neposielať",
    "s_at": "o {h}:00",
    "s_digest": "Zhrnutie prijatej pošty",
    "s_digest_note": "V piatok príde vždy zhrnutie celého týždňa. E-mail sa "
                     "posiela, len keď je čo povedať.",
    "s_report": "Mesačný report výdavkov (1. deň v mesiaci)",
    "s_tax": "Daňový kalendár — čo sa vás týka",
    "s_tax_note": "VORU pripomenie zákonné termíny (DPH, odvody, preddavky) "
                  "v ranných prehľadoch.",
    "s_save": "Uložiť",
    "s_pw_title": "Zmena hesla",
    "s_pw_ok": "Heslo je zmenené.",
    "s_pw_old": "Súčasné heslo",
    "s_pw_new": "Nové heslo (min. 8 znakov)",
    "s_pw_btn": "Zmeniť heslo",
    "err_pw_old": "Súčasné heslo nesedí.",
    "err_pw_short": "Nové heslo musí mať aspoň 8 znakov.",
    "s_totp_title": "Dvojfaktorové overenie (2FA)",
    "s_totp_on": "<b>Zapnuté.</b> <span class='muted'>Pri prihlásení sa okrem "
                 "hesla vyžaduje kód z autentifikačnej aplikácie.</span>",
    "s_totp_off_pw": "Heslo (na potvrdenie vypnutia)",
    "s_totp_off_btn": "Vypnúť 2FA",
    "s_totp_step1": "1. Do autentifikačnej aplikácie (Google Authenticator, "
                    "Aegis, 1Password…) pridajte tento kľúč:",
    "s_totp_link": "alebo otvorte na telefóne odkaz:",
    "s_totp_add": "pridať do aplikácie",
    "s_totp_step2": "2. Zadajte kód z aplikácie",
    "s_totp_on_btn": "Zapnúť 2FA",
    "s_totp_lead": "Druhá vrstva ochrany účtu: pri prihlásení sa okrem hesla "
                   "vyžaduje kód z aplikácie v telefóne. Odporúčame zapnúť.",
    "err_totp_code": "Kód nesedí — skúste znova.",
    "err_totp_pw": "Heslo nesedí.",
    "s_push_title": "Push notifikácie",
    "s_push_lead": "Ranné upozornenie na čakajúce platby priamo do telefónu — "
                   "funguje po nainštalovaní VORU na plochu (pozri Mobilná "
                   "aplikácia nižšie).",
    "s_push_unsupported": "Tento prehliadač push notifikácie nepodporuje.",
    "s_push_nokeys": "Notifikácie zatiaľ nie sú na tomto serveri dostupné — "
                     "skúste to neskôr.",
    "s_push_on": "Zapnúť notifikácie", "s_push_off": "Vypnúť notifikácie",
    "s_push_active": "Notifikácie sú na tomto zariadení zapnuté.",
    "s_push_denied": "Notifikácie sa nepodarilo zapnúť — povoľte ich pre "
                     "voru.sk v nastaveniach prehliadača a skúste to znova.",
    "s_data_title": "Vaše údaje",
    "s_data_lead": "Kompletný export evidencie (platby, úlohy, denník pošty, "
                   "strážené platnosti — poistky, STK…) ako CSV v ZIP archíve.",
    "s_data_btn": "Stiahnuť export dát",
    "s_del_title": "Zrušenie účtu",
    "s_del_lead": "Nenávratne zmaže účet aj všetky údaje (schránky, platby, "
                  "úlohy, súbory). Ak niečo potrebujete, najprv si stiahnite "
                  "export.",
    "s_del_pw": "Heslo (na potvrdenie)",
    "s_del_btn": "Zmazať účet aj všetky údaje",
    "s_del_confirm": "Naozaj nenávratne zmazať účet aj všetky údaje?",
    "err_del_pw": "Heslo nesedí.",
    "s_app_title": "Mobilná aplikácia",
    "s_app_lead": "VORU si nainštalujete na plochu telefónu — funguje ako "
                  "bežná appka, bez App Store.",
    "s_app_ios": "<b>iPhone:</b> otvorte voru.sk v Safari → tlačidlo Zdieľať "
                 "<span class='muted'>(štvorec so šípkou)</span> → "
                 "<b>Pridať na plochu</b>.",
    "s_app_android": "<b>Android:</b> otvorte voru.sk v Chrome → menu ⋮ → "
                     "<b>Pridať na plochu / Inštalovať aplikáciu</b>.",
    # predplatné
    "b_status": "Stav účtu:",
    "b_active": "aktívne predplatné",
    "b_trial": "skúšobná doba do {date}",
    "b_inactive": "neaktívne",
    "b_pick": "Vyberte si predplatné — platba prebieha bezpečne cez Stripe:",
    "b_monthly": "4,99 € / mesiac",
    "b_yearly": "49 € / rok — 2 mesiace zadarmo",
    "b_auto": "Po zaplatení sa účet aktivuje automaticky do minúty.",
    "b_manual": "Platobná brána sa pripravuje — napíšte nám na "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a> "
                "a aktivujeme vás ručne.",
    "b_thanks": "Ďakujeme, že VORU využívate. Zrušenie predplatného: cez "
                "odkaz v potvrdení od Stripe, alebo nám napíšte na "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a>.",
    "b_ref_title": "Odporučte VORU — mesiac zadarmo",
    "b_ref_lead": "Za každého, kto sa zaregistruje cez váš odkaz, dostanete "
                  "<b>+30 dní</b> služby zadarmo — a nový používateľ "
                  "<b>+14 dní</b> skúšobnej doby navyše.",
    "b_ref_count": "Cez váš odkaz sa už zaregistrovali:",
    # zabudnuté heslo / reset
    "fp_title": "Zabudnuté heslo",
    "fp_lead": "Pošleme vám e-mail s odkazom na nastavenie nového hesla.",
    "fp_email": "E-mail účtu",
    "fp_btn": "Poslať odkaz",
    "fp_back": "Späť na prihlásenie",
    "fp_sent_title": "E-mail odoslaný",
    "fp_sent_body": "Ak účet existuje, poslali sme vám e-mail s odkazom na "
                    "obnovu hesla. Skontrolujte si schránku (aj spam).",
    "rp_title": "Nastavte si nové heslo",
    "rp_pw": "Nové heslo (min. 8 znakov)",
    "rp_btn": "Uložiť heslo",
    "rp_invalid_title": "Neplatný odkaz",
    "rp_invalid_body": "Odkaz na obnovu hesla vypršal alebo je poškodený — "
                       "vyžiadajte si nový.",
    "rp_done_title": "Heslo zmenené",
    "rp_done_body": "Prihláste sa novým heslom.",
    "reset_mail_subject": "VORU — obnova hesla",
    "reset_mail_title": "Obnova hesla",
    "reset_mail_lead": "Nové heslo si nastavíte kliknutím (odkaz platí 2 hodiny):",
    "reset_mail_btn": "Nastaviť nové heslo",
    "reset_mail_ignore": "Ak ste o obnovu nežiadali, e-mail ignorujte.",
    "reset_mail_pre": "Odkaz na nastavenie nového hesla platí 2 hodiny.",
    # overenie e-mailu / systémové stránky
    "v_ok_title": "E-mail overený",
    "v_ok_body": "Ďakujeme, adresa je potvrdená. Schránky aj prehľady sú "
                 "odomknuté.",
    "v_bad_title": "Neplatný odkaz",
    "v_bad_body": "Overovací odkaz je poškodený alebo vypršal. Prihláste sa "
                  "a nechajte si poslať nový.",
    "v_gate_title": "Najprv potvrďte e-mail",
    "v_gate_body": "Pripojenie schránky sa odomkne po potvrdení vašej "
                   "e-mailovej adresy — kliknite na odkaz v uvítacom e-maile. "
                   "Nový odkaz si pošlete tlačidlom v prehľade.",
    "v_gate_cta": "Späť na prehľad",
    "login_cta": "Prihlásiť sa",
    "home_cta": "Prejsť na prehľad",
    # akčné stránky (jednoklik z e-mailu)
    "a_title": "Potvrdenie",
    "a_invalid_title": "Neplatný odkaz",
    "a_invalid_body": "Odkaz je poškodený alebo neúplný. Otvorte ho znova "
                      "z e-mailu, prípadne položku vybavte po prihlásení "
                      "v prehľade.",
    "a_done_title": "Vybavené",
    "a_done_count": ("Ako zaplatenú sme označili {n} platbu.",
                     "Ako zaplatené sme označili {n} platby.",
                     "Ako zaplatených sme označili {n} platieb."),
    "a_done_single": "Podarilo sa {label}.",
    "a_already_title": "Už vybavené",
    "a_already_bulk": "Nebolo čo označiť — buď ste nič nevybrali, alebo sú "
                      "vybrané platby medzičasom zaplatené.",
    "a_already_single": "Položka medzičasom zmenila stav — pravdepodobne ste "
                        "ju už odškrtli, alebo ju spároval výpis z banky.",
    "a_confirm_q": "Naozaj {label}?",
    "a_bulk_q": "Naozaj {label}? Zrušte zaškrtnutie pri platbách, ktoré "
                "ešte nie sú zaplatené.",
    "a_bulk_empty": "Momentálne nemáte žiadne nezaplatené platby.",
    "a_bulk_btn": "Označiť vybrané ako zaplatené",
    "a_no_due": "bez splatnosti",
    "a_yes": "Áno, potvrdiť",
    "a_safe": "Ak ste odkaz neotvorili vy, stránku jednoducho zavrite — nič "
              "sa nestane.",
    "a_label_paid": "označiť platbu ako zaplatenú",
    "a_label_snooze": "odložiť pripomienku o 3 dni",
    "a_label_done": "označiť úlohu ako hotovú",
    "a_label_bulk": "označiť vybrané platby ako zaplatené",
    # SEPA
    "sepa_missing_title": "Chýba váš IBAN",
    "sepa_missing_body": "Do hromadného príkazu treba doplniť IBAN vášho "
                         "účtu, z ktorého sa bude platiť.",
    "sepa_missing_cta": "Doplniť v nastaveniach",
    "sepa_empty_title": "Nie je čo uhradiť",
    "sepa_empty_body": "Žiadna nezaplatená platba s IBANom v EUR.",
    # Gmail OAuth a ďalšie systémové hlášky
    "g_fail_title": "Pripojenie Gmailu sa nepodarilo",
    "g_fail_auth": "Prihlásenie cez Google bolo prerušené alebo vypršalo. "
                   "Skúste to znova.",
    "g_fail_token": "Google nevrátil prístupové údaje. Skúste to znova.",
    "mb_back": "Späť na schránky",
    "mb_conn_fail": "Pripojenie zlyhalo: {err}. Skontrolujte heslo a adresu "
                    "servera, alebo nám napíšte na obchod@sorbxt.sk.",
    "rp_new_btn": "Vyžiadať nový",
    "rp_err": "Skontrolujte, či má nové heslo aspoň 8 znakov. Ak áno, odkaz "
              "už vypršal — vyžiadajte si nový.",
    "s_del_done_title": "Účet zrušený",
    "s_del_done_body": "Váš účet aj všetky údaje sme zmazali. Ďakujeme, "
                       "že ste VORU vyskúšali.",
    "back_btn": "Späť",
    # e-maily o konci skúšobnej doby (posiela webapp/expire.py)
    "trial_mail_subject_warn": "VORU — skúšobná doba končí {date}",
    "trial_mail_subject_end": "VORU — skúšobná doba skončila",
    "trial_mail_warn_title": "Skúšobná doba sa končí",
    "trial_mail_warn_lead": "Vaša skúšobná doba končí {date}. Aby vám VORU "
                            "ďalej strážilo faktúry, platby a termíny, "
                            "aktivujte si predplatné — 4,99 € mesačne alebo "
                            "49 € ročne (2 mesiace zadarmo).",
    "trial_mail_end_title": "Skúšobná doba skončila",
    "trial_mail_end_lead": "Vaša skúšobná doba dnes skončila a služba je "
                           "pozastavená — prehľady a pripomienky sa zatiaľ "
                           "neposielajú. Všetky vaše údaje zostávajú uložené; "
                           "predplatným ich hneď oživíte.",
    "trial_mail_btn": "Aktivovať predplatné",
    "trial_mail_footer": "Otázky? Odpovedzte na tento e-mail.",
    # prihlásenie cez Google
    "g_login_btn": "Pokračovať cez Google",
    "g_login_or": "alebo",
    "g_login_fail_title": "Prihlásenie cez Google zlyhalo",
    "g_login_fail_body": "Skúste to znova alebo použite e-mail a heslo.",
    # jazyk aplikácie + kalendárový feed
    "s_lang": "Jazyk aplikácie a e-mailov",
    "s_cal_title": "Kalendár termínov",
    "s_cal_lead": "Pridajte si tento odkaz do svojho kalendára a splatnosti, "
                  "daňové termíny aj konce platnosti sa vám zobrazia priamo "
                  "v ňom. Odkaz je súkromný — nezverejňujte ho.",
    "s_cal_how": "Google Kalendár: Ostatné kalendáre → + → Z URL adresy. "
                 "Apple Kalendár: Súbor → Nový odber kalendára.",
    "ics_cal_name": "VORU — platby a termíny",
    "ics_pay": "Zaplatiť: {s}",
}


def _load_app_translation(lang: str) -> dict:
    try:
        import importlib

        mod = importlib.import_module(f".translations.{lang}", __package__)
        return mod.APP
    except Exception:
        return {}


for _code, _table in _TABLES.items():
    _table.update(_SK_APP)
    if _code != "sk":
        _table.update(_load_app_translation(_code))
