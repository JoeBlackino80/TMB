"""Preklady e-mailov agenta (pripomienka, zhrnutie, mesačný report).

Jazyk klienta určuje APP_LANG v jeho .env (cez webapp — Nastavenia);
podporované sú trhy sk / cs / pl / de / hu. Slovenčina je predvolená
a zároveň referenčná — každý kľúč musí existovať vo všetkých jazykoch.
"""

LANGS = ("sk", "cs", "pl", "de", "hu", "en")


def plural(lang: str, n: int, forms: tuple[str, str, str]) -> str:
    """Vyskloňuje výraz s číslom: forms = (1, 2–4, 5+). Vracia aj číslo.

    Pre de/hu sa použije forms[0] pri n == 1, inak forms[2].
    """
    one, few, many = forms
    if n == 1:
        form = one
    elif lang in ("de", "hu"):
        form = many
    elif lang == "pl":
        form = few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many
    else:  # sk, cs
        form = few if 2 <= n <= 4 else many
    return form.format(n=n)


_SK = {
    # pripomienka
    "subject_reminder": "VORU: platby a úlohy",
    "subject_urgent": ("VORU: platby a úlohy — {n} súrna",
                       "VORU: platby a úlohy — {n} súrne",
                       "VORU: platby a úlohy — {n} súrnych"),
    "title": "Prehľad platieb a úloh",
    "summary_payments": ("{n} platba čaká na úhradu", "{n} platby čakajú na úhradu",
                         "{n} platieb čaká na úhradu"),
    "summary_urgent": (", z toho {n} súrna", ", z toho {n} súrne",
                       ", z toho {n} súrnych"),
    "summary_tasks": ("{n} aktívna úloha", "{n} aktívne úlohy", "{n} aktívnych úloh"),
    "sec_overdue": "Po splatnosti",
    "sec_today": "Splatné dnes",
    "sec_upcoming": "Splatné v najbližších dňoch",
    "sec_no_date": "Bez uvedenej splatnosti",
    "unknown_supplier": "(neznámy dodávateľ)",
    "unknown_supplier_short": "(neznámy)",
    "item_no": "č.",
    "due": "Splatnosť",
    "vs": "VS",
    "qr_hint": "Naskenujte v aplikácii banky a platbu potvrďte.",
    "btn_paid": "Označiť ako zaplatené",
    "btn_snooze": "Odložiť o 3 dni",
    "btn_done": "Hotovo",
    "btn_all_paid": "Označiť všetko ako zaplatené",
    "bulk_hint": "Otvorí sa potvrdenie so zoznamom platieb — zrušíte "
                 "zaškrtnutie pri tom, čo ešte zaplatené nie je.",
    "bulk_text": "Označiť všetko ako zaplatené",
    "reply_hint": "alebo odpovedzte na tento e-mail: <b>zaplatené {id}</b>",
    "cmd_paid": "zaplatené",
    "cmd_done": "hotovo",
    "tasks": "Úlohy",
    "task_due": "(do {d})",
    "task_hint": "Hotovo? Odpovedzte: <b>hotovo {id}</b>",
    "renewals": "Končí platnosť",
    "tax": "Daňové termíny",
    "footer_commands": "Ovládanie odpoveďou na tento e-mail: <b>zaplatené 3</b> "
                       "(číslo platby), <b>zaplatené všetko</b>, <b>ignoruj 5</b>, "
                       "<b>hotovo 2</b> (číslo úlohy), <b>odlož 4 o 5</b> "
                       "(pripomenie o 5 dní), <b>odlož úlohu 2</b> — VORU to "
                       "pri ďalšej kontrole pošty vybaví samo.",
    "footer_commands_text": "Ovládanie odpoveďou: 'zaplatené 3', 'zaplatené všetko', "
                            "'ignoruj 5', 'hotovo 2', 'odlož 4 o 5', 'odlož úlohu 2'.",
    "renewal_labels": {"pzp": "PZP", "havarijne": "Havarijné poistenie",
                       "stk": "STK", "ek": "Emisná kontrola", "poistka": "Poistka",
                       "domena": "Doména", "predplatne": "Predplatné",
                       "zmluva": "Zmluva", "ine": "Koniec platnosti"},
    # zhrnutie dňa / týždňa
    "digest_subject_day": "VORU: Zhrnutie dňa — {date}",
    "digest_subject_week": "VORU: Zhrnutie týždňa {range}",
    "digest_title_day": "Zhrnutie dňa",
    "digest_title_week": "Zhrnutie týždňa",
    "digest_stat": "Nezaplatených platieb: {n}",
    "digest_stat_urgent": (" (z toho {n} súrna!)", " (z toho {n} súrne!)",
                           " (z toho {n} súrnych!)"),
    "digest_stat_tasks": " · aktívnych úloh: {n}",
    "digest_stat_note": "Podrobnosti a QR kódy sú v poslednom e-maile "
                        "„VORU: platby a úlohy“.",
    "digest_missing": "Pravidelné faktúry, ktoré neprišli",
    "digest_missing_text": "Pravidelné faktúry, ktoré tento cyklus neprišli:",
    "digest_missing_line": "{s} — posledná {last}, ďalšia sa čakala do {exp}",
    "digest_missing_note": "Skontrolujte, či faktúra neskončila v spame, "
                           "alebo či nechodí na inú adresu.",
    "cat_faktura": "Faktúry a platby", "cat_banka": "Banka",
    "cat_objednavka": "Objednávky a zásielky", "cat_uloha": "Úlohy a termíny",
    "cat_marketing": "Marketing / newslettre", "cat_ine": "Ostatné",
    "no_subject": "(bez predmetu)",
    "ai_language": "po slovensky",
    # mesačný report
    "months": ["január", "február", "marec", "apríl", "máj", "jún", "júl",
               "august", "september", "október", "november", "december"],
    "report_title": "Mesačný report — {month} {year}",
    "report_payments": ("{n} platba", "{n} platby", "{n} platieb"),
    "report_total_text": "Zaplatené spolu",
    "report_more": "viac", "report_less": "menej",
    "report_compare": "o {diff} ({pct} %) {dir} než v predchádzajúcom mesiaci ({prev})",
    "report_by_supplier": "Podľa dodávateľov",
    "report_footer": "Kompletné podklady (faktúry + CSV) si stiahnete v prehľade "
                     "v aplikácii — Podklady pre účtovníctvo.",
}

