/* Daily Brief newsletter theme: turns a brief into an email-ready HTML page, a
   plain-text copy and a subject line. Table layout and solid colour cells only,
   because email programs strip scripts, SVG and background images.
   dailybrief/render.py mirrors this file and reads the stylesheet below from it,
   so the desktop email and the in-app preview are the same document. */
(function (root, factory) {
  const engine = typeof module === "object" && module.exports ? require("./engine.js") : root.DB_ENGINE;
  const api = factory(engine);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.DB_NEWSLETTER = api;
})(typeof self !== "undefined" ? self : this, function (E) {
  "use strict";

  /*CSS-START*/
  const CSS = `
body{margin:0;padding:0;background:#eef1f5;font-family:'Segoe UI',Roboto,Arial,Helvetica,sans-serif;font-size:14px;line-height:1.5;color:#1a1a1a;}
table.wrap{width:100%;max-width:680px;margin:0 auto;border-collapse:collapse;}
td.mast{background:#0f2744;padding:22px 24px 16px;}
div.kick{font-size:11px;font-weight:bold;letter-spacing:.18em;text-transform:uppercase;color:#e0b43a;}
div.ttl{font-family:Georgia,'Times New Roman',serif;font-size:28px;line-height:1.15;font-weight:bold;color:#ffffff;margin:6px 0 4px;}
div.dl{font-size:13px;color:#d3dbe6;}
td.rule{background:#d4a017;height:4px;font-size:0;line-height:0;padding:0;}
td.body{background:#ffffff;padding:18px 22px 6px;}
table.cd{width:100%;border-collapse:collapse;background:#fff8e1;border-left:5px solid #d4a017;margin:0 0 16px;}
td.cdn{padding:14px 10px 14px 16px;font-family:Georgia,serif;font-size:44px;line-height:1;font-weight:bold;color:#0f2744;white-space:nowrap;vertical-align:top;width:1%;}
td.cdt{padding:16px 16px 10px 6px;vertical-align:top;}
div.cdk{font-size:11px;font-weight:bold;letter-spacing:.14em;color:#6e5426;text-transform:uppercase;}
div.cds{font-size:13px;color:#4a4a4a;margin:2px 0 8px;}
table.bar{width:100%;border-collapse:collapse;}
td.barf{background:#d4a017;height:9px;font-size:0;line-height:0;}
td.bare{background:#ece4c8;height:9px;font-size:0;line-height:0;}
td.mst{padding:0 16px 12px;}
table.ms{width:100%;border-collapse:collapse;font-size:13px;}
table.ms td{padding:5px 0;border-top:1px solid #efe6c7;vertical-align:top;}
table.ms td.msd{width:1%;white-space:nowrap;padding-right:10px;}
span.msn{display:block;font-size:11px;color:#666666;}
span.pill{display:inline-block;font-size:10px;font-weight:bold;color:#ffffff;padding:2px 7px;border-radius:10px;letter-spacing:.03em;vertical-align:middle;margin-right:6px;}
span.ms-hot{background:#b03a2e;} span.ms-warm{background:#a04000;}
span.ms-cool{background:#34495e;} span.ms-mark{background:#d4a017;color:#0f2744;}
span.f1{background:#1b6e3d;} span.f2{background:#0f6e5c;} span.f3{background:#8a5a00;}
span.old{background:#6e5426;} span.ref{background:#5b3485;}
table.tiles{width:100%;border-collapse:separate;border-spacing:6px 0;margin:0 0 14px;}
td.tile{background:#f4f6f9;border-top:3px solid #0f2744;padding:10px 6px;text-align:center;width:25%;}
div.tn{font-family:Georgia,serif;font-size:24px;font-weight:bold;color:#0f2744;line-height:1.1;}
div.tl{font-size:11px;color:#555555;margin-top:2px;}
table.srcbar{width:100%;border-collapse:collapse;margin:0 0 4px;}
table.srcbar td.seg{height:8px;font-size:0;line-height:0;}
div.lgd{font-size:11px;color:#555555;margin:0 0 18px;}
span.lg{display:inline-block;margin:2px 12px 2px 0;white-space:nowrap;}
span.sw{display:inline-block;width:9px;height:9px;margin-right:4px;vertical-align:middle;border-radius:2px;}
table.card{width:100%;border-collapse:collapse;margin:0 0 16px;background:#ffffff;border:1px solid #e3e8ee;}
td.ch{padding:10px 14px;border-bottom:1px solid #e3e8ee;background:#f8f9fb;}
span.tag{display:inline-block;font-size:11px;font-weight:bold;color:#ffffff;padding:2px 7px;border-radius:3px;margin-right:8px;vertical-align:middle;letter-spacing:.04em;}
span.cn{font-family:Georgia,serif;font-size:17px;font-weight:bold;color:#0f2744;vertical-align:middle;}
span.mix{float:right;font-size:11px;color:#666666;margin-top:3px;}
td.sig{padding:9px 14px;border-bottom:1px solid #f0f2f5;background:#fbfaf4;font-size:13px;line-height:1.5;color:#333333;}
td.it{padding:11px 14px;border-bottom:1px solid #f0f2f5;}
a.hl{font-size:15px;font-weight:bold;line-height:1.35;color:#0f2744;text-decoration:none;}
div.meta{margin:5px 0 4px;}
span.src{font-size:11px;color:#666666;vertical-align:middle;}
div.sum{font-size:13px;line-height:1.55;color:#3d3d3d;}
div.st{font-size:12px;line-height:1.5;color:#5b3485;margin-top:4px;}
div.none{font-size:13px;color:#666666;font-style:italic;}
div.gap{background:#fdecea;border-left:4px solid #b03a2e;padding:10px 12px;font-size:12px;color:#7b241c;margin:0 0 16px;}
div.sample{background:#fff8e1;border-left:4px solid #d4a017;padding:10px 12px;font-size:12px;color:#5c4510;margin:0 0 16px;}
div.legend{background:#f4f6f9;border-left:4px solid #0f2744;padding:10px 12px;font-size:12px;line-height:1.55;color:#333333;margin:8px 0 14px;}
div.an{border:1px solid #e3e8ee;border-top:4px solid #0f2744;background:#f8f9fb;padding:12px 14px;margin:0 0 16px;}
div.anh{font-size:11px;font-weight:bold;letter-spacing:.14em;color:#0f2744;text-transform:uppercase;margin-bottom:8px;}
div.anb{font-size:14px;line-height:1.55;}
div.anb ol,div.anr ul{margin:4px 0 0;padding-left:20px;}
div.anr{margin-top:10px;font-size:13px;line-height:1.5;}
div.anf{font-size:11px;color:#666666;margin-top:10px;}
td.foot{background:#0f2744;padding:14px 22px;font-size:11px;line-height:1.6;color:#c3cdd9;}
`;
  /*CSS-END*/

  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December"];
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const TBL = 'role="presentation" width="100%" cellpadding="0" cellspacing="0"';
  const MIX_COLORS = { news: "#1b6e3d", backfill: "#6e5426", reference: "#5b3485" };

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

  function stamp(iso) {
    const ms = E.parseIso(iso);
    if (ms === null) return "";
    const dt = new Date(ms);
    return MONTHS[dt.getUTCMonth()] + " " + E.pad2(dt.getUTCDate()) + ", " + E.pad2(dt.getUTCHours()) + ":" + E.pad2(dt.getUTCMinutes()) + "Z";
  }

  function ageOf(item, brief) {
    if (typeof item.age_hours === "number" && isFinite(item.age_hours)) return item.age_hours;
    const p = E.parseIso(item.published);
    const g = E.parseIso(brief.generated_at);
    if (p === null || g === null) return null;
    return E.round1(Math.max(0, (g - p) / 3600000));
  }

  function safeHref(u) { return E.validUrl(u) ? String(u).trim() : ""; }

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

  function countdownData(cfg, day) {
    const cd = cfg.countdown;
    if (!cd || cd.enabled !== true || !E.isDateStr(cd.date) || !E.isDateStr(day)) return null;
    const days = E.daysBetween(day, cd.date);
    let pct = null;
    if (E.isDateStr(cd.start)) {
      const span = Math.max(E.daysBetween(cd.start, cd.date), 1);
      const done = Math.min(Math.max(E.daysBetween(cd.start, day), 0), span);
      pct = Math.floor(100 * done / span + 0.5);
    }
    const all = (cd.milestones || []).filter(m => E.isDateStr(m.date)).map(m => ({ date: m.date, label: E.collapse(m.label), note: E.collapse(m.note), mark: false }));
    all.push({ date: cd.date, label: "Target date", note: E.collapse(cd.label), mark: true });
    all.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : a.mark === b.mark ? 0 : a.mark ? 1 : -1));
    const upcoming = all.filter(m => m.date >= day).slice(0, 5);
    return { days: days, pct: pct, label: E.collapse(cd.label), date: cd.date, upcoming: upcoming };
  }

  function countdownHtml(c, day) {
    const rows = c.upcoming.map(m => {
      const dd = E.daysBetween(day, m.date);
      const cls = m.mark ? "ms-mark" : dd <= 30 ? "ms-hot" : dd <= 120 ? "ms-warm" : "ms-cool";
      const when = dd === 0 ? "today" : dd + " d";
      const note = m.note ? " &middot; " + esc(m.note) : "";
      return '<tr><td class="msd"><span class="pill ' + cls + '">' + when + '</span></td><td>' + esc(m.label) +
        '<span class="msn">' + shortDate(m.date) + note + '</span></td></tr>';
    }).join("");
    const sub = prettyDate(c.date) + (c.pct === null ? "" : " &middot; " + c.pct + "% of the countdown elapsed");
    const bar = c.pct === null ? "" : '<table class="bar" ' + TBL + '><tr><td class="barf" width="' + Math.max(c.pct, 1) +
      '%"></td><td class="bare" width="' + (100 - Math.max(c.pct, 1)) + '%"></td></tr></table>';
    return '<table class="cd" ' + TBL + '><tr><td class="cdn">' + c.days + '</td><td class="cdt"><div class="cdk">' +
      esc(c.label) + '</div><div class="cds">' + sub + '</div>' + bar + '</td></tr>' +
      (rows ? '<tr><td class="mst" colspan="2"><table class="ms" ' + TBL + '>' + rows + '</table></td></tr>' : "") + '</table>';
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
    let h = '<div class="an"><div class="anh">Lead analysis</div>';
    if (top.length) h += '<div class="anb"><b>Top three</b><ol>' + top.map(t => "<li>" + esc(t) + "</li>").join("") + "</ol></div>";
    if (conn) h += '<div class="anr"><b>Connection:</b> ' + esc(conn) + "</div>";
    if (watch.length) h += '<div class="anr"><b>' + esc(cfg.brief.watch_label) + ':</b><ul>' + watch.map(t => "<li>" + esc(t) + "</li>").join("") + "</ul></div>";
    if (act) h += '<div class="anr"><b>Action:</b> ' + esc(act) + "</div>";
    return h + '<div class="anf">Analysis is inference from the headlines below, not reporting. Check the linked sources before acting.</div></div>';
  }

  function cardHtml(cat, brief, cfg, index, win) {
    const color = /^#[0-9a-fA-F]{6}$/.test(String(cat.color || "")) ? cat.color : E.PALETTE[index % E.PALETTE.length];
    const items = Array.isArray(cat.items) ? cat.items : [];
    const rows = items.map(it => {
      const age = ageOf(it, brief);
      const href = safeHref(it.url);
      const title = esc(E.collapse(it.title));
      const head = href ? '<a class="hl" href="' + esc(href) + '">' + title + "</a>" : '<span class="hl">' + title + "</span>";
      let src = esc(E.collapse(it.source));
      if (it.published && it.recency !== "reference" && stamp(it.published)) src += (src ? " &middot; " : "") + stamp(it.published);
      const sum = E.collapse(it.summary);
      const st = cfg.brief.conversation_starters && E.collapse(it.starter) ? '<div class="st">Ask: ' + esc(E.collapse(it.starter)) + "</div>" : "";
      return '<tr><td class="it">' + head + '<div class="meta">' + pill(it, age) + '<span class="src">' + src + "</span></div>" +
        (sum ? '<div class="sum">' + esc(sum) + "</div>" : "") + st + "</td></tr>";
    });
    if (!rows.length) {
      rows.push('<tr><td class="it"><div class="none">No new items. Nothing was published in the last ' + win +
        " hours that you have not already been sent.</div></td></tr>");
    }
    const nNews = items.filter(i => i.recency === "news").length;
    const nBack = items.filter(i => i.recency === "backfill").length;
    const nRef = items.filter(i => i.recency === "reference").length;
    const mix = nNews + " fresh" + (nBack ? ", " + nBack + " older" : "") + (nRef ? ", " + nRef + " reference" : "");
    const sig = E.collapse(cat.signal);
    const so = E.collapse(cat.so_what);
    const sigRow = sig || so ? '<tr><td class="sig">' + (sig ? "<b>Signal:</b> " + esc(sig) : "") + (sig && so ? "<br>" : "") +
      (so ? "<b>So what:</b> " + esc(so) : "") + "</td></tr>" : "";
    return '<table class="card" ' + TBL + ' style="border-left:5px solid ' + color + '"><tr><td class="ch"><span class="tag" style="background:' +
      color + '">' + esc(tagOf(cat, index)) + '</span><span class="cn">' + esc(cat.name) + '</span><span class="mix">' + mix + "</span></td></tr>" +
      sigRow + '<tr><td style="padding:0"><table ' + TBL + ">" + rows.join("") + "</table></td></tr></table>";
  }

  /* Short desk label on each card: the category's own tag, else T1, T2 and so on. */
  function tagOf(cat, index) {
    const t = E.collapse(cat.tag);
    return t && Array.from(t).length <= 8 ? t : "T" + (index + 1);
  }

  function sourceLabel(brief) {
    if (brief.source === "sample") return "sample data, not real news";
    if (brief.source === "ai") return "written by an AI assistant with web search" + (E.collapse(brief.model) ? " (" + E.collapse(brief.model) + ")" : "");
    return "collected by the Daily Brief desktop app from Google News and publisher feeds";
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
    let dek = s.total + " stories across " + s.cats + " categories &middot; " + s.news + " published in the last " + win + " hours";
    if (brief.ledger_applied) dek += withheld ? " &middot; " + withheld + " withheld as already sent" : " &middot; nothing here has been sent to you before";
    const tiles = [[s.total, "stories"], [s.news, "fresh, under " + win + "h"], [s.filled + " of " + s.cats, "categories filled"],
      brief.ledger_applied ? [withheld || 0, "withheld as already sent"] : [s.outlets, "outlets"]];
    const tilesHtml = '<table class="tiles" ' + TBL + "><tr>" + tiles.map(t => '<td class="tile"><div class="tn">' + esc(t[0]) +
      '</div><div class="tl">' + esc(t[1]) + "</div></td>").join("") + "</tr></table>";
    const segs = [["Fresh", s.news, MIX_COLORS.news], ["Older", s.backfill, MIX_COLORS.backfill], ["Reference", s.reference, MIX_COLORS.reference]];
    const cells = segs.filter(x => x[1] > 0).map(x => '<td class="seg" width="' + Math.max(1, Math.floor(100 * x[1] / Math.max(s.total, 1) + 0.5)) +
      '%" style="background:' + x[2] + '"></td>').join("");
    const legend = segs.map(x => '<span class="lg"><span class="sw" style="background:' + x[2] + '"></span>' + x[0] + " " + x[1] + "</span>").join("");
    const bar = cells ? '<table class="srcbar" ' + TBL + "><tr>" + cells + '</tr></table><div class="lgd">Today\'s stories by age: ' + legend + "</div>" : "";
    const cd = countdownData(n, day);
    const gap = s.empty.length ? '<div class="gap">No new items for: ' + s.empty.map(c => esc(c.name)).join(", ") + ". Nothing was published in the last " +
      win + " hours that had not already been sent in an earlier brief.</div>" : "";
    const sample = brief.source === "sample" ? '<div class="sample">Sample brief: invented headlines that show the layout. Nothing here is real news and the links go to example.com.</div>' : "";
    const cards = (brief.categories || []).map((c, i) => cardHtml(c, brief, n, i, win)).join("");
    const html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
      "<title>" + esc(title + ", " + day) + "</title><style>" + CSS + "</style></head><body>" +
      '<table class="wrap" ' + TBL + '><tr><td class="mast"><div class="kick">' + esc(title) + " &middot; Edition " + esc(day) + '</div><div class="ttl">' +
      esc(prettyDate(day)) + '</div><div class="dl">' + dek + '</div></td></tr><tr><td class="rule"></td></tr><tr><td class="body">' +
      sample + (cd ? countdownHtml(cd, day) : "") + tilesHtml + bar + analysisHtml(brief.analysis, n) + gap + cards +
      '<div class="legend"><b>Reading the pills.</b> Green, teal and amber pills give a story\'s age inside the ' + win +
      '-hour window (under 6h, under 12h, under ' + win + 'h). <span class="pill old">OLDER</span> is beyond ' + win +
      'h, used only where a category had no fresh material, and stamped with its true age. <span class="pill ref">REFERENCE</span> is an undated authoritative page, never presented as an event.</div>' +
      '</td></tr><tr><td class="foot">Generated ' + esc(brief.generated_at || "") + " &middot; " + esc(sourceLabel(brief)) + " &middot; " + win +
      "-hour window &middot; summaries capped at " + esc(cap) + " characters &middot; Daily Brief " + E.VERSION + "</td></tr></table></body></html>";
    return { subject: subjectLine(brief, n), html: html, text: plainText(brief, n, s, cd, win, title, day, withheld) };
  }

  function plainText(brief, n, s, cd, win, title, day, withheld) {
    const L = [];
    const rule = "=".repeat(65);
    L.push(title.toUpperCase() + " - " + prettyDate(day), rule);
    L.push(s.total + " stories across " + s.cats + " categories | " + s.news + " fresh under " + win + "h" +
      (brief.ledger_applied ? " | " + (withheld || 0) + " withheld as already sent" : ""));
    if (brief.source === "sample") L.push("SAMPLE: invented headlines that show the layout. Nothing here is real news.");
    if (cd) {
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
      if (!items.length) L.push("  No new items in the last " + win + " hours that you have not already been sent.");
      for (const it of items) {
        const age = ageOf(it, brief);
        const label = it.recency === "reference" ? "REFERENCE, undated" : it.recency === "backfill" ? "OLDER, " + E.humanizeAge(age) : E.humanizeAge(age);
        L.push("  * " + E.collapse(it.title));
        L.push("    " + (E.collapse(it.source) ? E.collapse(it.source) + " | " : "") + label);
        L.push("    " + E.collapse(it.url));
        if (E.collapse(it.summary)) L.push("    " + E.collapse(it.summary));
        if (n.brief.conversation_starters && E.collapse(it.starter)) L.push("    Ask: " + E.collapse(it.starter));
      }
    });
    L.push("", rule, "Generated " + (brief.generated_at || "") + " | " + sourceLabel(brief) + " | Daily Brief " + E.VERSION);
    return L.join("\n") + "\n";
  }

  function b64(str) {
    if (typeof Buffer !== "undefined") return Buffer.from(str, "utf-8").toString("base64");
    const bytes = new TextEncoder().encode(str);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  }

  function wrap76(s) { return s.replace(/(.{76})/g, "$1\r\n"); }

  /* An unsent email file. Outlook opens it as a ready-to-send draft; other mail
     programs open it as a message you can forward. */
  function buildEml(out, to, fromName) {
    const boundary = "db-" + E.VERSION.replace(/\./g, "") + "-boundary";
    const subj = "=?UTF-8?B?" + b64(out.subject) + "?=";
    const head = ["X-Unsent: 1", "To: " + (to || []).join(", "), "Subject: " + subj, "MIME-Version: 1.0",
      'Content-Type: multipart/alternative; boundary="' + boundary + '"'];
    if (fromName) head.splice(1, 0, "X-Daily-Brief-From-Name: " + "=?UTF-8?B?" + b64(fromName) + "?=");
    return head.join("\r\n") + "\r\n\r\n" +
      "--" + boundary + "\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" + wrap76(b64(out.text)) + "\r\n" +
      "--" + boundary + "\r\nContent-Type: text/html; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" + wrap76(b64(out.html)) + "\r\n" +
      "--" + boundary + "--\r\n";
  }

  return { CSS, esc, prettyDate, stamp, stats, subjectLine, countdownData, render, buildEml };
});
