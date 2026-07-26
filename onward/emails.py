"""Itinerárový e-mail s PNR kódom (anglicky — služba cieli na globálny trh).

E-mail otvorene hovorí, čo zákazník dostal: skutočnú, aerolinkou overiteľnú
rezerváciu bez letenky, platnú do uvedeného času. Žiadne predstieranie,
že ide o zaplatenú letenku.
"""

import sqlite3


def _fmt_time(iso: str) -> str:
    return iso.replace("T", " ").replace("Z", " UTC")[:22]


def itinerary(order: sqlite3.Row, segments: list[dict], brand: str) -> tuple[str, str, str]:
    """Vráti (subject, text, html)."""
    subject = f"{brand}: flight reservation {order['pnr']} — {order['origin']} → {order['destination']}"

    seg_lines = [
        f"  {s['flight']}  {s['origin']} → {s['destination']}"
        f"  dep {_fmt_time(s['departing_at'])}  arr {_fmt_time(s['arriving_at'])}"
        for s in segments
    ]
    text = "\n".join([
        f"Booking reference (PNR): {order['pnr']}",
        f"Airline: {order['airline']}",
        f"Passenger: {order['given_name']} {order['family_name']}",
        "",
        "Flights:",
        *seg_lines,
        "",
        f"This reservation is valid until {_fmt_time(order['hold_expires_at'])}.",
        "You can verify it on the airline's website under 'Manage booking'"
        " using the PNR and passenger surname.",
        "",
        "Important: this is a genuine flight reservation, not a paid ticket."
        " It cannot be used to board a flight. It is intended as supporting"
        " documentation (e.g. visa application, proof of onward travel)."
        " After the validity time the airline releases it automatically.",
    ])

    rows = "".join(
        f"<tr><td style='padding:6px 12px'><b>{s['flight']}</b></td>"
        f"<td style='padding:6px 12px'>{s['origin']} → {s['destination']}</td>"
        f"<td style='padding:6px 12px'>{_fmt_time(s['departing_at'])}</td>"
        f"<td style='padding:6px 12px'>{_fmt_time(s['arriving_at'])}</td></tr>"
        for s in segments
    )
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#1a2233">
  <h2 style="margin-bottom:4px">{brand}</h2>
  <p style="font-size:15px">Your flight reservation is confirmed.</p>
  <div style="background:#f2f5fa;border-radius:10px;padding:18px;text-align:center">
    <div style="font-size:13px;color:#667">Booking reference (PNR)</div>
    <div style="font-size:32px;font-weight:bold;letter-spacing:4px">{order['pnr']}</div>
    <div style="font-size:14px;margin-top:6px">{order['airline']}</div>
  </div>
  <p><b>Passenger:</b> {order['given_name']} {order['family_name']}</p>
  <table style="border-collapse:collapse;font-size:14px;width:100%">
    <tr style="background:#e8edf5"><th style="padding:6px 12px;text-align:left">Flight</th>
      <th style="padding:6px 12px;text-align:left">Route</th>
      <th style="padding:6px 12px;text-align:left">Departure</th>
      <th style="padding:6px 12px;text-align:left">Arrival</th></tr>
    {rows}
  </table>
  <p style="font-size:14px"><b>Valid until {_fmt_time(order['hold_expires_at'])}.</b>
    Verify it any time before then on the airline's website
    (&ldquo;Manage booking&rdquo;) with the PNR and passenger surname.</p>
  <p style="font-size:12px;color:#667">This is a genuine airline reservation
    without a ticket issued — suitable for visa applications and proof of
    onward travel. It cannot be used to board a flight, and the airline
    releases it automatically after the validity time.</p>
</div>"""
    return subject, text, html


def expired_notice(order: sqlite3.Row, brand: str) -> tuple[str, str, str]:
    subject = f"{brand}: reservation {order['pnr']} has expired"
    text = (f"Your reservation {order['pnr']} ({order['origin']} → {order['destination']})"
            " has reached the end of its validity and was released by the airline.\n"
            "If you need a fresh reservation, simply place a new order.")
    html = f"<p>{text}</p>"
    return subject, text, html
