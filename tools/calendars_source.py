"""Rebuilds app/data/calendars.js: the community event calendars of local TV stations.

Many stations in dailybrief/local_stations.json run their "events" page on CitySpark.
This tool finds each station's CitySpark calendar name (its slug) by asking CitySpark
for likely names, keeps a calendar whose own page is on the station's site, records
the calendar's home area (the centre point and radius it publishes), and writes the
list by state. The web page then asks the nearest calendar, from the
reader's own browser, for events near the reader's town, for the Things to Do category.

Only these addresses and place names are stored. No event is copied: CitySpark's
terms allow personal viewing, so events go straight from CitySpark to the reader's
page and nowhere else.

It reads the live web, so run it by hand (python tools/calendars_source.py) and review
the change; the tests never run it.
"""
import concurrent.futures as cf
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dailybrief import engine as E  # noqa: E402

STATIONS = ROOT / "dailybrief" / "local_stations.json"
OUT = ROOT / "app" / "data" / "calendars.js"
SCHEMA = "daily-brief-calendars/1"
UA = "DailyBrief/" + E.VERSION + " (+https://github.com/JBrady0850/daily-brief-sitrep)"
PORTAL = "https://portal.cityspark.com/PortalScripts/"


def fetch(url: str, limit: int = 400_000, data: bytes = None) -> tuple:
    """(status, text) of a page, reading at most `limit` bytes."""
    headers = {"User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read(limit).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:  # noqa: BLE001 - any failure means "no calendar found here"
        return 0, ""


def bare(host: str) -> str:
    return host.lower().split(":")[0].removeprefix("www.")


def guesses(st: dict) -> list:
    """CitySpark calendar names to try: a calendar is usually named after the station's
    call letters or its web address (mypanhandle.com is "MyPanhandle")."""
    stem = bare(urllib.parse.urlparse(st["site"]).netloc).rsplit(".", 1)[0]
    out = []
    for g in (re.sub(r"[^A-Za-z0-9]", "", st.get("name") or ""), stem.replace(".", "").replace("-", ""), stem):
        if g and g.lower() not in [x.lower() for x in out]:
            out.append(g)
    return out


def find_slug(st: dict) -> tuple:
    """(slug, calendar page) of the station's CitySpark calendar, or ("", ""). The station
    sites turn scripts away, so this asks CitySpark only: a calendar whose own page is on
    the station's site belongs to the station."""
    host = bare(urllib.parse.urlparse(st["site"]).netloc)
    for g in guesses(st):
        status, text = fetch(PORTAL + urllib.parse.quote(g), limit=8000)
        slug = re.search(r'"slug":"([A-Za-z0-9_\-]+)"', text)
        base = re.search(r'"baseUrl":"(https?://[^"\\]+)"', text)
        if status == 200 and slug and base and bare(urllib.parse.urlparse(base.group(1)).netloc) == host:
            page = "https://" + urllib.parse.urlparse(base.group(1)).netloc + (urllib.parse.urlparse(base.group(1)).path or "/")
            return slug.group(1), page
        time.sleep(0.3)
    return "", ""


def portal_home(slug: str) -> dict:
    """The calendar's own home area: centre, radius in miles and place name."""
    status, text = fetch(PORTAL + slug, limit=2_000_000)
    if status != 200:
        return {}
    def num(key):
        m = re.search(r'"' + key + r'":(-?[0-9]+(?:\.[0-9]+)?)', text)
        return float(m.group(1)) if m else None
    fmt = re.search(r'"urlFormat":"([A-Za-z]+)"', text)
    lat, lng, miles = num("lat"), num("lng"), num("distance")
    if lat is None or lng is None or (lat == 0 and lng == 0):
        return {}
    return {"lat": round(lat, 4), "lng": round(lng, 4), "miles": int(miles or 50),
            # "hash" or "hashBang": the calendar page opens one event at page#/details/<name>/<id>/<time>
            # (or #!/details/...). Other calendars get the organizer's link instead.
            "links": fmt.group(1) if fmt and fmt.group(1) in ("hash", "hashBang") else ""}


def answers(slug: str, home: dict) -> bool:
    """True when the calendar returns events around its own centre."""
    body = json.dumps({"start": time.strftime("%Y-%m-%d"), "daysToLoad": 3, "eventsPerDay": 3,
                       "lat": home["lat"], "lng": home["lng"], "distance": 25, "search": "", "sort": "",
                       "category": [], "labels": [], "defFilter": "all"}).encode()
    status, text = fetch("https://portal.cityspark.com/api/events/GetEventsByDay/" + slug, data=body)
    if status != 200:
        return False
    try:
        d = json.loads(text)
    except ValueError:
        return False
    return bool(d.get("Success")) and any(day.get("Events") for day in d.get("Value") or [])


def check(st: dict) -> dict:
    slug, page = find_slug(st)
    if not slug:
        return {}
    home = portal_home(slug)
    if not home or not answers(slug, home):
        return {}
    return {"slug": slug, "station": st["name"], "page": page, "states": st["states"], **home}


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stations", default=str(STATIONS), help="station list to read")
    ap.add_argument("--out", default=str(OUT), help="file to write")
    args = ap.parse_args()
    stations = json.loads(Path(args.stations).read_text(encoding="utf-8"))["stations"]
    print(len(stations), "stations to check")
    found = []
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        for i, r in enumerate(pool.map(check, stations), 1):
            if r:
                found.append(r)
            if i % 50 == 0:
                print(i, "checked,", len(found), "calendars", flush=True)
    by_slug = {}
    for c in found:
        if c["slug"] in by_slug:
            by_slug[c["slug"]]["states"] = sorted(set(by_slug[c["slug"]]["states"]) | set(c["states"]))
        else:
            by_slug[c["slug"]] = dict(c, states=sorted(c["states"]))
    states = {}
    for c in sorted(by_slug.values(), key=lambda c: c["slug"].lower()):
        for s in c["states"]:
            states.setdefault(s, []).append({k: c[k] for k in ("slug", "station", "page", "lat", "lng", "miles", "links")})
    data = {"schema": SCHEMA, "checked": time.strftime("%Y-%m-%d"), "source": "CitySpark calendars of the stations in dailybrief/local_stations.json",
            "states": dict(sorted(states.items()))}
    Path(args.out).write_text("/* Generated by tools/calendars_source.py. Do not edit. */\nwindow.DB_CALENDARS = "
                   + json.dumps(data, indent=1, ensure_ascii=False) + ";\n", encoding="utf-8", newline="\n")
    print("kept", len(by_slug), "calendars")
    print("calendars per state:", ", ".join(s + " " + str(len(v)) for s, v in data["states"].items()))
    print("states with none:", ", ".join(sorted({s for st in stations for s in st["states"]} - set(states))) or "none")


if __name__ == "__main__":
    main()
