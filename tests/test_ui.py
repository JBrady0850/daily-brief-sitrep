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
TOWNS = {"results": [{"name": "Springfield", "admin1": "Illinois", "admin2": "Sangamon County", "country": "United States", "country_code": "US",
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


def fresh_feed():
    """A publisher feed with six stories from the last few hours, each with a photo."""
    now = datetime.now(timezone.utc)
    titles = ["Airlines add winter routes to sunny islands", "TSA tests faster lanes at three airports",
              "National parks extend autumn hours", "Cruise lines report record bookings",
              "Passport office clears its backlog", "Rail pass prices drop for families"]
    items = "".join(
        "<item><title>%s</title><link>https://feeds.example.com/story/%d</link>"
        "<pubDate>%s</pubDate><media:content url=\"https://img.example.com/fresh%d.jpg\" medium=\"image\"/>"
        "<description>A short summary. Second sentence.</description></item>"
        % (t, k, (now - timedelta(hours=k + 1)).strftime("%a, %d %b %Y %H:%M:%S GMT"), k) for k, t in enumerate(titles))
    return ('<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>'
            "<title>Example Travel Desk</title><link>https://feeds.example.com/</link>" + items + "</channel></rss>")


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
        if "portal.cityspark.com" in url:  # station event calendars: an empty week unless a test says otherwise
            return route.fulfill(status=200, body=json.dumps({"Success": True, "Value": []}),
                                 headers=dict(CORS, **{"content-type": "application/json", "access-control-allow-headers": "content-type"}))
        if "img.example.com" in url or "github.io" in url:
            svg = (ROOT / "app" / "img" / "sample" / "markets.svg").read_bytes()
            return route.fulfill(status=200, body=svg, headers={"content-type": "image/svg+xml"})
        if "fresh" in url:
            calls.append("feed")
            return route.fulfill(status=200, body=fresh_feed(), headers=dict(CORS, **{"content-type": "application/rss+xml"}))
        if url.startswith("http"):
            calls.append("feed")
            return route.fulfill(status=200, body=feed_bytes("rss_feed.xml"), headers=dict(CORS, **{"content-type": "application/rss+xml"}))
        return route.continue_()
    page.route("http*://**/*", handle)


@pytest.fixture(scope="module")
def http_app():
    """The app served over http, as on GitHub Pages. Chromium keeps local storage for
    file:// pages unreliably across a reload, so the reload test needs a real origin."""
    import functools
    import http.server
    import threading
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "app"))
    handler.log_message = lambda *a, **k: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d/index.html" % httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


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
        # Init scripts also run inside the brief's frame, so only the top page may seed.
        ctx.add_init_script("if (window.top === window && !localStorage.getItem('db.state.v1')) localStorage.setItem('db.state.v1', %s);" % json.dumps(json.dumps(state)))
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
    for _ in range(3):  # purpose, categories, order
        page.click("text=Next question")
    page.fill(".wxpick input", "Springfield")
    page.click("text=Find my town")
    page.click(".wxpick .chip >> text=Springfield, Illinois")
    assert "forecast for Springfield, Illinois" in page.inner_text(".wxpick")
    for _ in range(5):
        page.click("text=Next question")
    assert "Springfield, Illinois (fahrenheit)" in page.inner_text(".interview")
    page.click("button:has-text('Save and build my brief')")
    page.wait_for_selector("iframe.page", timeout=30000)
    assert "Setup complete" in page.inner_text(".welcome") and "forecast for Springfield, Illinois" in page.inner_text(".welcome")
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


def test_returning_visitor_gets_the_brief_by_itself_once_a_day(browser, http_app):
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["categories"] = [c for c in cfg["categories"] if not c.get("needs_location")]
    state = {"version": 1, "tab": "setup", "step": 7, "config": cfg, "setup_done": True, "auto_run": True}
    calls = []
    ctx, page, errors = open_page(browser, http_app, calls=calls, state=state)
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
    assert calls.count("refused") == 6, "three searches, each retried once, then the busy index is left alone"
    page.click("text=Sources and filters")
    text = page.inner_text("#briefview")
    assert "the site answered 503" in text and "skipped: the news index was busy" in text
    assert errors == []
    ctx.close()


def ready_state(**extra):
    """Saved choices from the example settings, without the local categories."""
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["categories"] = [c for c in cfg["categories"] if not c.get("needs_location")]
    st = {"version": 1, "tab": "brief", "config": cfg, "setup_done": True}
    st.update(extra)
    return st


def visible_tabs(page):
    """The tab buttons a visitor can see, in the order shown."""
    return page.evaluate("""() => [...document.querySelectorAll('#tabs button')].filter(b => !b.hidden)
        .sort((a, b) => (+a.style.order) - (+b.style.order)).map(b => b.dataset.tab)""")


def test_pasted_and_sample_briefs(browser):
    ctx, page, errors = open_page(browser, APP, state=ready_state())
    page.click('#tabs button[data-tab="brief"]')
    page.click("text=Other ways to fill the page")
    page.click("text=Show the sample brief")
    page.wait_for_selector("iframe.page")
    assert "[SAMPLE]" in page.inner_text("#briefview h2")
    assert "Showing the sample brief" in page.inner_text("#status")
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
    for tab in visible_tabs(page):
        page.click('#tabs button[data-tab="%s"]' % tab)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), tab
    ctx.close()
    ctx, page, errors2 = open_page(browser, APP, device="iPhone 13", state=ready_state(welcome="2099-01-01"))
    page.wait_for_selector(".todayhead")
    for tab in ("brief", "setup", "categories", "daily", "ai", "settings", "help"):
        page.evaluate("t => DB_APP.show(t)", tab)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), tab
    page.evaluate("DB_APP.show('setup')")
    page.click("button:has-text('Change my answers')")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "editing"
    assert errors == [] and errors2 == []
    ctx.close()