_CS = {
    "subject_reminder": "VORU: platby a úkoly",
    "subject_urgent": ("VORU: platby a úkoly — {n} urgentní",
                       "VORU: platby a úkoly — {n} urgentní",
                       "VORU: platby a úkoly — {n} urgentních"),
    "title": "Přehled plateb a úkolů",
    "summary_payments": ("{n} platba čeká na úhradu", "{n} platby čekají na úhradu",
                         "{n} plateb čeká na úhradu"),
    "summary_urgent": (", z toho {n} urgentní", ", z toho {n} urgentní",
                       ", z toho {n} urgentních"),
    "summary_tasks": ("{n} aktivní úkol", "{n} aktivní úkoly", "{n} aktivních úkolů"),
    "sec_overdue": "Po splatnosti",
    "sec_today": "Splatné dnes",
    "sec_upcoming": "Splatné v nejbližších dnech",
    "sec_no_date": "Bez uvedené splatnosti",
    "unknown_supplier": "(neznámý dodavatel)",
    "unknown_supplier_short": "(neznámý)",
    "item_no": "č.",
    "due": "Splatnost",
    "vs": "VS",
    "qr_hint": "Naskenujte v bankovní aplikaci a platbu potvrďte.",
    "btn_paid": "Označit jako zaplacené",
    "btn_snooze": "Odložit o 3 dny",
    "btn_done": "Hotovo",
    "btn_all_paid": "Označit vše jako zaplacené",
    "bulk_hint": "Otevře se potvrzení se seznamem plateb — zrušíte "
                 "zaškrtnutí u toho, co ještě není zaplacené.",
    "bulk_text": "Označit vše jako zaplacené",
    "reply_hint": "nebo odpovězte na tento e-mail: <b>zaplaceno {id}</b>",
    "cmd_paid": "zaplaceno",
    "cmd_done": "hotovo",
    "tasks": "Úkoly",
    "task_due": "(do {d})",
    "task_hint": "Hotovo? Odpovězte: <b>hotovo {id}</b>",
    "renewals": "Končí platnost",
    "tax": "Daňové termíny",
    "footer_commands": "Ovládání odpovědí na tento e-mail: <b>zaplaceno 3</b> "
                       "(číslo platby), <b>zaplaceno vše</b>, <b>ignoruj 5</b>, "
                       "<b>hotovo 2</b> (číslo úkolu), <b>odlož 4 o 5</b> "
                       "(připomene za 5 dní), <b>odlož úkol 2</b> — VORU to "
                       "při další kontrole pošty vyřídí samo.",
    "footer_commands_text": "Ovládání odpovědí: 'zaplaceno 3', 'zaplaceno vše', "
                            "'ignoruj 5', 'hotovo 2', 'odlož 4 o 5', 'odlož úkol 2'.",
    "renewal_labels": {"pzp": "Povinné ručení", "havarijne": "Havarijní pojištění",
                       "stk": "STK", "ek": "Emisní kontrola", "poistka": "Pojistka",
                       "domena": "Doména", "predplatne": "Předplatné",
                       "zmluva": "Smlouva", "ine": "Konec platnosti"},
    "digest_subject_day": "VORU: Shrnutí dne — {date}",
    "digest_subject_week": "VORU: Shrnutí týdne {range}",
    "digest_title_day": "Shrnutí dne",
    "digest_title_week": "Shrnutí týdne",
    "digest_stat": "Nezaplacených plateb: {n}",
    "digest_stat_urgent": (" (z toho {n} urgentní!)", " (z toho {n} urgentní!)",
                           " (z toho {n} urgentních!)"),
    "digest_stat_tasks": " · aktivních úkolů: {n}",
    "digest_stat_note": "Podrobnosti a QR kódy jsou v posledním e-mailu "
                        "„VORU: platby a úkoly“.",
    "digest_missing": "Pravidelné faktury, které nepřišly",
    "digest_missing_text": "Pravidelné faktury, které tento cyklus nepřišly:",
    "digest_missing_line": "{s} — poslední {last}, další jsme čekali do {exp}",
    "digest_missing_note": "Zkontrolujte, zda faktura neskončila ve spamu, "
                           "nebo nechodí na jinou adresu.",
    "cat_faktura": "Faktury a platby", "cat_banka": "Banka",
    "cat_objednavka": "Objednávky a zásilky", "cat_uloha": "Úkoly a termíny",
    "cat_marketing": "Marketing / newslettery", "cat_ine": "Ostatní",
    "no_subject": "(bez předmětu)",
    "ai_language": "česky",
    "months": ["leden", "únor", "březen", "duben", "květen", "červen", "červenec",
               "srpen", "září", "říjen", "listopad", "prosinec"],
    "report_title": "Měsíční report — {month} {year}",
    "report_payments": ("{n} platba", "{n} platby", "{n} plateb"),
    "report_total_text": "Zaplaceno celkem",
    "report_more": "více", "report_less": "méně",
    "report_compare": "o {diff} ({pct} %) {dir} než v předchozím měsíci ({prev})",
    "report_by_supplier": "Podle dodavatelů",
    "report_footer": "Kompletní podklady (faktury + CSV) si stáhnete v přehledu "
                     "v aplikaci — Podklady pro účetnictví.",
}

