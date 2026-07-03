"""Extrakcia platieb a úloh z e-mailu pomocou Claude API (štruktúrovaný výstup)."""

import base64
import json
from dataclasses import dataclass, field
from typing import Optional

import anthropic

from .config import Config
from .emails import Email

SYSTEM_PROMPT = """Si asistent slovenského podnikateľa. Analyzuješ prijaté e-maily
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

Ak e-mail neobsahuje nič relevantné (newsletter, spam, bežná konverzácia),
vráť prázdne zoznamy."""

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
        },
        "required": ["payments", "tasks"],
        "additionalProperties": False,
    },
}


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
class Extraction:
    payments: list[ExtractedPayment] = field(default_factory=list)
    tasks: list[ExtractedTask] = field(default_factory=list)


def _build_content(mail: Email) -> list[dict]:
    content: list[dict] = []
    for att in mail.attachments:
        if att.content_type == "application/pdf" or att.filename.lower().endswith(".pdf"):
            content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64encode(att.data).decode("ascii"),
                },
            })
        elif att.content_type in ("image/png", "image/jpeg", "image/webp", "image/gif"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": att.content_type,
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

    response = client.messages.create(
        model=cfg.claude_model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        output_config={"format": OUTPUT_SCHEMA},
        messages=[{"role": "user", "content": _build_content(mail)}],
    )

    if response.stop_reason == "refusal":
        return Extraction()

    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)
    return parse_extraction(data)


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
    return Extraction(payments=payments, tasks=tasks)