def test_desktop_app_collects_and_shows_the_page(browser):
    app = server.DesktopApp(port=0, fetcher=lambda u: feed_bytes("google_news.xml" if "google" in u else "rss_feed.xml"), pause=0)
    app.start_background()
    try:
        ctx, page, errors = open_page(browser, app.url, state=ready_state())
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
    page.click("#tabs button[data-tab=ai]")
    brief = json.loads((ROOT / "examples" / "sample-brief.json").read_text())
    brief["source"] = "ai"
    page.fill("#tab-ai textarea", json.dumps(brief))
    page.click("#tab-ai button:has-text('Show the pasted brief')")
    page.wait_for_selector("#tab-ai iframe.page")
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


def test_a_category_the_feeds_fill_needs_no_news_search(browser):
    calls = []
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["categories"] = [c for c in cfg["categories"] if c["id"] == "travel"]
    cfg["categories"][0]["feeds"] = ["https://feeds.example.com/fresh.xml"]
    cfg["categories"][0]["require"] = []
    state = {"version": 1, "tab": "brief", "config": cfg, "setup_done": True}
    ctx, page, errors = open_page(browser, APP, calls=calls, state=state)
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=30000)
    searches = [c for c in calls if c not in ("forecast", "feed")]
    assert searches == [], searches
    brief = page.evaluate("DB_APP.state().brief")
    items = brief["categories"][0]["items"]
    assert len(items) == 5 and all(i["image"].startswith("https://img.example.com/") for i in items)
    assert items[0]["summary"] == "A short summary. Second sentence."
    assert errors == []
    ctx.close()


def test_setup_is_its_own_mode_until_saved_then_the_app_opens_on_the_brief(browser, http_app):
    calls = []
    ctx, page, errors = open_page(browser, http_app, calls=calls)
    page.wait_for_selector(".hero")
    # Before saving: only the interview and the pages that need no setup.
    assert visible_tabs(page) == ["setup", "ai", "settings", "help"]
    page.evaluate("DB_APP.show('brief')")
    assert page.evaluate("DB_APP.state().tab") == "setup", "no brief page before setup is saved"
    assert "nothing is collected until you save" in page.inner_text("#modebar")
    with ctx.expect_page() as pop:
        page.click("button:has-text('See a sample brief')")
    sample = pop.value
    sample.wait_for_load_state()
    assert "Friday, October 23, 2026" in sample.inner_text("h1.ttl")
    sample.close()
    page.click(".stepper button[aria-label^='Question 9']")
    assert page.locator(".stepbar").count() == 0 and page.locator("text=Next: Categories").count() == 0
    assert calls == [], "nothing is collected during setup"
    # Saving: a confirmation, a panel that names each stage, then the brief.
    page.evaluate("""() => { window.__stages = []; new MutationObserver(() => {
        const now = document.querySelector('ol.stages li.now b');
        if (now && window.__stages[window.__stages.length - 1] !== now.textContent) window.__stages.push(now.textContent);
      }).observe(document.body, { subtree: true, childList: true }); }""")
    page.click("button:has-text('Save and build my brief')")
    page.wait_for_selector("iframe.page", timeout=30000)
    stages = page.evaluate("window.__stages")
    assert stages[:1] == ["Publisher feeds"] and "News search" in stages and stages[-1] == "Your page", stages
    assert "Setup complete" in page.inner_text(".welcome")
    assert page.inner_text("#status").startswith("Ready, built today at")
    assert visible_tabs(page) == ["brief", "setup", "daily", "ai", "settings", "help"]
    assert page.inner_text('#tabs button[data-tab="setup"]') == "Your choices"
    assert page.inner_text('#tabs button[data-tab="brief"]') == "Today's brief"
    state = page.evaluate("DB_APP.state()")
    assert state["setup_done"] and state["setup_saved"] and state["brief_sig"]
    # From now on the app opens on the brief, and setup shows the saved choices.
    page.reload()
    page.wait_for_selector("iframe.page")
    assert page.evaluate("DB_APP.state().tab") == "brief"
    page.click('#tabs button[data-tab="setup"]')
    assert page.inner_text("#tab-setup h1") == "Your choices" and "Question 9" not in page.inner_text("#tab-setup")
    assert "Saved" in page.inner_text("#tab-setup .pill")
    assert errors == []
    ctx.close()