_PL = {
    "subject_reminder": "VORU: płatności i zadania",
    "subject_urgent": ("VORU: płatności i zadania — {n} pilna",
                       "VORU: płatności i zadania — {n} pilne",
                       "VORU: płatności i zadania — {n} pilnych"),
    "title": "Przegląd płatności i zadań",
    "summary_payments": ("{n} płatność czeka na opłacenie",
                         "{n} płatności czekają na opłacenie",
                         "{n} płatności czeka na opłacenie"),
    "summary_urgent": (", w tym {n} pilna", ", w tym {n} pilne",
                       ", w tym {n} pilnych"),
    "summary_tasks": ("{n} aktywne zadanie", "{n} aktywne zadania",
                      "{n} aktywnych zadań"),
    "sec_overdue": "Po terminie",
    "sec_today": "Do zapłaty dzisiaj",
    "sec_upcoming": "Do zapłaty w najbliższych dniach",
    "sec_no_date": "Bez podanego terminu",
    "unknown_supplier": "(nieznany dostawca)",
    "unknown_supplier_short": "(nieznany)",
    "item_no": "nr",
    "due": "Termin",
    "vs": "Tytuł przelewu",
    "qr_hint": "Zeskanuj w aplikacji bankowej i potwierdź płatność.",
    "btn_paid": "Oznacz jako zapłacone",
    "btn_snooze": "Odłóż o 3 dni",
    "btn_done": "Gotowe",
    "btn_all_paid": "Oznacz wszystko jako zapłacone",
    "bulk_hint": "Otworzy się potwierdzenie z listą płatności — odznaczysz to, "
                 "co jeszcze nie jest zapłacone.",
    "bulk_text": "Oznacz wszystko jako zapłacone",
    "reply_hint": "albo odpowiedz na ten e-mail: <b>zapłacone {id}</b>",
    "cmd_paid": "zapłacone",
    "cmd_done": "gotowe",
    "tasks": "Zadania",
    "task_due": "(do {d})",
    "task_hint": "Gotowe? Odpowiedz: <b>gotowe {id}</b>",
    "renewals": "Kończy się ważność",
    "tax": "Terminy podatkowe",
    "footer_commands": "Możesz sterować VORU, odpowiadając na ten e-mail: <b>zapłacone 3</b> "
                       "(numer płatności), <b>zapłacone wszystko</b>, "
                       "<b>ignoruj 5</b>, <b>gotowe 2</b> (numer zadania), "
                       "<b>odłóż 4 o 5</b> (przypomni za 5 dni), "
                       "<b>odłóż zadanie 2</b> — VORU załatwi to samo przy "
                       "następnym sprawdzeniu poczty.",
    "footer_commands_text": "Sterowanie odpowiedzią na ten e-mail: 'zapłacone 3', 'zapłacone "
                            "wszystko', 'ignoruj 5', 'gotowe 2', 'odłóż 4 o 5', "
                            "'odłóż zadanie 2'.",
    "renewal_labels": {"pzp": "OC pojazdu", "havarijne": "Ubezpieczenie AC",
                       "stk": "Przegląd techniczny", "ek": "Badanie emisji",
                       "poistka": "Polisa", "domena": "Domena",
                       "predplatne": "Subskrypcja", "zmluva": "Umowa",
                       "ine": "Koniec ważności"},
    "digest_subject_day": "VORU: Podsumowanie dnia — {date}",
    "digest_subject_week": "VORU: Podsumowanie tygodnia {range}",
    "digest_title_day": "Podsumowanie dnia",
    "digest_title_week": "Podsumowanie tygodnia",
    "digest_stat": "Niezapłaconych płatności: {n}",
    "digest_stat_urgent": (" (w tym {n} pilna!)", " (w tym {n} pilne!)",
                           " (w tym {n} pilnych!)"),
    "digest_stat_tasks": " · aktywnych zadań: {n}",
    "digest_stat_note": "Szczegóły i kody QR znajdziesz w ostatnim e-mailu "
                        "„VORU: płatności i zadania”.",
    "digest_missing": "Regularne faktury, które nie przyszły",
    "digest_missing_text": "Regularne faktury, które nie przyszły w tym cyklu:",
    "digest_missing_line": "{s} — ostatnia {last}, następnej oczekiwano do {exp}",
    "digest_missing_note": "Sprawdź, czy faktura nie umknęła albo nie przychodzi "
                           "gdzie indziej.",
    "cat_faktura": "Faktury i płatności", "cat_banka": "Bank",
    "cat_objednavka": "Zamówienia i przesyłki", "cat_uloha": "Zadania i terminy",
    "cat_marketing": "Marketing / newslettery", "cat_ine": "Pozostałe",
    "no_subject": "(bez tematu)",
    "ai_language": "po polsku",
    "months": ["styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec",
               "sierpień", "wrzesień", "październik", "listopad", "grudzień"],
    "report_title": "Raport miesięczny — {month} {year}",
    "report_payments": ("{n} płatność", "{n} płatności", "{n} płatności"),
    "report_total_text": "Zapłacono łącznie",
    "report_more": "więcej", "report_less": "mniej",
    "report_compare": "o {diff} ({pct} %) {dir} niż w poprzednim miesiącu ({prev})",
    "report_by_supplier": "Według dostawców",
    "report_footer": "Komplet dokumentów (faktury + CSV) pobierzesz w aplikacji "
                     "— Dokumenty dla księgowości.",
}

