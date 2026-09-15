"""E-mail s hotelovou rezerváciou (anglicky, ako itinerár letov)."""

import sqlite3
from html import escape as _e

from . import config
from .emails import TEST_TEXT, subject_prefix, test_banner_html


def confirmation(row: sqlite3.Row, guests: list[dict], summ: dict, brand: str,
                 status_url: str = "") -> tuple[str, str, str]:
    ref = summ.get("reference", "") or row["reference"] or ""
    subject = (f"{subject_prefix()}{brand}: hotel reservation {ref} —"
               f" {summ.get('name', row['city'])}")
    guest_lines = [f"  {g['given_name']} {g['family_name']}" for g in guests]
    text = "\n".join([
        *([TEST_TEXT, ""] if config.test_mode() else []),
        "Your hotel reservation is confirmed.", "",
        f"Booking reference: {ref}",
        f"Hotel: {summ.get('name', '')}",
        f"Address: {summ.get('address', '')}",
        f"Check-in: {row['check_in']}   Check-out: {row['check_out']}",
        "Guests:", *guest_lines, "",
        *([f"Your reservation page: {status_url}"] if status_url else []),
        "A printable PDF reservation is attached.", "",
        "Important: this is a genuine, cancellable hotel reservation intended as"
        " supporting documentation (visa application, proof of accommodation)."
        " It is held on a free-cancellation rate and will be released"
        " automatically before the cancellation deadline.",
        "",
        f"Questions? Contact {config.contact_email()}",
    ])
    guest_html = "".join(f"<li>{_e(g['given_name'])} {_e(g['family_name'])}</li>"
                         for g in guests)
    qr_html = (f"<div style='text-align:center;margin:18px 0;padding:16px;"
               f"background:#f7f9fc;border-radius:10px'><img src='cid:qr' width='140'"
               f" height='140' alt='QR' style='display:block;margin:0 auto 8px'>"
               f"<div style='font-size:12px;color:#667'>Scan to view this"
               f" reservation online</div></div>" if status_url else "")
    html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#1a2233">
  <div style="background:linear-gradient(120deg,#0d1b3d,#16307a);color:#fff;
       padding:20px 24px;border-radius:12px 12px 0 0">
    <div style="font-size:22px;font-weight:bold">&#127976; {_e(brand)}</div>
    <div style="font-size:13px;color:#c7d4f2;margin-top:2px">Hotel reservation</div>
  </div>
  <div style="border:1px solid #e6ebf4;border-top:0;border-radius:0 0 12px 12px;padding:22px 24px">
    {test_banner_html()}
    <p style="margin-top:0">Your hotel reservation is confirmed.</p>
    <div style="background:#f2f5fa;border-radius:10px;padding:18px;text-align:center">
      <div style="font-size:13px;color:#667">Booking reference</div>
      <div style="font-size:26px;font-weight:bold;letter-spacing:2px">{_e(ref)}</div>
    </div>
    <p><b>{_e(summ.get('name', ''))}</b><br>
      <span style="font-size:13px;color:#667">{_e(summ.get('address', ''))}</span></p>
    <p><b>Check-in:</b> {_e(row['check_in'])} &nbsp; <b>Check-out:</b> {_e(row['check_out'])}</p>
    <p><b>Guests:</b></p><ul>{guest_html}</ul>
    {qr_html}
    <p style="font-size:12px;color:#667">Genuine, cancellable hotel reservation
      for visa applications and proof of accommodation. Held on a free-cancellation
      rate and released automatically before the cancellation deadline.</p>
    <p style="font-size:12px;color:#667">{_e(config.OPERATOR['name'])}, {_e(config.OPERATOR['address'])}
      · <a href="mailto:{_e(config.contact_email())}">{_e(config.contact_email())}</a></p>
  </div>
</div>"""
    return subject, text, html
