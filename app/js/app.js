/* Daily Brief app: the screens. Logic lives in engine.js and newsletter.js;
   saving, the clipboard and the desktop connection live in services.js. */
(function () {
  "use strict";
  const E = window.DB_ENGINE;
  const N = window.DB_NEWSLETTER;
  const S = window.DB_SERVICES;
  const LIB = window.DB_LIBRARY;
  const PROMPTS = window.DB_PROMPTS;
  const SAMPLE = window.DB_SAMPLE;
  const C = window.DB_COLLECT;
  const ICONS = window.DB_ICONS || { icons: {}, art: {} };

  const TABS = ["setup", "categories", "brief", "daily", "ai", "settings", "help"];
  /* Two modes. Before setup is saved, the app shows the interview and the pages
     that need no setup. Once it is saved, the app opens on the brief and the
     interview becomes "Your choices". Categories is a page under Your choices. */
  const NAV = {
    setup: ["setup", "ai", "gap", "settings", "help"],
    ready: ["brief", "setup", "daily", "ai", "gap", "settings", "help"]
  };
  const TAB_NAMES = { setup: { setup: "Setup", ready: "Your choices" }, brief: "Today's brief", categories: "Categories",
    daily: "Every day", ai: "AI assistants", settings: "Settings", help: "Help" };

  const freshBrowser = !S.readStore(S.STORE_KEY, null);  // before anything is saved
  let state = loadState();
  let history = E.cleanLedger(S.readStore(S.LEDGER_KEY, null));
  let desktop = null;
  let job = null;
  let webRun = null;
  let aiPlatform = "claude";

  // ------------------------------------------------------------ state
  function defaultState() {
    return { version: 1, tab: "setup", step: 0, config: null, brief: null, health: null, setup_done: false, auto_run: false,
      editing: false, draft: null, setup_saved: "", welcome: "", brief_sig: "", brief_version: "" };
  }

  function loadState() {
    const s = S.readStore(S.STORE_KEY, null);
    const st = s && s.version === 1 ? Object.assign(defaultState(), s) : defaultState();
    // Version 0.1.0 kept email recipients here; email sending is gone, so they go too.
    delete st.email;
    if (st.tab === "email" || st.tab === "deliver") st.tab = "daily";
    if (st.config) delete st.config.email;
    // Version 0.1.0 had no flag for a finished setup; the last question or a brief means it was done.
    if (s && s.setup_done === undefined && (s.step >= 7 || s.brief)) st.setup_done = true;
    if (!st.config) {
      // First visit: the starter pack without local categories, which need a town.
      st.config = E.configFromPack(LIB, "starter", {});
      st.config.categories = st.config.categories.filter(c => !c.needs_location);
    }
    st.config = dropEmail(E.merge(E.DEFAULTS, st.config));
    if (!st.config.delivery.timezone) st.config.delivery.timezone = browserZone();
    // Unsaved changes to saved choices survive a reload; anything else is dropped.
    if (st.setup_done && st.editing && st.draft && typeof st.draft === "object") {
      st.draft = dropEmail(E.merge(E.DEFAULTS, st.draft));
    } else {
      st.editing = false;
      st.draft = null;
    }
    return st;
  }

  /* Email delivery was removed in 0.2.0. Choices saved before then still list it;
     they lose it quietly instead of showing a warning on every review. */
  function dropEmail(c) {
    if (!c || typeof c !== "object") return c;
    delete c.email;
    if (c.delivery && Array.isArray(c.delivery.channels)) {
      const ch = c.delivery.channels.filter(x => x !== "email");
      c.delivery.channels = ch.length ? ch : ["issue"];
    }
    return c;
  }

  function browserZone() {
    try { return Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) { return ""; }
  }

  const ZONES = ["America/New_York", "America/Chicago", "America/Denver", "America/Phoenix", "America/Los_Angeles",
    "America/Anchorage", "Pacific/Honolulu", "America/Toronto", "Europe/London", "Europe/Berlin", "Asia/Kolkata",
    "Asia/Tokyo", "Australia/Sydney", "UTC"];

  function save() {
    if (!S.writeStore(S.STORE_KEY, state)) toast("This browser is not keeping your data (a private window, or storage is blocked).");
  }

  function saveHistory() { S.writeStore(S.LEDGER_KEY, history); }

  /* While saved choices are being changed, the interview works on a draft. Every
     other page, and every collection, keeps the saved choices until Save changes. */
  function cfg() { return state.editing && state.draft && state.tab === "setup" ? state.draft : state.config; }
  function saved() { return state.config; }
  function ready() { return !!state.setup_done; }

  // ------------------------------------------------------------ DOM helpers
  function h(tag, attrs) {
    const el = document.createElement(tag);
    if (attrs) {
      for (const k of Object.keys(attrs)) {
        const v = attrs[k];
        if (v === null || v === undefined || v === false) continue;
        if (k === "class") el.className = v;
        else if (k === "text") el.textContent = v;
        else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v);
        else if (k === "value") el.value = v;
        else if (k === "checked") el.checked = !!v;
        else if (v === true) el.setAttribute(k, "");
        else el.setAttribute(k, String(v));
      }
    }
    for (let i = 2; i < arguments.length; i++) add(el, arguments[i]);
    return el;
  }

  function add(el, kid) {
    if (kid === null || kid === undefined || kid === false) return;
    if (Array.isArray(kid)) { kid.forEach(k => add(el, k)); return; }
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }

  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }

  /* Icons and artwork are fixed markup from data/icons.js, drawn for this
     project; nothing typed by a person or read from the web goes in here. */
  function ico(name, cls) {
    const s = document.createElement("span");
    s.className = "ic" + (cls ? " " + cls : "");
    s.setAttribute("aria-hidden", "true");
    s.innerHTML = N.iconSvg(ICONS.icons[name] ? name : "news", "i");
    return s;
  }

  function art(name, cls) {
    const d = document.createElement("div");
    d.className = cls || "art";
    d.innerHTML = (ICONS.art && ICONS.art[name]) || "";
    return d;
  }

  function catIcon(cat) {
    if (cat.icon && ICONS.icons[cat.icon]) return cat.icon;
    const lc = E.categoryFromLibrary(LIB, cat.id);
    return lc && lc.icon ? lc.icon : "news";
  }

  function toast(msg) {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => t.classList.remove("show"), 4200);
  }

  function field(label, input, hint) {
    const id = input.id || ("f" + Math.random().toString(36).slice(2, 9));
    input.id = id;
    return h("div", { class: "field" }, h("label", { for: id, text: label }), input, hint ? h("p", { class: "hint", text: hint }) : null);
  }

  function lines(text) { return String(text || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean); }
  function commas(text) { return String(text || "").split(",").map(s => s.trim()).filter(Boolean); }

  function select(options, current, onChange) {
    const s = h("select", { onchange: e => onChange(e.target.value) });
    for (const o of options) {
      const opt = h("option", { value: String(o[0]), text: o[1] });
      if (String(o[0]) === String(current)) opt.selected = true;
      s.append(opt);
    }
    return s;
  }

  function msgList(v) {
    if (!v.errors.length && !v.warnings.length) return h("p", { class: "ok", text: "Everything checks out." });
    return h("div", null,
      v.errors.length ? h("div", { class: "bad" }, h("b", { text: "Fix before continuing:" }), h("ul", null, v.errors.map(e => h("li", { text: e })))) : null,
      v.warnings.length ? h("div", { class: "warn" }, h("b", { text: "Worth a look:" }), h("ul", null, v.warnings.map(w => h("li", { text: w })))) : null);
  }

  function slug(s) { return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 28) || "category"; }

  function uniqueId(base) {
    const ids = cfg().categories.map(c => c.id.toLowerCase());
    let id = base;
    let n = 2;
    while (ids.indexOf(id.toLowerCase()) >= 0) id = base.slice(0, 26) + "-" + n++;
    return id;
  }

  function q(term) { return /\s/.test(term) ? "\"" + term.replace(/"/g, "") + "\"" : term; }

  function today() {
    const d = new Date();
    return d.getFullYear() + "-" + E.pad2(d.getMonth() + 1) + "-" + E.pad2(d.getDate());
  }

  // ------------------------------------------------------------ tabs
  function show(tab, inPlace) {
    if (TABS.indexOf(tab) < 0) tab = "setup";
    // The brief and its pages appear only once setup is saved.
    if (!ready() && ["brief", "daily", "categories"].indexOf(tab) >= 0) tab = "setup";
    state.tab = tab;
    save();
    applyMode();
    const navTab = tab === "categories" ? "setup" : tab;
    for (const t of TABS) {
      document.getElementById("tab-" + t).hidden = t !== tab;
      const btn = document.querySelector('#tabs button[data-tab="' + t + '"]');
      btn.setAttribute("aria-selected", t === navTab ? "true" : "false");
      btn.classList.toggle("active", t === navTab);
    }
    const sec = clear(document.getElementById("tab-" + tab));
    RENDER[tab](sec);
    modebar();
    if (!inPlace) window.scrollTo(0, 0);
  }

  /* Moving to another page or question starts at the top. */
  function rerender() { show(state.tab); }

  /* A change on the page itself redraws it in place: the scroll position, the
     open sections and the focused control stay where they were. */
  function refresh() {
    const y = window.scrollY;
    const sec = document.getElementById("tab-" + state.tab);
    const open = {};
    sec.querySelectorAll("details[data-key]").forEach(d => { open[d.getAttribute("data-key")] = d.open; });
    const a = document.activeElement;
    const focusId = a && a.id && sec.contains(a) ? a.id : "";
    show(state.tab, true);
    const now = document.getElementById("tab-" + state.tab);
    now.querySelectorAll("details[data-key]").forEach(d => { const k = d.getAttribute("data-key"); if (k in open) d.open = open[k]; });
    window.scrollTo(0, y);
    const f = focusId ? document.getElementById(focusId) : null;
    if (f) { try { f.focus({ preventScroll: true }); } catch (e) { /* focus is a convenience */ } }
  }

  function applyMode() {
    const mode = ready() ? "ready" : "setup";
    document.body.classList.toggle("mode-ready", mode === "ready");
    document.body.classList.toggle("mode-setup", mode === "setup");
    const order = NAV[mode];
    document.querySelectorAll("#tabs button").forEach(b => {
      const t = b.getAttribute("data-tab");
      const k = order.indexOf(t);
      b.hidden = k < 0;
      b.style.order = String(k);
      const name = TAB_NAMES[t];
      b.querySelector(".tl").textContent = typeof name === "string" ? name : name[mode];
    });
    const gap = document.querySelector("#tabs .tab-gap");
    if (gap) gap.style.order = String(order.indexOf("gap"));
  }

  function modebar() {
    const bar = clear(document.getElementById("modebar"));
    bar.hidden = false;
    const link = (text, onclick) => h("button", { class: "link", onclick: onclick }, text);
    if (state.editing && state.draft && state.tab !== "setup") {
      bar.className = "modebar edit";
      add(bar, [ico("pencil", "mi"), h("span", null, h("b", { text: "You have unsaved changes to your choices. " }),
        "Your saved choices stay in use until you save. ", link("Continue changing", () => show("setup")), " ", link("Discard the changes", discardChanges))]);
    } else if (desktop) {
      bar.className = "modebar on";
      add(bar, [h("b", { text: "Desktop app. " }), "Live news and the no-repeat history are on."]);
    } else if (ready() && state.tab === "brief" && state.welcome === today()) {
      bar.hidden = true;  // the Setup complete message says the same, just below
    } else if (ready()) {
      bar.className = "modebar ready";
      add(bar, [ico("check", "mi"), h("span", null, h("b", { text: "Your brief is set up. " }), "Your choices are saved in this browser. ",
        state.tab !== "setup" ? link("See or change them", () => show("setup")) : null)]);
    } else {
      bar.className = "modebar";
      add(bar, [h("span", null, h("b", { text: "Setting up. " }), "Your answers stay in this browser, and nothing is collected until you save on the last question. ",
        link("How it works", () => show("help")))]);
    }
  }

  // ------------------------------------------------------------ 1 Setup (interview)
  const INTERVIEW = [
    { title: "What is the brief for?", short: "Purpose", icon: "sparkle", body: stepPurpose },
    { title: "Pick your categories", short: "Topics", icon: "news", body: stepCategories },
    { title: "Your town and weather", short: "Town", icon: "pin", body: stepArea },
    { title: "How much, and how fresh", short: "Amount", icon: "chart", body: stepVolume },
    { title: "What matters to you", short: "Focus", icon: "star", body: stepWatch },
    { title: "A countdown (optional)", short: "Countdown", icon: "calendar", body: stepCountdown },
    { title: "Name your brief", short: "Name", icon: "sunrise", body: stepTitle },
    { title: "Review and save", short: "Review", icon: "shield", body: stepReview }
  ];

  function renderSetup(sec) {
    if (ready() && !state.editing) { renderChoices(sec); return; }
    const editing = ready();
    const i = Math.min(Math.max(state.step || 0, 0), INTERVIEW.length - 1);
    const st = INTERVIEW[i];
    if (editing) {
      add(sec, h("div", { class: "intro edithead" },
        h("div", null, h("p", { class: "kicker", text: "Your choices" }), h("h1", { text: "Change your choices" }),
          h("p", { text: "Your saved choices stay in use until you press Save changes on the last question." })),
        h("button", { class: "btn ghost", onclick: discardChanges }, "Cancel changes")));
    } else if (i === 0) {
      add(sec, h("div", { class: "hero" },
        h("div", { class: "herotext" }, h("p", { class: "kicker", text: "Free, private, no account" }), h("h1", { text: "Your news, every morning, on one page" }),
          h("p", { text: "Answer eight short questions. The Daily Brief remembers your choices in this browser, collects fresh stories from free sources each day, leaves out anything you have already seen, and lays it all out as one clean page with photos and your local forecast." }),
          h("ul", { class: "heroticks" }, h("li", null, ico("news"), "Pick from " + LIB.categories.length + " ready-made categories or type your own"),
            h("li", null, ico("sun"), "A forecast for your town"), h("li", null, ico("shield"), "No sign-up, no tracking, no keys")),
          h("div", { class: "heroactions" }, h("button", { class: "btn onnavy", onclick: showSample }, "See a sample brief"),
            h("span", { class: "herohint", text: "The first question is just below." }))),
        art("hero", "heroart")));
    } else {
      add(sec, h("div", { class: "intro" }, h("h1", { text: "Set up your morning brief" }),
        h("p", { text: "Your answers are kept in this browser as you go. Nothing is collected until you press Save and build my brief on the last question." })));
    }
    const dots = h("ol", { class: "stepper", "aria-label": "Interview progress" });
    INTERVIEW.forEach((s, k) => dots.append(h("li", { class: k === i ? "now" : k < i ? "done" : "" },
      h("button", { onclick: () => { state.step = k; rerender(); }, "aria-label": "Question " + (k + 1) + ": " + s.title, "aria-current": k === i ? "step" : null },
        ico(s.icon), h("span", { class: "sl", text: s.short })))));
    const card = h("div", { class: "card interview" }, h("div", { class: "qhead" }, ico(st.icon, "qi"),
      h("div", null, h("p", { class: "kicker", text: "Question " + (i + 1) + " of " + INTERVIEW.length }), h("h2", { text: st.title }))));
    st.body(card);
    const nav = h("div", { class: "qnav" },
      i > 0 ? h("button", { class: "btn ghost", onclick: () => { state.step = i - 1; rerender(); } }, "Back") : h("span"),
      i < INTERVIEW.length - 1 ? h("button", { class: "btn", onclick: () => { state.step = i + 1; save(); rerender(); } }, "Next question") : null);
    add(sec, [dots, card, nav]);
  }

  function stepPurpose(card) {
    const r = cfg().reader;
    add(card, h("p", { text: "This shapes the Lead Analysis an AI assistant writes. Both answers are optional." }));
    add(card, field("What should the brief help you keep up with or decide this year? One per line.",
      h("textarea", { rows: 4, value: (r.goals || []).join("\n"), placeholder: "Plan a family trip next spring\nKeep up with security patches at work",
        oninput: e => { r.goals = lines(e.target.value); save(); } })));
    add(card, field("Your line of work", h("input", { type: "text", value: r.role || "", placeholder: "Network administrator",
      oninput: e => { r.role = e.target.value; save(); } }), "No names or employers needed."));
  }

  function hasCat(id) { return cfg().categories.some(c => c.id === id); }

  function toggleLibraryCat(id, on) {
    const c = cfg();
    if (on && !hasCat(id)) {
      if (c.categories.length >= E.MAX_CATEGORIES) { toast("Fifteen categories is the limit."); return false; }
      c.categories.push(E.categoryFromLibrary(LIB, id));
    } else if (!on) {
      c.categories = c.categories.filter(x => x.id !== id);
    }
    save();
    return true;
  }

  function stepCategories(card) {
    const c = cfg();
    add(card, h("p", { text: "Start from a pack, type any topic of your own, or tick single categories below. Up to fifteen." }));
    const packs = h("div", { class: "packs" });
    for (const p of LIB.packs) {
      packs.append(h("button", { class: "pack", onclick: () => {
        const custom = c.categories.filter(x => !E.categoryFromLibrary(LIB, x.id));
        const pick = p.categories.map(id => E.categoryFromLibrary(LIB, id));
        const room = Math.max(E.MAX_CATEGORIES - custom.length, 0);
        if (custom.length && !confirm("Replace the library categories with the " + p.name + " pack? Your own " + custom.length +
          " categories are kept" + (pick.length > room ? ", so only " + room + " of the pack's " + pick.length + " categories fit." : "."))) return;
        c.categories = pick.slice(0, room).concat(custom);
        save();
        refresh();
      } }, h("span", { class: "packicons" }, p.categories.slice(0, 4).map(id => { const lc = E.categoryFromLibrary(LIB, id); return ico(lc ? catIcon(lc) : "news"); })),
        h("b", { text: p.name }), h("span", { text: p.description })));
    }
    add(card, [h("h3", { text: "Starter packs" }), packs]);
    add(card, quickAdd(() => refresh()));
    const total = h("h3", { text: "Categories (" + c.categories.length + " of " + E.MAX_CATEGORIES + " chosen)" });
    add(card, total);
    const counts = [];
    const recount = () => {
      total.textContent = "Categories (" + cfg().categories.length + " of " + E.MAX_CATEGORIES + " chosen)";
      counts.forEach(x => { const n = x.list.filter(y => hasCat(y.id)).length; x.el.textContent = n ? n + " of " + x.list.length + " chosen" : x.list.length + " to choose from"; });
    };
    for (const g of LIB.groups) {
      const list = LIB.categories.filter(x => x.group === g.id);
      const chosen = list.filter(x => hasCat(x.id)).length;
      const gcount = h("span", { class: "gcount", text: chosen ? chosen + " of " + list.length + " chosen" : list.length + " to choose from" });
      counts.push({ list: list, el: gcount });
      const box = h("details", { class: "group", "data-key": "group-" + g.id, open: chosen > 0 || g.id === "news" || g.id === "weather" || g.id === "sports" },
        h("summary", null, ico(catIcon(list[0] || {}), "gi"), h("span", { text: g.name }), gcount));
      const grid = h("div", { class: "tiles" });
      for (const lc of list) {
        const id = "lib-" + lc.id;
        const on = hasCat(lc.id);
        const cb = h("input", { type: "checkbox", id: id, class: "sr", checked: on, onchange: e => {
          if (!toggleLibraryCat(lc.id, e.target.checked)) e.target.checked = false;
          e.target.parentNode.classList.toggle("on", e.target.checked);
          recount();
        } });
        grid.append(h("div", { class: "ctile" + (on ? " on" : ""), style: "--c:" + lc.color }, cb,
          h("label", { for: id }, ico(catIcon(lc), "ci"), h("span", { class: "ct" }, h("b", { text: lc.name.replace("({location})", "(your town)") }),
            h("span", { class: "hint", text: lc.description })))));
      }
      box.append(grid);
      add(card, box);
    }
    const custom = c.categories.filter(x => !E.categoryFromLibrary(LIB, x.id));
    if (custom.length) {
      add(card, h("h3", { text: "Your own categories" }));
      add(card, h("ul", { class: "plain" }, custom.map(x => h("li", null, h("b", { text: x.name }), " ",
        h("button", { class: "link", onclick: () => { c.categories = c.categories.filter(y => y !== x); save(); refresh(); } }, "Remove")))));
    }
    add(card, builder(() => refresh()));
  }

  const QUICK_STOP = ["the", "and", "for", "with", "about", "from", "that", "this", "what", "want", "more", "news", "any", "all"];

  function topicWords(text) {
    return String(text || "").toLowerCase().split(/[^a-z0-9+#&]+/).filter(w => w.length >= 3 && QUICK_STOP.indexOf(w) < 0);
  }

  /* Type a topic in plain words. Matching ready-made categories appear as you
     type; Add turns the words themselves into your own category. */
  function quickAdd(done) {
    const input = h("input", { type: "text", id: "topic", placeholder: "For example: electric cars, EVs, charging stations", "aria-label": "A topic to follow" });
    const hits = h("div", { class: "chips", "aria-live": "polite" });
    function suggest() {
      clear(hits);
      const ws = topicWords(input.value);
      if (!ws.length) return;
      const scored = LIB.categories.filter(lc => !hasCat(lc.id)).map(lc => {
        const terms = [].concat.apply([], lc.require || []);
        const hay = " " + topicWords([lc.name, lc.description].concat(lc.queries || [], terms).join(" ")).join(" ") + " ";
        const title = " " + topicWords(lc.name).join(" ") + " ";
        // A word in the category's name counts three times a word in its searches.
        return { lc: lc, n: ws.filter(w => hay.indexOf(" " + w + " ") >= 0).length + 2 * ws.filter(w => title.indexOf(" " + w + " ") >= 0).length };
      }).filter(x => x.n > 0).sort((a, b) => b.n - a.n).slice(0, 4);
      if (!scored.length) return;
      hits.append(h("span", { class: "hint", text: "Ready-made matches:" }));
      scored.forEach(x => {
        const nm = x.lc.name.replace("({location})", "(your town)");
        hits.append(h("button", { class: "chip", onclick: () => { if (toggleLibraryCat(x.lc.id, true)) { toast("Added " + nm + "."); done(); } } }, "+ " + nm));
      });
    }
    function addOwn() {
      const phrases = commas(input.value).map(E.collapse).filter(Boolean);
      if (!phrases.length) { toast("Type a topic first."); input.focus(); return; }
      if (cfg().categories.length >= E.MAX_CATEGORIES) { toast("Fifteen categories is the limit."); return; }
      const first = phrases[0];
      const nm = (first.charAt(0).toUpperCase() + first.slice(1)).slice(0, 70);
      cfg().categories.push({ id: uniqueId(slug(nm)), name: nm, description: "Your own category: " + phrases.join(", ") + ".",
        queries: ["(" + phrases.slice(0, 8).map(q).join(" OR ") + ")"], require: [phrases], exclude: [], feeds: [], items: null });
      save();
      toast("Added " + nm + ". You can fine-tune its searches later, under Your choices.");
      done();
    }
    input.addEventListener("input", suggest);
    input.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); addOwn(); } });
    return h("div", { class: "quickadd" },
      h("h3", { text: "Type what you want to follow" }),
      h("div", { class: "row" }, input, h("button", { class: "btn", onclick: addOwn }, "Add")),
      h("p", { class: "hint", text: "One topic at a time, in your own words; add other names for it after commas. Ready-made categories that match appear as you type." }),
      hits);
  }

  function builder(done) {
    const name = h("input", { type: "text", placeholder: "Amateur radio" });
    const kw = h("input", { type: "text", placeholder: "ham radio, amateur radio, ARRL, FCC license" });
    const must = h("input", { type: "text", placeholder: "Optional" });
    const ex = h("input", { type: "text", placeholder: "Optional: sale, giveaway" });
    const box = h("details", { class: "builder" }, h("summary", { text: "Or build one step by step (searches, must-mention and leave-out words)" }),
      field("Name", name),
      field("What should count? Words or phrases, separated by commas", kw, "These become the news searches."),
      field("Every story must mention at least one of these (commas)", must, "Leave empty to use the words above."),
      field("Leave out stories that mention (commas)", ex),
      h("button", { class: "btn", onclick: () => {
        const nm = E.collapse(name.value);
        const words = commas(kw.value);
        if (!nm || !words.length) { toast("Give the category a name and at least one word or phrase."); return; }
        if (cfg().categories.length >= E.MAX_CATEGORIES) { toast("Fifteen categories is the limit."); return; }
        const req = commas(must.value);
        const queries = ["(" + words.map(q).join(" OR ") + ")"];
        if (req.length) queries.push("(" + req.map(q).join(" OR ") + ") (" + words.slice(0, 4).map(q).join(" OR ") + ")");
        cfg().categories.push({ id: uniqueId(slug(nm)), name: nm.slice(0, 70), description: "Your own category: " + words.join(", ") + ".",
          queries: queries, require: [req.length ? req : words], exclude: commas(ex.value), feeds: [], items: null });
        save();
        toast("Added " + nm + ".");
        done();
      } }, "Add category"));
    return box;
  }

  function stepArea(card) {
    const r = cfg().reader;
    const local = localCats();
    add(card, h("p", { text: local.length ? "Your local categories (" + local.map(c => c.name.replace("({location})", "").trim()).join(", ") + ") search for news about this place." :
      "None of your categories are local, so you can skip this question." }));
    add(card, h("div", { class: "row" },
      field("Town or city", h("input", { type: "text", id: "town", value: r.location || "", placeholder: "Springfield",
        oninput: e => { r.location = e.target.value; save(); } }), "The town name only. No street address."),
      field("State or region", h("input", { type: "text", id: "region", value: r.region || "", placeholder: "Illinois",
        oninput: e => { r.region = e.target.value; save(); } }), "Filled in when you pick your town for the forecast below. In the US, your state also picks the local TV stations whose news this site gathers for you.")));
    add(card, field("Nearby towns or the county that also count as local (commas)", h("input", { type: "text", id: "nearby", value: (r.local_terms || []).join(", "),
      placeholder: "Shelbyville, Sangamon County", oninput: e => { r.local_terms = commas(e.target.value); save(); } }),
      "A story counts as local when it names your town or one of these."));
    add(card, weatherPicker());
    add(card, localFeedBox());
  }

  /* Town news needs a source that names the town. A local TV station or paper
     often has a feed; the Check button says whether this page can read it. */
  function localFeedBox() {
    const r = cfg().reader;
    const box = h("div", { class: "wxpick localfeeds" });
    const status = h("div", { class: "hint", "aria-live": "polite" });
    const ta = h("textarea", { rows: 2, id: "localfeeds", value: (r.local_feeds || []).join("\n"),
      placeholder: "https://www.example-tv.com/news/rss.xml",
      oninput: e => { r.local_feeds = lines(e.target.value).slice(0, 5); save(); } });
    async function check() {
      const urls = lines(ta.value).slice(0, 5);
      clear(status);
      if (!urls.length) { status.textContent = "Paste a feed link first."; return; }
      const terms = [r.location].concat(r.local_terms || []);
      status.textContent = "Checking...";
      const out = [];
      for (const u of urls) {
        if (!E.validUrl(u)) { out.push(h("li", { class: "badtext", text: u + ": not a web link." })); continue; }
        try {
          const got = await C.checkFeed(u, terms);
          out.push(h("li", { class: got.items ? "ok" : "warn", text: E.hostOf(u) + ": readable, " + got.items + " stories, " + got.local + " name your town or a nearby place." }));
        } catch (e) {
          out.push(h("li", { class: "badtext", text: E.hostOf(u) + ": " + (e.message || e) + ". This site does not let web pages read its feed. Your state's local TV stations are still read for you." }));
        }
      }
      clear(status).append(h("ul", { class: "plain" }, out));
    }
    add(box, h("h3", null, ico("news", "hi"), "Your local news feed (optional)"));
    add(box, h("p", { class: "hint", text: "Town news comes from the local TV stations in your state, whose feeds this site gathers on GitHub every four hours, and then from the GDELT news search. To add another source, such as your town's paper, paste up to five feed links, one per line, then press Check; the site has to let web pages read its feed, and many do not." }));
    add(box, ta);
    add(box, h("div", { class: "row" }, h("button", { class: "btn ghost", onclick: check }, "Check")));
    add(box, status);
    return box;
  }

  /* The forecast panel: find the town with Open-Meteo (free, no key), keep only
     its name and rounded map position. */
  function weatherPicker() {
    const w = cfg().weather;
    const box = h("div", { class: "wxpick" });
    const status = h("p", { class: "hint", "aria-live": "polite" });
    const results = h("div", { class: "chips" });
    const town = h("input", { type: "text", value: w.place || cfg().reader.location || "", placeholder: "Springfield", "aria-label": "Town for the forecast" });
    async function find() {
      clear(results);
      status.textContent = "Looking up " + E.collapse(town.value) + "...";
      try {
        const found = await C.geocode(town.value);
        status.textContent = found.length ? "Pick your town:" : "No town by that name. Try the nearest city.";
        found.forEach(f => results.append(h("button", { class: "chip", onclick: () => {
          Object.assign(w, { enabled: true, place: f.label, latitude: f.latitude, longitude: f.longitude });
          const rd = cfg().reader;
          if (!E.collapse(rd.location)) rd.location = f.name;
          // The state tells towns of the same name apart, and the county counts as local.
          if (f.region && E.collapse(rd.location).toLowerCase() === E.collapse(f.name).toLowerCase()) {
            rd.region = f.region;
            const near = (rd.local_terms || []).map(t => E.collapse(t).toLowerCase());
            if (f.county && near.indexOf(f.county.toLowerCase()) < 0) rd.local_terms = (rd.local_terms || []).concat([f.county]);
          }
          // Only the United States and a few others measure in Fahrenheit.
          if (f.country_code && ["US", "LR", "PR", "GU", "BS", "KY", "PW", "FM", "MH"].indexOf(f.country_code) < 0) w.units = "celsius";
          save();
          refresh();
        } }, f.label)));
      } catch (e) { status.textContent = "The town search is not answering right now (" + e.message + "). Try again later."; }
    }
    town.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); find(); } });
    add(box, h("h3", null, ico("sun", "hi"), "Weather forecast"));
    if (w.enabled && E.isNum(w.latitude)) {
      add(box, h("p", { class: "ok", text: "The brief shows the forecast for " + w.place + "." }));
      add(box, h("div", { class: "row" },
        field("Units", select([["fahrenheit", "Fahrenheit"], ["celsius", "Celsius"]], w.units, v => { w.units = v; save(); })),
        h("div", { class: "field" }, h("button", { class: "btn ghost", onclick: () => { w.enabled = false; save(); refresh(); } }, "Turn the forecast off"))));
      add(box, h("p", { class: "hint", text: "To change town, search again." }));
    } else {
      add(box, h("p", { class: "hint", text: "Optional: a four-day forecast at the top of each brief, from Open-Meteo. Only the town name and its rounded map position are kept, in this browser." }));
    }
    add(box, h("div", { class: "row" }, town, h("button", { class: "btn", onclick: find }, "Find my town")));
    add(box, [status, results]);
    return box;
  }

  function stepVolume(card) {
    const b = cfg().brief;
    const nums = (arr, unit) => arr.map(n => [n, n + unit]);
    add(card, field("Stories per category", select(nums([1, 2, 3, 4, 5, 6, 7, 8, 10], ""), b.items_per_category, v => { b.items_per_category = +v; save(); })));
    add(card, field("Fresh means published in the last", select(nums([12, 24, 36, 48, 72], " hours"), b.window_hours, v => {
      b.window_hours = +v;
      if (b.backfill_max_hours < b.window_hours) b.backfill_max_hours = b.window_hours;
      save();
      refresh();
    }), "24 hours keeps the brief new every morning."));
    add(card, field("When a category is short, allow older stories (labelled OLDER) up to",
      select([[b.window_hours, "No older stories"]].concat(nums([48, 72, 96, 120, 168], " hours").filter(x => x[0] > b.window_hours)), b.backfill_max_hours,
        v => { b.backfill_max_hours = +v; save(); })));
    const ref = h("input", { type: "checkbox", id: "allowref", checked: b.allow_reference, onchange: e => { b.allow_reference = e.target.checked; save(); } });
    add(card, h("div", { class: "check" }, ref, h("label", { for: "allowref" }, "Allow undated official pages, labelled REFERENCE, when a category is still short")));
  }

  function stepWatch(card) {
    const b = cfg().brief;
    const r = cfg().reader;
    add(card, h("p", { text: "An AI assistant adds a Lead Analysis at the top: the three stories that matter most to you, a connection between categories, your watch list, and one action. The desktop app collects and sorts the news without an AI, so its briefs skip this part." }));
    const an = h("input", { type: "checkbox", id: "analysis", checked: b.analysis, onchange: e => { b.analysis = e.target.checked; save(); } });
    add(card, h("div", { class: "check" }, an, h("label", { for: "analysis" }, "Ask AI assistants for a Lead Analysis")));
    add(card, field("Watch list: topics that would change a decision you face (one per line)", h("textarea", { rows: 4, value: (r.watch_list || []).join("\n"),
      placeholder: "mortgage rates\nairfare\nsoftware licence changes", oninput: e => { r.watch_list = lines(e.target.value); save(); } })));
    add(card, field("Name of the watch section", h("input", { type: "text", value: b.watch_label, oninput: e => { b.watch_label = e.target.value || "Watch"; save(); } })));
    const st = h("input", { type: "checkbox", id: "starters", checked: b.conversation_starters, onchange: e => { b.conversation_starters = e.target.checked; save(); } });
    add(card, h("div", { class: "check" }, st, h("label", { for: "starters" }, "Add a one-line conversation starter under each story (AI briefs)")));
  }

  function stepCountdown(card) {
    const cd = cfg().countdown;
    const on = h("input", { type: "checkbox", id: "cdon", checked: cd.enabled, onchange: e => { cd.enabled = e.target.checked; save(); refresh(); } });
    add(card, h("p", { text: "A countdown card at the top of the newsletter, with milestones on the way. Good for a move, a launch, a trip or a retirement date." }));
    add(card, h("div", { class: "check" }, on, h("label", { for: "cdon" }, "Show a countdown")));
    if (!cd.enabled) return;
    add(card, field("Label", h("input", { type: "text", value: cd.label, placeholder: "Days to the spring trip", oninput: e => { cd.label = e.target.value; save(); } })));
    add(card, field("Target date", h("input", { type: "date", value: cd.date, oninput: e => { cd.date = e.target.value; save(); } })));
    add(card, field("Count from (optional, draws a progress bar)", h("input", { type: "date", value: cd.start, oninput: e => { cd.start = e.target.value; save(); } })));
    add(card, h("h3", { text: "Milestones" }));
    const list = h("div", { class: "milestones" });
    (cd.milestones || []).forEach((m, i) => {
      list.append(h("div", { class: "mrow" },
        h("input", { type: "date", value: m.date, "aria-label": "Milestone date", oninput: e => { m.date = e.target.value; save(); } }),
        h("input", { type: "text", value: m.label, placeholder: "What happens", "aria-label": "Milestone", oninput: e => { m.label = e.target.value; save(); } }),
        h("input", { type: "text", value: m.note || "", placeholder: "Note (optional)", "aria-label": "Milestone note", oninput: e => { m.note = e.target.value; save(); } }),
        h("button", { class: "link", onclick: () => { cd.milestones.splice(i, 1); save(); refresh(); } }, "Remove")));
    });
    add(card, [list, h("button", { class: "btn ghost", onclick: () => { cd.milestones = cd.milestones || []; cd.milestones.push({ date: "", label: "", note: "" }); save(); refresh(); } }, "Add a milestone")]);
  }

  function stepTitle(card) {
    const b = cfg().brief;
    const preview = h("p", { class: "hint" });
    const upd = () => { preview.textContent = "Example: " + N.subjectLine({ date: today(), title: b.title, categories: [] }, cfg()); };
    add(card, field("Title at the top of the page", h("input", { type: "text", value: b.title, oninput: e => { b.title = e.target.value; save(); upd(); } })));
    add(card, field("Page title (the browser tab and the saved file)", h("input", { type: "text", value: b.subject, oninput: e => { b.subject = e.target.value; save(); upd(); } }),
      "{total} is the story count, {date} the date, {title} the title, {empty} the number of empty categories."));
    add(card, preview);
    upd();
    const dv = cfg().delivery;
    add(card, h("details", { class: "more" }, h("summary", { text: "Only if you also run a GitHub copy: its delivery time" }),
      h("div", { class: "row" },
        field("Delivery time", h("input", { type: "time", value: dv.time, oninput: e => { dv.time = e.target.value; save(); } }),
          "When your GitHub copy posts it."),
        field("Time zone", h("input", { type: "text", list: "zones", value: dv.timezone, placeholder: "America/New_York",
          oninput: e => { dv.timezone = E.collapse(e.target.value); save(); } }), "Your browser says " + (browserZone() || "nothing") + ".")),
      h("datalist", { id: "zones" }, ZONES.map(z => h("option", { value: z }))),
      h("p", { class: "hint", text: "This page needs no schedule: open it and press Get today's brief. A GitHub copy is optional; it posts the brief as an issue each morning (the Every day tab explains it)." })));
  }

  function localCats() {
    return cfg().categories.filter(c => c.needs_location || JSON.stringify(c).indexOf("{location}") >= 0 || JSON.stringify(c).indexOf("{local_terms}") >= 0);
  }

  /* One summary for the last question and for the Your choices page: label,
     value, and the question that changes it. */
  function summaryRows(c) {
    const n = E.normalizeConfig(c);
    return [
      ["Categories", n.categories.map(x => E.resolveCategory(x, n.reader).name).join(", ") || "none", 1],
      ["Your area", [n.reader.location, n.reader.region].map(E.collapse).filter(Boolean).join(", ") || "not set", 2],
      ["Also local", (n.reader.local_terms || []).join(", ") || "none", 2],
      ["Local news feeds", (n.reader.local_feeds || []).map(E.hostOf).join(", ") || "none", 2],
      ["Weather", n.weather.enabled ? "forecast for " + n.weather.place + " (" + n.weather.units + ")" : "off", 2],
      ["Stories per category", String(n.brief.items_per_category), 3],
      ["Fresh window", n.brief.window_hours + " hours", 3],
      ["Older stories", n.brief.backfill_max_hours > n.brief.window_hours ? "up to " + n.brief.backfill_max_hours + " hours, labelled OLDER" : "off", 3],
      ["Reference pages", n.brief.allow_reference ? "allowed, labelled REFERENCE" : "off", 3],
      ["Watch list", (n.reader.watch_list || []).join(", ") || "empty", 4],
      ["Countdown", n.countdown.enabled ? n.countdown.label + " on " + n.countdown.date : "off", 5],
      ["Brief name", E.collapse(n.brief.title) || "Daily Brief", 6],
      ["What it is for", (n.reader.goals || []).join("; ") || "not set", 0]
    ];
  }

  function summaryTable(c, onChange) {
    return h("table", { class: "summary choices" }, h("tbody", null, summaryRows(c).map(r => h("tr", null, h("th", { text: r[0] }), h("td", { text: r[1] }),
      h("td", { class: "chg" }, h("button", { class: "link", "aria-label": "Change: " + r[0], onclick: () => onChange(r[2]) }, "Change"))))));
  }

  function stepReview(card) {
    const v = E.validateConfig(cfg());
    add(card, msgList(v));
    if (localCats().length && !E.collapse(cfg().reader.location)) {
      add(card, h("div", { class: "actions" },
        h("button", { class: "btn ghost", onclick: () => { state.step = 2; rerender(); } }, "Add my town"),
        h("button", { class: "btn ghost", onclick: () => {
          const drop = localCats();
          cfg().categories = cfg().categories.filter(c => drop.indexOf(c) < 0);
          save();
          refresh();
        } }, "Remove the local categories")));
    }
    add(card, summaryTable(cfg(), k => { state.step = k; save(); rerender(); }));
    if (ready()) {
      add(card, h("div", { class: "finish" },
        h("p", null, h("b", { text: "Save to use these choices. " }), "They replace your saved choices, and your next brief uses them."),
        h("div", { class: "actions" },
          h("button", { class: "btn big", disabled: v.errors.length > 0, onclick: saveChanges }, "Save changes"),
          h("button", { class: "btn ghost", onclick: discardChanges }, "Cancel changes"))));
    } else {
      add(card, h("div", { class: "finish" },
        h("p", null, h("b", { text: "This finishes setup. " }), "Your choices are saved in this browser, today's brief is built straight away, and from then on the app opens on your brief."),
        h("div", { class: "actions" },
          h("button", { class: "btn big", disabled: v.errors.length > 0, onclick: finishSetup }, "Save and build my brief"),
          h("button", { class: "btn ghost", onclick: downloadSettings }, "Download settings file"))));
    }
  }

  function finishSetup() {
    if (E.validateConfig(saved()).errors.length) return;
    state.setup_done = true;
    state.setup_saved = today();
    state.welcome = today();
    state.step = 0;
    save();
    show("brief");
    getToday(true);
  }

  function startEditing(step) {
    state.editing = true;
    state.draft = E.clone(state.config);
    state.step = step || 0;
    save();
    show("setup");
  }

  function saveChanges() {
    if (!state.draft) { state.editing = false; show("setup"); return; }
    if (E.validateConfig(state.draft).errors.length) { toast("Fix the problems listed first."); return; }
    const changed = JSON.stringify(state.draft) !== JSON.stringify(state.config);
    state.config = state.draft;
    state.draft = null;
    state.editing = false;
    state.step = 0;
    save();
    show("brief");
    toast(changed ? "Changes saved. Your next brief uses them." : "Saved. Nothing had changed.");
  }

  function discardChanges() {
    state.draft = null;
    state.editing = false;
    state.step = 0;
    save();
    show("setup");
    toast("Changes discarded. Your saved choices are as they were.");
  }

  function showSample() {
    S.openPage(N.render(E.clone(SAMPLE.brief), SAMPLE.settings).html);
  }

  // ------------------------------------------------------------ Your choices (after setup)
  function renderChoices(sec) {
    const c = saved();
    const v = E.validateConfig(c);
    add(sec, h("div", { class: "intro choicehead" },
      h("div", null, h("p", { class: "kicker", text: state.setup_saved ? "Set up on " + N.prettyDate(state.setup_saved) : "Set up" }),
        h("h1", { text: "Your choices" }),
        h("p", { text: "Saved in this browser. Every brief uses them until you change them." })),
      h("span", { class: "pill good" }, ico("check"), "Saved")));
    if (v.errors.length) add(sec, h("div", { class: "card" }, msgList(v)));
    add(sec, h("div", { class: "card" },
      summaryTable(c, k => startEditing(k)),
      h("div", { class: "actions" },
        h("button", { class: "btn", onclick: () => startEditing(0) }, ico("pencil"), " Change my answers"),
        h("button", { class: "btn ghost", onclick: () => show("categories") }, "Fine-tune categories"),
        h("button", { class: "btn ghost", onclick: () => show("brief") }, "Go to today's brief"))));
  }

  // ------------------------------------------------------------ 2 Categories
  function renderCategories(sec) {
    const c = cfg();
    add(sec, h("div", { class: "intro" }, h("button", { class: "link back", onclick: () => show("setup") }, "Back to your choices"),
      h("h1", { text: "Fine-tune your categories" }),
      h("p", { text: "Each category is a desk in the newsletter. Open one to change its searches and filters. A story must mention at least one term from every \"must mention\" line, and none of the \"leave out\" terms. Changes here are saved as you make them and apply to your next brief." })));
    const msgs = h("div", { id: "catmsgs" });
    const refresh = () => { clear(msgs).append(msgList(E.validateConfig(c))); };
    add(sec, msgs);
    refresh();
    c.categories.forEach((cat, i) => add(sec, categoryCard(cat, i, refresh)));
    const pick = h("select", { "aria-label": "Category from the library" }, h("option", { value: "", text: "Choose from the library" }));
    for (const g of LIB.groups) {
      const og = h("optgroup", { label: g.name });
      LIB.categories.filter(x => x.group === g.id && !hasCat(x.id)).forEach(x => og.append(h("option", { value: x.id, text: x.name.replace("({location})", "(your town)") })));
      if (og.children.length) pick.append(og);
    }
    add(sec, h("div", { class: "card" }, h("h2", { text: "Add a category" }),
      quickAdd(() => refresh()),
      h("h3", { text: "Or choose from the library" }),
      h("div", { class: "row" }, pick, h("button", { class: "btn", onclick: () => { if (pick.value && toggleLibraryCat(pick.value, true)) refresh(); } }, "Add")),
      builder(() => refresh())));
  }

  function categoryCard(cat, i, refresh) {
    const c = cfg();
    const changed = () => { save(); refresh(); };
    const move = d => { const j = i + d; if (j < 0 || j >= c.categories.length) return; c.categories.splice(i, 1); c.categories.splice(j, 0, cat); save(); refresh(); };
    const color = h("input", { type: "color", value: /^#[0-9a-f]{6}$/i.test(cat.color || "") ? cat.color : E.PALETTE[i % E.PALETTE.length], "aria-label": "Colour",
      oninput: e => { cat.color = e.target.value; changed(); } });
    const name = h("input", { type: "text", class: "catname", value: cat.name, "aria-label": "Category name", oninput: e => { cat.name = e.target.value; changed(); } });
    const groupsText = (cat.require || []).map(g => g.join(", ")).join("\n");
    const body = h("div", { class: "catbody" },
      field("What it covers", h("input", { type: "text", value: cat.description || "", oninput: e => { cat.description = e.target.value; changed(); } })),
      field("Searches, one per line", h("textarea", { rows: 3, value: (cat.queries || []).join("\n"), oninput: e => { cat.queries = lines(e.target.value); changed(); } }),
        "Write them like a news search: OR between choices, quotes around phrases."),
      field("Must mention: one line per group, terms separated by commas", h("textarea", { rows: 3, value: groupsText,
        oninput: e => { cat.require = lines(e.target.value).map(commas).filter(g => g.length); changed(); } }),
        "Short all-capital terms such as AI or CVE match only in capitals."),
      field("Leave out stories that mention (commas)", h("input", { type: "text", value: (cat.exclude || []).join(", "), oninput: e => { cat.exclude = commas(e.target.value); changed(); } })),
      field("Publisher feeds, one link per line", h("textarea", { rows: 2, value: (cat.feeds || []).join("\n"), oninput: e => { cat.feeds = lines(e.target.value); changed(); } }),
        "Their stories still need a must-mention term. This web page can read only feeds that allow it."),
      field("On-topic feeds, one link per line", h("textarea", { rows: 2, value: (cat.topic_feeds || []).join("\n"), oninput: e => { cat.topic_feeds = lines(e.target.value); changed(); } }),
        "Feeds about this topic and nothing else, such as a tennis feed for a tennis category. Their stories count as on topic without a must-mention term."),
      field("Stories in this category", select([["", "Use the default"]].concat([1, 2, 3, 4, 5, 6, 7, 8, 10].map(n => [n, String(n)])), cat.items || "",
        v => { cat.items = v ? +v : null; changed(); })),
      h("div", { class: "check" }, h("input", { type: "checkbox", id: "lst" + i, checked: !!cat.skip_listicles, onchange: e => { cat.skip_listicles = e.target.checked; changed(); } }),
        h("label", { for: "lst" + i }, "Skip \"top 10\" and \"best of\" list articles")));
    return h("div", { class: "card cat", style: "border-left-color:" + color.value },
      h("div", { class: "cathead" }, h("span", { class: "tag", style: "background:" + color.value, text: "T" + (i + 1) }), color, name,
        h("button", { class: "icon", "aria-label": "Move up", disabled: i === 0, onclick: () => move(-1) }, "\u2191"),
        h("button", { class: "icon", "aria-label": "Move down", disabled: i === c.categories.length - 1, onclick: () => move(1) }, "\u2193"),
        h("button", { class: "link", onclick: () => { if (confirm("Remove " + cat.name + "?")) { c.categories.splice(i, 1); save(); refresh(); } } }, "Remove")),
      h("details", { "data-key": "cat-" + cat.id }, h("summary", { text: "Searches and filters" }), body));
  }

  // ------------------------------------------------------------ 3 Today
  function renderBrief(sec) {
    const v = E.validateConfig(saved());
    const running = !!job || !!webRun;
    const fresh = isFresh();
    if (state.welcome === today()) add(sec, welcomeCard());
    add(sec, h("div", { class: "intro todayhead" },
      h("div", null, h("p", { class: "kicker", text: N.prettyDate(today()) }), h("h1", { text: "Today's brief" }), statusLine(running, fresh)),
      ico("sunrise", "bigico")));
    if (v.errors.length) {
      add(sec, h("div", { class: "card" }, h("p", { text: "Your choices need a fix before a brief can be built." }), msgList(v),
        h("button", { class: "btn", onclick: () => startEditing(INTERVIEW.length - 1) }, "Fix my choices")));
    }
    if (!running && staleChoices()) {
      add(sec, h("div", { class: "card notice" }, ico("pencil", "ni"),
        h("div", { class: "grow" }, h("b", { text: "Your choices changed after this brief was built." }),
          h("p", { class: "hint", text: "Build a new brief to use them. Stories you have already seen stay out." })),
        h("button", { class: "btn", onclick: () => getToday(true) }, "Rebuild with my new choices")));
    }
    add(sec, running ? buildCard() : runCard(fresh, v));
    if (running) paintProgress();
    if (state.brief) add(sec, briefView());
    if (!desktop) {
      add(sec, h("details", { class: "card more" }, h("summary", { text: "Other ways to fill the page: an AI assistant, or the sample" }),
        h("p", { text: "An AI assistant (Claude, ChatGPT, Gemini or Grok) can write the brief with a Lead Analysis from a web search: get the prompt on the AI assistants tab, type JSON after the brief, and paste the reply here." }),
        pasteBox(h("button", { class: "btn ghost", onclick: () => setBrief(E.clone(SAMPLE.brief), null) }, "Show the sample brief"))));
    }
  }

  function isFresh() { return !!(state.brief && state.brief.date === today() && state.brief.source !== "sample"); }

  function timeOf(iso) {
    const ms = E.parseIso(iso);
    if (ms === null) return "";
    try { return new Date(ms).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }); } catch (e) { return ""; }
  }

  /* One line under the heading that says where today's brief stands. */
  function statusLine(running, fresh) {
    if (running) return h("p", { class: "status busy", id: "status" }, h("span", { class: "dot" }), "Building now");
    if (fresh) {
      const t = timeOf(state.brief.generated_at);
      const n = N.stats(state.brief).total;
      const old = state.brief_version && state.brief_version !== E.VERSION;
      return h("p", { class: "status good", id: "status" }, ico("check"), "Ready" + (t ? ", built at " + t : "") + ". " + n + (n === 1 ? " story." : " stories.") +
        (old ? " Built by version " + state.brief_version + "; check again to use " + E.VERSION + "." : ""));
    }
    if (state.brief && state.brief.source === "sample") return h("p", { class: "status idle", id: "status" }, "Not built yet today. Showing the sample brief.");
    if (state.brief) return h("p", { class: "status idle", id: "status" }, "Not built yet today. The page below is from " + N.prettyDate(state.brief.date) + ".");
    return h("p", { class: "status idle", id: "status" }, "Not built yet today.");
  }

  function welcomeCard() {
    const n = E.normalizeConfig(saved());
    const bits = [n.categories.length + " categories", n.brief.items_per_category + " stories each", "a " + n.brief.window_hours + "-hour window"];
    if (n.weather.enabled) bits.push("the forecast for " + n.weather.place);
    return h("div", { class: "card welcome", role: "status" }, ico("check", "wi"),
      h("div", { class: "grow" }, h("h2", { text: "Setup complete" }),
        h("p", { text: "Your choices are saved in this browser: " + bits.join(", ") + ". From now on the app opens here, on your brief." }),
        h("div", { class: "row" },
          h("button", { class: "link", onclick: () => show("setup") }, "See your choices"),
          h("button", { class: "link", onclick: () => { state.welcome = ""; save(); refresh(); } }, "Hide this message"))));
  }

  function runCard(fresh, v) {
    const useHist = h("input", { type: "checkbox", id: "usehist", checked: true });
    const go = h("button", { class: "btn big", id: "go", disabled: v.errors.length > 0, onclick: () => getToday(useHist.checked) },
      fresh ? "Check for newer stories" : "Get today's brief");
    const auto = h("input", { type: "checkbox", id: "autorun", checked: !!state.auto_run, onchange: e => { state.auto_run = e.target.checked; save(); } });
    const what = fresh ? "Today's brief is below. Check again later for stories published since; anything you have already seen stays out."
      : desktop ? "Searches Google News and the publisher feeds for every category, keeps fresh, on-topic stories, and leaves out anything you have already seen. About a minute."
        : "Collects fresh stories for your " + saved().categories.length + " categories from free news sources, right in this browser, and leaves out anything you have already seen. About a minute; the page stays usable.";
    return h("div", { class: "card runcard" + (fresh ? " quiet" : "") },
      h("p", { text: what }),
      h("div", { class: "row" }, go,
        h("div", { class: "check" }, useHist, h("label", { for: "usehist" }, "Leave out stories I have already seen"))),
      h("div", { class: "check" }, auto, h("label", { for: "autorun" }, h("b", { text: "Build it automatically when I open this page" }),
        h("span", { class: "hint", text: "Once a day. Your choices are saved in this browser, so bookmarking this page is all a daily routine needs." }))));
  }

  /* While a brief is being built, the run card becomes a panel that names each stage. */
  const STAGES = [
    ["choices", "Your choices", "Saved in this browser"],
    ["feeds", "Publisher feeds", "Reading the news sites' own feeds"],
    ["backup", "Backup collection", "Stories this site gathers on GitHub every four hours"],
    ["local", "Local stations", "Your state's local TV news, gathered on GitHub every four hours"],
    ["search", "News search", "Searching the news index for whatever is still short"],
    ["layout", "Your page", "Picking the freshest stories and laying out the page"]
  ];
  const DESKTOP_STAGES = [
    ["choices", "Your choices", "Saved in this browser"],
    ["sources", "News sources", "Google News and the publisher feeds"],
    ["layout", "Your page", "Picking the freshest stories and laying out the page"]
  ];

  function buildCard() {
    return h("div", { class: "card buildcard" }, h("h2", null, ico("sunrise", "hi"), "Building today's brief"),
      h("div", { id: "progress", role: "status", "aria-live": "polite" }));
  }

  function pasteBox(extra) {
    const ta = h("textarea", { rows: 5, placeholder: "Paste the whole reply from your AI assistant here. The app finds the brief JSON in it." });
    return h("div", { class: "pastebox" }, ta,
      h("div", { class: "actions" }, h("button", { class: "btn", onclick: () => pasteBrief(ta.value) }, "Show the pasted brief"), extra || null));
  }

  /* One button for every mode: the desktop app collects on this computer, the
     web version collects in the browser. */
  function getToday(useHistory) {
    if (desktop) return runDesktop(useHistory !== false);
    return runWeb(useHistory !== false);
  }

  /* A tab left open across a release keeps running the code it loaded. Before a brief,
     and when the page comes back into view, ask the site which version it serves (sw.js
     names it). When it is newer, reload once for that version, and carry on with the
     brief after the reload, so every brief uses the published code. */
  const VERSION_CHECK = location.protocol === "https:" || window.DB_VERSION_CHECK === true;
  async function siteVersion() {
    try {
      const r = await fetch("sw.js", { cache: "no-store", credentials: "same-origin" });
      const m = r.ok ? /VERSION = "db-v([^"]+)"/.exec(await r.text()) : null;
      return m ? m[1] : "";
    } catch (e) { return ""; }
  }
  async function reloadForNewVersion(next) {
    if (!VERSION_CHECK || desktop) return false;
    const v = await siteVersion();
    if (!v || v === E.VERSION) return false;
    try {
      if (sessionStorage.getItem("db.reloaded_for") === v) return false;  // already tried once; never loop
      sessionStorage.setItem("db.reloaded_for", v);
      sessionStorage.setItem("db.after_reload", next || "");
    } catch (e) { return false; }
    location.reload();
    return true;
  }

  async function runWeb(useHistory) {
    if (webRun) return;
    const v = E.validateConfig(saved());
    if (v.errors.length) { toast("Fix your choices first."); return; }
    if (!C) { toast("The collector did not load. Reload the page."); return; }
    if (await reloadForNewVersion(useHistory ? "run" : "run-all")) return;
    webRun = { state: "running", done: 0, total: 0, step: "", phase: "feeds", cancelled: false };
    if (state.tab === "brief") refresh();
    const ledger = useHistory ? history : null;
    try {
      const r = await C.runBrief(E.clone(saved()), ledger, {
        progress: (label, done, total, phase) => {
          if (!webRun) return;
          webRun.step = label;
          webRun.done = done;
          webRun.total = total;
          if (phase) webRun.phase = phase;
          paintProgress();
        },
        cancelled: () => !!(webRun && webRun.cancelled)
      });
      webRun = null;
      // Everything shown counts as seen, so tomorrow's brief has only new stories.
      if (r.brief.total) { history = E.ledgerAdd(history, r.brief, true); saveHistory(); }
      setBrief(r.brief, r.health);
      toast(r.brief.total ? r.brief.total + " stories collected." : "Nothing new right now. Try again later in the day.");
    } catch (e) {
      const was = webRun && webRun.cancelled;
      webRun = null;
      refresh();
      toast(was ? "Stopped." : "The collection failed: " + e.message);
    }
  }

  function pasteBrief(text) {
    const obj = E.extractJson(text);
    if (!obj) { toast("No JSON found. Ask the assistant for the JSON version of the brief."); return; }
    if (Array.isArray(obj.categories) && obj.categories.length && obj.categories[0].queries && !obj.categories[0].items) {
      if (confirm("This looks like settings, not a brief. Use these settings?")) importSettings(obj);
      return;
    }
    // A pasted brief always comes from an assistant, and its ages come from the publication times.
    obj.source = "ai";
    for (const cat of Array.isArray(obj.categories) ? obj.categories : []) {
      for (const it of cat && Array.isArray(cat.items) ? cat.items : []) if (it && typeof it === "object") delete it.age_hours;
    }
    const before = E.checkBrief(obj, saved());
    if (before.errors.length && !confirm("This brief has " + before.errors.length + " problem(s), listed under the preview. Show it anyway?")) return;
    const f = E.filterSeen(obj, history);
    setBrief(f.brief, null, true);
    if (f.withheld) toast(f.withheld + " stories were left out because you have already seen them.");
  }

  /* A short fingerprint of the choices a brief was built with, so the page can say
     when the choices changed afterwards. */
  function sig(c) {
    const s = JSON.stringify([c.categories, c.brief, c.reader, c.weather, c.countdown]);
    let x = 5381;
    for (let i = 0; i < s.length; i++) x = ((x * 33) ^ s.charCodeAt(i)) >>> 0;
    return x.toString(36);
  }

  function staleChoices() { return !!(state.brief && state.brief_sig && state.brief_sig !== sig(saved())); }

  function setBrief(brief, health, goToBrief) {
    state.brief = brief;
    state.health = health;
    state.brief_sig = brief && brief.source !== "sample" && brief.source !== "ai" ? sig(saved()) : "";
    state.brief_version = state.brief_sig ? E.VERSION : "";  // the version that collected it
    save();
    if (goToBrief && ready() && state.tab !== "brief") show("brief"); else rerender();
    // Just after setup, the welcome message stays in view; later runs jump to the page.
    const v = document.getElementById("briefview");
    if (v && state.welcome !== today()) v.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function rendered() {
    const isSample = state.brief && state.brief.source === "sample";
    return N.render(state.brief, isSample ? SAMPLE.settings : saved());
  }

  function briefView() {
    const out = rendered();
    const chk = E.checkBrief(state.brief, state.brief.source === "sample" ? SAMPLE.settings : saved());
    // No scripts may run in the page; same-origin only lets this app measure its height.
    const frame = h("iframe", { class: "page", title: "Today's brief", sandbox: "allow-same-origin allow-popups allow-popups-to-escape-sandbox" });
    frame.srcdoc = out.html.replace("<head>", "<head><base target=\"_blank\">");
    const fit = () => { try { const d = frame.contentDocument; if (d && d.documentElement) frame.style.height = d.documentElement.scrollHeight + "px"; } catch (e) { /* keep the default height */ } };
    frame.addEventListener("load", () => {
      fit();
      try { new ResizeObserver(fit).observe(frame.contentDocument.body); } catch (e) { setTimeout(fit, 1500); }
    });
    const st = N.stats(state.brief);
    const box = h("div", { class: "card", id: "briefview" },
      h("h2", { text: out.subject }),
      h("p", { class: "hint", text: st.total + " stories, " + st.news + " fresh, " + st.empty.length + " empty categories." }),
      h("div", { class: "actions" },
        h("button", { class: "btn", onclick: () => S.openPage(out.html) }, "Open as a full page"),
        h("button", { class: "btn ghost", onclick: () => S.download(fileStem() + ".html", out.html, "text/html") }, "Download page"),
        h("button", { class: "btn ghost", onclick: async () => {
          const how = await S.copyRich(out.html, out.text);
          toast(how === "rich" ? "Copied. Paste it where you want it." : how === "text"
            ? "Copied as plain text; this browser cannot copy the formatted version. Download page keeps the layout."
            : "This browser blocked copying. Use Download page.");
        } }, "Copy newsletter"),
        state.brief.source !== "sample" && state.brief.source !== "web" ? h("button", { class: "btn ghost", onclick: markRead }, "Mark as read") : null),
      chk.errors.length || chk.warnings.length ? h("details", { class: "checks" }, h("summary", { text: "Checks: " + chk.errors.length + " problem(s), " + chk.warnings.length + " note(s)" }), msgList(chk)) : null,
      frame,
      state.health ? healthView(state.health) : null);
    return box;
  }

  function fileStem() { return "daily-brief-" + (state.brief && state.brief.date ? state.brief.date : today()); }

  async function markRead() {
    if (desktop) {
      try {
        const r = await S.api("/api/commit", { brief: state.brief, config: saved() });
        desktop.ledger_size = r.ledger_size;
        toast("Marked as read. These stories will not come back.");
      } catch (e) { toast(e.message); }
      return;
    }
    history = E.ledgerAdd(history, state.brief, false);
    saveHistory();
    toast("Marked as read. Pasted briefs will leave these stories out from now on.");
  }

  async function runDesktop(useHistory) {
    try {
      const r = await S.api("/api/run", { config: saved(), use_history: useHistory });
      if (r.already_running) toast("A collection was already running, so this shows that one. Run again when it finishes to use new settings.");
      job = { id: r.job, state: "running", done: 0, total: 0, step: "Starting" };
      refresh();
      pollJob();
    } catch (e) { toast(e.message); }
  }

  async function pollJob() {
    if (!job) return;
    try {
      const j = await S.api("/api/run/" + job.id);
      job = j;
      if (j.state === "running") { paintProgress(); setTimeout(pollJob, 900); return; }
      job = null;
      if (j.state === "error") { toast("The run failed: " + j.error); rerender(); return; }
      setBrief(j.brief, j.health);
    } catch (e) { job = null; toast(e.message); rerender(); }
  }

  function paintProgress() {
    const p = document.getElementById("progress");
    const run = job || webRun;
    if (!p || !run) return;
    const stages = job ? DESKTOP_STAGES : STAGES;
    const phase = job ? "sources" : (run.phase || "feeds");
    const at = Math.max(1, stages.findIndex(s => s[0] === phase));
    const pct = phase === "layout" ? 100 : run.total ? Math.round(100 * run.done / run.total) : 3;
    const detail = run.step && phase !== "layout" && run.total ? run.step + ": " + run.done + " of " + run.total + " sources checked" : "";
    clear(p).append(
      h("ol", { class: "stages" }, stages.map((s, k) => h("li", { class: k < at ? "done" : k === at ? "now" : "" },
        h("span", { class: "sm" }, k < at ? ico("check") : h("span", { text: String(k + 1) })),
        h("span", null, h("b", { text: s[1] }), h("span", { class: "hint", text: k === at && detail ? detail : s[2] }))))),
      h("div", { class: "bar" }, h("div", { class: "fill", style: "width:" + pct + "%" })),
      h("div", { class: "row spread" }, h("p", { class: "hint", text: "About a minute. You can keep using the page." }),
        webRun ? h("button", { class: "link", onclick: () => { if (webRun) webRun.cancelled = true; } }, "Stop") : null));
  }

  function healthView(health) {
    const rows = [];
    for (const cat of state.brief.categories || []) {
      const hh = health[cat.id];
      if (!hh) continue;
      const errs = hh.queries.concat(hh.feeds).filter(x => x.error);
      // A missing backup file matters only on the published site; a downloaded copy never has one.
      if (hh.backup && hh.backup.error && location.protocol === "https:") errs.push({ url: "backup collection", error: hh.backup.error });
      if (hh.local && hh.local.error && location.protocol === "https:") errs.push({ url: "local stations (" + hh.local.state + ")", error: hh.local.error });
      const rej = Object.keys(cat.rejected || {}).map(k => k + " " + cat.rejected[k]).join(", ");
      const found = hh.queries.reduce((a, x) => a + x.items, 0) + " search results, " + hh.feeds.reduce((a, x) => a + x.items, 0) + " feed items" +
        (hh.backup && hh.backup.items ? ", " + hh.backup.items + " from the backup collection" : "") +
        (hh.local && hh.local.items ? ", " + hh.local.items + " from local stations naming your area" : "");
      rows.push(h("tr", null, h("th", { text: cat.name }), h("td", { text: found }),
        h("td", { text: rej || "none" }), h("td", { class: errs.length ? "badtext" : "", text: errs.length ? errs.map(x => (x.query || x.url) + ": " + x.error).join("; ") : "none" })));
    }
    if (health._weather) rows.push(h("tr", null, h("th", { text: "Weather" }), h("td", { text: "forecast" }), h("td", { text: "" }), h("td", { class: "badtext", text: health._weather.error })));
    return h("details", { class: "checks" }, h("summary", { text: "Sources and filters" }),
      h("table", { class: "summary" }, h("thead", null, h("tr", null, h("th", { text: "Category" }), h("th", { text: "Found" }), h("th", { text: "Left out" }), h("th", { text: "Source problems" }))),
        h("tbody", null, rows)));
  }

  // ------------------------------------------------------------ 4 Every day
  function cloudCard() {
    const proj = S.projectUrl();
    const d = E.normalizeConfig(cfg()).delivery;
    const lines = E.cronLines(d.time, d.timezone, new Date().getFullYear());
    const cronText = lines.map(l => "    - cron: \"" + l + "\"").join("\n");
    const link = (href, text) => href ? h("a", { href: href, target: "_blank", rel: "noopener", text: text }) : h("b", { text: text });
    return h("details", { class: "card more", id: "cloud" }, h("summary", null, ico("cloud", "hi"), "Optional: have GitHub post it each morning, even with no browser open"),
      h("p", { text: "GitHub's servers collect the news, build the newsletter and deliver it, with no computer of yours switched on. It uses free services only: Google News RSS and publisher feeds need no keys, and no AI or search service is involved." }),
      h("ol", { class: "ways" },
        h("li", null, h("b", { text: "Make your own private copy. " }), link(proj ? proj + "/generate" : "", "Use this template"),
          ", choose Private, and create the repository."),
        h("li", null, h("b", { text: "Add your settings. " }), h("button", { class: "link", onclick: downloadSettings }, "Download the settings file"),
          ", then in your copy choose Add file, Upload files, drop daily-brief-settings.json in, and commit. Upload it again after you change something here."),
        h("li", null, h("b", { text: "Nothing to add for delivery. " }), "Each morning the brief appears as an issue in your copy, mentioning you, and yesterday's issue closes. GitHub tells you about it by email or in its mobile app, following your notification settings (Settings, Notifications). No password or secret is stored."),
        h("li", null, h("b", { text: "Set the time. " }), lines.length ? [
          "In your copy open .github/workflows/daily-brief.yml, choose Edit, and replace the two cron lines with these (they put the brief out at " + d.time + " " + d.timezone + " in summer and winter):",
          h("pre", { class: "code", text: cronText }),
          h("button", { class: "link", onclick: async () => toast(await S.copyText(cronText) ? "Copied." : "Copy blocked.") }, "Copy the lines")
        ] : "Choose a delivery time and time zone on Setup question 7 first."),
        h("li", null, h("b", { text: "Test it. " }), "Open the Actions tab, choose Daily brief, then Run workflow. A run takes a minute or two; the summary shows what was sent.")),
      h("p", { class: "hint", text: "GitHub Actions is free for public repositories; a private copy uses your plan's included minutes, about three a day. Keep your copy private: in a public one, anyone can read your settings and run logs, and GitHub turns scheduled runs off after 60 days without activity. Times are best kept off the top of the hour, when GitHub delays runs." }));
  }

  function renderDaily(sec) {
    add(sec, h("div", { class: "intro" }, h("h1", { text: "Make it a daily habit" }),
      h("p", { text: "Your choices are already saved in this browser. Here is how to get a fresh brief every day." })));
    const auto = h("input", { type: "checkbox", id: "autorun2", checked: !!state.auto_run, onchange: e => { state.auto_run = e.target.checked; save(); } });
    add(sec, h("div", { class: "card" }, h("h2", null, ico("sunrise", "hi"), "Every morning, in this browser"),
      h("ol", { class: "ways" },
        h("li", null, h("b", { text: "Keep this page handy. " }), "Bookmark it, or add it to your home screen: on a phone, use Share, then Add to Home Screen; in Chrome or Edge on a computer, use the install button in the address bar. It then opens like an app."),
        h("li", null, h("b", { text: "Let it build by itself. " }), h("span", { class: "check inline" }, auto, h("label", { for: "autorun2", text: "Build it automatically when I open this page (once a day)" }))),
        h("li", null, h("b", { text: "Same browser, same device. " }), "Choices live in this browser only. To use another device, download the settings file (Settings) and import it there.")),
      h("p", { class: "hint", text: "Nothing is sent anywhere except the searches themselves: your search words go to the GDELT news index, and the forecast request carries your town's map position to Open-Meteo." })));
    add(sec, h("div", { class: "card" }, h("h2", null, ico("megaphone", "hi"), "Share or keep a copy"),
      h("ol", { class: "ways" },
        h("li", null, h("b", { text: "Open as a full page or Download page. " }), "On Today's brief. The page is one HTML file that opens in any browser and can be printed."),
        h("li", null, h("b", { text: "Copy newsletter. " }), "Copies the formatted page, ready to paste into a document or a message."))));
    add(sec, cloudCard());
    if (desktop) add(sec, scheduleCard());
  }

  function scheduleCard() {
    const cmd = "python -m dailybrief run --mark-read --quiet";
    return h("div", { class: "card" }, h("h2", { text: "Every morning on this computer" }),
      h("ol", { class: "ways" },
        h("li", null, h("button", { class: "btn ghost", onclick: async () => {
          try { const r = await S.api("/api/config", { config: cfg() }); toast(r.saved ? "Saved for scheduled runs." : "Not saved: fix the settings first."); }
          catch (e) { toast(e.message); }
        } }, "Save my settings for scheduled runs"), " The scheduled run uses the saved copy, so press this again after changes."),
        h("li", null, "Make the computer run this command each morning, in the Daily Brief folder: ", h("code", { text: cmd }), " ",
          h("button", { class: "link", onclick: async () => toast(await S.copyText(cmd) ? "Copied." : "Copy blocked.") }, "Copy")),
        h("li", null, "Windows: open Task Scheduler, Create Basic Task, Daily, pick the time, Start a program: python, arguments ", h("code", { text: "-m dailybrief run --mark-read --quiet" }),
          ", Start in: the Daily Brief folder. Mac or Linux: add it to crontab. The command ", h("code", { text: "python -m dailybrief schedule-help" }), " prints the exact lines for your computer.")),
      h("p", { class: "hint", text: "The computer must be on at that time. The newsletter page lands in the briefs folder of your data folder, and its stories join the no-repeat history." }));
  }

  // ------------------------------------------------------------ 5 AI assistants
  const PLATFORMS = {
    claude: { name: "Claude", prompt: "full", steps: [
      "Open claude.ai and create a Project (Projects in the sidebar, then New project).",
      "Paste the prompt into the project instructions, or upload it as a project file. Upload your settings file too.",
      "Turn on web search if it is off, start a chat in the project, and type START (first time) or RUN.",
      "For a daily run, paid plans can create a scheduled task that sends the same RUN request each morning."],
      note: "Checked 2026-10-23: web search is on every Claude plan and projects are too (free accounts up to five), but Anthropic's help page lists project instructions under paid plans, so on a free account send the prompt as the first message. Scheduled tasks are on paid plans.",
      links: [["Project instructions", "https://support.claude.com/en/articles/10185728"], ["Scheduled tasks", "https://support.claude.com/en/articles/13854387"]] },
    chatgpt: { name: "ChatGPT", prompt: "compact", steps: [
      "Create a GPT (Explore GPTs, Create) or a Project.",
      "Paste the compact prompt into the instructions box. GPT instructions allow 8,000 characters, so upload the full prompt, your settings file and the category library as knowledge files.",
      "Make sure web search is on, then type START or RUN.",
      "For a daily run, open Scheduled in the sidebar and create a task that says: Run my Daily Brief, followed by the compact prompt with your settings."],
      note: "Checked 2026-10-23: scheduled tasks live on the Scheduled page (OpenAI help). The 8,000-character GPT limit comes from OpenAI's community forum. A third-party guide says tasks do not run inside GPTs: UNVERIFIED.",
      links: [["Scheduled tasks", "https://help.openai.com/en/articles/10291617"]] },
    gemini: { name: "Gemini", prompt: "compact", steps: [
      "Open gemini.google.com and create a Gem (Gems, New Gem).",
      "Paste the prompt into the instructions and add your settings file and the category library as knowledge files.",
      "Open the Gem and type START or RUN.",
      "For a daily run, Google AI Pro, Ultra and some Workspace plans can make a scheduled action: up to 10 active, run within an hour of the time you pick."],
      note: "Checked 2026-10-23 against Google's Gems help page and reporting on scheduled actions. Whether a scheduled action can call a Gem: UNVERIFIED, so paste the compact prompt with your settings into the action.",
      links: [["Gems help", "https://support.google.com/gemini/answer/15236405"]] },
    grok: { name: "Grok", prompt: "compact", steps: [
      "Open grok.com and create a Project (Projects in the left panel), or use Customize to set instructions.",
      "Paste the prompt into the project instructions and add your settings file as a source.",
      "Type START or RUN.",
      "For a daily run, Grok Automations (formerly Tasks) can repeat a request on a schedule and send the result to you."],
      note: "Checked 2026-10-23 against third-party guides only; xAI help pages were not found. Treat the menu names and plan limits as UNVERIFIED.",
      links: [] },
    other: { name: "Another assistant", prompt: "full", steps: [
      "Use any assistant that can search the web.",
      "Send the prompt as the first message, or paste it into its custom instructions.",
      "Type START or RUN."], note: "The prompt refuses to write a brief when the assistant has no web search.", links: [] }
  };

  function settingsForAi() {
    const c = E.clone(cfg());
    delete c.email;
    return c;
  }

  function renderAi(sec) {
    add(sec, h("div", { class: "intro" }, h("h1", { text: "Use it with an AI assistant" }),
      h("p", { text: "The prompt makes Claude, ChatGPT, Gemini or Grok run the same interview and write the brief from a live web search, with a Lead Analysis and no repeats." })));
    const tabs = h("div", { class: "seg", role: "radiogroup", "aria-label": "Assistant" });
    Object.keys(PLATFORMS).forEach(k => tabs.append(h("button", { class: k === aiPlatform ? "on" : "", role: "radio", "aria-checked": k === aiPlatform ? "true" : "false",
      onclick: () => { aiPlatform = k; refresh(); } }, PLATFORMS[k].name)));
    add(sec, tabs);
    const p = PLATFORMS[aiPlatform];
    const kind = p.prompt;
    // Size-limited boxes get the compact prompt, with the settings as a separate file.
    const text = kind === "compact" ? E.buildPrompt(PROMPTS.compact, "file") : E.buildPrompt(PROMPTS.full, settingsForAi());
    const withSettings = E.buildPrompt(PROMPTS.compact, settingsForAi(), true);
    add(sec, h("div", { class: "card" }, h("h2", { text: p.name }),
      h("ol", { class: "ways" }, p.steps.map(s => h("li", { text: s }))),
      h("p", { class: "hint", text: p.note }),
      p.links.length ? h("p", { class: "hint" }, "Official help: ", p.links.map((l, i) => [i ? ", " : "", h("a", { href: l[1], target: "_blank", rel: "noopener", text: l[0] })])) : null,
      h("div", { class: "actions" },
        h("button", { class: "btn", onclick: async () => toast(await S.copyText(text) ? "Prompt copied (" + text.length + " characters)." : "Copy blocked; use Download.") },
          "Copy the " + (kind === "compact" ? "compact " : "") + "prompt"),
        h("button", { class: "btn ghost", onclick: () => S.download(kind === "compact" ? "daily-brief-prompt-compact.md" : "daily-brief-prompt.md", text, "text/markdown") }, "Download prompt"),
        kind === "compact" ? h("button", { class: "btn ghost", onclick: () => S.download("daily-brief-prompt.md", E.buildPrompt(PROMPTS.full, settingsForAi()), "text/markdown") }, "Download full prompt") : null,
        h("button", { class: "btn ghost", onclick: downloadSettings }, "Download settings file"),
        h("button", { class: "btn ghost", onclick: () => S.download("category-library.md", PROMPTS.library, "text/markdown") }, "Download category library")),
      kind === "compact" ? h("p", { class: "hint" }, "The compact prompt is " + text.length + " characters and expects your settings as a file. For a scheduled task, which cannot take files, use ",
        h("button", { class: "link", onclick: async () => toast(await S.copyText(withSettings) ? "Copied (" + withSettings.length + " characters)." : "Copy blocked.") }, "the compact prompt with your settings built in"),
        " (" + withSettings.length + " characters).") : null));
    add(sec, h("div", { class: "card" }, h("h2", { text: "Show the assistant's brief here" }),
      h("p", { text: "Ask the assistant for JSON (type JSON), copy its whole reply, and paste it below. The app turns it into your brief page" + (ready() ? " on Today's brief." : ".") }),
      pasteBox()));
    // Before setup is saved there is no Today page, so a pasted brief shows here.
    if (!ready() && state.brief) add(sec, briefView());
  }

  // ------------------------------------------------------------ Settings
  function downloadSettings() {
    S.download("daily-brief-settings.json", JSON.stringify(settingsForAi(), null, 2) + "\n", "application/json");
  }

  function importSettings(obj) {
    const v = E.validateConfig(obj);
    if (v.errors.length) { alert("These settings have problems:\n\n" + v.errors.join("\n")); return false; }
    state.config = E.merge(E.DEFAULTS, obj);
    delete state.config.email;  // version 0.1.0 settings may still hold addresses
    state.editing = false;
    state.draft = null;
    if (!ready()) {
      // A new browser: show the imported choices on the last question, ready to save.
      state.step = INTERVIEW.length - 1;
      save();
      show("setup");
      toast("Settings imported. Check them, then press Save and build my brief.");
      return true;
    }
    save();
    toast("Settings imported.");
    rerender();
    return true;
  }

  function renderSettings(sec) {
    add(sec, h("div", { class: "intro" }, h("h1", { text: "Settings" })));
    const file = h("input", { type: "file", accept: ".json,application/json", onchange: async e => {
      const f = e.target.files[0];
      if (!f) return;
      const obj = E.extractJson(await f.text());
      if (!obj) { toast("That file has no settings JSON."); return; }
      if (obj.db_backup === 1) restore(obj); else importSettings(obj);
    } });
    const paste = h("textarea", { rows: 4, placeholder: "Or paste settings JSON here, for example from an AI assistant" });
    add(sec, h("div", { class: "card" }, h("h2", { text: "Your settings file" }),
      h("p", { text: "One file holds your categories and choices. Use it to move to another device, to give an AI assistant, or to keep a copy." }),
      h("div", { class: "actions" }, h("button", { class: "btn", onclick: downloadSettings }, "Download settings file")),
      field("Import a settings or backup file", file), paste,
      h("button", { class: "btn ghost", onclick: () => { const o = E.extractJson(paste.value); if (o) importSettings(o); else toast("No JSON found."); } }, "Use pasted settings")));
    const size = desktop ? desktop.ledger_size : E.ledgerSize(history);
    add(sec, h("div", { class: "card" }, h("h2", { text: "No-repeat history" }),
      h("p", { text: size + " stories remembered " + (desktop ? "in your data folder on this computer." : "in this browser.") + " A story you have been sent, or marked as read, never comes back." }),
      h("button", { class: "btn ghost", onclick: async () => {
        if (!confirm("Forget every story you have been sent? Old stories may then appear again.")) return;
        if (desktop) { try { await S.api("/api/history/clear", {}); desktop.ledger_size = 0; } catch (e) { toast(e.message); return; } }
        else { history = E.emptyLedger(); saveHistory(); }
        toast("History cleared.");
        rerender();
      } }, "Clear the history")));
    add(sec, h("div", { class: "card" }, h("h2", { text: "Back up everything" }),
      h("p", { text: "Settings, the history in this browser and the last brief, in one file." }),
      h("div", { class: "actions" },
        h("button", { class: "btn ghost", onclick: () => S.download("daily-brief-backup-" + today() + ".json", JSON.stringify({ db_backup: 1, version: E.VERSION, state: state, history: history }) + "\n", "application/json") }, "Back up all data"),
        h("button", { class: "btn ghost", onclick: () => file.click() }, "Restore from file"))));
    if (desktop) {
      add(sec, h("div", { class: "card" }, h("h2", { text: "Desktop app" }),
        h("p", null, "Your data folder: ", h("code", { text: desktop.data_folder || "" })),
        h("p", { class: "hint", text: "It holds config.json (saved for scheduled runs), ledger.json (the history) and the briefs folder." })));
    }
    add(sec, h("div", { class: "card" }, h("h2", { text: "Start over" }),
      h("button", { class: "btn danger", onclick: () => {
        if (!confirm("Erase every setting and the history in this browser?")) return;
        S.removeStore(S.STORE_KEY);
        S.removeStore(S.LEDGER_KEY);
        state = loadState();
        history = E.emptyLedger();
        show("setup");
      } }, "Erase everything in this browser"),
      h("p", { class: "hint", text: "This browser holds about " + Math.ceil(S.storageBytes() / 1024) + " KB of Daily Brief data. Version " + E.VERSION + "." })));
  }

  function restore(obj) {
    if (!obj.state || typeof obj.state !== "object" || !obj.state.config) { toast("That backup is empty."); return; }
    const v = E.validateConfig(obj.state.config);
    if (v.errors.length) { alert("This backup's settings have problems:\n\n" + v.errors.join("\n")); return; }
    if (!confirm("Replace everything in this browser with the backup?")) return;
    // Only the known parts of the state come back, and the settings are checked like an import.
    const st = defaultState();
    for (const k of Object.keys(st)) if (k in obj.state && k !== "version") st[k] = obj.state[k];
    st.config = dropEmail(E.merge(E.DEFAULTS, obj.state.config));
    if (st.tab === "email" || st.tab === "deliver") st.tab = "daily";
    if (st.brief && (typeof st.brief !== "object" || !Array.isArray(st.brief.categories))) st.brief = null;
    st.editing = false;
    st.draft = null;
    state = st;
    history = E.cleanLedger(obj.history);
    save();
    saveHistory();
    toast("Restored.");
    show(state.setup_done ? "brief" : "setup");
  }

  // ------------------------------------------------------------ Help
  function renderHelp(sec) {
    const proj = S.projectUrl();
    add(sec, h("div", { class: "intro" }, h("h1", { text: "How the Daily Brief works" })));
    add(sec, h("div", { class: "card prose" },
      h("h2", { text: "Four ways to use it" }),
      h("ol", null,
        h("li", null, h("b", { text: "This web page. " }), "Runs the setup interview, remembers your choices in this browser, collects the news itself from free sources, and shows the brief as a page. Nothing to install, no account."),
        h("li", null, h("b", { text: "Your GitHub copy (optional). " }), "A private copy of the project runs every morning on GitHub's servers: it collects the news from Google News and publisher feeds and posts it as an issue in your copy. Free, no password. The Every day tab walks through it."),
        h("li", null, h("b", { text: "The desktop app. " }), "Download the project from GitHub (Code, Download ZIP), unzip it, and double-click Start-Windows.bat, Start-Mac.command or start-linux.sh. It opens this same app with live news from Google News and publisher feeds and the no-repeat history on disk. It needs Python 3.9 or newer from python.org, and no account or key."),
        h("li", null, h("b", { text: "An AI assistant. " }), "Claude, ChatGPT, Gemini or Grok runs the interview and writes the brief from a web search, adding a Lead Analysis.")),
      proj ? h("p", null, "Project page and download: ", h("a", { href: proj, target: "_blank", rel: "noopener", text: proj.replace("https://", "") }), " | ",
        h("a", { href: proj + "/issues/new", target: "_blank", rel: "noopener", text: "report a problem or suggest an idea" })) : null,
      h("h2", { text: "Where the news comes from" }),
      h("p", { text: "Browsers only let a page read another site when that site allows it. This page reads, in order: the publisher feeds that allow it (for example ESPN, CBS Sports, NASA, The New York Times, Fox News, CNBC and Wired); the backup collection, a file this site's GitHub project rebuilds every four hours from Google News and every library feed; for the categories about your town, the news of the local TV stations in your state, which the same GitHub project gathers every four hours into one file per state; and, only for what is still short, the GDELT news index, which watches news sites worldwide. The forecast comes from Open-Meteo. Everything is collected by this site and GitHub; nothing needs to run on your computer." }),
      h("h2", { text: "How stories are picked" }),
      h("ol", null,
        h("li", { text: "Search each category, then keep a story only if it mentions a term from every must-mention line and none of the leave-out terms." }),
        h("li", { text: "Drop social media posts, paperwork notices and, if you ask, list articles." }),
        h("li", { text: "Sort by freshness: NEWS inside your window first, then OLDER when a category is short, then undated REFERENCE pages." }),
        h("li", { text: "Leave out anything already sent, the same story from a second outlet, and any story already used in another category." }),
        h("li", { text: "Never pad a category. An empty one says so." })),
      h("h2", { text: "Reading the pills" }),
      h("p", { text: "Green, teal and amber pills give a story's age inside the window. OLDER is beyond the window, stamped with its true age. REFERENCE is an undated authoritative page, never presented as an event." }),
      h("h2", { text: "Privacy" }),
      h("p", { text: "No account and no tracking. Settings and the history stay in this browser, or in your data folder when you use the desktop app. This page sends your search words to the GDELT news index, fetches the feeds you list, reads your state's local news file from this site (your town stays in the browser), and, if the forecast is on, sends your town's rounded map position to Open-Meteo. Story photos load from the publishers' own sites. The desktop app and the GitHub copy send your search words to Google News instead." }),
      h("h2", { text: "Limits" }),
      h("ul", null,
        h("li", { text: "Stories from the GDELT index and Google News come with a headline only; publisher feeds add a short summary and often a photo." }),
        h("li", { text: "The GDELT index turns requests away when it is busy (too many requests). The page reads the backup collection and your state's local stations first, so most categories fill without it; categories you typed yourself still depend on it, and a small town can have quiet days on its local stations." }),
        h("li", { text: "Google News links open through a Google redirect page." }),
        h("li", { text: "AI assistants can still make mistakes. The prompt requires links from a live search; check a link before you act on a story." })),
      h("p", { class: "hint", text: "Daily Brief " + E.VERSION + ". Free and open source under the MIT licence." })));
  }

  const RENDER = { setup: renderSetup, categories: renderCategories, brief: renderBrief, daily: renderDaily, ai: renderAi, settings: renderSettings, help: renderHelp };

  // ------------------------------------------------------------ start
  document.querySelectorAll("#tabs button").forEach(b => b.addEventListener("click", () => show(b.getAttribute("data-tab"))));
  // Once set up, the app opens on the brief, unless changes to the choices are in progress.
  if (state.setup_done && (state.tab === "setup" || !state.tab) && !state.editing) state.tab = "brief";
  show(state.tab || "setup");
  // A daily routine: the first visit of the day collects by itself when asked to.
  const wantsAuto = () => state.auto_run && state.setup_done && !state.editing && !isFresh();
  S.detectDesktop().then(async info => {
    if (!info) return;
    desktop = info;
    // Settings live in the browser, per address. If this browser has none (a new
    // browser, or the app moved to another port), start from the copy saved for
    // scheduled runs instead of the defaults.
    if (freshBrowser && info.has_config) {
      try {
        const r = await S.api("/api/config");
        if (r.config && !E.validateConfig(r.config).errors.length) {
          state.config = E.merge(E.DEFAULTS, r.config);
          save();
          toast("Loaded the settings saved for scheduled runs on this computer.");
        }
      } catch (e) { /* keep the defaults */ }
    }
    modebar();
    rerender();
    if (wantsAuto()) getToday(true);
  });
  // After a reload for a new version, finish what was asked: the brief.
  let afterReload = "";
  try { afterReload = sessionStorage.getItem("db.after_reload") || ""; sessionStorage.removeItem("db.after_reload"); } catch (e) { /* nothing to finish */ }
  setTimeout(() => {
    if (desktop || webRun) return;
    if (afterReload === "run" || afterReload === "run-all") { if (state.tab !== "brief") show("brief"); getToday(afterReload === "run"); return; }
    if (wantsAuto()) { if (state.tab !== "brief") show("brief"); getToday(true); }
  }, 1200);
  // Coming back to a tab left open: load a newer version if the site has one, unless
  // a brief is being built or choices are being changed.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && !webRun && !job && !state.editing) reloadForNewVersion("");
  });
  if ("serviceWorker" in navigator && location.protocol === "https:") {
    navigator.serviceWorker.register("sw.js").catch(() => { /* offline support is optional */ });
  }
  window.DB_APP = { show: show, state: () => state, history: () => history, isDesktop: () => !!desktop };
})();
