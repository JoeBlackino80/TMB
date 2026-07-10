"""Preklady verejných stránok webu (registrácia, prihlásenie).

Jazyk sa vyberá parametrom ?lang= (posielajú ho tlačidlá z jazykových
mutácií landing page) a nesie sa skrytým poľom formulára.
"""

LANGS = ("sk", "cs", "pl", "de", "hu", "en")

_SK = {
    "err_login": "Nesprávny e-mail alebo heslo.",
    "err_lockout": "Príliš veľa neúspešných pokusov — skúste znova o 15 minút, alebo si obnovte heslo cez „Zabudli ste heslo?“.",
    "err_totp_expired": "Overenie vypršalo — prihláste sa znova.",
    "err_totp_wrong": "Nesprávny kód — skúste znova.",

    "nav_login": "Prihlásiť sa",
    "nav_try": "Vyskúšať zadarmo",
    "reg_title": "Vytvorte si účet",
    "reg_lead": "VORU stráži vaše faktúry, platby a termíny. 14 dní zadarmo — "
                "bez platobnej karty, potom 4,99 €/mesiac alebo 49 €/rok.",
    "use_as": "Používam VORU ako",
    "opt_business": "firma / živnostník",
    "opt_personal": "súkromná osoba",
    "opt_both": "obidvoje",
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
    "totp_lead": "Zadajte 6-miestny kód z autentifikačnej aplikácie.",
    "totp_code": "Kód",
    "totp_btn": "Overiť",
    "err_consent": "Registrácia vyžaduje súhlas s obchodnými podmienkami "
                   "a spracovaním údajov.",
    "err_invalid": "Zadajte platný e-mail a heslo aspoň 8 znakov.",
    "err_exists": "Účet už existuje — prihláste sa.",
    "err_bot": "Registráciu sa nepodarilo overiť — skúste to znova.",
    "err_expired": "Platnosť formulára vypršala — skúste to znova.",
    "err_ratelimit": "Priveľa registrácií z tejto adresy — skúste to o hodinu, "
                     "alebo nám napíšte na obchod@sorbxt.sk.",
    "err_turnstile": "Overenie, že nie ste robot, zlyhalo — skúste to znova.",
    "err_paused": "Registrácie sú dočasne pozastavené — skúste to neskôr, "
                  "alebo nám napíšte na obchod@sorbxt.sk.",
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
    "opt_both": "obojí",
    "email_label": "Váš e-mail (sem budou chodit přehledy)",
    "password_label": "Heslo (min. 8 znaků)",
    "consent_html": "Souhlasím s <a href='/podmienky' target='_blank'>obchodními "
                    "podmínkami</a> a se zpracováním osobních údajů podle "
                    "<a href='/gdpr' target='_blank'>zásad ochrany údajů</a> "
                    "(včetně zpracování obsahu připojené pošty pro účely služby).",
    "reg_btn": "Registrovat se",
    "have_account": "Máte účet?",
    "sign_in": "Přihlaste se",
    "login_title": "Přihlášení",
    "email": "E-mail",
    "password": "Heslo",
    "login_btn": "Přihlásit se",
    "no_account": "Nemáte účet?",
    "register_link": "Registrujte se",
    "trial_note": "— 14 dní zdarma.",
    "forgot": "Zapomněli jste heslo?",
    "totp_title": "Dvoufaktorové ověření",
    "totp_lead": "Zadejte 6místný kód z autentizační aplikace.",
    "totp_code": "Kód",
    "totp_btn": "Ověřit",
    "err_consent": "Registrace vyžaduje souhlas s obchodními podmínkami "
                   "a zpracováním údajů.",
    "err_invalid": "Zadejte platný e-mail a heslo alespoň 8 znaků.",
    "err_exists": "Účet už existuje — přihlaste se.",
    "err_bot": "Registraci se nepodařilo ověřit — zkuste to znovu.",
    "err_expired": "Platnost formuláře vypršela — zkuste to znovu.",
    "err_ratelimit": "Příliš mnoho registrací z této adresy — zkuste to za "
                     "hodinu, nebo nám napište na obchod@sorbxt.sk.",
    "err_turnstile": "Ověření, že nejste robot, selhalo — zkuste to znovu.",
    "err_paused": "Registrace jsou dočasně pozastaveny — zkuste to později, "
                  "nebo nám napište na obchod@sorbxt.sk.",
}

