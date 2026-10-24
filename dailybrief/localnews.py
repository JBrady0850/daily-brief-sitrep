"""Local news by state: the news feeds of local TV stations, read on GitHub's servers
every four hours and published beside the web app as data/local/<STATE>.json, with
data/local/index.json listing what each file holds.

Station sites do not let web pages read their feeds, but GitHub's servers can. The
web page reads only the file for the reader's state and keeps the stories that name
the reader's town or a nearby place, so town news comes from GitHub alone and the
reader's town never leaves the browser. Free, no key, no account.

The station list is dailybrief/local_stations.json (rebuilt by hand with
tools/stations_source.py). Each feed is read once per run, a few at a time. A station
that does not answer keeps its stories from the file already on the site while they
are still recent, so one bad run cannot empty a state.
"""
import concurrent.futures as cf
import json
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from . import collect as C, engine as E

STATIONS_FILE = Path(__file__).with_name("local_stations.json")
STATIONS_SCHEMA = "daily-brief-local-stations/1"
SCHEMA = "daily-brief-local-news/1"
INDEX_SCHEMA = "daily-brief-local-index/1"
MAX_AGE_HOURS = 96     # the longest "older stories" window the app offers
PER_STATION = 30       # newest stories kept from each station
SUMMARY_CHARS = 300
WORKERS = 8            # feeds read at the same time
BUDGET_SECONDS = 600   # stations still unread after ten minutes count as not answering


def load_stations(path: Optional[Path] = None) -> list:
    data = json.loads(Path(path or STATIONS_FILE).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != STATIONS_SCHEMA or not isinstance(data.get("stations"), list):
        raise ValueError("not a station list")
    return [s for s in data["stations"] if isinstance(s, dict) and s.get("feed") and s.get("states")]


def quick_fetch(url: str) -> bytes:
    return C.fetch(url, timeout=12, retries=1)


def _story(it: dict, now_ms: int, station: dict) -> Optional[dict]:
    c = E.clean_item(it, SUMMARY_CHARS)
    ms = c["published_ms"]
    if ms is None or (now_ms - ms) / 3600000 > MAX_AGE_HOURS or ms - now_ms > 3600000:
        return None
    if not c["title"] or not E.valid_url(c["url"]):
        return None
    return {"title": c["title"], "url": c["url"], "source": E.collapse(station.get("name")) or c["source"],
            "source_url": E.collapse(station.get("site")) or c["source_url"], "published": E.iso_z(ms),
            "summary": c["summary"], "image": c["image"], "station": station["id"]}


def _recent(stories: list, now_ms: int) -> list:
    out = []
    for s in stories:
        ms = E.parse_iso(s.get("published")) if isinstance(s, dict) else None
        if ms is not None and (now_ms - ms) / 3600000 <= MAX_AGE_HOURS and E.valid_url(E.collapse(s.get("url"))):
            out.append(s)
    return out


def parse_state_file(text: str) -> dict:
    """A published state file, checked; raises ValueError when it is not one."""
    d = json.loads(text)
    if not isinstance(d, dict) or d.get("schema") != SCHEMA or not isinstance(d.get("stories"), list):
        raise ValueError("not a local news file")
    return d


def build(now_iso: str, stations: Optional[list] = None, fetcher: Optional[C.Fetcher] = None,
          previous: Optional[Callable[[str], Optional[dict]]] = None, workers: int = WORKERS,
          budget: float = BUDGET_SECONDS, log: Optional[Callable[[str], None]] = None) -> dict:
    """Returns {"index": ..., "states": {"FL": file, ...}}. `previous(state)` returns the
    state's file already on the site (or None); it is asked only for states with a
    station that did not answer."""
    stations = stations if stations is not None else load_stations()
    get = fetcher or quick_fetch
    say = log or (lambda s: None)
    now_ms = E.parse_iso(now_iso)
    got: dict = {}
    errors: dict = {}

    def read(st: dict) -> tuple:
        try:
            items = C.parse_feed(get(st["feed"]))
            kept = [x for x in (_story(it, now_ms, st) for it in items) if x]
            kept.sort(key=lambda x: x["published"], reverse=True)
            return st["id"], kept[:PER_STATION], ""
        except Exception as exc:  # noqa: BLE001 - one station never stops the run
            return st["id"], [], (str(exc) or type(exc).__name__)[:120]

    start = time.monotonic()
    ex = cf.ThreadPoolExecutor(max(1, workers))
    futures = [ex.submit(read, st) for st in stations]
    try:
        for f in cf.as_completed(futures, timeout=budget):
            sid, kept, err = f.result()
            got[sid] = kept
            if err:
                errors[sid] = err
    except cf.TimeoutError:
        pass
    ex.shutdown(wait=False, cancel_futures=True)
    for st in stations:
        if st["id"] not in got:
            got[st["id"]] = []
            errors[st["id"]] = "no answer within the time budget"
    say("Read %d station feeds in %.0fs: %d answered, %d did not." % (
        len(stations), time.monotonic() - start, len(stations) - len(errors), len(errors)))

    codes = sorted({c for st in stations for c in st["states"]})
    old_files: dict = {}
    files: dict = {}
    index_states: dict = {}
    carried_total = 0
    for code in codes:
        members = [st for st in stations if code in st["states"]]
        failed = [st["id"] for st in members if st["id"] in errors]
        stories = [s for st in members for s in got[st["id"]]]
        carried = 0
        if failed and previous:
            if code not in old_files:
                try:
                    old_files[code] = previous(code)
                except Exception:  # noqa: BLE001 - no earlier file is fine
                    old_files[code] = None
            old = old_files[code]
            if isinstance(old, dict) and old.get("schema") == SCHEMA and isinstance(old.get("stories"), list):
                keep = [s for s in _recent(old["stories"], now_ms) if s.get("station") in failed]
                stories += keep
                carried = len(keep)
        seen: set = set()
        unique = []
        for s in sorted(stories, key=lambda x: x["published"], reverse=True):
            k = E.norm_url(s["url"])
            if k and k not in seen:
                seen.add(k)
                unique.append(s)
        carried_total += carried
        files[code] = {"schema": SCHEMA, "generated_at": now_iso, "state": code,
                       "stations": [{"id": st["id"], "name": st.get("name", ""), "site": st.get("site", ""),
                                     "answered": st["id"] not in errors} for st in members],
                       "stories": unique}
        index_states[code] = {"stations": len(members), "answered": len(members) - len(failed),
                              "stories": len(unique), "kept_from_last_run": carried}
    index = {"schema": INDEX_SCHEMA, "generated_at": now_iso, "states": index_states,
             "not_answering": {sid: errors[sid] for sid in sorted(errors)}, "carried": carried_total}
    return {"index": index, "states": files}


def write(result: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for code, data in result["states"].items():
        _write_json(out_dir / (code + ".json"), data)
    _write_json(out_dir / "index.json", result["index"])


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:  # Python 3.9 has no write_text(newline=)
        fh.write(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(path)


def site_reader(site: str, fetcher: Optional[C.Fetcher] = None) -> Callable[[str], Optional[dict]]:
    """Reads a state's file from the published site, for the stations that did not answer."""
    base = site.rstrip("/") + "/data/local/"
    get = fetcher or quick_fetch

    def previous(code: str) -> Optional[dict]:
        return parse_state_file(get(base + code + ".json").decode("utf-8"))
    return previous


def stderr_log(line: str) -> None:
    print(line, file=sys.stderr, flush=True)
