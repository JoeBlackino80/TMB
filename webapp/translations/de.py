# Deutsche Übersetzung der VORU-App-Oberfläche (formelles Sie).
# Quelle der Wahrheit: _SK_APP in webapp/webi18n.py — gleiche Schlüssel.

APP = {
    # Seitenmenü und Fußzeile
    "m_overview": "Übersicht", "m_mailboxes": "Postfächer",
    "m_settings": "Einstellungen", "m_billing": "Abonnement",
    "m_logout": "Abmelden",
    "f_terms": "AGB", "f_privacy": "Datenschutz",
    # Übersicht
    "d_verify": "Bitte bestätigen Sie Ihre E-Mail-Adresse — wir haben Ihnen "
                "einen Link geschickt. Nichts erhalten?",
    "d_verify_btn": "Erneut senden",
    "d_paused": "Der Dienst ist pausiert — die Testphase ist abgelaufen oder "
                "das Abonnement ist beendet. <a href='/billing'>Aktivieren "
                "Sie ein Abonnement</a>.",
    "d_trial": "Testphase bis <b>{date}</b>. <a href='/billing'>Zum "
               "Abonnement wechseln</a> — 4,99 €/Monat oder 49 €/Jahr.",
    "d_start_title": "Beginnen Sie mit dem Hinzufügen eines Postfachs",
    "d_start_body": "VORU benötigt Zugriff auf das Postfach, in dem Ihre "
                    "Rechnungen eingehen.",
    "d_start_btn": "Postfach hinzufügen",
    "d_demo": "Dies sind <b>Beispieldaten</b>, damit Sie sehen, wie die "
              "Übersicht aussehen wird. Sie verschwinden automatisch, sobald "
              "Sie ein Postfach hinzufügen.",
    "d_demo_btn": "Beispiel löschen",
    "d_overdue": "überfällig", "d_unpaid": "unbezahlt",
    "d_this_month": "fällig bis Monatsende", "d_next_month": "nächster Monat",
    "d_open_tasks": "offene Aufgaben",
    "d_missing_title": "Regelmäßige Rechnungen, die nicht eingegangen sind",
    "d_missing_last": "zuletzt {d}", "d_missing_exp": "erwartet bis {d}",
    "d_missing_note": "Prüfen Sie, ob die Rechnung im Spam gelandet ist oder "
                      "an eine andere Adresse geschickt wird.",
    "d_payments_title": "Unbezahlte Zahlungen",
    "th_supplier": "Lieferant", "th_amount": "Betrag", "th_due": "Fälligkeit",
    "d_other_iban": "andere IBAN — prüfen!", "d_today": "heute",
    "d_qr_btn": "QR-Zahlung", "d_paid_btn": "Bezahlt",
    "d_ignore_btn": "Ignorieren", "d_ignore_confirm": "Diese Zahlung ignorieren?",
    "d_qr_alt": "QR-Code für die Zahlung",
    "d_qr_note": "Scannen Sie den Code in Ihrer Banking-App — Betrag, IBAN "
                 "und Zahlungsreferenz sind vorausgefüllt.",
    "d_pay_note": "QR-Codes zum Bezahlen finden Sie in den E-Mail-"
                  "Übersichten. Zahlungen werden auch per Kontoauszug "
                  "abgehakt — oder per Antwort „bezahlt 3“ (Nummer der "
                  "Zahlung) auf die E-Mail.",
    "d_sepa_btn": "Sammelüberweisung (SEPA XML)",
    "d_sepa_note": "Die Datei laden Sie in Ihr Online-Banking hoch und "
                   "bestätigen alle Überweisungen auf einmal.",
    "d_no_payments": "Keine erfassten unbezahlten Zahlungen.",
    "d_renewals_title": "Läuft ab", "d_done_btn": "Erledigt",
    "d_renewals_note": "Versicherungen, §57a-Begutachtung („Pickerl“), "
                       "Domains und Abonnements, "
                       "die VORU in Ihrer Post gefunden hat. Haken Sie "
                       "Erledigtes ab, damit wir Sie nicht mehr daran "
                       "erinnern.",
    "d_recv_title": "Forderungen — Rechnungen, die man Ihnen schuldet",
    "d_recv_customer": "Kunde",
    "d_recv_paid_btn": "Bezahlt", "d_recv_ignore_btn": "Entfernen",
    "d_recv_ignore_confirm": "Diese Forderung wirklich entfernen?",
    "d_recv_note": "Rechnungen, die Sie gestellt haben und auf Zahlung warten. "
                   "Überfällige heben wir hervor und erinnern im Morgenüberblick.",
    "d_recv_add": "Forderung hinzufügen",
    "d_recv_amount": "Betrag (€)", "d_recv_save": "Speichern",
    "d_recv_hint": "Manuell für Rechnungen, die nicht per E-Mail kommen. "
                   "Ausgestellte Rechnungen aus der Post (z. B. aus der "
                   "Buchhaltungssoftware) erkennt VORU auch selbst.",
    "d_tax_title": "Steuertermine (nächste 30 Tage)",
    "d_bundle_title": "Unterlagen für die Buchhaltung",
    "d_bundle_note": "ZIP mit Rechnungen (PDF) und der Zahlungsübersicht des "
                     "Monats — senden Sie es Ihrer Buchhaltung mit einem "
                     "Klick.",
    "d_tasks_title": "Aufgaben", "d_task_due": "bis {d}", "d_task_done": "Fertig",
    "d_no_tasks": "Keine offenen Aufgaben.",
    # Postfächer
    "mb_title": "E-Mail verbinden",
    "mb_intro": "Verbinden Sie das Postfach, in dem Ihre Rechnungen ankommen. "
                "VORU liest sie dann selbst, entnimmt Betrag, Kontonummer und "
                "Termin und schickt Ihnen eine Übersicht mit QR-Code zur "
                "Zahlung. Sie tippen nichts mehr ab.",
    "mb_trust_read": "Nur Lesezugriff — wir senden und löschen nichts",
    "mb_trust_enc": "Passwort verschlüsselt, Zugriff nur für Ihr Konto",
    "mb_trust_revoke": "Jederzeit mit einem Klick trennen",
    "mb_verify_title": "Bestätigen Sie zuerst Ihre E-Mail",
    "mb_verify_body": "Das Verbinden eines Postfachs wird nach der "
                      "Bestätigung Ihrer E-Mail-Adresse freigeschaltet — "
                      "klicken Sie auf den Link in der Willkommens-E-Mail "
                      "(prüfen Sie auch den Spam-Ordner).",
    "mb_verify_btn": "Bestätigungs-E-Mail erneut senden",
    "mb_connected": "Verbundene Postfächer",
    "mb_active": "Aktiv",
    "mb_choose": "So verbinden Sie Ihre E-Mail",
    "mb_easiest": "Am einfachsten",
    "mb_nopass": "Ohne Passwort",
    "mb_any_provider": "Jede E-Mail",
    "mb_gmail_title": "Gmail mit einem Klick",
    "mb_gmail_body": "Sie melden sich bei Google an und erlauben VORU das "
                     "Lesen der Post — keine Passwörter, keine Einrichtung. "
                     "Empfohlen.",
    "mb_gmail_btn": "Mit Google verbinden",
    "mb_fwd_title": "Rechnungen weiterleiten",
    "mb_fwd_body": "Sie möchten nicht das ganze Postfach verbinden? Leiten Sie "
                   "Rechnungen einfach an diese Adresse weiter (oder per Regel) "
                   "und VORU verarbeitet sie genauso.",
    "mb_fwd_warn": "Die Adresse ist für Ihr Konto einzigartig — geben Sie sie "
                   "nicht weiter.",
    "mb_copy": "Kopieren", "mb_copied": "Kopiert ✓",
    "mb_imap_title": "Anderes Postfach",
    "mb_imap_lead": "Outlook, Firmen-E-Mail oder eigene Domain — in wenigen "
                    "Sekunden über IMAP verbunden.",
    "mb_imap_cta": "Postfach verbinden",
    "th_name": "Name", "th_server": "Server", "th_login": "Anmeldung",
    "mb_remove": "Trennen", "mb_remove_confirm": "Dieses Postfach wirklich trennen?",
    "mb_add_title": "Postfach über IMAP verbinden",
    "mb_step_1": "Geben Sie Anmelde-E-Mail und Postfach-Passwort ein.",
    "mb_step_2": "Den Server füllen wir anhand Ihrer Adresse selbst aus — nichts "
                 "Technisches einzustellen.",
    "mb_step_3": "Klick auf „Prüfen und verbinden“ — wir testen sofort.",
    "mb_where": "Anbieter (optional)",
    "mb_where_hint": "Nur wählen, wenn wir den Server nicht selbst ausgefüllt "
                     "haben oder die Verbindung nicht klappt.",
    "mb_pick": "— Anbieter wählen —",
    "mb_other_provider": "Anderer / eigene Domain",
    "mb_name_label": "Bezeichnung (optional)",
    "mb_host_label": "IMAP-Server",
    "mb_port_label": "Port",
    "mb_user_label": "Anmelde-E-Mail",
    "mb_pass_label": "Postfach-Passwort (oder App-Passwort)",
    "mb_advanced": "Servereinstellungen (füllen wir automatisch aus)",
    "mb_guess_hint": "Wir haben den Server anhand Ihrer Domain geschätzt. Klappt "
                     "die Verbindung nicht, passen Sie ihn unter "
                     "„Servereinstellungen“ an.",
    "mb_sec_label": "Sicherheit",
    "mb_sec_ssl": "SSL — sichere Verbindung (Standard)",
    "mb_sec_starttls": "STARTTLS (z. B. Proton Bridge)",
    "mb_sec_plain": "ohne Verschlüsselung (nicht empfohlen)",
    "mb_submit": "Prüfen und verbinden",
    "mb_add_help": "Sie kommen nicht weiter? Schreiben Sie uns an "
                   "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a> "
                   "und wir helfen Ihnen beim Verbinden.",
    "hint_gmail": "Gmail erfordert ein <b>App-Passwort</b> (nicht das "
                  "normale Passwort): Aktivieren Sie die Bestätigung in zwei "
                  "Schritten und erstellen Sie es auf "
                  "<a href='https://myaccount.google.com/apppasswords' "
                  "target='_blank' rel='noopener'>myaccount.google.com/"
                  "apppasswords</a>.",
    "hint_webmail": "Verwenden Sie die vollständige E-Mail-Adresse und das "
                    "Postfach-Passwort (das, was Sie im Webmail eingeben).",
    "hint_m365": "Microsoft 365: Wenn die Anmeldung fehlschlägt, muss der "
                 "Administrator IMAP und App-Passwörter in den "
                 "Microsoft-365-Einstellungen erlauben.",
    "hint_icloud": "iCloud erfordert ein <b>App-Passwort</b>: Sie erstellen "
                   "es auf <a href='https://account.apple.com' "
                   "target='_blank' rel='noopener'>account.apple.com</a> → "
                   "Anmeldung und Sicherheit → App-Passwörter.",
    "hint_simple": "Verwenden Sie die vollständige Adresse und das Passwort, "
                   "mit dem Sie sich anmelden.",
    "hint_other": "Der Server heißt meist <b>mail.ihredomain.at</b> oder Sie "
                  "finden ihn in der Dokumentation Ihres Hostings unter "
                  "„IMAP“. Wenn Sie nicht weiterwissen, schreiben Sie uns an "
                  "<a href='mailto:obchod@sorbxt.sk'>"
                  "obchod@sorbxt.sk</a> — wir helfen gern.",
    # Einstellungen
    "s_account_type": "Kontotyp",
    "s_type_business": "Firma / Selbstständige(r)",
    "s_type_personal": "Privatperson",
    "s_type_both": "beides — Firma und privat",
    "s_reminder_to": "Wohin sollen Übersichten und Benachrichtigungen "
                     "gesendet werden",
    "s_pdf": "Passwörter für geschützte PDF (Kontoauszüge) — mehrere durch "
             "Komma trennen",
    "s_pdf_ph": "z. B. Geburtsdatum oder das von der Bank vergebene Passwort",
    "s_pdf_note": "Das Passwort wird nur lokal zum Entsperren der "
                  "PDF-Auszüge verwendet, damit VORU bezahlte Zahlungen "
                  "selbst abhaken kann.",
    "s_iban": "IBAN Ihres Kontos (für die Sammelüberweisung)",
    "s_name": "Firmenname / Name (erscheint im Zahlungsauftrag)",
    "s_name_ph": "Meine Firma GmbH",
    "s_accountant": "E-Mail der Buchhaltung (automatische Monatsunterlagen)",
    "s_accountant_ph": "buchhaltung@example.com",
    "s_accountant_note": "Am 1. des Monats senden wir der Buchhaltung ein ZIP "
                         "mit Rechnungen (PDF) und einer CSV-Zahlungsübersicht "
                         "des Vormonats. Leer lassen, wenn nicht gewünscht.",
    "s_remind": "Morgendliche Zahlungsübersicht (mit QR-Codes)",
    "s_workdays": "Werktage", "s_daily": "jeden Tag",
    "s_weekly": "nur freitags (für die Woche)", "s_off": "nicht senden",
    "s_at": "um {h}:00",
    "s_digest": "Zusammenfassung der eingegangenen Post",
    "s_digest_note": "Am Freitag kommt immer eine Zusammenfassung der ganzen "
                     "Woche. Die E-Mail wird nur gesendet, wenn es etwas zu "
                     "berichten gibt.",
    "s_report": "Monatlicher Ausgabenbericht (am 1. des Monats)",
    "s_tax": "Steuerkalender — was Sie betrifft",
    "s_tax_note": "VORU erinnert in den morgendlichen Übersichten an "
                  "gesetzliche Termine (USt., SVS-Beiträge, "
                  "Vorauszahlungen).",
    "s_save": "Speichern",
    "s_pw_title": "Passwort ändern",
    "s_pw_ok": "Das Passwort wurde geändert.",
    "s_pw_old": "Aktuelles Passwort",
    "s_pw_new": "Neues Passwort (mind. 8 Zeichen)",
    "s_pw_btn": "Passwort ändern",
    "err_pw_old": "Das aktuelle Passwort stimmt nicht.",
    "err_pw_short": "Das neue Passwort muss mindestens 8 Zeichen haben.",
    "s_totp_title": "Zwei-Faktor-Authentifizierung (2FA)",
    "s_totp_on": "<b>Aktiviert.</b> <span class='muted'>Bei der Anmeldung "
                 "wird zusätzlich zum Passwort ein Code aus der "
                 "Authentifizierungs-App verlangt.</span>",
    "s_totp_off_pw": "Passwort (zur Bestätigung der Deaktivierung)",
    "s_totp_off_btn": "2FA deaktivieren",
    "s_totp_step1": "1. Fügen Sie diesen Schlüssel in Ihre "
                    "Authentifizierungs-App (Google Authenticator, Aegis, "
                    "1Password…) ein:",
    "s_totp_link": "oder öffnen Sie auf dem Telefon den Link:",
    "s_totp_add": "zur App hinzufügen",
    "s_totp_step2": "2. Geben Sie den Code aus der App ein",
    "s_totp_on_btn": "2FA aktivieren",
    "s_totp_lead": "Eine zweite Schutzebene für Ihr Konto: Bei der Anmeldung "
                   "wird zusätzlich zum Passwort ein Code aus der App auf "
                   "Ihrem Telefon verlangt. Wir empfehlen, sie zu "
                   "aktivieren.",
    "err_totp_code": "Der Code stimmt nicht — versuchen Sie es erneut.",
    "err_totp_pw": "Das Passwort stimmt nicht.",
    "s_push_title": "Push-Benachrichtigungen",
    "s_push_lead": "Morgendliche Erinnerung an ausstehende Zahlungen direkt "
                   "auf Ihr Telefon — funktioniert, nachdem Sie VORU auf dem "
                   "Startbildschirm installiert haben (siehe Mobile App "
                   "unten).",
    "s_push_unsupported": "Dieser Browser unterstützt keine "
                          "Push-Benachrichtigungen.",
    "s_push_nokeys": "Auf dem Server sind noch keine "
                     "Benachrichtigungsschlüssel eingerichtet.",
    "s_push_on": "Benachrichtigungen aktivieren",
    "s_push_off": "Benachrichtigungen deaktivieren",
    "s_push_active": "Benachrichtigungen sind auf diesem Gerät aktiviert.",
    "s_push_denied": "Benachrichtigungen konnten nicht aktiviert werden "
                     "(Berechtigung verweigert?).",
    "s_data_title": "Ihre Daten",
    "s_data_lead": "Vollständiger Export der Aufzeichnungen (Zahlungen, "
                   "Aufgaben, Post-Protokoll, Ablaufüberwachungen) als CSV "
                   "in einem ZIP-Archiv.",
    "s_data_btn": "Datenexport herunterladen",
    "s_del_title": "Konto löschen",
    "s_del_lead": "Löscht unwiderruflich das Konto und alle Daten "
                  "(Postfächer, Zahlungen, Aufgaben, Dateien). Wenn Sie "
                  "etwas benötigen, laden Sie zuerst den Export herunter.",
    "s_del_pw": "Passwort (zur Bestätigung)",
    "s_del_btn": "Konto und alle Daten löschen",
    "s_del_confirm": "Konto und alle Daten wirklich unwiderruflich löschen?",
    "err_del_pw": "Das Passwort stimmt nicht.",
    "s_app_title": "Mobile App",
    "s_app_lead": "Installieren Sie VORU auf dem Startbildschirm Ihres "
                  "Telefons — es funktioniert wie eine normale App, ohne "
                  "App Store.",
    "s_app_ios": "<b>iPhone:</b> öffnen Sie voru.at in Safari → Taste "
                 "„Teilen“ <span class='muted'>(Quadrat mit Pfeil)</span> → "
                 "<b>Zum Home-Bildschirm</b>.",
    "s_app_android": "<b>Android:</b> öffnen Sie voru.at in Chrome → Menü ⋮ → "
                     "<b>Zum Startbildschirm hinzufügen / App "
                     "installieren</b>.",
    # Abonnement
    "b_status": "Kontostatus:",
    "b_active": "aktives Abonnement",
    "b_trial": "Testphase bis {date}",
    "b_inactive": "inaktiv",
    "b_pick": "Wählen Sie einen Plan — die Zahlung erfolgt sicher über "
              "Stripe:",
    "b_monthly": "4,99 € / Monat",
    "b_yearly": "49 € / Jahr — 2 Monate gratis",
    "b_auto": "Nach der Zahlung wird das Konto automatisch innerhalb einer "
              "Minute aktiviert.",
    "b_manual": "Das Zahlungsportal wird gerade vorbereitet — schreiben Sie "
                "uns an <a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a> "
                "und wir aktivieren Sie manuell.",
    "b_thanks": "Danke, dass Sie VORU nutzen. Kündigung des Abonnements: "
                "über den Link in der Bestätigung von Stripe, oder schreiben "
                "Sie uns an "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a>.",
    "b_ref_title": "Empfehlen Sie VORU — ein Monat gratis",
    "b_ref_lead": "Für jede Person, die sich über Ihren Link registriert, "
                  "erhalten Sie <b>30 Tage</b> gratis dazu — und der neue "
                  "Nutzer <b>14 Tage</b> Testzeitraum extra.",
    "b_ref_count": "Über Ihren Link haben sich bereits registriert:",
    # Passwort vergessen / zurücksetzen
    "fp_title": "Passwort vergessen",
    "fp_lead": "Wir senden Ihnen eine E-Mail mit einem Link zum Festlegen "
               "eines neuen Passworts.",
    "fp_email": "Konto-E-Mail",
    "fp_btn": "Link senden",
    "fp_back": "Zurück zur Anmeldung",
    "fp_sent_title": "E-Mail gesendet",
    "fp_sent_body": "Falls das Konto existiert, haben wir einen Link zur "
                    "Passwort-Wiederherstellung dorthin gesendet. Prüfen Sie "
                    "Ihr Postfach (auch den Spam-Ordner).",
    "rp_title": "Legen Sie ein neues Passwort fest",
    "rp_pw": "Neues Passwort (mind. 8 Zeichen)",
    "rp_btn": "Passwort speichern",
    "rp_invalid_title": "Ungültiger Link",
    "rp_invalid_body": "Der Link zur Passwort-Wiederherstellung ist "
                       "abgelaufen oder beschädigt — fordern Sie einen neuen "
                       "an.",
    "rp_done_title": "Passwort geändert",
    "rp_done_body": "Melden Sie sich mit dem neuen Passwort an.",
    "reset_mail_subject": "VORU — Passwort-Wiederherstellung",
    "reset_mail_title": "Passwort-Wiederherstellung",
    "reset_mail_lead": "Ein neues Passwort legen Sie per Klick fest (der "
                       "Link ist 2 Stunden gültig):",
    "reset_mail_btn": "Neues Passwort festlegen",
    "reset_mail_ignore": "Falls Sie keine Wiederherstellung angefordert "
                         "haben, ignorieren Sie diese E-Mail.",
    "reset_mail_pre": "Der Link zum Festlegen eines neuen Passworts ist "
                      "2 Stunden gültig.",
    # E-Mail-Bestätigung / Systemseiten
    "v_ok_title": "E-Mail bestätigt",
    "v_ok_body": "Danke, die Adresse ist bestätigt. Postfächer und "
                 "Übersichten sind freigeschaltet.",
    "v_bad_title": "Ungültiger Link",
    "v_bad_body": "Der Bestätigungslink ist beschädigt oder abgelaufen. "
                  "Melden Sie sich an und lassen Sie sich einen neuen "
                  "senden.",
    "v_gate_title": "Bestätigen Sie zuerst Ihre E-Mail",
    "v_gate_body": "Das Verbinden eines Postfachs wird nach der Bestätigung "
                   "Ihrer E-Mail-Adresse freigeschaltet — klicken Sie auf "
                   "den Link in der Willkommens-E-Mail. Einen neuen Link "
                   "senden Sie sich mit der Schaltfläche in der Übersicht.",
    "v_gate_cta": "Zurück zur Übersicht",
    "login_cta": "Anmelden",
    "home_cta": "Zur Übersicht",
    # Aktionsseiten (Ein-Klick aus der E-Mail)
    "a_title": "Bestätigung",
    "a_invalid_title": "Ungültiger Link",
    "a_invalid_body": "Der Link ist beschädigt oder unvollständig. Öffnen "
                      "Sie ihn erneut aus der E-Mail, oder erledigen Sie den "
                      "Eintrag nach der Anmeldung in der Übersicht.",
    "a_done_title": "Erledigt",
    "a_done_count": ("Wir haben {n} Zahlung als bezahlt markiert.",
                     "Wir haben {n} Zahlungen als bezahlt markiert.",
                     "Wir haben {n} Zahlungen als bezahlt markiert."),
    "a_done_single": "Erledigt: {label}.",
    "a_already_title": "Bereits erledigt",
    "a_already_bulk": "Es gab nichts zu markieren — entweder haben Sie "
                      "nichts ausgewählt, oder die ausgewählten Zahlungen "
                      "wurden inzwischen bezahlt.",
    "a_already_single": "Der Eintrag hat inzwischen den Status geändert — "
                        "wahrscheinlich haben Sie ihn bereits abgehakt, oder "
                        "der Kontoauszug hat ihn zugeordnet.",
    "a_confirm_q": "Wirklich {label}?",
    "a_bulk_q": "Wirklich {label}? Entfernen Sie das Häkchen bei Zahlungen, "
                "die noch nicht bezahlt sind.",
    "a_bulk_empty": "Sie haben derzeit keine unbezahlten Zahlungen.",
    "a_bulk_btn": "Ausgewählte als bezahlt markieren",
    "a_no_due": "ohne Fälligkeit",
    "a_yes": "Ja, bestätigen",
    "a_safe": "Falls nicht Sie den Link geöffnet haben, schließen Sie die "
              "Seite einfach — es passiert nichts.",
    "a_label_paid": "die Zahlung als bezahlt markieren",
    "a_label_snooze": "die Erinnerung um 3 Tage verschieben",
    "a_label_done": "die Aufgabe als erledigt markieren",
    "a_label_bulk": "die ausgewählten Zahlungen als bezahlt markieren",
    # SEPA
    "sepa_missing_title": "Ihre IBAN fehlt",
    "sepa_missing_body": "In der Sammelüberweisung muss die IBAN Ihres "
                         "Kontos ergänzt werden, von dem gezahlt wird.",
    "sepa_missing_cta": "In den Einstellungen ergänzen",
    "sepa_empty_title": "Nichts zu bezahlen",
    "sepa_empty_body": "Keine unbezahlte Zahlung mit IBAN in EUR.",
    # Gmail OAuth und weitere Systemmeldungen
    "g_fail_title": "Die Verbindung mit Gmail ist fehlgeschlagen",
    "g_fail_auth": "Die Google-Anmeldung wurde abgebrochen oder ist "
                   "abgelaufen. Versuchen Sie es erneut.",
    "g_fail_token": "Google hat keine Zugangsdaten zurückgegeben. Versuchen "
                    "Sie es erneut.",
    "mb_back": "Zurück zu den Postfächern",
    "mb_conn_fail": "Verbindung fehlgeschlagen: {err}",
    "rp_new_btn": "Neuen anfordern",
    "rp_err": "Der Link ist abgelaufen oder das Passwort ist kürzer als "
              "8 Zeichen.",
    "s_del_done_title": "Konto gelöscht",
    "s_del_done_body": "Wir haben Ihr Konto und alle Daten gelöscht. Danke, "
                       "dass Sie VORU ausprobiert haben.",
}
APP["back_btn"] = "Zurück"

