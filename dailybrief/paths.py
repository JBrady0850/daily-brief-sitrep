"""Where the app, the prompts and your own data live."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
PROMPT_DIR = REPO_ROOT / "prompt"
EXAMPLES_DIR = REPO_ROOT / "examples"


def user_dir() -> Path:
    """Your settings, history and mail settings. Never inside the repository.

    Set DAILY_BRIEF_HOME to use another folder (the tests do).
    """
    env = os.environ.get("DAILY_BRIEF_HOME", "").strip()
    return Path(env).expanduser() if env else Path.home() / ".daily-brief"
