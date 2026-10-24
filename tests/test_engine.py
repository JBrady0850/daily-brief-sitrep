"""Story selection, freshness, history and checks (Python engine)."""
import copy

from dailybrief import engine as E
from dailybrief.jsdata import library

NOW = "2026-10-23T12:00:00Z"


def ago(hours):
    return E.iso_z(E.parse_iso(NOW) - int(hours * 3600000))


def cfg_one(**brief):
    cat = {"id": "sec", "name": "Security", "queries": ["security"], "require": [["security", "CVE", "patch"]],
           "exclude": ["webinar"]}
    return {"version": 1, "brief": brief, "categories": [cat]}


def item(title, hours, url=None, **kw):
    return dict({"title": title, "url": url or "https://news.example.com/" + E.norm_title(title).replace(" ", "-"),
                 "source": "Example", "published": None if hours is None else ago(hours), "summary": ""}, **kw)


# ---------------------------------------------------------------- matching
def test_acronyms_match_only_in_capitals_and_whole_words():
    assert E.term_hit("Pentagon expands AI pilots", "AI")
    assert not E.term_hit("He said it was fine", "AI")
    assert not E.term_hit("Tariff talks resume", "RIF")
    assert not E.term_hit("Kansas expands broadband", "NSA")
    assert E.term_hit("CISA warns about a new CVE", "CVE")
    assert not E.term_hit("It is fine", "IT")
    assert E.term_hit("IT budgets grow", "IT")


def test_phrases_and_punctuated_terms():
    assert E.term_hit("New 401(k) limits announced", "401(k)")
    assert E.term_hit("The S&P 500 closes higher", "S&P 500")
    assert E.term_hit("Zero Trust maturity model", "zero trust")
    assert not E.term_hit("zerotrust", "zero trust")


def test_url_identity_ignores_tracking_and_trailing_slash():
    a = E.norm_url("https://www.Example.com/a/b/?utm_source=x&id=3&fbclid=9#top")
    b = E.norm_url("http://example.com/a/b?id=3")
    assert a == b == "example.com/a/b?id=3"


def test_title_identity_drops_outlet_suffix():
    assert E.norm_title("Agencies weigh new buyout offers - Federal Daily") == E.norm_title("Agencies weigh new buyout offers")
    assert E.near_dup("Agencies weigh new buyout offers for staff", "Agencies weigh new buyout offers for their staff")
    assert not E.near_dup("Agencies weigh new buyout offers", "Bakery opens a second location downtown")


# -------------------------------------------------------------- freshness
def test_window_boundaries():
    b = E.normalize_config(cfg_one())["brief"]
    now = E.parse_iso(NOW)
    assert E.classify(E.parse_iso(ago(23.5)), now, b)["recency"] == "news"
    assert E.classify(E.parse_iso(ago(25)), now, b)["recency"] == "backfill"
    assert E.classify(E.parse_iso(ago(71)), now, b)["recency"] == "backfill"
    assert E.classify(E.parse_iso(ago(73)), now, b) == {"reject": "too old"}
    assert E.classify(None, now, b)["recency"] == "reference"
    assert E.classify(E.parse_iso(ago(-10)), now, b) == {"recency": "news", "age": 0}
    assert E.classify(E.parse_iso(ago(-60)), now, b) == {"reject": "bad date"}


def test_backfill_disabled_when_equal_to_window():
    b = E.normalize_config(cfg_one(backfill_max_hours=24))["brief"]
    assert E.classify(E.parse_iso(ago(30)), E.parse_iso(NOW), b) == {"reject": "too old"}


def test_parse_iso_rejects_impossible_dates():
    assert E.parse_iso("2026-02-30") is None
    assert E.parse_iso("2026-10-23T24:00:00Z") is None
    assert E.parse_iso("yesterday") is None
    assert E.parse_iso("2026-10-23T08:15:00+05:30") == E.parse_iso("2026-10-23T02:45:00Z")


