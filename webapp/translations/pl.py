# Poľský preklad UI aplikácie

APP = {
    # menu boczne i stopka
    "m_overview": "Przegląd", "m_mailboxes": "Skrzynki",
    "m_settings": "Ustawienia", "m_billing": "Subskrypcja",
    "m_logout": "Wyloguj się",
    "f_terms": "Regulamin", "f_privacy": "Dane osobowe",
    # przegląd
    "d_verify": "Prosimy, potwierdź swój adres e-mail — wysłaliśmy Ci "
                "link. Nic nie przyszło?",
    "d_verify_btn": "Wyślij ponownie",
    "d_paused": "Usługa jest wstrzymana — okres próbny wygasł albo "
                "subskrypcja się skończyła. <a href='/billing'>Aktywuj "
                "subskrypcję</a>.",
    "d_trial": "Okres próbny do <b>{date}</b>. <a href='/billing'>Przejdź na "
               "subskrypcję</a> — 4,99 €/mies. albo 49 €/rok.",
    "d_start_title": "Zacznij od dodania skrzynki",
    "d_start_body": "VORU potrzebuje dostępu do skrzynki, na którą przychodzą "
                    "Twoje faktury.",
    "d_start_btn": "Dodaj skrzynkę",
    "d_demo": "To są <b>dane przykładowe</b>, pokazujące, jak będzie wyglądał "
              "przegląd. Znikną automatycznie po dodaniu skrzynki.",
    "d_demo_btn": "Usuń przykład",
    "d_overdue": "po terminie", "d_unpaid": "niezapłacone",
    "d_this_month": "do zapłaty do końca miesiąca",
    "d_next_month": "w przyszłym miesiącu",
    "d_open_tasks": "otwarte zadania",
    "d_missing_title": "Regularne faktury, które nie przyszły",
    "d_missing_last": "ostatnia {d}", "d_missing_exp": "oczekiwana do {d}",
    "d_missing_note": "Sprawdź, czy faktura nie utknęła w spamie albo czy "
                      "nie przychodzi na inny adres.",
    "d_payments_title": "Niezapłacone płatności",
    "th_supplier": "Dostawca", "th_amount": "Kwota",
    "th_due": "Termin płatności",
    "d_other_iban": "inny numer konta — sprawdź!", "d_today": "dzisiaj",
    "d_qr_btn": "Płatność QR", "d_paid_btn": "Zapłacone",
    "d_ignore_btn": "Ignoruj", "d_ignore_confirm": "Zignorować tę płatność?",
    "d_qr_alt": "Kod QR do płatności",
    "d_qr_note": "Zeskanuj w aplikacji bankowej — kwota, numer konta i tytuł "
                 "przelewu są wstępnie wypełnione.",
    "d_pay_note": "Kody QR do zapłaty znajdziesz w zestawieniach e-mailowych. "
                  "Zapłacone odhaczy też wyciąg z banku lub odpowiedź na "
                  "e-mail w formie „zapłacone 3” (numer płatności).",
    "d_sepa_btn": "Zbiorcze polecenie przelewu (SEPA XML)",
    "d_sepa_note": "Plik wgrywasz do bankowości internetowej i wszystkie "
                   "przelewy zatwierdzasz naraz.",
    "d_no_payments": "Brak zarejestrowanych niezapłaconych płatności.",
    "d_renewals_title": "Kończy się ważność", "d_done_btn": "Załatwione",
    "d_renewals_note": "Polisy, przeglądy techniczne, domeny i subskrypcje, "
                       "które VORU znalazło w Twojej poczcie. Załatwione "
                       "odhacz, żebyśmy Ci o nich nie przypominali.",
    "d_recv_title": "Należności — faktury, które mają Ci zapłacić",
    "d_recv_customer": "Odbiorca",
    "d_recv_paid_btn": "Zapłacone", "d_recv_ignore_btn": "Usuń",
    "d_recv_ignore_confirm": "Na pewno usunąć tę należność?",
    "d_recv_note": "Faktury, które wystawiłeś i czekasz na zapłatę. Po terminie "
                   "wyróżnimy je i przypomnimy w porannym przeglądzie.",
    "d_recv_add": "Dodaj należność",
    "d_recv_amount": "Kwota (€)", "d_recv_save": "Zapisz",
    "d_recv_hint": "Ręcznie dla faktur, które nie przyjdą e-mailem. Wystawione "
                   "faktury z poczty (np. z programu księgowego) VORU wychwyci samo.",
    "d_tax_title": "Terminy podatkowe (najbliższe 30 dni)",
    "d_bundle_title": "Dokumenty dla księgowości",
    "d_bundle_note": "ZIP z fakturami (PDF) i zestawieniem płatności za "
                     "miesiąc — wyślij księgowej jednym kliknięciem.",
    "d_tasks_title": "Zadania", "d_task_due": "do {d}", "d_task_done": "Gotowe",
    "d_no_tasks": "Brak otwartych zadań.",
    # skrzynki
    "mb_title": "Podłączenie poczty",
    "mb_intro": "Podłącz skrzynkę, na którą przychodzą faktury. VORU sam je "
                "wtedy czyta, wyciąga kwotę, numer konta i termin oraz wysyła "
                "Ci przegląd z kodem QR do zapłaty. Niczego nie przepisujesz "
                "ręcznie.",
    "mb_trust_read": "Tylko do odczytu — nic nie wysyłamy ani nie kasujemy",
    "mb_trust_enc": "Hasło szyfrowane, dostęp tylko dla Twojego konta",
    "mb_trust_revoke": "Odłączysz w każdej chwili jednym kliknięciem",
    "mb_verify_title": "Najpierw potwierdź swój e-mail",
    "mb_verify_body": "Podłączenie skrzynki odblokuje się po potwierdzeniu "
                      "Twojego adresu e-mail — kliknij link w e-mailu "
                      "powitalnym (sprawdź też folder spam).",
    "mb_verify_btn": "Wyślij e-mail weryfikacyjny ponownie",
    "mb_connected": "Podłączone skrzynki",
    "mb_active": "Aktywna",
    "mb_choose": "Jak podłączysz pocztę",
    "mb_easiest": "Najprościej",
    "mb_nopass": "Bez hasła",
    "mb_any_provider": "Dowolny e-mail",
    "mb_gmail_title": "Gmail jednym kliknięciem",
    "mb_gmail_body": "Logujesz się w Google i pozwalasz VORU czytać pocztę — "
                     "bez haseł, bez ustawień. Zalecane.",
    "mb_gmail_btn": "Podłącz przez Google",
    "mb_fwd_title": "Przekazywanie faktur",
    "mb_fwd_body": "Nie chcesz podłączać całej skrzynki? Faktury po prostu "
                   "przekaż (lub ustaw regułę) na ten adres, a VORU przetworzy "
                   "je tak samo.",
    "mb_fwd_warn": "Adres jest unikalny dla Twojego konta — nie udostępniaj go.",
    "mb_copy": "Kopiuj", "mb_copied": "Skopiowano",
    "mb_imap_title": "Inna skrzynka",
    "mb_imap_lead": "Outlook, poczta firmowa czy własna domena — podłączysz "
                    "przez IMAP w kilka sekund.",
    "mb_imap_cta": "Podłącz skrzynkę",
    "th_name": "Nazwa", "th_server": "Serwer", "th_login": "Login",
    "mb_remove": "Odłącz", "mb_remove_confirm": "Na pewno odłączyć tę skrzynkę?",
    "mb_add_title": "Podłącz skrzynkę przez IMAP",
    "mb_step_1": "Podaj e-mail do logowania i hasło skrzynki.",
    "mb_step_2": "Serwer uzupełnimy sami na podstawie Twojego adresu — nic "
                 "technicznego nie ustawiasz.",
    "mb_step_3": "Kliknij „Zweryfikuj i podłącz“ — od razu sprawdzimy połączenie.",
    "mb_where": "Dostawca (opcjonalnie)",
    "mb_where_hint": "Wybierz tylko, jeśli nie uzupełniliśmy serwera sami lub "
                     "jeśli połączenie się nie uda.",
    "mb_pick": "— wybierz dostawcę —",
    "mb_other_provider": "Inny / własna domena",
    "mb_name_label": "Nazwa (opcjonalnie)",
    "mb_host_label": "Serwer IMAP",
    "mb_port_label": "Port",
    "mb_user_label": "E-mail do logowania",
    "mb_pass_label": "Hasło skrzynki (lub hasło aplikacji)",
    "mb_advanced": "Ustawienia serwera (wypełnimy automatycznie)",
    "mb_guess_hint": "Serwer odgadliśmy na podstawie Twojej domeny. Jeśli się nie "
                     "połączy, popraw go w sekcji „Ustawienia serwera“.",
    "mb_sec_label": "Zabezpieczenie",
    "mb_sec_ssl": "SSL — bezpieczne połączenie (domyślne)",
    "mb_sec_starttls": "STARTTLS (np. Proton Bridge)",
    "mb_sec_plain": "bez szyfrowania (niezalecane)",
    "mb_submit": "Zweryfikuj i podłącz",
    "mb_add_help": "Nie wiesz jak? Napisz do nas na "
                   "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a> "
                   "i pomożemy Ci się podłączyć.",
    "hint_gmail": "Gmail wymaga <b>hasła aplikacji</b> (nie zwykłego hasła): "
                  "włącz weryfikację dwuetapową i utwórz je na "
                  "<a href='https://myaccount.google.com/apppasswords' "
                  "target='_blank' rel='noopener'>myaccount.google.com/"
                  "apppasswords</a>.",
    "hint_webmail": "Użyj pełnego adresu e-mail i hasła do skrzynki (tego, "
                    "którym logujesz się do webmaila).",
    "hint_m365": "Microsoft 365: jeśli logowanie się nie powiedzie, "
                 "administrator musi włączyć IMAP i hasła aplikacji w "
                 "ustawieniach Microsoft 365.",
    "hint_icloud": "iCloud wymaga <b>hasła aplikacji</b>: utworzysz je na "
                   "<a href='https://account.apple.com' target='_blank' "
                   "rel='noopener'>account.apple.com</a> → Logowanie i "
                   "zabezpieczenia → Hasła aplikacji.",
    "hint_simple": "Użyj pełnego adresu i hasła, którym się logujesz.",
    "hint_other": "Serwer to zwykle <b>mail.twojadomena.pl</b> albo znajdziesz "
                  "go w dokumentacji swojego hostingu pod hasłem „IMAP”. "
                  "Jeśli nie wiesz, jak dalej, napisz do nas na "
                  "<a href='mailto:obchod@sorbxt.sk'>"
                  "obchod@sorbxt.sk</a> — doradzimy.",
    # ustawienia
    "s_account_type": "Typ konta",
    "s_type_business": "firma / działalność gospodarcza",
    "s_type_personal": "osoba prywatna",
    "s_type_both": "jedno i drugie — firma i prywatnie",
    "s_reminder_to": "Dokąd wysyłać zestawienia i powiadomienia",
    "s_pdf": "Hasła do chronionych PDF (wyciągi z banku) — kilka oddziel "
             "przecinkiem",
    "s_pdf_ph": "np. PESEL albo hasło z banku",
    "s_pdf_note": "Hasło jest używane tylko lokalnie do odblokowania wyciągów "
                  "PDF, żeby VORU samo odhaczało zapłacone płatności.",
    "s_iban": "IBAN Twojego konta (do zbiorczego polecenia przelewu)",
    "s_name": "Nazwa firmy / imię i nazwisko (pojawi się w poleceniu)",
    "s_name_ph": "Moja firma sp. z o.o.",
    "s_accountant": "E-mail księgowej (automatyczne miesięczne dokumenty)",
    "s_accountant_ph": "ksiegowa@example.com",
    "s_accountant_note": "1. dnia miesiąca wyślemy księgowej ZIP z fakturami "
                         "(PDF) i zestawieniem CSV płatności za poprzedni "
                         "miesiąc. Zostaw puste, jeśli tego nie chcesz.",
    "s_remind": "Poranne zestawienie płatności (z danymi do przelewu)",
    "s_workdays": "dni robocze", "s_daily": "codziennie",
    "s_weekly": "tylko w piątek (podsumowanie tygodnia)", "s_off": "nie wysyłaj",
    "s_at": "o {h}:00",
    "s_digest": "Podsumowanie odebranej poczty",
    "s_digest_note": "W piątek zawsze przychodzi podsumowanie całego "
                     "tygodnia. E-mail jest wysyłany tylko wtedy, gdy jest "
                     "o czym pisać.",
    "s_report": "Miesięczny raport wydatków (1. dzień miesiąca)",
    "s_tax": "Kalendarz podatkowy — co Cię dotyczy",
    "s_tax_note": "VORU przypomni o ustawowych terminach (VAT, składki, "
                  "zaliczki) w porannych zestawieniach.",
    "s_save": "Zapisz",
    "s_pw_title": "Zmiana hasła",
    "s_pw_ok": "Hasło zostało zmienione.",
    "s_pw_old": "Obecne hasło",
    "s_pw_new": "Nowe hasło (min. 8 znaków)",
    "s_pw_btn": "Zmień hasło",
    "err_pw_old": "Obecne hasło się nie zgadza.",
    "err_pw_short": "Nowe hasło musi mieć co najmniej 8 znaków.",
    "s_totp_title": "Weryfikacja dwuskładnikowa (2FA)",
    "s_totp_on": "<b>Włączona.</b> <span class='muted'>Przy logowaniu oprócz "
                 "hasła wymagany jest kod z aplikacji "
                 "uwierzytelniającej.</span>",
    "s_totp_off_pw": "Hasło (do potwierdzenia wyłączenia)",
    "s_totp_off_btn": "Wyłącz 2FA",
    "s_totp_step1": "1. Do aplikacji uwierzytelniającej (Google Authenticator, "
                    "Aegis, 1Password…) dodaj ten klucz:",
    "s_totp_link": "albo otwórz na telefonie link:",
    "s_totp_add": "dodaj do aplikacji",
    "s_totp_step2": "2. Wpisz kod z aplikacji",
    "s_totp_on_btn": "Włącz 2FA",
    "s_totp_lead": "Druga warstwa ochrony konta: przy logowaniu oprócz hasła "
                   "wymagany jest kod z aplikacji w telefonie. Zalecamy "
                   "włączenie.",
    "err_totp_code": "Kod się nie zgadza — spróbuj ponownie.",
    "err_totp_pw": "Hasło się nie zgadza.",
    "s_push_title": "Powiadomienia push",
    "s_push_lead": "Poranne powiadomienie o oczekujących płatnościach prosto "
                   "na telefon — działa po zainstalowaniu VORU na ekranie "
                   "głównym (zobacz Aplikacja mobilna poniżej).",
    "s_push_unsupported": "Ta przeglądarka nie obsługuje powiadomień push.",
    "s_push_nokeys": "Serwer nie ma jeszcze skonfigurowanych kluczy "
                     "powiadomień.",
    "s_push_on": "Włącz powiadomienia", "s_push_off": "Wyłącz powiadomienia",
    "s_push_active": "Powiadomienia są włączone na tym urządzeniu.",
    "s_push_denied": "Nie udało się włączyć powiadomień (odmowa uprawnień?).",
    "s_data_title": "Twoje dane",
    "s_data_lead": "Kompletny eksport ewidencji (płatności, zadania, dziennik "
                   "poczty, pilnowanie ważności) jako CSV w archiwum ZIP.",
    "s_data_btn": "Pobierz eksport danych",
    "s_del_title": "Usunięcie konta",
    "s_del_lead": "Nieodwracalnie usuwa konto i wszystkie dane (skrzynki, "
                  "płatności, zadania, pliki). Jeśli czegoś potrzebujesz, "
                  "najpierw pobierz eksport.",
    "s_del_pw": "Hasło (do potwierdzenia)",
    "s_del_btn": "Usuń konto i wszystkie dane",
    "s_del_confirm": "Na pewno nieodwracalnie usunąć konto i wszystkie dane?",
    "err_del_pw": "Hasło się nie zgadza.",
    "s_app_title": "Aplikacja mobilna",
    "s_app_lead": "VORU zainstalujesz na ekranie głównym telefonu — działa "
                  "jak zwykła apka, bez App Store.",
    "s_app_ios": "<b>iPhone:</b> otwórz voru.sk w Safari → przycisk "
                 "Udostępnij <span class='muted'>(kwadrat ze "
                 "strzałką)</span> → <b>Dodaj do ekranu początkowego</b>.",
    "s_app_android": "<b>Android:</b> otwórz voru.sk w Chrome → menu ⋮ → "
                     "<b>Dodaj do ekranu głównego / Zainstaluj aplikację</b>.",
    # subskrypcja
    "b_status": "Stan konta:",
    "b_active": "aktywna subskrypcja",
    "b_trial": "okres próbny do {date}",
    "b_inactive": "brak aktywnej subskrypcji",
    "b_pick": "Wybierz plan — płatność przebiega bezpiecznie przez Stripe:",
    "b_monthly": "4,99 € / miesiąc",
    "b_yearly": "49 € / rok — 2 miesiące gratis",
    "b_auto": "Po zapłacie konto aktywuje się automatycznie w ciągu minuty.",
    "b_manual": "Bramka płatności jest w przygotowaniu — napisz do nas na "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a>, "
                "a aktywujemy Cię ręcznie.",
    "b_thanks": "Dziękujemy, że korzystasz z VORU. Anulowanie subskrypcji: "
                "przez link w potwierdzeniu od Stripe albo napisz do nas na "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a>.",
    "b_ref_title": "Poleć VORU — miesiąc gratis",
    "b_ref_lead": "Za każdego, kto zarejestruje się przez Twój link, "
                  "dostaniesz <b>+30 dni</b> usługi gratis — a nowy "
                  "użytkownik <b>+14 dni</b> okresu próbnego ekstra.",
    "b_ref_count": "Przez Twój link zarejestrowali się już:",
    # zapomniane hasło / reset
    "fp_title": "Zapomniane hasło",
    "fp_lead": "Wyślemy Ci e-mail z linkiem do ustawienia nowego hasła.",
    "fp_email": "E-mail konta",
    "fp_btn": "Wyślij link",
    "fp_back": "Powrót do logowania",
    "fp_sent_title": "E-mail wysłany",
    "fp_sent_body": "Jeśli konto istnieje, wysłaliśmy na nie link do "
                    "odzyskania hasła. Sprawdź skrzynkę (także spam).",
    "rp_title": "Ustaw nowe hasło",
    "rp_pw": "Nowe hasło (min. 8 znaków)",
    "rp_btn": "Zapisz hasło",
    "rp_invalid_title": "Nieprawidłowy link",
    "rp_invalid_body": "Link do odzyskania hasła wygasł albo jest "
                       "uszkodzony — poproś o nowy.",
    "rp_done_title": "Hasło zmienione",
    "rp_done_body": "Zaloguj się nowym hasłem.",
    "reset_mail_subject": "VORU — odzyskanie hasła",
    "reset_mail_title": "Odzyskanie hasła",
    "reset_mail_lead": "Nowe hasło ustawisz jednym kliknięciem (link jest "
                       "ważny 2 godziny):",
    "reset_mail_btn": "Ustaw nowe hasło",
    "reset_mail_ignore": "Jeśli to nie Ty prosisz o odzyskanie hasła, "
                         "zignoruj ten e-mail.",
    "reset_mail_pre": "Link do ustawienia nowego hasła jest ważny 2 godziny.",
    # weryfikacja e-maila / strony systemowe
    "v_ok_title": "E-mail zweryfikowany",
    "v_ok_body": "Dziękujemy, adres jest potwierdzony. Skrzynki i przeglądy "
                 "są odblokowane.",
    "v_bad_title": "Nieprawidłowy link",
    "v_bad_body": "Link weryfikacyjny jest uszkodzony albo wygasł. Zaloguj "
                  "się i poproś o nowy.",
    "v_gate_title": "Najpierw potwierdź e-mail",
    "v_gate_body": "Podłączenie skrzynki odblokuje się po potwierdzeniu "
                   "Twojego adresu e-mail — kliknij link w e-mailu "
                   "powitalnym. Nowy link wyślesz sobie przyciskiem na "
                   "przeglądzie.",
    "v_gate_cta": "Powrót do przeglądu",
    "login_cta": "Zaloguj się",
    "home_cta": "Przejdź do przeglądu",
    # strony akcji (jedno kliknięcie z e-maila)
    "a_title": "Potwierdzenie",
    "a_invalid_title": "Nieprawidłowy link",
    "a_invalid_body": "Link jest uszkodzony albo niekompletny. Otwórz go "
                      "ponownie z e-maila, ewentualnie załatw pozycję po "
                      "zalogowaniu w przeglądzie.",
    "a_done_title": "Załatwione",
    "a_done_count": ("Oznaczyliśmy {n} płatność jako zapłaconą.",
                     "Oznaczyliśmy {n} płatności jako zapłacone.",
                     "Oznaczyliśmy {n} płatności jako zapłacone."),
    "a_done_single": "Udało się {label}.",
    "a_already_title": "Już załatwione",
    "a_already_bulk": "Nie było czego oznaczyć — albo nic nie wybrano, albo "
                      "wybrane płatności zostały w międzyczasie zapłacone.",
    "a_already_single": "Pozycja w międzyczasie zmieniła stan — "
                        "prawdopodobnie została już odhaczona albo sparował "
                        "ją wyciąg z banku.",
    "a_confirm_q": "Na pewno {label}?",
    "a_bulk_q": "Na pewno {label}? Odznacz płatności, które nie są jeszcze "
                "zapłacone.",
    "a_bulk_empty": "Obecnie nie masz żadnych niezapłaconych płatności.",
    "a_bulk_btn": "Oznacz wybrane jako zapłacone",
    "a_no_due": "bez terminu płatności",
    "a_yes": "Tak, potwierdź",
    "a_safe": "Jeśli to nie Ty otwierasz ten link, po prostu zamknij "
              "stronę — nic się nie stanie.",
    "a_label_paid": "oznaczyć płatność jako zapłaconą",
    "a_label_snooze": "odłożyć przypomnienie o 3 dni",
    "a_label_done": "oznaczyć zadanie jako wykonane",
    "a_label_bulk": "oznaczyć wybrane płatności jako zapłacone",
    # SEPA
    "sepa_missing_title": "Brakuje Twojego IBAN-u",
    "sepa_missing_body": "W zbiorczym poleceniu przelewu trzeba uzupełnić "
                         "IBAN Twojego konta, z którego będą wykonywane "
                         "płatności.",
    "sepa_missing_cta": "Uzupełnij w ustawieniach",
}

