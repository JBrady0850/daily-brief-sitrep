"""The browser engine (app/js) and the desktop engine (dailybrief) must agree.

Each case runs the same function with the same input in Node and in Python
and requires equal results, so the web page and the desktop email can never
pick, check or draw a brief differently.
"""
import copy
import json

from conftest import ROOT, js_calls

from dailybrief import engine as E, render as R
from dailybrief.jsdata import library

NOW = "2026-10-23T12:00:00Z"


def same(py_value, js_value):
    return json.loads(json.dumps(py_value)) == js_value


def ago(hours):
    return E.iso_z(E.parse_iso(NOW) - int(hours * 3600000))


TERMS = [("Pentagon expands AI pilots", "AI"), ("He said it", "AI"), ("Tariff talks", "RIF"), ("New 401(k) limits", "401(k)"),
         ("The S&P 500 closes", "S&P 500"), ("IT budgets", "IT"), ("it budgets", "IT"), ("Zero-day in Chrome", "zero-day"),
         ("Résumé tips for engineers", "engineers"), ("A.I. policy", "A.I."), ("zerotrust", "zero trust"), ("x", "")]
URLS = ["https://www.Example.com/a/b/?utm_source=x&id=3#f", "http://example.com", "https://example.com/?b=2&a=1&gclid=z",
        "not a url", "https://user@host.example.com:8080/path/", "  https://EXAMPLE.org/A  "]
TITLES = ["Agencies weigh new buyout offers - Federal Daily", "Top 10 tools | Example", "Short - X", "  Mixed   CASE, punctuation!! ",
          "2026 budget: what changes in 2027 and 2028", "Café owners welcome tourists"]
DATES = ["2026-10-23T08:15:00Z", "2026-10-23T08:15", "2026-10-23", "2026-02-30", "2026-10-23T24:00:00Z",
         "2026-10-23T08:15:00.123456+0530", "Fri, 23 Oct 2026 09:00:00 GMT", "", "2026-13-01"]


def test_small_functions_agree():
    reqs, pys = [], []
    for text, term in TERMS:
        reqs.append({"fn": "termHit", "args": [text, term]}); pys.append(E.term_hit(text, term))
    for u in URLS:
        reqs.append({"fn": "normUrl", "args": [u]}); pys.append(E.norm_url(u))
        reqs.append({"fn": "validUrl", "args": [u]}); pys.append(E.valid_url(u))
        reqs.append({"fn": "hostOf", "args": [u]}); pys.append(E.host_of(u))
    images = ["https://img.example.com/a.jpg?w=600&h=400", "http://img.example.com/a.jpg", "https://img.example.com/a b.jpg",
              'https://img.example.com/a.jpg"onerror="x', "https://localhost/a.png", "javascript:alert(1)", "https://x.example.org",
              None, 7, "https://" + "a" * 2000 + ".com/x.png", "HTTPS://IMG.EXAMPLE.COM/Y.PNG", "https://img.example.com\\a.png"]
    for u in images:
        reqs.append({"fn": "validImage", "args": [u]}); pys.append(E.valid_image(u))
    for t in TITLES:
        reqs.append({"fn": "normTitle", "args": [t]}); pys.append(E.norm_title(t))
        reqs.append({"fn": "titleTokens", "args": [t]}); pys.append(E.title_tokens(t))
    for a in TITLES:
        for b in TITLES:
            reqs.append({"fn": "nearDup", "args": [a, b]}); pys.append(E.near_dup(a, b))
    words = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india", "juliet",
             "kilo", "lima", "mike", "november", "oscar", "papa", "quebec", "romeo"]
    pairs = [(" ".join(words[:6]), " ".join(words[:8])),            # 6 of 8 shared: exactly 0.75
             (" ".join(words[:15]), " ".join(words[:13] + words[15:18])),  # 13 of 18: about 0.72
             (" ".join(words[:3]), " ".join(words[:3]))]             # too short to compare
    expect = [True, False, False]
    for (a, b), want in zip(pairs, expect):
        assert E.near_dup(a, b) is want
        reqs.append({"fn": "nearDup", "args": [a, b]}); pys.append(want)
    for hrs in [0, 0.4, 1, 5.9, 23.99, 24, 25.5, 49, 72, -3, None]:
        reqs.append({"fn": "humanizeAge", "args": [hrs]}); pys.append(E.humanize_age(hrs))
    for d in DATES:
        reqs.append({"fn": "parseIso", "args": [d]}); pys.append(E.parse_iso(d))
    for s, n in [("short text", 320), ("word " * 100, 90), ("x" * 200, 80)]:
        reqs.append({"fn": "cutSummary", "args": [s, n]}); pys.append(E.cut_summary(s, n))
    dash = chr(0x2014)
    for raw in [{"title": "A " + dash + " B - Wire", "source": "Wire", "url": "https://e.com/1", "summary": "x" + dash + "y " * 50},
                {"title": "Plain - Out" + dash + "let", "source": "Out" + dash + "let", "url": " https://e.com/2 "}]:
        reqs.append({"fn": "cleanItem", "args": [raw, 60]}); pys.append(E.clean_item(raw, 60))
    reqs.append({"fn": "googleNewsUrl", "args": ['"zero trust" (CISA OR NSA) é', 3, {"brief": {"language": "en", "region": "GB"}}]})
    pys.append(E.google_news_url('"zero trust" (CISA OR NSA) é', 3, {"brief": {"language": "en", "region": "GB"}}))
    for k, (req, py) in enumerate(zip(reqs, js_calls(reqs))):
        assert same(pys[k], py), (reqs[k], pys[k], py)


