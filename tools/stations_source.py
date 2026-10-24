"""Rebuilds dailybrief/local_stations.json: local TV station news feeds by state.

The GitHub workflow reads these feeds every four hours and publishes one file of
stories per state (app/data/local/<STATE>.json). The web page reads only the file
for the reader's state and keeps the stories that name the reader's town or a
nearby place, so town news comes from GitHub alone.

This tool reads the station lists that the station groups publish, finds each
station's news feed, and keeps the stations whose feed answers with recent
stories. It reads the live web, so run it by hand (python tools/stations_source.py)
and review the change; the tests never run it.
"""
import concurrent.futures as cf
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dailybrief import collect as C, engine as E  # noqa: E402

OUT = ROOT / "dailybrief" / "local_stations.json"
SCHEMA = "daily-brief-local-stations/1"

GROUP_PAGES = {
    "gray": "https://gray.tv/companies",
    "nexstar": "https://www.nexstar.tv/stations/",
    "scripps": "https://scripps.com/our-brands/local-media/",
    "hearst": "https://www.hearst.com/broadcasting",
}

# Feed addresses by site platform, tried in this order for each group's sites.
PATTERNS = {
    "arc": "/arc/outboundfeeds/rss/?outputType=xml",
    "tegna": "/feeds/syndication/rss/news/local",
    "wordpress": "/feed/",
    "sinclair": "/news/local.rss",
    "scripps": "/news/local-news.rss",
    "hearst": "/local-news-rss",
    "hearst-top": "/topstories-rss",
    "nbc": "/?rss=y",
}
ORDER = {
    "gray": ["arc"],
    "nexstar": ["wordpress", "tegna", "arc"],
    "scripps": ["scripps"],
    "hearst": ["hearst", "hearst-top"],
    "extra": ["arc", "wordpress", "tegna", "sinclair", "scripps", "hearst", "nbc"],
}

# Stations from other groups, for states the lists above leave thin. Each entry is
# (site, states). Checked the same way as the rest; one that does not answer is left out.
EXTRA = [
    ("https://www.news4jax.com", ["FL", "GA"]),   # Graham Media
    ("https://www.clickorlando.com", ["FL"]),
    ("https://www.clickondetroit.com", ["MI"]),
    ("https://www.click2houston.com", ["TX"]),
    ("https://www.ksat.com", ["TX"]),
    ("https://www.wsls.com", ["VA"]),
    ("https://www.wsbtv.com", ["GA"]),             # Cox Media Group
    ("https://www.wftv.com", ["FL"]),
    ("https://www.wpxi.com", ["PA"]),
    ("https://www.kiro7.com", ["WA"]),
    ("https://www.whio.com", ["OH"]),
    ("https://www.wsoctv.com", ["NC", "SC"]),
    ("https://www.actionnewsjax.com", ["FL", "GA"]),
    ("https://www.boston25news.com", ["MA", "NH"]),
    ("https://www.ktvu.com", ["CA"]),
    ("https://www.kokh25.com", ["OK"]),
    ("https://weartv.com", ["FL", "AL"]),           # Sinclair
    ("https://wjla.com", ["DC", "MD", "VA"]),
    ("https://komonews.com", ["WA"]),
    ("https://katv.com", ["AR"]),
    ("https://kutv.com", ["UT"]),
    ("https://wpde.com", ["SC", "NC"]),
    ("https://wset.com", ["VA"]),
    ("https://wlos.com", ["NC", "SC"]),
    ("https://keprtv.com", ["WA"]),
    ("https://kmph.com", ["CA"]),
    ("https://cbs4indy.com", ["IN"]),
    ("https://www.nbcmiami.com", ["FL"]),          # NBC owned stations
    ("https://www.nbcchicago.com", ["IL"]),
    ("https://www.nbcnewyork.com", ["NY", "NJ", "CT"]),
    ("https://www.nbclosangeles.com", ["CA"]),
    ("https://www.nbcdfw.com", ["TX"]),
    ("https://www.nbcboston.com", ["MA"]),
    ("https://www.nbcwashington.com", ["DC", "MD", "VA"]),
    ("https://www.nbcphiladelphia.com", ["PA", "NJ", "DE"]),
    ("https://www.nbcbayarea.com", ["CA"]),
    ("https://www.nbcsandiego.com", ["CA"]),
    ("https://www.nbcconnecticut.com", ["CT"]),
    ("https://www.hawaiinewsnow.com", ["HI"]),
    ("https://www.alaskasnewssource.com", ["AK"]),
    ("https://www.wcax.com", ["VT", "NY", "NH"]),
    ("https://www.wmtw.com", ["ME", "NH"]),
    ("https://www.wmur.com", ["NH"]),
    ("https://www.ktiv.com", ["IA", "NE", "SD"]),
    ("https://www.kfyrtv.com", ["ND"]),
    ("https://www.ksfy.com", ["SD"]),
    ("https://www.kotatv.com", ["SD", "WY"]),
    ("https://www.wyomingnewsnow.tv", ["WY"]),
    ("https://www.kulr8.com", ["MT"]),
    ("https://www.ktvh.com", ["MT"]),
    ("https://www.kivitv.com", ["ID"]),
    ("https://www.ktvb.com", ["ID", "OR"]),
    ("https://www.kolotv.com", ["NV", "CA"]),
    ("https://www.8newsnow.com", ["NV"]),
    ("https://www.wboc.com", ["DE", "MD"]),
    ("https://www.wpri.com", ["RI", "MA"]),
    ("https://turnto10.com", ["RI", "MA"]),
]