# kľúče doplnené po prvom preklade (systémové hlášky)
APP.update({
    "sepa_empty_title": "Nie ma nic do zapłaty",
    "sepa_empty_body": "Brak niezapłaconej płatności z IBAN-em w EUR.",
    "g_fail_title": "Połączenie z Gmailem nie powiodło się",
    "g_fail_auth": "Logowanie Google zostało przerwane lub wygasło. "
                   "Spróbuj ponownie.",
    "g_fail_token": "Google nie zwrócił danych dostępowych. Spróbuj ponownie.",
    "mb_back": "Wróć do skrzynek",
    "mb_conn_fail": "Połączenie nie powiodło się: {err}",
    "rp_new_btn": "Poproś o nowy",
    "rp_err": "Link wygasł albo hasło jest krótsze niż 8 znaków.",
    "s_del_done_title": "Konto usunięte",
    "s_del_done_body": "Usunęliśmy Twoje konto i wszystkie dane. "
                       "Dziękujemy za wypróbowanie VORU.",
})
APP["back_btn"] = "Wstecz"

# e-maile o końcu okresu próbnego
APP.update({
    "trial_mail_subject_warn": "VORU — okres próbny kończy się {date}",
    "trial_mail_subject_end": "VORU — okres próbny dobiegł końca",
    "trial_mail_warn_title": "Okres próbny dobiega końca",
    "trial_mail_warn_lead": "Twój okres próbny kończy się {date}. Aby VORU "
                            "dalej pilnowało Twoich faktur, płatności i "
                            "terminów, aktywuj subskrypcję — 4,99 € miesięcznie "
                            "lub 49 € rocznie (2 miesiące gratis).",
    "trial_mail_end_title": "Okres próbny dobiegł końca",
    "trial_mail_end_lead": "Twój okres próbny dziś się zakończył i usługa jest "
                           "wstrzymana — zestawienia i przypomnienia nie są na "
                           "razie wysyłane. Wszystkie Twoje dane pozostają "
                           "zapisane; subskrypcja od razu je przywróci.",
    "trial_mail_btn": "Aktywuj subskrypcję",
    "trial_mail_footer": "Pytania? Odpowiedz na ten e-mail.",
})

