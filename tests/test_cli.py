"""Command line: validate, check, prompt, render, send, run and scan."""
import json
from pathlib import Path

from conftest import ROOT, feed_bytes

from dailybrief import cli, collect, mailer, store

EX = ROOT / "examples"


def run(*args):
    return cli.main([str(a) for a in args])


def test_validate_and_check(capsys, tmp_path):
    assert run("validate", EX / "sample-settings.json") == 0
    assert run("check", EX / "sample-brief.json", "--config", EX / "sample-settings.json") == 0
    bad = json.loads((EX / "sample-brief.json").read_text())
    bad["categories"][0]["items"][0]["url"] = "ftp://example.com/x"
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    assert run("check", p) == 1
    assert "needs an http or https link" in capsys.readouterr().out


def test_prompt_with_settings(tmp_path):
    out = tmp_path / "p.md"
    assert run("prompt", "--compact", "--config", EX / "sample-settings.json", "-o", out) == 0
    text = out.read_text()
    assert '"location":"Example City"' in text and "START" in text
    assert len(text) < 12000, "the compact prompt keeps its settings on one line"


def test_prompt_never_carries_an_email_address(tmp_path):
    cfg = json.loads((EX / "sample-settings.json").read_text())
    cfg["email"] = {"to": ["reader@example.org"], "from_name": "Pat Example"}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(cfg))
    for flag in ([], ["--compact"]):
        out = tmp_path / ("p%d.md" % len(flag))
        assert run("prompt", *flag, "--config", p, "-o", out) == 0
        text = out.read_text()
        assert "reader@example.org" not in text and "Pat Example" not in text and "Example City" in text


def test_render_and_dry_run_send_touch_nothing(tmp_path):
    assert run("render", EX / "sample-brief.json", "--out", tmp_path / "r") == 0
    assert sorted(p.suffix for p in (tmp_path / "r").iterdir()) == [".eml", ".html", ".txt"]
    assert run("send", EX / "sample-brief.json", "--dry-run", "--out", tmp_path / "d") == 0
    assert not store.path(store.LEDGER).exists()


def test_send_once_per_day_and_history(tmp_path, monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send", lambda msg, s, **kw: sent.append(msg["Subject"]))
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "me@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setenv("MAIL_TO", "a@example.com")
    brief = json.loads((EX / "sample-brief.json").read_text())
    brief["source"] = "ai"
    p = tmp_path / "ai.json"
    p.write_text(json.dumps(brief))
    assert run("send", p) == 0 and len(sent) == 1
    assert store.load_ledger()["sent_dates"] == ["2026-10-23"]
    assert run("send", p) == 1 and len(sent) == 1  # the same day is not sent twice
    assert run("send", p, "--force") == 0 and len(sent) == 2


def test_run_collects_saves_and_sends(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "fetch", lambda url, **kw: feed_bytes("google_news.xml" if "google" in url else "rss_feed.xml"))
    monkeypatch.setattr(collect, "GOOGLE_PAUSE", 0)
    sent = []
    monkeypatch.setattr(mailer, "send", lambda msg, s, **kw: sent.append(msg["Subject"]))
    for k, v in {"SMTP_HOST": "smtp.example.com", "SMTP_USER": "me@example.com", "SMTP_PASSWORD": "x", "MAIL_TO": "a@example.com"}.items():
        monkeypatch.setenv(k, v)
    cfg = {"version": 1, "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'], "require": [["zero trust", "VPN"]]}]}
    store.save_config(cfg)
    assert run("run", "--date", "2026-10-23", "--quiet", "--out", tmp_path / "o") == 0
    saved = json.loads((tmp_path / "o" / "brief-2026-10-23.json").read_text())
    assert saved["schema"] == "daily-brief/v1" and not sent
    assert run("run", "--send", "--date", "2026-10-23", "--quiet", "--out", tmp_path / "o") == 0 and len(sent) == 1
    assert run("run", "--send", "--date", "2026-10-23", "--quiet") == 1 and len(sent) == 1


def test_run_refuses_while_another_run_holds_the_lock(capsys):
    store.save_config({"version": 1, "categories": [{"id": "a", "name": "A", "queries": ["a"]}]})
    assert store.acquire_lock()
    try:
        assert run("run", "--quiet") == 1
        assert "in progress" in capsys.readouterr().out
    finally:
        store.release_lock()


def test_scan_finds_planted_secrets_and_private_terms(tmp_path, capsys):
    d = tmp_path / "repo"
    d.mkdir()
    (d / "ok.md").write_text("Contact you@example.com for help.\n")
    assert run("scan", d) == 0
    # Built at run time so this test file itself stays clean for the repository scan.
    leak = "mail me at someone" + "@" + "realmail.test or 555-555" + "-0199\nkey sk-" + "ant-abcdefghijklmnopqrstuvwxyz\n"
    (d / "leak.md").write_text(leak)
    terms = tmp_path / "terms.txt"
    terms.write_text("# private words\nHometownville\n")
    (d / "town.txt").write_text("Greetings from hometownville\n")
    assert run("scan", d, "--terms", terms) == 1
    out = capsys.readouterr().out
    assert "email address" in out and "phone number" in out and "Anthropic key" in out and "private term" in out


def test_build_assets_current_and_schedule_help(capsys):
    assert run("build-assets", "--check") == 0
    assert run("schedule-help", "--time", "06:15") == 0
    out = capsys.readouterr().out
    assert "schtasks /Create /SC DAILY /ST 06:15" in out and "15 6 * * *" in out


def test_sample_files(tmp_path):
    assert run("sample", "--out", tmp_path) == 0
    assert (Path(tmp_path) / "sample-brief.html").read_text().startswith("<!doctype html>")
