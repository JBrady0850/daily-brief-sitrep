"""When a scheduled cloud run should send the brief.

GitHub's cron schedules are in UTC and cannot follow a time zone, so the
workflow fires at two UTC times an hour apart (one for standard time, one for
daylight saving time). Each run asks decide() whether to send:

1. Not yet the delivery time in the reader's time zone: skip, unless this is
   the last scheduled run of the UTC day, in which case send early and warn
   (the cron lines do not match the time zone, so this run is the last chance).
2. Already sent today (local date): skip.
3. At or after the delivery time: send. A run more than WINDOW_HOURS late still
   sends, with a warning, because a late brief beats no brief.

Everything here is pure and tested; the clock and the workflow file are passed in.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

WINDOW_HOURS = 3
_CRON = re.compile(r"""cron:\s*["']([^"']+)["']""")
_DAILY = re.compile(r"^\s*(\d{1,2})\s+(\d{1,2})\s+\*\s+\*\s+\*\s*$")


def zone(name: str):
    """A tzinfo for an IANA name, or None when it is empty or unknown here."""
    if not name:
        return None
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:  # unknown name, or no time zone data on this computer
        return None


def local_now(now_utc: datetime, tz_name: str) -> datetime:
    tz = zone(tz_name)
    return now_utc.astimezone(tz) if tz else now_utc.astimezone()


def parse_crons(workflow_text: str) -> list:
    """The daily (minute hour * * *) cron lines in a workflow, as (hour, minute)."""
    out = []
    for expr in _CRON.findall(workflow_text):
        m = _DAILY.match(expr)
        if m:
            minute, hour = int(m.group(1)), int(m.group(2))
            if 0 <= minute < 60 and 0 <= hour < 24:
                out.append((hour, minute))
    return sorted(set(out))


def read_crons(path: Optional[str]) -> list:
    if not path:
        return []
    try:
        return parse_crons(Path(path).read_text(encoding="utf-8"))
    except OSError:
        return []


def fired_time(expr: Optional[str]) -> Optional[tuple]:
    m = _DAILY.match(expr or "")
    return (int(m.group(2)), int(m.group(1))) if m else None


def decide(now_utc: datetime, delivery: dict, sent_dates: list, crons: list,
           fired: Optional[str] = None) -> dict:
    """Returns {"send": bool, "date": local YYYY-MM-DD, "reason": text, "warning": text}."""
    tz_name = (delivery or {}).get("timezone") or ""
    when = (delivery or {}).get("time") or ""
    now_local = local_now(now_utc, tz_name)
    day = now_local.strftime("%Y-%m-%d")
    where = tz_name or "this computer's time zone"
    if tz_name and zone(tz_name) is None:
        return {"send": True, "date": day, "reason": "time zone not recognised, sending now",
                "warning": f"Time zone {tz_name!r} is not known here; check delivery.timezone in the settings."}
    if day in (sent_dates or []):
        return {"send": False, "date": day, "reason": f"already sent for {day}", "warning": ""}
    if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", when or ""):
        return {"send": True, "date": day, "reason": "no delivery time set, sending now", "warning": ""}
    hh, mm = int(when[:2]), int(when[3:])
    target = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if now_local < target:
        this = fired_time(fired) or (now_utc.hour, now_utc.minute)
        later = [c for c in crons if c > this]
        if crons and not later:
            return {"send": True, "date": day, "reason": "last scheduled run of the day, sending early",
                    "warning": (f"Sent at {now_local:%H:%M} {where}, before the {when} delivery time, because no later "
                                "run is scheduled today. Update the cron lines in .github/workflows/daily-brief.yml "
                                "(the app's Every day tab shows the right ones).")}
        wait = target - now_local
        return {"send": False, "date": day, "warning": "",
                "reason": f"not yet {when} {where} (it is {now_local:%H:%M}); {_hm(wait)} to go"}
    late = now_local - target
    warning = ""
    if late > timedelta(hours=WINDOW_HOURS):
        warning = (f"Sent {_hm(late)} after the {when} delivery time. GitHub may have delayed the run, or the cron "
                   "lines do not match the time zone.")
    return {"send": True, "date": day, "reason": f"delivery time {when} {where} reached", "warning": warning}


def _hm(d: timedelta) -> str:
    mins = int(d.total_seconds() // 60)
    return f"{mins // 60}h {mins % 60:02d}m"


def crons_for(time_hhmm: str, tz_name: str, year: int) -> list:
    """The UTC cron lines that hit time_hhmm in tz_name in winter and in summer."""
    tz = zone(tz_name)
    if tz is None or not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", time_hhmm or ""):
        return []
    hh, mm = int(time_hhmm[:2]), int(time_hhmm[3:])
    out = []
    for month in (1, 7):
        local = datetime(year, month, 15, hh, mm, tzinfo=tz)
        u = local.astimezone(timezone.utc)
        line = f"{u.minute} {u.hour} * * *"
        if line not in out:
            out.append(line)
    return sorted(out, key=lambda s: (int(s.split()[1]), int(s.split()[0])))
