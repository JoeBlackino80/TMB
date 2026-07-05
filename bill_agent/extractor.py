"""Extrakcia platieb a úloh z e-mailu pomocou Claude API (štruktúrovaný výstup)."""

import base64
import json
import sys
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from .config import Config
from .emails import Email

_SUMMARY_LANGS = {"sk": "slovenčine", "cs": "češtine", "pl": "poľštine",
                  "de": "nemčine", "hu": "maďarčine"}


def system_prompt(account_type: str = "business", lang: str = "sk") -> str:
    if account_type == "personal":
        persona = ("Si asistent slovenskej domácnosti (súkromnej osoby). Typická "
                   "pošta: vyúčtovania energií a telekomunikácií, nájom, poistky, "
                   "splátky, predpisy platieb, školy a škôlky, predplatné.")
    elif account_type == "both":
        persona = ("Si asistent slovenského podnikateľa, ktorý v tej istej schránke "
                   "dostáva aj súkromnú poštu domácnosti (energie, nájom, poistky, "
                   "splátky, školy) — spracúvaj firemné aj súkromné položky.")
    else:
        persona = "Si asistent slovenského podnikateľa."
    return persona + """ Analyzuješ prijaté e-maily
(vrátane PDF príloh — faktúry, upomienky, výzvy na platbu, zálohové faktúry) a
extrahuješ z nich:

1. PLATBY, ktoré má používateľ uhradiť: dodávateľ, suma, mena, IBAN, variabilný
   symbol, špecifický symbol, konštantný symbol, dátum splatnosti.
   - Extrahuj len platby, ktoré má POUŽÍVATEĽ zaplatiť (prijaté faktúry, upomienky,
     predpisy). NIE faktúry, ktoré používateľ sám vystavil, potvrdenia o už
     prijatej platbe, ani marketingové cenníky.
   - Sumu uveď ako desatinné číslo. IBAN bez medzier. Ak údaj chýba, nechaj prázdny
     reťazec. Dátumy vo formáte YYYY-MM-DD.
   - Ak e-mail aj príloha uvádzajú tú istú platbu, uveď ju len raz (uprednostni
     údaje z prílohy — faktúry).

2. ÚLOHY / TERMÍNY: veci, ktoré má používateľ urobiť (poslať podklady, podpísať
   zmluvu, dostaviť sa na termín, obnoviť certifikát...). Krátky popis po slovensky
   + termín, ak je uvedený.

3. UŽ VYKONANÉ PLATBY (paid_transactions): z bankových výpisov a potvrdení
   o vykonanej platbe extrahuj ODCHÁDZAJÚCE platby — suma (kladné číslo),
   variabilný symbol, IBAN protistrany, dátum, krátky popis. Použijú sa na
   automatické odškrtnutie už zaplatených záväzkov. Prijaté (kreditné) platby
   a poplatky banky neuvádzaj.

4. KONCE PLATNOSTI (expirations): ak e-mail hovorí, že niečo KONČÍ alebo treba
   OBNOVIŤ — poistenie PZP/havarijné (uveď aj EČV vozidla, ak je známe), STK,
   emisná kontrola, doména, predplatné, zmluva — extrahuj druh, predmet
   (napr. "Škoda Octavia BA-123XY" alebo "voru.sk"), dátum konca platnosti
   a krátku poznámku (napr. ponúknutá nová cena). Neuvádzaj bežné splatnosti
   faktúr, tie patria do PLATIEB.

5. SÚHRN (summary + category): 1–2 vety po slovensky, o čom e-mail je a či
   vyžaduje pozornosť. Kategória: faktura | banka | objednavka | uloha |
   marketing | ine.

Ak e-mail neobsahuje nič relevantné (newsletter, spam, bežná konverzácia),
vráť prázdne zoznamy (summary a category vyplň vždy).""" + (
        f"\n\nSúhrn (summary) a popisy úloh píš v {_SUMMARY_LANGS[lang]}."
        if lang in _SUMMARY_LANGS and lang != "sk" else "")


SYSTEM_PROMPT = system_prompt()

OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "payments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "supplier": {"type": "string", "description": "Názov dodávateľa/príjemcu platby"},
                        "amount": {"type": "number"},
                        "currency": {"type": "string", "description": "ISO kód meny, napr. EUR"},
                        "iban": {"type": "string"},
                        "variable_symbol": {"type": "string"},
                        "specific_symbol": {"type": "string"},
                        "constant_symbol": {"type": "string"},
                        "due_date": {"type": "string", "description": "YYYY-MM-DD alebo prázdny reťazec"},
                        "note": {"type": "string", "description": "Krátky popis, napr. číslo faktúry"},
                    },
                    "required": [
                        "supplier", "amount", "currency", "iban", "variable_symbol",
                        "specific_symbol", "constant_symbol", "due_date", "note",
                    ],
                    "additionalProperties": False,
                },
            },
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "due_date": {"type": "string", "description": "YYYY-MM-DD alebo prázdny reťazec"},
                    },
                    "required": ["description", "due_date"],
                    "additionalProperties": False,
                },
            },
            "paid_transactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number", "description": "Kladná suma odchádzajúcej platby"},
                        "variable_symbol": {"type": "string"},
                        "counterparty_iban": {"type": "string"},
                        "date": {"type": "string", "description": "YYYY-MM-DD alebo prázdny reťazec"},
                        "description": {"type": "string"},
                    },
                    "required": ["amount", "variable_symbol", "counterparty_iban", "date", "description"],
                    "additionalProperties": False,
                },
            },
            "expirations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": ["pzp", "havarijne", "stk", "ek", "poistka",
                                     "domena", "predplatne", "zmluva", "ine"],
                        },
                        "subject": {"type": "string",
                                    "description": "Čoho sa to týka — napr. EČV vozidla, doména, názov zmluvy"},
                        "expires_on": {"type": "string", "description": "YYYY-MM-DD alebo prázdny reťazec"},
                        "note": {"type": "string"},
                    },
                    "required": ["kind", "subject", "expires_on", "note"],
                    "additionalProperties": False,
                },
            },
            "summary": {"type": "string", "description": "1-2 vety po slovensky"},
            "category": {
                "type": "string",
                "enum": ["faktura", "banka", "objednavka", "uloha", "marketing", "ine"],
            },
        },
        "required": ["payments", "tasks", "paid_transactions", "expirations",
                     "summary", "category"],
        "additionalProperties": False,
    },
}

CATEGORIES = ("faktura", "banka", "objednavka", "uloha", "marketing", "ine")
RENEWAL_KINDS = ("pzp", "havarijne", "stk", "ek", "poistka", "domena",
                 "predplatne", "zmluva", "ine")


@dataclass
class ExtractedPayment:
    supplier: str
    amount: float
    currency: str = "EUR"
    iban: str = ""
    variable_symbol: str = ""
    specific_symbol: str = ""
    constant_symbol: str = ""
    due_date: str = ""
    note: str = ""


@dataclass
class ExtractedTask:
    description: str
    due_date: str = ""


@dataclass
class ExtractedPaid:
    amount: float
    variable_symbol: str = ""
    counterparty_iban: str = ""
    date: str = ""
    description: str = ""


@dataclass
class ExtractedExpiration:
    kind: str
    subject: str = ""
    expires_on: str = ""
    note: str = ""


@dataclass
class Extraction:
    payments: list[ExtractedPayment] = field(default_factory=list)
    tasks: list[ExtractedTask] = field(default_factory=list)
    paid_transactions: list[ExtractedPaid] = field(default_factory=list)
    expirations: list[ExtractedExpiration] = field(default_factory=list)
    summary: str = ""
    category: str = "ine"
    # prílohy, ktoré sa nepodarilo odomknúť žiadnym heslom z PDF_PASSWORDS
    locked_pdfs: list = field(default_factory=list)


