"""Python mirror of app/js/newsletter.js (the page theme).

The stylesheet is read from app/js/newsletter.js and the icons from
app/data/icons.js, so a page saved here and the view in the browser use one
copy of each.
tests/test_parity.py renders the same briefs with both and requires identical
HTML, text and subject lines.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Optional

from . import engine as E
from .jsdata import load_js_json
from .paths import APP_DIR

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MIX_COLORS = {"news": "#1b6e3d", "backfill": "#6e5426", "reference": "#5b3485"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

_CSS: Optional[str] = None
_ICONS: Optional[dict] = None


def icons() -> dict:
    """The icon set and artwork, taken from app/data/icons.js."""
    global _ICONS
    if _ICONS is None:
        _ICONS = load_js_json(APP_DIR / "data" / "icons.js", "DB_ICONS")
    return _ICONS


def icon_svg(name: Any, cls: str) -> str:
    ic = icons()["icons"]
    inner = ic.get(name) if isinstance(name, str) and name in ic else ic.get("news", "")
    return ('<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + "</svg>")


def icon_of(cat: dict, cfg: dict) -> str:
    ic = icons()["icons"]
    own = E.collapse(cat.get("icon"))
    if own and own in ic:
        return own
    match = next((c for c in cfg.get("categories") or [] if c.get("id") == cat.get("id")), None)
    if match and isinstance(match.get("icon"), str) and match["icon"] in ic:
        return match["icon"]
    return "news"


def wx_kind(code: Any) -> str:
    if not isinstance(code, bool):
        for k, codes in icons()["weather_codes"].items():
            if code in codes:
                return k
    return "cloudy"


def wx_svg(kind: str, cls: str) -> str:
    return ('<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">' + icons()["weather"].get(kind, "") + "</svg>")


def rnd(x: float) -> int:
    return math.floor(x + 0.5)


def _day_label(d: str, day: str) -> str:
    if d == day:
        return "Today"
    return DAYS[_weekday_index(datetime.strptime(d, "%Y-%m-%d"))][:3]


def _wx_days(wx: dict) -> list:
    return [d for d in wx["days"] if isinstance(d, dict) and E.is_date_str(d.get("date"))][:4]


def _wx_ok(wx: Any) -> bool:
    return isinstance(wx, dict) and isinstance(wx.get("days"), list)


def weather_html(wx: Any, day: str) -> str:
    """The forecast panel. Numbers are checked before they are written."""
    if not _wx_ok(wx):
        return ""
    days = _wx_days(wx)
    if not days:
        return ""
    words = icons()["weather_words"]
    unit = "C" if wx.get("units") == "celsius" else "F"
    c = wx.get("current")
    cur = c if isinstance(c, dict) and _num(c.get("temp")) else None
    now_kind = wx_kind(cur.get("code") if cur else days[0].get("code"))
    place = E.collapse(wx.get("place")) or "your area"
    h = ('<section class="wx"><div class="wxnow">' + wx_svg(now_kind, "wxi big") + '<div><div class="wxk">Weather &middot; '
         + esc(place) + "</div>" + ('<div class="wxt">' + str(rnd(cur["temp"])) + "&deg;" + unit + "</div>" if cur else "")
         + '<div class="wxw">' + esc(words.get(now_kind, "")) + (" now" if cur else " today") + '</div></div></div><ol class="wxd">')
    for d in days:
        k = wx_kind(d.get("code"))
        hi = str(rnd(d["hi"])) + "&deg;" if _num(d.get("hi")) else "&ndash;"
        lo = str(rnd(d["lo"])) + "&deg;" if _num(d.get("lo")) else "&ndash;"
        rain = str(rnd(d["rain"])) + "% rain" if _num(d.get("rain")) and d["rain"] > 0 else ""
        h += ('<li title="' + esc(words.get(k, "")) + '"><span class="wxdn">' + _day_label(d["date"], day) + "</span>" + wx_svg(k, "wxi")
              + '<span class="wxhl"><b>' + hi + "</b> / " + lo + '</span><span class="wxr">' + rain + "</span></li>")
    when = stamp(wx.get("fetched_at"))
    return (h + '</ol><p class="wxs">Forecast by <a href="https://open-meteo.com/">Open-Meteo.com</a> (CC BY 4.0)'
            + (" &middot; updated " + when if when else "") + "</p></section>")


def css() -> str:
    """The newsletter stylesheet, taken from app/js/newsletter.js."""
    global _CSS
    if _CSS is None:
        src = (APP_DIR / "js" / "newsletter.js").read_text(encoding="utf-8")
        m = re.search(r"/\*CSS-START\*/\s*const CSS = `([\s\S]*?)`;\s*/\*CSS-END\*/", src)
        if not m:
            raise RuntimeError("newsletter.js has no CSS block")
        _CSS = m.group(1)
    return _CSS


def esc(v: Any) -> str:
    s = "" if v is None else _js_str(v)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#x27;"))


def _js_str(v: Any) -> str:
    """String(v) the way JavaScript writes numbers and booleans."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _weekday_index(d: datetime) -> int:
    return (d.weekday() + 1) % 7  # JavaScript counts Sunday as 0


