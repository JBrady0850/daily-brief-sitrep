"""The newsletter theme."""
import copy

from dailybrief import engine as E, render as R


def test_sample_renders_every_part(sample_brief, sample_settings):
    out = R.render(sample_brief, sample_settings)
    html, text = out["html"], out["text"]
    assert out["subject"] == "[SAMPLE] Daily Brief - 12-Item SITREP | 2026-10-23 | 1 empty"
    for part in ("Friday, October 23, 2026", "Lead analysis", "Days to the spring trip", "Target date", "No new items for:",
                 "REFERENCE &middot; undated", "OLDER &middot; 1d 16h ago", "Reading the pills", ">T1<", ">T6<"):
        assert part in html, part
    for c in sample_brief["categories"]:
        assert E.collapse(c["name"]) in text
    assert "DAYS TO THE SPRING TRIP: 159 days" in text
    assert chr(0x2014) not in html and chr(0x2014) not in text


def test_untrusted_text_is_escaped_and_bad_links_are_not_links(sample_brief):
    b = copy.deepcopy(sample_brief)
    b["source"] = "ai"
    it = b["categories"][0]["items"]
    it[0]["title"] = "<img src=x onerror=alert(1)> \"q\" & 'a'"
    it[1]["url"] = "javascript:alert(document.cookie)"
    b["categories"][0]["name"] = "<b>Desk</b>"
    html = R.render(b, None)["html"]
    assert "<img src=x" not in html and "&lt;img src=x onerror=alert(1)&gt; &quot;q&quot; &amp; &#x27;a&#x27;" in html
    assert "javascript:" not in html
    assert "&lt;b&gt;Desk&lt;/b&gt;" in html


def test_subject_template_and_countdown_off(sample_brief, sample_settings):
    s = copy.deepcopy(sample_settings)
    s["brief"]["subject"] = "{title}: {total} stories, {empty} empty, {date}"
    s["countdown"]["enabled"] = False
    b = dict(sample_brief, source="ai")
    out = R.render(b, s)
    assert out["subject"] == "The Morning Brief: 12 stories, 1 empty, 2026-10-23"
    assert 'class="cd"' not in out["html"]


def test_history_wording(sample_brief):
    b = dict(sample_brief, source="desktop", ledger_applied=True, withheld=0)
    assert "nothing here has been sent to you before" in R.render(b)["html"]
    b["withheld"] = 4
    out = R.render(b)
    assert "4 withheld as already sent" in out["html"] and "4 withheld as already sent" in out["text"]


def test_css_comes_from_the_app_file():
    css = R.css()
    assert "header.mast" in css and "section.card" in css and len(css) > 3000
    assert "table" not in css, "a web page, not an email layout"


def test_times_use_the_computer_clock_when_it_has_no_zone_data(monkeypatch):
    """Windows without the tzdata package: the computer's own clock stands in for the reader's zone."""
    from datetime import datetime, timedelta, timezone as tzone
    from dailybrief import render as R
    monkeypatch.setattr(R, "_zone", lambda tz: None)
    central = tzone(timedelta(hours=-5))
    monkeypatch.setattr(R, "_computer_clock", lambda s: datetime.fromtimestamp(s, tz=tzone.utc).astimezone(central))
    assert R.built_label("2026-10-25T14:56:08Z", "America/Chicago") == "Sunday, October 25, 2026 at 9:56 AM CDT"
    assert R.stamp("2026-10-25T14:56:08Z", "America/Los_Angeles") == "Oct 25, 2:56 PM UTC", "another US zone: UTC, never a wrong clock"
    assert R.stamp("2026-10-25T14:56:08Z", "Europe/Paris") == "Oct 25, 9:56 AM UTC-5", "elsewhere: the computer's clock and its offset"
    assert R.stamp("2026-10-25T14:56:08Z", "") == "Oct 25, 2:56 PM UTC"
