"""The GitHub cloud run: the delivery-time gate, the issue channel, the
Markdown brief and the workflow file."""
import json
import re
from datetime import datetime, timezone

import pytest
from conftest import ROOT, feed_bytes

from dailybrief import cli, collect, github_issue, mailer, schedule as S, store
from dailybrief.markdown import md, render_markdown

WF = (ROOT / ".github" / "workflows" / "daily-brief.yml").read_text()
EASTERN = {"time": "06:15", "timezone": "America/New_York"}
CRONS = S.parse_crons(WF)

needs_tz = pytest.mark.skipif(S.zone("America/New_York") is None, reason="no time zone data on this computer")


def utc(y, mo, d, h, mi):
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)


def test_workflow_crons_are_the_two_eastern_lines():
    assert CRONS == [(10, 15), (11, 15)]


@needs_tz
def test_crons_for_time_zones():
    assert S.crons_for("06:15", "America/New_York", 2026) == ["15 10 * * *", "15 11 * * *"]
    assert S.crons_for("06:15", "America/Phoenix", 2026) == ["15 13 * * *"]
    assert S.crons_for("07:30", "Europe/London", 2026) == ["30 6 * * *", "30 7 * * *"]


@needs_tz
def test_summer_sends_on_the_first_run_and_skips_the_second():
    first = S.decide(utc(2026, 7, 10, 10, 21), EASTERN, [], CRONS, "15 10 * * *")
    assert first["send"] and first["date"] == "2026-07-10" and not first["warning"]
    second = S.decide(utc(2026, 7, 10, 11, 20), EASTERN, ["2026-07-10"], CRONS, "15 11 * * *")
    assert not second["send"] and "already sent" in second["reason"]


@needs_tz
def test_winter_waits_for_the_second_run():
    first = S.decide(utc(2026, 1, 12, 10, 16), EASTERN, [], CRONS, "15 10 * * *")
    assert not first["send"] and "not yet 06:15" in first["reason"]
    second = S.decide(utc(2026, 1, 12, 11, 17), EASTERN, [], CRONS, "15 11 * * *")
    assert second["send"] and second["date"] == "2026-01-12"


@needs_tz
def test_wrong_cron_lines_still_deliver_on_the_last_run():
    pacific = {"time": "06:15", "timezone": "America/Los_Angeles"}
    early = S.decide(utc(2026, 7, 10, 10, 15), pacific, [], CRONS, "15 10 * * *")
    assert not early["send"]
    last = S.decide(utc(2026, 7, 10, 11, 15), pacific, [], CRONS, "15 11 * * *")
    assert last["send"] and "Update the cron lines" in last["warning"]


@needs_tz
def test_late_runs_still_send_with_a_warning():
    late = S.decide(utc(2026, 7, 10, 14, 40), EASTERN, [], CRONS, "15 10 * * *")
    assert late["send"] and "after the 06:15 delivery time" in late["warning"]


def test_unknown_zone_and_no_time():
    assert S.decide(utc(2026, 7, 10, 11, 0), {"time": "06:15", "timezone": "Mars/Base"}, [], CRONS)["send"]
    assert S.decide(utc(2026, 7, 10, 11, 0), {"time": "", "timezone": ""}, [], CRONS)["send"]


def test_markdown_brief_escapes_feed_text(sample_brief, sample_settings):
    b = dict(sample_brief)
    text = render_markdown(b, sample_settings)
    assert text.startswith("# The Morning Brief") and "## [T1] Markets and the Economy (3 fresh)" in text
    assert "`REFERENCE, undated`" in text and "`OLDER, 1d 16h ago`" in text
    assert md("<b>x</b> [y](javascript:z) @octocat") == "\\<b\\>x\\</b\\> \\[y\\]\\(javascript:z\\) @" + chr(0x200B) + "octocat"


class FakeGitHub:
    def __init__(self):
        self.calls = []

    def __call__(self, req):
        body = json.loads(req.data.decode()) if req.data else None
        self.calls.append((req.get_method(), req.full_url, body, req.headers.get("Authorization")))
        if req.get_method() == "POST":
            return json.dumps({"number": 9, "html_url": "https://github.com/me/brief/issues/9"}).encode()
        if req.get_method() == "GET":
            return json.dumps([{"number": 9, "title": "Daily Brief - 3-Item SITREP | 2026-10-23"},
                               {"number": 8, "title": "Daily Brief - 5-Item SITREP | 2026-10-22"},
                               {"number": 3, "title": "A question from a person"}]).encode()
        return b"{}"


