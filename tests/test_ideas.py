"""Countdown ideas (app/js/ideas.js): the published date rules and the suggestions
picked from the reader's categories. Run in Node through the parity bridge."""
from conftest import js_calls


def call(fn, *args):
    return js_calls([{"fn": "I." + fn, "args": list(args)}])[0]


def test_date_rules_match_published_dates():
    # Tax Day moves past weekends and Emancipation Day (IRS, 2016 to 2023).
    got = js_calls([{"fn": "I.taxDay", "args": [y]} for y in (2016, 2017, 2018, 2019, 2022, 2023, 2024, 2027, 2028)])
    assert got == ["2016-04-18", "2017-04-18", "2018-04-17", "2019-04-15", "2022-04-18", "2023-04-18", "2024-04-15",
                   "2027-04-15", "2028-04-18"]
    assert [call("electionDay", y) for y in (2024, 2026, 2028)] == ["2024-11-05", "2026-11-03", "2028-11-07"]
    assert [call("thanksgiving", y) for y in (2025, 2026, 2027)] == ["2025-11-27", "2026-11-26", "2027-11-25"]
    # Federal Benefits Open Season (5 CFR 890.301(f)), as OPM and Checkbook list it for 2022 to 2026.
    got = js_calls([{"fn": "I.openSeason", "args": [y]} for y in (2022, 2023, 2024, 2025, 2026)])
    assert got == [["2022-11-14", "2022-12-12"], ["2023-11-13", "2023-12-11"], ["2024-11-11", "2024-12-09"],
                   ["2025-11-10", "2025-12-08"], ["2026-11-09", "2026-12-14"]]


def cats(*ids):
    return [{"id": i, "name": i.replace("-", " ").title()} for i in ids]


def test_ideas_follow_the_category_order_and_stop_at_four():
    got = call("ideasFor", cats("federal-retirement", "local-weather", "politics", "travel", "nfl"), "2026-10-25", {"region": "Florida"})
    assert [i["id"] for i in got] == ["federal-retirement", "open-season", "hurricane", "election"]
    fed = got[0]
    assert fed["fixed"] is False and fed["from"] == "Federal Retirement" and "Give HR your retirement application" in fed["steps"][3]
    assert got[1]["label"] == "Days to Federal Benefits Open Season" and got[1]["date"] == "2026-11-09"
    assert got[2]["label"] == "Days left in hurricane season" and got[2]["date"] == "2026-11-30"
    assert got[3]["date"] == "2026-11-03"
    # One retirement idea, even when two categories suggest it; nothing for unknown categories.
    assert [i["id"] for i in call("ideasFor", cats("retirement-planning", "federal-retirement"), "2026-10-25", {})] == ["retirement", "open-season"]
    assert call("ideasFor", cats("world-news"), "2026-10-25", {}) == [] and call("ideasFor", [], "2026-10-25", None) == []
    every = call("ideasFor", cats("federal-retirement", "local-weather", "politics", "travel", "nfl"), "2026-10-25", {"region": "Florida"}, 99)
    assert [i["id"] for i in every] == ["federal-retirement", "open-season", "hurricane", "election", "trip", "season"], "a limit lifts the cap"
    assert "launch" not in [i["id"] for i in call("ideasFor", cats("enterprise-ai", "ai-tools"), "2026-10-25", {}, 99)]


def test_ideas_for_some_readers_wait_in_more_ideas():
    """Medicare is never suggested (most readers are not on Medicare); the hurricane season
    only on the Atlantic and Gulf coasts. Both stay one pick away in More ideas."""
    picked = cats("retirement-planning", "health-wellness", "local-weather")
    inland = call("ideasFor", picked, "2026-10-25", {"region": "Illinois"})
    assert "medicare" not in [i["id"] for i in inland] and "hurricane" not in [i["id"] for i in inland]
    coast = call("ideasFor", picked, "2026-10-25", {"region": "FL"})
    assert "hurricane" in [i["id"] for i in coast] and "medicare" not in [i["id"] for i in coast]
    more = call("moreIdeas", picked, "2026-10-25", {"region": "Illinois"}, [i["id"] for i in inland])
    ids = [m["id"] for m in more]
    assert ids[:2] == ["medicare", "hurricane"], "ideas that fit a chosen category come first"
    assert more[0]["from"] == "Retirement Planning" and more[0]["about"].startswith("For people on Medicare")
    assert len(ids) == len(set(ids)) and not set(ids) & {i["id"] for i in inland}, "nothing twice, nothing already shown"
    assert {"trip", "move", "season"} <= set(ids) and [m["from"] for m in more if m["id"] == "trip"] == [""]
    assert call("ideaById", "medicare", "2026-10-25", "Retirement Planning")["label"] == "Days left in Medicare Open Enrollment"
    assert call("ideaById", "nothing", "2026-10-25", "") is None


def test_fixed_ideas_fill_in_the_next_date_and_future_milestones():
    med = call("fill", "medicare", "", "2026-10-25")
    assert med == {"label": "Days left in Medicare Open Enrollment", "date": "2026-12-07", "start": "2026-10-15", "idea": "medicare",
                   "milestones": [{"date": "2026-11-16", "label": "Compare plans for next year", "note": ""},
                                  {"date": "2026-11-30", "label": "Make any change", "note": ""}]}
    assert call("fill", "medicare", "", "2026-12-20")["label"] == "Days to Medicare Open Enrollment"
    assert call("fill", "medicare", "", "2026-12-20")["date"] == "2027-10-15"
    tax = call("fill", "tax", "", "2026-10-25")
    assert tax["date"] == "2027-04-15" and [m["date"] for m in tax["milestones"]] == ["2027-02-01", "2027-03-16"]
    assert call("fill", "tax", "", "2027-04-16")["date"] == "2028-04-18"
    storm = call("fill", "hurricane", "", "2027-01-10")
    assert (storm["label"], storm["date"], storm["start"]) == ("Days to hurricane season", "2027-06-01", "2026-12-01")
    assert [m["date"] for m in storm["milestones"]] == ["2027-05-02", "2027-05-18"]
    assert call("fill", "election", "", "2026-11-04")["date"] == "2028-11-07", "after the vote, the next one"
    assert call("fill", "election", "", "2027-03-01")["date"] == "2028-11-07"
    before = call("fill", "open-season", "", "2026-10-25")
    assert (before["label"], before["date"], before["start"]) == ("Days to Federal Benefits Open Season", "2026-11-09", "2026-10-25")
    during = call("fill", "open-season", "", "2026-11-20")
    assert (during["label"], during["date"], during["start"]) == ("Days left in Federal Benefits Open Season", "2026-12-14", "2026-11-09")
    assert [m["label"] for m in during["milestones"]][1] == "Re-enroll in FSAFEDS if you use it (it does not carry over)"
    assert call("fill", "open-season", "", "2026-12-14")["date"] == "2027-11-08", "after the last day, next year's"


def test_personal_ideas_count_back_from_the_readers_date():
    got = call("fill", "federal-retirement", "2027-06-30", "2026-10-25")
    assert (got["label"], got["date"], got["start"]) == ("Days to retirement", "2027-06-30", "2026-10-25")
    assert [m["date"] for m in got["milestones"]] == ["2027-01-01", "2027-03-02", "2027-04-01", "2027-06-16"], "past steps drop out"
    assert call("fill", "trip", "2026-10-25", "2026-10-25") is None, "the date has to be after today"
    assert call("fill", "trip", "", "2026-10-25") is None and call("fill", "nothing", "2027-01-01", "2026-10-25") is None
    assert call("fill", "season", "2027-09-09", "2026-10-25")["milestones"] == []