_DE = {
    "subject_reminder": "VORU: Zahlungen und Aufgaben",
    "subject_urgent": ("VORU: Zahlungen und Aufgaben — {n} dringend",) * 3,
    "title": "Übersicht der Zahlungen und Aufgaben",
    "summary_payments": ("{n} Zahlung wartet auf Begleichung",
                         "{n} Zahlungen warten auf Begleichung",
                         "{n} Zahlungen warten auf Begleichung"),
    "summary_urgent": (", davon {n} dringend",) * 3,
    "summary_tasks": ("{n} offene Aufgabe", "{n} offene Aufgaben",
                      "{n} offene Aufgaben"),
    "sec_overdue": "Überfällig",
    "sec_today": "Heute fällig",
    "sec_upcoming": "In den nächsten Tagen fällig",
    "sec_no_date": "Ohne Fälligkeitsdatum",
    "unknown_supplier": "(unbekannter Lieferant)",
    "unknown_supplier_short": "(unbekannt)",
    "item_no": "Nr.",
    "due": "Fällig am",
    "vs": "Referenz",
    "qr_hint": "In der Banking-App scannen und die Zahlung bestätigen.",
    "btn_paid": "Als bezahlt markieren",
    "btn_snooze": "Um 3 Tage verschieben",
    "btn_done": "Erledigt",
    "btn_all_paid": "Alles als bezahlt markieren",
    "bulk_hint": "Es öffnet sich eine Bestätigungsseite mit allen Zahlungen — "
                 "Sie wählen ab, was noch nicht bezahlt ist.",
    "bulk_text": "Alles als bezahlt markieren",
    "reply_hint": "oder antworten Sie auf diese E-Mail: <b>bezahlt {id}</b>",
    "cmd_paid": "bezahlt",
    "cmd_done": "erledigt",
    "tasks": "Aufgaben",
    "task_due": "(bis {d})",
    "task_hint": "erledigt? Antworten Sie: <b>erledigt {id}</b>",
    "renewals": "Läuft bald ab",
    "tax": "Steuertermine",
    "footer_commands": "Steuerung per Antwort auf diese E-Mail: <b>bezahlt 3</b> "
                       "(Zahlungsnummer), <b>bezahlt alles</b>, <b>ignoriere 5</b>, "
                       "<b>erledigt 2</b> (Aufgabennummer), <b>verschieb 4 um 5</b> "
                       "(erinnert in 5 Tagen), <b>verschieb Aufgabe 2</b> — "
                       "VORU erledigt es beim nächsten Abruf selbst.",
    "footer_commands_text": "Steuerung per Antwort: 'bezahlt 3', 'bezahlt alles', "
                            "'ignoriere 5', 'erledigt 2', 'verschieb 4 um 5', "
                            "'verschieb Aufgabe 2'.",
    "renewal_labels": {"pzp": "Kfz-Haftpflicht", "havarijne": "Kaskoversicherung",
                       "stk": "§57a-Begutachtung („Pickerl“)", "ek": "Abgasuntersuchung",
                       "poistka": "Versicherung", "domena": "Domain",
                       "predplatne": "Abonnement", "zmluva": "Vertrag",
                       "ine": "Ablaufdatum"},
    "digest_subject_day": "VORU: Tageszusammenfassung — {date}",
    "digest_subject_week": "VORU: Wochenzusammenfassung {range}",
    "digest_title_day": "Tageszusammenfassung",
    "digest_title_week": "Wochenzusammenfassung",
    "digest_stat": "Unbezahlte Zahlungen: {n}",
    "digest_stat_urgent": (" (davon {n} dringend!)",) * 3,
    "digest_stat_tasks": " · offene Aufgaben: {n}",
    "digest_stat_note": "Details und QR-Codes finden Sie in der letzten E-Mail "
                        "„VORU: Zahlungen und Aufgaben“.",
    "digest_missing": "Regelmäßige Rechnungen, die nicht eingetroffen sind",
    "digest_missing_text": "Regelmäßige Rechnungen, die in diesem Zyklus nicht "
                           "eingetroffen sind:",
    "digest_missing_line": "{s} — zuletzt {last}, nächste erwartet bis {exp}",
    "digest_missing_note": "Prüfen Sie, ob die Rechnung untergegangen ist oder "
                           "woanders eingeht.",
    "cat_faktura": "Rechnungen und Zahlungen", "cat_banka": "Bank",
    "cat_objednavka": "Bestellungen und Sendungen",
    "cat_uloha": "Aufgaben und Termine",
    "cat_marketing": "Marketing / Newsletter", "cat_ine": "Sonstiges",
    "no_subject": "(ohne Betreff)",
    "ai_language": "auf Deutsch",
    "months": ["Jänner", "Februar", "März", "April", "Mai", "Juni", "Juli",
               "August", "September", "Oktober", "November", "Dezember"],
    "report_title": "Monatsreport — {month} {year}",
    "report_payments": ("{n} Zahlung", "{n} Zahlungen", "{n} Zahlungen"),
    "report_total_text": "Insgesamt bezahlt",
    "report_more": "mehr", "report_less": "weniger",
    "report_compare": "um {diff} ({pct} %) {dir} als im Vormonat ({prev})",
    "report_by_supplier": "Nach Lieferanten",
    "report_footer": "Die vollständigen Unterlagen (Rechnungen + CSV) laden Sie "
                     "in der App herunter — Unterlagen für die Buchhaltung.",
}