def test_cron_lines_agree():
    from dailybrief import schedule as S
    cases = [("06:15", "America/New_York"), ("06:15", "America/Phoenix"), ("07:30", "Europe/London"), ("06:00", "Asia/Kolkata"),
             ("06:15", "Australia/Sydney"), ("23:45", "Pacific/Auckland"), ("06:15", "Bad/Zone"), ("6:15", "America/New_York"),
             ("06:15", "")]
    if S.zone("America/New_York") is None:
        import pytest
        pytest.skip("no time zone data for Python on this computer")
    got = js_calls([{"fn": "cronLines", "args": [t, z, 2026]} for t, z in cases])
    for (t, z), j in zip(cases, got):
        assert S.crons_for(t, z, 2026) == j, (t, z)


def configs():
    lib = library()
    good = E.config_from_pack(lib, "federal-it", {"reader": {"location": "Springfield", "local_terms": ["Sangamon County"]}})
    bad = copy.deepcopy(good)
    bad["brief"].update(window_hours=0, subject="x {bad}", summary_max_chars="long")
    bad["categories"][1]["id"] = bad["categories"][0]["id"]
    bad["categories"][2]["require"] = "not a list"
    bad["categories"][3]["queries"] = []
    bad["reader"] = {"location": "", "role": "me" + "@" + "mail.test", "local_terms": "x"}
    bad["countdown"] = {"enabled": True, "label": "", "date": "2026-02-30", "milestones": [{"date": "x"}]}
    bad["email"] = {"to": ["nope", "you@example.com"]}
    bad["extra"] = 1
    return [good, bad, {}, [], {"categories": [{"id": "constructor", "name": "c", "queries": ["q"]}]}]


def test_validation_agrees():
    cases = configs()
    got = js_calls([{"fn": "validateConfig", "args": [c]} for c in cases])
    for c, js in zip(cases, got):
        assert same(E.validate_config(c), js), (E.validate_config(c), js)


