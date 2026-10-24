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


def test_the_backup_keeps_only_stories_on_the_category_topic():
    lib = {"version": 1, "groups": [], "packs": [], "categories": [
        {"id": "net", "name": "Network security", "queries": ['"zero trust"'], "require": [["zero trust", "VPN"]], "exclude": ["guidance"]}]}
    data = NC.build(NOW, lib, fake_fetcher([]), pause=0)
    titles = [i["title"] for i in data["categories"]["net"]]
    assert titles and all(("zero trust" in t.lower() or "VPN" in t) and "guidance" not in t.lower() for t in titles), titles
    assert not any("Bakery" in t for t in titles), "off-topic stories stay out of the backup"


def test_the_backup_keeps_only_the_newest_stories_per_category():
    data = NC.build(NOW, LIB, fake_fetcher([]), pause=0, per_category=2)
    assert all(len(v) <= 2 for v in data["categories"].values())


def test_each_feed_is_read_once_one_search_per_category_and_a_time_budget():
    calls = []
    lib = {"version": 1, "groups": [], "packs": [], "categories": [
        {"id": "a", "name": "A", "queries": ["one", "two"], "require": [["buyout"]], "feeds": ["https://shared.example.com/feed"]},
        {"id": "b", "name": "B", "queries": ["three"], "require": [["buyout"]], "feeds": ["https://shared.example.com/feed"]},
        {"id": "c", "name": "C", "queries": ["four"], "require": [["buyout"]]}]}
    ticks = iter([0, 0, 1, 2, 999, 999])
    lines = []
    data = NC.build(NOW, lib, fake_fetcher(calls), pause=0, budget=100, log=lines.append, clock=lambda: next(ticks))
    assert calls.count("https://shared.example.com/feed") == 1
    assert len([u for u in calls if "news.google.com" in u]) == 2, "one search per category, none for the skipped one"
    assert sorted(data["categories"]) == ["a", "b"] and data["sources"]["skipped"] == 1
    assert any("[1/3] a" in s for s in lines) and any("budget" in s for s in lines)


def test_build_cache_command_writes_the_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(NC, "quick_fetch", fake_fetcher([]))
    monkeypatch.setattr(NC, "library", lambda: LIB)
    out = tmp_path / "data" / "news-cache.json"
    code = cli.main(["build-cache", "--out", str(out), "--pause", "0"])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0 and data["schema"] == "daily-brief-news-cache/1" and data["categories"]["net"]
    assert "Wrote" in capsys.readouterr().out


def refusing_google(calls):
    """Google News turns every search away (as it did GitHub's servers on 2026-10-24)."""
    def fetch(url):
        calls.append(url)
        if "news.google.com" in url:
            raise C.FetchError("Service Unavailable")
        return feed_bytes("rss_feed.xml")
    return fetch


def test_google_refusals_end_the_searching_and_every_category_still_reads_its_feeds():
    calls, lines = [], []
    lib = {"version": 1, "groups": [], "packs": [], "categories": [
        {"id": "c%d" % i, "name": "C%d" % i, "queries": ["buyout %d" % i], "require": [["buyout"]],
         "feeds": ["https://federal%d.example.com/feed" % i]} for i in range(6)]}
    data = NC.build(NOW, lib, refusing_google(calls), pause=0, log=lines.append)
    assert len([u for u in calls if "news.google.com" in u]) == C.GOOGLE_GIVE_UP, "three refusals, then no more searches"
    assert len([u for u in calls if "federal" in u]) == 6, "every category still reads its feeds"
    assert sorted(data["categories"]) == ["c%d" % i for i in range(6)] and all(data["categories"].values())
    src = data["sources"]
    assert (src["searches"], src["searches_failed"], src["searches_skipped"]) == (3, 3, 3)
    assert any("turned away" in s for s in lines)
    assert not any(C.SKIPPED in s for s in lines), "skipped searches are not reported as problems"


def previous_file(stories, schema="daily-brief-news-cache/1"):
    return {"schema": schema, "generated_at": "2026-10-23T08:00:00Z", "categories": {"fed": stories}, "sources": {}}


def story(title, url, published):
    return {"title": title, "url": url, "source": "Example Federal", "source_url": "https://federal.example.com",
            "published": published, "summary": "", "image": ""}


def test_recent_on_topic_stories_from_the_last_run_are_kept():
    lib = {"version": 1, "groups": [], "packs": [], "categories": [
        {"id": "fed", "name": "Federal workforce", "queries": ["buyout"], "require": [["buyout"]]}]}
    old = [story("Agency offers buyout to federal staff", "https://federal.example.com/kept", "2026-10-22T08:00:00Z"),
           story("Second buyout round opens", "https://federal.example.com/too-old", "2026-10-18T08:00:00Z"),
           story("Bakery opens downtown", "https://federal.example.com/off-topic", "2026-10-22T09:00:00Z")]

    def nothing_answers(url):
        raise C.FetchError("Service Unavailable")
    data = NC.build(NOW, lib, nothing_answers, pause=0, previous=previous_file(old))
    assert [i["url"] for i in data["categories"]["fed"]] == ["https://federal.example.com/kept"]
    assert data["sources"]["carried"] == 1
    assert set(data["categories"]["fed"][0]) <= {"title", "url", "source", "source_url", "published", "summary", "image", "on_topic"}
    # A file in another format counts as no earlier file.
    data = NC.build(NOW, lib, nothing_answers, pause=0, previous=previous_file(old, schema="something-else/9"))
    assert data["categories"]["fed"] == [] and data["sources"]["carried"] == 0


def test_new_stories_come_first_and_a_category_without_time_keeps_its_earlier_stories():
    lib = {"version": 1, "groups": [], "packs": [], "categories": [
        {"id": "net", "name": "Network security", "queries": ['"zero trust"'], "require": [["zero trust", "VPN", "network"]]},
        {"id": "fed", "name": "Federal workforce", "queries": ["buyout"], "require": [["buyout"]]}]}
    kept = story("Agency offers buyout to federal staff", "https://federal.example.com/kept", "2026-10-22T08:00:00Z")
    ticks = iter([0, 0, 1, 999])
    data = NC.build(NOW, lib, fake_fetcher([]), pause=0, budget=100, clock=lambda: next(ticks), previous=previous_file([kept]))
    assert data["categories"]["net"], "the category that ran has new stories"
    assert data["categories"]["fed"] == [kept] and data["sources"]["skipped"] == 1 and data["sources"]["carried"] == 1


def test_build_cache_command_keeps_the_previous_file_and_survives_a_missing_one(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(NC, "quick_fetch", lambda url: (_ for _ in ()).throw(C.FetchError("Service Unavailable")))
    monkeypatch.setattr(NC, "library", lambda: LIB)
    prev = tmp_path / "previous.json"
    prev.write_text(json.dumps(previous_file([story("Agency offers buyout to federal staff", "https://federal.example.com/kept",
                                                       "2026-10-23T08:00:00Z")])), encoding="utf-8")
    out = tmp_path / "news-cache.json"
    code = cli.main(["build-cache", "--out", str(out), "--pause", "0", "--previous", str(prev)])
    data = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0 and data["categories"]["fed"][0]["url"] == "https://federal.example.com/kept"
    assert "Kept from the last run: 1" in capsys.readouterr().out
    code = cli.main(["build-cache", "--out", str(out), "--pause", "0", "--previous", str(tmp_path / "missing.json")])
    assert code == 1, "nothing new and nothing earlier: the command says so"
    assert "starting fresh" in capsys.readouterr().err
