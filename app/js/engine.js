/* Daily Brief engine: settings, topic filters, freshness, no-repeat history,
   story selection and brief checks. No page code here, so the same file runs in
   the browser and under Node for the tests. dailybrief/engine.py mirrors every
   function; tests/test_parity.py proves the two give identical answers. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.DB_ENGINE = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const VERSION = "0.7.0";
  const SCHEMA = "daily-brief/v1";
  const MAX_CATEGORIES = 15;
  const MAX_RECENT = 3000;
  const MAX_LEDGER = 20000;
  const MAX_SENT_DATES = 400;
  const PALETTE = ["#1f3a5f", "#0b5e8f", "#0f6e5c", "#5b3485", "#a04000", "#8a5a00",
    "#1b6e3d", "#922b21", "#1d6aa0", "#34495e", "#6b4f2a", "#7a2f5f"];
  const SOCIAL_HOSTS = ["instagram.com", "facebook.com", "fb.watch", "tiktok.com", "youtube.com",
    "youtu.be", "pinterest.com", "twitter.com", "x.com", "threads.net", "reddit.com"];
  const PAPERWORK = ["Agency Information Collection", "Information Collection Request",
    "Proposed Collection", "Comment Request", "Submission for OMB Review", "OMB Control Number",
    "Sunshine Act Meeting", "Notice of Federal Advisory Committee"];
  const TRACKING = ["fbclid", "gclid", "mc_cid", "mc_eid", "cmpid", "ref", "ref_src", "igshid",
    "s_cid", "ocid", "mkt_tok"];
  const STOP = ["the", "and", "for", "with", "from", "that", "this", "are", "was", "has", "have",
    "its", "after", "over", "into", "about", "new", "says", "said", "will", "how", "why", "what"];
  const RECENCY = ["news", "backfill", "reference"];
  const SUBJECT_FIELDS = ["total", "date", "title", "empty"];
  const FILE_NOTE = "Saved settings are in the attached knowledge file daily-brief-settings.json. Use them; if that file is missing, start with the setup interview.";

  const DEFAULTS = {
    version: 1,
    brief: {
      title: "The Morning Brief",
      subject: "Daily Brief - {total}-Item SITREP | {date}",
      window_hours: 24,
      backfill_max_hours: 72,
      items_per_category: 5,
      summary_max_chars: 320,
      allow_reference: true,
      analysis: true,
      conversation_starters: false,
      watch_label: "Watch",
      language: "en",
      region: "US"
    },
    reader: { role: "", location: "", region: "", local_terms: [], local_feeds: [], goals: [], watch_list: [] },
    countdown: { enabled: false, label: "", date: "", start: "", milestones: [] },
    delivery: { time: "06:15", timezone: "", channels: ["issue"] },
    weather: { enabled: false, place: "", latitude: null, longitude: null, units: "fahrenheit" },
    sources: { avoid_hosts: SOCIAL_HOSTS.slice(), prefer: [] },
    style: { no_em_dashes: true },
    categories: []
  };

  // ------------------------------------------------------------------ helpers
  function clone(v) { return v === undefined ? undefined : JSON.parse(JSON.stringify(v)); }
  function isObj(v) { return v !== null && typeof v === "object" && !Array.isArray(v); }
  function isStr(v) { return typeof v === "string"; }
  function isInt(v) { return typeof v === "number" && Number.isInteger(v); }
  function strList(v) { return Array.isArray(v) && v.every(isStr); }
  function collapse(s) { return String(s == null ? "" : s).replace(/\s+/g, " ").trim(); }
  const EM_DASH = String.fromCharCode(0x2014);
  // Feed text with each em dash turned into a hyphen; the length does not change.
  function noEmDash(s) { return s.split(EM_DASH).join("-"); }
  function cpLen(s) { return Array.from(s).length; }
  function isWordChar(ch) { return /^[A-Za-z0-9]$/.test(ch); }
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function round1(x) { return Math.floor(x * 10 + 0.5) / 10; }
  function has(map, key) { return Object.prototype.hasOwnProperty.call(map, key); }

  function merge(base, over) {
    const out = clone(base);
    if (!isObj(over)) return out;
    for (const k of Object.keys(over)) {
      if (isObj(out[k]) && isObj(over[k])) out[k] = merge(out[k], over[k]);
      else out[k] = clone(over[k]);
    }
    return out;
  }

  function parseIso(s) {
    if (!isStr(s) || !s.trim()) return null;
    const t = s.trim();
    if (!/^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/.test(t)) return null;
    let iso = t.replace(" ", "T");
    if (/T\d{2}:\d{2}$/.test(iso)) iso += ":00";
    if (/T/.test(iso) && !/(Z|[+-]\d{2}:?\d{2})$/.test(iso)) iso += "Z";
    iso = iso.replace(/([+-]\d{2})(\d{2})$/, "$1:$2");
    const y = +iso.slice(0, 4), mo = +iso.slice(5, 7), d = +iso.slice(8, 10);
    if (y < 1 || mo < 1 || mo > 12 || d < 1 || d > new Date(Date.UTC(y, mo, 0)).getUTCDate()) return null;
    const tm = /T(\d{2}):(\d{2}):(\d{2})/.exec(iso);
    if (tm && (+tm[1] > 23 || +tm[2] > 59 || +tm[3] > 59)) return null;
    const off = /([+-])(\d{2}):(\d{2})$/.exec(iso);
    if (off && (+off[2] > 23 || +off[3] > 59)) return null;
    const ms = Date.parse(iso.length === 10 ? iso + "T00:00:00Z" : iso);
    return Number.isNaN(ms) ? null : ms;
  }

  function isoZ(ms) { return new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z"); }

  function isDateStr(s) {
    if (!isStr(s) || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
    const ms = Date.parse(s + "T00:00:00Z");
    return !Number.isNaN(ms) && isoZ(ms).slice(0, 10) === s;
  }

  function daysBetween(a, b) { // whole days from date a to date b (YYYY-MM-DD)
    return Math.round((Date.parse(b + "T00:00:00Z") - Date.parse(a + "T00:00:00Z")) / 86400000);
  }

  /* A photo link the page may show: https only (an http picture breaks an https page), no quotes or spaces. */
  function validImage(u) {
    return isStr(u) && u.length <= 2000 && /^https:\/\/[^/?#\s"'<>\\]+\.[^/?#\s"'<>\\]+(?:[/?#][^\s"'<>\\]*)?$/i.test(u);
  }

  function isNum(v) { return typeof v === "number" && isFinite(v); }

  function validUrl(u) {
    if (!isStr(u)) return false;
    const m = /^https?:\/\/([^/?#\s]+)[^\s]*$/i.exec(u.trim());
    return !!m && m[1].indexOf(".") > 0;
  }

  function hostOf(u) {
    const m = /^https?:\/\/([^/?#\s]+)/i.exec(String(u || "").trim());
    if (!m) return "";
    let h = m[1].toLowerCase();
    const at = h.lastIndexOf("@");
    if (at >= 0) h = h.slice(at + 1);
    const colon = h.indexOf(":");
    if (colon >= 0) h = h.slice(0, colon);
    return h.indexOf("www.") === 0 ? h.slice(4) : h;
  }

  // ----------------------------------------------------------- term matching
  function isAcronym(term) {
    const len = Array.from(term).length;
    if (len < 2 || len > 6) return false;
    if (term !== term.toUpperCase()) return false;
    let caps = 0;
    for (const ch of term) if (ch >= "A" && ch <= "Z") caps += 1;
    return caps >= 2;
  }

  /* Whole-word match. Acronyms (AI, CVE, TSP) match case-sensitively so "AI"
     never matches "said" and "IT" never matches "it". */
  function termHit(text, term) {
    const t = collapse(term);
    if (!t) return false;
    const acr = isAcronym(t);
    const hay = acr ? String(text) : String(text).toLowerCase();
    const needle = acr ? t : t.toLowerCase();
    const wantBefore = isWordChar(needle[0]);
    const wantAfter = isWordChar(needle[needle.length - 1]);
    let from = 0;
    for (;;) {
      const i = hay.indexOf(needle, from);
      if (i < 0) return false;
      const before = i > 0 ? hay[i - 1] : "";
      const after = i + needle.length < hay.length ? hay[i + needle.length] : "";
      const okB = !wantBefore || !before || !isWordChar(before);
      const okA = !wantAfter || !after || !isWordChar(after);
      if (okB && okA) return true;
      from = i + 1;
    }
  }

  function countHits(text, terms) {
    const seen = Object.create(null);
    let n = 0;
    for (const term of terms) {
      const key = collapse(term).toLowerCase();
      if (!key || seen[key]) continue;
      seen[key] = true;
      if (termHit(text, term)) n += 1;
    }
    return n;
  }

  // ------------------------------------------------------------------ config
  /* A town category: it names the reader's town, or says it needs one. */
  // US states and the District of Columbia, "name CODE" pairs (mirrors US_STATES in engine.py).
  const US_STATES = {};
  "alabama AL|alaska AK|arizona AZ|arkansas AR|california CA|colorado CO|connecticut CT|delaware DE|district of columbia DC|florida FL|georgia GA|hawaii HI|idaho ID|illinois IL|indiana IN|iowa IA|kansas KS|kentucky KY|louisiana LA|maine ME|maryland MD|massachusetts MA|michigan MI|minnesota MN|mississippi MS|missouri MO|montana MT|nebraska NE|nevada NV|new hampshire NH|new jersey NJ|new mexico NM|new york NY|north carolina NC|north dakota ND|ohio OH|oklahoma OK|oregon OR|pennsylvania PA|rhode island RI|south carolina SC|south dakota SD|tennessee TN|texas TX|utah UT|vermont VT|virginia VA|washington WA|west virginia WV|wisconsin WI|wyoming WY".split("|").forEach(p => { const k = p.lastIndexOf(" "); US_STATES[p.slice(0, k)] = p.slice(k + 1); });
  const US_CODES = Object.keys(US_STATES).map(k => US_STATES[k]);

  /* The two-letter code of the US state named in the reader's region ("Florida", "FL",
     "Washington, D.C."), or "" for anything else (mirrors state_code in engine.py). */
  function stateCode(region) {
    const s = collapse(String(isStr(region) ? region : "").replace(/[.,]/g, " ")).toLowerCase();
    if (["dc", "d c", "washington dc", "washington d c"].indexOf(s) >= 0) return "DC";
    if (s.length === 2 && US_CODES.indexOf(s.toUpperCase()) >= 0) return s.toUpperCase();
    return Object.prototype.hasOwnProperty.call(US_STATES, s) ? US_STATES[s] : "";
  }

  function isLocalCategory(cat) {
    const t = JSON.stringify(cat || {});
    return !!(cat && cat.needs_location === true) || t.indexOf("{location}") >= 0 || t.indexOf("{local_terms}") >= 0;
  }

  const AREA_MAX = 4;  // the town and up to three nearby places in one search

  /* The town first, then nearby places of three or more letters, at most AREA_MAX. */
  function areaTerms(local) {
    const out = [];
    for (const t of local) {
      const v = collapse(String(t).split('"').join(""));
      if (!v || (out.length && v.length < 3)) continue;
      if (out.map(x => x.toLowerCase()).indexOf(v.toLowerCase()) < 0) out.push(v);
      if (out.length >= AREA_MAX) break;
    }
    return out;
  }

  /* In a search, the quoted town ("{location}") outside a group stands for your area:
     ("Town" OR "Nearby place" ...). Inside a group it stays the town (groups never nest). */
  function areaQuery(q, area) {
    const key = '"{location}"';
    const parts = String(q).split(key);
    let s = parts[0];
    for (let i = 1; i < parts.length; i++) {
      const depth = s.split("(").length - s.split(")").length;
      const group = "(" + area.map(t => '"' + t + '"').join(" OR ") + ")";
      s += (depth === 0 && area.length > 1 ? group : key) + parts[i];
    }
    return s;
  }

  function resolveCategory(cat, reader) {
    const c = clone(cat);
    const loc = collapse(reader && reader.location);
    const region = collapse(reader && reader.region);
    const sub = s => String(s).split("{location}").join(loc).split("{region}").join(region);
    const local = [];
    for (const t of [loc].concat((reader && reader.local_terms) || [])) {
      const v = collapse(t);
      if (v && local.map(x => x.toLowerCase()).indexOf(v.toLowerCase()) < 0) local.push(v);
    }
    c.name = sub(c.name || "");
    c.description = sub(c.description || "");
    const area = loc ? areaTerms(local) : [];
    c.queries = (c.queries || []).map(q => sub(areaQuery(q, area)));
    c.require = (c.require || []).map(group => {
      const out = [];
      for (const term of group) {
        if (term === "{local_terms}") local.forEach(v => out.push(v));
        else out.push(sub(term));
      }
      return out;
    });
    c.exclude = (c.exclude || []).map(sub);
    // The reader's own local news feeds count for every town category.
    if (isLocalCategory(cat)) {
      const feeds = Array.isArray(c.feeds) ? c.feeds.slice() : [];
      for (const u of (reader && Array.isArray(reader.local_feeds) ? reader.local_feeds : [])) {
        const v = collapse(u);
        if (validUrl(v) && feeds.indexOf(v) < 0) feeds.push(v);
      }
      c.feeds = feeds;
    }
    return c;
  }

  function normalizeConfig(cfg) {
    const out = merge(DEFAULTS, isObj(cfg) ? cfg : {});
    const cats = Array.isArray(out.categories) ? out.categories : [];
    out.categories = cats.filter(isObj).map((c, i) => {
      const base = {
        id: "", name: "", description: "", queries: [], require: [], exclude: [], feeds: [], topic_feeds: [],
        color: PALETTE[i % PALETTE.length], items: null, skip_listicles: false, needs_location: false, icon: ""
      };
      const m = merge(base, c);
      if (!isStr(m.color) || !/^#[0-9a-fA-F]{6}$/.test(m.color)) m.color = PALETTE[i % PALETTE.length];
      return m;
    });
    // Email delivery was removed in 0.2.0: older settings lose it quietly.
    delete out.email;
    if (isObj(out.delivery) && Array.isArray(out.delivery.channels)) {
      const ch = out.delivery.channels.filter(c => c !== "email");
      out.delivery.channels = ch.length ? ch : ["issue"];
    }
    return out;
  }

  function placeholderSet(s) {
    const found = [];
    const re = /\{([a-z_]+)\}/g;
    let m;
    while ((m = re.exec(String(s)))) found.push(m[1]);
    return found;
  }

  function validateConfig(cfg) {
    const errors = [];
    const warnings = [];
    if (!isObj(cfg)) return { errors: ["The settings are not a JSON object."], warnings };
    if (cfg.version !== undefined && cfg.version !== 1) errors.push("version must be 1.");
    for (const k of Object.keys(cfg)) {
      if (!has(DEFAULTS, k) && k !== "email") warnings.push("Unknown setting \"" + k + "\" is ignored.");
    }
    const n = normalizeConfig(cfg);
    const b = n.brief;
    const intRange = (v, lo, hi, label) => {
      if (!isInt(v) || v < lo || v > hi) errors.push(label + " must be a whole number from " + lo + " to " + hi + ".");
    };
    intRange(b.window_hours, 1, 168, "brief.window_hours");
    intRange(b.backfill_max_hours, 1, 336, "brief.backfill_max_hours");
    if (isInt(b.window_hours) && isInt(b.backfill_max_hours) && b.backfill_max_hours < b.window_hours) {
      errors.push("brief.backfill_max_hours must be at least brief.window_hours.");
    }
    intRange(b.items_per_category, 1, 10, "brief.items_per_category");
    intRange(b.summary_max_chars, 80, 1000, "brief.summary_max_chars");
    for (const k of ["title", "subject", "watch_label", "language", "region"]) {
      if (!isStr(b[k]) || !collapse(b[k])) errors.push("brief." + k + " must be text.");
    }
    if (isStr(b.subject)) {
      for (const p of placeholderSet(b.subject)) {
        if (SUBJECT_FIELDS.indexOf(p) < 0) errors.push("brief.subject uses {" + p + "}; allowed are {total}, {date}, {title} and {empty}.");
      }
    }
    for (const k of ["allow_reference", "analysis", "conversation_starters"]) {
      if (typeof b[k] !== "boolean") errors.push("brief." + k + " must be true or false.");
    }
    const r = n.reader;
    if (!isStr(r.role) || !isStr(r.location) || !isStr(r.region)) errors.push("reader.role, reader.location and reader.region must be text.");
    if (!strList(r.local_feeds) || r.local_feeds.length > 5 || !r.local_feeds.every(u => validUrl(collapse(u)))) {
      errors.push("reader.local_feeds must be a list of up to 5 http or https links.");
    }
    for (const k of ["local_terms", "goals", "watch_list"]) {
      if (!strList(r[k])) errors.push("reader." + k + " must be a list of text.");
    }
    const personal = JSON.stringify(r);
    if (/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/.test(personal)) {
      warnings.push("reader holds an email address; it is not needed and is better left out.");
    }
    if (/\d{3}[-. )]+\d{3}[-. ]+\d{4}/.test(personal)) {
      warnings.push("reader holds what looks like a phone number; it is not needed and is better left out.");
    }
    const cats = n.categories;
    if (!Array.isArray(cfg.categories) || cats.length === 0) errors.push("Add at least one category.");
    if (cats.length > MAX_CATEGORIES) errors.push("Use at most " + MAX_CATEGORIES + " categories.");
    const ids = Object.create(null);
    cats.forEach((c, i) => {
      const label = "Category " + (i + 1) + (c.id ? " (" + c.id + ")" : "");
      if (!isStr(c.id) || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$/.test(c.id)) {
        errors.push(label + ": id must be 1 to 32 letters, numbers, dashes or underscores.");
      } else {
        const key = c.id.toLowerCase();
        if (ids[key]) errors.push(label + ": id is used twice.");
        ids[key] = true;
      }
      if (!isStr(c.name) || !collapse(c.name) || cpLen(c.name) > 70) errors.push(label + ": name must be 1 to 70 characters.");
      if (!strList(c.queries) || c.queries.filter(q => collapse(q)).length === 0 || c.queries.length > 6) {
        errors.push(label + ": give 1 to 6 search queries.");
      }
      if (!Array.isArray(c.require) || !c.require.every(g => strList(g) && g.length > 0 && g.length <= 80)) {
        errors.push(label + ": require must be a list of term lists (1 to 80 terms each).");
      }
      if (!strList(c.exclude)) errors.push(label + ": exclude must be a list of text.");
      if (!strList(c.feeds) || !c.feeds.every(validUrl)) errors.push(label + ": feeds must be a list of http or https links.");
      if (!strList(c.topic_feeds) || !c.topic_feeds.every(validUrl)) errors.push(label + ": topic_feeds must be a list of http or https links.");
      if (c.items !== null && (!isInt(c.items) || c.items < 1 || c.items > 10)) {
        errors.push(label + ": items must be a whole number from 1 to 10.");
      }
      const texts = [c.name, c.description].concat(Array.isArray(c.queries) ? c.queries : [],
        Array.isArray(c.exclude) ? c.exclude : []);
      if (Array.isArray(c.require)) c.require.forEach(g => { if (Array.isArray(g)) g.forEach(t => texts.push(t)); });
      let usesLocal = false;
      for (const t of texts) {
        for (const p of placeholderSet(t)) {
          if (p !== "location" && p !== "local_terms" && p !== "region") errors.push(label + ": unknown placeholder {" + p + "}.");
          else usesLocal = true;
        }
      }
      if (!isStr(c.icon) || (c.icon && !/^[a-z0-9-]{1,32}$/.test(c.icon))) errors.push(label + ": icon must be a short name like weather or football.");
      if ((usesLocal || c.needs_location) && !collapse(r.location)) {
        errors.push(label + ": needs your town in reader.location.");
      }
    });
    const cd = n.countdown;
    if (cd.enabled === true) {
      if (!isStr(cd.label) || !collapse(cd.label)) errors.push("countdown.label must be text.");
      if (!isDateStr(cd.date)) errors.push("countdown.date must be a date like 2027-06-30.");
      if (cd.start && !isDateStr(cd.start)) errors.push("countdown.start must be a date like 2026-01-01.");
      if (isDateStr(cd.date) && isDateStr(cd.start) && cd.start > cd.date) errors.push("countdown.start must be before countdown.date.");
      if (!Array.isArray(cd.milestones) || !cd.milestones.every(m => isObj(m) && isDateStr(m.date) && isStr(m.label) && collapse(m.label))) {
        errors.push("countdown.milestones must be a list of {date, label}.");
      }
    } else if (cd.enabled !== false) {
      errors.push("countdown.enabled must be true or false.");
    }
    const dv = n.delivery;
    if (!isStr(dv.time) || (dv.time && !/^([01]\d|2[0-3]):[0-5]\d$/.test(dv.time))) errors.push("delivery.time must be a time like 06:15, or empty.");
    if (!isStr(dv.timezone) || (dv.timezone && !/^[A-Za-z_]+(\/[A-Za-z0-9_+-]+)*$/.test(dv.timezone))) errors.push("delivery.timezone must be a time zone name like America/New_York, or empty.");
    if (!strList(dv.channels) || !dv.channels.length || !dv.channels.every(c => c === "issue")) {
      errors.push('delivery.channels must be ["issue"].');
    }
    const w = n.weather;
    if (!isObj(w) || typeof w.enabled !== "boolean") errors.push("weather.enabled must be true or false.");
    else if (w.enabled) {
      if (!(isNum(w.latitude) && w.latitude >= -90 && w.latitude <= 90 && isNum(w.longitude) && w.longitude >= -180 && w.longitude <= 180)) {
        errors.push("weather needs a place: pick your town so the forecast knows where you are.");
      }
      if (w.units !== "fahrenheit" && w.units !== "celsius") errors.push("weather.units must be fahrenheit or celsius.");
      if (!isStr(w.place)) errors.push("weather.place must be text.");
    }
    if (!strList(n.sources.avoid_hosts)) errors.push("sources.avoid_hosts must be a list of text.");
    if (typeof n.style.no_em_dashes !== "boolean") errors.push("style.no_em_dashes must be true or false.");
    return { errors, warnings };
  }

  function categoryFromLibrary(lib, id) {
    const hit = ((lib && lib.categories) || []).filter(c => c.id === id)[0];
    if (!hit) return null;
    const c = clone(hit);
    delete c.group;
    return c;
  }

  function configFromPack(lib, packId, overrides) {
    const pack = ((lib && lib.packs) || []).filter(p => p.id === packId)[0];
    const cats = pack ? pack.categories.map(id => categoryFromLibrary(lib, id)).filter(Boolean) : [];
    return merge(merge(DEFAULTS, { categories: cats }), overrides || {});
  }

  // ------------------------------------------------------------- identities
  function normUrl(u) {
    const s = collapse(u);
    const m = /^(https?):\/\/([^/?#]+)([^?#]*)(\?[^#]*)?(#.*)?$/i.exec(s);
    if (!m) return s.toLowerCase();
    let host = m[2].toLowerCase();
    if (host.indexOf("www.") === 0) host = host.slice(4);
    let path = m[3] || "";
    while (path.length > 1 && path[path.length - 1] === "/") path = path.slice(0, -1);
    if (path === "/") path = "";
    const kept = [];
    for (const part of (m[4] || "").replace(/^\?/, "").split("&")) {
      if (!part) continue;
      const key = part.split("=")[0].toLowerCase();
      if (key.indexOf("utm_") === 0 || TRACKING.indexOf(key) >= 0) continue;
      kept.push(part);
    }
    kept.sort();
    return host + path + (kept.length ? "?" + kept.join("&") : "");
  }

  function stripOutlet(title) {
    const t = collapse(title);
    for (const sep of [" - ", " | "]) {
      const i = t.lastIndexOf(sep);
      if (i > 0) {
        const head = t.slice(0, i);
        const tail = t.slice(i + sep.length);
        if (tail.split(" ").length <= 6 && head.split(" ").length >= 4) return head;
      }
    }
    return t;
  }

  function normTitle(title) {
    return stripOutlet(title).toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }

  function titleTokens(title) {
    const out = [];
    for (const w of normTitle(title).split(" ")) {
      if (w.length >= 3 && STOP.indexOf(w) < 0 && out.indexOf(w) < 0) out.push(w);
    }
    return out;
  }

  function nearDup(a, b) {
    const ta = Array.isArray(a) ? a : titleTokens(a);
    const tb = Array.isArray(b) ? b : titleTokens(b);
    if (ta.length < 4 || tb.length < 4) return false;
    const sb = Object.create(null);
    tb.forEach(w => { sb[w] = true; });
    let inter = 0;
    ta.forEach(w => { if (sb[w]) inter += 1; });
    const union = ta.length + tb.length - inter;
    return inter / union >= 0.75;
  }

  // ------------------------------------------------------------------ ledger
  function emptyLedger() { return { version: 1, urls: {}, titles: {}, recent: [], sent_dates: [] }; }

  function cleanLedger(l) {
    const out = emptyLedger();
    if (!isObj(l)) return out;
    if (isObj(l.urls)) for (const k of Object.keys(l.urls)) if (isStr(l.urls[k])) out.urls[k] = l.urls[k];
    if (isObj(l.titles)) for (const k of Object.keys(l.titles)) if (isStr(l.titles[k])) out.titles[k] = l.titles[k];
    if (Array.isArray(l.recent)) out.recent = l.recent.filter(isStr).slice(-MAX_RECENT);
    if (Array.isArray(l.sent_dates)) out.sent_dates = l.sent_dates.filter(isDateStr).slice(-MAX_SENT_DATES);
    return out;
  }

  /* The recent headlines' words, read once, with each word pointing at the
     headlines that use it, so near-duplicate checks stay fast with a full history. */
  function recentIndex(ledger) {
    const toks = ledger.recent.map(titleTokens);
    const index = new Map();
    toks.forEach((tk, i) => {
      if (tk.length >= 4) for (const w of tk) { if (!index.has(w)) index.set(w, []); index.get(w).push(i); }
    });
    return { toks: toks, index: index };
  }

  function ledgerHas(ledger, item, idx) {
    if (!ledger) return false;
    const nu = normUrl(item.url);
    const nt = normTitle(item.title);
    if (nu && has(ledger.urls, nu)) return true;
    if (nt && has(ledger.titles, nt)) return true;
    const toks = titleTokens(item.title);
    if (toks.length < 4) return false;
    const ix = idx || recentIndex(ledger);
    const shared = new Map();  // headline -> words in common; the same test as nearDup
    for (const w of toks) for (const i of ix.index.get(w) || []) shared.set(i, (shared.get(i) || 0) + 1);
    for (const [i, inter] of shared) if (inter / (toks.length + ix.toks[i].length - inter) >= 0.75) return true;
    return false;
  }

  function pruneMap(map) {
    const keys = Object.keys(map);
    if (keys.length <= MAX_LEDGER) return map;
    keys.sort((a, b) => (map[a] < map[b] ? -1 : map[a] > map[b] ? 1 : a < b ? -1 : a > b ? 1 : 0));
    const out = {};
    keys.slice(keys.length - MAX_LEDGER).forEach(k => { out[k] = map[k]; });
    return out;
  }

  // sent === false ("Mark as read") leaves the day's delivery open, so a scheduled send still goes out.
  function ledgerAdd(ledger, brief, sent) {
    const l = cleanLedger(ledger);
    const day = isDateStr(brief && brief.date) ? brief.date : "1970-01-01";
    for (const cat of (brief && brief.categories) || []) {
      for (const it of cat.items || []) {
        const nu = normUrl(it.url);
        const nt = normTitle(it.title);
        if (nu) l.urls[nu] = day;
        if (nt) { l.titles[nt] = day; l.recent.push(nt); }
      }
    }
    l.recent = l.recent.slice(-MAX_RECENT);
    if (sent !== false && l.sent_dates.indexOf(day) < 0) l.sent_dates.push(day);
    l.sent_dates = l.sent_dates.slice(-MAX_SENT_DATES);
    l.urls = pruneMap(l.urls);
    l.titles = pruneMap(l.titles);
    return l;
  }

  function ledgerSize(ledger) { return ledger ? Object.keys(ledger.urls || {}).length : 0; }

  // ---------------------------------------------------------- freshness
  function humanizeAge(hours) {
    if (typeof hours !== "number" || !isFinite(hours)) return "undated";
    const h = Math.max(0, hours);
    if (h < 1) return "under 1h";
    if (h < 24) return Math.floor(h) + "h ago";
    const d = Math.floor(h / 24);
    const rem = Math.floor(h - d * 24);
    return rem ? d + "d " + rem + "h ago" : d + "d ago";
  }

  function classify(publishedMs, nowMs, brief) {
    if (publishedMs === null) {
      return brief.allow_reference ? { recency: "reference", age: null } : { reject: "undated" };
    }
    let age = (nowMs - publishedMs) / 3600000;
    if (age < -48) return { reject: "bad date" };
    if (age < 0) age = 0;
    if (age <= brief.window_hours) return { recency: "news", age: age };
    if (age <= brief.backfill_max_hours) return { recency: "backfill", age: age };
    return { reject: "too old" };
  }

  function cutSummary(text, max) {
    const s = collapse(text);
    const cps = Array.from(s);
    if (cps.length <= max) return s;
    let head = cps.slice(0, max - 3);
    const sp = head.lastIndexOf(" ");  // code points, like Python
    if (sp > max / 2) head = head.slice(0, sp);
    return head.join("").replace(/[ ,.;:]+$/, "") + "...";
  }

  // ---------------------------------------------------------------- gating
  function gateItem(item, cat, cfg) {
    const text = item.title + " " + (item.summary || "");
    const hosts = (cfg.sources.avoid_hosts || []).map(h => String(h).toLowerCase().replace(/^www\./, ""));
    for (const h of [hostOf(item.url), hostOf(item.source_url)]) {
      if (!h) continue;
      for (const bad of hosts) if (bad && (h === bad || h.slice(-(bad.length + 1)) === "." + bad)) return "social or avoided site";
    }
    for (const p of PAPERWORK) if (termHit(item.title, p)) return "paperwork notice";
    if (cat.skip_listicles) {
      const t = item.title.trim().toLowerCase();
      if (/^(top|best)\s+\d+\b/.test(t) || termHit(t, "to watch") || /\bbest\b.*\b20\d\d\b/.test(t)) return "list article";
    }
    for (const term of cat.exclude || []) if (termHit(text, term)) return "excluded term";
    // A story from one of the category's on-topic feeds needs no must-mention term.
    if (item.on_topic) return null;
    for (const group of cat.require || []) {
      if (group.length && !group.some(term => termHit(text, term))) return "off topic";
    }
    return null;
  }

  function cleanItem(raw, maxChars) {
    const it = {
      title: noEmDash(collapse(raw && raw.title)),
      url: collapse(raw && raw.url),
      source: noEmDash(collapse(raw && raw.source)),
      source_url: collapse(raw && raw.source_url),
      published: null,
      summary: noEmDash(cutSummary((raw && raw.summary) || "", maxChars)),
      image: "",
      on_topic: !!(raw && raw.on_topic === true)
    };
    const img = collapse(raw && raw.image);
    if (validImage(img)) it.image = img;
    const pub = raw && raw.published;
    const ms = parseIso(pub);
    it.published_ms = ms;
    it.published = ms === null ? null : isoZ(ms);
    // A date that is present but unreadable is not "undated": the story may be years old.
    it.bad_date = ms === null && isStr(pub) && collapse(pub) !== "";
    if (it.source && it.title.slice(-(it.source.length + 3)) === " - " + it.source) {
      it.title = collapse(it.title.slice(0, it.title.length - it.source.length - 3));
    }
    if (it.summary && normTitle(it.summary) === normTitle(it.title)) it.summary = "";
    return it;
  }

  function score(it, cat, brief) {
    let s;
    if (it.recency === "news") s = 4.0 - 2.0 * Math.min(it.age / brief.window_hours, 1);
    else if (it.recency === "backfill") {
      const span = Math.max(brief.backfill_max_hours - brief.window_hours, 1);
      s = 1.5 - 0.5 * Math.min((it.age - brief.window_hours) / span, 1);
    } else s = 0.5;
    let terms = [];
    for (const g of cat.require || []) terms = terms.concat(g);
    return s + 0.25 * Math.min(countHits(it.title, terms), 4);
  }

  /* candidates: {categoryId: [{title, url, source, source_url, published, summary}]}.
     Returns a brief. Fresh news first, then labelled older items, then undated
     reference pages, each by score; a category is never padded with repeats. */
  function selectBrief(candidates, cfg, ledger, nowIso, dateStr, source) {
    const n = normalizeConfig(cfg);
    const b = n.brief;
    const nowMs = parseIso(nowIso);
    const takenUrls = Object.create(null);
    const takenTitles = Object.create(null);
    const takenToks = [];
    const out = [];
    let withheld = 0;
    const idx = ledger ? recentIndex(ledger) : null;
    const rank = { news: 0, backfill: 1, reference: 2 };
    for (const raw of n.categories) {
      const cat = resolveCategory(raw, n.reader);
      const rejected = {};
      const bump = r => { rejected[r] = (rejected[r] || 0) + 1; };
      const pool = [];
      const list = candidates && has(candidates, raw.id) && Array.isArray(candidates[raw.id]) ? candidates[raw.id] : [];
      for (const cand of list) {
        const it = cleanItem(cand, b.summary_max_chars);
        if (!it.title || !validUrl(it.url)) { bump("missing title or link"); continue; }
        const why = gateItem(it, cat, n);
        if (why) { bump(why); continue; }
        if (it.bad_date) { bump("unreadable date"); continue; }
        const cls = classify(it.published_ms, nowMs, b);
        if (cls.reject) { bump(cls.reject); continue; }
        it.recency = cls.recency;
        it.age = cls.age;
        if (ledger && ledgerHas(ledger, it, idx)) { bump("already sent"); withheld += 1; continue; }
        it.score = score(it, cat, b);
        pool.push(it);
      }
      pool.sort((x, y) => {
        if (rank[x.recency] !== rank[y.recency]) return rank[x.recency] - rank[y.recency];
        if (x.score !== y.score) return y.score - x.score;
        const px = x.published_ms === null ? -Infinity : x.published_ms;
        const py = y.published_ms === null ? -Infinity : y.published_ms;
        if (px !== py) return py - px;
        return x.title < y.title ? -1 : x.title > y.title ? 1 : 0;
      });
      const want = raw.items === null || raw.items === undefined ? b.items_per_category : raw.items;
      const picked = [];
      for (const it of pool) {
        if (picked.length >= want) break;
        const nu = normUrl(it.url);
        const nt = normTitle(it.title);
        const toks = titleTokens(it.title);
        if (takenUrls[nu] || takenTitles[nt] || takenToks.some(t => nearDup(toks, t))) { bump("duplicate"); continue; }
        takenUrls[nu] = true;
        takenTitles[nt] = true;
        takenToks.push(toks);
        picked.push({
          title: it.title, url: it.url, source: it.source, published: it.published,
          recency: it.recency, age_hours: it.age === null ? null : round1(it.age), summary: it.summary, image: it.image
        });
      }
      out.push({ id: cat.id, name: cat.name, color: cat.color, icon: cat.icon, items: picked, rejected: rejected });
    }
    const total = out.reduce((a, c) => a + c.items.length, 0);
    return {
      schema: SCHEMA, title: b.title, date: dateStr, generated_at: isoZ(nowMs),
      window_hours: b.window_hours, backfill_max_hours: b.backfill_max_hours,
      items_per_category: b.items_per_category, source: source || "desktop",
      total: total, empty: out.filter(c => c.items.length === 0).length,
      withheld: withheld, ledger_applied: !!ledger, categories: out, analysis: null
    };
  }

  /* Drop items a reader has already been sent (for briefs written by an AI). */
  function filterSeen(brief, ledger) {
    const b = clone(brief);
    let withheld = 0;
    const idx = ledger ? recentIndex(ledger) : null;
    for (const cat of b.categories || []) {
      const kept = [];
      for (const it of cat.items || []) {
        if (ledgerHas(ledger, { title: String(it.title || ""), url: String(it.url || "") }, idx)) withheld += 1;
        else kept.push(it);
      }
      cat.items = kept;
    }
    b.withheld = (isInt(b.withheld) ? b.withheld : 0) + withheld;
    b.ledger_applied = true;
    b.total = (b.categories || []).reduce((a, c) => a + (c.items || []).length, 0);
    b.empty = (b.categories || []).filter(c => !(c.items || []).length).length;
    return { brief: b, withheld: withheld };
  }

  // ------------------------------------------------------------ brief check
  function briefTexts(brief) {
    const out = [];
    const push = (where, v) => { if (isStr(v)) out.push([where, v]); };
    push("title", brief.title);
    for (const cat of brief.categories || []) {
      push((cat.id || "?") + " name", cat.name);
      push((cat.id || "?") + " signal", cat.signal);
      push((cat.id || "?") + " so_what", cat.so_what);
      (cat.items || []).forEach((it, i) => {
        const w = (cat.id || "?") + " item " + (i + 1);
        push(w + " title", it.title);
        push(w + " summary", it.summary);
        push(w + " starter", it.starter);
      });
    }
    const a = brief.analysis;
    if (isObj(a)) {
      (Array.isArray(a.top_three) ? a.top_three : []).forEach((t, i) => push("analysis top " + (i + 1), t));
      push("analysis connection", a.connection);
      (Array.isArray(a.watch) ? a.watch : [a.watch]).forEach((t, i) => push("analysis watch " + (i + 1), t));
      push("analysis action", a.action);
    }
    return out;
  }

  function checkBrief(brief, cfg, nowIso) {
    const errors = [];
    const warnings = [];
    if (!isObj(brief)) return { errors: ["The brief is not a JSON object."], warnings };
    if (!Array.isArray(brief.categories)) return { errors: ["The brief has no categories list."], warnings };
    const n = normalizeConfig(cfg || {});
    const b = n.brief;
    const win = isInt(brief.window_hours) ? brief.window_hours : b.window_hours;
    const back = isInt(brief.backfill_max_hours) ? brief.backfill_max_hours : b.backfill_max_hours;
    // Without settings a category may hold up to 10 stories, the most any setting allows.
    const per = cfg ? b.items_per_category : 10;
    const maxChars = b.summary_max_chars;
    if (brief.schema !== SCHEMA) warnings.push("schema should be \"" + SCHEMA + "\".");
    if (!isDateStr(brief.date)) errors.push("date must be a date like 2026-10-23.");
    const refMs = parseIso(brief.generated_at) !== null ? parseIso(brief.generated_at) : parseIso(nowIso);
    if (refMs === null) errors.push("generated_at must be a time like 2026-10-23T11:00:00Z.");
    const seenUrls = Object.create(null);
    const allToks = [];
    let total = 0;
    const cfgIds = cfg ? n.categories.map(c => c.id) : [];
    brief.categories.forEach((cat, ci) => {
      if (!isObj(cat) || !isStr(cat.id) || !collapse(cat.id) || !isStr(cat.name) || !collapse(cat.name)) {
        errors.push("Category " + (ci + 1) + " needs an id and a name.");
        return;
      }
      if (cfg && cfgIds.indexOf(cat.id) < 0) warnings.push(cat.id + ": not one of your categories.");
      const items = Array.isArray(cat.items) ? cat.items : [];
      if (!Array.isArray(cat.items)) errors.push(cat.id + ": items must be a list.");
      const limit = cfg ? ((n.categories.filter(c => c.id === cat.id)[0] || {}).items || per) : per;
      if (items.length > limit) errors.push(cat.id + ": has " + items.length + " items; the limit is " + limit + ".");
      items.forEach((it, i) => {
        const w = cat.id + " item " + (i + 1);
        total += 1;
        if (!isObj(it)) { errors.push(w + ": is not an object."); return; }
        if (!isStr(it.title) || !collapse(it.title)) errors.push(w + ": needs a title.");
        if (!validUrl(it.url)) errors.push(w + ": needs an http or https link.");
        else {
          const nu = normUrl(it.url);
          if (seenUrls[nu]) errors.push(w + ": repeats the link in " + seenUrls[nu] + ".");
          else seenUrls[nu] = w;
        }
        if (RECENCY.indexOf(it.recency) < 0) errors.push(w + ": recency must be news, backfill or reference.");
        const pms = parseIso(it.published);
        if (it.published !== null && it.published !== undefined && pms === null) errors.push(w + ": published is not a valid time.");
        if (refMs !== null && pms !== null) {
          const age = (refMs - pms) / 3600000;
          if (age < -2) warnings.push(w + ": published is in the future.");
          if (it.recency === "news" && age > win + 1) errors.push(w + ": marked news but is " + humanizeAge(age).replace(" ago", "") + " old; the window is " + win + "h.");
          if (it.recency === "backfill" && age > back + 1) errors.push(w + ": older than the " + back + "h limit.");
          if (it.recency === "backfill" && age <= win) warnings.push(w + ": inside the window, so it should be news.");
        }
        if ((it.recency === "news" || it.recency === "backfill") && pms === null) errors.push(w + ": " + it.recency + " items need a published time.");
        if (it.recency === "reference" && pms !== null) warnings.push(w + ": reference items should have no date.");
        if (it.image !== undefined && it.image !== null && it.image !== "" && !validImage(it.image)) warnings.push(w + ": image must be an https link to a picture; it will not be shown.");
        if (isStr(it.summary) && cpLen(it.summary) > maxChars) warnings.push(w + ": summary is longer than " + maxChars + " characters.");
        if (isStr(it.title)) {
          const toks = titleTokens(it.title);
          for (const prev of allToks) {
            if (nearDup(toks, prev[1])) { warnings.push(w + ": looks like the same story as " + prev[0] + "."); break; }
          }
          allToks.push([w, toks]);
        }
      });
    });
    if (cfg) {
      const ids = brief.categories.filter(isObj).map(c => c.id);
      for (const id of cfgIds) if (ids.indexOf(id) < 0) warnings.push(id + ": missing from the brief.");
    }
    if (brief.total !== undefined && brief.total !== total) errors.push("total says " + brief.total + " but the brief holds " + total + " items.");
    if (b && n.style.no_em_dashes) {
      for (const pair of briefTexts(brief)) if (pair[1].indexOf("\u2014") >= 0) errors.push(pair[0] + ": contains an em dash.");
    }
    const wx = brief.weather;
    if (wx !== null && wx !== undefined && !(isObj(wx) && Array.isArray(wx.days))) warnings.push("weather must be an object with a days list; it will not be shown.");
    const a = brief.analysis;
    if (a !== null && a !== undefined) {
      if (!isObj(a)) errors.push("analysis must be an object or null.");
      else if (Array.isArray(a.top_three) && a.top_three.length > 3) warnings.push("analysis.top_three has more than three entries.");
    }
    return { errors, warnings };
  }

  // ---------------------------------------------------------- AI hand-off
  function buildPrompt(promptText, cfg, compact) {
    const begin = "<!-- CONFIG:BEGIN -->";
    const end = "<!-- CONFIG:END -->";
    const i = promptText.indexOf(begin);
    const j = promptText.indexOf(end);
    if (i < 0 || j < i) throw new Error("The prompt has no configuration markers.");
    // cfg "file" means the settings travel as a separate knowledge file (size-limited boxes).
    const body = cfg === "file" ? FILE_NOTE : cfg ? "Saved configuration (use it; skip the interview unless I ask to change it):\n\n```json\n" +
      (compact ? JSON.stringify(cfg) : JSON.stringify(cfg, null, 2)) + "\n```" : "No settings are saved in this prompt. Use an attached daily-brief-settings.json or the latest settings JSON in this conversation; if there is none, start with the setup interview.";
    return promptText.slice(0, i + begin.length) + "\n" + body + "\n" + promptText.slice(j);
  }

  /* Finds the brief or settings JSON in text pasted from an AI chat. */
  function extractJson(text) {
    const s = String(text || "");
    const fence = /```(?:json)?\s*([\s\S]*?)```/gi;
    let m;
    const blocks = [];
    while ((m = fence.exec(s))) blocks.push(m[1]);
    blocks.push(s);
    for (const block of blocks) {
      const start = block.indexOf("{");
      if (start < 0) continue;
      let depth = 0, inStr = false, esc = false;
      for (let k = start; k < block.length; k++) {
        const ch = block[k];
        if (inStr) {
          if (esc) esc = false;
          else if (ch === "\\") esc = true;
          else if (ch === "\"") inStr = false;
        } else if (ch === "\"") inStr = true;
        else if (ch === "{") depth += 1;
        else if (ch === "}") {
          depth -= 1;
          if (depth === 0) {
            try { return JSON.parse(block.slice(start, k + 1)); } catch (e) { break; }
          }
        }
      }
    }
    return null;
  }

  /* The UTC cron lines that hit a local time in a time zone in winter and in
     summer (twin of dailybrief.schedule.crons_for). Empty if the zone is unknown. */
  function tzOffsetMinutes(tz, ms) {
    const parts = new Intl.DateTimeFormat("en-US", { timeZone: tz, hourCycle: "h23", year: "numeric", month: "2-digit",
      day: "2-digit", hour: "2-digit", minute: "2-digit" }).formatToParts(new Date(ms));
    const get = t => +parts.filter(p => p.type === t)[0].value;
    const asUtc = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour") % 24, get("minute"));
    return Math.round((asUtc - Math.floor(ms / 60000) * 60000) / 60000);
  }

  function cronLines(time, tz, year) {
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(time || "") || !tz) return [];
    try { new Intl.DateTimeFormat("en-US", { timeZone: tz }); } catch (e) { return []; }
    const hh = +time.slice(0, 2), mm = +time.slice(3, 5);
    const out = [];
    for (const month of [0, 6]) {
      const wall = Date.UTC(year, month, 15, hh, mm);
      let utc = wall - tzOffsetMinutes(tz, wall) * 60000;
      utc = wall - tzOffsetMinutes(tz, utc) * 60000;
      const d = new Date(utc);
      const line = d.getUTCMinutes() + " " + d.getUTCHours() + " * * *";
      if (out.indexOf(line) < 0) out.push(line);
    }
    return out.sort((a, b) => (+a.split(" ")[1] - +b.split(" ")[1]) || (+a.split(" ")[0] - +b.split(" ")[0]));
  }

  function googleNewsUrl(query, days, cfg) {
    const b = normalizeConfig(cfg).brief;
    const q = query + " when:" + days + "d";
    return "https://news.google.com/rss/search?q=" + encodeURIComponent(q) +
      "&hl=" + b.language + "-" + b.region + "&gl=" + b.region + "&ceid=" + b.region + ":" + b.language;
  }

  return {
    VERSION, SCHEMA, DEFAULTS, PALETTE, SOCIAL_HOSTS, MAX_CATEGORIES, MAX_LEDGER, MAX_RECENT,
    clone, merge, collapse, parseIso, isoZ, isDateStr, daysBetween, validUrl, validImage, isNum, hostOf, round1, pad2,
    isAcronym, termHit, countHits, US_STATES, stateCode, isLocalCategory, areaTerms, areaQuery, resolveCategory, normalizeConfig, validateConfig,
    categoryFromLibrary, configFromPack, normUrl, stripOutlet, normTitle, titleTokens, nearDup,
    emptyLedger, cleanLedger, ledgerHas, ledgerAdd, ledgerSize, humanizeAge, classify, cutSummary,
    gateItem, cleanItem, selectBrief, filterSeen, checkBrief, buildPrompt, extractJson, googleNewsUrl, cronLines
  };
});
