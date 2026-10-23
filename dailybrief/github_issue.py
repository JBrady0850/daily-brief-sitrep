"""Delivers the brief as a GitHub issue, using the token every workflow run
gets for free (GITHUB_TOKEN). No personal key or password is involved: GitHub
sends you the issue by email according to your notification settings, and the
issue mentions the repository owner so it counts as a notification for them.

Use this only in a private repository. Issues in a public repository are public.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable, Mapping, Optional

API = "https://api.github.com"
MAX_BODY = 65000  # GitHub's issue body limit is 65,536 characters
BOT = "github-actions[bot]"

Opener = Callable[[urllib.request.Request], bytes]


class IssueError(RuntimeError):
    pass


def _open(req: urllib.request.Request) -> bytes:
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise IssueError(f"GitHub answered {exc.code}: {detail}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise IssueError(f"Could not reach GitHub: {exc}") from exc


def settings(env: Optional[Mapping[str, str]] = None) -> Optional[dict]:
    """The token and repository from a workflow run, or None outside one."""
    env = os.environ if env is None else env
    token, repo = env.get("GITHUB_TOKEN", ""), env.get("GITHUB_REPOSITORY", "")
    if not token or "/" not in repo:
        return None
    return {"token": token, "repo": repo, "owner": env.get("BRIEF_MENTION", "") or repo.split("/")[0],
            "api": env.get("GITHUB_API_URL", API).rstrip("/")}


def _call(s: dict, method: str, path: str, body: Optional[dict], opener: Opener) -> object:
    req = urllib.request.Request(s["api"] + path, method=method,
                                 data=None if body is None else json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + s["token"], "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "daily-brief",
                                          "Content-Type": "application/json"})
    raw = opener(req)
    return json.loads(raw.decode("utf-8")) if raw else None


def post(subject: str, markdown: str, prefix: str, s: dict, opener: Opener = _open) -> dict:
    """Opens today's brief issue and closes earlier brief issues the workflow opened."""
    body = markdown
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY - 200] + "\n\n*The brief was longer than a GitHub issue allows and was cut here.*\n"
    body += "\n@" + s["owner"] + "\n"
    created = _call(s, "POST", "/repos/" + s["repo"] + "/issues", {"title": subject, "body": body}, opener)
    number = created.get("number") if isinstance(created, dict) else None
    closed = 0
    try:
        open_issues = _call(s, "GET", "/repos/" + s["repo"] + "/issues?state=open&per_page=50&creator="
                            + BOT.replace("[", "%5B").replace("]", "%5D"), None, opener)
        for it in open_issues if isinstance(open_issues, list) else []:
            if it.get("number") != number and str(it.get("title", "")).startswith(prefix) and "pull_request" not in it:
                _call(s, "PATCH", "/repos/" + s["repo"] + "/issues/" + str(it["number"]),
                      {"state": "closed", "state_reason": "completed"}, opener)
                closed += 1
    except IssueError:
        pass  # tidying old issues is optional; today's issue is already open
    return {"number": number, "url": created.get("html_url") if isinstance(created, dict) else "", "closed": closed}
