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

  const TABS = ["setup", "categories", "brief", "email", "ai", "settings", "help"];
  const STEPS = ["setup", "categories", "brief", "email", "ai"];
  const STEP_LABELS = { setup: "Setup", categories: "Categories", brief: "Brief", email: "Email", ai: "AI assistants" };

  const freshBrowser = !S.readStore(S.STORE_KEY, null);  // before anything is saved
  let state = loadState();
  let history = E.cleanLedger(S.readStore(S.LEDGER_KEY, null));
  let desktop = null;
  let job = null;
  let aiPlatform = "claude";

  // ------------------------------------------------------------ state
  function defaultState() {
    return { version: 1, tab: "setup", step: 0, config: null, email: { to: [], from_name: "" }, brief: null, health: null };
  }

  function loadState() {
    const s = S.readStore(S.STORE_KEY, null);
    const st = s && s.version === 1 ? Object.assign(defaultState(), s) : defaultState();
    if (!st.config) {
      // First visit: the starter pack without local categories, which need a town.
      st.config = E.configFromPack(LIB, "starter", {});
      st.config.categories = st.config.categories.filter(c => !c.needs_location);
    }
    st.config = E.merge(E.DEFAULTS, st.config);
    if (!st.config.delivery.timezone) st.config.delivery.timezone = browserZone();
    return st;
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

  function cfg() { return state.config; }

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

  function stepBar(tab) {
    const i = STEPS.indexOf(tab);
    if (i < 0) return null;
    const back = i > 0 ? h("button", { class: "btn ghost", onclick: () => show(STEPS[i - 1]) }, "Back: " + STEP_LABELS[STEPS[i - 1]]) : h("span");
    const next = i < STEPS.length - 1 ? h("button", { class: "btn", onclick: () => show(STEPS[i + 1]) }, "Next: " + STEP_LABELS[STEPS[i + 1]]) : null;
    return h("div", { class: "stepbar" }, back, next);
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
  function show(tab) {
    if (TABS.indexOf(tab) < 0) tab = "setup";
    state.tab = tab;
    save();
    for (const t of TABS) {
      const sec = document.getElementById("tab-" + t);
      sec.hidden = t !== tab;
      const btn = document.querySelector('#tabs button[data-tab="' + t + '"]');
      btn.setAttribute("aria-selected", t === tab ? "true" : "false");
      btn.classList.toggle("active", t === tab);
    }
    const sec = clear(document.getElementById("tab-" + tab));
    RENDER[tab](sec);
    if (tab !== "setup" || state.step === INTERVIEW.length - 1) add(sec, stepBar(tab));
    window.scrollTo(0, 0);
  }

  function rerender() { show(state.tab); }

  function modebar() {
    const bar = clear(document.getElementById("modebar"));
    if (desktop) {
      bar.className = "modebar on";
      add(bar, [h("b", { text: "Desktop app. " }), "Live news, the no-repeat history and email sending are on."]);
    } else {
      bar.className = "modebar";
      add(bar, [h("b", { text: "Web version. " }), "Setup, preview, email drafts and the AI prompt work here. Live news comes from your GitHub copy, the desktop app or an AI assistant. ",
        h("a", { href: "#", onclick: e => { e.preventDefault(); show("help"); } }, "Why?")]);
    }
  }

  // ------------------------------------------------------------ 1 Setup (interview)
  const INTERVIEW = [
    { title: "What is the brief for?", body: stepPurpose },
    { title: "Pick your categories", body: stepCategories },
    { title: "Your area", body: stepArea },
    { title: "How much, and how fresh", body: stepVolume },
    { title: "What matters to you", body: stepWatch },
    { title: "A countdown (optional)", body: stepCountdown },
    { title: "When and how it arrives", body: stepTitle },
    { title: "Review and save", body: stepReview }
  ];

  function renderSetup(sec) {
    const i = Math.min(Math.max(state.step || 0, 0), INTERVIEW.length - 1);
    const st = INTERVIEW[i];
    add(sec, h("div", { class: "intro" }, h("h1", { text: "Set up your morning brief" }),
      i === 0 ? h("p", { text: "Eight short questions. Every answer starts with a sensible value, so change only what is different for you. You can come back any time." }) : null));
    const dots = h("ol", { class: "dots", "aria-label": "Interview progress" });
    INTERVIEW.forEach((s, k) => dots.append(h("li", { class: k === i ? "now" : k < i ? "done" : "" },
      h("button", { onclick: () => { state.step = k; rerender(); }, "aria-label": "Question " + (k + 1) + ": " + s.title }, String(k + 1)))));
    const card = h("div", { class: "card interview" }, h("p", { class: "kicker", text: "Question " + (i + 1) + " of " + INTERVIEW.length }), h("h2", { text: st.title }));
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
        rerender();
      } }, h("b", { text: p.name }), h("span", { text: p.description })));
    }
    add(card, [h("h3", { text: "Starter packs" }), packs]);
    add(card, quickAdd(() => rerender()));
    add(card, h("h3", { text: "Categories (" + c.categories.length + " of " + E.MAX_CATEGORIES + " chosen)" }));
    for (const g of LIB.groups) {
      const box = h("fieldset", { class: "group" }, h("legend", { text: g.name }));
      for (const lc of LIB.categories.filter(x => x.group === g.id)) {
        const id = "lib-" + lc.id;
        const cb = h("input", { type: "checkbox", id: id, checked: hasCat(lc.id), onchange: e => {
          if (!toggleLibraryCat(lc.id, e.target.checked)) e.target.checked = false;
          rerender();
        } });
        box.append(h("div", { class: "check" }, cb, h("label", { for: id }, h("b", { text: lc.name.replace("({location})", "(your town)") }),
          h("span", { class: "hint", text: lc.description }))));
      }
      add(card, box);
    }
    const custom = c.categories.filter(x => !E.categoryFromLibrary(LIB, x.id));
    if (custom.length) {
      add(card, h("h3", { text: "Your own categories" }));
      add(card, h("ul", { class: "plain" }, custom.map(x => h("li", null, h("b", { text: x.name }), " ",
        h("button", { class: "link", onclick: () => { c.categories = c.categories.filter(y => y !== x); save(); rerender(); } }, "Remove")))));
    }
    add(card, builder(() => rerender()));
  }

  const QUICK_STOP = ["the", "and", "for", "with", "about", "from", "that", "this", "what", "want", "more", "news", "any", "all"];

  function topicWords(text) {
    return String(text || "").toLowerCase().split(/[^a-z0-9+#&]+/).filter(w => w.length >= 3 && QUICK_STOP.indexOf(w) < 0);
  }

  /* Type a topic in plain words. Matching ready-made categories appear as you
     type; Add turns the words themselves into your own category. */
  function quickAdd(done) {
    const input = h("input", { type: "text", placeholder: "For example: electric cars, EVs, charging stations", "aria-label": "A topic to follow" });
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
      toast("Added " + nm + ". Fine-tune its searches on step 2, Categories.");
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
    add(card, field("Town or city", h("input", { type: "text", value: r.location || "", placeholder: "Springfield",
      oninput: e => { r.location = e.target.value; save(); } }), "The town name only. No street address."));
    add(card, field("Nearby towns or the county that also count as local (commas)", h("input", { type: "text", value: (r.local_terms || []).join(", "),
      placeholder: "Shelbyville, Sangamon County", oninput: e => { r.local_terms = commas(e.target.value); save(); } })));
  }

  function stepVolume(card) {
    const b = cfg().brief;
    const nums = (arr, unit) => arr.map(n => [n, n + unit]);
    add(card, field("Stories per category", select(nums([1, 2, 3, 4, 5, 6, 7, 8, 10], ""), b.items_per_category, v => { b.items_per_category = +v; save(); })));
    add(card, field("Fresh means published in the last", select(nums([12, 24, 36, 48, 72], " hours"), b.window_hours, v => {
      b.window_hours = +v;
      if (b.backfill_max_hours < b.window_hours) b.backfill_max_hours = b.window_hours;
      save();
      rerender();
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
    const on = h("input", { type: "checkbox", id: "cdon", checked: cd.enabled, onchange: e => { cd.enabled = e.target.checked; save(); rerender(); } });
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
        h("button", { class: "link", onclick: () => { cd.milestones.splice(i, 1); save(); rerender(); } }, "Remove")));
    });
    add(card, [list, h("button", { class: "btn ghost", onclick: () => { cd.milestones = cd.milestones || []; cd.milestones.push({ date: "", label: "", note: "" }); save(); rerender(); } }, "Add a milestone")]);
  }

  function stepTitle(card) {
    const b = cfg().brief;
    const preview = h("p", { class: "hint" });
    const upd = () => { preview.textContent = "Example: " + N.subjectLine({ date: today(), title: b.title, categories: [] }, cfg()); };
    add(card, field("Newsletter title", h("input", { type: "text", value: b.title, oninput: e => { b.title = e.target.value; save(); upd(); } })));
    add(card, field("Email subject", h("input", { type: "text", value: b.subject, oninput: e => { b.subject = e.target.value; save(); upd(); } }),
      "{total} is the story count, {date} the date, {title} the title, {empty} the number of empty categories."));
    add(card, preview);
    upd();
    const dv = cfg().delivery;
    add(card, h("div", { class: "row" },
      field("Delivery time", h("input", { type: "time", value: dv.time, oninput: e => { dv.time = e.target.value; save(); } }),
        "When the GitHub copy or the desktop app sends it."),
      field("Time zone", h("input", { type: "text", list: "zones", value: dv.timezone, placeholder: "America/New_York",
        oninput: e => { dv.timezone = E.collapse(e.target.value); save(); } }), "Your browser says " + (browserZone() || "nothing") + ".")));
    add(card, h("datalist", { id: "zones" }, ZONES.map(z => h("option", { value: z }))));
    const ch = (name, label, hint) => {
      const id = "ch-" + name;
      return h("div", { class: "check" }, h("input", { type: "checkbox", id: id, checked: dv.channels.indexOf(name) >= 0, onchange: e => {
        const set = dv.channels.filter(x => x !== name);
        if (e.target.checked) set.push(name);
        if (!set.length) { e.target.checked = true; toast("Keep at least one way to receive it."); return; }
        dv.channels = ["email", "issue"].filter(x => set.indexOf(x) >= 0);
        save();
      } }), h("label", { for: id }, h("b", { text: label }), h("span", { class: "hint", text: hint })));
    };
    add(card, h("h3", { text: "How it arrives" }));
    add(card, ch("email", "Email", "Sent through your own mail account. Needs that account's app password, saved as a secret in your GitHub copy or in the desktop app."));
    add(card, ch("issue", "GitHub issue", "No password at all: the brief is posted as an issue in your private GitHub copy, and GitHub emails it to you."));
    add(card, field("Send to (commas)", h("input", { type: "email", multiple: true, value: (state.email.to || []).join(", "), placeholder: "you@example.com",
      oninput: e => { state.email.to = commas(e.target.value); save(); } }), "Kept in this browser only. It is never added to your settings file or the AI prompt. In GitHub, recipients go in the MAIL_TO secret."));
  }

  function localCats() {
    return cfg().categories.filter(c => c.needs_location || JSON.stringify(c).indexOf("{location}") >= 0 || JSON.stringify(c).indexOf("{local_terms}") >= 0);
  }

  function stepReview(card) {
    const v = E.validateConfig(cfg());
    const n = E.normalizeConfig(cfg());
    add(card, msgList(v));
    if (localCats().length && !E.collapse(cfg().reader.location)) {
      add(card, h("div", { class: "actions" },
        h("button", { class: "btn ghost", onclick: () => { state.step = 2; rerender(); } }, "Add my town"),
        h("button", { class: "btn ghost", onclick: () => {
          const drop = localCats();
          cfg().categories = cfg().categories.filter(c => drop.indexOf(c) < 0);
          save();
          rerender();
        } }, "Remove the local categories")));
    }
    const rows = [
      ["Categories", n.categories.map(c => E.resolveCategory(c, n.reader).name).join(", ") || "none"],
      ["Stories per category", String(n.brief.items_per_category)],
      ["Fresh window", n.brief.window_hours + " hours"],
      ["Older stories", n.brief.backfill_max_hours > n.brief.window_hours ? "up to " + n.brief.backfill_max_hours + " hours, labelled OLDER" : "off"],
      ["Reference pages", n.brief.allow_reference ? "allowed, labelled REFERENCE" : "off"],
      ["Your area", n.reader.location || "not set"],
      ["Watch list", (n.reader.watch_list || []).join(", ") || "empty"],
      ["Countdown", n.countdown.enabled ? n.countdown.label + " on " + n.countdown.date : "off"]
    ];
    add(card, h("table", { class: "summary" }, h("tbody", null, rows.map(r => h("tr", null, h("th", { text: r[0] }), h("td", { text: r[1] }))))));
    add(card, h("div", { class: "actions" },
      h("button", { class: "btn", disabled: v.errors.length > 0, onclick: () => { save(); show("brief"); } }, "Save and get my brief"),
      h("button", { class: "btn ghost", onclick: downloadSettings }, "Download settings file")));
  }

  // ------------------------------------------------------------ 2 Categories
  function renderCategories(sec) {
    const c = cfg();
    add(sec, h("div", { class: "intro" }, h("h1", { text: "Your categories" }),
      h("p", { text: "Each category is a desk in the newsletter. Open one to change its searches and filters. A story must mention at least one term from every \"must mention\" line, and none of the \"leave out\" terms." })));
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
      quickAdd(() => rerender()),
      h("h3", { text: "Or choose from the library" }),
      h("div", { class: "row" }, pick, h("button", { class: "btn", onclick: () => { if (pick.value && toggleLibraryCat(pick.value, true)) rerender(); } }, "Add")),
      builder(() => rerender())));
  }

  function categoryCard(cat, i, refresh) {
    const c = cfg();
    const changed = () => { save(); refresh(); };
    const move = d => { const j = i + d; if (j < 0 || j >= c.categories.length) return; c.categories.splice(i, 1); c.categories.splice(j, 0, cat); save(); rerender(); };
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
      field("Publisher feeds (desktop app), one link per line", h("textarea", { rows: 2, value: (cat.feeds || []).join("\n"), oninput: e => { cat.feeds = lines(e.target.value); changed(); } })),
      field("Stories in this category", select([["", "Use the default"]].concat([1, 2, 3, 4, 5, 6, 7, 8, 10].map(n => [n, String(n)])), cat.items || "",
        v => { cat.items = v ? +v : null; changed(); })),
      h("div", { class: "check" }, h("input", { type: "checkbox", id: "lst" + i, checked: !!cat.skip_listicles, onchange: e => { cat.skip_listicles = e.target.checked; changed(); } }),
        h("label", { for: "lst" + i }, "Skip \"top 10\" and \"best of\" list articles")));
    return h("div", { class: "card cat", style: "border-left-color:" + color.value },
      h("div", { class: "cathead" }, h("span", { class: "tag", style: "background:" + color.value, text: "T" + (i + 1) }), color, name,
        h("button", { class: "icon", "aria-label": "Move up", disabled: i === 0, onclick: () => move(-1) }, "\u2191"),
        h("button", { class: "icon", "aria-label": "Move down", disabled: i === c.categories.length - 1, onclick: () => move(1) }, "\u2193"),
        h("button", { class: "link", onclick: () => { if (confirm("Remove " + cat.name + "?")) { c.categories.splice(i, 1); save(); rerender(); } } }, "Remove")),
      h("details", null, h("summary", { text: "Searches and filters" }), body));
  }

  // ------------------------------------------------------------ 3 Brief
  function renderBrief(sec) {
    add(sec, h("div", { class: "intro" }, h("h1", { text: "Today's brief" })));
    const v = E.validateConfig(cfg());
    if (v.errors.length) {
      add(sec, h("div", { class: "card" }, h("p", { text: "Your settings need a fix before a brief can be built." }), msgList(v),
        h("button", { class: "btn", onclick: () => { state.step = 7; show("setup"); } }, "Go to Review")));
    }
    if (desktop) {
      const useHist = h("input", { type: "checkbox", id: "usehist", checked: true });
      const go = h("button", { class: "btn big", disabled: v.errors.length > 0 || !!job, onclick: () => runDesktop(useHist.checked) }, job ? "Collecting..." : "Get today's brief");
      add(sec, h("div", { class: "card" }, h("p", { text: "Searches Google News and the publisher feeds for every category, keeps fresh, on-topic stories, and leaves out anything you have already been sent. About a minute." }),
        h("div", { class: "row" }, go, h("div", { class: "check" }, useHist, h("label", { for: "usehist" }, "Leave out stories already sent"))),
        h("div", { id: "progress" })));
      if (job) paintProgress();
    } else {
      add(sec, h("div", { class: "card" },
        h("h2", { text: "Get the news in" }),
        h("p", { text: "News sites do not let a web page read their feeds, so this page cannot fetch the news by itself. Choose one:" }),
        h("ol", { class: "ways" },
          h("li", null, h("b", { text: "Run it on GitHub, free. " }), "Your own private copy of this project collects the news and delivers it every morning on GitHub's servers. No computer, no AI, no keys. ",
            h("button", { class: "link", onclick: () => { show("email"); const c = document.getElementById("cloud"); if (c) c.scrollIntoView(); } }, "Set it up")),
          h("li", null, h("b", { text: "Ask an AI assistant. " }), "Claude, ChatGPT, Gemini or Grok searches the web with your settings and writes the brief, with a Lead Analysis. ",
            h("button", { class: "link", onclick: () => show("ai") }, "Set it up")),
          h("li", null, h("b", { text: "Use the desktop app. " }), "A free download for Windows, Mac or Linux that collects the news itself and emails it every morning, no AI needed. ",
            h("button", { class: "link", onclick: () => show("help") }, "How to get it")),
          h("li", null, h("b", { text: "See the sample. " }), h("button", { class: "link", onclick: () => setBrief(E.clone(SAMPLE.brief), null) }, "Show the sample brief")))));
      const ta = h("textarea", { rows: 6, placeholder: "Paste the whole reply from your AI assistant here. The app finds the brief JSON in it." });
      add(sec, h("div", { class: "card" }, h("h2", { text: "Paste a brief from your AI assistant" }),
        h("p", { text: "In the chat, type JSON after the brief (or RUN with the JSON output setting), copy the reply, and paste it here." }),
        ta, h("button", { class: "btn", onclick: () => pasteBrief(ta.value) }, "Show the newsletter")));
    }
    if (state.brief) add(sec, briefView());
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
    const before = E.checkBrief(obj, cfg());
    if (before.errors.length && !confirm("This brief has " + before.errors.length + " problem(s), listed under the preview. Show it anyway?")) return;
    const f = E.filterSeen(obj, history);
    setBrief(f.brief, null);
    if (f.withheld) toast(f.withheld + " stories were left out because you have already seen them.");
  }

  function setBrief(brief, health) {
    state.brief = brief;
    state.health = health;
    save();
    rerender();
    const v = document.getElementById("briefview");
    if (v) v.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function rendered() {
    const isSample = state.brief && state.brief.source === "sample";
    return N.render(state.brief, isSample ? SAMPLE.settings : cfg());
  }

  function briefView() {
    const out = rendered();
    const chk = E.checkBrief(state.brief, state.brief.source === "sample" ? SAMPLE.settings : cfg());
    const frame = h("iframe", { class: "preview", title: "Newsletter preview", sandbox: "allow-popups allow-popups-to-escape-sandbox" });
    frame.srcdoc = out.html.replace("<head>", "<head><base target=\"_blank\">");
    const st = N.stats(state.brief);
    const canSend = desktop && desktop.mail && desktop.mail.configured;
    const box = h("div", { class: "card", id: "briefview" },
      h("h2", { text: out.subject }),
      h("p", { class: "hint", text: st.total + " stories, " + st.news + " fresh, " + st.empty.length + " empty categories." }),
      h("div", { class: "actions" },
        desktop ? h("button", { class: "btn", disabled: !canSend, title: canSend ? "" : "Set up mail on the Email step first", onclick: () => sendNow(false) }, "Email it now") : null,
        h("button", { class: "btn" + (desktop ? " ghost" : ""), onclick: downloadEml }, "Download email draft"),
        h("button", { class: "btn ghost", onclick: async () => {
          const how = await S.copyRich(out.html, out.text);
          toast(how === "rich" ? "Copied. Paste it into a new email." : how === "text"
            ? "Copied as plain text; this browser cannot copy the formatted version. Download email draft keeps the layout."
            : "This browser blocked copying. Use Download email draft.");
        } }, "Copy for email"),
        h("button", { class: "btn ghost", onclick: () => S.download(fileStem() + ".html", out.html, "text/html") }, "Download page"),
        state.brief.source !== "sample" ? h("button", { class: "btn ghost", onclick: markRead }, "Mark as read") : null),
      chk.errors.length || chk.warnings.length ? h("details", { class: "checks" }, h("summary", { text: "Checks: " + chk.errors.length + " problem(s), " + chk.warnings.length + " note(s)" }), msgList(chk)) : null,
      frame,
      state.health ? healthView(state.health) : null);
    return box;
  }

  function fileStem() { return "daily-brief-" + (state.brief && state.brief.date ? state.brief.date : today()); }

  function downloadEml() {
    const out = rendered();
    S.download(fileStem() + ".eml", N.buildEml(out, state.email.to || [], cfg().email && cfg().email.from_name), "message/rfc822");
    toast("Saved. Open the file to get a ready-to-send email (Outlook opens it as a draft).");
  }

  async function markRead() {
    if (desktop) {
      try {
        const r = await S.api("/api/commit", { brief: state.brief, config: cfg() });
        desktop.ledger_size = r.ledger_size;
        toast("Marked as read. These stories will not come back.");
      } catch (e) { toast(e.message); }
      return;
    }
    history = E.ledgerAdd(history, state.brief, false);
    saveHistory();
    toast("Marked as read. Pasted briefs will leave these stories out from now on.");
  }

  async function sendNow(force) {
    try {
      const r = await S.api("/api/send", { brief: state.brief, config: cfg(), to: state.email.to, force: force === true });
      toast("Sent to " + r.sent + " recipient(s)." + (r.ledger_size !== null ? " Marked as read." : ""));
    } catch (e) {
      if (e.details && e.details.already_sent && confirm(e.message + " Send it again?")) return sendNow(true);
      toast(e.message);
    }
  }

  async function runDesktop(useHistory) {
    try {
      const r = await S.api("/api/run", { config: cfg(), use_history: useHistory });
      if (r.already_running) toast("A collection was already running, so this shows that one. Run again when it finishes to use new settings.");
      job = { id: r.job, state: "running", done: 0, total: 0, step: "Starting" };
      rerender();
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
    if (!p || !job) return;
    const pct = job.total ? Math.round(100 * job.done / job.total) : 3;
    clear(p).append(h("div", { class: "bar" }, h("div", { class: "fill", style: "width:" + pct + "%" })),
      h("p", { class: "hint", text: "Checking " + (job.step || "") + " (" + job.done + " of " + (job.total || "?") + " sources)" }));
  }

  function healthView(health) {
    const rows = [];
    for (const cat of state.brief.categories || []) {
      const hh = health[cat.id];
      if (!hh) continue;
      const errs = hh.queries.concat(hh.feeds).filter(x => x.error);
      const rej = Object.keys(cat.rejected || {}).map(k => k + " " + cat.rejected[k]).join(", ");
      rows.push(h("tr", null, h("th", { text: cat.name }), h("td", { text: hh.queries.reduce((a, x) => a + x.items, 0) + " search results, " + hh.feeds.reduce((a, x) => a + x.items, 0) + " feed items" }),
        h("td", { text: rej || "none" }), h("td", { class: errs.length ? "badtext" : "", text: errs.length ? errs.map(x => (x.query || x.url) + ": " + x.error).join("; ") : "none" })));
    }
    return h("details", { class: "checks" }, h("summary", { text: "Sources and filters" }),
      h("table", { class: "summary" }, h("thead", null, h("tr", null, h("th", { text: "Category" }), h("th", { text: "Found" }), h("th", { text: "Left out" }), h("th", { text: "Source problems" }))),
        h("tbody", null, rows)));
  }

  // ------------------------------------------------------------ 4 Email
  function cloudCard() {
    const proj = S.projectUrl();
    const d = E.normalizeConfig(cfg()).delivery;
    const lines = E.cronLines(d.time, d.timezone, new Date().getFullYear());
    const cronText = lines.map(l => "    - cron: \"" + l + "\"").join("\n");
    const link = (href, text) => href ? h("a", { href: href, target: "_blank", rel: "noopener", text: text }) : h("b", { text: text });
    const email = d.channels.indexOf("email") >= 0;
    const issue = d.channels.indexOf("issue") >= 0;
    return h("div", { class: "card", id: "cloud" }, h("h2", { text: "Every morning from GitHub, free" }),
      h("p", { text: "GitHub's servers collect the news, build the newsletter and deliver it, with no computer of yours switched on. It uses free services only: Google News RSS and publisher feeds need no keys, and no AI or search service is involved." }),
      h("ol", { class: "ways" },
        h("li", null, h("b", { text: "Make your own private copy. " }), link(proj ? proj + "/generate" : "", "Use this template"),
          ", choose Private, and create the repository."),
        h("li", null, h("b", { text: "Add your settings. " }), h("button", { class: "link", onclick: downloadSettings }, "Download the settings file"),
          ", then in your copy choose Add file, Upload files, drop daily-brief-settings.json in, and commit. Upload it again after you change something here."),
        email ? h("li", null, h("b", { text: "Email: add the mail secrets. " }), "In your copy open Settings, Secrets and variables, Actions, New repository secret, and add ",
          h("code", { text: "SMTP_HOST" }), " (smtp.gmail.com for Gmail), ", h("code", { text: "SMTP_USER" }), " (your address), ",
          h("code", { text: "SMTP_PASSWORD" }), " (an app password, not your normal one) and ", h("code", { text: "MAIL_TO" }),
          " (who gets it, commas between addresses). Optional: SMTP_PORT, SMTP_SECURITY, MAIL_FROM.") : null,
        issue ? h("li", null, h("b", { text: "GitHub issue: nothing to add. " }), "Each morning the brief appears as an issue in your copy, mentioning you, and yesterday's issue closes. GitHub emails it to you when email notifications are on (Settings, Notifications).") : null,
        h("li", null, h("b", { text: "Set the time. " }), lines.length ? [
          "In your copy open .github/workflows/daily-brief.yml, choose Edit, and replace the two cron lines with these (they put the brief out at " + d.time + " " + d.timezone + " in summer and winter):",
          h("pre", { class: "code", text: cronText }),
          h("button", { class: "link", onclick: async () => toast(await S.copyText(cronText) ? "Copied." : "Copy blocked.") }, "Copy the lines")
        ] : "Choose a delivery time and time zone on Setup question 7 first."),
        h("li", null, h("b", { text: "Test it. " }), "Open the Actions tab, choose Daily brief, then Run workflow. A run takes a minute or two; the summary shows what was sent.")),
      h("p", { class: "hint", text: "GitHub Actions is free for public repositories; a private copy uses your plan's included minutes, about three a day. Keep your copy private: in a public one, anyone can read your settings and run logs, and GitHub turns scheduled runs off after 60 days without activity. Times are best kept off the top of the hour, when GitHub delays runs." }));
  }

  function renderEmail(sec) {
    add(sec, h("div", { class: "intro" }, h("h1", { text: "Deliver the newsletter" })));
    add(sec, cloudCard());
    add(sec, h("div", { class: "card" }, h("h2", { text: "Who gets it" }),
      field("Send to (commas)", h("input", { type: "email", multiple: true, value: (state.email.to || []).join(", "), placeholder: "you@example.com",
        oninput: e => { state.email.to = commas(e.target.value); save(); } }), "Kept in this browser only."),
      field("From name", h("input", { type: "text", value: (cfg().email && cfg().email.from_name) || "", placeholder: "Morning Brief",
        oninput: e => { cfg().email.from_name = e.target.value; save(); } }))));
    if (desktop) add(sec, mailSettings());
    add(sec, h("div", { class: "card" }, h("h2", { text: "Other ways to send" }),
      h("ol", { class: "ways" },
        h("li", null, h("b", { text: "Email draft file. " }), "On step 3, Download email draft saves an .eml file. Outlook opens it as a draft ready to send; other mail programs open it as a message you can forward."),
        h("li", null, h("b", { text: "Copy for email. " }), "Copies the formatted newsletter. Paste it into a new message in Gmail, Outlook or Apple Mail."),
        h("li", null, h("b", { text: "From your computer. " }), desktop ? "Set up mail above, then schedule the morning run below." : "The desktop app also collects and sends it, from your own computer."))));
    if (desktop) add(sec, scheduleCard());
  }

  function mailSettings() {
    const m = desktop.mail || {};
    const vals = { host: m.host || "", port: m.port || "587", security: m.security || "starttls", user: m.user || "", sender: m.sender || "", password: "" };
    const inp = (k, type, ph) => h("input", { type: type || "text", value: vals[k], placeholder: ph || "", autocomplete: k === "password" ? "new-password" : "off", oninput: e => { vals[k] = e.target.value; } });
    const preset = select([["", "Choose a provider"], ["gmail", "Gmail or Google Workspace"], ["other", "Another provider"]], "", v => {
      if (v === "gmail") { vals.host = "smtp.gmail.com"; vals.port = "587"; vals.security = "starttls"; save(); clear(wrap).append(form()); }
    });
    const wrap = h("div");
    function form() {
      return h("div", null,
        field("SMTP server", inp("host", "text", "smtp.gmail.com")),
        h("div", { class: "row" }, field("Port", inp("port", "text", "587")),
          field("Security", select([["starttls", "STARTTLS (port 587)"], ["ssl", "SSL (port 465)"]], vals.security, v => {
            vals.security = v;
            const port = v === "ssl" ? "465" : "587";
            if ((vals.port === "587" || vals.port === "465" || !vals.port) && vals.port !== port) { vals.port = port; clear(wrap).append(form()); }
          }))),
        field("Account name (usually your address)", inp("user", "email")),
        field("App password", inp("password", "password", m.has_password ? "Saved. Leave empty to keep it." : "")),
        field("Send from (optional)", inp("sender", "email", "Defaults to the account name")));
    }
    wrap.append(form());
    return h("div", { class: "card" }, h("h2", { text: "Mail settings (this computer)" }),
      h("p", { class: m.configured ? "ok" : "warn", text: m.configured ? "Mail is set up." : "Mail is not set up yet." }),
      m.env_overrides && m.env_overrides.length ? h("p", { class: "hint", text: "These come from environment variables and win over this form: " + m.env_overrides.join(", ") }) : null,
      field("Provider", preset), wrap,
      h("p", { class: "hint", text: "Gmail needs 2-Step Verification and an app password (Google Account, Security, App passwords). The password is stored only in your data folder on this computer and is never shown again." }),
      h("div", { class: "actions" },
        h("button", { class: "btn", onclick: async () => {
          try {
            desktop.mail = await S.api("/api/mail", { values: Object.assign({}, vals, { to: state.email.to }) });
            toast(desktop.mail.configured ? "Mail settings saved." : "Saved, but mail is not ready yet. " + (desktop.mail.problem || ""));
            rerender();
          } catch (e) { toast(e.message); }
        } }, "Save mail settings"),
        h("button", { class: "btn ghost", disabled: !m.configured, onclick: async () => {
          try { const r = await S.api("/api/send", { brief: SAMPLE.brief, config: SAMPLE.settings, to: state.email.to }); toast("Test sent to " + r.sent + " recipient(s)."); }
          catch (e) { toast(e.message); }
        } }, "Send a test (the sample)")));
  }

  function scheduleCard() {
    const cmd = "python -m dailybrief run --send --quiet";
    return h("div", { class: "card" }, h("h2", { text: "Every morning, automatically" }),
      h("ol", { class: "ways" },
        h("li", null, h("button", { class: "btn ghost", onclick: async () => {
          try { const r = await S.api("/api/config", { config: cfg() }); toast(r.saved ? "Saved for scheduled runs." : "Not saved: fix the settings first."); }
          catch (e) { toast(e.message); }
        } }, "Save my settings for scheduled runs"), " The scheduled run uses the saved copy, so press this again after changes."),
        h("li", null, "Make the computer run this command each morning, in the Daily Brief folder: ", h("code", { text: cmd }), " ",
          h("button", { class: "link", onclick: async () => toast(await S.copyText(cmd) ? "Copied." : "Copy blocked.") }, "Copy")),
        h("li", null, "Windows: open Task Scheduler, Create Basic Task, Daily, pick the time, Start a program: python, arguments ", h("code", { text: "-m dailybrief run --send --quiet" }),
          ", Start in: the Daily Brief folder. Mac or Linux: add it to crontab. The command ", h("code", { text: "python -m dailybrief schedule-help" }), " prints the exact lines for your computer.")),
      h("p", { class: "hint", text: "The computer must be on at that time. Each day is sent once; the no-repeat history updates after a successful send." }));
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
      h("p", { text: "The prompt makes Claude, ChatGPT, Gemini or Grok run the same interview and write the brief from a live web search, with a Lead Analysis and no repeats. Your email address is never put in the prompt." })));
    const tabs = h("div", { class: "seg", role: "radiogroup", "aria-label": "Assistant" });
    Object.keys(PLATFORMS).forEach(k => tabs.append(h("button", { class: k === aiPlatform ? "on" : "", role: "radio", "aria-checked": k === aiPlatform ? "true" : "false",
      onclick: () => { aiPlatform = k; rerender(); } }, PLATFORMS[k].name)));
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
    add(sec, h("div", { class: "card" }, h("h2", { text: "Get the newsletter and email" }),
      h("p", { text: "Ask the assistant for JSON (type JSON), copy its reply, and paste it on step 3. The app turns it into the newsletter and the email." }),
      h("button", { class: "btn ghost", onclick: () => show("brief") }, "Go to step 3")));
  }

  // ------------------------------------------------------------ Settings
  function downloadSettings() {
    S.download("daily-brief-settings.json", JSON.stringify(settingsForAi(), null, 2) + "\n", "application/json");
  }

  function importSettings(obj) {
    const v = E.validateConfig(obj);
    if (v.errors.length) { alert("These settings have problems:\n\n" + v.errors.join("\n")); return false; }
    const keepEmail = cfg().email;
    state.config = E.merge(E.DEFAULTS, obj);
    state.config.email = obj.email && Array.isArray(obj.email.to) ? obj.email : keepEmail;
    if (obj.email && Array.isArray(obj.email.to) && obj.email.to.length) state.email.to = obj.email.to.slice();
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
      h("p", { text: "Settings, recipients, the history in this browser and the last brief, in one file." }),
      h("div", { class: "actions" },
        h("button", { class: "btn ghost", onclick: () => S.download("daily-brief-backup-" + today() + ".json", JSON.stringify({ db_backup: 1, version: E.VERSION, state: state, history: history }) + "\n", "application/json") }, "Back up all data"),
        h("button", { class: "btn ghost", onclick: () => file.click() }, "Restore from file"))));
    if (desktop) {
      add(sec, h("div", { class: "card" }, h("h2", { text: "Desktop app" }),
        h("p", null, "Your data folder: ", h("code", { text: desktop.data_folder || "" })),
        h("p", { class: "hint", text: "It holds config.json (saved for scheduled runs), ledger.json (the history), smtp.json (mail settings) and the briefs folder." })));
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
    st.config = E.merge(E.DEFAULTS, obj.state.config);
    st.email = { to: Array.isArray(st.email && st.email.to) ? st.email.to.filter(x => typeof x === "string") : [],
      from_name: typeof (st.email && st.email.from_name) === "string" ? st.email.from_name : "" };
    if (st.brief && (typeof st.brief !== "object" || !Array.isArray(st.brief.categories))) st.brief = null;
    state = st;
    history = E.cleanLedger(obj.history);
    save();
    saveHistory();
    toast("Restored.");
    show("setup");
  }

  // ------------------------------------------------------------ Help
  function renderHelp(sec) {
    const proj = S.projectUrl();
    add(sec, h("div", { class: "intro" }, h("h1", { text: "How the Daily Brief works" })));
    add(sec, h("div", { class: "card prose" },
      h("h2", { text: "Four ways to use it" }),
      h("ol", null,
        h("li", null, h("b", { text: "Your GitHub copy. " }), "A private copy of the project runs every morning on GitHub's servers: it collects the news from Google News and publisher feeds, builds the newsletter and emails it, or posts it as a GitHub issue. Free services only. Step 4 walks through it."),
        h("li", null, h("b", { text: "This web page. " }), "Runs the setup interview, edits your categories, previews and exports the newsletter, and builds the AI prompt. Nothing to install."),
        h("li", null, h("b", { text: "The desktop app. " }), "Download the project from GitHub (Code, Download ZIP), unzip it, and double-click Start-Windows.bat, Start-Mac.command or start-linux.sh. It opens this same app with live news from Google News and publisher feeds, the no-repeat history on disk, and email sending. It needs Python 3.9 or newer from python.org, and no account or key."),
        h("li", null, h("b", { text: "An AI assistant. " }), "Claude, ChatGPT, Gemini or Grok runs the interview and writes the brief from a web search, adding a Lead Analysis.")),
      proj ? h("p", null, "Project page and download: ", h("a", { href: proj, target: "_blank", rel: "noopener", text: proj.replace("https://", "") }), " | ",
        h("a", { href: proj + "/issues/new", target: "_blank", rel: "noopener", text: "report a problem or suggest an idea" })) : null,
      h("h2", { text: "Why this page cannot fetch the news" }),
      h("p", { text: "Browsers only let a page read another site when that site allows it. Google News and most publisher feeds do not, so a web page cannot read them. The desktop app reads them from your own computer, where that rule does not apply." }),
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
      h("p", { text: "No account and no tracking. Settings, recipients and the history stay in this browser, or in your data folder when you use the desktop app. The desktop app sends your search words to Google News and fetches the feeds you list; mail goes through the provider you set up. The AI prompt never includes your email address." }),
      h("h2", { text: "Limits" }),
      h("ul", null,
        h("li", { text: "Desktop briefs show headlines and short feed summaries. Google News gives no summary, so those stories show the headline only." }),
        h("li", { text: "Google News links open through a Google redirect page." }),
        h("li", { text: "AI assistants can still make mistakes. The prompt requires links from a live search; check a link before you act on a story." })),
      h("p", { class: "hint", text: "Daily Brief " + E.VERSION + ". Free and open source under the MIT licence." })));
  }

  const RENDER = { setup: renderSetup, categories: renderCategories, brief: renderBrief, email: renderEmail, ai: renderAi, settings: renderSettings, help: renderHelp };

  // ------------------------------------------------------------ start
  document.querySelectorAll("#tabs button").forEach(b => b.addEventListener("click", () => show(b.getAttribute("data-tab"))));
  modebar();
  show(state.tab || "setup");
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
  });
  if ("serviceWorker" in navigator && location.protocol === "https:") {
    navigator.serviceWorker.register("sw.js").catch(() => { /* offline support is optional */ });
  }
  window.DB_APP = { show: show, state: () => state, history: () => history, isDesktop: () => !!desktop };
})();
