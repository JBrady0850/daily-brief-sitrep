"""Python mirror of app/js/engine.js.

Every function here has a twin in the JavaScript engine with the same name in
snake_case, and tests/test_parity.py feeds both the same inputs and requires
identical answers. Change both files together. Standard library only.
"""
from __future__ import annotations

import copy
import json
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

VERSION = "0.3.0"
SCHEMA = "daily-brief/v1"
MAX_CATEGORIES = 15
MAX_RECENT = 3000
MAX_LEDGER = 20000
MAX_SENT_DATES = 400
PALETTE = ["#1f3a5f", "#0b5e8f", "#0f6e5c", "#5b3485", "#a04000", "#8a5a00",
           "#1b6e3d", "#922b21", "#1d6aa0", "#34495e", "#6b4f2a", "#7a2f5f"]
SOCIAL_HOSTS = ["instagram.com", "facebook.com", "fb.watch", "tiktok.com", "youtube.com",
                "youtu.be", "pinterest.com", "twitter.com", "x.com", "threads.net", "reddit.com"]
PAPERWORK = ["Agency Information Collection", "Information Collection Request",
             "Proposed Collection", "Comment Request", "Submission for OMB Review", "OMB Control Number",
             "Sunshine Act Meeting", "Notice of Federal Advisory Committee"]
TRACKING = ["fbclid", "gclid", "mc_cid", "mc_eid", "cmpid", "ref", "ref_src", "igshid",
            "s_cid", "ocid", "mkt_tok"]
STOP = ["the", "and", "for", "with", "from", "that", "this", "are", "was", "has", "have",
        "its", "after", "over", "into", "about", "new", "says", "said", "will", "how", "why", "what"]
RECENCY = ["news", "backfill", "reference"]
SUBJECT_FIELDS = ["total", "date", "title", "empty"]
FILE_NOTE = "Saved settings are in the attached knowledge file daily-brief-settings.json. Use them; if that file is missing, start with the setup interview."

DEFAULTS: dict = {
    "version": 1,
    "brief": {
        "title": "The Morning Brief",
        "subject": "Daily Brief - {total}-Item SITREP | {date}",
        "window_hours": 24,
        "backfill_max_hours": 72,
        "items_per_category": 5,
        "summary_max_chars": 320,
        "allow_reference": True,
        "analysis": True,
        "conversation_starters": False,
        "watch_label": "Watch",
        "language": "en",
        "region": "US",
    },
    "reader": {"role": "", "location": "", "local_terms": [], "goals": [], "watch_list": []},
    "countdown": {"enabled": False, "label": "", "date": "", "start": "", "milestones": []},
    "delivery": {"time": "06:15", "timezone": "", "channels": ["issue"]},
    "weather": {"enabled": False, "place": "", "latitude": None, "longitude": None, "units": "fahrenheit"},
    "sources": {"avoid_hosts": list(SOCIAL_HOSTS), "prefer": []},
    "style": {"no_em_dashes": True},
    "categories": [],
}

_WS = re.compile("[\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?\Z", re.ASCII)
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}\Z", re.ASCII)
_URL = re.compile(r"^https?://([^/?#\s]+)[^\s]*\Z", re.IGNORECASE)
_HOST = re.compile(r"^https?://([^/?#\s]+)", re.IGNORECASE)
_NORM_URL = re.compile(r"^(https?)://([^/?#]+)([^?#]*)(\?[^#]*)?(#.*)?\Z", re.IGNORECASE)
_HEX = re.compile(r"^#[0-9a-fA-F]{6}\Z")
_IMAGE = re.compile(r"^https://[^/?#\s\"'<>\\]+\.[^/?#\s\"'<>\\]+(?:[/?#][^\s\"'<>\\]*)?\Z", re.IGNORECASE)
_ICON = re.compile(r"^[a-z0-9-]{1,32}\Z")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}\Z")
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
_EMAIL_IN_TEXT = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_IN_TEXT = re.compile(r"\d{3}[-. )]+\d{3}[-. ]+\d{4}", re.ASCII)
_LIST1 = re.compile(r"^(top|best)\s+\d+\b", re.ASCII)
_LIST2 = re.compile(r"\bbest\b.*\b20\d\d\b", re.ASCII)


# ----------------------------------------------------------------- helpers
def clone(v: Any) -> Any:
    return copy.deepcopy(v)


def is_obj(v: Any) -> bool:
    return isinstance(v, dict)


def js_truthy(v: Any) -> bool:
    """Truth the way JavaScript tests a JSON value: an empty object or list is true."""
    if v is None or v is False:
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v == v and v != 0
    if isinstance(v, str):
        return v != ""
    return True


def is_str(v: Any) -> bool:
    return isinstance(v, str)


def _whole(text: str) -> Any:
    x = float(text)
    return int(x) if x.is_integer() else x


def _no_constant(name: str) -> Any:
    raise ValueError(name + " is not valid JSON")


