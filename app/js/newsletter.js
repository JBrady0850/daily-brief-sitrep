/* Daily Brief page theme: turns a brief into a self-contained web page (no
   scripts; story photos load from their publishers), a plain-text copy and a
   title line. dailybrief/render.py mirrors this file and reads the stylesheet
   below and the icons in data/icons.js, so the saved page and the in-app view
   are the same document. */
(function (root, factory) {
  const node = typeof module === "object" && module.exports;
  const engine = node ? require("./engine.js") : root.DB_ENGINE;
  let icons = root && root.DB_ICONS;
  if (node) {
    const txt = require("fs").readFileSync(require("path").join(__dirname, "..", "data", "icons.js"), "utf8");
    icons = JSON.parse(txt.slice(txt.indexOf("window.DB_ICONS = ") + 18, txt.lastIndexOf(";")));
  }
  const api = factory(engine, icons || { icons: {}, weather: {}, art: {}, weather_codes: {}, weather_words: {} });
  if (node) module.exports = api;
  else root.DB_NEWSLETTER = api;
})(typeof self !== "undefined" ? self : this, function (E, ICONS) {
  "use strict";

  /*CSS-START*/
  const CSS = `
*{box-sizing:border-box;}
body{margin:0;background:#eef1f5;font-family:'Segoe UI',Roboto,Arial,Helvetica,sans-serif;font-size:15px;line-height:1.5;color:#1a1a1a;overflow-wrap:break-word;}
.in{max-width:1180px;margin:0 auto;padding:0 20px;}
nav.site{background:#0a1c33;font-size:13px;}
nav.site .in{display:flex;flex-wrap:wrap;gap:6px 20px;padding-top:9px;padding-bottom:9px;}
nav.site a{color:#e0b43a;font-weight:bold;text-decoration:none;}
nav.site a:hover,nav.site a:focus{text-decoration:underline;}
header.mast{background:#0f2744;color:#ffffff;}
header.mast .in{padding-top:28px;padding-bottom:22px;}
div.kick{font-size:12px;font-weight:bold;letter-spacing:.18em;text-transform:uppercase;color:#e0b43a;}
h1.ttl{font-family:Georgia,'Times New Roman',serif;font-size:34px;line-height:1.15;font-weight:bold;margin:8px 0 6px;}
p.dl{font-size:14px;color:#d3dbe6;margin:0;}
p.built{font-size:13px;color:#d3dbe6;margin:6px 0 0;}
div.rule{background:#d4a017;height:4px;}
main{padding-top:20px;padding-bottom:28px;}
div.cdg{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(280px,100%),1fr));gap:14px;margin:0 0 18px;} div.cdg section.cd{margin:0;}
section.cd{background:#fff8e1;border-left:5px solid #d4a017;padding:14px 16px;margin:0 0 18px;}
div.cdtop{display:flex;gap:16px;align-items:flex-start;}
div.cdn{font-family:Georgia,serif;font-size:46px;line-height:1;font-weight:bold;color:#0f2744;white-space:nowrap;}
div.cdt{flex:1;min-width:0;}
div.cdk{font-size:12px;font-weight:bold;letter-spacing:.14em;color:#6e5426;text-transform:uppercase;}
div.cds{font-size:13px;color:#4a4a4a;margin:2px 0 8px;}
div.bar{background:#ece4c8;height:9px;}
div.barf{background:#d4a017;height:9px;}
ul.ms{list-style:none;margin:12px 0 0;padding:0;font-size:13px;}
ul.ms li{display:flex;gap:10px;align-items:flex-start;padding:6px 0;border-top:1px solid #efe6c7;}
ul.ms li > span.pill{flex:none;min-width:58px;text-align:center;margin-top:1px;}
span.msn{display:block;font-size:12px;color:#666666;}
span.pill{display:inline-block;font-size:11px;font-weight:bold;color:#ffffff;padding:2px 8px;border-radius:10px;letter-spacing:.03em;vertical-align:middle;margin-right:6px;white-space:nowrap;}
span.ms-hot{background:#b03a2e;} span.ms-warm{background:#a04000;}
span.ms-cool{background:#34495e;} span.ms-mark{background:#d4a017;color:#0f2744;}
span.f1{background:#1b6e3d;} span.f2{background:#0f6e5c;} span.f3{background:#8a5a00;}
span.old{background:#6e5426;} span.ref{background:#5b3485;} span.ev{background:#1f4e99;}
div.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 14px;}
div.tile{background:#ffffff;border-top:3px solid #0f2744;padding:12px 8px;text-align:center;}
div.tn{font-family:Georgia,serif;font-size:28px;font-weight:bold;color:#0f2744;line-height:1.1;}
div.tl{font-size:12px;color:#555555;margin-top:2px;}
div.srcbar{display:flex;height:9px;margin:0 0 4px;background:#dfe4ea;}
span.seg{display:block;height:9px;}
div.lgd{font-size:12px;color:#555555;margin:0 0 18px;}
span.lg{display:inline-block;margin:2px 14px 2px 0;white-space:nowrap;}
span.sw{display:inline-block;width:10px;height:10px;margin-right:5px;vertical-align:middle;border-radius:2px;}
div.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(440px,1fr));gap:18px;align-items:start;}
section.card{background:#ffffff;border:1px solid #e3e8ee;border-left:5px solid var(--c);}
h2.ch{margin:0;padding:11px 14px;border-bottom:1px solid #e3e8ee;background:#f8f9fb;display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;font-weight:normal;}
span.tag{display:inline-block;font-size:11px;font-weight:bold;color:#ffffff;background:var(--c);padding:2px 8px;border-radius:3px;letter-spacing:.04em;}
span.cn{font-family:Georgia,serif;font-size:19px;font-weight:bold;color:#0f2744;flex:1;}
span.mix{font-size:12px;color:#666666;}
p.sig{margin:0;padding:10px 14px;border-bottom:1px solid #f0f2f5;background:#fbfaf4;font-size:14px;color:#333333;}
ul.items{list-style:none;margin:0;padding:0;}
li.it{padding:12px 14px;border-bottom:1px solid #f0f2f5;}
li.it:last-child{border-bottom:0;}
a.hl{font-size:16px;font-weight:bold;line-height:1.35;color:#0f2744;text-decoration:none;}
a.hl:hover,a.hl:focus{text-decoration:underline;}
span.hl{font-size:16px;font-weight:bold;color:#0f2744;}
div.meta{margin:5px 0 4px;}
span.src{font-size:12px;color:#666666;vertical-align:middle;}
p.sum{margin:0;font-size:14px;line-height:1.55;color:#3d3d3d;}
p.st{margin:4px 0 0;font-size:13px;color:#5b3485;}
p.none{margin:0;padding:12px 14px;font-size:14px;color:#666666;font-style:italic;}
div.gap{background:#fdecea;border-left:4px solid #b03a2e;padding:10px 12px;font-size:13px;color:#7b241c;margin:0 0 18px;}
div.sample{background:#fff8e1;border-left:4px solid #d4a017;padding:10px 12px;font-size:13px;color:#5c4510;margin:0 0 18px;}
div.legend{background:#ffffff;border-left:4px solid #0f2744;padding:10px 12px;font-size:13px;line-height:1.55;color:#333333;margin:22px 0 0;}
section.an{border:1px solid #e3e8ee;border-top:4px solid #0f2744;background:#ffffff;padding:14px 16px;margin:0 0 18px;}
h2.anh{margin:0 0 8px;font-size:12px;font-weight:bold;letter-spacing:.14em;color:#0f2744;text-transform:uppercase;}
div.anb{font-size:15px;line-height:1.55;}
div.anb ol,div.anr ul{margin:4px 0 0;padding-left:22px;}
div.anr{margin-top:10px;font-size:14px;line-height:1.5;}
p.anf{font-size:12px;color:#666666;margin:10px 0 0;}
section.arch{margin:22px 0 0;background:#ffffff;border:1px solid #e3e8ee;padding:12px 16px;}
section.arch h2{margin:0 0 6px;font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#0f2744;}
section.arch ul{margin:0;padding-left:20px;columns:2 220px;font-size:14px;}
footer.foot{background:#0f2744;font-size:12px;line-height:1.6;color:#c3cdd9;}
footer.foot .in{padding-top:14px;padding-bottom:14px;}
header.mast{position:relative;overflow:hidden;}
header.mast .in{position:relative;}
div.art{position:absolute;top:0;right:0;bottom:0;width:62%;max-width:640px;pointer-events:none;}
div.art svg{display:block;width:100%;height:100%;}
svg.ki{width:16px;height:16px;vertical-align:-3px;margin-right:7px;}
span.ico{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:50%;background:var(--c);color:#ffffff;flex:none;}
span.ico svg{width:18px;height:18px;}
li.lead .ph{display:block;margin:-12px -14px 10px;aspect-ratio:2/1;background:#e9edf2;overflow:hidden;}
li.lead img{display:block;width:100%;height:100%;object-fit:cover;}
li.th{display:flex;gap:12px;align-items:flex-start;}
li.th div.tx{flex:1;min-width:0;}
.thumb{flex:none;display:block;width:96px;height:64px;border-radius:6px;overflow:hidden;background:#e9edf2;}
.thumb img{display:block;width:100%;height:100%;object-fit:cover;}
section.wx{display:flex;flex-wrap:wrap;gap:12px 24px;align-items:center;background:linear-gradient(135deg,#e6f0fb,#ffffff);border:1px solid #d3e0ef;border-left:5px solid #2b6cc4;padding:14px 16px;margin:0 0 18px;}
div.wxnow{display:flex;align-items:center;gap:12px;min-width:220px;}
svg.wxi{width:40px;height:40px;}
svg.wxi.big{width:64px;height:64px;}
div.wxk{font-size:12px;font-weight:bold;letter-spacing:.14em;text-transform:uppercase;color:#2b6cc4;}
div.wxt{font-family:Georgia,'Times New Roman',serif;font-size:34px;font-weight:bold;color:#0f2744;line-height:1.1;}
div.wxw{font-size:14px;color:#3d3d3d;}
ol.wxd{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:10px;flex:1;}
ol.wxd li{flex:1;min-width:92px;background:#ffffff;border:1px solid #e3e8ee;border-radius:8px;padding:8px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:2px;}
span.wxdn{font-size:12px;font-weight:bold;color:#0f2744;text-transform:uppercase;letter-spacing:.08em;}
span.wxhl{font-size:14px;}
span.wxr{font-size:12px;color:#2b6cc4;min-height:16px;}
p.wxs{flex-basis:100%;margin:0;font-size:11px;color:#666666;}
p.wxs a{color:#2b6cc4;}
@media (max-width:760px){h1.ttl{font-size:26px;} div.tiles{grid-template-columns:repeat(2,1fr);} div.grid{grid-template-columns:1fr;} .in{padding:0 10px;} section.cd,section.wx,section.an,section.arch{padding:12px;} div.cdtop{gap:12px;} div.cdn{font-size:38px;} h2.ch,p.sig{padding:10px 12px;} li.it,p.none{padding:12px;} li.lead .ph{margin:-12px -12px 10px;} div.art{width:100%;opacity:.22;} ol.wxd{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;flex-basis:100%;} ol.wxd li{min-width:0;padding:6px 2px;} svg.wxi{width:30px;height:30px;} span.wxhl{font-size:13px;} div.wxnow{min-width:0;}}
@media print{nav.site{display:none;} body{background:#ffffff;} div.grid{display:block;} section.card{break-inside:avoid;margin:0 0 12px;}}
`;
  /*CSS-END*/

  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December"];
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const MIX_COLORS = { news: "#1b6e3d", backfill: "#6e5426", reference: "#5b3485" };
  const EVENT_NOTE = "Events come from the community calendars of local TV stations, powered by CitySpark. Check the details with the organizer before you go.";

  function esc(v) {
    return String(v == null ? "" : v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
  }

  function prettyDate(d) {
    if (!E.isDateStr(d)) return String(d || "");
    const dt = new Date(d + "T00:00:00Z");
    return DAYS[dt.getUTCDay()] + ", " + MONTHS_LONG[dt.getUTCMonth()] + " " + E.pad2(dt.getUTCDate()) + ", " + dt.getUTCFullYear();
  }

  function shortDate(d) {
    const dt = new Date(d + "T00:00:00Z");
    return DAYS[dt.getUTCDay()].slice(0, 3) + " " + MONTHS[dt.getUTCMonth()] + " " + E.pad2(dt.getUTCDate()) + ", " + dt.getUTCFullYear();
  }

  /* US time zones by their usual names: [standard offset in minutes, standard, daylight].
     Elsewhere the offset from UTC is shown (mirrors US_ZONES in render.py). */
  const US_ZONES = {
    "America/New_York": [-300, "EST", "EDT"], "America/Detroit": [-300, "EST", "EDT"], "America/Indiana/Indianapolis": [-300, "EST", "EDT"],
    "America/Kentucky/Louisville": [-300, "EST", "EDT"], "America/Chicago": [-360, "CST", "CDT"], "America/Denver": [-420, "MST", "MDT"],
    "America/Boise": [-420, "MST", "MDT"], "America/Phoenix": [-420, "MST", "MST"], "America/Los_Angeles": [-480, "PST", "PDT"],
    "America/Anchorage": [-540, "AKST", "AKDT"], "Pacific/Honolulu": [-600, "HST", "HST"]
  };

  /* The wall clock at an instant in a time zone: [year, month, day, hour, minute, offset
     in minutes], or null when the zone is unknown. The instant counts to the minute. */
  function zoneClock(ms, tz) {
    const t = ms - (((ms % 60000) + 60000) % 60000);
    if (!tz || tz === "UTC") {
      const d = new Date(t);
      return [d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate(), d.getUTCHours(), d.getUTCMinutes(), 0];
    }
    let parts;
    try {
      parts = new Intl.DateTimeFormat("en-US", { timeZone: tz, hourCycle: "h23", year: "numeric", month: "numeric", day: "numeric",
        hour: "numeric", minute: "numeric" }).formatToParts(new Date(t));
    } catch (e) { return null; }
    const get = k => { const p = parts.filter(x => x.type === k)[0]; return p ? Number(p.value) : NaN; };
    const c = [get("year"), get("month"), get("day"), get("hour") % 24, get("minute")];
    if (!c.every(v => isFinite(v))) return null;
    return c.concat([Math.round((Date.UTC(c[0], c[1] - 1, c[2], c[3], c[4]) - t) / 60000)]);
  }

  function zoneName(tz, off) {
    const us = US_ZONES[tz];
    if (us) return off === us[0] ? us[1] : us[2];
    if (off === 0) return "UTC";
    const a = Math.abs(off);
    return "UTC" + (off < 0 ? "-" : "+") + Math.floor(a / 60) + (a % 60 ? ":" + E.pad2(a % 60) : "");
  }

  /* When a brief was built, in the reader's time zone (UTC when it is unknown):
     "Sunday, October 25, 2026 at 6:16 AM CDT". Empty without a readable time. */
  /* A time as the reader's clock shows it: [clock, zone], or null without a readable time. */
  function localClock(iso, tz) {
    const ms = E.parseIso(iso);
    if (ms === null) return null;
    let zone = E.collapse(tz) || "UTC";
    let c = zoneClock(ms, zone);
    if (!c) { zone = "UTC"; c = zoneClock(ms, zone); }
    return [c, zone];
  }

  function clockTime(c, zone) {
    return (c[3] % 12 === 0 ? 12 : c[3] % 12) + ":" + E.pad2(c[4]) + " " + (c[3] < 12 ? "AM" : "PM") + " " + zoneName(zone, c[5]);
  }

  function builtLabel(iso, tz) {
    const lc = localClock(iso, tz);
    if (!lc) return "";
    const c = lc[0];
    return prettyDate(c[0] + "-" + E.pad2(c[1]) + "-" + E.pad2(c[2])) + " at " + clockTime(c, lc[1]);
  }

  /* When a calendar event happens, in the reader's zone: "Sun, Oct 25, 7:00 PM CDT"
     or "Sat, Oct 31, all day". Empty for an unreadable event. */
  function eventWhen(ev, tz) {
    const e = E.cleanEvent(ev);
    if (!e) return "";
    let date = e.start, time = "all day";
    if (!e.all_day) {
      const lc = localClock(e.start, tz);
      date = lc[0][0] + "-" + E.pad2(lc[0][1]) + "-" + E.pad2(lc[0][2]);
      time = clockTime(lc[0], lc[1]);
    }
    const dt = new Date(date + "T00:00:00Z");
    return DAYS[dt.getUTCDay()].slice(0, 3) + ", " + MONTHS[dt.getUTCMonth()] + " " + E.pad2(dt.getUTCDate()) + ", " + time;
  }

  function eventWhere(ev) {
    const e = E.cleanEvent(ev);
    return e ? [e.venue, e.place].filter(Boolean).join(", ") : "";
  }

  function hasEvents(brief) {
    return (brief.categories || []).some(c => Array.isArray(c.items) && c.items.some(it => it && E.cleanEvent(it.event)));
  }

  /* A story's or the forecast's time, short: "Oct 25, 9:20 AM CDT". */
  function stamp(iso, tz) {
    const lc = localClock(iso, tz);
    if (!lc) return "";
    const c = lc[0];
    return MONTHS[c[1] - 1] + " " + E.pad2(c[2]) + ", " + clockTime(c, lc[1]);
  }

  function ageOf(item, brief) {
    if (typeof item.age_hours === "number" && isFinite(item.age_hours)) return item.age_hours;
    const p = E.parseIso(item.published);
    const g = E.parseIso(brief.generated_at);
    if (p === null || g === null) return null;
    return E.round1(Math.max(0, (g - p) / 3600000));
  }

  function safeHref(u) { return E.validUrl(u) ? String(u).trim() : ""; }

  /* Icons and artwork come from data/icons.js and are drawn for this project. */
  function iconSvg(name, cls) {
    const inner = ICONS.icons[name] || ICONS.icons.news || "";
    return '<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + "</svg>";
  }

  function iconOf(cat, cfg) {
    const own = E.collapse(cat.icon);
    if (own && ICONS.icons[own]) return own;
    const match = (cfg.categories || []).filter(c => c.id === cat.id)[0];
    if (match && ICONS.icons[match.icon]) return match.icon;
    return "news";
  }

  function wxKind(code) {
    for (const k of Object.keys(ICONS.weather_codes)) if (ICONS.weather_codes[k].indexOf(code) >= 0) return k;
    return "cloudy";
  }

  function wxSvg(kind, cls) {
    return '<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      (ICONS.weather[kind] || "") + "</svg>";
  }

  function rnd(x) { return Math.floor(x + 0.5); }

  /* The forecast panel. Numbers are checked before they are written, so a
     pasted brief cannot put markup into the page through them. */
  function weatherHtml(wx, day, tz) {
    if (!wx || typeof wx !== "object" || Array.isArray(wx) || !Array.isArray(wx.days)) return "";
    const days = wx.days.filter(d => d && typeof d === "object" && E.isDateStr(d.date)).slice(0, 4);
    if (!days.length) return "";
    const unit = wx.units === "celsius" ? "C" : "F";
    const cur = wx.current && typeof wx.current === "object" && isNum(wx.current.temp) ? wx.current : null;
    const nowKind = wxKind(cur ? cur.code : days[0].code);
    const place = E.collapse(wx.place) || "your area";
    let h = '<section class="wx"><div class="wxnow">' + wxSvg(nowKind, "wxi big") + '<div><div class="wxk">Weather &middot; ' + esc(place) + "</div>" +
      (cur ? '<div class="wxt">' + rnd(cur.temp) + "&deg;" + unit + "</div>" : "") + '<div class="wxw">' + esc(ICONS.weather_words[nowKind] || "") +
      (cur ? " now" : " today") + '</div></div></div><ol class="wxd">';
    days.forEach(d => {
      const k = wxKind(d.code);
      const label = d.date === day ? "Today" : DAYS[new Date(d.date + "T00:00:00Z").getUTCDay()].slice(0, 3);
      const hi = isNum(d.hi) ? rnd(d.hi) + "&deg;" : "&ndash;";
      const lo = isNum(d.lo) ? rnd(d.lo) + "&deg;" : "&ndash;";
      const rain = isNum(d.rain) && d.rain > 0 ? rnd(d.rain) + "% rain" : "";
      h += '<li title="' + esc(ICONS.weather_words[k] || "") + '"><span class="wxdn">' + label + "</span>" + wxSvg(k, "wxi") +
        '<span class="wxhl"><b>' + hi + "</b> / " + lo + '</span><span class="wxr">' + rain + "</span></li>";
    });
    const when = stamp(wx.fetched_at, tz);
    return h + '</ol><p class="wxs">Forecast by <a href="https://open-meteo.com/">Open-Meteo.com</a> (CC BY 4.0)' +
      (when ? " &middot; updated " + when : "") + "</p></section>";
  }

  function stats(brief) {
    const cats = Array.isArray(brief.categories) ? brief.categories : [];
    const s = { total: 0, news: 0, backfill: 0, reference: 0, filled: 0, cats: cats.length, outlets: 0, empty: [] };
    const outlets = Object.create(null);
    for (const c of cats) {
      const items = Array.isArray(c.items) ? c.items : [];
      if (items.length) s.filled += 1; else s.empty.push(c);
      for (const it of items) {
        s.total += 1;
        if (it.recency === "news") s.news += 1;
        else if (it.recency === "backfill") s.backfill += 1;
        else s.reference += 1;
        const o = E.collapse(it.source).toLowerCase();
        if (o) outlets[o] = true;
      }
    }
    s.outlets = Object.keys(outlets).length;
    return s;
  }

  function subjectLine(brief, cfg) {
    const n = E.normalizeConfig(cfg || {});
    const s = stats(brief);
    const tpl = n.brief.subject;
    let out = tpl.split("{total}").join(String(s.total)).split("{date}").join(String(brief.date || ""))
      .split("{title}").join(String(brief.title || n.brief.title)).split("{empty}").join(String(s.empty.length));
    if (s.empty.length && tpl.indexOf("{empty}") < 0) out += " | " + s.empty.length + " empty";
    if (brief.source === "sample") out = "[SAMPLE] " + out;
    return out;
  }

  /* One countdown as the page draws it, or null when it is unreadable or already past. */
  function countdownData(cd, day) {
    if (!cd || typeof cd !== "object" || !E.isDateStr(cd.date) || !E.isDateStr(day)) return null;
    const days = E.daysBetween(day, cd.date);
    if (days < 0) return null;
    let pct = null;
    if (E.isDateStr(cd.start)) {
      const span = Math.max(E.daysBetween(cd.start, cd.date), 1);
      const done = Math.min(Math.max(E.daysBetween(cd.start, day), 0), span);
      pct = Math.floor(100 * done / span + 0.5);
    }
    const all = (Array.isArray(cd.milestones) ? cd.milestones : []).filter(m => m && typeof m === "object" && E.isDateStr(m.date)).map(m => ({ date: m.date, label: E.collapse(m.label), note: E.collapse(m.note), mark: false }));
    all.push({ date: cd.date, label: "Target date", note: E.collapse(cd.label), mark: true });
    all.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : a.mark === b.mark ? 0 : a.mark ? 1 : -1));
    const upcoming = all.filter(m => m.date >= day).slice(0, 5);
    return { days: days, pct: pct, label: E.collapse(cd.label), date: cd.date, upcoming: upcoming };
  }

  /* Every countdown in the settings that is still ahead, at most E.MAX_COUNTDOWNS. */
  function countdownList(cfg, day) {
    const list = Array.isArray(cfg.countdowns) ? cfg.countdowns.slice(0, E.MAX_COUNTDOWNS) : [];
    return list.map(cd => countdownData(cd, day)).filter(Boolean);
  }

  function countdownHtml(c, day) {
    const rows = c.upcoming.map(m => {
      const dd = E.daysBetween(day, m.date);
      const cls = m.mark ? "ms-mark" : dd <= 30 ? "ms-hot" : dd <= 120 ? "ms-warm" : "ms-cool";
      const when = dd === 0 ? "today" : dd + " d";
      const note = m.note ? " &middot; " + esc(m.note) : "";
      return '<li><span class="pill ' + cls + '">' + when + '</span><span>' + esc(m.label) +
        '<span class="msn">' + shortDate(m.date) + note + '</span></span></li>';
    }).join("");
    const sub = prettyDate(c.date) + (c.pct === null ? "" : " &middot; " + c.pct + "% of the countdown elapsed");
    const bar = c.pct === null ? "" : '<div class="bar"><div class="barf" style="width:' + Math.max(c.pct, 1) + '%"></div></div>';
    return '<section class="cd"><div class="cdtop"><div class="cdn">' + c.days + '</div><div class="cdt"><div class="cdk">' +
      esc(c.label) + '</div><div class="cds">' + sub + '</div>' + bar + '</div></div>' +
      (rows ? '<ul class="ms">' + rows + '</ul>' : "") + '</section>';
  }

  function pill(item, age) {
    if (item.recency === "reference") return '<span class="pill ref">REFERENCE &middot; undated</span>';
    if (item.recency === "backfill") return '<span class="pill old">OLDER &middot; ' + E.humanizeAge(age) + '</span>';
    const cls = age === null ? "f3" : age < 6 ? "f1" : age < 12 ? "f2" : "f3";
    return '<span class="pill ' + cls + '">' + E.humanizeAge(age) + '</span>';
  }

  /* The Lead Analysis lines, without the "NONE" an assistant writes for an empty section. */
  function analysisParts(a) {
    const keep = t => Boolean(t) && !/^none\.?$/i.test(t);
    const conn = E.collapse(a.connection);
    const act = E.collapse(a.action);
    return {
      top: (Array.isArray(a.top_three) ? a.top_three : []).map(E.collapse).filter(keep),
      watch: (Array.isArray(a.watch) ? a.watch : (a.watch ? [a.watch] : [])).map(E.collapse).filter(keep),
      conn: keep(conn) ? conn : "",
      act: keep(act) ? act : ""
    };
  }

  function isNum(v) { return typeof v === "number" && isFinite(v); }

  function analysisHtml(a, cfg) {
    if (!a || typeof a !== "object") return "";
    const { top, watch, conn, act } = analysisParts(a);
    if (!top.length && !watch.length && !conn && !act) return "";
    let h = '<section class="an"><h2 class="anh">Lead analysis</h2>';
    if (top.length) h += '<div class="anb"><b>Top three</b><ol>' + top.map(t => "<li>" + esc(t) + "</li>").join("") + "</ol></div>";
    if (conn) h += '<div class="anr"><b>Connection:</b> ' + esc(conn) + "</div>";
    if (watch.length) h += '<div class="anr"><b>' + esc(cfg.brief.watch_label) + ':</b><ul>' + watch.map(t => "<li>" + esc(t) + "</li>").join("") + "</ul></div>";
    if (act) h += '<div class="anr"><b>Action:</b> ' + esc(act) + "</div>";
    return h + '<p class="anf">Analysis is inference from the headlines below, not reporting. Check the linked sources before acting.</p></section>';
  }

  function cardHtml(cat, brief, cfg, index, win) {
    const color = /^#[0-9a-fA-F]{6}$/.test(String(cat.color || "")) ? cat.color : E.PALETTE[index % E.PALETTE.length];
    const items = Array.isArray(cat.items) ? cat.items : [];
    let lead = false;
    const rows = items.map(it => {
      const age = ageOf(it, brief);
      const href = safeHref(it.url);
      const title = esc(E.collapse(it.title));
      const head = href ? '<a class="hl" href="' + esc(href) + '">' + title + "</a>" : '<span class="hl">' + title + "</span>";
      let src = esc(E.collapse(it.source));
      const tz = cfg.delivery && cfg.delivery.timezone;
      const when = eventWhen(it.event, tz);
      if (when) { if (eventWhere(it.event)) src += (src ? " &middot; " : "") + esc(eventWhere(it.event)); }
      else if (it.published && it.recency !== "reference" && stamp(it.published, tz)) src += (src ? " &middot; " : "") + stamp(it.published, tz);
      const sum = E.collapse(it.summary);
      const st = cfg.brief.conversation_starters && E.collapse(it.starter) ? '<p class="st">Ask: ' + esc(E.collapse(it.starter)) + "</p>" : "";
      const badge = when ? '<span class="pill ev">' + esc(when) + "</span>" : pill(it, age);
      const text = head + '<div class="meta">' + badge + '<span class="src">' + src + "</span></div>" +
        (sum ? '<p class="sum">' + esc(sum) + "</p>" : "") + st;
      const img = E.validImage(it.image) ? '<img src="' + esc(it.image) + '" alt="" loading="lazy" referrerpolicy="no-referrer">' : "";
      if (!img) return '<li class="it">' + text + "</li>";
      // The first story with a photo leads the card; later ones get a thumbnail.
      const wrap = cls => href ? '<a class="' + cls + '" href="' + esc(href) + '" tabindex="-1" aria-hidden="true">' + img + "</a>" : '<span class="' + cls + '">' + img + "</span>";
      if (!lead) { lead = true; return '<li class="it lead">' + wrap("ph") + text + "</li>"; }
      return '<li class="it th"><div class="tx">' + text + "</div>" + wrap("thumb") + "</li>";
    });
    const body = rows.length ? '<ul class="items">' + rows.join("") + "</ul>"
      : cat.unchecked === true ? '<p class="none">Not checked today: the news search did not answer, so this desk could not be searched. Try again later.</p>'
        : '<p class="none">No new items. Nothing was published in the last ' + win + " hours that you have not already been sent.</p>";
    const nNews = items.filter(i => i.recency === "news").length;
    const nBack = items.filter(i => i.recency === "backfill").length;
    const nRef = items.filter(i => i.recency === "reference").length;
    const mix = nNews + " fresh" + (nBack ? ", " + nBack + " older" : "") + (nRef ? ", " + nRef + " reference" : "");
    const sig = E.collapse(cat.signal);
    const so = E.collapse(cat.so_what);
    const sigRow = sig || so ? '<p class="sig">' + (sig ? "<b>Signal:</b> " + esc(sig) : "") + (sig && so ? "<br>" : "") +
      (so ? "<b>So what:</b> " + esc(so) : "") + "</p>" : "";
    return '<section class="card" style="--c:' + color + '"><h2 class="ch"><span class="ico">' + iconSvg(iconOf(cat, cfg), "i") + '</span><span class="tag">' + esc(tagOf(cat, index)) +
      '</span><span class="cn">' + esc(cat.name) + '</span><span class="mix">' + mix + "</span></h2>" + sigRow + body + "</section>";
  }

  /* Short desk label on each card: the category's own tag, else T1, T2 and so on. */
  function tagOf(cat, index) {
    const t = E.collapse(cat.tag);
    return t && Array.from(t).length <= 8 ? t : "T" + (index + 1);
  }

  function sourceLabel(brief) {
    if (brief.source === "sample") return "sample data, not real news";
    if (brief.source === "ai") return "written by an AI assistant with web search" + (E.collapse(brief.model) ? " (" + E.collapse(brief.model) + ")" : "");
    if (brief.source === "web") return "collected in your browser from publisher feeds, the backup collection and the GDELT news index";
    return "collected by the Daily Brief from Google News and publisher feeds";
  }

  function render(brief, cfg) {
    const n = E.normalizeConfig(cfg || {});
    const s = stats(brief);
    const win = isNum(brief.window_hours) ? brief.window_hours
      : isNum(n.brief.window_hours) ? n.brief.window_hours : E.DEFAULTS.brief.window_hours;
    const cap = isNum(n.brief.summary_max_chars) ? n.brief.summary_max_chars : E.DEFAULTS.brief.summary_max_chars;
    const title = E.collapse(brief.title) || n.brief.title;
    const day = String(brief.date || "");
    const withheld = typeof brief.withheld === "number" ? brief.withheld : null;
    const built = builtLabel(brief.generated_at, n.delivery && n.delivery.timezone);
    const events = hasEvents(brief);
    let dek = s.total + " stories across " + s.cats + " categories &middot; " + s.news + " published in the last " + win + " hours";
    if (brief.ledger_applied) dek += withheld ? " &middot; " + withheld + " withheld as already sent" : " &middot; nothing here has been sent to you before";
    const tiles = [[s.total, "stories"], [s.news, "fresh, under " + win + "h"], [s.filled + " of " + s.cats, "categories filled"],
      brief.ledger_applied ? [withheld || 0, "withheld as already sent"] : [s.outlets, "outlets"]];
    const tilesHtml = '<div class="tiles">' + tiles.map(t => '<div class="tile"><div class="tn">' + esc(t[0]) +
      '</div><div class="tl">' + esc(t[1]) + "</div></div>").join("") + "</div>";
    const segs = [["Fresh", s.news, MIX_COLORS.news], ["Older", s.backfill, MIX_COLORS.backfill], ["Reference", s.reference, MIX_COLORS.reference]];
    const cells = segs.filter(x => x[1] > 0).map(x => '<span class="seg" style="width:' + Math.max(1, Math.floor(100 * x[1] / Math.max(s.total, 1) + 0.5)) +
      '%;background:' + x[2] + '"></span>').join("");
    const legend = segs.map(x => '<span class="lg"><span class="sw" style="background:' + x[2] + '"></span>' + x[0] + " " + x[1] + "</span>").join("");
    const bar = cells ? '<div class="srcbar">' + cells + '</div><div class="lgd">Today\'s stories by age: ' + legend + "</div>" : "";
    const cds = countdownList(n, day);
    const quiet = s.empty.filter(c => c.unchecked !== true);
    const unchecked = s.empty.filter(c => c.unchecked === true);
    const gap = (quiet.length ? '<div class="gap">No new items for: ' + quiet.map(c => esc(c.name)).join(", ") + ". Nothing was published in the last " +
      win + " hours that had not already been sent in an earlier brief.</div>" : "") +
      (unchecked.length ? '<div class="gap">Not checked today, because the news search did not answer: ' + unchecked.map(c => esc(c.name)).join(", ") + ". Try again later.</div>" : "");
    const sample = brief.source === "sample" ? '<div class="sample">Sample brief: invented headlines that show the layout. Nothing here is real news and the links go to example.com.</div>' : "";
    const cards = (brief.categories || []).map((c, i) => cardHtml(c, brief, n, i, win)).join("");
    const subject = subjectLine(brief, n);
    // No script can run in the page, wherever it is opened, even if something slipped past the escaping.
    const html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; img-src https: data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">" +
      "<title>" + esc(subject) + "</title><style>" + CSS + "</style></head><body>" +
      '<header class="mast"><div class="art">' + (ICONS.art.masthead || "") + '</div><div class="in"><div class="kick">' + iconSvg("sunrise", "ki") + esc(title) + " &middot; Edition " + esc(day) + '</div><h1 class="ttl">' +
      esc(prettyDate(day)) + '</h1><p class="dl">' + dek + "</p>" + (built ? '<p class="built">Built ' + esc(built) + "</p>" : "") +
      '</div></header><div class="rule"></div><main class="in">' +
      sample + weatherHtml(brief.weather, day, n.delivery && n.delivery.timezone) + (cds.length ? '<div class="cdg">' + cds.map(c => countdownHtml(c, day)).join("") + "</div>" : "") + tilesHtml + bar + analysisHtml(brief.analysis, n) + gap + '<div class="grid">' + cards + "</div>" +
      '<div class="legend"><b>Reading the pills.</b> Green, teal and amber pills give a story\'s age inside the ' + win +
      '-hour window (under 6h, under 12h, under ' + win + 'h). <span class="pill old">OLDER</span> is beyond ' + win +
      'h, used only where a category had no fresh material, and stamped with its true age. <span class="pill ref">REFERENCE</span> is an undated authoritative page, never presented as an event.' +
      (events ? ' A <span class="pill ev">blue</span> pill gives the day and time of a coming event.' : "") + "</div>" +
      '</main><footer class="foot"><div class="in">' + (built ? "Built " + esc(built) : "Generated " + esc(brief.generated_at || "")) +
      " &middot; " + esc(sourceLabel(brief)) + " &middot; " + win +
      "-hour window &middot; summaries capped at " + esc(cap) + " characters &middot; Daily Brief " + E.VERSION +
      "<br>Headlines, photos and summaries belong to their publishers; every link opens the original story." +
      (events ? "<br>" + EVENT_NOTE : "") + "</div></footer></body></html>";
    return { subject: subject, html: html, text: plainText(brief, n, s, cds, win, title, day, withheld, built) };
  }

  function plainText(brief, n, s, cds, win, title, day, withheld, built) {
    const L = [];
    const rule = "=".repeat(65);
    L.push(title.toUpperCase() + " - " + prettyDate(day));
    if (built) L.push("Built " + built);
    L.push(rule);
    L.push(s.total + " stories across " + s.cats + " categories | " + s.news + " fresh under " + win + "h" +
      (brief.ledger_applied ? " | " + (withheld || 0) + " withheld as already sent" : ""));
    if (brief.source === "sample") L.push("SAMPLE: invented headlines that show the layout. Nothing here is real news.");
    const wx = brief.weather;
    if (wx && typeof wx === "object" && !Array.isArray(wx) && Array.isArray(wx.days)) {
      const unit = wx.units === "celsius" ? "C" : "F";
      const parts = wx.days.filter(d => d && typeof d === "object" && E.isDateStr(d.date)).slice(0, 4).map(d =>
        (d.date === day ? "Today" : DAYS[new Date(d.date + "T00:00:00Z").getUTCDay()].slice(0, 3)) + " " + (ICONS.weather_words[wxKind(d.code)] || "") +
        (isNum(d.hi) ? " " + rnd(d.hi) + unit : "") + (isNum(d.lo) ? "/" + rnd(d.lo) + unit : "") + (isNum(d.rain) && d.rain > 0 ? " " + rnd(d.rain) + "% rain" : ""));
      if (parts.length) L.push("", "WEATHER, " + (E.collapse(wx.place) || "your area").toUpperCase() + ": " + parts.join(" | "));
    }
    for (const cd of cds) {
      L.push("", cd.label.toUpperCase() + ": " + cd.days + " days to " + prettyDate(cd.date) + (cd.pct === null ? "" : " (" + cd.pct + "% elapsed)"));
      for (const m of cd.upcoming) L.push("  " + String(E.daysBetween(day, m.date)).padStart(4) + " d  " + m.date + "  " + m.label + (m.note ? "  [" + m.note + "]" : ""));
    }
    const a = brief.analysis;
    if (a && typeof a === "object") {
      const { top, watch, conn, act } = analysisParts(a);
      if (top.length || watch.length || conn || act) {
        L.push("", "LEAD ANALYSIS (inference, check the sources)");
        top.forEach((t, i) => L.push("  " + (i + 1) + ". " + t));
        if (conn) L.push("  Connection: " + conn);
        watch.forEach(t => L.push("  " + n.brief.watch_label + ": " + t));
        if (act) L.push("  Action: " + act);
      }
    }
    (brief.categories || []).forEach((cat, index) => {
      L.push("", "[" + tagOf(cat, index) + "] " + E.collapse(cat.name), "-".repeat(60));
      if (E.collapse(cat.signal)) L.push("  Signal: " + E.collapse(cat.signal));
      if (E.collapse(cat.so_what)) L.push("  So what: " + E.collapse(cat.so_what));
      const items = Array.isArray(cat.items) ? cat.items : [];
      if (!items.length) L.push(cat.unchecked === true ? "  Not checked today: the news search did not answer. Try again later."
        : "  No new items in the last " + win + " hours that you have not already been sent.");
      for (const it of items) {
        const age = ageOf(it, brief);
        const when = eventWhen(it.event, n.delivery.timezone);
        const label = when ? "EVENT, " + when + (eventWhere(it.event) ? ", " + eventWhere(it.event) : "")
          : it.recency === "reference" ? "REFERENCE, undated" : it.recency === "backfill" ? "OLDER, " + E.humanizeAge(age) : E.humanizeAge(age);
        L.push("  * " + E.collapse(it.title));
        L.push("    " + (E.collapse(it.source) ? E.collapse(it.source) + " | " : "") + label);
        L.push("    " + E.collapse(it.url));
        if (E.collapse(it.summary)) L.push("    " + E.collapse(it.summary));
        if (n.brief.conversation_starters && E.collapse(it.starter)) L.push("    Ask: " + E.collapse(it.starter));
      }
    });
    L.push("", rule, (built ? "Built " + built : "Generated " + (brief.generated_at || "")) + " | " + sourceLabel(brief) +
      " | Daily Brief " + E.VERSION);
    if (hasEvents(brief)) L.push(EVENT_NOTE);
    return L.join("\n") + "\n";
  }

  return { CSS, ICONS, esc, prettyDate, builtLabel, stamp, eventWhen, eventWhere, stats, subjectLine, countdownData, countdownList, iconSvg, wxKind, wxSvg, weatherHtml, render };
});
