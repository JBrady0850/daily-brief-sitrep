"""The desktop app: serves the Daily Brief app on this computer only and adds
what a web page cannot do on its own: read news feeds, keep the no-repeat
history on disk, and send the email.

    python -m dailybrief serve              # opens the app in your browser
    python -m dailybrief serve --port 8766 --no-browser

Safety: the server listens on 127.0.0.1 only, answers only requests addressed
to 127.0.0.1 or localhost, and every /api call must carry the random key that
this run writes into the page it serves. Another web site open in your browser
cannot read the key, so it cannot use the app or send mail through it.
"""
from __future__ import annotations

import http.server
import json
import secrets
import socket
import threading
import uuid
import webbrowser
from datetime import datetime, timezone
from functools import partial
from typing import Any, Callable, Optional
from urllib.parse import urlsplit

from . import collect, engine as E, mailer, render, store
from .paths import APP_DIR

MAX_BODY = 4_000_000


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


class Jobs:
    """Runs one news collection at a time in the background."""

    def __init__(self, fetcher: Optional[Callable[[str], bytes]] = None, pause: float = collect.GOOGLE_PAUSE):
        self.fetcher = fetcher
        self.pause = pause
        self.jobs: dict = {}
        self.lock = threading.Lock()

    def start(self, cfg: dict, use_ledger: bool) -> str:
        with self.lock:
            for j in self.jobs.values():
                if j["state"] == "running":
                    return j["id"]
            jid = uuid.uuid4().hex[:12]
            job = {"id": jid, "state": "running", "done": 0, "total": 0, "step": "Starting", "brief": None,
                   "health": None, "error": "", "started": now_iso()}
            self.jobs = {k: v for k, v in self.jobs.items() if v["state"] == "running"}
            self.jobs[jid] = job
        threading.Thread(target=self._run, args=(job, cfg, use_ledger), daemon=True).start()
        return jid

    def _run(self, job: dict, cfg: dict, use_ledger: bool) -> None:
        def progress(label: str, done: int, total: int) -> None:
            job.update(step=label, done=done, total=total)
        try:
            ledger = store.load_ledger() if use_ledger else None
            brief, health = collect.run_brief(cfg, now_iso(), local_date(), ledger, self.fetcher, progress, self.pause)
            job.update(brief=brief, health=health, state="done", step="Done")
        except Exception as exc:  # reported to the app, never raised into the server
            job.update(state="error", error=type(exc).__name__ + ": " + str(exc))

    def get(self, jid: str) -> Optional[dict]:
        return self.jobs.get(jid)


