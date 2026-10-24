"""Collects candidate stories from Google News RSS searches and publisher feeds,
and the forecast from Open-Meteo.

This runs on your computer (the desktop app or a scheduled run) or on GitHub's
servers. The web page has its own collector (app/js/collect.js), because Google
News does not let a web page read it. Nothing here needs an account or a key. A
source that fails is recorded in the health report and the brief still goes out
with whatever the other sources returned.
"""
from __future__ import annotations

import html
import math
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Callable, Optional

from . import engine as E

USER_AGENT = "Mozilla/5.0 (compatible; DailyBrief/" + E.VERSION + "; personal news digest)"
TIMEOUT = 20
MAX_BYTES = 5_000_000
GOOGLE_PAUSE = 0.6

Fetcher = Callable[[str], bytes]


class FetchError(Exception):
    pass


CERT_HELP = ("Python cannot check web site certificates. On a Mac with Python from python.org, open the "
             "Python folder in Applications and double-click Install Certificates.command, then try again.")


def fetch(url: str, timeout: int = TIMEOUT, retries: int = 2) -> bytes:
    """GET a URL with a browser-like agent; retries twice on network errors."""
    last: Optional[Exception] = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise FetchError("feed is larger than 5 MB")
                return data
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 401, 403, 410):
                raise FetchError(f"HTTP {exc.code}") from exc
            last = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                raise FetchError(CERT_HELP) from exc
            last = exc
        if attempt < retries:
            time.sleep(1 + 2 * attempt)
    raise FetchError(str(getattr(last, "reason", last) or "network error"))


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "br", "div", "li"):
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)


def html_to_text(s: str) -> str:
    if not s:
        return ""
    if "<" not in s:
        return E.collapse(html.unescape(s))
    p = _Text()
    try:
        p.feed(s)
        p.close()
    except Exception:  # malformed markup: fall back to the raw text
        return E.collapse(html.unescape(s))
    return E.collapse("".join(p.parts))


def first_sentences(text: str, n: int = 2) -> str:
    out, count = [], 0
    for chunk in text.replace("? ", "?|").replace("! ", "!|").replace(". ", ".|").split("|"):
        out.append(chunk)
        count += 1
        if count >= n:
            break
    return E.collapse(" ".join(out))


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child(el: ET.Element, name: str) -> Optional[ET.Element]:
    want = name.lower()
    for c in el:
        if _local(c.tag) == want:
            return c
    return None


def _text(el: Optional[ET.Element]) -> str:
    return "" if el is None else "".join(el.itertext())


_IMG_TAG = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.I)


def _image(it: ET.Element) -> str:
    """The story's photo from media:content, media:thumbnail, an image enclosure
    or the first picture in its HTML. Only https links count."""
    cands = []
    for c in it.iter():
        ln = _local(c.tag)
        typ = (c.get("type") or "").lower()
        medium = (c.get("medium") or "").lower()
        if ln == "content" and c.get("url") and (medium == "image" or typ.startswith("image/") or (not typ and not medium)):
            cands.append(c.get("url"))
        elif ln == "thumbnail" and c.get("url"):
            cands.append(c.get("url"))
        elif ln == "enclosure" and typ.startswith("image/") and c.get("url"):
            cands.append(c.get("url"))
    markup = " ".join(_text(_child(it, n)) for n in ("encoded", "description", "content", "summary"))
    m = _IMG_TAG.search(markup)
    if m:
        cands.append(m.group(1).replace("&amp;", "&"))
    for u in cands:
        v = E.collapse(u)
        if E.valid_image(v):
            return v
    return ""


_ZONES = {"CET": "+0100", "CEST": "+0200", "BST": "+0100", "WET": "+0000", "WEST": "+0100", "EET": "+0200",
          "EEST": "+0300", "IST": "+0530", "JST": "+0900", "AEST": "+1000", "AEDT": "+1100", "NZST": "+1200",
          "NZDT": "+1300", "HST": "-1000", "AKST": "-0900", "AKDT": "-0800"}
