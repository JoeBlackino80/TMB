"""PDF itinerár (fpdf2) — príloha k e-mailu, na tlač pre ambasádu.

Dokument je poctivo označený ako "Flight reservation / itinerary"
so skutočným PNR a časom platnosti — nie je to napodobenina letenky.
"""

import unicodedata

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
                    brand: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_text_color(*INK)
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 10, _latin(brand), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, "Flight reservation / itinerary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

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
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, "Passengers", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    for p in passengers:
        name = f"{p['title'].capitalize()} {p['given_name']} {p['family_name']}"
        pdf.cell(0, 6, _latin(name), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 7, "Flights", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(232, 237, 245)
    widths = (28, 40, 56, 56)
    for w, head in zip(widths, ("Flight", "Route", "Departure", "Arrival")):
        pdf.cell(w, 7, head, fill=True)
    pdf.ln()
    pdf.set_font("helvetica", "", 9)
    for s in segments:
        pdf.cell(widths[0], 7, _latin(s["flight"]))
        pdf.cell(widths[1], 7, f"{s['origin']} -> {s['destination']}")
        pdf.cell(widths[2], 7, _fmt_time(s["departing_at"]))
        pdf.cell(widths[3], 7, _fmt_time(s["arriving_at"]))
        pdf.ln()
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, f"Valid until {_fmt_time(order['hold_expires_at'] or '')}",
             new_x="LMARGIN", new_y="NEXT")
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
