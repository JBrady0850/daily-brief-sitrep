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
    # Leave years as OPM's table lists them (2023 had 27 pay periods, so it began January 1).
    got = js_calls([{"fn": "I.leaveYear", "args": [y]} for y in range(2022, 2031)])
    assert got == ["2022-01-02", "2023-01-01", "2024-01-14", "2025-01-12", "2026-01-11", "2027-01-10", "2028-01-09",
                   "2029-01-07", "2030-01-06"]


def cats(*ids):
    return [{"id": i, "name": i.replace("-", " ").title()} for i in ids]


def test_ideas_follow_the_category_order_and_stop_at_four():
    got = call("ideasFor", cats("federal-retirement", "local-weather", "politics", "travel", "nfl"), "2026-10-25", {"region": "Florida"})
    assert [i["id"] for i in got] == ["federal-retirement", "open-season", "hurricane", "election"]
    fed = got[0]
    assert fed["fixed"] is False and fed["from"] == "Federal Retirement" and "Give HR your retirement application" in fed["steps"][2]
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
    assert [m["label"] for m in during["milestones"]] == ["Compare health, dental and vision plans for next year",
                                                          "Make any change on your benefits site"], "no step only some readers use"
    assert call("fill", "open-season", "", "2026-12-14")["date"] == "2027-11-08", "after the last day, next year's"


def test_personal_ideas_count_back_from_the_readers_date():
    got = call("fill", "retirement", "2027-06-30", "2026-10-25")
    assert (got["label"], got["date"], got["start"]) == ("Days to retirement", "2027-06-30", "2026-10-25")
    assert [m["date"] for m in got["milestones"]] == ["2027-05-01"], "past steps drop out"
    got = call("fill", "federal-retirement", "2027-06-30", "2026-10-25")
    steps = [m for m in got["milestones"] if not m["note"]]
    assert [m["date"] for m in steps] == ["2027-01-01", "2027-04-01", "2027-06-16"], "past steps drop out"
    # No idea adds a dated step that only some readers qualify for or use, at any time of year.
    every = [i["id"] for i in call("moreIdeas", [], "2026-10-25", {}, [])]
    for d in ("2026-01-15", "2026-06-15", "2026-10-25", "2026-11-20"):
        for idea in every:
            steps = call("ideaById", idea, d, "")["steps"]
            assert not any(w in s for s in steps for w in ("Social Security", "FSAFEDS")), (idea, d, steps)
            if idea != "medicare":
                assert not any("Medicare" in s for s in steps), (idea, d, steps)
    assert call("fill", "trip", "2026-10-25", "2026-10-25") is None, "the date has to be after today"
    assert call("fill", "trip", "", "2026-10-25") is None and call("fill", "nothing", "2027-01-01", "2026-10-25") is None
    assert call("fill", "season", "2027-09-09", "2026-10-25")["milestones"] == []


def test_federal_retirement_brings_the_federal_dates_on_the_way():
    """The dates from the reader's own federal brief (2026-10-26): this Open Season, the
    leave year change, and the final Open Season as an employee, in date order among
    the steps."""
    got = call("fill", "federal-retirement", "2027-12-31", "2026-10-26")
    rule = [(m["date"], m["label"], m["note"]) for m in got["milestones"] if m["note"]]
    assert rule == [("2026-11-09", "FEHB and FEDVIP Open Season opens, plan year 2027", "5 CFR 890.301(f)"),
                    ("2026-12-14", "Open Season closes", "5 CFR 890.301(f)"),
                    ("2027-01-09", "Leave year 2026 ends", "OPM leave-year table"),
                    ("2027-01-10", "Leave year 2027 begins", "OPM leave-year table"),
                    ("2027-11-08", "Final Open Season as an employee opens, plan year 2028", "5 CFR 890.301(f)"),
                    ("2027-12-13", "Final Open Season as an employee closes", "5 CFR 890.301(f)")]
    dates = [m["date"] for m in got["milestones"]]
    assert dates == sorted(dates) and len(got["milestones"]) == 10 and got["dates_added"] is True
    # During Open Season: only its last day is ahead. A date before the next season: no season at all.
    mid = [m["label"] for m in call("fill", "federal-retirement", "2028-06-30", "2026-11-20")["milestones"] if m["note"]]
    assert mid == ["Open Season closes", "Leave year 2026 ends", "Leave year 2027 begins",
                   "Final Open Season as an employee opens, plan year 2028", "Final Open Season as an employee closes"]
    soon = [m["label"] for m in call("fill", "federal-retirement", "2026-11-05", "2026-10-26")["milestones"]]
    assert not any("Open Season" in s or "Leave year" in s for s in soon)
    # Retiring inside an Open Season: that season is the final one, and its closing comes after the date.
    inside = [m["label"] for m in call("fill", "federal-retirement", "2027-11-30", "2026-10-26")["milestones"] if m["note"]]
    assert inside[-1] == "Final Open Season as an employee opens, plan year 2028"
    assert "Final Open Season as an employee closes" not in inside
    # The idea says what it adds before the reader picks a date; the general retirement idea adds none.
    steps = call("ideaById", "federal-retirement", "2026-10-26", "")["steps"]
    assert any("Open Season" in s for s in steps) and any("leave year" in s for s in steps)
    assert not [m for m in call("fill", "retirement", "2027-12-31", "2026-10-26")["milestones"] if m["note"]]


