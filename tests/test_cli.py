"""Command line: validate, check, prompt, render, run and scan."""
import json
from pathlib import Path

import pytest

from conftest import ROOT, fresh_feed_bytes

from dailybrief import cli, collect, github_issue, store

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


def test_prompt_drops_an_old_email_block(tmp_path):
    cfg = json.loads((EX / "sample-settings.json").read_text())
    cfg["email"] = {"to": ["reader@example.org"], "from_name": "Pat Example"}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(cfg))
    for flag in ([], ["--compact"]):
        out = tmp_path / ("p%d.md" % len(flag))
        assert run("prompt", *flag, "--config", p, "-o", out) == 0
        text = out.read_text()
        assert "reader@example.org" not in text and "Pat Example" not in text and "Example City" in text


def test_render_writes_the_page_and_text_and_touches_nothing(tmp_path):
    assert run("render", EX / "sample-brief.json", "--out", tmp_path / "r") == 0
    assert sorted(p.suffix for p in (tmp_path / "r").iterdir()) == [".html", ".txt"]
    assert not store.path(store.LEDGER).exists()


def test_email_commands_are_gone(capsys):
    for args in (["send", EX / "sample-brief.json"], ["run", "--to", "a@example.com"]):
        with pytest.raises(SystemExit) as exc:
            run(*args)
        assert exc.value.code == 2  # argparse: unknown command or option
    err = capsys.readouterr().err
    assert "invalid choice: 'send'" in err and "unrecognized arguments: --to" in err


def _fake_news(monkeypatch):
    monkeypatch.setattr(collect, "fetch", lambda url, **kw: fresh_feed_bytes("google_news.xml" if "google" in url else "rss_feed.xml"))
    monkeypatch.setattr(collect, "GOOGLE_PAUSE", 0)
    store.save_config({"version": 1, "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'],
                                                     "require": [["zero trust", "VPN"]]}]})


def test_run_collects_saves_and_posts_the_issue(tmp_path, monkeypatch):
    _fake_news(monkeypatch)
    posted = []
    monkeypatch.setattr(github_issue, "post", lambda subject, body, prefix, s, opener=None: posted.append(subject) or {"number": 2, "url": "", "closed": 0})
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "me/brief")
    assert run("run", "--date", "2026-10-23", "--quiet", "--out", tmp_path / "o") == 0
    saved = json.loads((tmp_path / "o" / "brief-2026-10-23.json").read_text())
    assert saved["schema"] == "daily-brief/v1" and not posted
    assert sorted(p.name for p in (tmp_path / "o").iterdir()) == ["brief-2026-10-23.html", "brief-2026-10-23.json", "brief-2026-10-23.txt"]
    assert run("run", "--send", "--date", "2026-10-23", "--quiet", "--out", tmp_path / "o") == 0 and len(posted) == 1
    assert run("run", "--send", "--date", "2026-10-23", "--quiet") == 1 and len(posted) == 1  # once a day


def test_mark_read_keeps_tomorrows_page_free_of_repeats(tmp_path, monkeypatch):
    _fake_news(monkeypatch)
    assert run("run", "--mark-read", "--date", "2026-10-23", "--quiet", "--out", tmp_path / "a") == 0
    first = json.loads((tmp_path / "a" / "brief-2026-10-23.json").read_text())
    led = store.load_ledger()
    assert first["total"] > 0 and len(led["urls"]) == first["total"] and led["sent_dates"] == []
    assert run("run", "--date", "2026-10-24", "--quiet", "--out", tmp_path / "b") == 0
    second = json.loads((tmp_path / "b" / "brief-2026-10-24.json").read_text())
    assert second["total"] == 0 and second["withheld"] == first["total"]


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