_DAY_FORMATS = ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y")


def _date(raw: str) -> Optional[str]:
    """A feed date as UTC ISO. None when there is no date; the raw text when the
    date is there but unreadable, so the story is left out instead of being
    treated as an undated page."""
    raw = (raw or "").strip()
    if not raw:
        return None
    ms = E.parse_iso(re.sub(r"^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?)\s+(Z|[+-]\d{2}:?\d{2})$",
                            r"\1T\2\3", raw))
    if ms is None and re.fullmatch(r"\d{9,11}", raw):
        ms = int(raw) * 1000
    if ms is None:
        named = re.sub(r"\s([A-Z]{2,4})$", lambda m: " " + _ZONES.get(m.group(1), m.group(1)), raw)
        try:
            dt = parsedate_to_datetime(named)
        except (TypeError, ValueError, IndexError):
            dt = None
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ms = int(dt.timestamp()) * 1000
    if ms is None:
        for fmt in _DAY_FORMATS:
            try:
                ms = int(datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc).timestamp()) * 1000
                break
            except ValueError:
                continue
    return raw if ms is None else E.iso_z(ms)


def _declares_entities(data: bytes) -> bool:
    """True when the document declares XML entities anywhere (a billion-laughs
    guard that does not depend on the installed expat version)."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return "<!ENTITY" in data.decode("utf-16").upper()
        except UnicodeDecodeError:
            return True
    return b"<!ENTITY" in data.upper()


def parse_feed(data: bytes, google: bool = False) -> list:
    """RSS 2.0 or Atom to a list of candidate items."""
    if _declares_entities(data):
        raise FetchError("feed declares XML entities; refused")
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        start = data.find(b"<")
        try:
            root = ET.fromstring(data[start:]) if start > 0 else ET.fromstring(data.strip())
        except ET.ParseError as exc:
            raise FetchError(f"not a readable feed ({exc})") from exc
    items = []
    channel_title = ""
    channel_link = ""
    if _local(root.tag) == "rss":
        ch = _child(root, "channel")
        if ch is None:
            return []
        channel_title = E.collapse(_text(_child(ch, "title")))
        channel_link = E.collapse(_text(_child(ch, "link")))
        for it in ch:
            if _local(it.tag) != "item":
                continue
            src_el = _child(it, "source")
            source = E.collapse(_text(src_el)) or channel_title
            source_url = (src_el.get("url") if src_el is not None else "") or channel_link
            desc = html_to_text(_text(_child(it, "description")))
            items.append({
                "title": E.collapse(html.unescape(_text(_child(it, "title")))),
                "url": E.collapse(_text(_child(it, "link"))),
                "published": _date(_text(_child(it, "pubDate")) or _text(_child(it, "date"))),
                "summary": "" if google else first_sentences(desc),
                "source": source,
                "source_url": E.collapse(source_url),
                "image": "" if google else _image(it),
            })
    elif _local(root.tag) == "feed":
        channel_title = E.collapse(_text(_child(root, "title")))
        for ln in root:
            if _local(ln.tag) == "link" and ln.get("rel", "alternate") == "alternate":
                channel_link = ln.get("href", "")
        for it in root:
            if _local(it.tag) != "entry":
                continue
            link = ""
            for ln in it:
                if _local(ln.tag) == "link" and ln.get("rel", "alternate") == "alternate":
                    link = ln.get("href", "")
                    break
            desc = html_to_text(_text(_child(it, "summary")) or _text(_child(it, "content")))
            items.append({
                "title": E.collapse(html.unescape(_text(_child(it, "title")))),
                "url": E.collapse(link),
                "published": _date(_text(_child(it, "published")) or _text(_child(it, "updated"))),
                "summary": first_sentences(desc),
                "source": channel_title,
                "source_url": E.collapse(channel_link),
                "image": _image(it),
            })
    return items


def _fetch_parse(url: str, fetcher: Fetcher, google: bool) -> tuple:
    try:
        return parse_feed(fetcher(url), google=google), ""
    except FetchError as exc:
        return [], str(exc)
    except Exception as exc:  # one bad source never stops the brief
        return [], type(exc).__name__ + ": " + str(exc)


def _fresh_count(items: list, now_ms: int, window: int) -> int:
    n = 0
    for it in items:
        ms = E.parse_iso(it.get("published"))
        if ms is not None and (now_ms - ms) / 3600000 <= window:
            n += 1
    return n


def collect(cfg: dict, now_iso: str, ledger: Optional[dict] = None, fetcher: Optional[Fetcher] = None,
            progress: Optional[Callable[[str, int, int], None]] = None, pause: float = GOOGLE_PAUSE) -> tuple:
    """Returns (candidates, health). candidates maps category id to items."""
    fetcher = fetcher or fetch
    n = E.normalize_config(cfg)
    b = n["brief"]
    now_ms = E.parse_iso(now_iso)
    days1 = max(1, math.ceil(b["window_hours"] / 24))
    days2 = max(days1, math.ceil(b["backfill_max_hours"] / 24))
    cats = [E.resolve_category(c, n["reader"]) for c in n["categories"]]
    region = E.collapse(n["reader"].get("region"))
    # Google understands a place: town searches add the reader's state or region.
    local_ids = {c["id"] for c in n["categories"] if E.is_local_category(c)} if region else set()
    def feeds_of(c: dict) -> list:
        """A category's feeds plus its on-topic feeds, each address once."""
        return list(c["feeds"]) + [u for u in c.get("topic_feeds") or [] if u not in c["feeds"]]

    total_steps = sum(len([q for q in c["queries"] if E.collapse(q)]) + len(feeds_of(c)) for c in cats)
    step = 0
    candidates: dict = {}
    health: dict = {}

    def tick(label: str) -> None:
        nonlocal step
        step += 1
        if progress:
            progress(label, step, total_steps)

    feed_cache: dict = {}  # each feed address is read once per run, however many categories list it

    def read_feed(url: str) -> tuple:
        if url not in feed_cache:
            feed_cache[url] = _fetch_parse(url, fetcher, False)
        return feed_cache[url]

    for cat in cats:
        pool: list = []
        seen: set = set()
        h = {"queries": [], "feeds": []}

        def add(items: list, on_topic: bool = False) -> int:
            added = 0
            for it in items:
                key = E.norm_url(it.get("url"))
                if key and key not in seen:
                    seen.add(key)
                    pool.append(dict(it, on_topic=True) if on_topic else it)
                    added += 1
            return added

        queries = [q for q in cat["queries"] if E.collapse(q)]
        if cat["id"] in local_ids:
            queries = [q + ' "' + region.replace('"', "") + '"' for q in queries]
        for q in queries:
            items, err = _fetch_parse(E.google_news_url(q, days1, n), fetcher, True)
            h["queries"].append({"query": q, "days": days1, "items": len(items), "added": add(items), "error": err})
            tick(cat["name"])
            if pause:
                time.sleep(pause)
        for url in feeds_of(cat):
            items, err = read_feed(url)
            on_topic = url in (cat.get("topic_feeds") or [])
            h["feeds"].append({"url": url, "items": len(items), "fresh": _fresh_count(items, now_ms, b["window_hours"]),
                               "added": add(items, on_topic), "error": err, "on_topic": on_topic})
            tick(cat["name"])
        # Second pass: a category short of fresh, on-topic news may use labelled older items.
        if days2 > days1:
            trial = E.select_brief({cat["id"]: pool}, dict(n, categories=[c for c in n["categories"] if c["id"] == cat["id"]]),
                                   ledger, now_iso, now_iso[:10])
            want = cat["items"] if cat.get("items") else b["items_per_category"]
            fresh = len([i for i in trial["categories"][0]["items"] if i["recency"] == "news"])
            if fresh < want:
                for q in queries:
                    items, err = _fetch_parse(E.google_news_url(q, days2, n), fetcher, True)
                    h["queries"].append({"query": q, "days": days2, "items": len(items), "added": add(items), "error": err})
                    if pause:
                        time.sleep(pause)
        candidates[cat["id"]] = pool
        health[cat["id"]] = h
    return candidates, health


