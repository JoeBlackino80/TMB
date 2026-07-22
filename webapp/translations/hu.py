# A VORU alkalmazás felületének magyar fordítása (magázó forma, Ön).
# Az igazság forrása: _SK_APP a webapp/webi18n.py fájlban — azonos kulcsok.

APP = {
    # oldalmenü és lábléc
    "m_overview": "Áttekintés", "m_mailboxes": "Postafiókok",
    "m_settings": "Beállítások", "m_billing": "Előfizetés",
    "m_logout": "Kijelentkezés",
    "f_terms": "Feltételek", "f_privacy": "Adatvédelem",
    # áttekintés
    "d_verify": "Kérjük, erősítse meg az e-mail-címét — küldtünk Önnek egy "
                "linket. Nem érkezett meg semmi?",
    "d_verify_btn": "Újraküldés",
    "d_paused": "A szolgáltatás szünetel — a próbaidőszak lejárt vagy az "
                "előfizetés véget ért. <a href='/billing'>Aktiváljon "
                "előfizetést</a>.",
    "d_trial": "Próbaidőszak vége: <b>{date}</b>. <a href='/billing'>Váltás "
               "előfizetésre</a> — 4,99 €/hó vagy 49 €/év.",
    "d_start_title": "Kezdje egy postafiók hozzáadásával",
    "d_start_body": "A VORU-nak hozzáférésre van szüksége ahhoz a "
                    "postafiókhoz, ahová a számlái érkeznek.",
    "d_start_btn": "Postafiók hozzáadása",
    "d_demo": "Ezek <b>mintaadatok</b>, hogy lássa, hogyan fog kinézni az "
              "áttekintés. Postafiók hozzáadása után automatikusan "
              "eltűnnek.",
    "d_demo_btn": "Minta törlése",
    "d_overdue": "lejárt határidejű", "d_unpaid": "kifizetetlen",
    "d_this_month": "a hónap végéig esedékes", "d_next_month": "jövő hónapban",
    "d_open_tasks": "nyitott feladat",
    "d_missing_title": "Rendszeres számlák, amelyek nem érkeztek meg",
    "d_missing_last": "utolsó: {d}", "d_missing_exp": "várható volt eddig: {d}",
    "d_missing_note": "Ellenőrizze, hogy a számla nem került-e a spam "
                      "mappába, vagy nem másik címre érkezik-e.",
    "d_payments_title": "Kifizetetlen tételek",
    "th_supplier": "Szállító", "th_amount": "Összeg",
    "th_due": "Fizetési határidő",
    "d_other_iban": "eltérő IBAN — ellenőrizze!", "d_today": "ma",
    "d_qr_btn": "QR-fizetés", "d_paid_btn": "Kifizetve",
    "d_ignore_btn": "Mellőzés", "d_ignore_confirm": "Mellőzi ezt a tételt?",
    "d_qr_alt": "QR-kód a fizetéshez",
    "d_qr_note": "Olvassa be a banki alkalmazásában — az összeg, az IBAN és "
                 "a közlemény előre ki van töltve.",
    "d_pay_note": "A fizetéshez szükséges QR-kódokat az e-mail-"
                  "összefoglalókban találja. A kifizetett tételeket a "
                  "bankszámlakivonat vagy az e-mailre küldött "
                  "„fizetve 3” (a tétel száma) válasz is kipipálja.",
    "d_sepa_btn": "Csoportos átutalási megbízás (SEPA XML)",
    "d_sepa_note": "A fájlt feltölti az internetbankba, és az összes "
                   "átutalást egyszerre hagyja jóvá.",
    "d_no_payments": "Nincs nyilvántartott kifizetetlen tétel.",
    "d_renewals_title": "Lejáró érvényesség", "d_done_btn": "Elintézve",
    "d_renewals_note": "Biztosítások, műszaki vizsga, domainek és "
                       "előfizetések, amelyeket a VORU a levelezésében "
                       "talált. Az elintézetteket pipálja ki, hogy ne "
                       "emlékeztessük rájuk.",
    "d_tax_title": "Adóhatáridők (a következő 30 nap)",
    "d_bundle_title": "Könyvelési anyagok",
    "d_bundle_note": "ZIP a számlákkal (PDF) és a havi fizetési "
                     "áttekintéssel — egy kattintással elküldheti a "
                     "könyvelőjének.",
    "d_tasks_title": "Feladatok", "d_task_due": "határidő: {d}",
    "d_task_done": "Kész",
    "d_no_tasks": "Nincs nyitott feladat.",
    # postafiókok
    "mb_title": "E-mail-postafiókok",
    "mb_fwd_title": "Az Ön továbbítási címe",
    "mb_fwd_body": "Nem szeretné megadni a postafiókja jelszavát? Elég a "
                   "számlákat erre a címre továbbítani (kézzel vagy a "
                   "levelezőjében beállított szabállyal), és a VORU "
                   "ugyanúgy feldolgozza őket. A cím az Ön fiókjához "
                   "egyedi — ne tegye közzé.",
    "mb_verify_title": "Először erősítse meg az e-mail-címét",
    "mb_verify_body": "A postafiók csatlakoztatása az e-mail-címe "
                      "megerősítése után válik elérhetővé — kattintson az "
                      "üdvözlő e-mailben található linkre (ellenőrizze a "
                      "spam mappát is).",
    "mb_verify_btn": "Megerősítő e-mail újraküldése",
    "mb_gmail_title": "Gmail egy kattintással",
    "mb_gmail_body": "A Gmailt alkalmazásjelszó nélkül csatlakoztathatja — "
                     "bejelentkezik a Google-nál, és engedélyezi a "
                     "VORU-nak a postafiók olvasását. A hozzáférést "
                     "bármikor visszavonhatja a myaccount.google.com "
                     "oldalon.",
    "mb_gmail_btn": "Gmail csatlakoztatása Google-fiókkal",
    "mb_none": "Még nincs postafiók — adja hozzá az elsőt lent.",
    "th_name": "Név", "th_server": "Szerver", "th_login": "Bejelentkezés",
    "mb_remove": "Eltávolítás",
    "mb_remove_confirm": "Eltávolítja a postafiókot?",
    "mb_add_title": "Postafiók hozzáadása",
    "mb_add_lead": "Válassza ki a szolgáltatót — a szerverbeállításokat "
                   "kitöltjük Ön helyett. A bejelentkezést azonnal "
                   "ellenőrizzük. Részletes útmutató: "
                   "<a href='/navod' target='_blank'>csatlakozási "
                   "útmutató</a>.",
    "mb_where": "Hol van az e-mail-fiókja?",
    "mb_pick": "— válasszon szolgáltatót —",
    "mb_other_provider": "Egyéb / saját domain",
    "mb_name_label": "Név (pl. „cégem”)",
    "mb_host_label": "IMAP-szerver",
    "mb_port_label": "Port",
    "mb_user_label": "Bejelentkezési e-mail",
    "mb_pass_label": "Postafiók jelszava / alkalmazásjelszó",
    "mb_sec_label": "Biztonság",
    "mb_sec_ssl": "SSL (általános, 993-as port)",
    "mb_sec_starttls": "STARTTLS (pl. Proton Bridge)",
    "mb_sec_plain": "titkosítás nélkül",
    "mb_submit": "Ellenőrzés és hozzáadás",
    "hint_gmail": "A Gmailhez <b>alkalmazásjelszó</b> szükséges (nem a "
                  "szokásos jelszó): kapcsolja be a kétlépcsős azonosítást, "
                  "és hozza létre a jelszót itt: "
                  "<a href='https://myaccount.google.com/apppasswords' "
                  "target='_blank' rel='noopener'>myaccount.google.com/"
                  "apppasswords</a>.",
    "hint_webmail": "Használja a teljes e-mail-címet és a postafiók "
                    "jelszavát (amit a webmailbe szokott beírni).",
    "hint_m365": "Microsoft 365: ha a bejelentkezés sikertelen, a "
                 "rendszergazdának engedélyeznie kell az IMAP-ot és az "
                 "alkalmazásjelszavakat a Microsoft 365 beállításaiban.",
    "hint_icloud": "Az iCloudhoz <b>alkalmazásjelszó</b> szükséges: itt "
                   "hozhatja létre: <a href='https://account.apple.com' "
                   "target='_blank' rel='noopener'>account.apple.com</a> → "
                   "Bejelentkezés és biztonság → Alkalmazásjelszavak.",
    "hint_simple": "Használja a teljes címet és a bejelentkezéshez használt "
                   "jelszót.",
    "hint_other": "A szerver általában <b>mail.sajatdomain.hu</b>, vagy "
                  "megtalálja a tárhelyszolgáltató dokumentációjában az "
                  "„IMAP” résznél. Ha elakadt, írjon nekünk: "
                  "<a href='mailto:obchod@sorbxt.sk'>"
                  "obchod@sorbxt.sk</a> — segítünk.",
    # beállítások
    "s_account_type": "Fiók típusa",
    "s_type_business": "cég / egyéni vállalkozó",
    "s_type_personal": "magánszemély",
    "s_type_both": "mindkettő — céges és magán",
    "s_reminder_to": "Hová küldjük az összefoglalókat és értesítéseket",
    "s_pdf": "Védett PDF-ek jelszavai (bankszámlakivonatok) — többet "
             "vesszővel válasszon el",
    "s_pdf_ph": "pl. személyi szám vagy a banktól kapott jelszó",
    "s_pdf_note": "A jelszót csak helyben használjuk a PDF-kivonatok "
                  "feloldásához, hogy a VORU magától kipipálhassa a "
                  "kifizetett tételeket.",
    "s_iban": "Az Ön számlájának IBAN-ja (a csoportos átutalási "
              "megbízáshoz)",
    "s_name": "Cégnév / név (a megbízásban jelenik meg)",
    "s_name_ph": "Az Én Cégem Kft.",
    "s_remind": "Reggeli fizetési összefoglaló (QR-kódokkal)",
    "s_workdays": "munkanapokon", "s_daily": "minden nap",
    "s_weekly": "csak pénteken (az egész hétről)", "s_off": "ne küldje",
    "s_at": "{h}:00-kor",
    "s_digest": "A beérkezett levelek összefoglalója",
    "s_digest_note": "Pénteken mindig az egész hét összefoglalója érkezik. "
                     "Az e-mailt csak akkor küldjük, ha van miről "
                     "beszámolni.",
    "s_report": "Havi kiadási jelentés (a hónap 1. napján)",
    "s_tax": "Adónaptár — ami Önt érinti",
    "s_tax_note": "A VORU a reggeli összefoglalókban emlékeztet a törvényes "
                  "határidőkre (áfa, járulékok, előlegek).",
    "s_save": "Mentés",
    "s_pw_title": "Jelszó módosítása",
    "s_pw_ok": "A jelszó megváltozott.",
    "s_pw_old": "Jelenlegi jelszó",
    "s_pw_new": "Új jelszó (min. 8 karakter)",
    "s_pw_btn": "Jelszó módosítása",
    "err_pw_old": "A jelenlegi jelszó nem egyezik.",
    "err_pw_short": "Az új jelszónak legalább 8 karakterből kell állnia.",
    "s_totp_title": "Kétlépcsős azonosítás (2FA)",
    "s_totp_on": "<b>Bekapcsolva.</b> <span class='muted'>Bejelentkezéskor "
                 "a jelszó mellett a hitelesítő alkalmazás kódja is "
                 "szükséges.</span>",
    "s_totp_off_pw": "Jelszó (a kikapcsolás megerősítéséhez)",
    "s_totp_off_btn": "2FA kikapcsolása",
    "s_totp_step1": "1. Adja hozzá ezt a kulcsot a hitelesítő alkalmazáshoz "
                    "(Google Authenticator, Aegis, 1Password…):",
    "s_totp_link": "vagy nyissa meg a linket a telefonján:",
    "s_totp_add": "hozzáadás az alkalmazáshoz",
    "s_totp_step2": "2. Írja be az alkalmazásban megjelenő kódot",
    "s_totp_on_btn": "2FA bekapcsolása",
    "s_totp_lead": "A fiók második védelmi rétege: bejelentkezéskor a "
                   "jelszó mellett a telefonján lévő alkalmazás kódja is "
                   "szükséges. Ajánljuk bekapcsolni.",
    "err_totp_code": "A kód nem egyezik — próbálja újra.",
    "err_totp_pw": "A jelszó nem egyezik.",
    "s_push_title": "Push-értesítések",
    "s_push_lead": "Reggeli értesítés a függőben lévő fizetésekről "
                   "közvetlenül a telefonjára — a VORU kezdőképernyőre "
                   "telepítése után működik (lásd lent: Mobilalkalmazás).",
    "s_push_unsupported": "Ez a böngésző nem támogatja a "
                          "push-értesítéseket.",
    "s_push_nokeys": "A szerveren még nincsenek beállítva az értesítési "
                     "kulcsok.",
    "s_push_on": "Értesítések bekapcsolása",
    "s_push_off": "Értesítések kikapcsolása",
    "s_push_active": "Az értesítések ezen az eszközön be vannak kapcsolva.",
    "s_push_denied": "Az értesítéseket nem sikerült bekapcsolni "
                     "(megtagadta az engedélyt?).",
    "s_data_title": "Az Ön adatai",
    "s_data_lead": "A nyilvántartás teljes exportja (fizetések, feladatok, "
                   "levelezési napló, érvényességfigyelések) CSV "
                   "formátumban, ZIP archívumban.",
    "s_data_btn": "Adatexport letöltése",
    "s_del_title": "Fiók megszüntetése",
    "s_del_lead": "Visszavonhatatlanul törli a fiókot és az összes adatot "
                  "(postafiókok, fizetések, feladatok, fájlok). Ha valamire "
                  "szüksége van, előbb töltse le az exportot.",
    "s_del_pw": "Jelszó (megerősítéshez)",
    "s_del_btn": "Fiók és minden adat törlése",
    "s_del_confirm": "Valóban visszavonhatatlanul törli a fiókot és az "
                     "összes adatot?",
    "err_del_pw": "A jelszó nem egyezik.",
    "s_app_title": "Mobilalkalmazás",
    "s_app_lead": "A VORU-t telepítheti a telefonja kezdőképernyőjére — úgy "
                  "működik, mint egy megszokott alkalmazás, App Store "
                  "nélkül.",
    "s_app_ios": "<b>iPhone:</b> nyissa meg a voru.hu oldalt Safariban → "
                 "Megosztás gomb <span class='muted'>(négyzet "
                 "nyíllal)</span> → <b>Hozzáadás a kezdőképernyőhöz</b>.",
    "s_app_android": "<b>Android:</b> nyissa meg a voru.hu oldalt "
                     "Chrome-ban → ⋮ menü → <b>Hozzáadás a "
                     "kezdőképernyőhöz / Alkalmazás telepítése</b>.",
    # előfizetés
    "b_status": "Fiók állapota:",
    "b_active": "aktív előfizetés",
    "b_trial": "próbaidőszak vége: {date}",
    "b_inactive": "inaktív",
    "b_pick": "Válasszon csomagot — a fizetés biztonságosan, a Stripe-on "
              "keresztül történik:",
    "b_monthly": "4,99 € / hó",
    "b_yearly": "49 € / év — 2 hónap ingyen",
    "b_auto": "Fizetés után a fiók egy percen belül automatikusan "
              "aktiválódik.",
    "b_manual": "Az online bankkártyás fizetés előkészítés alatt áll — "
                "írjon nekünk: "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a>, "
                "és kézzel aktiváljuk.",
    "b_thanks": "Köszönjük, hogy a VORU-t használja. Az előfizetés "
                "lemondása: a Stripe visszaigazolásában található linken "
                "keresztül, vagy írjon nekünk: "
                "<a href='mailto:obchod@sorbxt.sk'>obchod@sorbxt.sk</a>.",
    "b_ref_title": "Ajánlja a VORU-t — egy hónap ingyen",
    "b_ref_lead": "Mindenki után, aki az Ön linkjén keresztül regisztrál, "
                  "<b>+30 nap</b> ingyenes szolgáltatást kap — az új "
                  "felhasználó pedig <b>+14 nap</b> extra próbaidőszakot.",
    "b_ref_count": "Az Ön linkjén keresztül eddig regisztráltak:",
    # elfelejtett jelszó / visszaállítás
    "fp_title": "Elfelejtett jelszó",
    "fp_lead": "Küldünk Önnek egy e-mailt egy linkkel az új jelszó "
               "beállításához.",
    "fp_email": "A fiók e-mail-címe",
    "fp_btn": "Link küldése",
    "fp_back": "Vissza a bejelentkezéshez",
    "fp_sent_title": "E-mail elküldve",
    "fp_sent_body": "Ha a fiók létezik, elküldtük rá a jelszó-visszaállító "
                    "linket. Ellenőrizze a postafiókját (a spam mappát is).",
    "rp_title": "Állítson be új jelszót",
    "rp_pw": "Új jelszó (min. 8 karakter)",
    "rp_btn": "Jelszó mentése",
    "rp_invalid_title": "Érvénytelen link",
    "rp_invalid_body": "A jelszó-visszaállító link lejárt vagy sérült — "
                       "kérjen újat.",
    "rp_done_title": "Jelszó megváltoztatva",
    "rp_done_body": "Jelentkezzen be az új jelszavával.",
    "reset_mail_subject": "VORU — jelszó-visszaállítás",
    "reset_mail_title": "Jelszó-visszaállítás",
    "reset_mail_lead": "Az új jelszót kattintással állíthatja be (a link "
                       "2 óráig érvényes):",
    "reset_mail_btn": "Új jelszó beállítása",
    "reset_mail_ignore": "Ha nem Ön kérte a visszaállítást, hagyja "
                         "figyelmen kívül az e-mailt.",
    "reset_mail_pre": "Az új jelszó beállítására szolgáló link 2 óráig "
                      "érvényes.",
    # e-mail megerősítése / rendszeroldalak
    "v_ok_title": "E-mail megerősítve",
    "v_ok_body": "Köszönjük, a cím meg van erősítve. A postafiókok és az "
                 "áttekintések elérhetővé váltak.",
    "v_bad_title": "Érvénytelen link",
    "v_bad_body": "A megerősítő link sérült vagy lejárt. Jelentkezzen be, "
                  "és küldessen magának újat.",
    "v_gate_title": "Először erősítse meg az e-mail-címét",
    "v_gate_body": "A postafiók csatlakoztatása az e-mail-címe megerősítése "
                   "után válik elérhetővé — kattintson az üdvözlő "
                   "e-mailben lévő linkre. Új linket az áttekintésen "
                   "található gombbal küldhet magának.",
    "v_gate_cta": "Vissza az áttekintéshez",
    "login_cta": "Bejelentkezés",
    "home_cta": "Ugrás az áttekintéshez",
    # műveleti oldalak (egy kattintás az e-mailből)
    "a_title": "Megerősítés",
    "a_invalid_title": "Érvénytelen link",
    "a_invalid_body": "A link sérült vagy hiányos. Nyissa meg újra az "
                      "e-mailből, vagy intézze el a tételt bejelentkezés "
                      "után az áttekintésben.",
    "a_done_title": "Elintézve",
    "a_done_count": ("{n} fizetést jelöltünk meg kifizetettként.",
                     "{n} fizetést jelöltünk meg kifizetettként.",
                     "{n} fizetést jelöltünk meg kifizetettként."),
    "a_done_single": "Sikerült: {label}.",
    "a_already_title": "Már elintézve",
    "a_already_bulk": "Nem volt mit megjelölni — vagy nem választott ki "
                      "semmit, vagy a kiválasztott fizetések időközben ki "
                      "lettek fizetve.",
    "a_already_single": "A tétel állapota időközben megváltozott — "
                        "valószínűleg már kipipálta, vagy a "
                        "bankszámlakivonat párosította.",
    "a_confirm_q": "Valóban: {label}?",
    "a_bulk_q": "Valóban: {label}? Vegye ki a pipát azoknál a tételeknél, "
                "amelyek még nincsenek kifizetve.",
    "a_bulk_empty": "Jelenleg nincs kifizetetlen tétele.",
    "a_bulk_btn": "A kiválasztottak megjelölése kifizetettként",
    "a_no_due": "határidő nélkül",
    "a_yes": "Igen, megerősítem",
    "a_safe": "Ha nem Ön nyitotta meg a linket, egyszerűen zárja be az "
              "oldalt — semmi sem történik.",
    "a_label_paid": "a fizetés megjelölése kifizetettként",
    "a_label_snooze": "az emlékeztető elhalasztása 3 nappal",
    "a_label_done": "a feladat megjelölése készként",
    "a_label_bulk": "a kiválasztott fizetések megjelölése kifizetettként",
    # SEPA
    "sepa_missing_title": "Hiányzik az Ön IBAN-ja",
    "sepa_missing_body": "A csoportos átutalási megbízáshoz meg kell adni "
                         "annak a számlának az IBAN-ját, amelyről a fizetés "
                         "történik.",
    "sepa_missing_cta": "Megadás a beállításokban",
    "sepa_empty_title": "Nincs mit átutalni",
    "sepa_empty_body": "Nincs kifizetetlen tétel IBAN-nal, EUR-ban.",
    # Gmail OAuth és további rendszerüzenetek
    "g_fail_title": "A Gmail csatlakoztatása nem sikerült",
    "g_fail_auth": "A Google-bejelentkezés megszakadt vagy lejárt. Próbálja "
                   "újra.",
    "g_fail_token": "A Google nem adott vissza hozzáférési adatokat. "
                    "Próbálja újra.",
    "mb_back": "Vissza a postafiókokhoz",
    "mb_conn_fail": "A csatlakozás nem sikerült: {err}",
    "rp_new_btn": "Új link kérése",
    "rp_err": "A link lejárt, vagy a jelszó rövidebb 8 karakternél.",
    "s_del_done_title": "Fiók megszüntetve",
    "s_del_done_body": "A fiókját és minden adatát töröltük. Köszönjük, "
                       "hogy kipróbálta a VORU-t.",
}
APP["back_btn"] = "Vissza"

# a próbaidőszak végéről szóló e-mailek
APP.update({
    "trial_mail_subject_warn": "VORU — hamarosan lejár a próbaidőszak ({date})",
    "trial_mail_subject_end": "VORU — lejárt a próbaidőszak",
    "trial_mail_warn_title": "Hamarosan lejár a próbaidőszak",
    "trial_mail_warn_lead": "A próbaidőszaka {date}-ig tart. Hogy a VORU "
                            "továbbra is figyelje számláit, fizetéseit és "
                            "határidőit, aktiválja előfizetését — havi 4,99 € "
                            "vagy évi 49 € (2 hónap ingyen).",
    "trial_mail_end_title": "Lejárt a próbaidőszak",
    "trial_mail_end_lead": "A próbaidőszaka ma lejárt, a szolgáltatás szünetel "
                           "— az összefoglalókat és emlékeztetőket egyelőre "
                           "nem küldjük. Minden adata megmarad; előfizetéssel "
                           "azonnal folytatódik.",
    "trial_mail_btn": "Előfizetés aktiválása",
    "trial_mail_footer": "Kérdése van? Válaszoljon erre az e-mailre.",
})
