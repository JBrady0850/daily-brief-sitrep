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


def cats(*ids):
    return [{"id": i, "name": i.replace("-", " ").title()} for i in ids]


def test_ideas_follow_the_category_order_and_stop_at_four():
    got = call("ideasFor", cats("federal-retirement", "local-weather", "politics", "travel", "nfl"), "2026-10-25")
    assert [i["id"] for i in got] == ["federal-retirement", "medicare", "hurricane", "election"]
    fed = got[0]
    assert fed["fixed"] is False and fed["from"] == "Federal Retirement" and "Give HR your retirement application" in fed["steps"][3]
    assert got[2]["label"] == "Days left in hurricane season" and got[2]["date"] == "2026-11-30"
    assert got[3]["date"] == "2026-11-03"
    # One retirement idea, even when two categories suggest it; nothing for unknown categories.
    assert [i["id"] for i in call("ideasFor", cats("retirement-planning", "federal-retirement"), "2026-10-25")] == ["retirement", "medicare"]
    assert call("ideasFor", cats("world-news"), "2026-10-25") == [] and call("ideasFor", [], "2026-10-25") == []


def test_fixed_ideas_fill_in_the_next_date_and_future_milestones():
    med = call("fill", "medicare", "", "2026-10-25")
    assert med == {"enabled": True, "label": "Days left in Medicare Open Enrollment", "date": "2026-12-07", "start": "2026-10-15",
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


def test_personal_ideas_count_back_from_the_readers_date():
    got = call("fill", "federal-retirement", "2027-06-30", "2026-10-25")
    assert (got["label"], got["date"], got["start"]) == ("Days to retirement", "2027-06-30", "2026-10-25")
    assert [m["date"] for m in got["milestones"]] == ["2027-01-01", "2027-03-02", "2027-04-01", "2027-06-16"], "past steps drop out"
    assert call("fill", "trip", "2026-10-25", "2026-10-25") is None, "the date has to be after today"
    assert call("fill", "trip", "", "2026-10-25") is None and call("fill", "nothing", "2027-01-01", "2026-10-25") is None
    assert call("fill", "season", "2027-09-09", "2026-10-25")["milestones"] == []