# -------------------------------------------------------------- selection
def test_fresh_first_then_older_then_reference_and_never_pads():
    cands = {"sec": [item("Old security patch roundup from the week", 40), item("Security agency page", None),
                     item("Fresh security patch for routers ships today", 2), item("Security patch notes for browsers", 10)]}
    b = E.select_brief(cands, cfg_one(items_per_category=3), None, NOW, "2026-10-23")
    got = [i["recency"] for i in b["categories"][0]["items"]]
    assert got == ["news", "news", "backfill"]
    b5 = E.select_brief(cands, cfg_one(items_per_category=10), None, NOW, "2026-10-23")
    assert [i["recency"] for i in b5["categories"][0]["items"]] == ["news", "news", "backfill", "reference"]
    assert b5["total"] == 4


def test_gates_reject_off_topic_excluded_social_and_paperwork():
    cands = {"sec": [
        item("Bakery opens downtown", 1),
        item("Free security webinar next week", 1),
        item("Security patch video", 1, url="https://www.youtube.com/watch?v=1"),
        item("Agency Information Collection Request on security", 1),
        item("Security patch released for mail servers", 1),
    ]}
    b = E.select_brief(cands, cfg_one(), None, NOW, "2026-10-23")
    cat = b["categories"][0]
    assert [i["title"] for i in cat["items"]] == ["Security patch released for mail servers"]
    assert cat["rejected"] == {"off topic": 1, "excluded term": 1, "social or avoided site": 1, "paperwork notice": 1}


def test_on_topic_feed_stories_need_no_must_mention_term_but_still_pass_every_other_filter():
    cands = {"sec": [
        item("Bakery opens downtown", 1, on_topic=True),
        item("Free security webinar next week", 1, on_topic=True),
        item("Garden show draws crowds", 1),
    ]}
    b = E.select_brief(cands, cfg_one(), None, NOW, "2026-10-23")
    cat = b["categories"][0]
    assert [i["title"] for i in cat["items"]] == ["Bakery opens downtown"]
    assert cat["rejected"] == {"excluded term": 1, "off topic": 1}
    assert "on_topic" not in cat["items"][0], "the flag never reaches the brief"
    assert not E.clean_item({"title": "x", "on_topic": "yes"}, 100)["on_topic"], "only a real true counts"
    c = cfg_one()
    c["categories"][0]["topic_feeds"] = ["not a link"]
    assert any("topic_feeds" in e for e in E.validate_config(c)["errors"])
    c["categories"][0]["topic_feeds"] = ["https://feeds.example.com/security.xml"]
    assert not E.validate_config(c)["errors"]


def test_listicles_skipped_only_when_asked():
    c = cfg_one()
    c["categories"][0]["skip_listicles"] = True
    cands = {"sec": [item("Top 10 security tools to watch", 1), item("Security patch for printers", 2)]}
    assert E.select_brief(cands, c, None, NOW, "2026-10-23")["total"] == 1
    assert E.select_brief(cands, cfg_one(), None, NOW, "2026-10-23")["total"] == 2


def test_history_withholds_sent_items_forever():
    cands = {"sec": [item("Security patch for printers ships", 2), item("Security patch for routers ships", 3)]}
    first = E.select_brief(cands, cfg_one(), E.empty_ledger(), NOW, "2026-10-23")
    led = E.ledger_add(E.empty_ledger(), first)
    again = E.select_brief(cands, cfg_one(), led, NOW, "2026-10-24")
    assert again["total"] == 0 and again["withheld"] == 2
    # Permanence: a sent URL stays barred after 2,000 later items.
    for k in range(2000):
        filler = {"date": "2026-10-25", "categories": [{"items": [{"title": "Filler story number %d" % k, "url": "https://f.example.com/%d" % k}]}]}
        led = E.ledger_add(led, filler)
    assert E.ledger_has(led, cands["sec"][0])
    # The same story syndicated under another link is caught by its title.
    assert E.ledger_has(led, item("Security patch for printers ships - Another Outlet", 1, url="https://other.example.com/x"))


def test_a_story_appears_in_one_category_only():
    c = cfg_one()
    c["categories"].append({"id": "sec2", "name": "Security two", "queries": ["x"], "require": [["security"]]})
    shared = item("Security patch for printers ships today", 2)
    b = E.select_brief({"sec": [shared], "sec2": [copy.deepcopy(shared)]}, c, None, NOW, "2026-10-23")
    assert b["categories"][0]["items"] and not b["categories"][1]["items"]
    assert b["categories"][1]["rejected"] == {"duplicate": 1}