_HU = {
    "subject_reminder": "VORU: fizetések és teendők",
    "subject_urgent": ("VORU: fizetések és teendők — {n} sürgős",) * 3,
    "title": "Fizetések és teendők áttekintése",
    "summary_payments": ("{n} fizetés vár rendezésre", "{n} fizetés vár rendezésre",
                         "{n} fizetés vár rendezésre"),
    "summary_urgent": (", ebből {n} sürgős",) * 3,
    "summary_tasks": ("{n} aktív teendő", "{n} aktív teendő", "{n} aktív teendő"),
    "sec_overdue": "Lejárt határidejű",
    "sec_today": "Ma esedékes",
    "sec_upcoming": "A következő napokban esedékes",
    "sec_no_date": "Határidő nélkül",
    "unknown_supplier": "(ismeretlen szállító)",
    "unknown_supplier_short": "(ismeretlen)",
    "item_no": "sz.",
    "due": "Határidő",
    "vs": "Közlemény",
    "qr_hint": "Olvassa be a banki alkalmazásban, és hagyja jóvá a fizetést.",
    "btn_paid": "Megjelölés fizetettként",
    "btn_snooze": "Halasztás 3 nappal",
    "btn_done": "Kész",
    "btn_all_paid": "Mind megjelölése fizetettként",
    "bulk_hint": "Megnyílik egy megerősítő oldal az összes fizetéssel — "
                 "kiveszi a pipát abból, ami még nincs kifizetve.",
    "bulk_text": "Mind megjelölése fizetettként",
    "reply_hint": "vagy válaszoljon erre az e-mailre: <b>fizetve {id}</b>",
    "cmd_paid": "fizetve",
    "cmd_done": "kész",
    "tasks": "Teendők",
    "task_due": "({d}-ig)",
    "task_hint": "kész? válaszoljon: <b>kész {id}</b>",
    "renewals": "Hamarosan lejár",
    "tax": "Adóhatáridők",
    "footer_commands": "Vezérlés az e-mailre adott válasszal: <b>fizetve 3</b> "
                       "(fizetés száma), <b>fizetve mind</b>, <b>ignoráld 5</b>, "
                       "<b>kész 2</b> (teendő száma), <b>halaszd 4 5 nappal</b> "
                       "(5 nap múlva emlékeztet), <b>halaszd teendő 2</b> — "
                       "a VORU a következő levélellenőrzéskor elintézi.",
    "footer_commands_text": "Vezérlés válasszal: 'fizetve 3', 'fizetve mind', "
                            "'ignoráld 5', 'kész 2', 'halaszd 4 5 nappal', "
                            "'halaszd teendő 2'.",
    "renewal_labels": {"pzp": "Kötelező biztosítás", "havarijne": "Casco",
                       "stk": "Műszaki vizsga", "ek": "Környezetvédelmi vizsga",
                       "poistka": "Biztosítás", "domena": "Domain",
                       "predplatne": "Előfizetés", "zmluva": "Szerződés",
                       "ine": "Lejárat"},
    "digest_subject_day": "VORU: Napi összefoglaló — {date}",
    "digest_subject_week": "VORU: Heti összefoglaló {range}",
    "digest_title_day": "Napi összefoglaló",
    "digest_title_week": "Heti összefoglaló",
    "digest_stat": "Kifizetetlen fizetések: {n}",
    "digest_stat_urgent": (" (ebből {n} sürgős!)",) * 3,
    "digest_stat_tasks": " · aktív teendők: {n}",
    "digest_stat_note": "A részleteket és QR-kódokat a legutóbbi „VORU: fizetések "
                        "és teendők” e-mailben találja.",
    "digest_missing": "Rendszeres számlák, amelyek nem érkeztek meg",
    "digest_missing_text": "Rendszeres számlák, amelyek ebben a ciklusban nem "
                           "érkeztek meg:",
    "digest_missing_line": "{s} — utolsó {last}, a következőt {exp}-ig vártuk",
    "digest_missing_note": "Ellenőrizze, hogy a számla nem veszett-e el, vagy nem "
                           "máshová érkezik-e.",
    "cat_faktura": "Számlák és fizetések", "cat_banka": "Bank",
    "cat_objednavka": "Rendelések és csomagok", "cat_uloha": "Teendők és határidők",
    "cat_marketing": "Marketing / hírlevelek", "cat_ine": "Egyéb",
    "no_subject": "(tárgy nélkül)",
    "ai_language": "magyarul",
    "months": ["január", "február", "március", "április", "május", "június",
               "július", "augusztus", "szeptember", "október", "november",
               "december"],
    "report_title": "Havi jelentés — {month} {year}",
    "report_payments": ("{n} fizetés", "{n} fizetés", "{n} fizetés"),
    "report_total_text": "Összesen kifizetve",
    "report_more": "több", "report_less": "kevesebb",
    "report_compare": "{diff}-val ({pct} %) {dir}, mint az előző hónapban "
                      "({prev})",
    "report_by_supplier": "Szállítók szerint",
    "report_footer": "A teljes dokumentációt (számlák + CSV) az alkalmazásban "
                     "töltheti le — Könyvelési dokumentumok.",
}