def pretty_date(d: Any) -> str:
    if not E.is_date_str(d):
        return str(d or "")
    dt = datetime.strptime(d, "%Y-%m-%d")
    return DAYS[_weekday_index(dt)] + ", " + MONTHS_LONG[dt.month - 1] + " " + E.pad2(dt.day) + ", " + str(dt.year)


def short_date(d: str) -> str:
    dt = datetime.strptime(d, "%Y-%m-%d")
    return DAYS[_weekday_index(dt)][:3] + " " + MONTHS[dt.month - 1] + " " + E.pad2(dt.day) + ", " + str(dt.year)


def stamp(iso: Any) -> str:
    ms = E.parse_iso(iso)
    if ms is None:
        return ""
    dt = E.utc_dt(ms)
    return MONTHS[dt.month - 1] + " " + E.pad2(dt.day) + ", " + E.pad2(dt.hour) + ":" + E.pad2(dt.minute) + "Z"


def age_of(item: dict, brief: dict) -> Optional[float]:
    a = item.get("age_hours")
    if isinstance(a, (int, float)) and not isinstance(a, bool) and math.isfinite(a):
        return a
    p = E.parse_iso(item.get("published"))
    g = E.parse_iso(brief.get("generated_at"))
    if p is None or g is None:
        return None
    return E.round1(max(0, (g - p) / 3600000))


def safe_href(u: Any) -> str:
    return str(u).strip() if E.valid_url(u) else ""


def stats(brief: dict) -> dict:
    cats = brief.get("categories") if isinstance(brief.get("categories"), list) else []
    s = {"total": 0, "news": 0, "backfill": 0, "reference": 0, "filled": 0, "cats": len(cats),
         "outlets": 0, "empty": []}
    outlets: set = set()
    for c in cats:
        items = c.get("items") if isinstance(c.get("items"), list) else []
        if items:
            s["filled"] += 1
        else:
            s["empty"].append(c)
        for it in items:
            s["total"] += 1
            r = it.get("recency")
            if r == "news":
                s["news"] += 1
            elif r == "backfill":
                s["backfill"] += 1
            else:
                s["reference"] += 1
            o = E.collapse(it.get("source")).lower()
            if o:
                outlets.add(o)
    s["outlets"] = len(outlets)
    return s


def subject_line(brief: dict, cfg: Any) -> str:
    n = E.normalize_config(cfg or {})
    s = stats(brief)
    tpl = n["brief"]["subject"]
    out = (tpl.replace("{total}", str(s["total"])).replace("{date}", str(brief.get("date") or ""))
           .replace("{title}", str(brief.get("title") or n["brief"]["title"]))
           .replace("{empty}", str(len(s["empty"]))))
    if s["empty"] and "{empty}" not in tpl:
        out += " | " + str(len(s["empty"])) + " empty"
    if brief.get("source") == "sample":
        out = "[SAMPLE] " + out
    return out


def countdown_data(cfg: dict, day: str) -> Optional[dict]:
    cd = cfg.get("countdown") or {}
    if cd.get("enabled") is not True or not E.is_date_str(cd.get("date")) or not E.is_date_str(day):
        return None
    days = E.days_between(day, cd["date"])
    pct = None
    if E.is_date_str(cd.get("start")):
        span = max(E.days_between(cd["start"], cd["date"]), 1)
        done = min(max(E.days_between(cd["start"], day), 0), span)
        pct = math.floor(100 * done / span + 0.5)
    allm = [{"date": m["date"], "label": E.collapse(m.get("label")), "note": E.collapse(m.get("note")), "mark": False}
            for m in (cd.get("milestones") or []) if E.is_date_str(m.get("date"))]
    allm.append({"date": cd["date"], "label": "Target date", "note": E.collapse(cd.get("label")), "mark": True})
    allm.sort(key=lambda m: (m["date"], 1 if m["mark"] else 0))
    upcoming = [m for m in allm if m["date"] >= day][:5]
    return {"days": days, "pct": pct, "label": E.collapse(cd.get("label")), "date": cd["date"], "upcoming": upcoming}


