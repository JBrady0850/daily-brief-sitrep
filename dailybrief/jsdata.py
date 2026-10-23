"""Reads the JSON that the app's data files assign to window.NAME."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import APP_DIR


def load_js_json(path: Path, name: str) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    marker = "window." + name + " = "
    i = text.find(marker)
    j = text.rfind(";")
    if i < 0 or j < i:
        raise ValueError(f"{path} does not assign window.{name}")
    return json.loads(text[i + len(marker):j])


def write_js_json(path: Path, name: str, value: Any, header: str) -> str:
    body = json.dumps(value, indent=1, ensure_ascii=True)
    text = header.rstrip("\n") + "\n" + "window." + name + " = " + body + ";\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return text


def library() -> dict:
    return load_js_json(APP_DIR / "data" / "library.js", "DB_LIBRARY")