_EN = {
    "subject_reminder": "VORU: payments and tasks",
    "subject_urgent": ("VORU: payments and tasks — {n} urgent",) * 3,
    "title": "Payments and tasks overview",
    "summary_payments": ("{n} outstanding payment",
                         "{n} outstanding payments",
                         "{n} outstanding payments"),
    "summary_urgent": (", {n} of them urgent",) * 3,
    "summary_tasks": ("{n} open task", "{n} open tasks", "{n} open tasks"),
    "sec_overdue": "Overdue",
    "sec_today": "Due today",
    "sec_upcoming": "Due in the coming days",
    "sec_no_date": "No due date",
    "unknown_supplier": "(unknown supplier)",
    "unknown_supplier_short": "(unknown)",
    "item_no": "no.",
    "due": "Due",
    "vs": "Payment ref",
    "qr_hint": "Scan in your banking app and confirm the payment.",
    "btn_paid": "Mark as paid",
    "btn_snooze": "Snooze 3 days",
    "btn_done": "Done",
    "btn_all_paid": "Mark everything as paid",
    "bulk_hint": "Opens a confirmation page listing all payments — untick "
                 "whatever is not paid yet.",
    "bulk_text": "Mark everything as paid",
    "reply_hint": "or reply to this email: <b>paid {id}</b>",
    "cmd_paid": "paid",
    "cmd_done": "done",
    "tasks": "Tasks",
    "task_due": "(by {d})",
    "task_hint": "Done? Reply: <b>done {id}</b>",
    "renewals": "Expiring soon",
    "tax": "Tax deadlines",
    "footer_commands": "You can control VORU by replying to this email: "
                       "<b>paid 3</b> (payment number), <b>paid all</b>, "
                       "<b>ignore 5</b>, <b>done 2</b> (task number), "
                       "<b>snooze 4 by 5</b> (we'll remind you again in "
                       "5 days), <b>snooze task 2</b> — VORU takes care of it "
                       "on the next mail check.",
    "footer_commands_text": "Control by reply: 'paid 3', 'paid all', 'ignore 5', "
                            "'done 2', 'snooze 4 by 5', 'snooze task 2'.",
    "renewal_labels": {"pzp": "Motor liability insurance",
                       "havarijne": "Comprehensive insurance",
                       "stk": "Vehicle inspection (MOT)",
                       "ek": "Emissions test", "poistka": "Insurance policy",
                       "domena": "Domain", "predplatne": "Subscription",
                       "zmluva": "Contract", "ine": "Expiry"},
    "digest_subject_day": "VORU: Daily digest — {date}",
    "digest_subject_week": "VORU: Weekly digest {range}",
    "digest_title_day": "Daily digest",
    "digest_title_week": "Weekly digest",
    "digest_stat": "Outstanding payments: {n}",
    "digest_stat_urgent": (" ({n} of them urgent!)",) * 3,
    "digest_stat_tasks": " · open tasks: {n}",
    "digest_stat_note": "Details and QR codes are in the latest "
                        "“VORU: payments and tasks” email.",
    "digest_missing": "Recurring invoices that did not arrive",
    "digest_missing_text": "Recurring invoices that did not arrive this cycle:",
    "digest_missing_line": "{s} — last received {last}, next expected by {exp}",
    "digest_missing_note": "Check whether the invoice landed in spam or is "
                           "being sent to a different address.",
    "cat_faktura": "Invoices and payments", "cat_banka": "Bank",
    "cat_objednavka": "Orders and deliveries", "cat_uloha": "Tasks and deadlines",
    "cat_marketing": "Marketing / newsletters", "cat_ine": "Other",
    "no_subject": "(no subject)",
    "ai_language": "in English",
    "months": ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"],
    "report_title": "Monthly report — {month} {year}",
    "report_payments": ("{n} payment", "{n} payments", "{n} payments"),
    "report_total_text": "Total paid",
    "report_more": "more", "report_less": "less",
    "report_compare": "{diff} ({pct}%) {dir} than the previous month ({prev})",
    "report_by_supplier": "By supplier",
    "report_footer": "Download the complete records (invoices + CSV) in the app "
                     "— Accounting documents.",
}

_TABLES = {"sk": _SK, "cs": _CS, "pl": _PL, "de": _DE, "hu": _HU, "en": _EN}

# predmety pripomienok vo všetkých jazykoch — podľa nich commands.py spozná,
# že odpoveď patrí k pripomienke (malé písmená)
SUBJECT_MARKERS = tuple(
    tbl["subject_reminder"].removeprefix("VORU: ").lower() for tbl in _TABLES.values()
)


def t(lang: str | None) -> dict:
    """Prekladová tabuľka jazyka; neznámy/None → slovenčina."""
    return _TABLES.get(lang or "sk", _SK)
