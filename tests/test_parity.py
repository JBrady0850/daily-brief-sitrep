"""The browser engine (app/js) and the desktop engine (dailybrief) must agree.

Each case runs the same function with the same input in Node and in Python
and requires equal results, so the web page and the desktop email can never
pick, check or draw a brief differently.
"""
import copy
import json

from conftest import ROOT, js_calls

from dailybrief import collect as C, engine as E, render as R
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
        "not a url", "https://user@host.example.com:8080/path/", "  https://EXAMPLE.org/A  ",
        "https://www.example.com/events/#/details/market/101/2026-10-25T18", "https://example.com/story#comments",
        "https://example.com/calendar/#!/details/run/7/2026-10-27T17", "https://example.com/a#!x"]
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
    many = copy.deepcopy(good)
    many["countdowns"] = [{"label": "", "date": "2026-02-30", "milestones": [{"date": "x"}]}, "x",
                          {"label": "Late start", "date": "2027-01-01", "start": "2028-01-01", "idea": 3},
                          {"label": "Fine", "date": "2027-01-01"}, {"label": "Fifth", "date": "2027-02-01", "milestones": None}]
    return [good, bad, many, dict(good, countdowns="soon"), {}, [], {"categories": [{"id": "constructor", "name": "c", "queries": ["q"]}]}]


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


def test_on_topic_feed_stories_agree():
    cfg = {"version": 1, "categories": [{"id": "t", "name": "Tennis", "queries": ["tennis"], "require": [["tennis"]],
                                         "exclude": ["betting"], "topic_feeds": ["https://feeds.example.com/tennis.xml"]}]}
    cands = {"t": [{"title": "Swiatek wins in straight sets", "url": "https://e.com/1", "published": ago(2), "on_topic": True},
                   {"title": "Best betting picks for the final", "url": "https://e.com/2", "published": ago(2), "on_topic": True},
                   {"title": "Golf major moves to June", "url": "https://e.com/3", "published": ago(2)},
                   {"title": "Odd flag", "url": "https://e.com/4", "published": ago(2), "on_topic": 1}]}
    py = [E.select_brief(cands, cfg, None, NOW, "2026-10-23", "web"), E.validate_config(cfg)]
    got = js_calls([{"fn": "selectBrief", "args": [cands, cfg, None, NOW, "2026-10-23", "web"]}, {"fn": "validateConfig", "args": [cfg]}])
    for p, j in zip(py, got):
        assert same(p, j), json.dumps([p, j])[:2000]
    assert [i["title"] for i in py[0]["categories"][0]["items"]] == ["Swiatek wins in straight sets"]


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


def test_town_categories_agree():
    town = {"id": "local-news", "name": "Local ({location})", "queries": ['"{location}" council'], "require": [["{local_terms}"]],
            "needs_location": True, "feeds": ["https://tv.example.com/feed"]}
    plain = {"id": "tech", "name": "Tech", "queries": ["tech"], "require": [["tech"]], "feeds": []}
    custom = {"id": "mine", "name": "Mine", "queries": ['"{location}" {region} parade'], "require": [["parade"]]}
    readers = [{"location": "Springfield", "region": "Illinois", "local_terms": ["Sangamon County"],
                "local_feeds": ["https://tv.example.com/feed", "https://paper.example.com/rss", "not a link"]},
               {"location": "", "region": "", "local_terms": [], "local_feeds": []}, None]
    reqs, pys = [], []
    for c in (town, plain, custom):
        reqs.append({"fn": "isLocalCategory", "args": [c]}); pys.append(E.is_local_category(c))
        for r in readers:
            reqs.append({"fn": "resolveCategory", "args": [c, r]}); pys.append(E.resolve_category(c, r))
    cfgs = [{"version": 1, "reader": readers[0], "categories": [town]},
            {"version": 1, "reader": {"region": 5, "local_feeds": ["https://a.example.com/x"] * 6}, "categories": [plain]}]
    for cfg in cfgs:
        reqs.append({"fn": "validateConfig", "args": [cfg]}); pys.append(E.validate_config(cfg))
    got = js_calls(reqs)
    for p, j in zip(pys, got):
        assert same(p, j), json.dumps([p, j])[:1500]
    town_cat = E.resolve_category(town, readers[0])
    assert town_cat["feeds"] == ["https://tv.example.com/feed", "https://paper.example.com/rss"], "own feeds join town categories once"
    assert town_cat["require"] == [["Springfield", "Sangamon County"]]
    assert E.resolve_category(plain, readers[0])["feeds"] == [], "other categories never get them"
    assert E.resolve_category(custom, readers[0])["queries"] == ['("Springfield" OR "Sangamon County") Illinois parade']
    assert any("local_feeds" in e for e in E.validate_config(cfgs[0])["errors"]), "a bad link is refused"
    assert any("local_feeds" in e for e in E.validate_config(cfgs[1])["errors"]) and any("region" in e for e in E.validate_config(cfgs[1])["errors"])