# E-Mails zum Ende der Testphase
APP.update({
    "trial_mail_subject_warn": "VORU — Testphase endet am {date}",
    "trial_mail_subject_end": "VORU — Testphase beendet",
    "trial_mail_warn_title": "Ihre Testphase endet bald",
    "trial_mail_warn_lead": "Ihre Testphase endet am {date}. Damit VORU Ihre "
                            "Rechnungen, Zahlungen und Termine weiter im Blick "
                            "behält, aktivieren Sie Ihr Abonnement — 4,99 € "
                            "monatlich oder 49 € jährlich (2 Monate gratis).",
    "trial_mail_end_title": "Testphase beendet",
    "trial_mail_end_lead": "Ihre Testphase ist heute abgelaufen und der Dienst "
                           "ist pausiert — Übersichten und Erinnerungen werden "
                           "vorerst nicht gesendet. Alle Ihre Daten bleiben "
                           "gespeichert; mit einem Abonnement geht es sofort "
                           "weiter.",
    "trial_mail_btn": "Abonnement aktivieren",
    "trial_mail_footer": "Fragen? Antworten Sie einfach auf diese E-Mail.",
})

# App-Sprache + Kalender-Feed
APP.update({
    "s_lang": "Sprache der App und E-Mails",
    "s_cal_title": "Terminkalender",
    "s_cal_lead": "Fügen Sie diesen Link zu Ihrem Kalender hinzu — "
                  "Fälligkeiten, Steuertermine und Ablaufdaten erscheinen "
                  "direkt darin. Der Link ist privat — geben Sie ihn nicht "
                  "weiter.",
    "s_cal_how": "Google Kalender: Weitere Kalender → + → Per URL. "
                 "Apple Kalender: Ablage → Neues Kalenderabonnement.",
    "ics_cal_name": "VORU — Zahlungen und Termine",
    "ics_pay": "Bezahlen: {s}",
})

