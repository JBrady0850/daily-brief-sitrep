"""Reading feeds and collecting candidates (with recorded feeds, no network)."""
import pytest
from conftest import feed_bytes

from dailybrief import collect as C, engine as E

NOW = "2026-10-23T12:00:00Z"


def test_google_news_items():
    items = C.parse_feed(feed_bytes("google_news.xml"), google=True)
    assert len(items) == 5
    first = items[0]
    assert first["title"] == "Agency publishes new zero trust guidance for network teams - Example Security News"
    assert first["source"] == "Example Security News" and first["source_url"] == "https://security.example.com"
    assert first["published"] == "2026-10-23T09:00:00Z"
    assert first["summary"] == ""  # Google News descriptions only repeat the headline


def test_rss_with_html_description_and_undated_item():
    items = C.parse_feed(feed_bytes("rss_feed.xml"))
    assert items[0]["summary"] == "Several agencies are weighing voluntary separation offers. Officials expect decisions next month."
    assert items[0]["published"] == "2026-10-23T10:15:00Z" and items[0]["source"] == "Example Federal Daily"
    assert items[2]["published"] is None


def test_atom_feed():
    items = C.parse_feed(feed_bytes("atom_feed.xml"))
    assert [i["url"] for i in items] == ["https://science.example.org/sleep", "https://science.example.org/water"]
    assert items[1]["published"] == "2026-10-22T20:00:00Z"
    assert items[0]["summary"] == "The team traced a brain signal. It shortens deep sleep."


def test_refuses_entity_declarations_and_garbage():
    with pytest.raises(C.FetchError):
        C.parse_feed(b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><rss><channel></channel></rss>')
    with pytest.raises(C.FetchError):
        C.parse_feed(b"this is not xml")


def fake_fetcher(calls):
    def fetch(url):
        calls.append(url)
        if "news.google.com" in url:
            return feed_bytes("google_news.xml")
        if "broken" in url:
            raise C.FetchError("HTTP 404")
        return feed_bytes("rss_feed.xml")
    return fetch


def settings():
    return {"version": 1, "brief": {"items_per_category": 3},
            "categories": [
                {"id": "net", "name": "Network security", "queries": ['"zero trust"', "VPN patch"],
                 "require": [["zero trust", "VPN", "network", "segmentation"]], "feeds": ["https://broken.example.com/feed"]},
                {"id": "fed", "name": "Federal workforce", "queries": ["buyout"], "require": [["buyout", "buyouts", "reduction in force"]],
                 "feeds": ["https://federal.example.com/feed"]}]}


def test_collect_and_select_with_health_report():
    calls = []
    brief, health = C.run_brief(settings(), NOW, "2026-10-23", E.empty_ledger(), fetcher=fake_fetcher(calls), pause=0)
    net, fed = brief["categories"]
    assert [i["title"] for i in net["items"]] == ["Agency publishes new zero trust guidance for network teams",
                                                   "Firewall vendor patches VPN flaw under active attack",
                                                   "Network segmentation lessons from a hospital breach"]
    assert [i["recency"] for i in net["items"]] == ["news", "news", "backfill"]
    assert net["rejected"]["social or avoided site"] >= 1 and net["rejected"]["off topic"] >= 1
    assert health["net"]["feeds"][0]["error"] == "HTTP 404"
    assert [i["recency"] for i in fed["items"]] == ["news", "reference"]
    assert fed["rejected"]["paperwork notice"] == 1
    # Short of fresh news, so each category asked Google for older items too.
    assert any("when%3A3d" in u for u in calls)


def test_one_failing_source_never_stops_the_brief():
    def boom(url):
        raise RuntimeError("network down")
    brief, health = C.run_brief(settings(), NOW, "2026-10-23", None, fetcher=boom, pause=0)
    assert brief["total"] == 0 and brief["empty"] == 2
    assert all(q["error"] for h in health.values() for q in h["queries"])


def test_html_to_text():
    assert C.html_to_text("<p>One &amp; two</p><script>x()</script><br>three") == "One & two three"
    assert C.first_sentences("A. B. C.", 2) == "A. B."


def test_more_date_formats_and_unreadable_dates_are_not_undated():
    d = C._date
    assert d("2026-10-23 09:00:00 +0000") == "2026-10-23T09:00:00Z"
    assert d("23 October 2026") == d("Oct 23, 2026") == "2026-10-23T00:00:00Z"
    assert d("1792800000") == "2026-10-24T00:00:00Z"
    assert d("Fri, 23 Oct 2026 09:00:00 CET") == "2026-10-23T08:00:00Z"
    assert d("") is None and d("sometime soon") == "sometime soon"
    cfg = {"version": 1, "categories": [{"id": "x", "name": "X", "queries": ["x"], "require": [["patch"]]}]}
    b = E.select_brief({"x": [{"title": "Old patch", "url": "https://e.com/1", "published": "sometime soon"},
                              {"title": "Undated patch page", "url": "https://e.com/2", "published": None}]},
                       cfg, None, "2026-10-23T12:00:00Z", "2026-10-23")
    cat = b["categories"][0]
    assert [i["title"] for i in cat["items"]] == ["Undated patch page"] and cat["rejected"] == {"unreadable date": 1}


def test_entity_guard_scans_the_whole_document():
    hidden = b"<?xml version='1.0'?><!-- " + b"x" * 6000 + b" --><!DOCTYPE rss [<!ENTITY a 'b'>]><rss>&a;</rss>"
    with pytest.raises(C.FetchError):
        C.parse_feed(hidden)
    with pytest.raises(C.FetchError):
        C.parse_feed("<!DOCTYPE r [<!ENTITY a 'b'>]><rss/>".encode("utf-16"))