def test_changes_to_saved_choices_apply_only_on_save(browser, http_app):
    ctx, page, errors = open_page(browser, http_app, state=ready_state())
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=30000)
    saved_before = page.evaluate("JSON.stringify(DB_APP.state().config)")
    nfl = "c => c.categories.some(x => x.id === 'nfl')"
    page.click('#tabs button[data-tab="setup"]')
    page.click("button[aria-label='Change: Categories']")
    assert page.inner_text("#tab-setup h1") == "Change your choices"
    page.click("label[for=lib-nfl]")
    assert page.evaluate("(%s)(DB_APP.state().draft)" % nfl)
    assert page.evaluate("JSON.stringify(DB_APP.state().config)") == saved_before, "saved choices untouched while changing"
    # Elsewhere in the app the saved choices stay in use, with a reminder.
    page.click('#tabs button[data-tab="brief"]')
    assert "unsaved changes to your choices" in page.inner_text("#modebar")
    assert page.locator(".notice").count() == 0
    # Unsaved changes survive a reload.
    page.reload()
    page.wait_for_selector("#modebar.edit")
    page.click("#modebar button:has-text('Continue changing')")
    assert page.evaluate("(%s)(DB_APP.state().draft)" % nfl)
    page.click(".edithead button:has-text('Cancel changes')")
    assert page.evaluate("DB_APP.state().draft") is None
    assert page.evaluate("JSON.stringify(DB_APP.state().config)") == saved_before
    assert page.inner_text("#tab-setup h1") == "Your choices"
    # Saving applies them, and today's brief offers a rebuild.
    page.click("button[aria-label='Change: Categories']")
    page.click("label[for=lib-nfl]")
    page.click(".stepper button[aria-label^='Question 9']")
    page.click("button:has-text('Save changes')")
    assert page.evaluate("DB_APP.state().tab") == "brief"
    assert page.evaluate("(%s)(DB_APP.state().config)" % nfl)
    assert "Your choices changed after this brief was built" in page.inner_text(".notice")
    page.click("button:has-text('Rebuild with my new choices')")
    page.wait_for_function("DB_APP.state().brief.categories.some(c => c.id === 'nfl')", timeout=30000)
    page.wait_for_selector("#status.good")
    assert page.locator(".notice").count() == 0
    assert errors == []
    ctx.close()


def test_choosing_categories_keeps_your_place(browser):
    ctx, page, errors = open_page(browser, APP)
    page.wait_for_selector(".interview")
    page.click("button:has-text('Next question')")
    page.evaluate("document.querySelector('details[data-key=group-life]').open = true")
    tile = page.locator("label[for=lib-pets]")
    tile.scroll_into_view_if_needed()
    y = page.evaluate("window.scrollY")
    assert y > 600
    tile.click()
    assert page.evaluate("window.scrollY") == y, "ticking a category must not jump to the top"
    assert page.locator(".ctile.on >> text=Pets and Animals").count() == 1
    assert page.evaluate("document.activeElement.id") == "lib-pets"
    assert "chosen" in page.inner_text("details[data-key=group-life] .gcount")
    assert "(8 of 15 chosen)" in page.inner_text(".interview")
    tile.click()
    assert page.evaluate("window.scrollY") == y
    assert page.locator(".ctile.on >> text=Pets and Animals").count() == 0
    assert "(7 of 15 chosen)" in page.inner_text(".interview")
    # A group with nothing chosen stays open after a tick and an untick.
    page.evaluate("document.querySelector('details[data-key=group-culture]').open = true")
    game = page.locator("label[for=lib-gaming]")
    game.scroll_into_view_if_needed()
    game.click()
    game.click()
    assert page.evaluate("document.querySelector('details[data-key=group-culture]').open"), "the group stays open when emptied"
    assert "to choose from" in page.inner_text("details[data-key=group-culture] .gcount")
    # A typed topic and a pack redraw the page in place: same spot, same open groups.
    box = page.locator("#topic")
    box.scroll_into_view_if_needed()
    y = page.evaluate("window.scrollY")
    box.fill("beekeeping")
    box.press("Enter")
    assert abs(page.evaluate("window.scrollY") - y) <= 2
    assert page.evaluate("document.activeElement.id") == "topic"
    page.locator(".pack >> nth=1").click()
    assert page.evaluate("document.querySelector('details[data-key=group-life]').open")
    assert errors == []
    ctx.close()


def test_on_topic_feeds_fill_a_category_in_the_browser(browser):
    calls = []
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["categories"] = [c for c in cfg["categories"] if c["id"] == "travel"]
    cfg["categories"][0]["feeds"] = []
    cfg["categories"][0]["topic_feeds"] = ["https://feeds.example.com/fresh.xml"]
    cfg["categories"][0]["require"] = [["zzzz-no-story-says-this"]]
    state = {"version": 1, "tab": "brief", "config": cfg, "setup_done": True}
    ctx, page, errors = open_page(browser, APP, calls=calls, state=state)
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=30000)
    brief = page.evaluate("DB_APP.state().brief")
    assert len(brief["categories"][0]["items"]) == 5
    assert all("on_topic" not in i for i in brief["categories"][0]["items"])
    assert [c for c in calls if c not in ("forecast", "feed")] == [], "a full category needs no news search"
    assert page.evaluate("DB_APP.state().health.travel.feeds[0].on_topic") is True
    assert errors == []
    ctx.close()


