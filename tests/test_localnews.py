"""Local news by state, built on GitHub from local TV station feeds (recorded feeds, no network)."""
import json
import re
import time
from datetime import datetime, timedelta, timezone

from dailybrief import cli, collect as C, engine as E, localnews as LN

NOW = "2026-10-23T12:00:00Z"


def feed(titles_hours, host):
    """An RSS feed whose stories are the given hours old."""
    now = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
    items = "".join(
        "<item><title>%s</title><link>https://%s/story/%d</link><pubDate>%s</pubDate>"
        "<description>Summary for %s. Second sentence.</description></item>"
        % (t, host, k, (now - timedelta(hours=h)).strftime("%a, %d %b %Y %H:%M:%S GMT"), t)
        for k, (t, h) in enumerate(titles_hours))
    return ('<?xml version="1.0"?><rss version="2.0"><channel><title>Feed title</title><link>https://%s/</link>%s'
            "</channel></rss>" % (host, items)).encode()


STATIONS = [
    {"id": "wone", "name": "WONE", "site": "https://www.wone.example.com", "feed": "https://www.wone.example.com/rss", "states": ["IL"]},
    {"id": "wtwo", "name": "WTWO", "site": "https://wtwo.example.com", "feed": "https://wtwo.example.com/feed/", "states": ["IL", "MO"]},
    {"id": "kdown", "name": "KDOWN", "site": "https://kdown.example.com", "feed": "https://kdown.example.com/feed/", "states": ["MO"]},
]


def fetcher(calls, down=("kdown",)):
    feeds = {
        "https://www.wone.example.com/rss": feed([("Springfield council approves budget", 2), ("Old story", 120)], "www.wone.example.com"),
        "https://wtwo.example.com/feed/": feed([("Sangamon County fair opens", 5), ("Chatham parade Saturday", 30)], "wtwo.example.com"),
    }

    def get(url):
        calls.append(url)
        for sid in down:
            if sid in url:
                raise C.FetchError("Service Unavailable")
        return feeds[url]
    return get


def test_each_state_file_holds_its_stations_recent_stories():
    calls = []
    result = LN.build(NOW, STATIONS, fetcher(calls, down=()) if False else fetcher(calls, down=("kdown",)), workers=2)
    il, mo = result["states"]["IL"], result["states"]["MO"]
    assert sorted(result["states"]) == ["IL", "MO"]
    assert il["schema"] == "daily-brief-local-news/1" and il["state"] == "IL" and il["generated_at"] == NOW
    assert [s["title"] for s in il["stories"]] == ["Springfield council approves budget", "Sangamon County fair opens",
                                                    "Chatham parade Saturday"], "newest first; the 120-hour story is too old"
    assert [s["title"] for s in mo["stories"]] == ["Sangamon County fair opens", "Chatham parade Saturday"], \
        "a station that covers two states is in both files"
    s = il["stories"][0]
    assert s["source"] == "WONE" and s["source_url"] == "https://www.wone.example.com" and s["station"] == "wone"
    assert set(s) == {"title", "url", "source", "source_url", "published", "summary", "image", "station"}
    assert sorted(calls) == sorted(st["feed"] for st in STATIONS), "each feed is read once"
    idx = result["index"]
    assert idx["schema"] == "daily-brief-local-index/1" and idx["states"]["MO"] == {"stations": 2, "answered": 1, "stories": 2,
                                                                                    "kept_from_last_run": 0}
    assert list(idx["not_answering"]) == ["kdown"]


def test_a_station_that_does_not_answer_keeps_its_recent_stories_from_the_site():
    asked = []
    old = {"schema": "daily-brief-local-news/1", "state": "MO", "stories": [
        {"title": "Kept from the last run", "url": "https://kdown.example.com/a", "source": "KDOWN", "source_url": "",
         "published": "2026-10-23T06:00:00Z", "summary": "", "image": "", "station": "kdown"},
        {"title": "Too old to keep", "url": "https://kdown.example.com/b", "source": "KDOWN", "source_url": "",
         "published": "2026-10-18T06:00:00Z", "summary": "", "image": "", "station": "kdown"},
        {"title": "From a station that answered", "url": "https://wtwo.example.com/z", "source": "WTWO", "source_url": "",
         "published": "2026-10-23T06:00:00Z", "summary": "", "image": "", "station": "wtwo"}]}

    def previous(code):
        asked.append(code)
        return old if code == "MO" else None
    result = LN.build(NOW, STATIONS, fetcher([]), previous=previous, workers=2)
    titles = [s["title"] for s in result["states"]["MO"]["stories"]]
    assert "Kept from the last run" in titles and "Too old to keep" not in titles
    assert "From a station that answered" not in titles, "a station that answered speaks for itself"
    assert asked == ["MO"], "only a state with a station that did not answer looks back"
    assert result["index"]["states"]["MO"]["kept_from_last_run"] == 1 and result["index"]["carried"] == 1


def test_a_slow_station_counts_as_not_answering_after_the_budget():
    def slow(url):
        if "wone" in url:
            time.sleep(1.5)
        return fetcher([], down=())(url) if "kdown" not in url else feed([("Missouri story", 1)], "kdown.example.com")
    t = time.monotonic()
    result = LN.build(NOW, STATIONS, slow, workers=3, budget=0.5)
    assert time.monotonic() - t < 1.4, "the run does not wait for the slow feed"
    assert result["index"]["not_answering"] == {"wone": "no answer within the time budget"}
    assert [s["title"] for s in result["states"]["MO"]["stories"]][0] == "Missouri story"


def test_write_and_the_command(tmp_path, monkeypatch, capsys):
    stations = tmp_path / "stations.json"
    stations.write_text(json.dumps({"schema": "daily-brief-local-stations/1", "stations": STATIONS}), encoding="utf-8")
    monkeypatch.setattr(LN, "quick_fetch", fetcher([]))
    monkeypatch.setattr(cli, "_now_iso", lambda: NOW)
    out = tmp_path / "local"
    code = cli.main(["build-local", "--out", str(out), "--stations", str(stations)])
    assert code == 0 and sorted(p.name for p in out.iterdir()) == ["IL.json", "MO.json", "index.json"]
    raw = (out / "IL.json").read_bytes()
    assert b"\r" not in raw and LN.parse_state_file(raw.decode())["stories"]
    assert "Wrote 2 state files" in capsys.readouterr().out


def test_the_station_list_covers_every_state_with_working_looking_feeds():
    data = json.loads(LN.STATIONS_FILE.read_text(encoding="utf-8"))
    assert data["schema"] == LN.STATIONS_SCHEMA and E.is_date_str(data["checked"])
    stations = LN.load_stations()
    assert len(stations) >= 300
    ids = [s["id"] for s in stations]
    feeds = [s["feed"] for s in stations]
    assert len(set(ids)) == len(ids) and len(set(feeds)) == len(feeds)
    codes = set(E.US_STATES.values())
    for s in stations:
        assert re.fullmatch(r"[a-z0-9-]+", s["id"]), s["id"]
        assert s["feed"].startswith("https://") and s["site"].startswith("https://") and E.collapse(s["name"]), s
        assert s["states"] and set(s["states"]) <= codes, s
    covered = {c for s in stations for c in s["states"]}
    assert covered == codes, "every state and DC has at least one station: missing " + ", ".join(sorted(codes - covered))
