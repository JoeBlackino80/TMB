"""PDF voucher hotelovej rezervácie (fpdf2 + QR), obdoba letového itinerára."""

from io import BytesIO

import qrcode
from fpdf import FPDF

from .pdf import _latin, INK, MUTED, LIGHT


def build_voucher(row, guests: list[dict], summ: dict, brand: str,
                  status_url: str = "") -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_fill_color(13, 27, 61)
    pdf.rect(0, 0, pdf.w, 26, style="F")
    pdf.set_xy(pdf.l_margin, 6)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(90, 9, _latin(brand))
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(199, 212, 242)
    pdf.cell(0, 9, "Hotel reservation", align="R")
    pdf.set_y(32)
    pdf.set_text_color(*INK)

    ref = summ.get("reference", "") or (row["reference"] or "")
    pdf.set_fill_color(*LIGHT)
    y = pdf.get_y()
    pdf.rect(pdf.l_margin, y, pdf.w - pdf.l_margin - pdf.r_margin, 24, style="F")
    pdf.set_y(y + 4)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 5, "BOOKING REFERENCE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 10, _latin(ref), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 7, _latin(summ.get("name", "")), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, _latin(summ.get("address", "")), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Check-in:  {row['check_in']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Check-out: {row['check_out']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, "Guests", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    for g in guests:
        pdf.cell(0, 6, _latin(f"{g['given_name']} {g['family_name']}"),
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if status_url:
        buf = BytesIO()
        qrcode.make(status_url).get_image().save(buf, format="PNG")
        y = pdf.get_y()
        pdf.image(buf, x=pdf.l_margin, y=y, w=26)
        pdf.set_xy(pdf.l_margin + 30, y + 8)
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, "Scan to view this reservation online.")
        pdf.set_y(y + 30)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 5,
        "This document confirms a genuine, cancellable hotel reservation held on"
        " a free-cancellation rate. It is intended as supporting documentation"
        " (visa application, proof of accommodation) and is released"
        " automatically before the cancellation deadline.")
    return bytes(pdf.output())
