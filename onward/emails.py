"""E-maily zákazníkovi (anglicky — služba cieli na globálny trh).

E-maily otvorene hovoria, čo zákazník dostal: skutočnú, aerolinkou
overiteľnú rezerváciu bez letenky, platnú do uvedeného času. Žiadne
predstieranie, že ide o zaplatenú letenku.
"""

import sqlite3
from html import escape as _e

from . import config

TEST_TEXT = ("TEST MODE — this is NOT a real reservation. It was created in a"
             " booking sandbox, does not exist in the airline's system, cannot be"
             " verified and must NOT be used for a visa application or any"
             " official purpose.")


def test_banner_html() -> str:
    if not config.test_mode():
        return ""
    return ("<div style='background:#b3261e;color:#fff;padding:14px 18px;"
            "border-radius:10px;font-size:14px;font-weight:bold;margin-bottom:16px'>"
            f"{TEST_TEXT}</div>")


def subject_prefix() -> str:
    return "[TEST — NOT VALID] " if config.test_mode() else ""


def _fmt_time(iso: str) -> str:
    return iso.replace("T", " ").replace("Z", " UTC")[:23]


def itinerary(order: sqlite3.Row, passengers: list[dict], segments: list[dict],
              brand: str, status_url: str = "",
              renewed: bool = False, qr_cid: str = "") -> tuple[str, str, str]:
    """Vráti (subject, text, html)."""
    prefix = "renewed reservation" if renewed else "flight reservation"
    subject = (f"{subject_prefix()}{brand}: {prefix} {order['pnr']} — "
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
        *([TEST_TEXT, ""] if config.test_mode() else []),
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
        "",
        f"Questions? Contact {config.contact_email()}",
    ])

    pax_html = "".join(f"<li>{_e(p['title'].capitalize())} {_e(p['given_name'])}"
                       f" {_e(p['family_name'])}</li>" for p in passengers)
    rows = "".join(
        f"<tr><td style='padding:6px 12px'><b>{_e(s['flight'])}</b><br>"
        f"<span style='font-size:12px;color:#667'>{_e(s['airline'])}"
        f"{' · ' + _e(s['cabin']) if s.get('cabin') else ''}</span></td>"
        f"<td style='padding:6px 12px'>{_e(s['origin'])} → {_e(s['destination'])}<br>"
        f"<span style='font-size:12px;color:#667'>{_e(s.get('origin_name', ''))} →"
        f" {_e(s.get('destination_name', ''))}</span></td>"
        f"<td style='padding:6px 12px'>{_e(_fmt_time(s['departing_at']))}</td>"
        f"<td style='padding:6px 12px'>{_e(_fmt_time(s['arriving_at']))}"
        + (f"<br><span style='font-size:12px;color:#667'>{_e(s['duration'])}</span>"
           if s.get("duration") else "")
        + "</td></tr>"
        for s in segments
    )
    renew_html = ("" if order["plan"] == "basic" else
                  f"<p style='font-size:14px'>We keep this reservation alive for you:"
                  f" whenever the airline releases a hold, we automatically create a"
                  f" fresh one and e-mail you the new PNR —"
                  f" until <b>{_e(order['valid_until'])}</b>.</p>")
    link_html = (f"<p style='font-size:14px'><a href='{_e(status_url)}'>Your itinerary"
                 f" page (live status &amp; PDF download)</a></p>" if status_url else "")
    qr_html = (
        f"<div style='text-align:center;margin:18px 0;padding:16px;"
        f"background:#f7f9fc;border-radius:10px'>"
        f"<img src='cid:{_e(qr_cid)}' width='140' height='140' alt='Verification QR'"
        f" style='display:block;margin:0 auto 8px'>"
        f"<div style='font-size:12px;color:#667'>Scan to verify this reservation"
        f" &amp; view its live status</div></div>" if qr_cid else "")
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#1a2233">
  <div style="background:#0d1b3d;background:linear-gradient(120deg,#0d1b3d,#16307a);
       color:#fff;padding:20px 24px;border-radius:12px 12px 0 0">
    <div style="font-size:22px;font-weight:bold;letter-spacing:.5px">&#9992; {_e(brand)}</div>
    <div style="font-size:13px;color:#c7d4f2;margin-top:2px">Flight reservation / itinerary</div>
  </div>
  <div style="border:1px solid #e6ebf4;border-top:0;border-radius:0 0 12px 12px;padding:22px 24px">
    {test_banner_html()}
    <p style="font-size:15px;margin-top:0">{_e(intro)}</p>
    <div style="background:#f2f5fa;border-radius:10px;padding:18px;text-align:center">
      <div style="font-size:13px;color:#667">Booking reference (PNR)</div>
      <div style="font-size:32px;font-weight:bold;letter-spacing:4px">{_e(order['pnr'] or '')}</div>
      <div style="font-size:14px;margin-top:6px">{_e(order['airline'] or '')}</div>
    </div>
    <p><b>Passengers:</b></p><ul>{pax_html}</ul>
    <table style="border-collapse:collapse;font-size:14px;width:100%">
      <tr style="background:#e8edf5"><th style="padding:6px 12px;text-align:left">Flight</th>
        <th style="padding:6px 12px;text-align:left">Route</th>
        <th style="padding:6px 12px;text-align:left">Departure</th>
        <th style="padding:6px 12px;text-align:left">Arrival</th></tr>
      {rows}
    </table>
    <p style="font-size:14px"><b>Valid until {_e(_fmt_time(order['hold_expires_at']))}.</b>
      Verify it any time before then on the airline's website
      (&ldquo;Manage booking&rdquo;) with the PNR and passenger surname.
      A printable PDF itinerary is attached.</p>
    {qr_html}
    {renew_html}
    {link_html}
    <p style="font-size:12px;color:#667">This is a genuine airline reservation
      without a ticket issued — suitable for visa applications and proof of
      onward travel. It cannot be used to board a flight, and the airline
      releases it automatically after the validity time.</p>
    <p style="font-size:12px;color:#667">{_e(config.OPERATOR['name'])}, {_e(config.OPERATOR['address'])}
      · <a href="mailto:{_e(config.contact_email())}">{_e(config.contact_email())}</a></p>
  </div>
</div>"""
    return subject, text, html


def expired_notice(order: sqlite3.Row, brand: str) -> tuple[str, str, str]:
    subject = f"{subject_prefix()}{brand}: reservation {order['pnr']} has expired"
    text = (f"Your reservation {order['pnr']} ({order['origin']} → {order['destination']})"
            " has reached the end of its validity and was released by the airline.\n"
            "If you need a fresh reservation, simply place a new order.")
    html = f"<p>{_e(text)}</p>"
    return subject, text, html