FORECAST = "https://api.open-meteo.com/v1/forecast"


def forecast_url(w: dict) -> str:
    """Mirrors forecastUrl in app/js/collect.js."""
    return (FORECAST + "?latitude=" + E.js_str(w["latitude"]) + "&longitude=" + E.js_str(w["longitude"])
            + "&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max&timezone=auto&forecast_days=4&temperature_unit="
            + ("celsius" if w.get("units") == "celsius" else "fahrenheit"))


def weather_from(data: object, w: dict, now_iso: str) -> dict:
    """The brief's weather block from an Open-Meteo answer (mirrors weatherFrom in collect.js)."""
    d = data.get("daily") if isinstance(data, dict) else None
    if not isinstance(d, dict) or not isinstance(d.get("time"), list):
        raise FetchError("the forecast came back empty")

    def num(v: object) -> Optional[float]:
        return v if E.is_num(v) else None

    def col(name: str) -> list:
        v = d.get(name)
        return v if isinstance(v, list) else []

    def at(lst: list, i: int) -> Optional[float]:
        return num(lst[i]) if i < len(lst) else None

    days = [{"date": E.js_str(t), "code": at(col("weather_code"), i), "hi": at(col("temperature_2m_max"), i),
             "lo": at(col("temperature_2m_min"), i), "rain": at(col("precipitation_probability_max"), i)}
            for i, t in enumerate(d["time"][:4])]
    c = data.get("current") if isinstance(data, dict) else None
    current = None
    if isinstance(c, dict) and num(c.get("temperature_2m")) is not None:
        current = {"temp": c["temperature_2m"], "code": num(c.get("weather_code"))}
    return {"place": E.collapse(w.get("place")), "units": "celsius" if w.get("units") == "celsius" else "fahrenheit",
            "source": "Open-Meteo", "fetched_at": now_iso, "current": current, "days": days}