def candidates():
    lib = library()
    cfg = E.config_from_pack(lib, "federal-it", {"reader": {"location": "Springfield", "local_terms": ["Sangamon County"]},
                                                 "brief": {"items_per_category": 3}})
    base = [
        ("Pentagon CDAO expands AI pilots across the Army", 2, "defense-ai"),
        ("Military AI strategy update from the Pentagon - Example Defense", 30, "defense-ai"),
        ("Agencies weigh new buyout offers as hiring freeze continues", 1, "federal-workforce"),
        ("Agencies weigh new buyout offers as the hiring freeze continues", 3, "federal-workforce"),
        ("Federal employees face RIF notices at OPM", None, "federal-workforce"),
        ("Ransomware gang exploits zero-day in mail servers", 4, "cybersecurity"),
        ("Top 10 enterprise AI tools to watch", 5, "enterprise-ai"),
        ("Companies report ROI from generative AI deployment", 6, "enterprise-ai"),
        ("Claude adds a new feature for scheduled tasks", 7, "ai-tools"),
        ("Runner overcame injury to finish an inspiring marathon", 8, "inspiring"),
        ("Federal pay raise of 1 percent proposed for federal employees", 9, "federal-pay"),
        ("FERS COLA for federal retirees announced", 10, "federal-retirement"),
        ("Springfield council approves library hours", 11, "local-news"),
        ("Springfield man arrested after crash", 12, "local-news"),
        ("CISA advisory urges VPN patch for network teams", 13, "network-security"),
        ("CISA advisory urges VPN patch for network teams", 14, "cybersecurity"),
        ("Pentagon AI story from a social site", 1, "defense-ai"),
        ("Very old Army AI story", 200, "defense-ai"),
    ]
    out = {}
    for k, (title, hrs, cid) in enumerate(base):
        url = "https://example.com/story/%d?utm_source=feed" % k
        if "social site" in title:
            url = "https://www.facebook.com/post/%d" % k
        out.setdefault(cid, []).append({"title": title, "url": url, "source": "Example Outlet", "source_url": "https://example.com",
                                        "published": None if hrs is None else ago(hrs), "summary": "Summary text for " + title + "."})
    return cfg, out


def test_selection_and_history_agree():
    cfg, cands = candidates()
    led = E.ledger_add(E.empty_ledger(), {"date": "2026-10-22", "categories": [{"items": [cands["ai-tools"][0]]}]})
    reqs = [{"fn": "selectBrief", "args": [cands, cfg, None, NOW, "2026-10-23", "desktop"]},
            {"fn": "selectBrief", "args": [cands, cfg, led, NOW, "2026-10-23", "desktop"]},
            {"fn": "ledgerAdd", "args": [led, {"date": "2026-10-23", "categories": [{"items": cands["cybersecurity"]}]}]}]
    py = [E.select_brief(cands, cfg, None, NOW, "2026-10-23", "desktop"),
          E.select_brief(cands, cfg, led, NOW, "2026-10-23", "desktop"),
          E.ledger_add(led, {"date": "2026-10-23", "categories": [{"items": cands["cybersecurity"]}]})]
    got = js_calls(reqs)
    for p, j in zip(py, got):
        assert same(p, j), json.dumps([p, j])[:2000]
    assert py[1]["withheld"] == 1 and py[0]["total"] > 8


def test_checks_agree(sample_brief, sample_settings):
    bad = copy.deepcopy(sample_brief)
    it = bad["categories"][0]["items"]
    it[0]["published"] = "2026-10-01T00:00:00Z"
    it[1]["url"] = it[0]["url"]
    it[2]["summary"] = "x " + chr(0x2014) + " y" + " long" * 100
    bad["categories"][1]["items"][0]["recency"] = "maybe"
    bad["total"] = 3
    bad["analysis"]["top_three"].append("fourth")
    bad["categories"].append({"id": "", "name": ""})
    cases = [(sample_brief, sample_settings), (bad, sample_settings), (bad, None), ({}, None), ({"categories": "x"}, None)]
    got = js_calls([{"fn": "checkBrief", "args": [b, c, NOW]} for b, c in cases])
    for (b, c), j in zip(cases, got):
        assert same(E.check_brief(b, c, NOW), j), (E.check_brief(b, c, NOW), j)


def test_prompt_and_json_agree(sample_settings):
    text = (ROOT / "prompt" / "daily-brief-prompt-compact.md").read_text(encoding="utf-8")
    chats = ["```json\n{\"a\": 1}\n```", "text {\"b\": [1, {\"c\": \"}\"}]} tail", "nothing", "{broken"]
    reqs = [{"fn": "buildPrompt", "args": [text, sample_settings]}, {"fn": "buildPrompt", "args": [text, None]},
            {"fn": "buildPrompt", "args": [text, "file"]}] + [{"fn": "extractJson", "args": [c]} for c in chats]
    py = [E.build_prompt(text, sample_settings), E.build_prompt(text, None), E.build_prompt(text, "file")] + [E.extract_json(c) for c in chats]
    for p, j in zip(py, js_calls(reqs)):
        assert same(p, j)