def test_unchecked_desks_render_the_same(sample_brief, sample_settings):
    b = copy.deepcopy(sample_brief)
    b["categories"][0]["items"] = []
    b["categories"][0]["unchecked"] = True
    b["categories"][1]["items"] = []
    got = js_calls([{"fn": "render", "args": [b, sample_settings]}])[0]
    p = R.render(b, sample_settings)
    for k in ("subject", "text", "html"):
        assert p[k] == got[k], k
    assert "Not checked today: the news search did not answer" in p["html"] and "Not checked today, because the news search did not answer: " in p["html"]
    assert "No new items for: " + b["categories"][1]["name"] in p["html"]
    assert "Not checked today: the news search did not answer. Try again later." in p["text"]


def test_town_searches_name_the_nearby_places_the_same_way():
    """A town search asks for the town or a nearby place the reader named (both engines)."""
    lists = [["Springfield"], ["Springfield", "Sangamon County", "springfield", "IL", "Chatham", "Rochester", "Auburn"],
             ['Spring"field', "  Sangamon   County "], [], ["", "Chatham"]]
    queries = ['"{location}" council', '("high school" OR "{location}") prep', '"{location}" (a OR b) "{location}"', "no town here",
               '"{location}"("x" OR y)']
    reqs, pys = [], []
    for terms in lists:
        reqs.append({"fn": "areaTerms", "args": [terms]}); pys.append(E.area_terms(terms))
        for q in queries:
            area = E.area_terms(terms)
            reqs.append({"fn": "areaQuery", "args": [q, area]}); pys.append(E.area_query(q, area))
    for p, j in zip(pys, js_calls(reqs)):
        assert same(p, j), json.dumps([p, j])
    assert E.area_terms(lists[1]) == ["Springfield", "Sangamon County", "Chatham", "Rochester"], "no repeats, no short names, four at most"
    area = E.area_terms(lists[1])
    assert E.area_query('"{location}" council', area) == '("Springfield" OR "Sangamon County" OR "Chatham" OR "Rochester") council'
    assert E.area_query('("high school" OR "{location}") prep', area) == '("high school" OR "{location}") prep', "groups never nest"
    assert E.area_query('"{location}" council', ["Springfield"]) == '"{location}" council', "the town alone stays as it was"
    town = {"id": "local-news", "name": "Local ({location})", "queries": ['"{location}" council'], "require": [["{local_terms}"]],
            "needs_location": True}
    got = E.resolve_category(town, {"location": "Springfield", "local_terms": ["Sangamon County"]})
    assert got["queries"] == ['("Springfield" OR "Sangamon County") council'] and got["name"] == "Local (Springfield)"
    assert E.resolve_category(town, {"location": "", "local_terms": ["Sangamon County"]})["queries"] == ['"" council'], \
        "no town, no area search (as before)"


