"""The desktop app server: safety checks and every API call (no network)."""
import http.client
import json
import time

import pytest
from conftest import feed_bytes

from dailybrief import server, store


def fetcher(url):
    return feed_bytes("google_news.xml" if "news.google.com" in url else "rss_feed.xml")


@pytest.fixture
def app():
    a = server.DesktopApp(port=0, fetcher=fetcher, pause=0, key="test-key")
    a.start_background()
    yield a
    a.stop()


def call(app, method, path, body=None, key="test-key", host=None, origin=None, ctype="application/json"):
    port = app.httpd.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Host": host or f"127.0.0.1:{port}"}
    if key is not None:
        headers["X-Brief-Key"] = key
    if origin:
        headers["Origin"] = origin
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = ctype
    conn.request(method, path, body=data, headers=headers)
    res = conn.getresponse()
    raw = res.read()
    conn.close()
    try:
        return res.status, json.loads(raw)
    except ValueError:
        return res.status, raw.decode("utf-8", "replace")


def settings():
    return {"version": 1, "categories": [{"id": "net", "name": "Network", "queries": ['"zero trust"'],
                                          "require": [["zero trust", "VPN", "network"]]}]}


def test_page_carries_the_key_and_api_needs_it(app):
    code, page = call(app, "GET", "/", key=None)
    assert code == 200 and 'content="test-key"' in page
    assert call(app, "GET", "/api/health", key=None)[0] == 403
    assert call(app, "GET", "/api/health", key="wrong")[0] == 403
    code, health = call(app, "GET", "/api/health")
    assert code == 200 and health["mode"] == "desktop" and health["ledger_size"] == 0


def test_other_sites_and_hosts_are_refused(app):
    assert call(app, "GET", "/api/health", host="evil.example.com")[0] == 403
    assert call(app, "POST", "/api/history/clear", {}, origin="https://evil.example.com")[0] == 403
    assert call(app, "POST", "/api/history/clear", {}, ctype="text/plain")[0] == 400
    assert call(app, "GET", "/", key=None, host="rebind.example.com")[0] == 403


def test_run_commit_and_history(app):
    code, r = call(app, "POST", "/api/run", {"config": settings()})
    assert code == 200
    for _ in range(100):
        code, job = call(app, "GET", "/api/run/" + r["job"])
        if job["state"] != "running":
            break
        time.sleep(0.05)
    assert job["state"] == "done", job
    brief = job["brief"]
    assert brief["categories"][0]["items"] and job["health"]["net"]["queries"][0]["items"] == 5
    code, c = call(app, "POST", "/api/commit", {"brief": brief})
    assert code == 200 and c["ledger_size"] == len(brief["categories"][0]["items"])
    code, r2 = call(app, "POST", "/api/run", {"config": settings()})
    for _ in range(100):
        code, job2 = call(app, "GET", "/api/run/" + r2["job"])
        if job2["state"] != "running":
            break
        time.sleep(0.05)
    assert job2["brief"]["withheld"] >= 1
    assert call(app, "POST", "/api/history/clear", {})[1]["ledger_size"] == 0


def test_bad_settings_are_rejected(app):
    code, r = call(app, "POST", "/api/run", {"config": {"categories": []}})
    assert code == 400 and "Add at least one category." in r["errors"]
    code, r = call(app, "POST", "/api/config", {"config": settings()})
    assert code == 200 and r["saved"] and store.load_config()["categories"][0]["id"] == "net"


def test_email_sending_is_gone(app, sample_brief):
    code, health = call(app, "GET", "/api/health")
    assert code == 200 and "mail" not in health
    for method, path, body in (("POST", "/api/send", {"brief": sample_brief}), ("POST", "/api/mail", {"values": {}}),
                               ("GET", "/api/mail", None)):
        code, r = call(app, method, path, body)
        assert code == 404 and r["error"] == "Unknown request.", path


# ------------------------------------------------------------- review findings
def test_head_requests_and_folder_listings_are_refused(app):
    port = app.httpd.server_address[1]
    for host, path, want in ((f"127.0.0.1:{port}", "/", 200), ("evil.example.com", "/", 403),
                             (f"127.0.0.1:{port}", "/api/health", 403)):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("HEAD", path, headers={"Host": host})
        assert conn.getresponse().status == want, (host, path)
        conn.close()
    assert call(app, "GET", "/js/", key=None)[0] == 404
    assert call(app, "POST", "/api/history/clear", {}, origin="null")[0] == 403


def test_mark_as_read_keeps_the_scheduled_send_and_honours_category_limits(app, sample_brief):
    brief = dict(sample_brief, source="desktop")
    cats = [dict(c) for c in brief["categories"]]
    cats[0] = dict(cats[0], items=(cats[0]["items"] * 3)[:7])
    for k, it in enumerate(cats[0]["items"]):
        cats[0]["items"][k] = dict(it, url=it["url"] + "?n=%d" % k, title=it["title"] + " part %d" % k)
    brief["categories"] = cats
    brief["total"] = sum(len(c["items"]) for c in cats)
    cfg = {"version": 1, "categories": [{"id": c["id"], "name": c["name"], "queries": ["x"], "items": 8 if i == 0 else None}
                                        for i, c in enumerate(cats)]}
    code, r = call(app, "POST", "/api/commit", {"brief": brief, "config": cfg})
    assert code == 200, r
    led = store.load_ledger()
    assert led["sent_dates"] == [] and len(led["urls"]) == brief["total"]