_PL = {
    "err_login": "Nieprawidłowy e-mail lub hasło.",
    "err_lockout": "Zbyt wiele nieudanych prób — spróbuj za 15 minut lub odzyskaj hasło przez „Zapomniałeś hasła?”.",
    "err_totp_expired": "Weryfikacja wygasła — zaloguj się ponownie.",
    "err_totp_wrong": "Nieprawidłowy kod — spróbuj ponownie.",

    "nav_login": "Zaloguj się",
    "nav_try": "Wypróbuj za darmo",
    "reg_title": "Załóż konto",
    "reg_lead": "VORU pilnuje Twoich faktur, płatności i terminów. 14 dni za "
                "darmo — bez karty płatniczej, potem 4,99 €/mies. lub 49 €/rok.",
    "use_as": "Używam VORU jako",
    "opt_business": "firma / działalność",
    "opt_personal": "osoba prywatna",
    "opt_both": "jedno i drugie",
    "email_label": "Twój e-mail (tu będą przychodzić przeglądy)",
    "password_label": "Hasło (min. 8 znaków)",
    "consent_html": "Akceptuję <a href='/podmienky' target='_blank'>regulamin</a> "
                    "i zgadzam się na przetwarzanie danych osobowych zgodnie z "
                    "<a href='/gdpr' target='_blank'>polityką prywatności</a> "
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
    "forgot": "Zapomniałeś hasła?",
    "totp_title": "Weryfikacja dwuetapowa",
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
    "opt_both": "beides",
    "email_label": "Ihre E-Mail (hierhin kommen die Übersichten)",
    "password_label": "Passwort (min. 8 Zeichen)",
    "consent_html": "Ich stimme den <a href='/podmienky' target='_blank'>AGB</a> "
                    "und der Verarbeitung personenbezogener Daten gemäß der "
                    "<a href='/gdpr' target='_blank'>Datenschutzerklärung</a> zu "
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
    "opt_both": "mindkettő",
    "email_label": "Az Ön e-mail-címe (ide érkeznek az áttekintések)",
    "password_label": "Jelszó (min. 8 karakter)",
    "consent_html": "Elfogadom az <a href='/podmienky' target='_blank'>ÁSZF-et</a> "
                    "és hozzájárulok a személyes adatok kezeléséhez az "
                    "<a href='/gdpr' target='_blank'>adatvédelmi tájékoztató</a> "
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
}

_EN = {
    "err_login": "Wrong e-mail or password.",
    "err_lockout": "Too many failed attempts — try again in 15 minutes or reset your password via “Forgot your password?”.",
    "err_totp_expired": "Verification expired — please sign in again.",
    "err_totp_wrong": "Wrong code — try again.",

    "nav_login": "Sign in",
    "nav_try": "Try for free",
    "reg_title": "Create your account",
    "reg_lead": "VORU watches your invoices, payments and deadlines. 14 days "
                "free — no credit card, then €4.99/month or €49/year.",
    "use_as": "I'm using VORU as",
    "opt_business": "a business / freelancer",
    "opt_personal": "a private person",
    "opt_both": "both",
    "email_label": "Your e-mail (overviews will arrive here)",
    "password_label": "Password (min. 8 characters)",
    "consent_html": "I agree to the <a href='/podmienky' target='_blank'>terms "
                    "of service</a> and to the processing of personal data "
                    "under the <a href='/gdpr' target='_blank'>privacy "
                    "policy</a> (including processing the contents of the "
                    "connected mailbox for the service).",
    "reg_btn": "Sign up",
    "have_account": "Already have an account?",
    "sign_in": "Sign in",
    "login_title": "Sign in",
    "email": "E-mail",
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
    "err_invalid": "Enter a valid e-mail and a password of at least "
                   "8 characters.",
    "err_exists": "The account already exists — sign in instead.",
    "err_bot": "The registration could not be verified — please try again.",
    "err_expired": "The form has expired — please try again.",
    "err_ratelimit": "Too many registrations from this address — try again in "
                     "an hour or write to us at obchod@sorbxt.sk.",
    "err_turnstile": "The robot check failed — please try again.",
    "err_paused": "Registrations are temporarily paused — try again later or "
                  "write to us at obchod@sorbxt.sk.",
}

_TABLES = {"sk": _SK, "cs": _CS, "pl": _PL, "de": _DE, "hu": _HU, "en": _EN}


def t(lang: str | None) -> dict:
    return _TABLES.get(lang or "sk", _SK)