def test_state_codes_agree():
    inputs = ["Florida", "FL", "fl", " new  york ", "Washington", "Washington, D.C.", "DC", "District of Columbia", "West Virginia",
              "Fla.", "Ontario", "", None, 5, "TX ", "texas", "Puerto Rico"]
    reqs = [{"fn": "stateCode", "args": [x]} for x in inputs]
    got = js_calls(reqs)
    for x, j in zip(inputs, got):
        assert same(E.state_code(x), j), (x, j)
    assert [E.state_code(x) for x in inputs[:10]] == ["FL", "FL", "FL", "NY", "WA", "DC", "DC", "DC", "WV", ""]
    js_table = js_calls([{"fn": "stateCode", "args": [name]} for name in E.US_STATES])
    assert js_table == list(E.US_STATES.values()) and len(E.US_STATES) == 51


def test_a_desk_the_backup_collection_covers_counts_as_checked():
    """Searches all failed, but GitHub's backup collection searched this category: the
    desk says "No new items", not "Not checked today" (both collectors agree)."""
    failed = [{"query": "q", "error": "the news index turned the search away (busy or offline)"}]
    cases = [
        {"queries": failed, "feeds": []},                                                       # nothing answered
        {"queries": failed, "feeds": [], "backup": {"items": 2, "error": "", "covered": True}},   # backup searched it
        {"queries": failed, "feeds": [], "backup": {"items": 0, "error": "", "covered": False}},  # not in the backup
        {"queries": failed, "feeds": [], "backup": {"items": 0, "error": "the site answered 404", "covered": False}},
        {"queries": failed, "feeds": [], "local": {"state": "IL", "items": 3, "error": ""}},
        {"queries": [{"query": "q", "error": "", "note": "not needed"}], "feeds": []},
    ]
    reqs, pys = [], []
    for h in cases:
        brief = {"categories": [{"id": "x", "items": []}]}
        reqs.append({"fn": "collect.markUnchecked", "args": [brief, {"x": h}]})
        pys.append(C.mark_unchecked(json.loads(json.dumps(brief)), {"x": h}))
    got = js_calls(reqs)
    for p, j in zip(pys, got):
        assert same(p, j), json.dumps([p, j])
    flags = [bool(b["categories"][0].get("unchecked")) for b in pys]
    assert flags == [True, False, True, True, False, False]


def test_settings_from_before_0_2_0_lose_email_quietly():
    CAT = {"id": "net", "name": "Network", "queries": ['"zero trust"'], "require": [["zero trust"]]}
    old = [{"version": 1, "delivery": {"time": "06:15", "timezone": "", "channels": ["issue", "email"]},
            "email": {"to": ["someone@example.com"]}, "categories": [CAT]},
           {"version": 1, "delivery": {"time": "", "timezone": "", "channels": ["email"]}, "categories": [CAT]},
           {"version": 1, "delivery": {"time": "", "timezone": "", "channels": ["issue", "fax"]}, "categories": [CAT]}]
    reqs, pys = [], []
    for cfg in old:
        for fn, py in (("normalizeConfig", E.normalize_config), ("validateConfig", E.validate_config)):
            reqs.append({"fn": fn, "args": [cfg]})
            pys.append(py(json.loads(json.dumps(cfg))))
    for p, j in zip(pys, js_calls(reqs)):
        assert same(p, j), json.dumps([p, j])
    n0, v0, n1, v1, n2, v2 = pys
    assert n0["delivery"]["channels"] == ["issue"] and "email" not in n0
    assert v0 == {"errors": [], "warnings": []}, "no warning on every review"
    assert n1["delivery"]["channels"] == ["issue"] and v1["errors"] == [] and v1["warnings"] == []
    assert v2["errors"] == ['delivery.channels must be ["issue"].'], "other unknown channels are still errors"