def test_newsletters_are_identical(sample_brief, sample_settings):
    cfg, cands = candidates()
    desk = E.select_brief(cands, cfg, E.empty_ledger(), NOW, "2026-10-23", "desktop")
    ai = copy.deepcopy(sample_brief)
    ai["source"] = "ai"
    ai["model"] = "Example model <b>"
    ai["categories"][0]["items"][0]["title"] = "<script>alert('x')</script> & \"quotes\""
    ai["categories"][0]["items"][1]["url"] = "javascript:alert(1)"
    starters = copy.deepcopy(sample_settings)
    starters["brief"]["conversation_starters"] = True
    starters["brief"]["subject"] = "{title} {empty} {date}"
    cases = [(sample_brief, sample_settings), (sample_brief, None), (desk, cfg), (ai, starters), (E.filter_seen(ai, E.ledger_add(E.empty_ledger(), ai))["brief"], starters)]
    got = js_calls([{"fn": "render", "args": [b, c]} for b, c in cases])
    for (b, c), j in zip(cases, got):
        p = R.render(b, c)
        for k in ("subject", "text", "html"):
            assert p[k] == j[k], (k, b.get("source"))
    assert "<script>" not in got[3]["html"] and "javascript:" not in got[3]["html"]


def test_review_edge_cases_agree(sample_brief, sample_settings):
    """The divergences an adversarial review found, kept equal from now on."""
    dash = chr(0x2014)
    astral = chr(0x1F600)
    reqs, pys = [], []

    def both(fn, py, *args):
        reqs.append({"fn": fn, "args": list(args)})
        pys.append(py(*args))

    for s in ["  a\x1cb\x1f ", "x\x85", " tabs\tand\nlines "]:
        both("collapse", E.collapse, s)
    for s in [astral * 30 + " end of the story here", ("word " + astral) * 40]:
        both("cutSummary", E.cut_summary, s, 50)
    for t in ["AB" + astral, astral * 3, "CVE"]:
        both("termHit", E.term_hit, "Story about " + t + " today", t)
    for d in ["0000-01-01", "2026-10-23\n", "\uff12\uff10\uff12\uff16-10-23", "2026-10-23T09:00:00Z"]:
        both("parseIso", E.parse_iso, d)
    for cfg in [{"version": 1, "categories": [{"id": "net\n", "name": "N", "queries": ["x"]}]},
                {"version": True, "categories": [{"id": "net", "name": "N", "queries": ["x"], "color": "#123456\n"}]},
                {"version": 1, "categories": [{"id": "net", "name": "N", "queries": ["x"]}],
                 "reader": {"role": "call 555\uff10555\uff100199"}}]:
        both("validateConfig", E.validate_config, cfg)
    weird = copy.deepcopy(sample_brief)
    weird["total"] = True
    for b, c in [(sample_brief, {}), (weird, None), (sample_brief, sample_settings)]:
        both("checkBrief", E.check_brief, b, c, NOW)
    led = E.ledger_add(E.empty_ledger(), sample_brief, False)
    reqs.append({"fn": "ledgerAdd", "args": [E.empty_ledger(), sample_brief, False]}); pys.append(led)
    assert led["sent_dates"] == []
    text = "x\n<!-- CONFIG:BEGIN -->\n<!-- CONFIG:END -->\n"
    reqs.append({"fn": "buildPrompt", "args": [text, sample_settings, True]}); pys.append(E.build_prompt(text, sample_settings, True))
    reqs.append({"fn": "buildPrompt", "args": [text, {}]}); pys.append(E.build_prompt(text, {}))
    raw = {"title": "Old " + dash + " story", "url": "https://e.com/1", "published": "last Tuesday"}
    both("cleanItem", E.clean_item, raw, 100)
    for k, (req, js) in enumerate(zip(reqs, js_calls(reqs))):
        assert same(pys[k], js), (req, pys[k], js)


