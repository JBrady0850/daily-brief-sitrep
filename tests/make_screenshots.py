"""Regenerates the screenshots in docs/images with Playwright and Chromium.

    python tests/make_screenshots.py

The brief shown is the invented sample, so no real news or personal data ever
appears in the pictures.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402

from dailybrief import render  # noqa: E402
import json  # noqa: E402

OUT = ROOT / "docs" / "images"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    url = (ROOT / "app" / "index.html").as_uri()
    brief = json.loads((ROOT / "examples" / "sample-brief.json").read_text(encoding="utf-8"))
    settings = json.loads((ROOT / "examples" / "sample-settings.json").read_text(encoding="utf-8"))
    news_html = ROOT / "output" / "sample-newsletter.html"
    news_html.parent.mkdir(exist_ok=True)
    news_html.write_text(render.render(brief, settings)["html"], encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1100, "height": 820})
        page.on("dialog", lambda d: d.accept())
        page.goto(url)
        page.wait_for_selector(".interview")
        page.screenshot(path=str(OUT / "01-setup.png"))
        page.click("text=Next question")
        page.screenshot(path=str(OUT / "02-pick-categories.png"))
        page.click('#tabs button[data-tab="categories"]')
        page.click("#tab-categories details >> nth=0")
        page.screenshot(path=str(OUT / "03-categories.png"))
        page.click('#tabs button[data-tab="brief"]')
        page.click("text=Show the sample brief")
        page.wait_for_selector("iframe.preview")
        page.wait_for_timeout(400)
        page.locator("#briefview").scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / "04-brief.png"))
        page.click('#tabs button[data-tab="ai"]')
        page.screenshot(path=str(OUT / "05-ai-assistants.png"))
        nl = b.new_page(viewport={"width": 760, "height": 1300})
        nl.goto(news_html.as_uri())
        nl.screenshot(path=str(OUT / "06-newsletter.png"))
        phone = b.new_context(**p.devices["iPhone 13"]).new_page()
        phone.goto(url)
        phone.wait_for_selector(".interview")
        phone.screenshot(path=str(OUT / "07-phone.png"))
        b.close()
    for f in sorted(OUT.glob("*.png")):
        print(f.relative_to(ROOT), f.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