def test_built_time_labels_agree(sample_brief, sample_settings):
    """The page says when it was built, in the reader's time zone, the same way in both engines."""
    times = ["2026-10-25T14:56:08Z", "2026-01-15T05:30:00Z", "2026-03-08T07:59:00Z", "2026-03-08T08:00:00Z",
             "2026-11-01T06:59:59Z", "2026-11-01T07:00:00Z", "2026-06-30T00:00:00Z", "2026-06-30T12:00:00Z", "not a time", None]
    zones = ["America/Chicago", "America/New_York", "America/Phoenix", "Pacific/Honolulu", "Europe/London", "Asia/Kolkata",
             "Australia/Lord_Howe", "Asia/Kathmandu", "UTC", "", "Nowhere/Land", None]
    pairs = [(t, z) for t in times for z in zones]
    got = js_calls([{"fn": "N.builtLabel", "args": [t, z]} for t, z in pairs])
    for (t, z), j in zip(pairs, got):
        assert R.built_label(t, z) == j, (t, z, R.built_label(t, z), j)
    assert R.built_label("2026-10-25T14:56:08Z", "America/Chicago") == "Sunday, October 25, 2026 at 9:56 AM CDT"
    assert R.built_label("2026-01-15T05:30:00Z", "America/Chicago") == "Wednesday, January 14, 2026 at 11:30 PM CST"
    assert R.built_label("2026-03-08T08:00:00Z", "America/Chicago") == "Sunday, March 08, 2026 at 3:00 AM CDT", "daylight time starts"
    assert R.built_label("2026-06-30T12:00:00Z", "Asia/Kolkata") == "Tuesday, June 30, 2026 at 5:30 PM UTC+5:30"
    assert R.built_label("2026-06-30T00:00:00Z", "") == "Tuesday, June 30, 2026 at 12:00 AM UTC"
    assert R.built_label("2026-06-30T12:00:00Z", "Nowhere/Land").endswith("12:00 PM UTC"), "an unknown zone falls back to UTC"
    assert R.built_label("not a time", "America/Chicago") == ""
    # The page, its plain text and the GitHub issue all carry it, identically in both engines.
    cfg = copy.deepcopy(sample_settings)
    cfg["delivery"] = dict(cfg.get("delivery") or {}, timezone="America/Chicago")
    b = copy.deepcopy(sample_brief)
    b["generated_at"] = "2026-10-25T14:56:08Z"
    j = js_calls([{"fn": "render", "args": [b, cfg]}])[0]
    p = R.render(b, cfg)
    for k in ("subject", "text", "html"):
        assert p[k] == j[k], k
    assert '<p class="built">Built Sunday, October 25, 2026 at 9:56 AM CDT</p>' in p["html"]
    assert "Built Sunday, October 25, 2026 at 9:56 AM CDT &middot;" in p["html"] and "14:56" not in p["html"], "no UTC time in the page"
    assert p["text"].splitlines()[1] == "Built Sunday, October 25, 2026 at 9:56 AM CDT"
    from dailybrief.markdown import render_markdown
    assert "Built Sunday, October 25, 2026 at 9:56 AM CDT" in render_markdown(b, cfg)
    no_time = dict(b, generated_at="")
    assert 'class="built"' not in R.render(no_time, cfg)["html"], "no time, no line"