def countdown_html(c: dict, day: str) -> str:
    rows = []
    for m in c["upcoming"]:
        dd = E.days_between(day, m["date"])
        cls = "ms-mark" if m["mark"] else "ms-hot" if dd <= 30 else "ms-warm" if dd <= 120 else "ms-cool"
        when = "today" if dd == 0 else str(dd) + " d"
        note = " &middot; " + esc(m["note"]) if m["note"] else ""
        rows.append('<li><span class="pill ' + cls + '">' + when + '</span><span>' + esc(m["label"])
                    + '<span class="msn">' + short_date(m["date"]) + note + '</span></span></li>')
    rows_html = "".join(rows)
    sub = pretty_date(c["date"]) + ("" if c["pct"] is None else " &middot; " + str(c["pct"]) + "% of the countdown elapsed")
    bar = ""
    if c["pct"] is not None:
        bar = '<div class="bar"><div class="barf" style="width:' + str(max(c["pct"], 1)) + '%"></div></div>'
    return ('<section class="cd"><div class="cdtop"><div class="cdn">' + str(c["days"]) + '</div><div class="cdt"><div class="cdk">'
            + esc(c["label"]) + '</div><div class="cds">' + sub + '</div>' + bar + '</div></div>'
            + ('<ul class="ms">' + rows_html + '</ul>' if rows_html else "") + '</section>')


def pill(item: dict, age: Optional[float]) -> str:
    if item.get("recency") == "reference":
        return '<span class="pill ref">REFERENCE &middot; undated</span>'
    if item.get("recency") == "backfill":
        return '<span class="pill old">OLDER &middot; ' + E.humanize_age(age) + '</span>'
    cls = "f3" if age is None else "f1" if age < 6 else "f2" if age < 12 else "f3"
    return '<span class="pill ' + cls + '">' + E.humanize_age(age) + '</span>'


def _list_of(v: Any) -> list:
    if isinstance(v, list):
        return v
    return [v] if v else []


_NONE = re.compile(r"none\.?", re.I | re.A)


def analysis_parts(a: dict) -> dict:
    """The Lead Analysis lines, without the "NONE" an assistant writes for an empty section."""
    def keep(t: str) -> bool:
        return bool(t) and not _NONE.fullmatch(t)
    conn = E.collapse(a.get("connection"))
    act = E.collapse(a.get("action"))
    tops = a.get("top_three") if isinstance(a.get("top_three"), list) else []
    return {"top": [t for t in (E.collapse(x) for x in tops) if keep(t)],
            "watch": [t for t in (E.collapse(x) for x in _list_of(a.get("watch"))) if keep(t)],
            "conn": conn if keep(conn) else "", "act": act if keep(act) else ""}


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def analysis_html(a: Any, cfg: dict) -> str:
    if not a or not isinstance(a, dict):
        return ""
    p = analysis_parts(a)
    top, watch, conn, act = p["top"], p["watch"], p["conn"], p["act"]
    if not top and not watch and not conn and not act:
        return ""
    h = '<section class="an"><h2 class="anh">Lead analysis</h2>'
    if top:
        h += '<div class="anb"><b>Top three</b><ol>' + "".join("<li>" + esc(t) + "</li>" for t in top) + "</ol></div>"
    if conn:
        h += '<div class="anr"><b>Connection:</b> ' + esc(conn) + "</div>"
    if watch:
        h += ('<div class="anr"><b>' + esc(cfg["brief"]["watch_label"]) + ':</b><ul>'
              + "".join("<li>" + esc(t) + "</li>" for t in watch) + "</ul></div>")
    if act:
        h += '<div class="anr"><b>Action:</b> ' + esc(act) + "</div>"
    return (h + '<p class="anf">Analysis is inference from the headlines below, not reporting. '
            'Check the linked sources before acting.</p></section>')