class Handler(http.server.SimpleHTTPRequestHandler):
    server_version = "DailyBrief"
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript",
                      ".webmanifest": "application/manifest+json", ".svg": "image/svg+xml"}

    def __init__(self, *args: Any, app: "DesktopApp", **kwargs: Any) -> None:
        self.app = app
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def log_message(self, *args: Any) -> None:  # keep the console readable
        pass

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        super().end_headers()

    # ------------------------------------------------------------ checks
    def _host_ok(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        port = self.server.server_address[1]
        return origin in (f"http://127.0.0.1:{port}", f"http://localhost:{port}")

    def _json(self, code: int, value: Any) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _guard(self) -> bool:
        if not self._host_ok() or not self._origin_ok():
            self._json(403, {"error": "This app answers only on this computer."})
            return False
        if not secrets.compare_digest(self.headers.get("X-Brief-Key", ""), self.app.key):
            self._json(403, {"error": "Missing or wrong app key. Reload the page."})
            return False
        return True

    def _body(self) -> Any:
        if "application/json" not in self.headers.get("Content-Type", ""):
            raise ValueError("Send JSON.")
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("Request is too large.")
        return E.json_loads(self.rfile.read(length) or b"{}")

    # ------------------------------------------------------------ routes
    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            if self._guard():
                self._api_get(path)
            return
        if not self._host_ok():
            self.send_error(403)
            return
        if path in ("/", "/index.html"):
            html = (APP_DIR / "index.html").read_text(encoding="utf-8")
            html = html.replace('<meta name="db-key" content="">', f'<meta name="db-key" content="{self.app.key}">', 1)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path.startswith("/api/") or not self._host_ok():
            self.send_error(403)
            return
        super().do_HEAD()

    def list_directory(self, path: Any) -> None:  # no folder listings
        self.send_error(404)
        return None

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if not path.startswith("/api/"):
            self.send_error(404)
            return
        if not self._guard():
            return
        try:
            body = self._body()
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
            return
        try:
            self._api_post(path, body if isinstance(body, dict) else {})
        except mailer.MailConfigError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:  # report, never crash the server
            self._json(500, {"error": type(exc).__name__ + ": " + str(exc)})

    def _api_get(self, path: str) -> None:
        if path == "/api/health":
            ledger = store.load_ledger()
            self._json(200, {"ok": True, "mode": "desktop", "version": E.VERSION, "mail": mailer.public_settings(),
                             "ledger_size": E.ledger_size(ledger), "sent_dates": ledger["sent_dates"][-14:],
                             "has_config": store.load_config() is not None, "data_folder": str(store.path(""))})
        elif path == "/api/config":
            self._json(200, {"config": store.load_config()})
        elif path.startswith("/api/run/"):
            job = self.app.jobs.get(path.rsplit("/", 1)[-1])
            self._json(200 if job else 404, job or {"error": "No such run."})
        elif path == "/api/mail":
            self._json(200, mailer.public_settings())
        else:
            self._json(404, {"error": "Unknown request."})

    def _api_post(self, path: str, body: dict) -> None:
        if path == "/api/config":
            cfg = body.get("config")
            v = E.validate_config(cfg)
            if not v["errors"]:
                store.save_config(cfg)
            self._json(200, {**v, "saved": not v["errors"]})
        elif path == "/api/run":
            cfg = body.get("config")
            v = E.validate_config(cfg)
            if v["errors"]:
                self._json(400, {"error": "Fix the settings first.", **v})
                return
            running = any(j["state"] == "running" for j in list(self.app.jobs.jobs.values()))
            jid = self.app.jobs.start(cfg, body.get("use_history", True) is not False)
            self._json(200, {"job": jid, "already_running": running})
        elif path == "/api/commit":
            brief = body.get("brief")
            chk = E.check_brief(brief, body.get("config"), now_iso())
            if chk["errors"]:
                self._json(400, {"error": "The brief has problems.", **chk})
                return
            # "Mark as read" remembers the stories but leaves the day's scheduled send in place.
            ledger = store.update_ledger(lambda led: E.ledger_add(led, brief, sent=False))
            self._json(200, {"ledger_size": E.ledger_size(ledger)})
        elif path == "/api/send":
            brief, cfg = body.get("brief"), body.get("config")
            chk = E.check_brief(brief, cfg, now_iso())
            if chk["errors"]:
                self._json(400, {"error": "The brief has problems.", **chk})
                return
            if not self.app.send_lock.acquire(blocking=False):
                self._json(409, {"error": "An email is already being sent. Wait for it to finish."})
                return
            try:
                real = brief.get("source") != "sample"
                day = brief.get("date")
                if real and body.get("force") is not True and day in store.load_ledger()["sent_dates"]:
                    self._json(409, {"error": f"The brief for {day} was already sent.", "already_sent": True})
                    return
                out = render.render(brief, cfg)
                n = E.normalize_config(cfg or {})
                to = mailer.split_addresses(body.get("to")) or None
                s = mailer.load_settings(to_override=to, from_name=n["email"].get("from_name", ""))
                mailer.send(mailer.build_message(out["subject"], out["text"], out["html"], s.sender, s.recipients,
                                                 s.from_name), s)
                size = None
                if real:
                    size = E.ledger_size(store.update_ledger(lambda led: E.ledger_add(led, brief)))
                self._json(200, {"sent": len(s.recipients), "subject": out["subject"], "ledger_size": size})
            finally:
                self.app.send_lock.release()
        elif path == "/api/mail":
            mailer.save_settings(body.get("values") or {})
            self._json(200, mailer.public_settings())
        elif path == "/api/history/clear":
            store.update_ledger(lambda led: E.empty_ledger())
            self._json(200, {"ledger_size": 0})
        else:
            self._json(404, {"error": "Unknown request."})


class DesktopApp:
    def __init__(self, port: int = 8765, fetcher: Optional[Callable[[str], bytes]] = None,
                 pause: float = collect.GOOGLE_PAUSE, key: Optional[str] = None):
        self.key = key or secrets.token_urlsafe(24)
        self.jobs = Jobs(fetcher, pause)
        self.send_lock = threading.Lock()
        handler = partial(Handler, app=self)
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", _free_port(port)), handler)
        self.httpd.daemon_threads = True

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_address[1]}/"

    def serve_forever(self) -> None:
        self.httpd.serve_forever()

    def start_background(self) -> threading.Thread:
        t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def _free_port(preferred: int) -> int:
    for port in [preferred] + list(range(preferred + 1, preferred + 20)) + [0]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise OSError("No free port found")


def serve(port: int = 8765, open_browser: bool = True) -> int:
    app = DesktopApp(port)
    print("Daily Brief desktop app")
    print("  Open:", app.url)
    print("  Your data folder:", store.path(""))
    print("  Leave this window open while you use the app. Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(app.url)).start()
    try:
        app.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        app.httpd.server_close()
    return 0
