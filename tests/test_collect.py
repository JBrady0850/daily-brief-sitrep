"""Reading feeds and collecting candidates (with recorded feeds, no network)."""
import json

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


def test_on_topic_feeds_count_only_for_the_category_that_names_them():
    feed = "https://dedicated.example.com/feed"
    cfg = {"version": 1, "brief": {"items_per_category": 3}, "categories": [
        {"id": "plain", "name": "Plain", "queries": [], "require": [["zzzz"]], "feeds": [feed]},
        {"id": "topic", "name": "Topic", "queries": [], "require": [["zzzz"]], "topic_feeds": [feed]}]}
    calls = []
    brief, health = C.run_brief(cfg, NOW, "2026-10-23", None, fetcher=fake_fetcher(calls), pause=0)
    plain, topic = brief["categories"]
    assert plain["items"] == [] and plain["rejected"]["off topic"] >= 1
    assert len(topic["items"]) >= 1
    assert health["topic"]["feeds"][0]["on_topic"] and not health["plain"]["feeds"][0]["on_topic"]
    assert calls.count(feed) == 1, "the feed is read once"


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


# ------------------------------------------------------------- photos and weather
PHOTO_FEED = b"""<?xml version="1.0"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel><title>Example Daily</title><link>https://example.com/</link>
<item><title>Story with media content</title><link>https://example.com/a</link><pubDate>Fri, 23 Oct 2026 09:00:00 GMT</pubDate>
<media:content url="https://img.example.com/a.jpg" medium="image" width="600"/></item>
<item><title>Story with a thumbnail</title><link>https://example.com/b</link>
<media:thumbnail url="https://img.example.com/b.jpg"/></item>
<item><title>Story with an http picture only</title><link>https://example.com/c</link>
<enclosure url="http://img.example.com/c.jpg" type="image/jpeg" length="1"/></item>
<item><title>Story with a picture in its HTML</title><link>https://example.com/d</link>
<description>&lt;p&gt;&lt;img src="https://img.example.com/d.png?w=1&amp;amp;h=2" alt=""&gt;Text.&lt;/p&gt;</description></item>
<item><title>Story with a video</title><link>https://example.com/e</link>
<media:content url="https://video.example.com/e.mp4" type="video/mp4"/></item>
</channel></rss>"""


def test_feed_photos_are_found_and_only_https_counts():
    items = C.parse_feed(PHOTO_FEED)
    assert [i["image"] for i in items] == ["https://img.example.com/a.jpg", "https://img.example.com/b.jpg", "",
                                          "https://img.example.com/d.png?w=1&h=2", ""]
    assert all(i["image"] == "" for i in C.parse_feed(feed_bytes("google_news.xml"), google=True))


FORECAST = {"current": {"temperature_2m": 51.4, "weather_code": 3},
            "daily": {"time": ["2026-10-23", "2026-10-24", "2026-10-25", "2026-10-26", "2026-10-27"],
                      "weather_code": [3, 61, 0, 95, 71], "temperature_2m_max": [58.2, 55, 61.5, 60.1, 40],
                      "temperature_2m_min": [44.1, 47.9, 43, 50, 30], "precipitation_probability_max": [10, 80, 0, 65, 90]}}


def test_forecast_becomes_the_weather_block():
    w = {"enabled": True, "place": "Example City", "latitude": 41.88, "longitude": -87.63, "units": "fahrenheit"}
    cfg = {"version": 1, "weather": w, "categories": [{"id": "a", "name": "A", "queries": ["a"]}]}
    asked = []

    def fetcher(url):
        asked.append(url)
        return json.dumps(FORECAST).encode()
    wx = C.weather(cfg, "2026-10-23T11:00:00Z", fetcher)
    assert asked == [C.forecast_url(w)] and "latitude=41.88&longitude=-87.63" in asked[0] and "fahrenheit" in asked[0]
    assert wx["place"] == "Example City" and wx["current"] == {"temp": 51.4, "code": 3} and len(wx["days"]) == 4
    assert wx["days"][1] == {"date": "2026-10-24", "code": 61, "hi": 55, "lo": 47.9, "rain": 80}
    assert C.weather(dict(cfg, weather=dict(w, enabled=False)), "2026-10-23T11:00:00Z", fetcher) is None


def test_weather_failure_never_stops_the_brief(monkeypatch):
    w = {"enabled": True, "place": "Example City", "latitude": 41.88, "longitude": -87.63, "units": "celsius"}
    cfg = {"version": 1, "weather": w, "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'],
                                                     "require": [["zero trust", "VPN"]]}]}

    def fetcher(url):
        if "open-meteo" in url:
            raise C.FetchError("down")
        return feed_bytes("google_news.xml")
    brief, health = C.run_brief(cfg, "2026-10-23T12:00:00Z", "2026-10-23", None, fetcher, pause=0)
    assert "weather" not in brief and "down" in health["_weather"]["error"] and brief["total"] > 0


def test_town_searches_add_the_state_and_failed_searches_are_marked_unchecked():
    calls = []
    cfg = {"version": 1, "reader": {"location": "Springfield", "region": "Illinois"}, "categories": [
        {"id": "town", "name": "Local ({location})", "queries": ['"{location}" council'], "require": [["{local_terms}"]], "needs_location": True},
        {"id": "net", "name": "Net", "queries": ['"zero trust"'], "require": [["zero trust"]]}]}

    def fetcher(url):
        calls.append(url)
        raise C.FetchError("HTTP 503")
    brief, health = C.run_brief(cfg, NOW, "2026-10-23", None, fetcher=fetcher, pause=0)
    town_urls = [u for u in calls if "council" in u]
    assert town_urls and all("%22Illinois%22" in u for u in town_urls), town_urls
    assert all("Illinois" not in u for u in calls if "zero" in u), "only town searches add the state"
    assert all(c.get("unchecked") is True for c in brief["categories"])