def card_html(cat: dict, brief: dict, cfg: dict, index: int, win: Any) -> str:
    color = cat.get("color") if _HEX.match(str(cat.get("color") or "")) else E.PALETTE[index % len(E.PALETTE)]
    items = cat.get("items") if isinstance(cat.get("items"), list) else []
    rows = []
    lead = False
    for it in items:
        age = age_of(it, brief)
        href = safe_href(it.get("url"))
        title = esc(E.collapse(it.get("title")))
        head = ('<a class="hl" href="' + esc(href) + '">' + title + "</a>") if href else ('<span class="hl">' + title + "</span>")
        src = esc(E.collapse(it.get("source")))
        if it.get("published") and it.get("recency") != "reference" and stamp(it.get("published")):
            src += (" &middot; " if src else "") + stamp(it.get("published"))
        summ = E.collapse(it.get("summary"))
        st = ""
        if cfg["brief"]["conversation_starters"] and E.collapse(it.get("starter")):
            st = '<p class="st">Ask: ' + esc(E.collapse(it.get("starter"))) + "</p>"
        text = (head + '<div class="meta">' + pill(it, age) + '<span class="src">' + src + "</span></div>"
                + ('<p class="sum">' + esc(summ) + "</p>" if summ else "") + st)
        img = ('<img src="' + esc(it.get("image")) + '" alt="" loading="lazy" referrerpolicy="no-referrer">'
               if E.valid_image(it.get("image")) else "")
        if not img:
            rows.append('<li class="it">' + text + "</li>")
            continue

        def wrap(cls: str) -> str:
            if href:
                return '<a class="' + cls + '" href="' + esc(href) + '" tabindex="-1" aria-hidden="true">' + img + "</a>"
            return '<span class="' + cls + '">' + img + "</span>"
        # The first story with a photo leads the card; later ones get a thumbnail.
        if not lead:
            lead = True
            rows.append('<li class="it lead">' + wrap("ph") + text + "</li>")
        else:
            rows.append('<li class="it th"><div class="tx">' + text + "</div>" + wrap("thumb") + "</li>")
    if rows:
        body = '<ul class="items">' + "".join(rows) + "</ul>"
    else:
        body = ('<p class="none">No new items. Nothing was published in the last ' + _js_str(win)
                + " hours that you have not already been sent.</p>")
    n_news = len([i for i in items if i.get("recency") == "news"])
    n_back = len([i for i in items if i.get("recency") == "backfill"])
    n_ref = len([i for i in items if i.get("recency") == "reference"])
    mix = str(n_news) + " fresh" + (", " + str(n_back) + " older" if n_back else "") + (", " + str(n_ref) + " reference" if n_ref else "")
    sig = E.collapse(cat.get("signal"))
    so = E.collapse(cat.get("so_what"))
    sig_row = ""
    if sig or so:
        sig_row = ('<p class="sig">' + ("<b>Signal:</b> " + esc(sig) if sig else "") + ("<br>" if sig and so else "")
                   + ("<b>So what:</b> " + esc(so) if so else "") + "</p>")
    return ('<section class="card" style="--c:' + color + '"><h2 class="ch"><span class="ico">' + icon_svg(icon_of(cat, cfg), "i")
            + '</span><span class="tag">' + esc(tag_of(cat, index))
            + '</span><span class="cn">' + esc(cat.get("name")) + '</span><span class="mix">' + mix + "</span></h2>"
            + sig_row + body + "</section>")


def tag_of(cat: dict, index: int) -> str:
    """Short desk label on each card: the category's own tag, else T1, T2 and so on."""
    t = E.collapse(cat.get("tag"))
    return t if t and len(t) <= 8 else "T" + str(index + 1)


def source_label(brief: dict) -> str:
    if brief.get("source") == "sample":
        return "sample data, not real news"
    if brief.get("source") == "ai":
        model = E.collapse(brief.get("model"))
        return "written by an AI assistant with web search" + (" (" + model + ")" if model else "")
    if brief.get("source") == "web":
        return "collected in your browser from the GDELT news index and publisher feeds"
    return "collected by the Daily Brief from Google News and publisher feeds"