STATES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "district of columbia": "DC", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD", "massachusetts": "MA",
    "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}
CODES = set(STATES.values())


def states_in(text):
    """State codes named in a market label such as "Augusta, GA-Aiken, SC" or "Tampa, Florida"."""
    codes = [c for c in re.findall(r"\b([A-Z]{2})\b", text) if c in CODES]
    if codes:
        return list(dict.fromkeys(codes))
    low = " " + re.sub(r"[^a-z]+", " ", text.lower()) + " "
    found = []
    if " d c " in low or " district of columbia " in low:
        found.append("DC")
        low = low.replace(" district of columbia ", " | ").replace(" d c ", " | ").replace(" washington ", " | ")
    for name, code in sorted(STATES.items(), key=lambda kv: -len(kv[0])):
        if " " + name + " " in low:
            found.append(code)
            low = low.replace(" " + name + " ", " | ")
    return list(dict.fromkeys(found))


def site_of(url):
    m = re.match(r"https?://([^/]+)", url.strip())
    return ("https://" + m.group(1).lower()) if m else ""


def parse_gray(s):
    for m in re.finditer(r'mapT_city d-none">([^<]+)</span>', s):
        g = re.search(r'href="(https?://[^"]+)"[^>]*><i class="bi bi-globe"', s[m.end():m.end() + 3000])
        if g:
            yield site_of(g.group(1)), states_in(m.group(1))


def parse_nexstar(s):
    """Each market heading, then every site link before its affiliates list."""
    for m in re.finditer(r"<h2>([^<]+)</h2>(.*?)<div class=\"affiliates\">", s, re.S):
        for href in re.findall(r'<a href="(https?://[^"]+)"', m.group(2)):
            yield site_of(href), states_in(m.group(1))


def parse_scripps(s):
    for m in re.finditer(r'<a class="local-media" href="(https?://[^"]+)".*?<span class="location">([^<]+)</span>', s, re.S):
        yield site_of(m.group(1)), states_in(m.group(2))


def parse_hearst(s):
    """Rows of a script array: state, ..., call letters, logo, contact, weather, region, market, ..., site."""
    q = r"'[^']*',\s*"
    row = re.compile(r"\['([A-Za-z ]+)',\s*'\d+',\s*\d+,\s*" + q * 5 + r"'([^']*)',\s*" + q * 4 + r"'(https?://[^']*)'")
    for m in row.finditer(s):
        yield site_of(m.group(3)), states_in(m.group(2) + ", " + m.group(1))


