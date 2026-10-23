"""Browser tests of the app: the web version with its in-browser collector
(every outside request answered from recorded data), and the desktop app with
recorded feeds. Needs Playwright with Chromium (see CONTRIBUTING.md)."""
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest
from conftest import ROOT, feed_bytes

from dailybrief import server

sync_api = pytest.importorskip("playwright.sync_api")

APP = (ROOT / "app" / "index.html").as_uri()
CORS = {"access-control-allow-origin": "*"}
FORECAST = {"current": {"temperature_2m": 51.4, "weather_code": 3},
            "daily": {"time": [(datetime.now() + timedelta(days=k)).strftime("%Y-%m-%d") for k in range(4)],
                      "weather_code": [3, 61, 0, 95], "temperature_2m_max": [58.2, 55, 61.5, 60.1],
                      "temperature_2m_min": [44.1, 47.9, 43, 50], "precipitation_probability_max": [10, 80, 0, 65]}}
TOWNS = {"results": [{"name": "Springfield", "admin1": "Illinois", "country": "United States", "country_code": "US",
                      "latitude": 39.80172, "longitude": -89.64371}]}
# Headlines the fake news index hands out, by a word in the search.
STORIES = {
    "stocks": ["Stocks rally to a record as inflation cools", "Dow closes higher after jobs report"],
    "airlines": ["Airlines add holiday flights as travelers book early", "TSA expects record airport crowds"],
    "study": ["Researchers link sleep to heart health in a new study", "Scientists map a disease gene"],
    "inspiring": ["Inspiring comeback: a runner overcame injury to finish", "A survivor's resilience inspires a town"],
    "Congress": ["Congress passes a stopgap budget bill", "Supreme Court hears a voting case"],
    "NATO": ["NATO leaders meet for summit talks", "United Nations calls for ceasefire talks"],
    "NFL": ["Chiefs beat Bills in overtime thriller", "NBA trade shakes up the playoff race"],
}


def gdelt_answer(url, calls):
    q = parse_qs(urlsplit(url).query)["query"][0]
    calls.append(q)
    now = datetime.now(timezone.utc)
    arts = []
    for word, titles in STORIES.items():
        if word in q:
            for k, t in enumerate(titles):
                seen = (now - timedelta(hours=1 + k)).strftime("%Y%m%dT%H%M%SZ")
                arts.append({"url": "https://news.example.com/%s/%d" % (word.lower(), k), "title": t.replace(":", " :"),
                             "seendate": seen, "socialimage": "https://img.example.com/%s%d.jpg" % (word, k),
                             "domain": "news.example.com", "language": "English", "sourcecountry": "United States"})
    return json.dumps({"articles": arts})


def route_world(page, calls, gdelt_status=200):
    """Answers every outside request the way the real services would, with CORS."""
    def handle(route):
        url = route.request.url
        if urlsplit(url).hostname in ("127.0.0.1", "localhost"):
            return route.continue_()  # the desktop app itself
        if "api.gdeltproject.org" in url:
            if gdelt_status != 200:
                calls.append("refused")
                return route.fulfill(status=gdelt_status, body="busy")  # like GDELT: no CORS header on errors
            return route.fulfill(status=200, body=gdelt_answer(url, calls), headers=dict(CORS, **{"content-type": "application/json"}))
        if "geocoding-api.open-meteo.com" in url:
            return route.fulfill(status=200, body=json.dumps(TOWNS), headers=CORS)
        if "api.open-meteo.com" in url:
            calls.append("forecast")
            return route.fulfill(status=200, body=json.dumps(FORECAST), headers=CORS)
        if "img.example.com" in url or "github.io" in url:
            svg = (ROOT / "app" / "img" / "sample" / "markets.svg").read_bytes()
            return route.fulfill(status=200, body=svg, headers={"content-type": "image/svg+xml"})
        if url.startswith("http"):
            calls.append("feed")
            return route.fulfill(status=200, body=feed_bytes("rss_feed.xml"), headers=dict(CORS, **{"content-type": "application/rss+xml"}))
        return route.continue_()
    page.route("http*://**/*", handle)