def render(brief: dict, cfg: Any = None) -> dict:
    """Returns {"subject", "html", "text"} for a brief."""
    n = E.normalize_config(cfg or {})
    s = stats(brief)
    wh = brief.get("window_hours")
    win = wh if _num(wh) else n["brief"]["window_hours"] if _num(n["brief"]["window_hours"]) else E.DEFAULTS["brief"]["window_hours"]
    mc = n["brief"]["summary_max_chars"]
    cap = mc if _num(mc) else E.DEFAULTS["brief"]["summary_max_chars"]
    title = E.collapse(brief.get("title")) or n["brief"]["title"]
    day = str(brief.get("date") or "")
    w = brief.get("withheld")
    withheld = w if isinstance(w, (int, float)) and not isinstance(w, bool) else None
    W = _js_str(win)
    dek = (str(s["total"]) + " stories across " + str(s["cats"]) + " categories &middot; " + str(s["news"])
           + " published in the last " + W + " hours")
    if brief.get("ledger_applied"):
        dek += (" &middot; " + _js_str(withheld) + " withheld as already sent") if withheld else " &middot; nothing here has been sent to you before"
    tiles = [[s["total"], "stories"], [s["news"], "fresh, under " + W + "h"],
             [str(s["filled"]) + " of " + str(s["cats"]), "categories filled"],
             [withheld or 0, "withheld as already sent"] if brief.get("ledger_applied") else [s["outlets"], "outlets"]]
    tiles_html = ('<div class="tiles">' + "".join(
        '<div class="tile"><div class="tn">' + esc(t[0]) + '</div><div class="tl">' + esc(t[1]) + "</div></div>" for t in tiles)
        + "</div>")
    segs = [["Fresh", s["news"], MIX_COLORS["news"]], ["Older", s["backfill"], MIX_COLORS["backfill"]],
            ["Reference", s["reference"], MIX_COLORS["reference"]]]
    cells = "".join('<span class="seg" style="width:' + str(max(1, math.floor(100 * x[1] / max(s["total"], 1) + 0.5)))
                    + '%;background:' + x[2] + '"></span>' for x in segs if x[1] > 0)
    legend = "".join('<span class="lg"><span class="sw" style="background:' + x[2] + '"></span>' + x[0] + " " + str(x[1])
                     + "</span>" for x in segs)
    bar = ('<div class="srcbar">' + cells + '</div><div class="lgd">Today\'s stories by age: '
           + legend + "</div>") if cells else ""
    cd = countdown_data(n, day)
    gap = ""
    if s["empty"]:
        gap = ('<div class="gap">No new items for: ' + ", ".join(esc(c.get("name")) for c in s["empty"])
               + ". Nothing was published in the last " + W + " hours that had not already been sent in an earlier brief.</div>")
    sample = ('<div class="sample">Sample brief: invented headlines that show the layout. Nothing here is real news and the '
              'links go to example.com.</div>') if brief.get("source") == "sample" else ""
    cards = "".join(card_html(c, brief, n, i, win) for i, c in enumerate(brief.get("categories") or []))
    subject = subject_line(brief, n)
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
            + "<title>" + esc(subject) + "</title><style>" + css() + "</style></head><body>"
            + '<header class="mast"><div class="art">' + icons()["art"].get("masthead", "") + '</div><div class="in"><div class="kick">'
            + icon_svg("sunrise", "ki") + esc(title) + " &middot; Edition " + esc(day)
            + '</div><h1 class="ttl">' + esc(pretty_date(day)) + '</h1><p class="dl">' + dek
            + '</p></div></header><div class="rule"></div><main class="in">'
            + sample + weather_html(brief.get("weather"), day) + (countdown_html(cd, day) if cd else "") + tiles_html + bar + analysis_html(brief.get("analysis"), n) + gap
            + '<div class="grid">' + cards + "</div>"
            + '<div class="legend"><b>Reading the pills.</b> Green, teal and amber pills give a story\'s age inside the ' + W
            + '-hour window (under 6h, under 12h, under ' + W + 'h). <span class="pill old">OLDER</span> is beyond ' + W
            + 'h, used only where a category had no fresh material, and stamped with its true age. <span class="pill ref">REFERENCE</span>'
            + ' is an undated authoritative page, never presented as an event.</div>'
            + '</main><footer class="foot"><div class="in">Generated ' + esc(brief.get("generated_at") or "") + " &middot; " + esc(source_label(brief))
            + " &middot; " + W + "-hour window &middot; summaries capped at " + esc(cap)
            + " characters &middot; Daily Brief " + E.VERSION
            + "<br>Headlines, photos and summaries belong to their publishers; every link opens the original story.</div></footer></body></html>")
    return {"subject": subject, "html": html,
            "text": plain_text(brief, n, s, cd, win, title, day, withheld)}


