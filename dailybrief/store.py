"""Your saved settings and no-repeat history, kept in user_dir().

Every write goes to a temporary file first and then replaces the old file, so a
crash or a full disk can never leave half a file behind.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from . import engine as E
from .paths import user_dir

CONFIG = "config.json"
LEDGER = "ledger.json"
OLD_SMTP = "smtp.json"  # mail settings from version 0.1.0; no longer read
LOCK = "run.lock"


def write_text(p: Path, text: str) -> None:
    """Writes text with LF line endings (Path.write_text(newline=) needs Python 3.10)."""
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def path(name: str) -> Path:
    return user_dir() / name


def read_json(p: Path, default: Any = None) -> Any:
    try:
        return E.json_loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Could not read {p}: {exc}") from exc


def write_json(p: Path, value: Any, private: bool = False) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    data = json.dumps(value, indent=1, ensure_ascii=False) + "\n"
    try:
        tmp.unlink()  # a leftover file would keep its old permissions
    except FileNotFoundError:
        pass
    # A private file is owner-only from the moment it exists, before anything is written to it.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)  # O_BINARY: no CRLF on Windows
    fd = os.open(str(tmp), flags, 0o600 if private else 0o666)
    with open(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)


def load_config(p: Optional[Path] = None) -> Optional[dict]:
    return read_json(p or path(CONFIG), None)


def save_config(cfg: dict, p: Optional[Path] = None) -> None:
    write_json(p or path(CONFIG), cfg)


def load_ledger(p: Optional[Path] = None) -> dict:
    return E.clean_ledger(read_json(p or path(LEDGER), None))


def save_ledger(ledger: dict, p: Optional[Path] = None) -> None:
    write_json(p or path(LEDGER), E.clean_ledger(ledger))


_LEDGER_MUTEX = threading.Lock()


def update_ledger(change: Callable[[dict], dict], p: Optional[Path] = None, wait: float = 15.0) -> dict:
    """Reads, changes and writes the no-repeat history under a lock, so the desktop
    app and a scheduled run never lose each other's entries."""
    target = Path(p or path(LEDGER))
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = target.with_name(target.name + ".lock")
    with _LEDGER_MUTEX:
        deadline = time.time() + wait
        while True:
            try:
                os.close(os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                break
            except FileExistsError:
                try:
                    if time.time() - lock.stat().st_mtime > 120:
                        lock.unlink()
                        continue
                except OSError:
                    pass
                if time.time() > deadline:
                    raise RuntimeError("The no-repeat history is busy. Try again in a moment.")
                time.sleep(0.05)
        try:
            ledger = change(load_ledger(target))
            save_ledger(ledger, target)
            return ledger
        finally:
            try:
                lock.unlink()
            except OSError:
                pass


def acquire_lock(stale_seconds: int = 1800) -> bool:
    """One run at a time. A lock older than stale_seconds is taken over."""
    p = path(LOCK)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            if time.time() - p.stat().st_mtime > stale_seconds:
                p.unlink()
                return acquire_lock(stale_seconds)
        except OSError:
            pass
        return False
    with os.fdopen(fd, "w") as fh:
        fh.write(str(os.getpid()))
    return True


def release_lock() -> None:
    try:
        path(LOCK).unlink()
    except OSError:
        pass
