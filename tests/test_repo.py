"""Repository hygiene: files the app needs exist, versions agree, generated
files are current, colours are readable, and nothing personal is committed."""
import json
import re

from conftest import ROOT

from dailybrief import assets, engine as E, privacy
from dailybrief.jsdata import library, load_js_json

APP = ROOT / "app"
TEXT = {".md", ".py", ".js", ".json", ".html", ".css", ".yml", ".txt", ".webmanifest", ".svg", ".bat", ".sh", ".command"}


def repo_files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and not any(x in p.parts for x in (".git", "__pycache__", ".pytest_cache", "output")):
            yield p


def test_index_references_existing_files():
    html = (APP / "index.html").read_text()
    refs = re.findall(r'(?:src|href)="([^"#:]+)"', html)
    assert refs, "no references found"
    for r in refs:
        assert (APP / r).exists(), r


def test_offline_file_list_exists_and_version_matches():
    sw = (APP / "sw.js").read_text()
    files = json.loads("[" + re.search(r"const FILES = \[([\s\S]*?)\];", sw).group(1) + "]")
    for f in files:
        assert f == "./" or (APP / f).exists(), f
    for f in ["js/" + p.name for p in (APP / "js").glob("*.js")] + ["data/" + p.name for p in (APP / "data").glob("*.js")]:
        assert f in files, f + " is missing from the offline list"
    assert 'const VERSION = "db-v' + E.VERSION + '"' in sw
    assert 'const VERSION = "' + E.VERSION + '"' in (APP / "js" / "engine.js").read_text()
    assert "## " + E.VERSION in (ROOT / "CHANGELOG.md").read_text()


def test_generated_files_are_current():
    assert assets.build(check=True) == []


def test_no_em_dashes_anywhere():
    bad = []
    for p in repo_files():
        if p.suffix in TEXT and "\u2014" in p.read_text(encoding="utf-8"):
            bad.append(str(p.relative_to(ROOT)))
    assert bad == []


def test_json_files_parse():
    for p in repo_files():
        if p.suffix in (".json", ".webmanifest"):
            json.loads(p.read_text(encoding="utf-8"))


def test_prompts_fit_and_carry_their_markers():
    full = (ROOT / "prompt" / "daily-brief-prompt.md").read_text()
    compact = (ROOT / "prompt" / "daily-brief-prompt-compact.md").read_text()
    for text in (full, compact):
        assert "<!-- CONFIG:BEGIN -->" in text and "<!-- CONFIG:END -->" in text
        for cmd in ("START", "RUN", "UPDATE", "JSON", "SHOW SETTINGS", "HELP"):
            assert cmd in text, cmd
        assert "No web search" in text or "No web search tool" in text
    assert len(E.build_prompt(compact, "file")) <= 7000, "keep room under the 8,000-character GPT limit"
    for sec in ("## 1.", "## 2.", "## 3.", "## 4.", "## 5.", "## 6.", "## 7.", "## 8.", "## 9."):
        assert sec in full
    lib = library()
    assert all("`" + c["id"] + "`" in full for c in lib["categories"])


def _lum(hexcolor):
    def ch(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_white_text_on_every_colour_meets_wcag_aa():
    lib = library()
    colours = set(E.PALETTE) | {c["color"] for c in lib["categories"]}
    css = (APP / "js" / "newsletter.js").read_text()
    for cls in ("f1", "f2", "f3", "old", "ref", "ms-hot", "ms-warm", "ms-cool"):
        colours.add(re.search(r"span\." + re.escape(cls) + r"\{background:(#[0-9a-f]{6})", css).group(1))
    for c in sorted(colours):
        assert contrast(c, "#ffffff") >= 4.5, c


def test_library_is_complete_and_valid():
    lib = library()
    ids = [c["id"] for c in lib["categories"]]
    assert len(ids) == len(set(ids)) == 67
    for need in ("severe-weather", "weather-outlook", "local-weather", "nfl", "nba", "mlb", "nhl", "soccer", "golf",
                 "movies", "tv-streaming", "music", "space", "food-dining", "pets"):
        assert need in ids, need
    icons = load_js_json(ROOT / "app" / "data" / "icons.js", "DB_ICONS")["icons"]
    for c in lib["categories"]:
        assert c["icon"] in icons, (c["id"], c["icon"])
    groups = {g["id"] for g in lib["groups"]}
    for c in lib["categories"]:
        assert c["group"] in groups
        cfg = {"version": 1, "reader": {"location": "Springfield"}, "categories": [E.category_from_library(lib, c["id"])]}
        assert E.validate_config(cfg)["errors"] == [], c["id"]
    for p in lib["packs"]:
        assert all(i in ids for i in p["categories"])


def test_no_personal_data_or_secrets_committed():
    findings = privacy.scan_tree(ROOT)
    assert findings == [], findings


def test_start_scripts():
    assert (ROOT / "Start-Windows.bat").read_bytes().count(b"\r\n") >= 5
    for name in ("Start-Mac.command", "start-linux.sh"):
        assert b"\r\n" not in (ROOT / name).read_bytes()
        assert (ROOT / name).read_text().startswith("#!/bin/sh")


def test_icon_file_matches_its_source():
    import importlib.util
    spec = importlib.util.spec_from_file_location("icons_source", ROOT / "tools" / "icons_source.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert load_js_json(ROOT / "app" / "data" / "icons.js", "DB_ICONS") == mod.data(), "run: python tools/icons_source.py"


def test_every_document_link_resolves():
    for md in [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "CHANGELOG.md"] + sorted((ROOT / "docs").glob("*.md")):
        for target in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            assert (md.parent / target).exists(), (md.name, target)


def test_install_identity_is_this_app_only():
    """Browsers resolve a manifest id against the site's origin, not the app's folder,
    so "./" would claim the whole of jbrady0850.github.io and clash with any other
    app installed from that site ("already installed")."""
    m = json.loads((APP / "manifest.webmanifest").read_text())
    assert m["id"] == "/daily-brief-sitrep/" and m["start_url"] == "./" and m["scope"] == "./"