def plain_text(brief: dict, n: dict, s: dict, cd: Optional[dict], win: Any, title: str, day: str,
               withheld: Any) -> str:
    W = _js_str(win)
    L = []
    rule = "=" * 65
    L += [title.upper() + " - " + pretty_date(day), rule]
    L.append(str(s["total"]) + " stories across " + str(s["cats"]) + " categories | " + str(s["news"]) + " fresh under " + W + "h"
             + (" | " + _js_str(withheld or 0) + " withheld as already sent" if brief.get("ledger_applied") else ""))
    if brief.get("source") == "sample":
        L.append("SAMPLE: invented headlines that show the layout. Nothing here is real news.")
    wx = brief.get("weather")
    if _wx_ok(wx):
        unit = "C" if wx.get("units") == "celsius" else "F"
        words = icons()["weather_words"]
        parts = [_day_label(d["date"], day) + " " + words.get(wx_kind(d.get("code")), "")
                 + (" " + str(rnd(d["hi"])) + unit if _num(d.get("hi")) else "")
                 + ("/" + str(rnd(d["lo"])) + unit if _num(d.get("lo")) else "")
                 + (" " + str(rnd(d["rain"])) + "% rain" if _num(d.get("rain")) and d["rain"] > 0 else "")
                 for d in _wx_days(wx)]
        if parts:
            L += ["", "WEATHER, " + (E.collapse(wx.get("place")) or "your area").upper() + ": " + " | ".join(parts)]
    if cd:
        L += ["", cd["label"].upper() + ": " + str(cd["days"]) + " days to " + pretty_date(cd["date"])
              + ("" if cd["pct"] is None else " (" + str(cd["pct"]) + "% elapsed)")]
        for m in cd["upcoming"]:
            L.append("  " + str(E.days_between(day, m["date"])).rjust(4) + " d  " + m["date"] + "  " + m["label"]
                     + ("  [" + m["note"] + "]" if m["note"] else ""))
    a = brief.get("analysis")
    if a and isinstance(a, dict):
        p = analysis_parts(a)
        top, watch = p["top"], p["watch"]
        if top or watch or p["conn"] or p["act"]:
            L += ["", "LEAD ANALYSIS (inference, check the sources)"]
            for i, t in enumerate(top):
                L.append("  " + str(i + 1) + ". " + t)
            if p["conn"]:
                L.append("  Connection: " + p["conn"])
            for t in watch:
                L.append("  " + n["brief"]["watch_label"] + ": " + t)
            if p["act"]:
                L.append("  Action: " + p["act"])
    for index, cat in enumerate(brief.get("categories") or []):
        L += ["", "[" + tag_of(cat, index) + "] " + E.collapse(cat.get("name")), "-" * 60]
        if E.collapse(cat.get("signal")):
            L.append("  Signal: " + E.collapse(cat.get("signal")))
        if E.collapse(cat.get("so_what")):
            L.append("  So what: " + E.collapse(cat.get("so_what")))
        items = cat.get("items") if isinstance(cat.get("items"), list) else []
        if not items:
            L.append("  No new items in the last " + W + " hours that you have not already been sent.")
        for it in items:
            age = age_of(it, brief)
            r = it.get("recency")
            label = ("REFERENCE, undated" if r == "reference" else "OLDER, " + E.humanize_age(age) if r == "backfill"
                     else E.humanize_age(age))
            L.append("  * " + E.collapse(it.get("title")))
            src = E.collapse(it.get("source"))
            L.append("    " + (src + " | " if src else "") + label)
            L.append("    " + E.collapse(it.get("url")))
            if E.collapse(it.get("summary")):
                L.append("    " + E.collapse(it.get("summary")))
            if n["brief"]["conversation_starters"] and E.collapse(it.get("starter")):
                L.append("    Ask: " + E.collapse(it.get("starter")))
    L += ["", rule, "Generated " + str(brief.get("generated_at") or "") + " | " + source_label(brief) + " | Daily Brief " + E.VERSION]
    return "\n".join(L) + "\n"