# prihlásenie cez Google
APP.update({
    "g_login_btn": "Mit Google fortfahren",
    "g_login_or": "oder",
    "g_login_fail_title": "Anmeldung über Google fehlgeschlagen",
    "g_login_fail_body": "Versuchen Sie es erneut oder nutzen Sie E-Mail und Passwort.",
})

# popisky k typom účtu
APP.update({
    "acct_hint_business": "Rechnungen, Steuern, Unterlagen für die Buchhaltung",
    "acct_hint_personal": "Haushaltsrechnungen, Versicherungen, Zahlungserinnerungen",
    "acct_hint_both": "ein Postfach — Geschäftliches und Privates zusammen",
})

# uvítacia obrazovka (onboarding)
APP.update({
    "ob_title": "Noch eine Sache",
    "ob_lead": "Wie werden Sie VORU nutzen? Danach richten wir Übersicht und E-Mails aus — jederzeit in den Einstellungen änderbar.",
    "ob_save": "Weiter",
})

# + Pridať termín
APP.update({
    "d_add_deadline": "Termin hinzufügen", "d_add_kind": "Art", "d_add_date": "Gültig bis",
    "d_add_note": "Beschreibung (z. B. Kennzeichen)", "d_add_save": "Hinzufügen", "d_add_hint": "Für Käufe ohne E-Mail (Vignette an der Tankstelle, Papier-Pickerl…). Den Rest erfasst VORU selbst aus der Post.",
    "k_pzp": "Kfz-Haftpflicht", "k_havarijne": "Kaskoversicherung", "k_stk": "§57a-Begutachtung", "k_ek": "Abgasuntersuchung",
    "k_znamka": "Vignette", "k_poistka": "Versicherung", "k_ine": "Sonstiger Termin",
})