# język aplikacji + kanał kalendarza
APP.update({
    "s_lang": "Język aplikacji i e-maili",
    "s_cal_title": "Kalendarz terminów",
    "s_cal_lead": "Dodaj ten link do swojego kalendarza, a terminy płatności, "
                  "terminy podatkowe i końce ważności pojawią się bezpośrednio "
                  "w nim. Link jest prywatny — nie udostępniaj go.",
    "s_cal_how": "Kalendarz Google: Inne kalendarze → + → Z adresu URL. "
                 "Kalendarz Apple: Plik → Nowa subskrypcja kalendarza.",
    "ics_cal_name": "VORU — płatności i terminy",
    "ics_pay": "Zapłać: {s}",
})

# prihlásenie cez Google
APP.update({
    "g_login_btn": "Kontynuuj przez Google",
    "g_login_or": "lub",
    "g_login_fail_title": "Logowanie przez Google nie powiodło się",
    "g_login_fail_body": "Spróbuj ponownie lub użyj e-maila i hasła.",
})

# popisky k typom účtu
APP.update({
    "acct_hint_business": "faktury, podatki, dokumenty dla księgowej",
    "acct_hint_personal": "rachunki domowe, ubezpieczenia, przypomnienia o płatnościach",
    "acct_hint_both": "jedna skrzynka — obsłużę pozycje firmowe i domowe",
})

# uvítacia obrazovka (onboarding)
APP.update({
    "ob_title": "Jeszcze jedno",
    "ob_lead": "Jak będziesz korzystać z VORU? Dopasujemy do tego przegląd i e-maile — zmienisz to w każdej chwili w Ustawieniach.",
    "ob_save": "Kontynuuj",
})

# + Pridať termín
APP.update({
    "d_add_deadline": "Dodaj termin", "d_add_kind": "Typ", "d_add_date": "Ważne do",
    "d_add_note": "Opis (np. numer rej.)", "d_add_save": "Dodaj", "d_add_hint": "Dla zakupu bez e-maila (winieta na stacji, papierowy przegląd…). Resztę VORU wychwyci z poczty sam.",
    "k_pzp": "OC pojazdu", "k_havarijne": "Ubezpieczenie AC", "k_stk": "Przegląd techniczny", "k_ek": "Badanie emisji",
    "k_znamka": "Winieta autostradowa", "k_poistka": "Polisa", "k_ine": "Inny termin",
})
