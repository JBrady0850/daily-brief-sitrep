"""The backup collection that GitHub builds for the web page (recorded feeds, no network)."""
import json

from conftest import feed_bytes

from dailybrief import cli, collect as C, engine as E, newscache as NC

NOW = "2026-10-23T12:00:00Z"
LIB = {"version": 1, "groups": [], "packs": [], "categories": [
    {"id": "net", "name": "Network security", "queries": ['"zero trust"'], "require": [["zero trust", "VPN", "network"]],
     "feeds": ["https://broken.example.com/feed"]},
    {"id": "fed", "name": "Federal workforce", "queries": ["buyout"], "require": [["buyout"]],
     "topic_feeds": ["https://federal.example.com/feed"]},
    {"id": "town", "name": "Local news ({location})", "queries": ['"{location}" council'], "require": [["{local_terms}"]],
     "needs_location": True},
]}


def fake_fetcher(calls):
    def fetch(url):
        calls.append(url)
        if "news.google.com" in url:
            return feed_bytes("google_news.xml")
        if "broken" in url:
            raise C.FetchError("HTTP 404")
        return feed_bytes("rss_feed.xml")
    return fetch


def test_the_backup_collection_covers_every_category_except_the_town_ones():
    calls = []
    data = NC.build(NOW, LIB, fake_fetcher(calls), pause=0)
    assert data["schema"] == "daily-brief-news-cache/1" and data["generated_at"] == NOW
    assert sorted(data["categories"]) == ["fed", "net"], "town categories depend on each reader's town"
    assert not any("council" in u for u in calls)
    for items in data["categories"].values():
        assert items, "every category has stories"
        stamps = [i["published"] for i in items]
        assert stamps == sorted(stamps, reverse=True), "newest first"
        for i in items:
            assert set(i) <= {"title", "url", "source", "source_url", "published", "summary", "image", "on_topic"}
            assert E.parse_iso(i["published"]) is not None, "undated stories stay out"
            assert (E.parse_iso(NOW) - E.parse_iso(i["published"])) / 3600000 <= NC.MAX_AGE_HOURS
            assert len(i["summary"]) <= NC.SUMMARY_CHARS
    feed_items = [i for i in data["categories"]["fed"] if i.get("on_topic")]
    assert feed_items, "stories from an on-topic feed keep their mark"
    assert data["sources"]["feeds_failed"] == 1 and data["sources"]["searches"] >= 2


def test_the_backup_keeps_only_the_newest_stories_per_category():
    data = NC.build(NOW, LIB, fake_fetcher([]), pause=0, per_category=2)
    assert all(len(v) <= 2 for v in data["categories"].values())


def test_build_cache_command_writes_the_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(C, "fetch", fake_fetcher([]))
    monkeypatch.setattr(NC, "library", lambda: LIB)
    out = tmp_path / "data" / "news-cache.json"
    code = cli.main(["build-cache", "--out", str(out), "--pause", "0"])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0 and data["schema"] == "daily-brief-news-cache/1" and data["categories"]["net"]
    assert "Wrote" in capsys.readouterr().out