def test_category_item_override():
    c = cfg_one()
    c["categories"][0]["items"] = 1
    cands = {"sec": [item("Security patch one for printers", 1), item("Security patch two for routers", 2)]}
    assert E.select_brief(cands, c, None, NOW, "2026-10-23")["total"] == 1


def test_local_placeholders():
    lib = library()
    cfg = E.config_from_pack(lib, "around-town", {"reader": {"location": "Springfield", "local_terms": ["Sangamon County"]}})
    cat = E.resolve_category(E.normalize_config(cfg)["categories"][0], cfg["reader"])
    assert cat["name"] == "Local Community (Springfield)"
    assert cat["require"][0] == ["Springfield", "Sangamon County"]
    assert '"Springfield"' in cat["queries"][0]


# ------------------------------------------------------------- settings
def test_every_pack_is_valid_with_a_town():
    lib = library()
    for p in lib["packs"]:
        cfg = E.config_from_pack(lib, p["id"], {"reader": {"location": "Springfield"}})
        v = E.validate_config(cfg)
        assert v["errors"] == [], (p["id"], v["errors"])


def test_validation_catches_bad_settings():
    good = cfg_one()
    assert E.validate_config(good)["errors"] == []
    bad = copy.deepcopy(good)
    bad["brief"].update(window_hours=48, backfill_max_hours=24, items_per_category=0)
    bad["categories"].append(dict(bad["categories"][0], color="red"))
    bad["categories"].append({"id": "loc", "name": "Local ({location})", "queries": ["{location} news"], "require": [["{local_terms}"]]})
    bad["brief"]["subject"] = "Brief {nope}"
    errs = E.validate_config(bad)["errors"]
    assert "brief.backfill_max_hours must be at least brief.window_hours." in errs
    assert "brief.items_per_category must be a whole number from 1 to 10." in errs
    assert "Category 2 (sec): id is used twice." in errs
    assert "Category 3 (loc): needs your town in reader.location." in errs
    assert any("{nope}" in e for e in errs)
    many = copy.deepcopy(good)
    many["categories"] = [dict(good["categories"][0], id="c%d" % i) for i in range(16)]
    assert "Use at most 15 categories." in E.validate_config(many)["errors"]


def test_validation_warns_about_personal_data():
    c = cfg_one()
    c["reader"] = {"role": "call me at 555-123" + "-4567 or me" + "@" + "mail.test"}
    w = E.validate_config(c)["warnings"]
    assert any("email address" in x for x in w) and any("phone number" in x for x in w)


# ----------------------------------------------------------------- checks
def test_sample_brief_passes(sample_brief, sample_settings):
    assert E.check_brief(sample_brief, sample_settings) == {"errors": [], "warnings": []}


def test_check_catches_each_planted_defect(sample_brief, sample_settings):
    def errors_after(mutate):
        b = copy.deepcopy(sample_brief)
        mutate(b)
        return E.check_brief(b, sample_settings)["errors"]

    items = lambda b: b["categories"][0]["items"]  # noqa: E731
    assert any("marked news but is" in e for e in errors_after(lambda b: items(b)[0].update(published="2026-10-20T00:00:00Z")))
    assert any("em dash" in e for e in errors_after(lambda b: items(b)[0].update(summary="A " + chr(0x2014) + " B")))
    assert any("http or https" in e for e in errors_after(lambda b: items(b)[0].update(url="javascript:alert(1)")))
    assert any("repeats the link" in e for e in errors_after(lambda b: items(b)[1].update(url=items(b)[0]["url"])))
    assert any("the limit is 5" in e for e in errors_after(lambda b: items(b).extend(copy.deepcopy(items(b)) * 2)))
    assert any("total says" in e for e in errors_after(lambda b: b.update(total=99)))
    assert any("need a published time" in e for e in errors_after(lambda b: items(b)[0].update(published=None)))
    assert any("recency must be" in e for e in errors_after(lambda b: items(b)[0].update(recency="fresh")))


def test_filter_seen_counts_withheld(sample_brief):
    led = E.ledger_add(E.empty_ledger(), sample_brief)
    out = E.filter_seen(sample_brief, led)
    assert out["withheld"] == sample_brief["total"] and out["brief"]["total"] == 0 and out["brief"]["ledger_applied"]