def backup_file(ids, n=6):
    now = datetime.now(timezone.utc)
    cats = {}
    for cid in ids:
        cats[cid] = [{"title": "Backup story %d for %s" % (k, cid), "url": "https://backup.example.com/%s/%d" % (cid, k),
                      "source": "Example Wire", "source_url": "https://backup.example.com", "summary": "",
                      "published": (now - timedelta(hours=k + 1)).strftime("%Y-%m-%dT%H:%M:%SZ"), "image": "", "on_topic": True}
                     for k in range(n)]
    return {"schema": "daily-brief-news-cache/1", "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "categories": cats}


def test_the_backup_collection_fills_categories_when_the_news_index_refuses(browser, http_app):
    calls = []
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    pick = {c["id"]: c for c in lib["categories"]}
    cats = [dict(pick["defense-ai"], feeds=[], topic_feeds=[]), dict(pick["pets"], feeds=[], topic_feeds=[])]
    state = {"version": 1, "tab": "brief", "config": {"version": 1, "categories": cats}, "setup_done": True}
    ctx, page, errors = open_page(browser, http_app, calls=calls, gdelt_status=429, state=state)
    asked = []
    page.route("**/data/news-cache.json", lambda r: (asked.append(1), r.fulfill(status=200, body=json.dumps(backup_file(["defense-ai"])),
                                                                          headers={"content-type": "application/json"})))
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    brief = page.evaluate("DB_APP.state().brief")
    by = {c["id"]: c for c in brief["categories"]}
    assert len(by["defense-ai"]["items"]) == 5 and by["defense-ai"]["items"][0]["title"].startswith("Backup story")
    assert by["pets"]["items"] == [], "not in the backup collection, and the news index refused"
    assert asked == [1], "the backup file is read once"
    health = page.evaluate("DB_APP.state().health")
    assert health["defense-ai"]["backup"]["added"] == 6 and health["pets"]["backup"]["items"] == 0
    assert all("defense" not in c for c in calls if c not in ("feed", "forecast", "refused")), "a full category is never searched"
    assert "refused" in calls, "the short category still tried the news index"
    assert by["pets"].get("unchecked") is True, "not in the backup collection and the search failed: not checked"
    page.click("#briefview summary:has-text('Sources and filters')")
    assert "6 from the backup collection" in page.inner_text("#briefview")
    assert errors == []
    ctx.close()
    # The backup collection searched the category on GitHub and has nothing new for it:
    # the desk was checked, so it says "No new items", not "Not checked today".
    covered = backup_file(["defense-ai"])
    covered["categories"]["pets"] = []
    ctx, page, errors = open_page(browser, http_app, calls=[], gdelt_status=429, state=state)
    page.route("**/data/news-cache.json", lambda r: r.fulfill(status=200, body=json.dumps(covered), headers={"content-type": "application/json"}))
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    by = {c["id"]: c for c in page.evaluate("DB_APP.state().brief.categories")}
    assert by["pets"]["items"] == [] and not by["pets"].get("unchecked")
    text = page.frame_locator("iframe.page").locator("main").inner_text()
    assert "Not checked today" not in text and "No new items" in text
    assert errors == []
    ctx.close()


def local_feed():
    now = datetime.now(timezone.utc)
    titles = ["Springfield council approves new park", "Sangamon County fair opens Friday", "State budget talks continue"]
    items = "".join("<item><title>%s</title><link>https://tv.example.com/story/%d</link><pubDate>%s</pubDate></item>"
                    % (t, k, (now - timedelta(hours=k + 1)).strftime("%a, %d %b %Y %H:%M:%S GMT")) for k, t in enumerate(titles))
    return '<?xml version="1.0"?><rss version="2.0"><channel><title>Example TV</title>' + items + "</channel></rss>"


def test_town_question_fills_the_state_and_county_and_checks_a_local_feed(browser):
    ctx, page, errors = open_page(browser, APP)
    page.route("**/local-news.xml", lambda r: r.fulfill(status=200, body=local_feed(), headers=dict(CORS, **{"content-type": "application/rss+xml"})))
    for _ in range(3):  # purpose, categories, order
        page.click("button:has-text('Next question')")
    page.fill("#town", "Springfield")
    page.fill(".wxpick input[aria-label='Town for the forecast']", "Springfield")
    page.click("text=Find my town")
    page.click(".wxpick .chip >> text=Springfield, Illinois")
    r = page.evaluate("DB_APP.state().config.reader")
    assert r["region"] == "Illinois" and "Sangamon County" in r["local_terms"]
    assert page.input_value("#region") == "Illinois"
    page.fill("#localfeeds", "https://tv.example.com/local-news.xml")
    page.click(".localfeeds button:has-text('Check')")
    page.wait_for_selector(".localfeeds li")
    assert "readable, 3 stories, 2 name your town or a nearby place" in page.inner_text(".localfeeds")
    assert page.evaluate("DB_APP.state().config.reader.local_feeds") == ["https://tv.example.com/local-news.xml"]
    assert errors == []
    ctx.close()


def test_town_categories_use_your_local_feed_and_say_when_they_could_not_be_checked(browser, http_app):
    calls = []
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    pick = {c["id"]: c for c in lib["categories"]}
    reader = {"location": "Springfield", "region": "Illinois", "local_terms": ["Sangamon County"],
              "local_feeds": ["https://tv.example.com/local-news.xml"]}
    state = {"version": 1, "tab": "brief", "setup_done": True,
             "config": {"version": 1, "reader": reader, "categories": [pick["local-news"], pick["local-events"]]}}
    ctx, page, errors = open_page(browser, http_app, calls=calls, gdelt_status=429, state=state)
    page.route("**/local-news.xml", lambda r: r.fulfill(status=200, body=local_feed(), headers=dict(CORS, **{"content-type": "application/rss+xml"})))
    page.route("**/data/local/*.json", lambda r: r.fulfill(status=404, body="not found"))  # no state file on this site
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    by = {c["id"]: c for c in page.evaluate("DB_APP.state().brief.categories")}
    assert [i["title"] for i in by["local-news"]["items"]] == ["Springfield council approves new park", "Sangamon County fair opens Friday"]
    events = by["local-events"]
    assert events["items"] == [] or all("fair" in i["title"].lower() or "opens" in i["title"].lower() for i in events["items"])
    ctx.close()
    # Without a local feed, a refused search leaves the desk unchecked, and the page says so.
    reader2 = dict(reader, local_feeds=[])
    state2 = dict(state, config={"version": 1, "reader": reader2, "categories": [pick["local-news"]]})
    ctx, page, errors2 = open_page(browser, http_app, calls=[], gdelt_status=429, state=state2)
    page.route("**/data/local/*.json", lambda r: r.fulfill(status=404, body="not found"))
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    assert page.evaluate("DB_APP.state().brief.categories[0].unchecked") is True
    frame = page.frame_locator("iframe.page")
    assert "Not checked today" in frame.locator("main").inner_text()
    assert errors == [] and errors2 == []
    ctx.close()



def local_state_file(code="IL"):
    now = datetime.now(timezone.utc)
    rows = [("Springfield council approves budget for new park", "WONE"), ("Sangamon County fair opens Friday", "WTWO"),
            ("Chicago transit adds late trains", "WONE"), ("Springfield man arrested after chase", "WTWO")]
    stories = [{"title": t, "url": "https://station.example.com/%d" % k, "source": src, "source_url": "https://station.example.com",
                "published": (now - timedelta(hours=k + 1)).strftime("%Y-%m-%dT%H:%M:%SZ"), "summary": "", "image": "", "station": src.lower()}
               for k, (t, src) in enumerate(rows)]
    return {"schema": "daily-brief-local-news/1", "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "state": code,
            "stations": [{"id": "wone", "name": "WONE", "site": "https://station.example.com", "answered": True}], "stories": stories}


def test_town_categories_read_the_local_stations_of_your_state(browser, http_app):
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    pick = {c["id"]: c for c in lib["categories"]}
    reader = {"location": "Springfield", "region": "Illinois", "local_terms": ["Sangamon County"]}
    state = {"version": 1, "tab": "brief", "setup_done": True,
             "config": {"version": 1, "reader": reader, "categories": [pick["local-government"], pick["local-news"]]}}
    ctx, page, errors = open_page(browser, http_app, calls=[], gdelt_status=429, state=state)
    asked = []
    page.route("**/data/local/*.json", lambda r: (asked.append(r.request.url.rsplit("/", 1)[1]),
                                                  r.fulfill(status=200, body=json.dumps(local_state_file()), headers={"content-type": "application/json"})))
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    by = {c["id"]: c for c in page.evaluate("DB_APP.state().brief.categories")}
    assert asked == ["IL.json"], "one read, of the reader's own state"
    assert [i["title"] for i in by["local-government"]["items"]] == ["Springfield council approves budget for new park"]
    assert [i["title"] for i in by["local-news"]["items"]] == ["Sangamon County fair opens Friday"]
    every = [i["title"] for c in by.values() for i in c["items"]]
    assert not any("Chicago" in t for t in every), "stories that do not name the area stay out"
    assert not any("arrested" in t for t in every), "crime stays out of the town desks"
    health = page.evaluate("DB_APP.state().health")
    assert health["local-news"]["local"]["state"] == "IL" and health["local-news"]["local"]["items"] == 3
    assert not any(c.get("unchecked") for c in by.values()), "the local stations answered, so the desks were checked"
    page.click("#briefview summary:has-text('Sources and filters')")
    assert "3 from local stations naming your area" in page.inner_text("#briefview")
    assert errors == []
    ctx.close()
    # Outside the US there is no state file to read.
    state2 = dict(state, config=dict(state["config"], reader=dict(reader, region="Ontario")))
    ctx, page, errors = open_page(browser, http_app, calls=[], gdelt_status=429, state=state2)
    asked.clear()
    page.route("**/data/local/*.json", lambda r: (asked.append(1), r.fulfill(status=404, body="")))
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    assert asked == [] and errors == []
    ctx.close()


def calendar_week():
    """A CitySpark answer for the next three days, made from invented events."""
    day = datetime.now(timezone.utc).date() + timedelta(days=1)
    rows = [[(101, "Harvest Night Market", 18, "Town Square", "https://events.example.com/market"),
             (102, "Library Story Time", 10, "Main Library", "https://www.facebook.com/events/1")],
            [(201, "Community Choir Rehearsal", 19, "Grace Hall", "https://choir.example.com")],
            [(301, "Pumpkin Walk", None, "Riverside Park", "https://walk.example.com")]]
    value = []
    for k, evs in enumerate(rows):
        d = day + timedelta(days=k)
        out = []
        for pid, name, hour, venue, url in evs:
            local = "%sT%02d:00:00Z" % (d.isoformat(), hour or 0)
            utc = None if hour is None else "%sT%02d:00:00Z" % (d.isoformat(), (hour + 5) % 24)
            out.append({"PId": pid, "Name": name, "DateStart": local, "StartUTC": utc, "AllDay": hour is None, "HasTime": hour is not None,
                        "Venue": venue, "CityState": "Example City, FL", "Summary": name + " for all ages.", "PrimaryUrl": url,
                        "LargeImg": "", "MediumImg": ""})
        value.append({"Date": d.isoformat(), "TotalCount": len(out), "Events": out})
    return {"Success": True, "Value": value}


def test_things_to_do_lists_the_week_from_the_nearest_station_calendar(browser, http_app):
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    pick = {c["id"]: c for c in lib["categories"]}
    cfg = {"version": 1, "reader": {"location": "Example City", "region": "Florida", "local_terms": []},
           "categories": [pick["local-events"]], "delivery": {"time": "06:15", "timezone": "America/Chicago", "channels": ["issue"]},
           "weather": {"enabled": False, "place": "Example City, Florida", "latitude": 30.25, "longitude": -85.65, "units": "fahrenheit"}}
    state = {"version": 1, "tab": "brief", "setup_done": True, "config": cfg}
    ctx, page, errors = open_page(browser, http_app, calls=[], gdelt_status=429, state=state)
    page.route("**/data/calendars.js", lambda r: r.fulfill(status=200, body=(ROOT / "tests" / "fixtures" / "calendars.js").read_text(),
                                                           headers={"content-type": "text/javascript"}))
    page.reload()
    asked = []
    week = calendar_week()

    def calendar(route):
        req = route.request
        if req.method == "OPTIONS":
            return route.fulfill(status=204, headers=dict(CORS, **{"access-control-allow-headers": "content-type", "access-control-allow-methods": "POST"}))
        asked.append((req.method, req.url.rsplit("/", 1)[1], json.loads(req.post_data)))
        return route.fulfill(status=200, body=json.dumps(week), headers=dict(CORS, **{"content-type": "application/json"}))
    page.route("https://portal.cityspark.com/**", calendar)
    page.route("**/data/local/*.json", lambda r: r.fulfill(status=404, body=""))
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    assert len(asked) == 1 and asked[0][:2] == ("POST", "ExampleTV"), "one question, to the nearest calendar only"
    body = asked[0][2]
    assert (body["lat"], body["lng"], body["distance"], body["daysToLoad"]) == (30.25, -85.65, 20, 7)
    assert "Example City" not in json.dumps(body), "only the rounded map position leaves the browser"
    items = page.evaluate("DB_APP.state().brief.categories[0].items")
    assert [i["title"] for i in items] == ["Harvest Night Market", "Community Choir Rehearsal", "Pumpkin Walk", "Library Story Time"]
    assert items[0]["url"] == "https://events.example.com/market", "the organizer's page"
    assert items[3]["url"].startswith("https://www.example.com/events/#/details/library-story-time/102/"), "a social-only event opens on the calendar"
    assert items[2]["event"]["all_day"] is True and items[0]["source"] == "WEXA community calendar"
    health = page.evaluate("DB_APP.state().health")["local-events"]
    assert health["events"]["calendars"] == ["WEXA"] and health["events"]["error"] == ""
    frame = page.frame_locator("iframe.page")
    assert frame.locator("ul.items span.pill.ev").count() == 4
    assert "Town Square, Example City, FL" in frame.locator("main").inner_text()
    assert "powered by CitySpark" in frame.locator("footer").inner_text()
    page.click("#briefview summary:has-text('Sources and filters')")
    assert "4 events from WEXA calendars" in page.inner_text("#briefview")
    assert errors == []
    ctx.close()


def test_a_slow_news_index_cannot_hold_the_brief(browser, http_app):
    """Past the search budget, the remaining searches are skipped and the brief goes out."""
    calls = []
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    pick = {c["id"]: c for c in lib["categories"]}
    state = {"version": 1, "tab": "brief", "setup_done": True,
             "config": {"version": 1, "categories": [dict(pick["defense-ai"], feeds=[], topic_feeds=[])]}}
    p, b = browser
    ctx = b.new_context(viewport={"width": 1100, "height": 900})
    ctx.add_init_script("window.DB_COLLECT_GAP = 0; window.DB_COLLECT_SEARCH_BUDGET = 0;")
    ctx.add_init_script("if (window.top === window && !localStorage.getItem('db.state.v1')) localStorage.setItem('db.state.v1', %s);"
                        % json.dumps(json.dumps(state)))
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    route_world(page, calls)
    page.route("**/data/news-cache.json", lambda r: r.fulfill(status=404, body=""))
    page.goto(http_app)
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    qs = page.evaluate("DB_APP.state().health['defense-ai'].queries")
    assert qs and all(q["error"].startswith("skipped: the news index was slow") for q in qs), qs
    assert not [c for c in calls if c not in ("feed", "forecast")], "no search was sent"
    assert page.evaluate("DB_APP.state().brief.categories[0].unchecked") is True
    assert errors == []
    ctx.close()


def test_a_tab_left_open_across_a_release_reloads_once_and_then_builds(browser, http_app):
    """The site serves a newer version than the page loaded: the brief button reloads the
    page once for it, and the brief is built after the reload. No reload loop."""
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    pick = {c["id"]: c for c in lib["categories"]}
    state = {"version": 1, "tab": "brief", "setup_done": True,
             "config": {"version": 1, "categories": [dict(pick["defense-ai"], feeds=[], topic_feeds=[])]}}
    p, b = browser
    ctx = b.new_context(viewport={"width": 1100, "height": 900})
    ctx.add_init_script("window.DB_COLLECT_GAP = 0; window.DB_VERSION_CHECK = true;")
    ctx.add_init_script("if (window.top === window && !localStorage.getItem('db.state.v1')) localStorage.setItem('db.state.v1', %s);"
                        % json.dumps(json.dumps(state)))
    page = ctx.new_page()
    errors, loads = [], []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("load", lambda: loads.append(1))
    route_world(page, [])
    page.route("**/sw.js", lambda r: r.fulfill(status=200, body='const VERSION = "db-v9.9.9";', headers={"content-type": "text/javascript"}))
    page.route("**/data/news-cache.json", lambda r: r.fulfill(status=404, body=""))
    page.goto(http_app)
    page.wait_for_selector("button:has-text(\"Get today's brief\")")
    page.click("button:has-text(\"Get today's brief\")")
    page.wait_for_selector("iframe.page", timeout=60000)
    assert len(loads) == 2, "one reload for the new version"
    assert page.evaluate("sessionStorage.getItem('db.reloaded_for')") == "9.9.9"
    assert page.evaluate("DB_APP.state().brief.categories[0].id") == "defense-ai", "the brief was built after the reload"
    assert page.evaluate("DB_APP.state().brief_version") == page.evaluate("DB_ENGINE.VERSION")
    # Still older than the site after the reload: the next brief does not reload again.
    page.click("button:has-text('Check for newer stories')")
    page.wait_for_function("!document.querySelector('#status.busy')", timeout=60000)
    assert len(loads) == 2
    assert errors == []
    ctx.close()


def test_choices_saved_before_email_was_removed_review_without_a_warning(browser):
    """Settings from version 0.1.0 list email as a delivery channel; the review shows no
    email warning, and the saved choices lose the retired channel."""
    state = {"version": 1, "tab": "setup", "step": 8, "setup_done": False,
             "config": {"version": 1, "delivery": {"time": "06:15", "timezone": "America/Chicago", "channels": ["issue", "email"]},
                        "email": {"to": ["someone@example.com"]},
                        "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'], "require": [["zero trust"]]}]}}
    ctx, page, errors = open_page(browser, APP, state=state)
    page.wait_for_selector("text=Review and save")
    text = page.inner_text("main") if page.query_selector("main") else page.inner_text("body")
    assert "email" not in text.lower(), "no warning about the retired email channel"
    assert page.evaluate("DB_APP.state().config.delivery.channels") == ["issue"]
    assert "email" not in page.evaluate("Object.keys(DB_APP.state().config)")
    assert errors == []
    ctx.close()


def test_put_the_categories_in_order(browser):
    """The third question lists the chosen categories with up, down and to-the-top
    buttons; the order is saved, the page stays put and the focus stays on the moved row."""
    ctx, page, errors = open_page(browser, APP)
    page.wait_for_selector(".hero")
    page.click("button:has-text('Next question')")
    page.click("button:has-text('Next question')")
    assert page.inner_text(".interview h2") == "Put them in order"
    ids = page.evaluate("DB_APP.state().config.categories.map(c => c.id)")
    assert len(ids) >= 4 and page.locator("ol.order li").count() == len(ids)
    last = ids[-1]
    assert page.is_disabled("#up-o-" + ids[0]) and page.is_disabled("#down-o-" + last)
    page.locator("#top-o-" + last).scroll_into_view_if_needed()
    y = page.evaluate("window.scrollY")
    page.click("#top-o-" + last)
    assert page.evaluate("DB_APP.state().config.categories.map(c => c.id)") == [last] + ids[:-1]
    assert page.evaluate("document.activeElement.id") == "down-o-" + last, "at the top, the focus moves to the button that still works"
    assert abs(page.evaluate("window.scrollY") - y) < 5, "the page stays where it was"
    assert "is now number 1 of %d" % len(ids) in page.inner_text("#orderstatus")
    page.keyboard.press("Enter")  # the focused Down button moves it back down one place
    assert page.evaluate("DB_APP.state().config.categories.map(c => c.id)")[:2] == [ids[0], last]
    assert page.evaluate("document.activeElement.id") == "down-o-" + last
    assert page.inner_text("ol.order li >> nth=1").split("\n")[0].strip() == "2"
    # The saved order survives a reload and shows on the review.
    page.reload()
    page.wait_for_selector("ol.order")
    assert page.evaluate("DB_APP.state().config.categories.map(c => c.id)")[:2] == [ids[0], last]
    page.click(".stepper button[aria-label^='Question 9']")
    rows = page.inner_text("table.summary")
    assert "Order" in rows and "most important first" in rows
    assert errors == []
    ctx.close()


def test_the_brief_says_when_it_was_built(browser):
    """An earlier brief on screen says when it was built, in the reader's time zone, on the
    status line, above the page and inside the page."""
    from dailybrief.jsdata import load_js_json
    sample = load_js_json(ROOT / "app" / "data" / "sample.js", "DB_SAMPLE")
    brief = dict(sample["brief"], source="web", date="2026-10-23", generated_at="2026-10-23T11:16:00Z")
    cfg = dict(sample["settings"], delivery={"time": "06:15", "timezone": "America/Chicago", "channels": ["issue"]})
    state = {"version": 1, "tab": "brief", "setup_done": True, "config": cfg, "brief": brief, "health": None}
    ctx, page, errors = open_page(browser, APP, state=state)
    page.wait_for_selector("#status")
    when = "Friday, October 23, 2026 at 6:16 AM CDT"
    assert page.inner_text("#status") == "Not built yet today. The page below was built " + when + "."
    assert ("Built " + when + ".") in page.inner_text("#builtline")
    frame = page.frame_locator("iframe.page")
    assert frame.locator("p.built").inner_text() == "Built " + when
    assert errors == []
    ctx.close()


def test_countdown_question_suggests_ideas_from_the_categories(browser, http_app):
    """The countdown question offers ideas from the chosen categories: a fixed date fills in
    at once, a personal one after its date is picked, and Undo puts the old countdown back."""
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    pick = {c["id"]: c for c in lib["categories"]}
    state = {"version": 1, "config": {"version": 1, "reader": {"location": "Springfield", "region": "Illinois"},
                                      "categories": [pick["federal-retirement"], pick["politics"], pick["travel"]],
                                      "countdown": {"enabled": True, "label": "Days to the reunion", "date": "2099-07-04", "start": "",
                                                    "milestones": []}}}
    ctx, page, errors = open_page(browser, http_app, state=state)
    page.wait_for_selector(".stepper")
    page.click(".stepper button[aria-label*='countdown']")
    page.wait_for_selector("#ideas")
    names = page.locator("#ideas .idea b").all_inner_texts()
    expect = page.evaluate("DB_IDEAS.ideasFor(DB_APP.state().config.categories, (d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'))(new Date()))")
    assert names == [i["label"] for i in expect] and [i["id"] for i in expect] == ["federal-retirement", "medicare", "election", "trip"]
    assert "From Federal Retirement" in page.inner_text("#ideas .idea >> nth=0"), "each idea names the category it came from"
    election = [i for i in expect if i["id"] == "election"][0]
    page.click("#idea-election")
    cd = page.evaluate("DB_APP.state().config.countdown")
    assert (cd["enabled"], cd["label"], cd["date"]) == (True, "Days to Election Day", election["date"])
    assert "Filled in: Days to Election Day" in page.inner_text("#ideastatus")
    assert page.evaluate("document.activeElement.id") == "ideaundo"
    page.keyboard.press("Enter")  # Undo
    cd = page.evaluate("DB_APP.state().config.countdown")
    assert (cd["label"], cd["date"]) == ("Days to the reunion", "2099-07-04"), "Undo puts the old countdown back"
    assert "Put back" in page.inner_text("#ideastatus")
    # A personal idea asks for its date first.
    page.click("#idea-federal-retirement")
    assert "Pick a date after today" in page.inner_text("#ideastatus")
    target = (datetime.now() + timedelta(days=300)).strftime("%Y-%m-%d")
    page.fill("#ideadate-federal-retirement", target)
    page.click("#idea-federal-retirement")
    cd = page.evaluate("DB_APP.state().config.countdown")
    assert (cd["label"], cd["date"]) == ("Days to retirement", target)
    assert [m["label"] for m in cd["milestones"]][-1] == "Check final leave and the last paycheck"
    assert all(m["date"] < target for m in cd["milestones"]) and len(cd["milestones"]) == 4, cd["milestones"]
    assert page.locator(".milestones .mrow").count() == 4, "the milestones show in the fields below, ready to change"
    assert page.evaluate("DB_ENGINE.validateConfig(DB_APP.state().config).errors") == []
    assert errors == []
    ctx.close()