PARSERS = {"gray": parse_gray, "nexstar": parse_nexstar, "scripps": parse_scripps, "hearst": parse_hearst}


def check_feed(url, now_ms):
    """A feed that answers with at least five stories, the newest within a week."""
    items = C.parse_feed(C.fetch(url, timeout=15, retries=0))
    dated = [E.parse_iso(i.get("published")) for i in items]
    dated = [d for d in dated if d is not None]
    if len(items) < 5 or not dated or (now_ms - max(dated)) / 86400000 > 7:
        raise C.FetchError("%d stories, newest %s" % (len(items), E.iso_z(max(dated)) if dated else "undated"))
    return station_name(items[0].get("source") or "", url)


GENERIC = {"local news", "top stories", "local", "news", "home", "rss", "latest news", "news feed"}


def station_name(title, url):
    """The feed's own title, unless it is a generic one ("Local News"); then the site's address."""
    t = re.sub(r"\s+RSS Feed:.*$", "", E.collapse(title))[:60]
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    return host if not re.search(r"[A-Za-z]", t) or t.lower() in GENERIC else t


def find_feed(site, group, now_ms):
    tried = []
    for key in ORDER.get(group, []) + [k for k in ORDER["extra"] if k not in ORDER.get(group, [])]:
        url = site + PATTERNS[key]
        try:
            return url, key, check_feed(url, now_ms), tried
        except Exception as exc:  # noqa: BLE001 - try the next pattern
            tried.append("%s: %s" % (key, str(exc)[:60]))
    return None, None, None, tried


def main():
    now_ms = int(time.time() * 1000)
    rows = {}
    for group, page in GROUP_PAGES.items():
        text = C.fetch(page, timeout=30, retries=1).decode("utf-8", "replace")
        n = 0
        for site, states in PARSERS[group](text):
            if not site or not states:
                continue
            r = rows.setdefault(site, {"group": group, "states": []})
            r["states"] += [s for s in states if s not in r["states"]]
            n += 1
        print("%-8s %3d listings" % (group, n), file=sys.stderr)
    for site, states in EXTRA:
        r = rows.setdefault(site_of(site), {"group": "extra", "states": []})
        r["states"] += [s for s in states if s not in r["states"]]
    print("%d sites to check" % len(rows), file=sys.stderr)

    def one(site):
        feed, kind, name, tried = find_feed(site, rows[site]["group"], now_ms)
        return site, feed, kind, name, tried

    stations, dropped = [], []
    with cf.ThreadPoolExecutor(8) as ex:
        for site, feed, kind, name, tried in ex.map(one, sorted(rows)):
            if not feed:
                dropped.append((site, tried))
                continue
            host = re.sub(r"^https://(www\.)?", "", site)
            stations.append({"id": re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-"), "name": name or host,
                             "site": site, "feed": feed, "states": sorted(rows[site]["states"]),
                             "group": rows[site]["group"]})
    seen = {}
    for s in stations:  # one entry per site, with or without "www."
        if s["id"] in seen:
            seen[s["id"]]["states"] = sorted(set(seen[s["id"]]["states"]) | set(s["states"]))
        else:
            seen[s["id"]] = s
    stations = sorted(seen.values(), key=lambda s: s["id"])
    by_state = {c: 0 for c in sorted(CODES)}
    for s in stations:
        for c in s["states"]:
            by_state[c] += 1
    data = {"schema": SCHEMA, "checked": E.iso_z(now_ms)[:10], "sources": list(GROUP_PAGES.values()),
            "stations": stations}
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:  # Python 3.9 has no write_text(newline=)
        fh.write(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print("kept %d stations, dropped %d sites" % (len(stations), len(dropped)), file=sys.stderr)
    print("stations per state: " + ", ".join("%s %d" % kv for kv in by_state.items()), file=sys.stderr)
    print("states with none: " + (", ".join(c for c, n in by_state.items() if not n) or "none"), file=sys.stderr)
    for site, tried in dropped:
        print("  dropped %s (%s)" % (site, "; ".join(tried[:3])), file=sys.stderr)


if __name__ == "__main__":
    main()
