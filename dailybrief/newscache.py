"""The backup collection: stories for every library category, gathered on
GitHub's servers every four hours and published beside the web app as
data/news-cache.json.

The web page reads its publisher feeds first, then this file, and asks the
GDELT news index only for what is still short (the categories about the
reader's own town, and categories the reader typed). So a busy news index
(HTTP 429, too many requests) no longer empties a brief.

The file comes from the app's own address, so a browser may read it, and
reading it sends nothing about the reader anywhere. Here, on GitHub, the
collector reads Google News and every library feed, including the feeds that
do not allow web pages to read them. Free, no key, no account.

It works one category at a time against a time budget, asks Google News once
per category (a four-day search), reads each feed address once, and writes
whatever it gathered when the budget runs out. Google News sometimes turns
GitHub's servers away (503); after three refusals in a row the run reads the
feeds only. Stories from the last published file that are still recent and on
topic are kept, so one bad run cannot empty a category.
"""
import json
import sys
import time
from typing import Callable, Optional

from . import collect as C, engine as E
from .jsdata import library

SCHEMA = "daily-brief-news-cache/1"
PER_CATEGORY = 20       # newest on-topic stories kept for each category
MAX_AGE_HOURS = 96      # a little beyond the longest "older stories" window the app offers
SUMMARY_CHARS = 300
BUDGET_SECONDS = 600    # stop starting new categories after ten minutes
FIELDS = ("title", "url", "source", "source_url", "published", "summary", "image")


def is_local(cat: dict) -> bool:
    """Town categories depend on each reader's town, so they cannot be collected ahead."""
    text = json.dumps(cat)
    return bool(cat.get("needs_location")) or "{location}" in text or "{local_terms}" in text


def _keep(it: dict, now_ms: int, cat: dict, cfg: dict) -> Optional[dict]:
    """A story worth keeping: dated, recent, and on the library category's topic (the
    page checks it again against the reader's own version of the category)."""
    if E.gate_item(E.clean_item(it, SUMMARY_CHARS), cat, cfg):
        return None
    ms = E.parse_iso(it.get("published"))
    if ms is None or (now_ms - ms) / 3600000 > MAX_AGE_HOURS or ms - now_ms > 3600000:
        return None
    if not E.collapse(it.get("title")) or not E.valid_url(E.collapse(it.get("url"))):
        return None
    out = {k: E.collapse(it.get(k)) if k != "summary" else E.cut_summary(it.get(k) or "", SUMMARY_CHARS) for k in FIELDS}
    out["published"] = E.iso_z(ms)
    if not E.valid_image(out["image"]):
        out["image"] = ""
    if it.get("on_topic") is True:
        out["on_topic"] = True
    return out


def quick_fetch(url: str) -> bytes:
    """Shorter waits than the desktop app: a slow site costs seconds, not minutes."""
    return C.fetch(url, timeout=12, retries=1)


def _remember(fetcher: C.Fetcher) -> C.Fetcher:
    """Reads each feed address once for the whole run; a failure is remembered too."""
    seen: dict = {}

    def fetch(url: str) -> bytes:
        if url not in seen:
            try:
                seen[url] = (fetcher(url), None)
            except Exception as exc:  # noqa: BLE001 - replayed for every category that lists it
                seen[url] = (b"", exc)
        data, exc = seen[url]
        if exc:
            raise exc
        return data
    return fetch


def previous_stories(data: object) -> dict:
    """The stories of an earlier backup file, by category; anything unreadable counts as none."""
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("categories"), dict):
        return {}
    return {k: [x for x in v if isinstance(x, dict)] for k, v in data["categories"].items() if isinstance(v, list)}