@pytest.fixture(scope="module")
def browser():
    try:
        with sync_api.sync_playwright() as p:
            b = p.chromium.launch()
            yield p, b
            b.close()
    except Exception as exc:  # no browser installed
        if os.environ.get("REQUIRE_BROWSER"):
            raise
        pytest.skip("Chromium is not available: %s" % exc)


def open_page(browser, url, device=None, calls=None, gdelt_status=200, state=None):
    p, b = browser
    ctx = b.new_context(**(p.devices[device] if device else {"viewport": {"width": 1100, "height": 900}}))
    ctx.add_init_script("window.DB_COLLECT_GAP = 0;")
    if state is not None:
        # Only the first load gets the saved choices; a reload keeps what the app saved since.
        ctx.add_init_script("if (!localStorage.getItem('db.state.v1')) localStorage.setItem('db.state.v1', %s);" % json.dumps(json.dumps(state)))
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    route_world(page, calls if calls is not None else [], gdelt_status)
    page.goto(url)
    return ctx, page, errors


def test_web_version_interview_collects_and_shows_the_page(browser):
    calls = []
    ctx, page, errors = open_page(browser, APP, calls=calls)
    page.wait_for_selector(".hero")
    page.click("text=Next question")
    page.click("text=Next question")
    page.fill(".wxpick input", "Springfield")
    page.click("text=Find my town")
    page.click(".wxpick .chip >> text=Springfield, Illinois")
    assert "forecast for Springfield, Illinois" in page.inner_text(".wxpick")
    for _ in range(5):
        page.click("text=Next question")
    assert "Springfield, Illinois (fahrenheit)" in page.inner_text(".interview")
    page.click("text=Save and get my brief")
    page.wait_for_selector("iframe.page", timeout=30000)
    frame = page.frame_locator("iframe.page")
    assert "SPRINGFIELD, ILLINOIS" in frame.locator("section.wx").inner_text().upper() and "51" in frame.locator("div.wxt").inner_text()
    assert frame.locator("li.lead img").count() >= 1
    assert "Stocks rally to a record as inflation cools" in frame.locator("main").inner_text()  # spacing tidied
    assert "forecast" in calls and any("sourcelang:english" in c for c in calls)
    state = page.evaluate("DB_APP.state()")
    assert state["setup_done"] and state["brief"]["source"] == "web" and state["brief"]["weather"]["place"] == "Springfield, Illinois"
    hist = page.evaluate("DB_APP.history()")
    assert len(hist["urls"]) == state["brief"]["total"] > 0, "what was shown counts as seen"
    # The same run again leaves out everything already shown.
    page.click("text=Check for newer stories")
    page.wait_for_function("DB_APP.state().brief.withheld > 0", timeout=30000)
    assert errors == []
    ctx.close()


def test_returning_visitor_gets_the_brief_by_itself_once_a_day(browser):
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["categories"] = [c for c in cfg["categories"] if not c.get("needs_location")]
    state = {"version": 1, "tab": "setup", "step": 7, "config": cfg, "setup_done": True, "auto_run": True}
    calls = []
    ctx, page, errors = open_page(browser, APP, calls=calls, state=state)
    page.wait_for_selector("iframe.page", timeout=30000)
    assert page.evaluate("DB_APP.state().tab") == "brief"
    searches = len([c for c in calls if c not in ("forecast", "feed")])
    assert searches >= len(cfg["categories"])
    page.reload()
    page.wait_for_selector("iframe.page")
    page.wait_for_timeout(2000)
    assert len([c for c in calls if c not in ("forecast", "feed")]) == searches, "already collected today"
    assert errors == []
    ctx.close()


