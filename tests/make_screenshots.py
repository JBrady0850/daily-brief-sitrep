"""Regenerates the screenshots in docs/images with Playwright and Chromium.

    python tests/make_screenshots.py

Every outside request is answered from recorded, invented data (the same fake
news index and forecast the browser tests use), so no real news or personal
data ever appears in the pictures.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from playwright.sync_api import sync_playwright  # noqa: E402

from dailybrief import render  # noqa: E402
import test_ui as T  # noqa: E402

OUT = ROOT / "docs" / "images"


def eager(page):
    """Loads every lazy photo so a full-page picture shows them."""
    page.evaluate("document.querySelectorAll('img').forEach(i => { i.loading = 'eager'; i.src = i.src; })")
    page.wait_for_timeout(600)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    brief = json.loads((ROOT / "examples" / "sample-brief.json").read_text(encoding="utf-8"))
    settings = json.loads((ROOT / "examples" / "sample-settings.json").read_text(encoding="utf-8"))
    page_html = ROOT / "output" / "sample-brief-page.html"
    page_html.parent.mkdir(exist_ok=True)
    page_html.write_text(render.render(brief, settings)["html"], encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx, page, _ = T.open_page((p, b), T.APP)
        page.set_viewport_size({"width": 1200, "height": 860})
        page.wait_for_selector(".hero")
        page.screenshot(path=str(OUT / "01-setup.png"))
        page.click("button:has-text('Next question')")
        page.screenshot(path=str(OUT / "02-pick-categories.png"), full_page=False)
        page.locator("details.group >> nth=2").scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "03-category-tiles.png"))
        page.click("button:has-text('Next question')")
        page.click("#up-o-travel")  # Travel moves up one place
        page.locator("ol.order").scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "10-order.png"))
        page.click("button:has-text('Next question')")
        page.fill(".wxpick input", "Springfield")
        page.click("text=Find my town")
        page.click(".wxpick .chip >> text=Springfield, Illinois")
        page.locator(".wxpick:not(.localfeeds)").scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "04-town-and-weather.png"))
        for _ in range(5):
            page.click("button:has-text('Next question')")
        page.click("button:has-text('Save and build my brief')")
        page.wait_for_selector("iframe.page", timeout=30000)
        page.wait_for_timeout(800)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(4500)  # let the "stories collected" note fade
        page.screenshot(path=str(OUT / "05-today.png"))
        page.click('#tabs button[data-tab="setup"]')
        page.screenshot(path=str(OUT / "06-your-choices.png"))
        page.click('#tabs button[data-tab="daily"]')
        page.screenshot(path=str(OUT / "09-every-day.png"))
        ctx.close()
        full = b.new_page(viewport={"width": 1280, "height": 900})
        T.route_world(full, [])
        full.goto(page_html.as_uri())
        eager(full)
        full.screenshot(path=str(OUT / "07-brief-page.png"), full_page=True)
        phone_ctx, phone, _ = T.open_page((p, b), page_html.as_uri(), device="iPhone 13")
        eager(phone)
        phone.screenshot(path=str(OUT / "08-phone.png"))
        b.close()
    for f in sorted(OUT.glob("*.png")):
        print(f.relative_to(ROOT), f.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