def test_story_and_forecast_times_use_the_reader_zone(sample_brief, sample_settings):
    """Story times and the forecast's "updated" time follow the reader's zone, never UTC with a Z."""
    import re
    pairs = [(t, z) for t in ["2026-10-23T07:48:00Z", "2026-01-15T05:30:00Z", "2026-03-08T08:00:00Z", "bad", None]
             for z in ["America/Chicago", "Asia/Kolkata", "UTC", "", "Nowhere/Land", None]]
    got = js_calls([{"fn": "N.stamp", "args": [t, z]} for t, z in pairs])
    for (t, z), j in zip(pairs, got):
        assert R.stamp(t, z) == j, (t, z, R.stamp(t, z), j)
    assert R.stamp("2026-10-23T07:48:00Z", "America/Chicago") == "Oct 23, 2:48 AM CDT"
    assert R.stamp("2026-01-15T05:30:00Z", "America/Chicago") == "Jan 14, 11:30 PM CST", "the date follows the zone too"
    assert R.stamp("2026-10-23T07:48:00Z", None) == "Oct 23, 7:48 AM UTC", "no zone set reads as UTC, spelled out"
    assert R.stamp("bad", "America/Chicago") == ""
    cfg = copy.deepcopy(sample_settings)
    cfg["delivery"] = dict(cfg.get("delivery") or {}, timezone="America/Chicago")
    j = js_calls([{"fn": "render", "args": [sample_brief, cfg]}])[0]
    p = R.render(sample_brief, cfg)
    assert p["html"] == j["html"]
    assert not re.search(r"[0-9]{2}:[0-9]{2}Z", p["html"]), "no Zulu time anywhere on the page"
    assert re.search(r"updated [A-Z][a-z]{2} [0-9]{2}, [0-9]{1,2}:[0-9]{2} [AP]M C[DS]T", p["html"]), "the forecast time is local"
    assert re.search(r"&middot; [A-Z][a-z]{2} [0-9]{2}, [0-9]{1,2}:[0-9]{2} [AP]M C[DS]T", p["html"]), "story times are local"


def _event_config(sample_settings):
    cfg = copy.deepcopy(sample_settings)
    cfg["categories"] = [E.category_from_library(library(), "local-events"), E.category_from_library(library(), "us-news")]
    cfg["reader"] = dict(cfg.get("reader") or {}, location="Example City", region="Florida", local_terms=[])
    cfg["delivery"] = dict(cfg.get("delivery") or {}, timezone="America/Chicago")
    return cfg


def test_calendar_events_lead_things_to_do_in_both_engines(sample_settings):
    """Events keep the calendar's order ahead of news, drop once over, and show their day and place."""
    now = "2026-10-25T17:00:00Z"
    week = json.loads((ROOT / "tests" / "fixtures" / "cityspark_week.json").read_text())
    cal = {"slug": "ExampleTV", "station": "WEXA", "page": "https://www.example.com/events/", "links": "hash"}
    events = js_calls([{"fn": "collect.eventsFrom", "args": [week, cal, now]}])[0]
    assert [e["title"] for e in events] == ["Harvest Night Market", "Community Choir Rehearsal", "Tuesday Night Run",
                                            "Pumpkin Walk", "Library Story Time"], "a day at a time, so the week shows"
    assert events[0]["url"] == "https://events.example.com/market", "the organizer's own page first"
    assert events[3]["url"] == "https://www.example.com/events/#/details/pumpkin-walk/102/2026-10-25T00", "a social link: the station calendar"
    assert events[3]["event"] == {"start": "2026-10-25", "all_day": True, "venue": "Riverside Park", "place": "Example City, FL"}
    assert events[0]["event"]["start"] == "2026-10-25T23:30:00Z" and events[0]["source"] == "WEXA community calendar"
    plain = js_calls([{"fn": "collect.eventsFrom", "args": [week, dict(cal, links=""), now]},
                      {"fn": "collect.eventsFrom", "args": [week, dict(cal, links="hashBang"), now]}])
    assert plain[0][3]["url"] == "https://www.example.com/events/", "never a social site: the calendar page instead"
    assert plain[1][3]["url"] == "https://www.example.com/events/#!/details/pumpkin-walk/102/2026-10-25T00"
    news = {"title": "City council approves a new park", "url": "https://news.example.com/park", "source": "Example News",
            "published": "2026-10-25T15:00:00Z", "summary": "The park opens next spring."}
    over = dict(events[4], title="Breakfast Talk", url="https://breakfast.example.com",
                event={"start": "2026-10-25T12:00:00Z", "all_day": False, "venue": "", "place": ""})
    cands = {"local-events": [news] + [dict(e, on_topic=True) for e in events] + [dict(over, on_topic=True)], "us-news": []}
    cfg = _event_config(sample_settings)
    py = E.select_brief(cands, cfg, None, now, "2026-10-25", "web")
    js = js_calls([{"fn": "selectBrief", "args": [cands, cfg, None, now, "2026-10-25", "web"]}])[0]
    assert same(py, js)
    items = py["categories"][0]["items"]
    assert [i["title"] for i in items] == ["Harvest Night Market", "Community Choir Rehearsal", "Tuesday Night Run",
                                           "Pumpkin Walk", "Library Story Time"], "events first, in calendar order"
    assert py["categories"][0]["rejected"].get("past event") == 1
    assert all(i["recency"] == "news" and i["event"] for i in items)
    chk = E.check_brief(py, cfg, now)
    assert chk["errors"] == [] and same(chk, js_calls([{"fn": "checkBrief", "args": [py, cfg, now]}])[0])
    bad = copy.deepcopy(py)
    bad["categories"][0]["items"][0]["event"] = {"start": "soon"}
    assert any("event needs a start time" in e for e in E.check_brief(bad, cfg, now)["errors"])
    j = js_calls([{"fn": "render", "args": [py, cfg]}])[0]
    p = R.render(py, cfg)
    for k in ("subject", "text", "html"):
        assert p[k] == j[k], k
    assert '<span class="pill ev">Sun, Oct 25, 6:30 PM CDT</span><span class="src">WEXA community calendar &middot; Town Square, Example City, FL</span>' in p["html"]
    assert '<span class="pill ev">Sun, Oct 25, all day</span>' in p["html"]
    assert "powered by CitySpark" in p["html"] and "powered by CitySpark" in p["text"]
    assert "EVENT, Mon, Oct 26, 7:00 PM CDT, Grace Hall, Example City, FL" in p["text"]
    from dailybrief.markdown import render_markdown
    md = render_markdown(py, cfg)
    assert "EVENT, Sun, Oct 25, 6:30 PM CDT, Town Square, Example City, FL" in md and "powered by CitySpark" in md
    plain_brief = R.render(E.select_brief({"local-events": [news], "us-news": []}, cfg, None, now, "2026-10-25", "web"), cfg)
    assert "CitySpark" not in plain_brief["html"] and "pill ev" not in plain_brief["html"], "no events, no credit line"


