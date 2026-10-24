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
    page.click("text=Next question")
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
    page.click(".stepper button[aria-label^='Question 8']")
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
    assert page.inner_text("#status").startswith("Ready, built at")
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
    assert page.inner_text("#tab-setup h1") == "Your choices" and "Question 8" not in page.inner_text("#tab-setup")
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
    page.click(".stepper button[aria-label^='Question 8']")
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
