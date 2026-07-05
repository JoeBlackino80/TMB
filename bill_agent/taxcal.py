"""Slovenský daňový kalendár — zákonné termíny podľa profilu podnikateľa.

Profil si klient zaškrtne v nastaveniach (TAX_PROFILE v .env, čiarkami oddelené):
  dph_monthly   — mesačný platca DPH (priznanie + platba do 25.)
  dph_quarterly — štvrťročný platca DPH
  szco          — SZČO (odvody do 8.)
  sro           — s.r.o. so štvrťročnými preddavkami na daň z príjmov

Termíny padajúce na víkend sa posúvajú na najbližší pracovný deň.
"""

from datetime import date, timedelta

PROFILES = {
    "dph_monthly": "mesačný platca DPH",
    "dph_quarterly": "štvrťročný platca DPH",
    "szco": "SZČO (odvody)",
    "sro": "s.r.o. — štvrťročné preddavky",
}

_QUARTER_ENDS = {3: 31, 6: 30, 9: 30, 12: 31}


def _next_workday(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def upcoming(profile: set, days_ahead: int, today: date | None = None) -> list[dict]:
    """Termíny v najbližších days_ahead dňoch: [{date, label}, ...]."""
    profile = {p for p in profile if p in PROFILES}
    if not profile:
        return []
    today = today or date.today()
    horizon = today + timedelta(days=days_ahead)
    items: list[dict] = []

    def add(d: date, label: str) -> None:
        d = _next_workday(d)
        if today <= d <= horizon:
            items.append({"date": d.isoformat(), "label": label})

    y, m = today.year, today.month
    months = []
    for _ in range(max(2, days_ahead // 28 + 2)):
        months.append((y, m))
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)

    for yy, mm in months:
        if "szco" in profile:
            add(date(yy, mm, 8),
                "Odvody SZČO — Sociálna a zdravotná poisťovňa (za predch. mesiac)")
        if "dph_monthly" in profile:
            add(date(yy, mm, 25), "DPH — priznanie a platba za predchádzajúci mesiac")
        if "dph_quarterly" in profile and mm in (1, 4, 7, 10):
            add(date(yy, mm, 25), "DPH — priznanie a platba za predchádzajúci štvrťrok")
        if "sro" in profile and mm in _QUARTER_ENDS:
            add(date(yy, mm, _QUARTER_ENDS[mm]),
                "Preddavok na daň z príjmov (štvrťročný)")
        if mm == 3:
            add(date(yy, 3, 31),
                "Daňové priznanie k dani z príjmov (ak nemáte odklad)")

    items.sort(key=lambda x: x["date"])
    return items