def js_str(v: Any) -> str:
    """String(v) the way JavaScript writes null, booleans and whole numbers."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def json_loads(text: Any) -> Any:
    """JSON the way a browser reads it: 24.0 is the number 24, and NaN or Infinity is an error."""
    return json.loads(text, parse_float=_whole, parse_constant=_no_constant)


def is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def str_list(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def collapse(s: Any) -> str:
    return _WS.sub(" ", "" if s is None else str(s)).strip(" ")


_EM_DASH = chr(0x2014)


def no_em_dash(s: str) -> str:
    """Feed text with each em dash turned into a hyphen; the length does not change."""
    return s.replace(_EM_DASH, "-")


def is_word_char(ch: str) -> bool:
    return len(ch) == 1 and (("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("0" <= ch <= "9"))


def pad2(n: int) -> str:
    return ("0" if n < 10 else "") + str(n)


def round1(x: float) -> float:
    return math.floor(x * 10 + 0.5) / 10


def merge(base: Any, over: Any) -> Any:
    out = clone(base)
    if not is_obj(over):
        return out
    for k, v in over.items():
        if is_obj(out.get(k)) and is_obj(v):
            out[k] = merge(out[k], v)
        else:
            out[k] = clone(v)
    return out


def parse_iso(s: Any) -> Optional[int]:
    """Milliseconds since 1970 (UTC), or None. Times without a zone are UTC."""
    if not is_str(s) or not s.strip():
        return None
    t = s.strip()
    if not _ISO.match(t):
        return None
    iso = t.replace(" ", "T", 1)
    if re.search(r"T\d{2}:\d{2}$", iso):
        iso += ":00"
    if "T" in iso and not re.search(r"(Z|[+-]\d{2}:?\d{2})$", iso):
        iso += "Z"
    iso = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", iso)
    if len(iso) == 10:
        iso += "T00:00:00Z"
    iso = iso.replace("Z", "+00:00")
    m = re.match(r"^(.*T\d{2}:\d{2}:\d{2})(\.\d+)?([+-]\d{2}:\d{2})$", iso)
    if not m:
        return None
    frac = (m.group(2) or "")[1:]
    try:
        dt = datetime.fromisoformat(m.group(1) + m.group(3))
    except ValueError:
        return None
    ms = int(frac[:3].ljust(3, "0")) if frac else 0
    return int(dt.timestamp()) * 1000 + ms


EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def utc_dt(ms: int) -> datetime:
    """A UTC datetime from milliseconds; unlike fromtimestamp it works before 1970 on Windows."""
    return EPOCH + timedelta(seconds=ms // 1000)


def iso_z(ms: int) -> str:
    return utc_dt(ms).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_date_str(s: Any) -> bool:
    if not is_str(s) or not _DATE.match(s):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def days_between(a: str, b: str) -> int:
    da = datetime.strptime(a, "%Y-%m-%d")
    db = datetime.strptime(b, "%Y-%m-%d")
    return (db - da).days


def valid_url(u: Any) -> bool:
    if not is_str(u):
        return False
    m = _URL.match(u.strip())
    return bool(m) and m.group(1).find(".") > 0


def valid_image(u: Any) -> bool:
    """A photo link the page may show: https only (an http picture breaks an https page), no quotes or spaces."""
    return is_str(u) and len(u) <= 2000 and bool(_IMAGE.match(u))


def is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def host_of(u: Any) -> str:
    m = _HOST.match(str(u or "").strip())
    if not m:
        return ""
    h = m.group(1).lower()
    at = h.rfind("@")
    if at >= 0:
        h = h[at + 1:]
    colon = h.find(":")
    if colon >= 0:
        h = h[:colon]
    return h[4:] if h.startswith("www.") else h


# ---------------------------------------------------------- term matching
def is_acronym(term: str) -> bool:
    if len(term) < 2 or len(term) > 6:
        return False
    if term != term.upper():
        return False
    return sum(1 for ch in term if "A" <= ch <= "Z") >= 2


def term_hit(text: Any, term: Any) -> bool:
    """Whole-word match; acronyms match case-sensitively."""
    t = collapse(term)
    if not t:
        return False
    acr = is_acronym(t)
    hay = str(text) if acr else str(text).lower()
    needle = t if acr else t.lower()
    want_before = is_word_char(needle[0])
    want_after = is_word_char(needle[-1])
    start = 0
    while True:
        i = hay.find(needle, start)
        if i < 0:
            return False
        before = hay[i - 1] if i > 0 else ""
        j = i + len(needle)
        after = hay[j] if j < len(hay) else ""
        ok_b = (not want_before) or (not before) or (not is_word_char(before))
        ok_a = (not want_after) or (not after) or (not is_word_char(after))
        if ok_b and ok_a:
            return True
        start = i + 1


def count_hits(text: str, terms: list) -> int:
    seen: set = set()
    n = 0
    for term in terms:
        key = collapse(term).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        if term_hit(text, term):
            n += 1
    return n


# ------------------------------------------------------------------ config
def resolve_category(cat: dict, reader: dict) -> dict:
    c = clone(cat)
    loc = collapse((reader or {}).get("location"))

    def sub(s: Any) -> str:
        return str(s).replace("{location}", loc)

    local: list = []
    for t in [loc] + list((reader or {}).get("local_terms") or []):
        v = collapse(t)
        if v and v.lower() not in [x.lower() for x in local]:
            local.append(v)
    c["name"] = sub(c.get("name") or "")
    c["description"] = sub(c.get("description") or "")
    c["queries"] = [sub(q) for q in (c.get("queries") or [])]
    groups = []
    for group in c.get("require") or []:
        out = []
        for term in group:
            if term == "{local_terms}":
                out.extend(local)
            else:
                out.append(sub(term))
        groups.append(out)
    c["require"] = groups
    c["exclude"] = [sub(x) for x in (c.get("exclude") or [])]
    return c


def normalize_config(cfg: Any) -> dict:
    out = merge(DEFAULTS, cfg if is_obj(cfg) else {})
    cats = out["categories"] if isinstance(out.get("categories"), list) else []
    norm = []
    for i, c in enumerate([c for c in cats if is_obj(c)]):
        base = {"id": "", "name": "", "description": "", "queries": [], "require": [], "exclude": [],
                "feeds": [], "color": PALETTE[i % len(PALETTE)], "items": None,
                "skip_listicles": False, "needs_location": False, "icon": ""}
        m = merge(base, c)
        if not is_str(m["color"]) or not _HEX.match(m["color"]):
            m["color"] = PALETTE[i % len(PALETTE)]
        norm.append(m)
    out["categories"] = norm
    return out


def placeholder_set(s: Any) -> list:
    return _PLACEHOLDER.findall(str(s))


def validate_config(cfg: Any) -> dict:
    errors: list = []
    warnings: list = []
    if not is_obj(cfg):
        return {"errors": ["The settings are not a JSON object."], "warnings": warnings}
    if "version" in cfg and (not is_int(cfg["version"]) or cfg["version"] != 1):
        errors.append("version must be 1.")
    for k in cfg:
        if k not in DEFAULTS:
            warnings.append('Unknown setting "' + k + '" is ignored.')
    n = normalize_config(cfg)
    b = n["brief"]

    def int_range(v: Any, lo: int, hi: int, label: str) -> None:
        if not is_int(v) or v < lo or v > hi:
            errors.append(label + " must be a whole number from " + str(lo) + " to " + str(hi) + ".")

    int_range(b["window_hours"], 1, 168, "brief.window_hours")
    int_range(b["backfill_max_hours"], 1, 336, "brief.backfill_max_hours")
    if is_int(b["window_hours"]) and is_int(b["backfill_max_hours"]) and b["backfill_max_hours"] < b["window_hours"]:
        errors.append("brief.backfill_max_hours must be at least brief.window_hours.")
    int_range(b["items_per_category"], 1, 10, "brief.items_per_category")
    int_range(b["summary_max_chars"], 80, 1000, "brief.summary_max_chars")
    for k in ["title", "subject", "watch_label", "language", "region"]:
        if not is_str(b[k]) or not collapse(b[k]):
            errors.append("brief." + k + " must be text.")
    if is_str(b["subject"]):
        for p in placeholder_set(b["subject"]):
            if p not in SUBJECT_FIELDS:
                errors.append("brief.subject uses {" + p + "}; allowed are {total}, {date}, {title} and {empty}.")
    for k in ["allow_reference", "analysis", "conversation_starters"]:
        if not isinstance(b[k], bool):
            errors.append("brief." + k + " must be true or false.")
    r = n["reader"]
    if not is_str(r["role"]) or not is_str(r["location"]):
        errors.append("reader.role and reader.location must be text.")
    for k in ["local_terms", "goals", "watch_list"]:
        if not str_list(r[k]):
            errors.append("reader." + k + " must be a list of text.")
    personal = json.dumps(r, separators=(",", ":"), ensure_ascii=False)
    if _EMAIL_IN_TEXT.search(personal):
        warnings.append("reader holds an email address; it is not needed and is better left out.")
    if _PHONE_IN_TEXT.search(personal):
        warnings.append("reader holds what looks like a phone number; it is not needed and is better left out.")
    cats = n["categories"]
    if not isinstance(cfg.get("categories"), list) or len(cats) == 0:
        errors.append("Add at least one category.")
    if len(cats) > MAX_CATEGORIES:
        errors.append("Use at most " + str(MAX_CATEGORIES) + " categories.")
    ids: set = set()
    for i, c in enumerate(cats):
        label = "Category " + str(i + 1) + (" (" + str(c["id"]) + ")" if c["id"] else "")
        if not is_str(c["id"]) or not _ID.match(c["id"]):
            errors.append(label + ": id must be 1 to 32 letters, numbers, dashes or underscores.")
        else:
            key = c["id"].lower()
            if key in ids:
                errors.append(label + ": id is used twice.")
            ids.add(key)
        if not is_str(c["name"]) or not collapse(c["name"]) or len(c["name"]) > 70:
            errors.append(label + ": name must be 1 to 70 characters.")
        q = c["queries"]
        if not str_list(q) or len([x for x in q if collapse(x)]) == 0 or len(q) > 6:
            errors.append(label + ": give 1 to 6 search queries.")
        req = c["require"]
        if not isinstance(req, list) or not all(str_list(g) and 0 < len(g) <= 80 for g in req):
            errors.append(label + ": require must be a list of term lists (1 to 80 terms each).")
        if not str_list(c["exclude"]):
            errors.append(label + ": exclude must be a list of text.")
        if not str_list(c["feeds"]) or not all(valid_url(f) for f in c["feeds"]):
            errors.append(label + ": feeds must be a list of http or https links.")
        if c["items"] is not None and (not is_int(c["items"]) or c["items"] < 1 or c["items"] > 10):
            errors.append(label + ": items must be a whole number from 1 to 10.")
        texts = [c["name"], c["description"]]
        texts += list(q) if isinstance(q, list) else []
        texts += list(c["exclude"]) if isinstance(c["exclude"], list) else []
        if isinstance(req, list):
            for g in req:
                if isinstance(g, list):
                    texts += g
        uses_local = False
        for t in texts:
            for p in placeholder_set(t):
                if p not in ("location", "local_terms"):
                    errors.append(label + ": unknown placeholder {" + p + "}.")
                else:
                    uses_local = True
        if not is_str(c["icon"]) or (c["icon"] and not _ICON.match(c["icon"])):
            errors.append(label + ": icon must be a short name like weather or football.")
        if (uses_local or c["needs_location"]) and not collapse(r["location"]):
            errors.append(label + ": needs your town in reader.location.")
    cd = n["countdown"]
    if cd["enabled"] is True:
        if not is_str(cd["label"]) or not collapse(cd["label"]):
            errors.append("countdown.label must be text.")
        if not is_date_str(cd["date"]):
            errors.append("countdown.date must be a date like 2027-06-30.")
        if cd["start"] and not is_date_str(cd["start"]):
            errors.append("countdown.start must be a date like 2026-01-01.")
        if is_date_str(cd["date"]) and is_date_str(cd["start"]) and cd["start"] > cd["date"]:
            errors.append("countdown.start must be before countdown.date.")
        ms = cd["milestones"]
        if not isinstance(ms, list) or not all(is_obj(m) and is_date_str(m.get("date")) and is_str(m.get("label"))
                                               and collapse(m.get("label")) for m in ms):
            errors.append("countdown.milestones must be a list of {date, label}.")
    elif cd["enabled"] is not False:
        errors.append("countdown.enabled must be true or false.")
    dv = n["delivery"]
    if not is_str(dv["time"]) or (dv["time"] and not re.match(r"^([01][0-9]|2[0-3]):[0-5][0-9]\Z", dv["time"])):
        errors.append("delivery.time must be a time like 06:15, or empty.")
    if not is_str(dv["timezone"]) or (dv["timezone"] and not re.match(r"^[A-Za-z_]+(/[A-Za-z0-9_+-]+)*\Z", dv["timezone"])):
        errors.append("delivery.timezone must be a time zone name like America/New_York, or empty.")
    if not str_list(dv["channels"]) or not dv["channels"] or not all(c in ("email", "issue") for c in dv["channels"]):
        errors.append('delivery.channels must be ["issue"].')
    elif "email" in dv["channels"]:
        warnings.append("delivery.channels lists email, which was removed in version 0.2.0; the brief arrives as a GitHub issue.")
    w = n["weather"]
    if not is_obj(w) or not isinstance(w.get("enabled"), bool):
        errors.append("weather.enabled must be true or false.")
    elif w["enabled"]:
        lat, lon = w.get("latitude"), w.get("longitude")
        if not (is_num(lat) and -90 <= lat <= 90 and is_num(lon) and -180 <= lon <= 180):
            errors.append("weather needs a place: pick your town so the forecast knows where you are.")
        if w.get("units") not in ("fahrenheit", "celsius"):
            errors.append("weather.units must be fahrenheit or celsius.")
        if not is_str(w.get("place")):
            errors.append("weather.place must be text.")
    if not str_list(n["sources"]["avoid_hosts"]):
        errors.append("sources.avoid_hosts must be a list of text.")
    if not isinstance(n["style"]["no_em_dashes"], bool):
        errors.append("style.no_em_dashes must be true or false.")
    if "email" in n:
        warnings.append("The email settings are no longer used (email delivery was removed in version 0.2.0); delete them.")
    return {"errors": errors, "warnings": warnings}


def category_from_library(lib: dict, cid: str) -> Optional[dict]:
    for c in (lib or {}).get("categories") or []:
        if c.get("id") == cid:
            out = clone(c)
            out.pop("group", None)
            return out
    return None


def config_from_pack(lib: dict, pack_id: str, overrides: Optional[dict] = None) -> dict:
    pack = next((p for p in (lib or {}).get("packs") or [] if p.get("id") == pack_id), None)
    cats = [c for c in (category_from_library(lib, i) for i in (pack or {}).get("categories", [])) if c]
    return merge(merge(DEFAULTS, {"categories": cats}), overrides or {})


# ------------------------------------------------------------- identities
def norm_url(u: Any) -> str:
    s = collapse(u)
    m = _NORM_URL.match(s)
    if not m:
        return s.lower()
    host = m.group(2).lower()
    if host.startswith("www."):
        host = host[4:]
    path = m.group(3) or ""
    while len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    if path == "/":
        path = ""
    kept = []
    for part in (m.group(4) or "").lstrip("?").split("&"):
        if not part:
            continue
        key = part.split("=")[0].lower()
        if key.startswith("utm_") or key in TRACKING:
            continue
        kept.append(part)
    kept.sort()
    return host + path + ("?" + "&".join(kept) if kept else "")


def strip_outlet(title: Any) -> str:
    t = collapse(title)
    for sep in (" - ", " | "):
        i = t.rfind(sep)
        if i > 0:
            head = t[:i]
            tail = t[i + len(sep):]
            if len(tail.split(" ")) <= 6 and len(head.split(" ")) >= 4:
                return head
    return t


def norm_title(title: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_outlet(title).lower()).strip()


def title_tokens(title: Any) -> list:
    out: list = []
    for w in norm_title(title).split(" "):
        if len(w) >= 3 and w not in STOP and w not in out:
            out.append(w)
    return out


def near_dup(a: Any, b: Any) -> bool:
    ta = a if isinstance(a, list) else title_tokens(a)
    tb = b if isinstance(b, list) else title_tokens(b)
    if len(ta) < 4 or len(tb) < 4:
        return False
    sb = set(tb)
    inter = sum(1 for w in ta if w in sb)
    union = len(ta) + len(tb) - inter
    return inter / union >= 0.75


# ------------------------------------------------------------------ ledger
def empty_ledger() -> dict:
    return {"version": 1, "urls": {}, "titles": {}, "recent": [], "sent_dates": []}


def clean_ledger(l: Any) -> dict:
    out = empty_ledger()
    if not is_obj(l):
        return out
    if is_obj(l.get("urls")):
        out["urls"] = {k: v for k, v in l["urls"].items() if is_str(v)}
    if is_obj(l.get("titles")):
        out["titles"] = {k: v for k, v in l["titles"].items() if is_str(v)}
    if isinstance(l.get("recent"), list):
        out["recent"] = [x for x in l["recent"] if is_str(x)][-MAX_RECENT:]
    if isinstance(l.get("sent_dates"), list):
        out["sent_dates"] = [x for x in l["sent_dates"] if is_date_str(x)][-MAX_SENT_DATES:]
    return out


def recent_index(ledger: dict) -> dict:
    """The recent headlines' words, read once, with each word pointing at the
    headlines that use it, so near-duplicate checks stay fast with a full history."""
    toks = [title_tokens(t) for t in ledger["recent"]]
    index: dict = {}
    for i, tk in enumerate(toks):
        if len(tk) >= 4:
            for w in tk:
                index.setdefault(w, []).append(i)
    return {"toks": toks, "index": index}


def ledger_has(ledger: Optional[dict], item: dict, idx: Optional[dict] = None) -> bool:
    if not ledger:
        return False
    nu = norm_url(item.get("url"))
    nt = norm_title(item.get("title"))
    if nu and nu in ledger["urls"]:
        return True
    if nt and nt in ledger["titles"]:
        return True
    toks = title_tokens(item.get("title"))
    if len(toks) < 4:
        return False
    idx = idx or recent_index(ledger)
    shared: dict = {}  # headline -> words in common; the same test as near_dup
    for w in toks:
        for i in idx["index"].get(w, ()):
            shared[i] = shared.get(i, 0) + 1
    la = len(toks)
    return any(inter / (la + len(idx["toks"][i]) - inter) >= 0.75 for i, inter in shared.items())


def _prune_map(m: dict) -> dict:
    if len(m) <= MAX_LEDGER:
        return m
    keys = sorted(m.keys(), key=lambda k: (m[k], k))
    return {k: m[k] for k in keys[len(keys) - MAX_LEDGER:]}


def ledger_add(ledger: Any, brief: dict, sent: bool = True) -> dict:
    """Remembers a brief's stories. sent=False ("Mark as read") leaves the day's
    delivery open, so a scheduled send still goes out."""
    l = clean_ledger(ledger)
    day = brief.get("date") if is_date_str((brief or {}).get("date")) else "1970-01-01"
    for cat in (brief or {}).get("categories") or []:
        for it in cat.get("items") or []:
            nu = norm_url(it.get("url"))
            nt = norm_title(it.get("title"))
            if nu:
                l["urls"][nu] = day
            if nt:
                l["titles"][nt] = day
                l["recent"].append(nt)
    l["recent"] = l["recent"][-MAX_RECENT:]
    if sent and day not in l["sent_dates"]:
        l["sent_dates"].append(day)
    l["sent_dates"] = l["sent_dates"][-MAX_SENT_DATES:]
    l["urls"] = _prune_map(l["urls"])
    l["titles"] = _prune_map(l["titles"])
    return l


def ledger_size(ledger: Optional[dict]) -> int:
    return len((ledger or {}).get("urls") or {})


# -------------------------------------------------------------- freshness
def humanize_age(hours: Any) -> str:
    if not isinstance(hours, (int, float)) or isinstance(hours, bool) or not math.isfinite(hours):
        return "undated"
    h = max(0, hours)
    if h < 1:
        return "under 1h"
    if h < 24:
        return str(math.floor(h)) + "h ago"
    d = math.floor(h / 24)
    rem = math.floor(h - d * 24)
    return str(d) + "d " + str(rem) + "h ago" if rem else str(d) + "d ago"


def classify(published_ms: Optional[int], now_ms: int, brief: dict) -> dict:
    if published_ms is None:
        return {"recency": "reference", "age": None} if brief["allow_reference"] else {"reject": "undated"}
    age = (now_ms - published_ms) / 3600000
    if age < -48:
        return {"reject": "bad date"}
    if age < 0:
        age = 0
    if age <= brief["window_hours"]:
        return {"recency": "news", "age": age}
    if age <= brief["backfill_max_hours"]:
        return {"recency": "backfill", "age": age}
    return {"reject": "too old"}


def cut_summary(text: Any, max_chars: int) -> str:
    s = collapse(text)
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars - 3]
    sp = cut.rfind(" ")
    if sp > max_chars / 2:
        cut = cut[:sp]
    return re.sub(r"[ ,.;:]+$", "", cut) + "..."


# ---------------------------------------------------------------- gating
def gate_item(item: dict, cat: dict, cfg: dict) -> Optional[str]:
    text = item["title"] + " " + (item.get("summary") or "")
    hosts = [re.sub(r"^www\.", "", str(h).lower()) for h in (cfg["sources"].get("avoid_hosts") or [])]
    for h in (host_of(item.get("url")), host_of(item.get("source_url"))):
        if not h:
            continue
        for bad in hosts:
            if bad and (h == bad or h.endswith("." + bad)):
                return "social or avoided site"
    for p in PAPERWORK:
        if term_hit(item["title"], p):
            return "paperwork notice"
    if cat.get("skip_listicles"):
        t = item["title"].strip().lower()
        if _LIST1.search(t) or term_hit(t, "to watch") or _LIST2.search(t):
            return "list article"
    for term in cat.get("exclude") or []:
        if term_hit(text, term):
            return "excluded term"
    for group in cat.get("require") or []:
        if group and not any(term_hit(text, term) for term in group):
            return "off topic"
    return None


def clean_item(raw: Any, max_chars: int) -> dict:
    raw = raw if is_obj(raw) else {}
    it = {
        "title": no_em_dash(collapse(raw.get("title"))),
        "url": collapse(raw.get("url")),
        "source": no_em_dash(collapse(raw.get("source"))),
        "source_url": collapse(raw.get("source_url")),
        "published": None,
        "summary": no_em_dash(cut_summary(raw.get("summary") or "", max_chars)),
        "image": "",
    }
    img = collapse(raw.get("image"))
    if valid_image(img):
        it["image"] = img
    pub = raw.get("published")
    ms = parse_iso(pub)
    it["published_ms"] = ms
    it["published"] = None if ms is None else iso_z(ms)
    # A date that is present but unreadable is not "undated": the story may be years old.
    it["bad_date"] = ms is None and is_str(pub) and collapse(pub) != ""
    src = it["source"]
    if src and it["title"].endswith(" - " + src):
        it["title"] = collapse(it["title"][:len(it["title"]) - len(src) - 3])
    if it["summary"] and norm_title(it["summary"]) == norm_title(it["title"]):
        it["summary"] = ""
    return it


def score(it: dict, cat: dict, brief: dict) -> float:
    if it["recency"] == "news":
        s = 4.0 - 2.0 * min(it["age"] / brief["window_hours"], 1)
    elif it["recency"] == "backfill":
        span = max(brief["backfill_max_hours"] - brief["window_hours"], 1)
        s = 1.5 - 0.5 * min((it["age"] - brief["window_hours"]) / span, 1)
    else:
        s = 0.5
    terms: list = []
    for g in cat.get("require") or []:
        terms = terms + list(g)
    return s + 0.25 * min(count_hits(it["title"], terms), 4)


_RANK = {"news": 0, "backfill": 1, "reference": 2}


def _sort_key(it: dict) -> tuple:
    p = it["published_ms"]
    return (_RANK[it["recency"]], -it["score"], -(p if p is not None else -math.inf), _CodePointKey(it["title"]))


class _CodePointKey:
    """Orders strings by UTF-16 code units, the way JavaScript compares them."""

    __slots__ = ("k",)

    def __init__(self, s: str) -> None:
        self.k = s.encode("utf-16-be")

    def __lt__(self, other: "_CodePointKey") -> bool:
        return self.k < other.k

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _CodePointKey) and self.k == other.k


def select_brief(candidates: dict, cfg: Any, ledger: Optional[dict], now_iso: str, date_str: str,
                 source: str = "desktop") -> dict:
    """candidates: {category_id: [{title, url, source, source_url, published, summary}]}."""
    n = normalize_config(cfg)
    b = n["brief"]
    now_ms = parse_iso(now_iso)
    if now_ms is None:
        raise ValueError("now_iso must be an ISO time")
    taken_urls: set = set()
    taken_titles: set = set()
    taken_toks: list = []
    out = []
    withheld = 0
    idx = recent_index(ledger) if ledger else None
    for raw in n["categories"]:
        cat = resolve_category(raw, n["reader"])
        rejected: dict = {}

        def bump(r: str) -> None:
            rejected[r] = rejected.get(r, 0) + 1

        pool = []
        lst = (candidates or {}).get(raw["id"])
        for cand in (lst if isinstance(lst, list) else []):
            it = clean_item(cand, b["summary_max_chars"])
            if not it["title"] or not valid_url(it["url"]):
                bump("missing title or link")
                continue
            why = gate_item(it, cat, n)
            if why:
                bump(why)
                continue
            if it["bad_date"]:
                bump("unreadable date")
                continue
            cls = classify(it["published_ms"], now_ms, b)
            if "reject" in cls:
                bump(cls["reject"])
                continue
            it["recency"] = cls["recency"]
            it["age"] = cls["age"]
            if ledger and ledger_has(ledger, it, idx):
                bump("already sent")
                withheld += 1
                continue
            it["score"] = score(it, cat, b)
            pool.append(it)
        pool.sort(key=_sort_key)
        want = b["items_per_category"] if raw.get("items") is None else raw["items"]
        picked = []
        for it in pool:
            if len(picked) >= want:
                break
            nu = norm_url(it["url"])
            nt = norm_title(it["title"])
            toks = title_tokens(it["title"])
            if nu in taken_urls or nt in taken_titles or any(near_dup(toks, t) for t in taken_toks):
                bump("duplicate")
                continue
            taken_urls.add(nu)
            taken_titles.add(nt)
            taken_toks.append(toks)
            picked.append({
                "title": it["title"], "url": it["url"], "source": it["source"], "published": it["published"],
                "recency": it["recency"], "age_hours": None if it["age"] is None else round1(it["age"]),
                "summary": it["summary"], "image": it["image"],
            })
        out.append({"id": cat["id"], "name": cat["name"], "color": cat["color"], "icon": cat["icon"],
                    "items": picked, "rejected": rejected})
    total = sum(len(c["items"]) for c in out)
    return {
        "schema": SCHEMA, "title": b["title"], "date": date_str, "generated_at": iso_z(now_ms),
        "window_hours": b["window_hours"], "backfill_max_hours": b["backfill_max_hours"],
        "items_per_category": b["items_per_category"], "source": source or "desktop",
        "total": total, "empty": len([c for c in out if not c["items"]]),
        "withheld": withheld, "ledger_applied": bool(ledger), "categories": out, "analysis": None,
    }


def filter_seen(brief: dict, ledger: dict) -> dict:
    b = clone(brief)
    withheld = 0
    idx = recent_index(ledger) if ledger else None
    for cat in b.get("categories") or []:
        kept = []
        for it in cat.get("items") or []:
            if ledger_has(ledger, {"title": str(it.get("title") or ""), "url": str(it.get("url") or "")}, idx):
                withheld += 1
            else:
                kept.append(it)
        cat["items"] = kept
    b["withheld"] = (b["withheld"] if is_int(b.get("withheld")) else 0) + withheld
    b["ledger_applied"] = True
    b["total"] = sum(len(c.get("items") or []) for c in b.get("categories") or [])
    b["empty"] = len([c for c in b.get("categories") or [] if not (c.get("items") or [])])
    return {"brief": b, "withheld": withheld}


# ------------------------------------------------------------ brief check
def brief_texts(brief: dict) -> list:
    out = []

    def push(where: str, v: Any) -> None:
        if is_str(v):
            out.append([where, v])

    push("title", brief.get("title"))
    for cat in brief.get("categories") or []:
        cid = cat.get("id") or "?"
        push(cid + " name", cat.get("name"))
        push(cid + " signal", cat.get("signal"))
        push(cid + " so_what", cat.get("so_what"))
        for i, it in enumerate(cat.get("items") or []):
            w = cid + " item " + str(i + 1)
            push(w + " title", it.get("title"))
            push(w + " summary", it.get("summary"))
            push(w + " starter", it.get("starter"))
    a = brief.get("analysis")
    if is_obj(a):
        for i, t in enumerate(a.get("top_three") if isinstance(a.get("top_three"), list) else []):
            push("analysis top " + str(i + 1), t)
        push("analysis connection", a.get("connection"))
        watch = a.get("watch") if isinstance(a.get("watch"), list) else [a.get("watch")]
        for i, t in enumerate(watch):
            push("analysis watch " + str(i + 1), t)
        push("analysis action", a.get("action"))
    return out


def check_brief(brief: Any, cfg: Any = None, now_iso: Optional[str] = None) -> dict:
    errors: list = []
    warnings: list = []
    if not is_obj(brief):
        return {"errors": ["The brief is not a JSON object."], "warnings": warnings}
    if not isinstance(brief.get("categories"), list):
        return {"errors": ["The brief has no categories list."], "warnings": warnings}
    n = normalize_config(cfg or {})
    b = n["brief"]
    win = brief["window_hours"] if is_int(brief.get("window_hours")) else b["window_hours"]
    back = brief["backfill_max_hours"] if is_int(brief.get("backfill_max_hours")) else b["backfill_max_hours"]
    given = js_truthy(cfg)
    # Without settings a category may hold up to 10 stories, the most any setting allows.
    per = b["items_per_category"] if given else 10
    max_chars = b["summary_max_chars"]
    if brief.get("schema") != SCHEMA:
        warnings.append('schema should be "' + SCHEMA + '".')
    if not is_date_str(brief.get("date")):
        errors.append("date must be a date like 2026-10-23.")
    ref_ms = parse_iso(brief.get("generated_at"))
    if ref_ms is None:
        ref_ms = parse_iso(now_iso)
    if ref_ms is None:
        errors.append("generated_at must be a time like 2026-10-23T11:00:00Z.")
    seen_urls: dict = {}
    all_toks: list = []
    total = 0
    cfg_ids = [c["id"] for c in n["categories"]] if given else []
    for ci, cat in enumerate(brief["categories"]):
        if (not is_obj(cat) or not is_str(cat.get("id")) or not collapse(cat.get("id"))
                or not is_str(cat.get("name")) or not collapse(cat.get("name"))):
            errors.append("Category " + str(ci + 1) + " needs an id and a name.")
            continue
        cid = cat["id"]
        if given and cid not in cfg_ids:
            warnings.append(cid + ": not one of your categories.")
        items = cat["items"] if isinstance(cat.get("items"), list) else []
        if not isinstance(cat.get("items"), list):
            errors.append(cid + ": items must be a list.")
        if given:
            match = next((c for c in n["categories"] if c["id"] == cid), {})
            limit = match.get("items") or per
        else:
            limit = per
        if len(items) > limit:
            errors.append(cid + ": has " + str(len(items)) + " items; the limit is " + str(limit) + ".")
        for i, it in enumerate(items):
            w = cid + " item " + str(i + 1)
            total += 1
            if not is_obj(it):
                errors.append(w + ": is not an object.")
                continue
            if not is_str(it.get("title")) or not collapse(it.get("title")):
                errors.append(w + ": needs a title.")
            if not valid_url(it.get("url")):
                errors.append(w + ": needs an http or https link.")
            else:
                nu = norm_url(it["url"])
                if nu in seen_urls:
                    errors.append(w + ": repeats the link in " + seen_urls[nu] + ".")
                else:
                    seen_urls[nu] = w
            if it.get("recency") not in RECENCY:
                errors.append(w + ": recency must be news, backfill or reference.")
            pms = parse_iso(it.get("published"))
            if it.get("published") is not None and pms is None:
                errors.append(w + ": published is not a valid time.")
            if ref_ms is not None and pms is not None:
                age = (ref_ms - pms) / 3600000
                if age < -2:
                    warnings.append(w + ": published is in the future.")
                if it.get("recency") == "news" and age > win + 1:
                    errors.append(w + ": marked news but is " + humanize_age(age).replace(" ago", "")
                                  + " old; the window is " + str(win) + "h.")
                if it.get("recency") == "backfill" and age > back + 1:
                    errors.append(w + ": older than the " + str(back) + "h limit.")
                if it.get("recency") == "backfill" and age <= win:
                    warnings.append(w + ": inside the window, so it should be news.")
            if it.get("recency") in ("news", "backfill") and pms is None:
                errors.append(w + ": " + it["recency"] + " items need a published time.")
            if it.get("recency") == "reference" and pms is not None:
                warnings.append(w + ": reference items should have no date.")
            if it.get("image") not in (None, "") and not valid_image(it.get("image")):
                warnings.append(w + ": image must be an https link to a picture; it will not be shown.")
            if is_str(it.get("summary")) and len(it["summary"]) > max_chars:
                warnings.append(w + ": summary is longer than " + str(max_chars) + " characters.")
            if is_str(it.get("title")):
                toks = title_tokens(it["title"])
                for prev in all_toks:
                    if near_dup(toks, prev[1]):
                        warnings.append(w + ": looks like the same story as " + prev[0] + ".")
                        break
                all_toks.append([w, toks])
    if given:
        ids = [c.get("id") for c in brief["categories"] if is_obj(c)]
        for cid in cfg_ids:
            if cid not in ids:
                warnings.append(cid + ": missing from the brief.")
    if "total" in brief and (not is_int(brief["total"]) or brief["total"] != total):
        errors.append("total says " + js_str(brief["total"]) + " but the brief holds " + str(total) + " items.")
    if n["style"]["no_em_dashes"]:
        for where, text in brief_texts(brief):
            if "\u2014" in text:
                errors.append(where + ": contains an em dash.")
    wx = brief.get("weather")
    if wx is not None and not (is_obj(wx) and isinstance(wx.get("days"), list)):
        warnings.append("weather must be an object with a days list; it will not be shown.")
    a = brief.get("analysis")
    if a is not None:
        if not is_obj(a):
            errors.append("analysis must be an object or null.")
        elif isinstance(a.get("top_three"), list) and len(a["top_three"]) > 3:
            warnings.append("analysis.top_three has more than three entries.")
    return {"errors": errors, "warnings": warnings}


# ------------------------------------------------------------- AI hand-off
def build_prompt(prompt_text: str, cfg: Any, compact: bool = False) -> str:
    begin = "<!-- CONFIG:BEGIN -->"
    end = "<!-- CONFIG:END -->"
    i = prompt_text.find(begin)
    j = prompt_text.find(end)
    if i < 0 or j < i:
        raise ValueError("The prompt has no configuration markers.")
    if cfg == "file":  # the settings travel as a separate knowledge file
        body = FILE_NOTE
    elif js_truthy(cfg):
        text = (json.dumps(cfg, separators=(",", ":"), ensure_ascii=False) if compact
                else json.dumps(cfg, indent=2, ensure_ascii=False))
        body = ("Saved configuration (use it; skip the interview unless I ask to change it):\n\n```json\n"
                + text + "\n```")
    else:
        body = "No settings are saved in this prompt. Use an attached daily-brief-settings.json or the latest settings JSON in this conversation; if there is none, start with the setup interview."
    return prompt_text[:i + len(begin)] + "\n" + body + "\n" + prompt_text[j:]


def extract_json(text: Any) -> Optional[Any]:
    s = str(text or "")
    blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", s, flags=re.IGNORECASE)
    blocks.append(s)
    for block in blocks:
        start = block.find("{")
        if start < 0:
            continue
        depth = 0
        in_str = False
        escape = False
        for k in range(start, len(block)):
            ch = block[k]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json_loads(block[start:k + 1])
                    except ValueError:
                        break
    return None


def google_news_url(query: str, days: int, cfg: Any) -> str:
    from urllib.parse import quote
    b = normalize_config(cfg)["brief"]
    q = query + " when:" + str(days) + "d"
    return ("https://news.google.com/rss/search?q=" + quote(q, safe="-_.!~*'()") + "&hl=" + b["language"]
            + "-" + b["region"] + "&gl=" + b["region"] + "&ceid=" + b["region"] + ":" + b["language"])
