"""PDF itinerár (fpdf2) — príloha k e-mailu, na tlač pre ambasádu.

Dokument je poctivo označený ako "Flight reservation / itinerary"
so skutočným PNR a časom platnosti — nie je to napodobenina letenky.
"""

import unicodedata
from io import BytesIO

import qrcode
from fpdf import FPDF

INK = (22, 33, 58)
MUTED = (90, 104, 128)
ACCENT = (28, 100, 242)
LIGHT = (242, 245, 250)


def _latin(text: str) -> str:
    """Core PDF fonty sú latin-1; diakritiku mimo nej prepíš na ASCII."""
    try:
        text.encode("latin-1")
        return text
    except UnicodeEncodeError:
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def _fmt_time(iso: str) -> str:
    return iso.replace("T", " ").replace("Z", " UTC")[:22]


def build_itinerary(order, passengers: list[dict], segments: list[dict],
                    brand: str, status_url: str = "") -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # tmavomodrý pás s brandom cez celú šírku strany
    pdf.set_fill_color(13, 27, 61)
    pdf.rect(0, 0, pdf.w, 26, style="F")
    pdf.set_xy(pdf.l_margin, 6)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(90, 9, _latin(brand))
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(199, 212, 242)
    pdf.cell(0, 9, "Flight reservation / itinerary", align="R")
    pdf.set_y(32)
    pdf.set_text_color(*INK)

    # PNR box
    pdf.set_fill_color(*LIGHT)
    pdf.set_draw_color(*LIGHT)
    y = pdf.get_y()
    pdf.rect(pdf.l_margin, y, pdf.w - pdf.l_margin - pdf.r_margin, 26, style="F")
    pdf.set_y(y + 4)
    pdf.set_font("helvetica", "", 9)
    pdf.cell(0, 5, "BOOKING REFERENCE (PNR)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)
    pdf.set_font("helvetica", "B", 22)
    pdf.cell(0, 10, _latin(order["pnr"] or ""), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, _latin(order["airline"] or ""), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_text_color(*INK)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, _latin(f"Booking date: {_fmt_time(order['created_at'] or '')}"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, "Passengers", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    for p in passengers:
        name = f"{p['title'].capitalize()} {p['given_name']} {p['family_name']}"
        pdf.cell(0, 6, _latin(name), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, "Flights", new_x="LMARGIN", new_y="NEXT")
    for s in segments:
        pdf.set_fill_color(232, 237, 245)
        pdf.set_font("helvetica", "B", 10)
        header = f"  {s['flight']}  ·  {s['airline']}"
        if s.get("cabin"):
            header += f"  ·  {s['cabin']}"
        pdf.cell(0, 7, _latin(header), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 10)
        origin = f"{s['origin']} {s.get('origin_name', '')}".strip()
        dest = f"{s['destination']} {s.get('destination_name', '')}".strip()
        pdf.cell(0, 6, _latin(f"  {origin}  ->  {dest}"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        line = (f"  Departure {_fmt_time(s['departing_at'])}"
                f"    Arrival {_fmt_time(s['arriving_at'])}")
        if s.get("duration"):
            line += f"    Duration {s['duration']}"
        pdf.cell(0, 6, _latin(line), new_x="LMARGIN", new_y="NEXT")
        if s.get("baggage"):
            pdf.cell(0, 6, _latin(f"  Baggage: {s['baggage']}"),
                     new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.ln(2)
    pdf.ln(2)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, f"Valid until {_fmt_time(order['hold_expires_at'] or '')}",
             new_x="LMARGIN", new_y="NEXT")
    if status_url:
        buf = BytesIO()
        qrcode.make(status_url).get_image().save(buf, format="PNG")
        y = pdf.get_y() + 2
        pdf.image(buf, x=pdf.l_margin, y=y, w=26)
        pdf.set_xy(pdf.l_margin + 30, y + 8)
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, "Scan to verify this reservation and its live status online.")
        pdf.set_y(y + 30)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 5,
        "Verify this reservation on the airline's website under 'Manage booking'"
        " using the PNR and passenger surname.\n\n"
        "This document confirms a genuine airline reservation held without a ticket"
        " issued. It is intended as supporting documentation (visa application,"
        " proof of onward travel). It is not a flight ticket and cannot be used to"
        " board a flight; after the validity time the airline releases the"
        " reservation automatically.")
    return bytes(pdf.output())
