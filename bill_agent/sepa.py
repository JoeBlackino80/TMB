"""SEPA XML (pain.001.001.03) — hromadný príkaz na úhradu.

Vygenerovaný súbor sa nahrá do internet bankingu (všetky slovenské banky
podporujú import SEPA XML) a banka pripraví všetky úhrady naraz.
Slovenské symboly (VS/SS/KS) sa prenášajú v EndToEndId v tvare /VS.../SS.../KS...
"""

from datetime import date, datetime
from xml.sax.saxutils import escape

from .store import Payment


def _end_to_end(p: Payment) -> str:
    if p.variable_symbol or p.specific_symbol or p.constant_symbol:
        return (f"/VS{p.variable_symbol or ''}"
                f"/SS{p.specific_symbol or ''}"
                f"/KS{p.constant_symbol or ''}")
    return "NOTPROVIDED"


def build_pain001(
    *, debtor_name: str, debtor_iban: str, payments: list[Payment],
    execution_date: date | None = None,
) -> str:
    """Vráti XML hromadného príkazu pre platby v EUR s vyplneným IBANom."""
    payments = [p for p in payments if p.iban and p.currency == "EUR"]
    if not payments:
        raise ValueError("Žiadna platba s IBANom v EUR na zaradenie do príkazu.")

    now = datetime.now()
    exec_date = (execution_date or date.today()).isoformat()
    msg_id = f"ROMARIUM-{now.strftime('%Y%m%d-%H%M%S')}"
    total = sum(p.amount for p in payments)

    txs = []
    for p in payments:
        name = escape((p.supplier or "Dodavatel")[:70])
        note = escape((p.note or p.source_subject or "")[:140])
        txs.append(f"""      <CdtTrfTxInf>
        <PmtId><EndToEndId>{escape(_end_to_end(p)[:35])}</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="EUR">{p.amount:.2f}</InstdAmt></Amt>
        <Cdtr><Nm>{name}</Nm></Cdtr>
        <CdtrAcct><Id><IBAN>{escape(p.iban.replace(' ', ''))}</IBAN></Id></CdtrAcct>
        {f'<RmtInf><Ustrd>{note}</Ustrd></RmtInf>' if note else ''}
      </CdtTrfTxInf>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now.strftime('%Y-%m-%dT%H:%M:%S')}</CreDtTm>
      <NbOfTxs>{len(payments)}</NbOfTxs>
      <CtrlSum>{total:.2f}</CtrlSum>
      <InitgPty><Nm>{escape(debtor_name[:70])}</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>{msg_id}-1</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <NbOfTxs>{len(payments)}</NbOfTxs>
      <CtrlSum>{total:.2f}</CtrlSum>
      <ReqdExctnDt>{exec_date}</ReqdExctnDt>
      <Dbtr><Nm>{escape(debtor_name[:70])}</Nm></Dbtr>
      <DbtrAcct><Id><IBAN>{escape(debtor_iban.replace(' ', ''))}</IBAN></Id></DbtrAcct>
      <ChrgBr>SLEV</ChrgBr>
{chr(10).join(txs)}
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>
"""
