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
"""
import json
from typing import Optional

from . import collect as C, engine as E
from .jsdata import library

SCHEMA = "daily-brief-news-cache/1"
PER_CATEGORY = 20       # newest stories kept for each category
MAX_AGE_HOURS = 96      # a little beyond the longest "older stories" window the app offers
SUMMARY_CHARS = 300
FIELDS = ("title", "url", "source", "source_url", "published", "summary", "image")


def is_local(cat: dict) -> bool:
    """Town categories depend on each reader's town, so they cannot be collected ahead."""
    text = json.dumps(cat)
    return bool(cat.get("needs_location")) or "{location}" in text or "{local_terms}" in text


def _keep(it: dict, now_ms: int) -> Optional[dict]:
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


def build(now_iso: str, lib: Optional[dict] = None, fetcher: Optional[C.Fetcher] = None,
          pause: float = C.GOOGLE_PAUSE, per_category: int = PER_CATEGORY) -> dict:
    """Collects every non-town library category and returns the file's content."""
    lib = lib or library()
    cats = [E.category_from_library(lib, c["id"]) for c in lib["categories"] if not is_local(c)]
    candidates, health = C.collect({"version": 1, "categories": cats}, now_iso, None, fetcher, None, pause)
    now_ms = E.parse_iso(now_iso)
    out: dict = {}
    for cid, items in candidates.items():
        kept = [k for k in (_keep(it, now_ms) for it in items) if k]
        kept.sort(key=lambda x: x["published"], reverse=True)
        out[cid] = kept[:per_category]
    sources = {"searches": 0, "searches_failed": 0, "feeds": 0, "feeds_failed": 0}
    for h in health.values():
        for q in h["queries"]:
            sources["searches"] += 1
            sources["searches_failed"] += 1 if q.get("error") else 0
        for f in h["feeds"]:
            sources["feeds"] += 1
            sources["feeds_failed"] += 1 if f.get("error") else 0
    return {"schema": SCHEMA, "generated_at": now_iso, "categories": out, "sources": sources}