def test_issue_channel_opens_today_and_closes_yesterday():
    gh = github_issue.settings({"GITHUB_TOKEN": "t0k", "GITHUB_REPOSITORY": "me/brief"})
    fake = FakeGitHub()
    r = github_issue.post("Daily Brief - 3-Item SITREP | 2026-10-23", "# Brief\n", "Daily Brief - ", gh, opener=fake)
    assert r == {"number": 9, "url": "https://github.com/me/brief/issues/9", "closed": 1}
    post = fake.calls[0]
    assert post[0] == "POST" and post[1].endswith("/repos/me/brief/issues") and post[3] == "Bearer t0k"
    assert post[2]["body"].rstrip().endswith("@me")
    assert ("PATCH", "https://api.github.com/repos/me/brief/issues/8", {"state": "closed", "state_reason": "completed"}, "Bearer t0k") in fake.calls
    assert not any(c[1].endswith("/issues/3") for c in fake.calls)
    assert github_issue.settings({}) is None


def test_scheduled_run_skips_before_time_and_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "fetch", lambda url, **kw: feed_bytes("google_news.xml"))
    cfg = {"version": 1, "delivery": {"time": "23:59", "timezone": "", "channels": ["issue"]},
           "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'], "require": [["zero trust", "VPN"]]}]}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(cfg))
    wf = tmp_path / "wf.yml"
    wf.write_text('    - cron: "59 23 * * *"\n')
    summary = tmp_path / "summary.md"
    now = datetime.now().astimezone()
    if now.hour == 23 and now.minute == 59:
        pytest.skip("the clock is at the delivery minute")
    code = cli.main(["run", "--config", str(p), "--send", "--scheduled", "--fired", "0 0 * * *", "--workflow", str(wf),
                     "--summary", str(summary), "--quiet", "--out", str(tmp_path / "o")])
    assert code == 0 and "Skipped: not yet 23:59" in summary.read_text()


def test_run_delivers_by_issue_and_records_history(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "fetch", lambda url, **kw: feed_bytes("google_news.xml"))
    posted = []
    monkeypatch.setattr(github_issue, "post", lambda subject, body, prefix, s, opener=None: posted.append((subject, prefix)) or {"number": 4, "url": "", "closed": 0})
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "me/brief")
    cfg = {"version": 1, "delivery": {"time": "", "timezone": "", "channels": ["issue", "email"]},
           "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'], "require": [["zero trust", "VPN"]]}]}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(cfg))
    summary = tmp_path / "summary.md"
    code = cli.main(["run", "--config", str(p), "--send", "--quiet", "--out", str(tmp_path / "o"), "--summary", str(summary),
                     "--date", "2026-10-23"])
    text = summary.read_text()
    assert code == 0 and posted and posted[0][1] == "Daily Brief - "
    assert "Delivered: GitHub issue #4" in text and "Not delivered: email: Mail is not set up" in text
    assert store.load_ledger()["sent_dates"] == ["2026-10-23"]


def test_run_fails_when_no_channel_delivers(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "fetch", lambda url, **kw: feed_bytes("google_news.xml"))
    cfg = {"version": 1, "categories": [{"id": "net", "name": "Network", "queries": ["x"], "require": [["VPN"]]}]}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(cfg))
    assert cli.main(["run", "--config", str(p), "--send", "--quiet", "--out", str(tmp_path / "o")]) == 1
    assert store.load_ledger()["sent_dates"] == []


def test_workflow_matches_the_code():
    for name in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_SECURITY", "MAIL_FROM", "MAIL_TO"):
        assert f"{name}: ${{{{ secrets.{name} }}}}" in WF, name
        assert name in mailer.__doc__
    assert "issues: write" in WF and "contents: read" in WF
    for action in ("actions/checkout@v7", "actions/setup-python@v7", "actions/cache/restore@v6", "actions/cache/save@v6",
                   "actions/upload-artifact@v7"):
        assert action in WF, action
    assert "daily-brief-settings.json" in WF and "--scheduled --fired" in WF
    assert re.search(r"cron: \"\d+ \d+ \* \* \*\"", WF)
    assert not re.search(r"cron: \"0 ", WF), "avoid the top of the hour"


def test_run_does_not_send_a_brief_that_fails_its_check(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "fetch", lambda url, **kw: feed_bytes("google_news.xml"))
    monkeypatch.setattr(cli.E, "check_brief", lambda b, c=None, n=None: {"errors": ["planted defect"], "warnings": []})
    posted = []
    monkeypatch.setattr(github_issue, "post", lambda *a, **k: posted.append(a) or {"number": 1, "url": "", "closed": 0})
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "me/brief")
    cfg = {"version": 1, "delivery": {"time": "", "timezone": "", "channels": ["issue"]},
           "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'], "require": [["zero trust", "VPN"]]}]}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(cfg))
    summary = tmp_path / "summary.md"
    code = cli.main(["run", "--config", str(p), "--send", "--quiet", "--out", str(tmp_path / "o"), "--summary", str(summary)])
    assert code == 1 and not posted
    assert "failed its check and was not sent" in summary.read_text() and "planted defect" in summary.read_text()
    assert store.load_ledger()["sent_dates"] == []
