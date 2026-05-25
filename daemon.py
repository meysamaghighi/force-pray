"""Long-running watcher: triggers blocker.py at every prayer time.

Runs forever. Sleeps until the next prayer, opens the fullscreen blocker,
then sleeps to the next one. Restart-safe via state file (won't re-fire
the same prayer twice in a day).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import prayer_times

STATE = Path.home() / ".force-pray" / "state.json"
STATE.parent.mkdir(exist_ok=True)
HERE = Path(__file__).resolve().parent
PYTHON = HERE / ".venv" / "bin" / "python"
BLOCKER = HERE / "blocker.py"

# Prayers you actually want to be blocked for. Edit freely.
ACTIVE_PRAYERS = ["Fajr", "Dhuhr", "Maghrib"]

# How long after the scheduled time we're still willing to fire (minutes).
# If your laptop was asleep through Fajr, we don't ambush you 6 hours later.
GRACE_MIN = 30

LOG = Path.home() / ".force-pray" / "daemon.log"


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            return {}
    return {}


def save_state(s: dict) -> None:
    STATE.write_text(json.dumps(s))


def already_fired(prayer: str, when: datetime, s: dict) -> bool:
    key = f"{when.date().isoformat()}:{prayer}"
    return s.get("fired", {}).get(key) is True


def mark_fired(prayer: str, when: datetime, s: dict) -> None:
    s.setdefault("fired", {})[f"{when.date().isoformat()}:{prayer}"] = True
    # purge old entries (>14 days)
    cutoff = (date.today() - timedelta(days=14)).isoformat()
    s["fired"] = {k: v for k, v in s["fired"].items() if k.split(":")[0] >= cutoff}
    save_state(s)


def upcoming(now: datetime) -> tuple[str, datetime] | None:
    """Find next prayer in ACTIVE_PRAYERS, today or tomorrow."""
    for offset in (0, 1):
        d = now.date() + timedelta(days=offset)
        times = prayer_times.get_times(d)
        for name in ACTIVE_PRAYERS:
            dt = datetime.combine(d, times[name])
            if dt > now:
                return name, dt
    return None


def fire(prayer: str) -> None:
    log(f"firing blocker for {prayer}")
    try:
        subprocess.run([str(PYTHON), str(BLOCKER), "--prayer", prayer], check=False)
    except Exception as e:
        log(f"blocker failed: {e}")


def main() -> int:
    log("daemon started")
    state = load_state()

    while True:
        now = datetime.now()
        # Check if any active prayer is within the grace window and hasn't fired
        try:
            times_today = prayer_times.get_times(now.date())
        except Exception as e:
            log(f"fetch failed: {e}, sleeping 60s")
            time.sleep(60)
            continue

        fired_now = False
        for name in ACTIVE_PRAYERS:
            dt = datetime.combine(now.date(), times_today[name])
            late = (now - dt).total_seconds()
            if 0 <= late <= GRACE_MIN * 60 and not already_fired(name, dt, state):
                fire(name)
                mark_fired(name, dt, state)
                fired_now = True
                break

        if fired_now:
            time.sleep(60)  # give the blocker a beat before re-checking
            continue

        nxt = upcoming(now)
        if not nxt:
            time.sleep(300)
            continue
        name, when = nxt
        sleep_for = max(5, min(900, (when - datetime.now()).total_seconds()))
        log(f"next: {name} at {when.strftime('%Y-%m-%d %H:%M')} — sleeping {int(sleep_for)}s")
        time.sleep(sleep_for)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("interrupted")
        sys.exit(0)