def weather(cfg: dict, now_iso: str, fetcher: Optional[Fetcher] = None) -> Optional[dict]:
    w = E.normalize_config(cfg)["weather"]
    if not isinstance(w, dict) or w.get("enabled") is not True or not E.is_num(w.get("latitude")) or not E.is_num(w.get("longitude")):
        return None
    return weather_from(E.json_loads((fetcher or fetch)(forecast_url(w)).decode("utf-8")), w, now_iso)


def mark_unchecked(brief: dict, health: dict) -> dict:
    """An empty desk whose searches all failed was not checked (mirrors markUnchecked in collect.js)."""
    for bc in brief.get("categories") or []:
        h = (health or {}).get(bc.get("id"))
        if not h or bc.get("items"):
            continue
        tried = [q for q in h.get("queries") or [] if not q.get("note")]
        if tried and all(q.get("error") for q in tried):
            bc["unchecked"] = True
    return brief


def run_brief(cfg: dict, now_iso: str, date_str: str, ledger: Optional[dict], fetcher: Optional[Fetcher] = None,
              progress: Optional[Callable[[str, int, int], None]] = None, pause: float = GOOGLE_PAUSE) -> tuple:
    """Collect and select in one step. Returns (brief, health)."""
    candidates, health = collect(cfg, now_iso, ledger, fetcher, progress, pause)
    brief = E.select_brief(candidates, cfg, ledger, now_iso, date_str, "desktop")
    mark_unchecked(brief, health)
    try:
        wx = weather(cfg, now_iso, fetcher)
    except Exception as exc:  # the forecast never stops the brief
        wx = None
        health["_weather"] = {"error": type(exc).__name__ + ": " + str(exc)}
    if wx:
        brief["weather"] = wx
    return brief, health