def test_newsletter_numbers_are_escaped_and_none_is_hidden(sample_brief, sample_settings):
    cfg = copy.deepcopy(sample_settings)
    cfg["brief"]["summary_max_chars"] = "<img src=x onerror=alert(1)>"
    cfg["brief"]["window_hours"] = "<b>24</b>"
    b = copy.deepcopy(sample_brief)
    b.pop("window_hours", None)
    b["analysis"] = {"top_three": ["One", "NONE"], "connection": "NONE", "watch": ["none."], "action": "Act now"}
    py = R.render(b, cfg)
    js = js_calls([{"fn": "render", "args": [b, cfg]}])[0]
    assert py == js
    assert "<img src=x" not in py["html"] and "onerror" not in py["html"].replace("&lt;img src=x onerror", "")
    assert "Connection:" not in py["html"] and "Connection:" not in py["text"] and "Act now" in py["text"]


def test_collector_helpers_agree():
    """The forecast block and its address come out the same from both collectors."""
    from dailybrief import collect as C
    w = {"enabled": True, "place": " Example  City ", "latitude": 41.0, "longitude": -87.63, "units": "celsius"}
    answers = [
        {"current": {"temperature_2m": 51.4, "weather_code": 3},
         "daily": {"time": ["2026-10-23", None, 7], "weather_code": [3, "61", True], "temperature_2m_max": [58.2, None],
                   "temperature_2m_min": "x", "precipitation_probability_max": [10, 80, 0]}},
        {"current": [1, 2], "daily": {"time": ["2026-10-23"] * 6}},
        {"daily": {"time": ["2026-10-23"], "weather_code": [95]}, "current": {"temperature_2m": "warm"}},
    ]
    reqs = [{"fn": "collect.forecastUrl", "args": [w]}]
    pys = [C.forecast_url(w)]
    for a in answers:
        reqs.append({"fn": "collect.weatherFrom", "args": [a, w, NOW]})
        pys.append(C.weather_from(a, w, NOW))
    for k, (req, js) in enumerate(zip(reqs, js_calls(reqs))):
        assert same(pys[k], js), (req["fn"], pys[k], js)


def test_pages_with_photos_and_weather_are_identical(sample_brief, sample_settings):
    b = copy.deepcopy(sample_brief)
    b["weather"] = {"place": "<b>Example</b> City", "units": "fahrenheit", "fetched_at": "2026-10-23T10:58:00Z",
                    "current": {"temp": 51.5, "code": 3},
                    "days": [{"date": "2026-10-23", "code": 61, "hi": 58.5, "lo": -0.5, "rain": 80},
                             {"date": "2026-10-24", "code": True, "hi": "<i>", "lo": None, "rain": 0},
                             {"date": "nope", "code": 0}, "x",
                             {"date": "2026-10-25", "code": 95, "hi": -2.5, "lo": -10.49, "rain": 12.5},
                             {"date": "2026-10-26", "code": 71, "hi": 1e3, "lo": 0, "rain": None},
                             {"date": "2026-10-27", "code": 0, "hi": 70, "lo": 60, "rain": 5}]}
    items = b["categories"][0]["items"]
    items[0]["image"] = "https://img.example.com/a.jpg?w=600&h=400"
    items[1]["image"] = 'https://img.example.com/b.jpg" onerror="alert(1)'
    items[2]["image"] = "https://img.example.com/c.jpg"
    b["categories"][1]["items"][0]["image"] = "http://img.example.com/plain.jpg"
    b["categories"][1]["icon"] = "<svg onload=x>"
    celsius = copy.deepcopy(b)
    celsius["weather"]["units"] = "celsius"
    celsius["weather"]["current"] = None
    odd = copy.deepcopy(b)
    odd["weather"] = ["not", "a", "block"]
    cases = [(b, sample_settings), (celsius, None), (odd, sample_settings), (dict(b, source="web"), None)]
    got = js_calls([{"fn": "render", "args": [x, c]} for x, c in cases])
    for (x, c), j in zip(cases, got):
        p = R.render(x, c)
        for k in ("subject", "text", "html"):
            assert p[k] == j[k], k
    html = got[0]["html"]
    assert 'class="it lead"' in html and 'class="it th"' in html and "onerror" not in html and "http://img" not in html
    assert 'class="wx"' in html and "&lt;b&gt;Example&lt;/b&gt; City" in html and "<svg onload" not in html
    assert "59&deg;F" not in html and "52&deg;F" in html and "WEATHER, <B>EXAMPLE</B> CITY:" in got[0]["text"]
    assert 'class="wx"' not in got[2]["html"]