def test_a_busy_news_index_still_gives_a_brief_from_the_feeds(browser):
    calls = []
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["categories"] = [c for c in cfg["categories"] if c["id"] in ("travel", "markets-economy")]
    for c in cfg["categories"]:
        c["feeds"] = ["https://feeds.example.com/%s.xml" % c["id"]]
        c["require"] = []
    cfg["brief"]["window_hours"] = 168
    cfg["brief"]["backfill_max_hours"] = 168
    state = {"version": 1, "tab": "brief", "config": cfg, "setup_done": True}
    ctx, page, errors = open_page(browser, APP, calls=calls, gdelt_status=503, state=state)
    page.click("text=Get today's brief")
    page.wait_for_selector("iframe.page", timeout=30000)
    assert calls.count("refused") == 4, "two searches, each retried once, then the busy index is left alone"
    page.click("text=Sources and filters")
    text = page.inner_text("#briefview")
    assert "the site answered 503" in text and "skipped: the news index was busy" in text
    assert errors == []
    ctx.close()


def test_pasted_and_sample_briefs(browser):
    ctx, page, errors = open_page(browser, APP)
    page.click('#tabs button[data-tab="brief"]')
    page.click("text=Other ways to fill the page")
    page.click("text=Show the sample brief")
    page.wait_for_selector("iframe.page")
    assert "[SAMPLE]" in page.inner_text("#briefview h2")
    frame = page.frame_locator("iframe.page")
    assert "Friday, October 23, 2026" in frame.locator("h1.ttl").inner_text()
    assert frame.locator("section.card .ico svg").count() == 6
    brief = json.loads((ROOT / "examples" / "sample-brief.json").read_text())
    brief["source"] = "ai"
    page.click("text=Other ways to fill the page")
    page.fill("#tab-brief textarea", "Here it is:\n```json\n" + json.dumps(brief) + "\n```")
    page.click("text=Show the pasted brief")
    page.wait_for_function("document.querySelector('#briefview h2').textContent.indexOf('[SAMPLE]') < 0")
    page.click("text=Mark as read")
    page.click("text=Other ways to fill the page")
    page.fill("#tab-brief textarea", json.dumps(brief))
    page.click("text=Show the pasted brief")
    page.wait_for_function("document.querySelector('#briefview .hint').textContent.indexOf('0 stories') === 0")
    assert errors == []
    ctx.close()


def test_custom_category_and_ai_prompt(browser):
    ctx, page, errors = open_page(browser, APP)
    page.click("text=Next question")
    page.click("text=Or build one step by step")
    page.fill(".builder input >> nth=0", "Amateur Radio")
    page.fill(".builder input >> nth=1", "ham radio, amateur radio, ARRL")
    page.click("text=Add category")
    assert page.locator("text=Your own categories").count() == 1
    page.click('#tabs button[data-tab="ai"]')
    page.click("#tab-ai .seg >> text=ChatGPT")
    assert "expects your settings as a file" in page.inner_text("#tab-ai")
    state = page.evaluate("JSON.parse(localStorage.getItem('db.state.v1'))")
    assert any(c["id"] == "amateur-radio" for c in state["config"]["categories"])
    assert errors == []
    ctx.close()


def test_category_tiles_toggle_and_show_every_group(browser):
    ctx, page, errors = open_page(browser, APP)
    page.click("text=Next question")
    assert page.locator(".ctile").count() == 67
    page.click("label[for=lib-nfl]")  # the Sports group starts open
    assert page.evaluate("DB_APP.state().config.categories.some(c => c.id === 'nfl' && c.icon === 'football')")
    assert page.locator(".ctile.on >> text=NFL Football").count() == 1
    page.click("label[for=lib-nfl]")
    assert not page.evaluate("DB_APP.state().config.categories.some(c => c.id === 'nfl')")
    assert errors == []
    ctx.close()


