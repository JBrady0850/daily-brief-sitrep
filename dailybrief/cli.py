"""Command line for the Daily Brief. Run ``python -m dailybrief --help``."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import assets, collect, engine as E, privacy, render, store
from .paths import EXAMPLES_DIR, PROMPT_DIR

OK, FAIL, USAGE = 0, 1, 2


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: str) -> object:
    try:
        return E.json_loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"File not found: {path}")
    except ValueError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}")


def _config(path: Optional[str]) -> dict:
    if path:
        cfg = _load(path)
    else:
        cfg = store.load_config()
        if cfg is None:
            raise SystemExit("No saved settings. Save them in the desktop app (Every day: Save my settings for scheduled runs) "
                             "or pass --config FILE.")
    v = E.validate_config(cfg)
    for w in v["warnings"]:
        print("warning:", w)
    if v["errors"]:
        for e in v["errors"]:
            print("error:", e)
        raise SystemExit(FAIL)
    return cfg  # type: ignore[return-value]


def _write_outputs(out: dict, folder: Path, stem: str) -> list:
    folder.mkdir(parents=True, exist_ok=True)
    files = []
    for ext, text in (("html", out["html"]), ("txt", out["text"])):
        p = folder / f"{stem}.{ext}"
        store.write_text(p, text)
        files.append(p)
    return files


def _deliver(brief: dict, cfg: Optional[dict]) -> tuple:
    """Posts the brief as a GitHub issue. Returns (what was delivered, problems)."""
    from . import github_issue
    from .markdown import render_markdown
    out = render.render(brief, cfg)
    n = E.normalize_config(cfg or {})
    gh = github_issue.settings()
    if not gh:
        return [], ["issue: no GITHUB_TOKEN here; delivery works inside GitHub Actions"]
    prefix = n["brief"]["subject"].split("{")[0] or n["brief"]["title"]
    try:
        r = github_issue.post(out["subject"], render_markdown(brief, cfg), prefix, gh)
    except github_issue.IssueError as exc:
        return [], [f"issue failed: {exc}"]
    return [f"GitHub issue #{r['number']}" + (f" (closed {r['closed']} older)" if r["closed"] else "")], []


def _summary(path: Optional[str], lines: list) -> None:
    """Appends a Markdown report to the GitHub Actions job summary, when asked."""
    if not path:
        return
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ commands
def cmd_serve(a: argparse.Namespace) -> int:
    from .server import serve
    return serve(a.port, not a.no_browser)


def cmd_run(a: argparse.Namespace) -> int:
    from . import schedule
    cfg = _config(a.config)
    n = E.normalize_config(cfg)
    report = ["### Daily Brief"]
    if not store.acquire_lock():
        print("Another Daily Brief run is in progress. Try again in a few minutes.")
        return FAIL
    try:
        ledger_path = None if a.no_history else store.path(store.LEDGER)
        ledger = store.load_ledger(ledger_path) if ledger_path else None
        now = datetime.now(timezone.utc)
        warnings = []
        if a.scheduled:
            d = schedule.decide(now, n["delivery"], ledger["sent_dates"] if ledger else [],
                                schedule.read_crons(a.workflow), a.fired)
            if d["warning"]:
                warnings.append(d["warning"])
            if not d["send"]:
                print("Skipped:", d["reason"])
                _summary(a.summary, report + ["Skipped: " + d["reason"] + "."] + ["> " + w for w in warnings])
                return OK
            day = a.date or d["date"]
        else:
            day = a.date or schedule.local_now(now, n["delivery"]["timezone"]).strftime("%Y-%m-%d")
            if a.send and ledger is not None and day in ledger["sent_dates"] and not a.force:
                print(f"A brief for {day} was already sent. Use --force to send another.")
                return FAIL

        def progress(label: str, done: int, total: int) -> None:
            if not a.quiet:
                print(f"  [{done}/{total}] {label}", flush=True)

        brief, health = collect.run_brief(cfg, now.strftime("%Y-%m-%dT%H:%M:%SZ"), day, ledger, progress=progress)
        problems = [(cid, q.get("query") or q.get("url"), q["error"]) for cid, h in health.items() if cid != "_weather"
                    for q in h["queries"] + h["feeds"] if q["error"]]
        if "_weather" in health:
            problems.append(("weather", "Open-Meteo forecast", health["_weather"]["error"]))
        for cid, what, err in problems:
            print(f"  source problem in {cid}: {what}: {err}")
        counts = f"{brief['total']} stories, {brief['empty']} empty categories, {brief['withheld']} withheld as already sent."
        print(counts)
        check_errors = E.check_brief(brief, cfg)["errors"]
        for e in check_errors:
            print("  check failed:", e)
        out_dir = Path(a.out) if a.out else store.path("briefs")
        out_dir.mkdir(parents=True, exist_ok=True)
        store.write_text(out_dir / f"brief-{day}.json", json.dumps(brief, indent=1, ensure_ascii=False) + "\n")
        files = _write_outputs(render.render(brief, cfg), out_dir, f"brief-{day}")
        print("Saved:", ", ".join(str(f) for f in files))
        report += ["**" + render.subject_line(brief, cfg) + "**", "", counts]
        if problems:
            report += ["", "Source problems:"] + [f"- {cid}: {err}" for cid, _, err in problems]
        if check_errors:
            report += ["", "The brief failed its check" + (" and was not sent:" if a.send else ":")] + [f"- {e}" for e in check_errors]
        code = OK
        if a.send and check_errors:
            print("Not sent: the brief failed its check.")
            code = FAIL
        elif a.send:
            delivered, failures = _deliver(brief, cfg)
            for x in delivered:
                print("Sent:", x)
            for x in failures:
                print(x)
            report += [""] + ["Delivered: " + x for x in delivered] + ["Not delivered: " + x for x in failures]
            if delivered and ledger is not None:
                store.update_ledger(lambda led: E.ledger_add(led, brief), ledger_path)
            code = OK if delivered else FAIL
        elif a.mark_read and ledger is not None and not check_errors:
            store.update_ledger(lambda led: E.ledger_add(led, brief, sent=False), ledger_path)
            print("Marked as read: these stories will not come back.")
        for w in warnings:
            print("warning:", w)
        _summary(a.summary, report + ["> " + w for w in warnings])
        return code
    finally:
        store.release_lock()


def cmd_render(a: argparse.Namespace) -> int:
    brief = _load(a.brief)
    cfg = _load(a.config) if a.config else None
    files = _write_outputs(render.render(brief, cfg), Path(a.out), Path(a.brief).stem)
    print("Wrote", ", ".join(str(f) for f in files))
    return OK


def cmd_check(a: argparse.Namespace) -> int:
    brief = _load(a.brief)
    cfg = _load(a.config) if a.config else None
    chk = E.check_brief(brief, cfg, _now_iso())
    for w in chk["warnings"]:
        print("warning:", w)
    for e in chk["errors"]:
        print("error:", e)
    print("OK" if not chk["errors"] else f"{len(chk['errors'])} error(s)")
    return FAIL if chk["errors"] else OK


def cmd_validate(a: argparse.Namespace) -> int:
    v = E.validate_config(_load(a.config))
    for w in v["warnings"]:
        print("warning:", w)
    for e in v["errors"]:
        print("error:", e)
    print("OK" if not v["errors"] else f"{len(v['errors'])} error(s)")
    return FAIL if v["errors"] else OK


def cmd_prompt(a: argparse.Namespace) -> int:
    name = "daily-brief-prompt-compact.md" if a.compact else "daily-brief-prompt.md"
    text = (PROMPT_DIR / name).read_text(encoding="utf-8")
    cfg = _config(a.config) if a.config else None
    if cfg is not None:
        cfg = {k: v for k, v in cfg.items() if k != "email"}  # older settings files may hold addresses; keep them out
    out = E.build_prompt(text, cfg, compact=a.compact)
    if a.out:
        store.write_text(Path(a.out), out)
        print(f"Wrote {a.out} ({len(out)} characters)")
    else:
        sys.stdout.write(out)
    return OK


def cmd_sample(a: argparse.Namespace) -> int:
    brief = _load(str(EXAMPLES_DIR / "sample-brief.json"))
    cfg = _load(str(EXAMPLES_DIR / "sample-settings.json"))
    files = _write_outputs(render.render(brief, cfg), Path(a.out), "sample-brief")
    print("Wrote", ", ".join(str(f) for f in files))
    return OK


def cmd_check_feeds(a: argparse.Namespace) -> int:
    from .jsdata import library
    cats = library()["categories"] if not a.config else E.normalize_config(_config(a.config))["categories"]
    now = E.parse_iso(_now_iso())
    bad = 0
    for c in cats:
        for url in c.get("feeds") or []:
            try:
                items = collect.parse_feed(collect.fetch(url))
                fresh = collect._fresh_count(items, now, 24)
                print(f"ok    {c['id']:<22} {len(items):>3} items, {fresh:>3} under 24h  {url}")
            except collect.FetchError as exc:
                bad += 1
                print(f"FAIL  {c['id']:<22} {exc}  {url}")
    print(f"{bad} feed(s) failed.")
    return FAIL if bad else OK


def cmd_build_cache(a: argparse.Namespace) -> int:
    """The backup collection the web page reads when the news index is busy."""
    from . import newscache
    data = newscache.build(_now_iso(), pause=a.pause)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(out)
    cats = data["categories"]
    empty = sorted(k for k, v in cats.items() if not v)
    src = data["sources"]
    print(f"Wrote {out}: {sum(len(v) for v in cats.values())} stories in {len(cats)} categories, {len(text)} bytes.")
    print(f"Searches: {src['searches']} ({src['searches_failed']} failed). Feeds: {src['feeds']} ({src['feeds_failed']} failed).")
    if empty:
        print("No stories for: " + ", ".join(empty))
    return OK if sum(len(v) for v in cats.values()) else FAIL


def cmd_scan(a: argparse.Namespace) -> int:
    terms = privacy.load_terms(a.terms) if a.terms else []
    findings = privacy.scan_tree(Path(a.path), terms)
    for f in findings:
        print(f"{f['file']}:{f['line']}: {f['kind']}: {f['match']}")
    print(f"{len(findings)} finding(s).")
    return FAIL if findings else OK


def cmd_build_assets(a: argparse.Namespace) -> int:
    changed = assets.build(check=a.check)
    if a.check:
        for c in changed:
            print("out of date:", c)
        print("OK" if not changed else "Run: python -m dailybrief build-assets")
        return FAIL if changed else OK
    print("Updated:", ", ".join(changed) if changed else "nothing (already current)")
    return OK


def cmd_schedule_help(a: argparse.Namespace) -> int:
    py = sys.executable
    root = Path(__file__).resolve().parents[1]
    hh, mm = a.time.split(":")
    print("Collect the brief every day at", a.time, "and save the newsletter page in your data folder.")
    print("Pick the lines for your system.\n")
    print("Windows (Command Prompt):")
    print(f'  schtasks /Create /SC DAILY /ST {a.time} /TN "Daily Brief" /TR "\\"{py}\\" -m dailybrief run --mark-read --quiet" /F')
    print(f"  (the task runs in {root}; set Start in to that folder in Task Scheduler if it cannot find dailybrief)\n")
    print("macOS or Linux (crontab -e):")
    print(f"  {int(mm)} {int(hh)} * * * cd \"{root}\" && \"{py}\" -m dailybrief run --mark-read --quiet\n")
    print("The computer must be on at that time. The page lands in the briefs folder of your data folder.")
    print("For delivery with no computer on, use a GitHub copy: see docs/GITHUB-CLOUD.md.")
    return OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m dailybrief", description="Daily Brief: configurable news SITREP and newsletter.")
    p.add_argument("--version", action="version", version=E.VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="open the desktop app in your browser")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--no-browser", action="store_true")
    s.set_defaults(func=cmd_serve)

    s = sub.add_parser("run", help="collect today's news, save the brief, and optionally post it as a GitHub issue")
    s.add_argument("--config", help="settings JSON (default: the settings saved by the desktop app)")
    s.add_argument("--send", action="store_true", help="post the brief as a GitHub issue (inside GitHub Actions)")
    s.add_argument("--mark-read", action="store_true", help="remember the stories so they do not come back (for runs on this computer)")
    s.add_argument("--out", help="folder for the brief files (default: your data folder)")
    s.add_argument("--date", help="edition date, YYYY-MM-DD (default: today)")
    s.add_argument("--no-history", action="store_true", help="ignore and do not update the no-repeat history")
    s.add_argument("--force", action="store_true", help="send even if today's brief was already sent")
    s.add_argument("--quiet", action="store_true")
    s.add_argument("--scheduled", action="store_true", help="send only at the delivery time in the settings (for scheduled runs)")
    s.add_argument("--fired", help="the cron line that started this run (GitHub sets github.event.schedule)")
    s.add_argument("--workflow", default=".github/workflows/daily-brief.yml", help="workflow file holding the cron lines")
    s.add_argument("--summary", help="append a Markdown report to this file (GitHub's job summary)")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("render", help="turn a brief JSON into the newsletter page and plain text")
    s.add_argument("brief")
    s.add_argument("--config")
    s.add_argument("--out", default="output")
    s.set_defaults(func=cmd_render)

    s = sub.add_parser("check", help="check a brief JSON against the rules")
    s.add_argument("brief")
    s.add_argument("--config")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("validate", help="check a settings JSON")
    s.add_argument("config")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("prompt", help="print the AI prompt, with your settings built in")
    s.add_argument("--config")
    s.add_argument("--compact", action="store_true", help="the short version for size-limited instruction boxes")
    s.add_argument("-o", "--out")
    s.set_defaults(func=cmd_prompt)

    s = sub.add_parser("sample", help="render the sample brief")
    s.add_argument("--out", default="output")
    s.set_defaults(func=cmd_sample)

    s = sub.add_parser("check-feeds", help="test every publisher feed in the library (needs internet)")
    s.add_argument("--config")
    s.set_defaults(func=cmd_check_feeds)

    s = sub.add_parser("build-cache", help="collect the backup news file the web page reads (needs internet)")
    s.add_argument("--out", default="app/data/news-cache.json", help="where to write it")
    s.add_argument("--pause", type=float, default=collect.GOOGLE_PAUSE, help="seconds between Google News requests")
    s.set_defaults(func=cmd_build_cache)

    s = sub.add_parser("scan", help="look for personal data and secrets before you publish")
    s.add_argument("path", nargs="?", default=".")
    s.add_argument("--terms", help="a private file of words that must not appear (one per line)")
    s.set_defaults(func=cmd_scan)

    s = sub.add_parser("build-assets", help="rebuild the generated app and prompt files")
    s.add_argument("--check", action="store_true")
    s.set_defaults(func=cmd_build_assets)

    s = sub.add_parser("schedule-help", help="print the command that collects the brief every morning on this computer")
    s.add_argument("--time", default="06:00")
    s.set_defaults(func=cmd_schedule_help)
    return p


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code)
        return FAIL