def test_event_times_and_nearest_calendars_agree():
    evs = [{"start": "2026-10-25T23:30:00Z", "all_day": False}, {"start": "2026-10-31", "all_day": True},
           {"start": "2026-03-08T07:30:00Z", "all_day": False, "venue": "Hall", "place": "Town, ST"}, {"start": "bad"}, None, "x"]
    zones = ["America/Chicago", "Asia/Kolkata", "", None]
    pairs = [(e, z) for e in evs for z in zones]
    got = js_calls([{"fn": "N.eventWhen", "args": [e, z]} for e, z in pairs])
    for (e, z), j in zip(pairs, got):
        assert R.event_when(e, z) == j, (e, z)
    assert R.event_when(evs[0], "America/Chicago") == "Sun, Oct 25, 6:30 PM CDT"
    assert R.event_when(evs[1], "America/Chicago") == "Sat, Oct 31, all day"
    assert R.event_where(evs[2]) == "Hall, Town, ST" == js_calls([{"fn": "N.eventWhere", "args": [evs[2]]}])[0]
    cals = json.loads((ROOT / "tests" / "fixtures" / "calendars.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
    near = js_calls([{"fn": "collect.calendarsNear", "args": [cals, "FL", 30.25, -85.65]},
                     {"fn": "collect.calendarsNear", "args": [cals, "FL", 25.8, -80.2]},
                     {"fn": "collect.calendarsNear", "args": [cals, "GA", 30.25, -85.65]},
                     {"fn": "collect.calendarsNear", "args": [None, "FL", 30.25, -85.65]}])
    assert [c["slug"] for c in near[0]] == ["ExampleTV"], "only calendars whose area reaches the town"
    assert [c["slug"] for c in near[1]] == ["FarAwayTV"]
    assert near[2] == [] and near[3] == []


def test_several_countdowns_and_old_single_countdown_settings(sample_brief, sample_settings):
    """Up to four countdown cards, each with its milestones; a past one drops out; settings
    with the old single `countdown` keep it as the first card, or none when it was off."""
    cfg = copy.deepcopy(sample_settings)
    cfg["countdowns"] = [
        {"label": "Days to retirement", "date": "2027-06-30", "start": "2026-10-01", "idea": "federal-retirement",
         "milestones": [{"date": "2027-01-01", "label": "Review TSP withdrawals", "note": ""}]},
        {"label": "Days to Election Day", "date": "2026-11-03", "start": "2026-10-23", "milestones": []},
        {"label": "Already over", "date": "2026-10-01", "milestones": []},
        {"label": "Days to Thanksgiving", "date": "2026-11-26", "milestones": [{"date": "2026-11-24", "label": "Cook ahead"}]},
        {"label": "Fifth is ignored", "date": "2026-12-25", "milestones": []}]
    assert E.validate_config(cfg)["errors"] == ["Use at most 4 countdowns."]
    j = js_calls([{"fn": "render", "args": [sample_brief, cfg]}])[0]
    p = R.render(sample_brief, cfg)
    for k in ("subject", "text", "html"):
        assert p[k] == j[k], k
    assert p["html"].count('<section class="cd">') == 3, "past and fifth countdowns drop out"
    assert '<div class="cdg"><section class="cd">' in p["html"]
    for label in ("Days to retirement", "Days to Election Day", "Days to Thanksgiving"):
        assert label in p["html"] and label.upper() in p["text"]
    assert "Already over" not in p["html"] and "Fifth is ignored" not in p["html"]
    from dailybrief.markdown import render_markdown
    md = render_markdown(sample_brief, cfg)
    assert "**Days to retirement:" in md and "**Days to Thanksgiving:" in md
    # Old settings: one countdown with an on/off switch.
    old_on = {k: v for k, v in sample_settings.items() if k != "countdowns"}
    old_on["countdown"] = {"enabled": True, "label": "Days to the spring trip", "date": "2027-03-31", "start": "", "milestones": []}
    old_off = dict(old_on, countdown=dict(old_on["countdown"], enabled=False))
    got = js_calls([{"fn": "normalizeConfig", "args": [old_on]}, {"fn": "normalizeConfig", "args": [old_off]},
                    {"fn": "validateConfig", "args": [old_on]}])
    assert got[0]["countdowns"] == E.normalize_config(old_on)["countdowns"] == [
        {"label": "Days to the spring trip", "date": "2027-03-31", "start": "", "milestones": []}]
    assert "countdown" not in got[0] and "countdown" not in E.normalize_config(old_on)
    assert got[1]["countdowns"] == E.normalize_config(old_off)["countdowns"] == []
    assert got[2] == E.validate_config(old_on) and not any("countdown" in w for w in got[2]["warnings"]), got[2]
    both = dict(old_on, countdowns=[])
    assert E.normalize_config(both)["countdowns"] == [], "a countdowns list wins over the old field"
    # The same countdown twice is kept once, in both engines and in the app's upgrade.
    twice = dict(cfg, countdowns=[cfg["countdowns"][1], dict(cfg["countdowns"][1], label=" days to election day ", start=""),
                                  cfg["countdowns"][0], "x", "x"])
    got = js_calls([{"fn": "normalizeConfig", "args": [twice]}, {"fn": "upgradeCountdown", "args": [twice]}])
    py = E.normalize_config(twice)["countdowns"]
    assert got[0]["countdowns"] == py == got[1]["countdowns"] == E.upgrade_countdown(twice)["countdowns"]
    assert [c if isinstance(c, str) else c["label"] for c in py] == ["Days to Election Day", "Days to retirement", "x", "x"]
