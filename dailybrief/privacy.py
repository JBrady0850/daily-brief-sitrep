"""Finds personal data and secrets in files before they are published.

The built-in patterns catch email addresses, phone numbers and API keys. Keep
your own words (your name, town, employer) in a private file outside the
repository and pass it with --terms; that list is never committed.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "users.noreply.github.com")
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", "output", ".venv", "venv"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".js", ".json", ".html", ".css", ".yml", ".yaml", ".bat", ".sh",
                 ".command", ".webmanifest", ".svg", ".toml", ".cfg", ".ini", ""}

PATTERNS = [
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("phone number", re.compile(r"(?<![\d.])(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\d.])")),
    ("OpenAI or Anthropic key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("xAI key", re.compile(r"\bxai-[A-Za-z0-9]{20,}")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Google app password", re.compile(r"(?i)(?:app[ _-]?password|smtp_password)\s*[:=]\s*['\"]?[a-z]{4} ?[a-z]{4} ?[a-z]{4} ?[a-z]{4}\b")),
]


def load_terms(path: str) -> list:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if t and not t.startswith("#"):
            out.append(t)
    return out


def scan_text(text: str, terms: Iterable[str] = ()) -> list:
    """Returns [{line, kind, match}] for one text."""
    found = []
    lowered_terms = [(t, t.lower()) for t in terms if t]
    for n, line in enumerate(text.splitlines(), 1):
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                value = m.group(0)
                if kind == "email address" and value.lower().split("@")[-1].endswith(ALLOWED_EMAIL_DOMAINS):
                    continue
                found.append({"line": n, "kind": kind, "match": value})
        low = line.lower()
        for original, t in lowered_terms:
            if t in low:
                found.append({"line": n, "kind": "private term", "match": original})
    return found


def scan_tree(root: Path, terms: Iterable[str] = ()) -> list:
    terms = list(terms)
    out = []
    root = Path(root)
    paths = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    for p in paths:
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for f in scan_text(text, terms):
            f["file"] = str(p.relative_to(root) if root.is_dir() else p)
            out.append(f)
    return out