# ---------------------------------------------------------------- AI hand-off
def test_build_prompt_and_extract_json(sample_settings):
    text = "intro\n<!-- CONFIG:BEGIN -->\nold\n<!-- CONFIG:END -->\nend"
    out = E.build_prompt(text, sample_settings)
    assert '"items_per_category": 5' in out and "old" not in out
    assert E.FILE_NOTE in E.build_prompt(text, "file")
    chat = "Sure! Here is the brief.\n```json\n" + '{"a": {"b": "x } y"}}' + "\n```\nSEEN HISTORY"
    assert E.extract_json(chat) == {"a": {"b": "x } y"}}
    assert E.extract_json("no json here") is None


def test_google_news_url():
    url = E.google_news_url('"zero trust" (CISA OR NSA)', 1, {})
    assert url == ("https://news.google.com/rss/search?q=%22zero%20trust%22%20(CISA%20OR%20NSA)%20when%3A1d"
                   "&hl=en-US&gl=US&ceid=US:en")


# ------------------------------------------------------- live-run findings
def test_feed_em_dashes_become_hyphens():
    dash = chr(0x2014)
    cands = {"sec": [item("Security patch " + dash + " CNBC", 1, summary="Admins patch " + dash + "now" + dash + " today.",
                          source="Outlet " + dash + " Wire")]}
    b = E.select_brief(cands, cfg_one(), None, NOW, "2026-10-23")
    it = b["categories"][0]["items"][0]
    assert it["title"] == "Security patch - CNBC" and it["summary"] == "Admins patch -now- today."
    assert it["source"] == "Outlet - Wire"
    assert E.check_brief(b, cfg_one())["errors"] == []
    long = "word " * 60 + dash * 5
    assert len(E.clean_item({"title": "t", "url": "https://e.com", "summary": long}, 90)["summary"]) <= 90


def test_career_skills_leaves_out_election_certification():
    lib = library()
    cfg = E.config_from_pack(lib, "starter")
    cat = E.category_from_library(lib, "career-skills")
    cfg["categories"] = [cat]
    cands = {"career-skills": [
        item("Justice Department sues over certification of Alaska election results", 1),
        item("Sol de Janeiro achieves B Corp Certification, marking a new milestone", 1),
        item("Cloud certification demand rises among IT workers", 1),
        item("Tech salary survey shows pay gains for engineers", 2),
    ]}
    b = E.select_brief(cands, cfg, None, NOW, "2026-10-23")
    kept = [i["title"] for i in b["categories"][0]["items"]]
    assert kept == ["Cloud certification demand rises among IT workers", "Tech salary survey shows pay gains for engineers"]
    assert b["categories"][0]["rejected"] == {"excluded term": 1, "off topic": 1}


def test_history_lookup_is_fast_and_matches_the_plain_scan():
    import random
    import time
    rnd = random.Random(7)
    vocab = ["agency", "cyber", "patch", "federal", "budget", "network", "cloud", "model", "senate", "report",
             "vendor", "breach", "update", "policy", "market", "rates", "workers", "salary", "retire", "plans"]
    led = E.empty_ledger()
    for d in range(70):
        b = {"date": "2026-08-%02d" % (d % 28 + 1), "categories": [{"items": [
            {"title": " ".join(rnd.sample(vocab, 8)) + " n%d" % (d * 100 + k), "url": "https://e.com/%d/%d" % (d, k)}
            for k in range(45)]}]}
        led = E.ledger_add(led, b)
    cands = [{"title": " ".join(rnd.sample(vocab, 8)) + " c%d" % k, "url": "https://n.com/%d" % k} for k in range(80)]
    plain = [any(E.near_dup(E.title_tokens(c["title"]), E.title_tokens(r)) for r in led["recent"]) for c in cands]
    t = time.time()
    idx = E.recent_index(led)
    fast = [E.ledger_has({"urls": {}, "titles": {}, "recent": led["recent"]}, c, idx) for c in cands]
    assert fast == plain and any(plain)
    assert time.time() - t < 3, "the indexed lookup should not rescan the history for every story"
