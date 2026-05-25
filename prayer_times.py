"""Fetch and cache daily prayer times for Stockholm using the Aladhan API
with the Shia Ithna-Ashari (Jafari) calculation method — the same method
used by Imam Ali Islamic Center, Stockholm.

The PDF at imamalicenter.se/Bonetider-pdf/Stockholm.pdf renders times as
vector graphics, not selectable text, so direct parsing isn't reliable.
The API gives effectively the same times (within ~1 minute) for the same
method and location. If you want to fine-tune to match the PDF exactly,
edit OFFSETS_MIN below.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date, datetime, time, timedelta
from pathlib import Path

CITY = "Stockholm"
COUNTRY = "Sweden"
METHOD = 0  # Shia Ithna-Ashari, Leva Institute, Qum (Jafari)
SCHOOL = 0  # 0 = Shafi (matches Jafari Asr)

# Manual minute offsets if you want to align with the printed PDF.
# Positive = later. Adjust after comparing to the actual PDF.
OFFSETS_MIN = {
    "Fajr": 0,
    "Dhuhr": 0,
    "Asr": 0,
    "Maghrib": 0,
    "Isha": 0,
}

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

CACHE_DIR = Path.home() / ".force-pray"
CACHE_DIR.mkdir(exist_ok=True)


def _cache_path(d: date) -> Path:
    return CACHE_DIR / f"times-{d.isoformat()}.json"


def _fetch(d: date) -> dict[str, str]:
    url = (
        f"https://api.aladhan.com/v1/timingsByCity/{d.strftime('%d-%m-%Y')}"
        f"?city={CITY}&country={COUNTRY}&method={METHOD}&school={SCHOOL}"
    )
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.load(r)
    timings = data["data"]["timings"]
    return {p: timings[p][:5] for p in PRAYERS}


def get_times(d: date | None = None) -> dict[str, time]:
    """Return today's prayer times as a dict of name -> datetime.time."""
    d = d or date.today()
    cache = _cache_path(d)
    if cache.exists():
        raw = json.loads(cache.read_text())
    else:
        raw = _fetch(d)
        cache.write_text(json.dumps(raw))
        # purge old caches
        for old in CACHE_DIR.glob("times-*.json"):
            try:
                od = date.fromisoformat(old.stem.removeprefix("times-"))
                if (d - od).days > 7:
                    old.unlink()
            except Exception:
                pass

    out: dict[str, time] = {}
    for name, hhmm in raw.items():
        hh, mm = (int(x) for x in hhmm.split(":"))
        dt = datetime.combine(d, time(hh, mm)) + timedelta(minutes=OFFSETS_MIN.get(name, 0))
        out[name] = dt.time()
    return out


def next_prayer(now: datetime | None = None) -> tuple[str, datetime]:
    """Return (name, datetime) for the next upcoming prayer."""
    now = now or datetime.now()
    today = get_times(now.date())
    for name in PRAYERS:
        dt = datetime.combine(now.date(), today[name])
        if dt > now:
            return name, dt
    tomorrow = get_times(now.date() + timedelta(days=1))
    dt = datetime.combine(now.date() + timedelta(days=1), tomorrow["Fajr"])
    return "Fajr", dt


if __name__ == "__main__":
    t = get_times()
    print(f"Prayer times for {date.today().isoformat()} (Stockholm, Jafari):")
    for name, tm in t.items():
        print(f"  {name:8} {tm.strftime('%H:%M')}")
    name, when = next_prayer()
    print(f"\nNext: {name} at {when.strftime('%H:%M')} ({when - datetime.now()})")