def build(now_iso: str, lib: Optional[dict] = None, fetcher: Optional[C.Fetcher] = None,
          pause: float = C.GOOGLE_PAUSE, per_category: int = PER_CATEGORY, budget: float = BUDGET_SECONDS,
          log: Optional[Callable[[str], None]] = None, clock: Callable[[], float] = time.monotonic,
          previous: Optional[dict] = None) -> dict:
    """Collects every non-town library category and returns the file's content.
    `previous` is the last published file; its stories still recent and on topic stay."""
    lib = lib or library()
    say = log or (lambda s: None)
    get = _remember(fetcher or quick_fetch)
    prev = previous_stories(previous)
    searches: dict = {}  # shared by every category, so Google's refusals end the searching early
    cats = []
    for c in lib["categories"]:
        if is_local(c):
            continue
        cat = E.category_from_library(lib, c["id"])
        cat["queries"] = [q for q in cat.get("queries") or [] if E.collapse(q)][:1]  # one Google search each
        cats.append(cat)
    # One four-day window, so each category needs a single search and no second pass.
    cfg = E.normalize_config({"version": 1, "brief": {"window_hours": MAX_AGE_HOURS, "backfill_max_hours": MAX_AGE_HOURS},
                              "categories": cats})
    now_ms = E.parse_iso(now_iso)
    start = clock()
    out: dict = {}
    sources = {"searches": 0, "searches_failed": 0, "searches_skipped": 0, "feeds": 0, "feeds_failed": 0,
               "skipped": 0, "carried": 0}
    told = False
    for k, cat in enumerate(cfg["categories"], 1):
        rcat = E.resolve_category(cat, cfg["reader"])
        fresh: list = []
        errs: list = []
        elapsed = clock() - start
        over = elapsed > budget
        if over:
            sources["skipped"] += 1
        else:
            one = dict(cfg, categories=[cat])
            candidates, health = C.collect(one, now_iso, None, get, None, pause, searches)
            fresh = [x for x in (_keep(it, now_ms, rcat, cfg) for it in candidates.get(cat["id"], [])) if x]
            h = health.get(cat["id"], {"queries": [], "feeds": []})
            for q in h["queries"]:
                skipped = q.get("error") == C.SKIPPED
                sources["searches_skipped" if skipped else "searches"] += 1
                sources["searches_failed"] += 1 if q.get("error") and not skipped else 0
            for f in h["feeds"]:
                sources["feeds"] += 1
                sources["feeds_failed"] += 1 if f.get("error") else 0
            errs = [x["error"] for x in h["queries"] + h["feeds"] if x.get("error") and x["error"] != C.SKIPPED]
        # Earlier stories still recent and on topic stay, below anything new with the same address.
        have = {E.norm_url(x["url"]) for x in fresh}
        carried = []
        for x in (_keep(p, now_ms, rcat, cfg) for p in prev.get(cat["id"], [])):
            if x and E.norm_url(x["url"]) not in have:
                have.add(E.norm_url(x["url"]))
                x["_carried"] = True
                carried.append(x)
        both = sorted(fresh + carried, key=lambda x: x["published"], reverse=True)[:per_category]
        kept_old = sum(1 for x in both if x.pop("_carried", False))
        if over and not both:
            continue  # no time for this category and nothing earlier to keep
        out[cat["id"]] = both
        sources["carried"] += kept_old
        say("[%d/%d] %-22s %2d stories%s  %4.0fs%s" % (
            k, len(cfg["categories"]), cat["id"], len(both), (" (%d kept from the last run)" % kept_old) if kept_old else "",
            elapsed if over else clock() - start, ("  problems: " + "; ".join(errs[:2])) if errs else ""))
        if not told and searches.get("failures", 0) >= C.GOOGLE_GIVE_UP:
            told = True
            say("Google News turned away %d searches in a row; the rest of this run reads the feeds only." % C.GOOGLE_GIVE_UP)
    if sources["skipped"]:
        say("Time budget reached: %d categories had no time for new stories." % sources["skipped"])
    return {"schema": SCHEMA, "generated_at": now_iso, "categories": out, "sources": sources}


def stderr_log(line: str) -> None:
    print(line, file=sys.stderr, flush=True)