def test_saved_federal_retirement_countdowns_get_the_dates_once():
    saved = {"categories": [{"id": "federal-workforce"}], "countdowns": [
        {"label": "Days to retirement", "date": "2027-12-31", "idea": "federal-retirement", "milestones": [
            {"date": "2026-12-31", "label": "Ask HR for a retirement estimate"},
            {"date": "2026-12-14", "label": "open season closes", "note": "my own note"}]},
        {"label": "Days to retirement", "date": "2028-06-30", "milestones": []},
        {"label": "Days to retirement", "date": "2027-12-31", "idea": "retirement", "milestones": []},
        {"label": "Days to retirement", "date": "2026-01-01", "idea": "federal-retirement", "milestones": []},
        {"label": "Days to the trip", "date": "2027-03-01", "idea": "trip", "milestones": []}, "x"]}
    got = js_calls([{"fn": "I.addRuleDates", "args": [saved, "2026-10-26"]}])[0]
    assert got == 5 + 6, "five new dates on the first (one it had), six on the one saved without an idea"
    plain = dict(saved, categories=[{"id": "travel"}])
    assert js_calls([{"fn": "I.addRuleDates", "args": [plain, "2026-10-26"]}])[0] == 5, "no federal category: only the federal idea's"
    once = {"categories": [], "countdowns": [{"label": "Days to retirement", "date": "2027-12-31", "idea": "federal-retirement",
                                              "dates_added": True, "milestones": []}]}
    assert js_calls([{"fn": "I.addRuleDates", "args": [once, "2026-10-26"]}])[0] == 0, "a date the reader removed stays removed"
    assert js_calls([{"fn": "I.addRuleDates", "args": [None, "2026-10-26"]}, {"fn": "I.addRuleDates", "args": [saved, "bad"]}]) == [0, 0]


def test_no_idea_shows_twice():
    """Across every category, reader and time of year, an idea (by id or by name) shows
    once: in the ideas that fit, or in More ideas, never both and never twice."""
    from conftest import ROOT
    import json
    lib = json.loads((ROOT / "app" / "data" / "library.js").read_text().split("= ", 1)[1].rstrip().rstrip(";"))
    ids = [c["id"] for c in lib["categories"]]
    picks = [[i] for i in ids] + [ids, ["federal-retirement", "retirement-planning"], ["retirement-planning", "federal-retirement"],
                                  ["health-wellness", "retirement-planning", "local-weather"], []]
    dates = ["2026-%02d-15" % m for m in range(1, 13)] + ["2026-10-20", "2026-11-20", "2026-12-10", "2026-12-14", "2027-06-01"]
    readers = [{"region": "Florida"}, {"region": "Illinois"}]
    cases = [(p, d, r) for p in picks for d in dates for r in readers]
    first = js_calls([{"fn": "I.ideasFor", "args": [cats(*p), d, r, 99]} for p, d, r in cases])
    second = js_calls([{"fn": "I.moreIdeas", "args": [cats(*p), d, r, [i["id"] for i in f]]} for (p, d, r), f in zip(cases, first)])
    every = {i["id"] for i in call("moreIdeas", [], "2026-10-25", {}, [])}
    for (p, d, r), f, m in zip(cases, first, second):
        shown = f + m
        names = [i["label"].lower() for i in shown]
        assert len({i["id"] for i in shown}) == len(shown), (p, d, r, [i["id"] for i in shown])
        assert len(set(names)) == len(names), (p, d, r, names)
        # Every idea is reachable, except the second "Days to retirement".
        assert {i["id"] for i in shown} | {"retirement", "federal-retirement"} == every | {"retirement", "federal-retirement"}
        assert len({"retirement", "federal-retirement"} & {i["id"] for i in shown}) == 1


def test_a_countdown_saved_without_its_idea_still_belongs_to_it():
    got = js_calls([{"fn": "I.belongsTo", "args": [cd, idea]} for cd, idea in [
        ({"label": "Days to Federal Benefits Open Season", "date": "2026-11-09"}, "open-season"),
        ({"label": "days left in federal benefits open season ", "date": "2026-12-14"}, "open-season"),
        ({"label": "Days to retirement", "date": "2030-12-31"}, "federal-retirement"),
        ({"label": "Days to retirement", "date": "2030-12-31"}, "retirement"),
        ({"label": "Days to retirement", "date": "2030-12-31", "idea": "retirement"}, "federal-retirement"),
        ({"label": "Days to the reunion", "date": "2099-07-04"}, "trip"),
        ({"label": "", "date": "2026-11-03"}, "election"),
        (None, "election")]])
    assert got == [True, True, True, True, False, False, False, False]


def test_steps_that_assumed_eligibility_leave_saved_countdowns():
    saved = {"countdowns": [
        {"label": "Days to retirement", "date": "2027-12-31", "idea": "federal-retirement", "milestones": [
            {"date": "2026-12-31", "label": "Ask HR for a retirement estimate"},
            {"date": "2027-09-02", "label": "Apply for Social Security if it starts then (up to 4 months ahead)"},
            {"date": "2027-07-01", "label": "decide when to start social security and medicare "}]},
        {"label": "Days left in Federal Benefits Open Season", "date": "2026-12-14", "milestones": [
            {"date": "2026-12-07", "label": "Re-enroll in FSAFEDS if you use it (it does not carry over)"}, "x"]},
        {"label": "Mine", "date": "2027-01-01", "milestones": [{"date": "2026-12-01", "label": "Apply for Social Security, my own note"}]},
        "x"]}
    got = js_calls([{"fn": "I.dropRetiredSteps", "args": [saved]}])[0]
    assert got == 3
