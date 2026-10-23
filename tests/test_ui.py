"""Browser tests of the app: the web version opened from disk, and the desktop
app with recorded feeds. Needs Playwright with Chromium (see CONTRIBUTING.md)."""
import json
import os

import pytest
from conftest import ROOT, feed_bytes

from dailybrief import server

sync_api = pytest.importorskip("playwright.sync_api")


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


def open_page(browser, url, device=None):
    p, b = browser
    ctx = b.new_context(**(p.devices[device] if device else {"viewport": {"width": 1100, "height": 900}}))
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("dialog", lambda d: d.accept())
    page.goto(url)
    return ctx, page, errors


def test_web_version_interview_to_newsletter(browser):
    ctx, page, errors = open_page(browser, (ROOT / "app" / "index.html").as_uri())
    page.wait_for_selector(".interview")
    for _ in range(7):
        page.click("text=Next question")
    page.click("text=Save and get my brief")
    page.click("text=Show the sample brief")
    page.wait_for_selector("iframe.preview")
    assert "[SAMPLE]" in page.inner_text("#briefview h2")
    frame = page.frame_locator("iframe.preview")
    assert "Friday, October 23, 2026" in frame.locator("div.ttl").inner_text()
    brief = json.loads((ROOT / "examples" / "sample-brief.json").read_text())
    brief["source"] = "ai"
    page.fill("#tab-brief textarea", "Here it is:\n```json\n" + json.dumps(brief) + "\n```")
    page.click("text=Show the newsletter")
    page.wait_for_function("document.querySelector('#briefview h2').textContent.indexOf('[SAMPLE]') < 0")
    page.click("text=Mark as read")
    page.fill("#tab-brief textarea", json.dumps(brief))
    page.click("text=Show the newsletter")
    page.wait_for_function("document.querySelector('#briefview .hint').textContent.indexOf('0 stories') === 0")
    assert errors == []
    ctx.close()


def test_custom_category_and_ai_prompt(browser):
    ctx, page, errors = open_page(browser, (ROOT / "app" / "index.html").as_uri())
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


def test_phone_layout_never_scrolls_sideways(browser):
    ctx, page, errors = open_page(browser, (ROOT / "app" / "index.html").as_uri(), device="iPhone 13")
    page.wait_for_selector(".interview")
    for tab in ("setup", "categories", "brief", "email", "ai", "settings", "help"):
        page.click('#tabs button[data-tab="%s"]' % tab)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), tab
    assert errors == []
    ctx.close()


def test_desktop_app_collects_previews_and_guards_email(browser):
    app = server.DesktopApp(port=0, fetcher=lambda u: feed_bytes("google_news.xml" if "google" in u else "rss_feed.xml"), pause=0)
    app.start_background()
    try:
        ctx, page, errors = open_page(browser, app.url)
        page.wait_for_selector(".modebar.on")
        page.click('#tabs button[data-tab="brief"]')
        page.click("text=Get today's brief")
        page.wait_for_selector("iframe.preview", timeout=20000)
        assert page.locator("text=Email it now").is_disabled()
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
    page.goto((ROOT / "app" / "index.html").as_uri())
    page.wait_for_selector(".interview")
    cfg = json.loads((ROOT / "examples" / "sample-settings.json").read_text())
    cfg["brief"]["summary_max_chars"] = "<img src=x onerror=\"document.title='owned'\">"
    backup = tmp_path / "backup.json"
    backup.write_text(json.dumps({"db_backup": 1, "version": "0.1.0", "state": {"version": 1, "config": cfg}, "history": None}))
    page.click("#tabs button[data-tab=settings]")
    page.set_input_files("#tab-settings input[type=file]", str(backup))
    page.wait_for_timeout(300)
    assert any("problems" in m for m in messages), messages
    # Even if bad settings got in, the newsletter escapes them, and the copy
    # fallback (no rich clipboard) copies text only: the page title never changes.
    page.evaluate("p => { DB_APP.state().config.brief.summary_max_chars = p; }", cfg["brief"]["summary_max_chars"])
    page.evaluate("window.ClipboardItem = undefined")
    page.click("#tabs button[data-tab=brief]")
    brief = json.loads((ROOT / "examples" / "sample-brief.json").read_text())
    brief["source"] = "ai"
    page.fill("#tab-brief textarea", json.dumps(brief))
    page.click("text=Show the newsletter")
    page.wait_for_selector("iframe.preview")
    page.click("text=Copy for email")
    page.wait_for_timeout(300)
    assert page.title() != "owned" and errors == []
    ctx.close()


def test_type_a_topic_with_suggestions(browser):
    ctx, page, errors = open_page(browser, (ROOT / "app" / "index.html").as_uri())
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
