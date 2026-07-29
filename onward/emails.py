"""E-maily zákazníkovi (anglicky — služba cieli na globálny trh).

E-maily otvorene hovoria, čo zákazník dostal: skutočnú, aerolinkou
overiteľnú rezerváciu bez letenky, platnú do uvedeného času. Žiadne
predstieranie, že ide o zaplatenú letenku.
"""

import sqlite3


def _fmt_time(iso: str) -> str:
    return iso.replace("T", " ").replace("Z", " UTC")[:22]


def itinerary(order: sqlite3.Row, passengers: list[dict], segments: list[dict],
              brand: str, status_url: str = "",
              renewed: bool = False) -> tuple[str, str, str]:
    """Vráti (subject, text, html)."""
    prefix = "renewed reservation" if renewed else "flight reservation"
    subject = (f"{brand}: {prefix} {order['pnr']} — "
               f"{order['origin']} → {order['destination']}")

    pax_lines = [f"  {p['title'].capitalize()} {p['given_name']} {p['family_name']}"
                 for p in passengers]
    seg_lines = [
        f"  {s['flight']} ({s['airline']}{', ' + s['cabin'] if s.get('cabin') else ''})"
        f"  {s['origin']} {s.get('origin_name', '')} → "
        f"{s['destination']} {s.get('destination_name', '')}"
        f"  dep {_fmt_time(s['departing_at'])}  arr {_fmt_time(s['arriving_at'])}"
        + (f"  ({s['duration']})" if s.get("duration") else "")
        for s in segments
    ]
    intro = ("Your reservation has been renewed with a fresh booking —"
             " the previous PNR was released by the airline, use this new one:"
             if renewed else "Your flight reservation is confirmed.")
    text = "\n".join([
        intro, "",
        f"Booking reference (PNR): {order['pnr']}",
        f"Airline: {order['airline']}",
        "Passengers:", *pax_lines, "",
        "Flights:", *seg_lines, "",
        f"This reservation is valid until {_fmt_time(order['hold_expires_at'])}.",
        "You can verify it on the airline's website under 'Manage booking'"
        " using the PNR and passenger surname.",
        *([f"We will keep renewing it automatically until {order['valid_until']}."]
          if order["plan"] != "basic" else []),
        *([f"Your itinerary page: {status_url}"] if status_url else []),
        "",
        "A printable PDF itinerary is attached.",
        "",
        "Important: this is a genuine flight reservation, not a paid ticket."
        " It cannot be used to board a flight. It is intended as supporting"
        " documentation (e.g. visa application, proof of onward travel)."
        " After the validity time the airline releases it automatically.",
    ])

    pax_html = "".join(f"<li>{p['title'].capitalize()} {p['given_name']}"
                       f" {p['family_name']}</li>" for p in passengers)
    rows = "".join(
        f"<tr><td style='padding:6px 12px'><b>{s['flight']}</b><br>"
        f"<span style='font-size:12px;color:#667'>{s['airline']}"
        f"{' · ' + s['cabin'] if s.get('cabin') else ''}</span></td>"
        f"<td style='padding:6px 12px'>{s['origin']} → {s['destination']}<br>"
        f"<span style='font-size:12px;color:#667'>{s.get('origin_name', '')} →"
        f" {s.get('destination_name', '')}</span></td>"
        f"<td style='padding:6px 12px'>{_fmt_time(s['departing_at'])}</td>"
        f"<td style='padding:6px 12px'>{_fmt_time(s['arriving_at'])}"
        f"{'<br><span style=&quot;font-size:12px;color:#667&quot;>' + s['duration'] + '</span>' if s.get('duration') else ''}</td></tr>"
        for s in segments
    )
    renew_html = ("" if order["plan"] == "basic" else
                  f"<p style='font-size:14px'>We keep this reservation alive for you:"
                  f" whenever the airline releases a hold, we automatically create a"
                  f" fresh one and e-mail you the new PNR —"
                  f" until <b>{order['valid_until']}</b>.</p>")
    link_html = (f"<p style='font-size:14px'><a href='{status_url}'>Your itinerary"
                 f" page (live status &amp; PDF download)</a></p>" if status_url else "")
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#1a2233">
  <h2 style="margin-bottom:4px">{brand}</h2>
  <p style="font-size:15px">{intro}</p>
  <div style="background:#f2f5fa;border-radius:10px;padding:18px;text-align:center">
    <div style="font-size:13px;color:#667">Booking reference (PNR)</div>
    <div style="font-size:32px;font-weight:bold;letter-spacing:4px">{order['pnr']}</div>
    <div style="font-size:14px;margin-top:6px">{order['airline']}</div>
  </div>
  <p><b>Passengers:</b></p><ul>{pax_html}</ul>
  <table style="border-collapse:collapse;font-size:14px;width:100%">
    <tr style="background:#e8edf5"><th style="padding:6px 12px;text-align:left">Flight</th>
      <th style="padding:6px 12px;text-align:left">Route</th>
      <th style="padding:6px 12px;text-align:left">Departure</th>
      <th style="padding:6px 12px;text-align:left">Arrival</th></tr>
    {rows}
  </table>
  <p style="font-size:14px"><b>Valid until {_fmt_time(order['hold_expires_at'])}.</b>
    Verify it any time before then on the airline's website
    (&ldquo;Manage booking&rdquo;) with the PNR and passenger surname.
    A printable PDF itinerary is attached.</p>
  {renew_html}
  {link_html}
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