def test_phone_layout_never_scrolls_sideways(browser):
    ctx, page, errors = open_page(browser, APP, device="iPhone 13")
    page.wait_for_selector(".interview")
    for tab in ("setup", "categories", "brief", "daily", "ai", "settings", "help"):
        page.click('#tabs button[data-tab="%s"]' % tab)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), tab
    assert errors == []
    ctx.close()


def test_desktop_app_collects_and_shows_the_page(browser):
    app = server.DesktopApp(port=0, fetcher=lambda u: feed_bytes("google_news.xml" if "google" in u else "rss_feed.xml"), pause=0)
    app.start_background()
    try:
        ctx, page, errors = open_page(browser, app.url)
        page.wait_for_selector(".modebar.on")
        page.click('#tabs button[data-tab="brief"]')
        page.click("text=Get today's brief")
        page.wait_for_selector("iframe.page", timeout=20000)
        assert page.locator("text=Email it now").count() == 0
        assert page.locator("text=Sources and filters").count() == 1
        assert errors == []
        ctx.close()
    finally:
        app.stop()


def test_a_crafted_backup_is_refused_and_copy_never_injects_html(browser, tmp_path):
    p, b = browser
    ctx = b.new_context(viewport={"width": 1100, "height": 900})
    page = ctx.new_page()
    errors, messages = [], []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: (messages.append(d.message), d.accept()))
    route_world(page, [])
    page.goto(APP)
    page.wait_for_selector(".interview")
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["brief"]["summary_max_chars"] = "<img src=x onerror=\"document.title='owned'\">"
    backup = tmp_path / "backup.json"
    backup.write_text(json.dumps({"db_backup": 1, "version": "0.1.0", "state": {"version": 1, "config": cfg}, "history": None}))
    page.click("#tabs button[data-tab=settings]")
    page.set_input_files("#tab-settings input[type=file]", str(backup))
    page.wait_for_timeout(300)
    assert any("problems" in m for m in messages), messages
    # Even if bad settings got in, the page escapes them, and the copy
    # fallback (no rich clipboard) copies text only: the page title never changes.
    page.evaluate("p => { DB_APP.state().config.brief.summary_max_chars = p; }", cfg["brief"]["summary_max_chars"])
    page.evaluate("window.ClipboardItem = undefined")
    page.click("#tabs button[data-tab=brief]")
    brief = json.loads((ROOT / "examples" / "sample-brief.json").read_text())
    brief["source"] = "ai"
    page.click("text=Other ways to fill the page")
    page.fill("#tab-brief textarea", json.dumps(brief))
    page.click("text=Show the pasted brief")
    page.wait_for_selector("iframe.page")
    page.click("text=Copy newsletter")
    page.wait_for_timeout(300)
    assert page.title() != "owned" and errors == []
    ctx.close()


def test_type_a_topic_with_suggestions(browser):
    ctx, page, errors = open_page(browser, APP)
    page.wait_for_selector(".interview")
    page.click("text=Next question")
    box = page.locator(".quickadd input")
    box.fill("cloud outages")
    page.wait_for_selector(".quickadd .chip")
    assert "Cloud and Data Centers" in page.inner_text(".quickadd .chips")
    page.click(".quickadd .chip >> text=Cloud and Data Centers")
    page.locator(".quickadd input").fill("electric cars, EVs, charging stations")
    page.locator(".quickadd input").press("Enter")
    cats = page.evaluate("DB_APP.state().config.categories")
    own = [c for c in cats if c["name"] == "Electric cars"]
    assert own and own[0]["require"] == [["electric cars", "EVs", "charging stations"]]
    assert own[0]["queries"] == ['("electric cars" OR EVs OR "charging stations")']
    assert any(c["id"] == "cloud-infrastructure" for c in cats)
    assert page.evaluate("window.DB_ENGINE.validateConfig(DB_APP.state().config).errors") == []
    assert errors == []
    ctx.close()