def _maybe_decrypt_pdf(data: bytes, passwords: list[str]) -> Optional[bytes]:
    """Odomkne heslom chránené PDF (bankové výpisy, poistky...).

    Vráti pôvodné dáta, ak PDF nie je šifrované; odomknuté PDF, ak sadlo
    niektoré z hesiel; None, ak sa PDF nepodarilo otvoriť.
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return data  # bez pypdf necháme PDF tak, ako je
    import io

    try:
        reader = PdfReader(io.BytesIO(data))
        if not reader.is_encrypted:
            return data
        for password in passwords:
            try:
                if reader.decrypt(password):
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    out = io.BytesIO()
                    writer.write(out)
                    return out.getvalue()
            except Exception:
                continue
    except Exception:
        return None
    return None


def _sniff_media_type(data: bytes) -> Optional[str]:
    """Určí skutočný typ súboru z magických bajtov.

    E-maily občas deklarujú nesprávny content-type (napr. PNG označené ako
    image/jpeg) a API taký obsah odmietne — preto typ overujeme z obsahu.
    """
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _build_content(
    mail: Email, pdf_passwords: Optional[list[str]] = None,
    locked: Optional[list] = None,
) -> list[dict]:
    content: list[dict] = []
    for att in mail.attachments:
        media_type = _sniff_media_type(att.data)
        if media_type == "application/pdf":
            data = _maybe_decrypt_pdf(att.data, pdf_passwords or [])
            if data is None:
                print(
                    f"  🔒 príloha {att.filename!r} je zaheslované PDF a nesedí "
                    "žiadne heslo z PDF_PASSWORDS — preskakujem",
                    file=sys.stderr,
                )
                if locked is not None:
                    locked.append(att.filename)
                continue
            content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(data).decode("ascii"),
                },
            })
        elif media_type and media_type.startswith("image/"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64.standard_b64encode(att.data).decode("ascii"),
                },
            })
    content.append({
        "type": "text",
        "text": (
            f"Od: {mail.sender}\n"
            f"Predmet: {mail.subject}\n"
            f"Dátum: {mail.date}\n\n"
            f"{mail.body[:20000]}"
        ),
    })
    return content


def extract(cfg: Config, mail: Email, client: Optional[anthropic.Anthropic] = None) -> Extraction:
    """Pošle e-mail (text + PDF/obrázkové prílohy) do Claude a vráti extrahované dáta."""
    if client is None:
        cfg.require("anthropic_api_key")
        client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    def _call(content: list[dict]):
        return client.messages.create(
            model=cfg.claude_model,
            max_tokens=16000,
            system=system_prompt(getattr(cfg, "account_type", "business"),
                                 getattr(cfg, "lang", "sk")),
            output_config={"format": OUTPUT_SCHEMA},
            messages=[{"role": "user", "content": content}],
        )

    locked: list = []
    content = _build_content(mail, cfg.pdf_passwords, locked)
    try:
        response = _call(content)
    except anthropic.BadRequestError:
        # napr. heslom chránené PDF alebo poškodená príloha — skúsime aspoň
        # samotný text e-mailu, nech sa nezahodí celá správa
        text_only = [b for b in content if b["type"] == "text"]
        if len(text_only) == len(content):
            raise
        response = _call(text_only)

    if response.stop_reason == "refusal":
        return Extraction(locked_pdfs=locked)

    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)
    result = parse_extraction(data)
    result.locked_pdfs = locked
    return result


def parse_extraction(data: dict) -> Extraction:
    payments = []
    for p in data.get("payments", []):
        try:
            amount = float(p.get("amount", 0))
        except (TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        payments.append(ExtractedPayment(
            supplier=p.get("supplier", "").strip(),
            amount=round(amount, 2),
            currency=(p.get("currency") or "EUR").strip().upper(),
            iban=p.get("iban", "").replace(" ", "").upper(),
            variable_symbol=p.get("variable_symbol", "").strip(),
            specific_symbol=p.get("specific_symbol", "").strip(),
            constant_symbol=p.get("constant_symbol", "").strip(),
            due_date=p.get("due_date", "").strip(),
            note=p.get("note", "").strip(),
        ))
    tasks = [
        ExtractedTask(description=t["description"].strip(), due_date=t.get("due_date", "").strip())
        for t in data.get("tasks", [])
        if t.get("description", "").strip()
    ]
    paid = []
    for tr in data.get("paid_transactions", []):
        try:
            amount = abs(float(tr.get("amount", 0)))
        except (TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        paid.append(ExtractedPaid(
            amount=round(amount, 2),
            variable_symbol=tr.get("variable_symbol", "").strip(),
            counterparty_iban=tr.get("counterparty_iban", "").replace(" ", "").upper(),
            date=tr.get("date", "").strip(),
            description=tr.get("description", "").strip(),
        ))
    expirations = []
    for e in data.get("expirations", []):
        kind = (e.get("kind") or "ine").strip()
        if kind not in RENEWAL_KINDS:
            kind = "ine"
        if not (e.get("subject", "").strip() or e.get("expires_on", "").strip()):
            continue
        expirations.append(ExtractedExpiration(
            kind=kind,
            subject=e.get("subject", "").strip(),
            expires_on=e.get("expires_on", "").strip(),
            note=e.get("note", "").strip(),
        ))
    category = data.get("category", "ine")
    if category not in CATEGORIES:
        category = "ine"
    return Extraction(
        payments=payments, tasks=tasks, paid_transactions=paid,
        expirations=expirations,
        summary=data.get("summary", "").strip(), category=category,
    )
