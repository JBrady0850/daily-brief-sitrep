import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT))

NODE = shutil.which("node")


def load(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


@pytest.fixture
def sample_brief():
    return load("sample-brief.json")


@pytest.fixture
def sample_settings():
    return load("sample-settings.json")


@pytest.fixture(autouse=True)
def private_home(tmp_path, monkeypatch):
    """Every test gets its own empty data folder and no mail variables."""
    home = tmp_path / "home"
    monkeypatch.setenv("DAILY_BRIEF_HOME", str(home))
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_SECURITY", "MAIL_FROM", "MAIL_TO"):
        monkeypatch.delenv(k, raising=False)
    return home


def js_calls(requests):
    """Runs engine or newsletter functions in Node; returns their values."""
    if not NODE:
        if os.environ.get("REQUIRE_NODE"):
            raise RuntimeError("node is required for the parity tests")
        pytest.skip("node is not installed")
    res = subprocess.run([NODE, str(ROOT / "tests" / "js_bridge.js")], input=json.dumps(requests),
                         capture_output=True, text=True, encoding="utf-8", check=True)
    out = json.loads(res.stdout)
    for r in out:
        if "error" in r:
            raise AssertionError("JavaScript error: " + r["error"])
    return [r["value"] for r in out]


def feed_bytes(name):
    return (FIX / name).read_bytes()
