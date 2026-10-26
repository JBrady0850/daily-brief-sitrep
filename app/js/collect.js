/* Daily Brief browser collector: gathers today's stories right at the web
   address, with no server, account or key.

   Sources, all free:
   - the GDELT DOC 2.0 news search (api.gdeltproject.org), which allows web
     pages to read it. It turns busy clients away with an error, so requests
     go one at a time with a pause between them, and a failed one is retried
     once;
   - publisher feeds that allow web pages to read them (most do not; those
     simply report "not readable from a web page");
   - Open-Meteo (open-meteo.com) for the forecast and for finding your town;
   - for Things to Do, the community calendar of the nearest local TV station
     (CitySpark), asked for the week's events near the town.

   The engine (engine.js) then picks the brief exactly as the desktop app does. */
(function (root, factory) {
  const node = typeof module === "object" && module.exports;
  const api = factory(node ? require("./engine.js") : root.DB_ENGINE, root);
  if (node) module.exports = api;
  else root.DB_COLLECT = api;
})(typeof self !== "undefined" ? self : this, function (E, root) {
  "use strict";

  const GDELT = "https://api.gdeltproject.org/api/v2/doc/doc";
  const FORECAST = "https://api.open-meteo.com/v1/forecast";
  const GEOCODE = "https://geocoding-api.open-meteo.com/v1/search";
  // Pause between GDELT requests. Tests set window.DB_COLLECT_GAP before this file loads.
  const GAP_MS = root && typeof root.DB_COLLECT_GAP === "number" ? root.DB_COLLECT_GAP : 6000;
  const TIMEOUT_MS = 25000;
  // The news search phase stops starting searches after this long, so a slow news
  // index cannot hold a brief for minutes. Tests set window.DB_COLLECT_SEARCH_BUDGET.
  const SEARCH_BUDGET_MS = root && typeof root.DB_COLLECT_SEARCH_BUDGET === "number" ? root.DB_COLLECT_SEARCH_BUDGET : 90000;
  // The backup collection, published beside the app by GitHub every four hours (dailybrief/newscache.py).
  const BACKUP_URL = "data/news-cache.json";
  const BACKUP_SCHEMA = "daily-brief-news-cache/1";
  // Local TV station news by state, published beside the app by GitHub every four hours (dailybrief/localnews.py).
  const LOCAL_DIR = "data/local/";
  const LOCAL_SCHEMA = "daily-brief-local-news/1";
  // Things to Do: events from the community calendars of local TV stations (CitySpark),
  // read from this browser for this reader only. app/data/calendars.js lists the calendars.
  const CALENDAR_API = "https://portal.cityspark.com/api/events/GetEventsByDay/";
  const EVENT_MILES = 20;     // how far from the town an event may be
  const EVENT_TOWN_MILES = 5; // the town itself, asked first so its own events lead
  const EVENT_DAYS = 7;       // today and the next six days
  const EVENT_CALENDARS = 2;  // the nearest calendars, the second only when the first is short
  const LANGS = { en: "english", es: "spanish", fr: "french", de: "german", it: "italian", pt: "portuguese", nl: "dutch" };

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  /* A state's local news file: {schema, generated_at, state, stations, stories: [story]}. */
  function parseLocal(text) {
    let d;
    try { d = JSON.parse(text); } catch (e) { throw new Error("the local news file is damaged"); }
    if (!d || d.schema !== LOCAL_SCHEMA || !Array.isArray(d.stories)) throw new Error("not a local news file");
    return { generated_at: typeof d.generated_at === "string" ? d.generated_at : "", state: typeof d.state === "string" ? d.state : "",
      stories: d.stories.filter(it => it && typeof it === "object" && !Array.isArray(it)) };
  }

  /* The backup collection file: {schema, generated_at, categories: {id: [story]}}.
     Every story still goes through the same checks as any other. */
  function parseBackup(text) {
    let d;
    try { d = JSON.parse(text); } catch (e) { throw new Error("the backup collection file is damaged"); }
    if (!d || d.schema !== BACKUP_SCHEMA || !d.categories || typeof d.categories !== "object" || Array.isArray(d.categories)) {
      throw new Error("not a backup collection file");
    }
    const cats = {};
    for (const k of Object.keys(d.categories)) if (Array.isArray(d.categories[k])) cats[k] = d.categories[k].slice(0, 40);
    return { generated_at: typeof d.generated_at === "string" ? d.generated_at : "", categories: cats };
  }

  /* GDELT reads the same query language as Google News for what the library
     uses: quoted phrases, OR inside parentheses, AND by spaces. */
  function gdeltQuery(q, cfg) {
    const n = E.normalizeConfig(cfg || {});
    let s = E.collapse(q).replace(/\bwhen:\S+/g, "");
    const lang = LANGS[n.brief.language];
    if (lang) s += " sourcelang:" + lang;
    return E.collapse(s);
  }

  function gdeltUrl(q, hours, cfg) {
    return GDELT + "?query=" + encodeURIComponent(gdeltQuery(q, cfg)) + "&mode=artlist&format=json&maxrecords=75&sort=datedesc&timespan=" +
      Math.max(1, Math.round(hours)) + "h";
  }

  /* GDELT spaces out punctuation in headlines ("end ( and more )"); put it back. */
  function tidyTitle(t) {
    return E.collapse(String(t || "")
      .replace(/\s+([,:;!?.%)\]])/g, "$1").replace(/([(\[$])\s+/g, "$1")
      .replace(/\s+'\s*(s|re|ve|ll|d|t|m)\b/gi, "'$1").replace(/\s+’\s*(s|re|ve|ll|d|t|m)\b/gi, "’$1")
      .replace(/(\d)\s*,\s*(\d{3})\b/g, "$1,$2"));
  }

  function gdeltDate(s) {
    const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(String(s || ""));
    return m ? m[1] + "-" + m[2] + "-" + m[3] + "T" + m[4] + ":" + m[5] + ":" + m[6] + "Z" : "";
  }

  function parseGdelt(text) {
    let data;
    try { data = JSON.parse(text); } catch (e) {
      throw new Error("GDELT said: " + E.collapse(String(text).replace(/<[^>]*>/g, " ")).slice(0, 140));
    }
    const arts = data && Array.isArray(data.articles) ? data.articles : [];
    return arts.map(a => ({
      title: tidyTitle(a.title),
      url: E.collapse(a.url),
      published: gdeltDate(a.seendate),
      summary: "",
      source: E.collapse(a.domain),
      source_url: a.domain ? "https://" + E.collapse(a.domain) : "",
      image: E.validImage(E.collapse(a.socialimage)) ? E.collapse(a.socialimage) : ""
    }));
  }

  // ------------------------------------------------------------ feeds
  function htmlToText(s) {
    const box = String(s || "").replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ").replace(/<[^>]*>/g, " ");
    const txt = typeof document !== "undefined" ? decode(box) : box;
    return E.collapse(txt);
  }

  function decode(s) {
    const d = new DOMParser().parseFromString("<!doctype html><body>" + s.replace(/</g, "&lt;"), "text/html");
    return d.body.textContent || "";
  }

  function firstSentences(text, n) {
    const parts = String(text).match(/[^.!?]+[.!?]+(\s|$)/g);
    return parts ? E.collapse(parts.slice(0, n).join(" ")) : E.collapse(text);
  }

  function kids(el, name) {
    const out = [];
    for (const c of Array.from(el.children || [])) if ((c.localName || c.nodeName) === name) out.push(c);
    return out;
  }

  function kidText(el, name) { const k = kids(el, name)[0]; return k ? k.textContent || "" : ""; }

  function imageOf(it) {
    const isImg = c => {
      const t = (c.getAttribute("type") || "").toLowerCase();
      const medium = (c.getAttribute("medium") || "").toLowerCase();
      return medium === "image" || t.indexOf("image/") === 0 || (!t && !medium);
    };
    const cands = [];
    for (const c of Array.from(it.getElementsByTagName("*"))) {
      const ln = c.localName;
      if ((ln === "content" && c.getAttribute("url") && isImg(c)) || ln === "thumbnail") cands.push(c.getAttribute("url"));
      else if (ln === "enclosure" && /^image\//i.test(c.getAttribute("type") || "")) cands.push(c.getAttribute("url"));
    }
    const html = kidText(it, "encoded") + " " + kidText(it, "description") + " " + kidText(it, "content") + " " + kidText(it, "summary");
    const m = /<img[^>]+src=["']([^"']+)["']/i.exec(html);
    if (m) cands.push(m[1].replace(/&amp;/g, "&"));
    for (const u of cands) { const v = E.collapse(u); if (E.validImage(v)) return v; }
    return "";
  }

  function parseFeed(text) {
    const doc = new DOMParser().parseFromString(String(text), "text/xml");
    if (doc.getElementsByTagName("parsererror").length) throw new Error("not a readable feed");
    const rootEl = doc.documentElement;
    const items = [];
    if (rootEl.localName === "rss" || rootEl.localName === "RDF") {
      const ch = kids(rootEl, "channel")[0] || rootEl;
      const chTitle = E.collapse(kidText(ch, "title"));
      const chLink = E.collapse(kidText(ch, "link"));
      for (const it of Array.from(rootEl.getElementsByTagName("item"))) {
        const src = kids(it, "source")[0];
        items.push({
          title: E.collapse(htmlToText(kidText(it, "title"))),
          url: E.collapse(kidText(it, "link")),
          published: E.collapse(kidText(it, "pubDate") || kidText(it, "date")),
          summary: firstSentences(htmlToText(kidText(it, "description")), 2),
          source: E.collapse(src ? src.textContent : "") || chTitle,
          source_url: (src && src.getAttribute("url")) || chLink,
          image: imageOf(it)
        });
      }
    } else if (rootEl.localName === "feed") {
      const chTitle = E.collapse(kidText(rootEl, "title"));
      const linkOf = el => { const l = kids(el, "link").filter(x => (x.getAttribute("rel") || "alternate") === "alternate")[0]; return l ? l.getAttribute("href") || "" : ""; };
      for (const it of kids(rootEl, "entry")) {
        items.push({
          title: E.collapse(htmlToText(kidText(it, "title"))),
          url: E.collapse(linkOf(it)),
          published: E.collapse(kidText(it, "published") || kidText(it, "updated")),
          summary: firstSentences(htmlToText(kidText(it, "summary") || kidText(it, "content")), 2),
          source: chTitle,
          source_url: linkOf(rootEl),
          image: imageOf(it)
        });
      }
    }
    // Feed dates come as RFC 822 ("Fri, 23 Oct 2026 09:00:00 GMT"); the engine wants ISO.
    for (const it of items) {
      if (it.published && E.parseIso(it.published) === null) {
        const ms = Date.parse(it.published);
        it.published = isFinite(ms) ? E.isoZ(ms) : it.published;
      }
    }
    return items;
  }

  // ------------------------------------------------------------ fetching
  async function getText(url, opts) {
    const f = (opts && opts.fetch) || (typeof fetch === "function" ? fetch.bind(root || null) : null);
    const ctl = typeof AbortController === "function" ? new AbortController() : null;
    const timer = ctl ? setTimeout(() => ctl.abort(), (opts && opts.timeout) || TIMEOUT_MS) : null;
    try {
      const init = { credentials: "omit", referrerPolicy: "no-referrer" };
      if (ctl) init.signal = ctl.signal;
      if (opts && typeof opts.body === "string") {
        init.method = "POST";
        init.headers = { "Content-Type": "application/json" };
        init.body = opts.body;
      }
      const r = await f(url, init);
      if (!r.ok) throw new Error("the site answered " + r.status);
      return await r.text();
    } catch (e) {
      if (e && e.name === "AbortError") throw new Error("no answer in time");
      if (e instanceof TypeError) throw new Error("not readable from a web page (the site blocks it, or it is offline)");
      throw e;
    } finally {
      if (timer) clearTimeout(timer);
    }
  }

  async function gdelt(q, hours, cfg, opts) {
    const url = gdeltUrl(q, hours, cfg);
    const wait = opts && typeof opts.sleep === "function" ? opts.sleep : sleep;
    const gap = opts && typeof opts.gap === "number" ? opts.gap : GAP_MS;
    try {
      return parseGdelt(await getText(url, opts));
    } catch (e) {
      await wait(gap * 1.5);  // GDELT is busy; give it a moment, then try once more
      try {
        return parseGdelt(await getText(url, opts));
      } catch (e2) {
        // A busy GDELT answers without the header browsers need, which looks like a blocked site.
        if (/not readable from a web page/.test(String(e2.message))) throw new Error("the news index turned the search away (busy or offline)");
        throw e2;
      }
    }
  }

  // ------------------------------------------------------------ weather
  function forecastUrl(w) {
    return FORECAST + "?latitude=" + w.latitude + "&longitude=" + w.longitude +
      "&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max" +
      "&timezone=auto&forecast_days=4&temperature_unit=" + (w.units === "celsius" ? "celsius" : "fahrenheit");
  }

  function weatherFrom(data, w, nowIso) {
    const d = data && data.daily;
    if (!d || !Array.isArray(d.time)) throw new Error("the forecast came back empty");
    const num = v => (typeof v === "number" && isFinite(v) ? v : null);
    const days = d.time.slice(0, 4).map((t, i) => ({
      date: String(t), code: num((d.weather_code || [])[i]), hi: num((d.temperature_2m_max || [])[i]),
      lo: num((d.temperature_2m_min || [])[i]), rain: num((d.precipitation_probability_max || [])[i])
    }));
    const c = data.current;
    return {
      place: E.collapse(w.place), units: w.units === "celsius" ? "celsius" : "fahrenheit", source: "Open-Meteo",
      fetched_at: nowIso, current: c && num(c.temperature_2m) !== null ? { temp: c.temperature_2m, code: num(c.weather_code) } : null,
      days: days
    };
  }

  async function weather(cfg, nowIso, opts) {
    const w = E.normalizeConfig(cfg || {}).weather;
    if (!w || w.enabled !== true || !E.isNum(w.latitude) || !E.isNum(w.longitude)) return null;
    return weatherFrom(JSON.parse(await getText(forecastUrl(w), opts)), w, nowIso);
  }

  /* Finds towns by name for the setup interview. Returns up to five matches. */
  async function geocode(name, opts) {
    const q = E.collapse(name);
    if (q.length < 2) return [];
    const data = JSON.parse(await getText(GEOCODE + "?name=" + encodeURIComponent(q) + "&count=5&language=en&format=json", opts));
    return (data && Array.isArray(data.results) ? data.results : []).filter(r => E.isNum(r.latitude) && E.isNum(r.longitude)).map(r => ({
      name: E.collapse(r.name), region: E.collapse(r.admin1), country: E.collapse(r.country), country_code: E.collapse(r.country_code),
      latitude: Math.round(r.latitude * 100) / 100, longitude: Math.round(r.longitude * 100) / 100,
      county: E.collapse(r.admin2),
      label: [r.name, r.admin1, r.country_code === "US" ? "" : r.country].map(E.collapse).filter(Boolean).join(", ")
    }));
  }

  // ------------------------------------------------------------ event calendars
  function milesBetween(lat1, lng1, lat2, lng2) {
    const r = Math.PI / 180;
    const a = Math.pow(Math.sin((lat2 - lat1) * r / 2), 2) +
      Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.pow(Math.sin((lng2 - lng1) * r / 2), 2);
    return 3958.8 * 2 * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  /* The station calendars in the state whose home area reaches the town, nearest first. */
  function calendarsNear(list, code, lat, lng) {
    const all = list && list.states && Array.isArray(list.states[code]) ? list.states[code] : [];
    return all.filter(c => c && /^[A-Za-z0-9_-]+$/.test(String(c.slug)) && E.isNum(c.lat) && E.isNum(c.lng))
      .map(c => ({ cal: c, miles: milesBetween(lat, lng, c.lat, c.lng) }))
      .filter(x => x.miles <= (E.isNum(x.cal.miles) ? x.cal.miles : 50) + EVENT_MILES)
      .sort((a, b) => a.miles - b.miles).map(x => x.cal);
  }

  function slugify(name) { return String(name).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, ""); }

  /* One calendar event as a brief item. The link opens the organizer's own page; for an
     event listed only on a social site, the event on the station's calendar page (when
     that page takes direct links), else the calendar page itself. */
  function eventItem(ev, cal, nowIso) {
    if (!ev || typeof ev !== "object") return null;
    const title = tidyTitle(htmlToText(ev.Name));
    const allDay = ev.AllDay === true || ev.HasTime === false;
    const local = String(ev.DateStart || "");  // the calendar's wall-clock time, marked Z
    const start = allDay ? local.slice(0, 10) : String(ev.StartUTC || "");
    if (!title || (allDay ? !E.isDateStr(start) : E.parseIso(start) === null)) return null;
    const page = E.validUrl(cal.page) ? String(cal.page).replace(/#.*$/, "") : "";
    const pid = /^[0-9]+$/.test(String(ev.PId)) ? String(ev.PId) : "";
    const social = u => { const h = E.hostOf(u); return E.SOCIAL_HOSTS.some(s => h === s || h.slice(-(s.length + 1)) === "." + s); };
    let url = page;
    const mark = cal.links === "hash" ? "#/" : cal.links === "hashBang" ? "#!/" : "";
    if (E.validUrl(ev.PrimaryUrl) && !social(ev.PrimaryUrl)) url = E.collapse(ev.PrimaryUrl);
    else if (mark && page && pid && /^\d{4}-\d{2}-\d{2}T\d{2}/.test(local)) url = page + mark + "details/" + slugify(title) + "/" + pid + "/" + local.slice(0, 13);
    if (!url) return null;
    const img = [ev.LargeImg, ev.MediumImg].map(E.collapse).filter(E.validImage)[0] || "";
    const text = htmlToText(ev.Summary) || firstSentences(htmlToText(ev.Description), 2);
    return {
      title: title, url: url, source: E.collapse(cal.station) ? E.collapse(cal.station) + " community calendar" : "Community calendar",
      source_url: page, published: nowIso, summary: text, image: img,
      event: { start: start, all_day: allDay, venue: htmlToText(ev.Venue), place: htmlToText(ev.CityState) }
    };
  }

  /* A calendar's answer as brief items, taking each day's first event, then each
     day's second, and so on, so the brief shows the week rather than one evening. */
  function eventsFrom(data, cal, nowIso) {
    if (!data || data.Success !== true || !Array.isArray(data.Value)) throw new Error("the calendar answered without events");
    const days = data.Value.map(d => (d && Array.isArray(d.Events) ? d.Events : []).map(ev => eventItem(ev, cal, nowIso)).filter(Boolean));
    const out = [];
    for (let i = 0; days.some(d => d.length > i); i++) for (const d of days) if (d[i]) out.push(d[i]);
    return out;
  }

  /* Asks one calendar for the week's events within `miles` (EVENT_MILES unless given) of
     the town. Only the town's rounded map position and the date are sent. */
  async function calendarEvents(cal, lat, lng, startDate, nowIso, opts, miles) {
    const body = JSON.stringify({ start: startDate, daysToLoad: EVENT_DAYS, eventsPerDay: 3, lat: lat, lng: lng,
      distance: E.isNum(miles) ? miles : EVENT_MILES,
      search: "", sort: "", category: [], labels: [], defFilter: "all" });
    const text = await getText(CALENDAR_API + cal.slug, Object.assign({}, opts, { body: body }));
    let data;
    try { data = JSON.parse(text); } catch (e) { throw new Error("the calendar answered with something unreadable"); }
    return eventsFrom(data, cal, nowIso);
  }

  // ------------------------------------------------------------ the run
  /* Collects candidates for every category. Feeds come first, all at once. GDELT
     then goes one request at a time, and only for categories the feeds left short
     of fresh stories: first the main search, then the second search, then a wider
     time window. After a refused search the pause doubles, and after three
     refused searches in a row the rest of the run uses the feeds alone. */
  async function collect(cfg, ledger, opts) {
    opts = opts || {};
    const n = E.normalizeConfig(cfg);
    const b = n.brief;
    const now = opts.now || new Date();
    const nowIso = E.isoZ(now.getTime());
    const wait = typeof opts.sleep === "function" ? opts.sleep : sleep;
    const gap = typeof opts.gap === "number" ? opts.gap : GAP_MS;
    const cats = n.categories.map(c => E.resolveCategory(c, n.reader));
    const pools = {}, seen = {}, health = {};
    const progress = typeof opts.progress === "function" ? opts.progress : () => {};
    let done = 0;
    let phase = "feeds";  // reported with every step, so the page can show which stage is running
    // A category's feeds plus its on-topic feeds, each address once.
    const feedsOf = c => (c.feeds || []).concat((c.topic_feeds || []).filter(u => (c.feeds || []).indexOf(u) < 0));
    const feedCount = cats.reduce((a, c) => a + feedsOf(c).length, 0);
    let total = feedCount + cats.filter(c => (c.queries || []).some(q => E.collapse(q))).length;
    const tick = label => { done += 1; progress(label, done, total, phase); };
    for (const c of cats) { pools[c.id] = []; seen[c.id] = {}; health[c.id] = { queries: [], feeds: [] }; }
    const add = (cid, items, onTopic) => {
      let added = 0;
      for (const it of items) {
        const k = E.normUrl(it.url);
        if (k && !seen[cid][k]) { seen[cid][k] = true; pools[cid].push(onTopic ? Object.assign({}, it, { on_topic: true }) : it); added += 1; }
      }
      return added;
    };
    if (opts.cancelled && opts.cancelled()) throw new Error("cancelled");
    progress("Publisher feeds", 0, total, phase);
    // Feeds: each address once, a few at a time, then shared by every category that lists it.
    const urls = [];
    for (const c of cats) for (const url of feedsOf(c)) if (urls.indexOf(url) < 0) urls.push(url);
    const got = {};
    let next = 0;
    async function worker() {
      while (next < urls.length) {
        const url = urls[next++];
        try { got[url] = { items: parseFeed(await getText(url, opts)), err: "" }; } catch (e) { got[url] = { items: [], err: String(e.message || e) }; }
        for (const c of cats) if (feedsOf(c).indexOf(url) >= 0) tick(c.name);
      }
    }
    await Promise.all([worker(), worker(), worker(), worker()]);
    const nowMs = now.getTime();
    for (const c of cats) {
      for (const url of feedsOf(c)) {
        const g = got[url] || { items: [], err: "not read" };
        const fresh = g.items.filter(it => { const ms = E.parseIso(it.published); return ms !== null && (nowMs - ms) / 3600000 <= b.window_hours; }).length;
        const onTopic = (c.topic_feeds || []).indexOf(url) >= 0;
        health[c.id].feeds.push({ url: url, items: g.items.length, fresh: fresh, added: add(c.id, g.items, onTopic), error: g.err, on_topic: onTopic });
      }
    }

    const freshShort = c => {
      const trial = E.selectBrief({ [c.id]: pools[c.id] }, Object.assign({}, n, { categories: n.categories.filter(x => x.id === c.id) }), ledger, nowIso, nowIso.slice(0, 10), "web");
      const want = c.items || b.items_per_category;
      return trial.categories[0].items.filter(i => i.recency === "news").length < want;
    };
    // The backup collection: stories gathered on GitHub every four hours for every
    // library category, published beside this page. One read, and only when a
    // category is still short, so the news index is asked as little as possible.
    const shortAfterFeeds = cats.filter(freshShort);
    if (shortAfterFeeds.length && opts.backup !== false) {
      phase = "backup";
      progress("Backup collection", done, total, phase);
      let backup = null, err = "";
      try { backup = parseBackup(await getText(opts.backupUrl || BACKUP_URL, opts)); } catch (e) { err = String(e.message || e); }
      for (const c of shortAfterFeeds) {
        const items = backup && Object.prototype.hasOwnProperty.call(backup.categories, c.id) ? backup.categories[c.id].filter(it => it && typeof it === "object") : [];
        health[c.id].backup = { items: items.length, added: add(c.id, items), error: backup ? "" : err, collected_at: backup ? backup.generated_at : "",
          covered: !!backup && Object.prototype.hasOwnProperty.call(backup.categories, c.id) };
      }
    }
    // Local news: stories from the local TV stations in the reader's state, gathered on
    // GitHub every four hours and published beside this page. One read, only for town
    // categories still short. Only stories that name the town or a nearby place join a
    // category; the town itself is never sent anywhere.
    const code = E.stateCode(n.reader.region);
    const townShort = cats.filter((c, i) => E.isLocalCategory(n.categories[i]) && freshShort(c));
    if (townShort.length && code && opts.local !== false) {
      phase = "local";
      progress("Local stations", done, total, phase);
      let file = null, err = "";
      try { file = parseLocal(await getText((opts.localDir || LOCAL_DIR) + code + ".json", opts)); } catch (e) { err = String(e.message || e); }
      const area = [n.reader.location].concat(Array.isArray(n.reader.local_terms) ? n.reader.local_terms : []).map(E.collapse).filter(Boolean);
      const near = file ? file.stories.filter(it => area.some(t => E.termHit(String(it.title || "") + " " + String(it.summary || ""), t))) : [];
      for (const c of townShort) {
        health[c.id].local = { state: code, items: near.length, added: add(c.id, near), error: file ? "" : err, collected_at: file ? file.generated_at : "" };
      }
    }
    // Things to do: the week's events near the town, from the community calendar of the
    // nearest local TV station, asked from this browser for this reader only.
    const evCats = cats.filter((c, i) => n.categories[i].id === "local-events");
    if (evCats.length && code && opts.events !== false) {
      phase = "events";
      progress("Event calendars", done, total, phase);
      const w = n.weather;
      let pos = E.isNum(w.latitude) && E.isNum(w.longitude) ? { lat: w.latitude, lng: w.longitude } : null;
      let err = "";
      if (!pos && E.collapse(n.reader.location)) {
        try {
          const f = (await geocode(n.reader.location, opts)).filter(r => r.country_code === "US" && E.stateCode(r.region) === code)[0];
          if (f) pos = { lat: f.latitude, lng: f.longitude };
        } catch (e) { err = "the town search did not answer (" + String(e.message || e) + ")"; }
      }
      const list = opts.calendars || (root && root.DB_CALENDARS) || null;
      const near = pos ? calendarsNear(list, code, pos.lat, pos.lng).slice(0, EVENT_CALENDARS) : [];
      const want = Math.max.apply(null, evCats.map(c => c.items || b.items_per_category));
      const items = [], used = [], have = {};
      // The town's own events first, so the busier calendar of a bigger town nearby cannot
      // crowd them out; then the area around it while the brief is still short.
      for (const cal of near) {
        for (const miles of [EVENT_TOWN_MILES, EVENT_MILES]) {
          if (items.length >= want * 2) break;
          try {
            const got = await calendarEvents(cal, pos.lat, pos.lng, opts.date || localDate(now), nowIso, opts, miles);
            for (const it of got) {
              const k = E.normUrl(it.url) + " " + it.event.start;
              if (!have[k]) { have[k] = true; items.push(it); }
            }
            const name = E.collapse(cal.station) || cal.slug;
            if (used.indexOf(name) < 0) used.push(name);
          } catch (e) { err = err || String(e.message || e); }
        }
      }
      if (!near.length && !err) err = pos ? "no station calendar covers your town" : "your town has no map position; find it under the forecast in setup";
      for (const c of evCats) {
        health[c.id].events = { calendars: used, items: items.length, added: add(c.id, items, true), error: used.length ? "" : err };
      }
    }
    phase = "search";
    progress("News search", done, total, phase);
    let first = true;
    let failures = 0;  // searches in a row that failed even after the retry
    const deadline = Date.now() + (typeof opts.searchBudget === "number" ? opts.searchBudget : SEARCH_BUDGET_MS);
    async function search(c, q, hours) {
      if (opts.cancelled && opts.cancelled()) throw new Error("cancelled");
      if (failures >= 3) {
        health[c.id].queries.push({ query: q, hours: hours, items: 0, added: 0, error: "skipped: the news index was busy, so this brief uses the feeds" });
        tick(c.name);
        return;
      }
      if (Date.now() >= deadline) {
        health[c.id].queries.push({ query: q, hours: hours, items: 0, added: 0, error: "skipped: the news index was slow, so this brief uses what it has" });
        tick(c.name);
        return;
      }
      if (!first) await wait(failures ? gap * 2 : gap);
      first = false;
      let items = [], err = "";
      try { items = await gdelt(q, hours, n, { fetch: opts.fetch, sleep: wait, gap: gap, timeout: opts.timeout }); } catch (e) { err = String(e.message || e); }
      failures = err ? failures + 1 : 0;
      health[c.id].queries.push({ query: q, hours: hours, items: items.length, added: add(c.id, items), error: err });
      tick(c.name);
    }
    for (const c of cats) {
      const qs = (c.queries || []).filter(q => E.collapse(q));
      if (!qs.length) continue;
      if (freshShort(c)) await search(c, qs[0], b.window_hours);
      else {
        health[c.id].queries.push({ query: qs[0], hours: b.window_hours, items: 0, added: 0, error: "", note: "not needed: the earlier sources filled this category" });
        tick(c.name);
      }
    }
    // Second searches and the wider window only where a category is still short.
    const short = cats.filter(c => (c.queries || []).filter(q => E.collapse(q)).length && freshShort(c));
    total += short.length * 2;
    for (const c of short) {
      const qs = c.queries.filter(q => E.collapse(q));
      if (qs[1]) await search(c, qs[1], b.window_hours); else tick(c.name);
      if (b.backfill_max_hours > b.window_hours && freshShort(c)) await search(c, qs[0], b.backfill_max_hours); else tick(c.name);
    }
    return { candidates: pools, health: health, nowIso: nowIso };
  }

  /* An empty desk whose searches all failed was not checked, which is not the
     same as "nothing new"; the page says so. A desk was still checked when the
     backup collection covers it (GitHub searched it within the last four hours)
     or, for a town desk, when its local stations answered. */
  function markUnchecked(brief, health) {
    for (const bc of brief.categories || []) {
      const h = health && health[bc.id];
      if (!h || (bc.items && bc.items.length)) continue;
      const tried = (h.queries || []).filter(q => !q.note);
      const stations = (h.local && !h.local.error) || (h.events && !h.events.error) || (h.feeds || []).some(f => f.station && !f.error);
      const backup = !!(h.backup && !h.backup.error && h.backup.covered);
      if (tried.length && tried.every(q => q.error) && !stations && !backup) bc.unchecked = true;
    }
    return brief;
  }

  /* Reads one feed the way a brief would and says how many stories mention the
     reader's town or nearby places. For the "Check" button on the town question. */
  async function checkFeed(url, terms, opts) {
    const items = parseFeed(await getText(url, opts));
    const local = (terms || []).map(E.collapse).filter(Boolean);
    const mention = items.filter(it => local.some(t => E.termHit(it.title + " " + (it.summary || ""), t))).length;
    return { items: items.length, local: mention };
  }

  function localDate(d) {
    return d.getFullYear() + "-" + E.pad2(d.getMonth() + 1) + "-" + E.pad2(d.getDate());
  }

  /* Collects and picks today's brief. Returns {brief, health}. */
  async function runBrief(cfg, ledger, opts) {
    opts = opts || {};
    const now = opts.now || new Date();
    const wxPromise = weather(cfg, E.isoZ(now.getTime()), opts).then(w => ({ w: w, err: "" }), e => ({ w: null, err: String(e.message || e) }));
    const got = await collect(cfg, ledger, Object.assign({}, opts, { now: now }));
    if (typeof opts.progress === "function") opts.progress("Your page", 1, 1, "layout");
    const brief = E.selectBrief(got.candidates, cfg, ledger, got.nowIso, opts.date || localDate(now), "web");
    markUnchecked(brief, got.health);
    const wx = await wxPromise;
    if (wx.w) brief.weather = wx.w;
    const health = got.health;
    if (wx.err) health._weather = { error: wx.err };
    return { brief: brief, health: health };
  }

  return { GDELT, GAP_MS, BACKUP_URL, parseBackup, LOCAL_DIR, parseLocal, CALENDAR_API, EVENT_MILES, EVENT_TOWN_MILES, milesBetween, calendarsNear, eventItem, eventsFrom, calendarEvents, gdeltQuery, gdeltUrl, tidyTitle, gdeltDate, parseGdelt, parseFeed, imageOf, forecastUrl, weatherFrom,
    weather, geocode, collect, runBrief, localDate, markUnchecked, checkFeed };
});
