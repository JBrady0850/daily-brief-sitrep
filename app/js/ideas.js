/* Daily Brief countdown ideas: suggestions for the countdown question, picked from
   the categories a reader chose (most important first).

   Two kinds:
   - fixed dates that follow a published rule (Election Day, Thanksgiving, Tax Day,
     the Atlantic hurricane season, Federal Benefits Open Season, Medicare Open
     Enrollment), worked out here;
   - personal dates (a retirement, a trip, a move), where the reader picks the day
     and the milestones are set back from it.

   An idea that fits only some readers is never suggested on its own: Medicare Open
   Enrollment (people on Medicare) always waits in the "More ideas" list, and the
   hurricane season does too unless the reader's state is on the Atlantic or Gulf coast.

   Milestones are suggestions the reader can change or remove. Rules checked on
   2026-10-25: Election Day is the Tuesday after the first Monday in November in
   even years (2 U.S.C. 7); Thanksgiving is the fourth Thursday in November
   (5 U.S.C. 6103); federal returns are due April 15, or the next business day when
   that is a weekend or a District of Columbia holiday such as Emancipation Day
   (April 16) (IRS); the Atlantic hurricane season runs June 1 to November 30
   (NOAA); Medicare Open Enrollment runs October 15 to December 7 (Medicare.gov);
   Social Security takes an application up to 4 months ahead (SSA); an agency
   needs at least 60 days to process a federal retirement application (OPM).
   Checked on 2026-10-26: Federal Benefits Open Season (FEHB, PSHB, FEDVIP,
   FSAFEDS) runs from the Monday of the second full workweek in November through
   the Monday of the second full workweek in December (5 CFR 890.301(f)), which is
   the second Monday of each month (November 9 to December 14, 2026); FSAFEDS
   elections do not carry over and must be made each year (FSAFEDS). */
(function (root, factory) {
  const node = typeof module === "object" && module.exports;
  const api = factory(node ? require("./engine.js") : root.DB_ENGINE);
  if (node) module.exports = api;
  else root.DB_IDEAS = api;
})(typeof self !== "undefined" ? self : this, function (E) {
  "use strict";

  const DAY = 86400000;
  const MAX = 4;  // ideas shown at once

  function ms(d) { return Date.parse(d + "T00:00:00Z"); }
  function day(t) { return E.isoZ(t).slice(0, 10); }
  function shift(d, days) { return day(ms(d) + days * DAY); }
  function ymd(y, m, d) { return y + "-" + E.pad2(m) + "-" + E.pad2(d); }
  function weekday(d) { return new Date(ms(d)).getUTCDay(); }  // 0 Sunday

  /* The n-th given weekday (0 Sunday) of a month. */
  function nthWeekday(y, m, wd, n) {
    const first = ymd(y, m, 1);
    return shift(first, ((wd - weekday(first) + 7) % 7) + 7 * (n - 1));
  }

  function electionDay(y) { return shift(nthWeekday(y, 11, 1, 1), 1); }  // Tuesday after the first Monday
  function thanksgiving(y) { return nthWeekday(y, 11, 4, 4); }

  /* Federal Benefits Open Season: [first day, last day]. The Monday of the second full
     workweek is always the second Monday, since the first Monday falls by the 7th. */
  function openSeason(y) { return [nthWeekday(y, 11, 1, 2), nthWeekday(y, 12, 1, 2)]; }

  // States on the Atlantic or Gulf coast, where the hurricane season is everyone's business.
  const STORM_COAST = ["TX", "LA", "MS", "AL", "FL", "GA", "SC", "NC", "VA", "MD", "DE", "NJ", "NY", "CT", "RI", "MA", "NH", "ME"];

  /* April 15, moved to the next business day past weekends and Emancipation Day. */
  function taxDay(y) {
    const em = ymd(y, 4, 16);
    const emObserved = weekday(em) === 6 ? shift(em, -1) : weekday(em) === 0 ? shift(em, 1) : em;
    let d = ymd(y, 4, 15);
    while (weekday(d) === 0 || weekday(d) === 6 || d === emObserved) d = shift(d, 1);
    return d;
  }

  /* The next date from a yearly rule that is still ahead of today (today counts). */
  function next(rule, today, every) {
    const y = Number(today.slice(0, 4));
    for (let k = 0; k <= 4; k += every || 1) { const d = rule(y + k); if (d >= today) return d; }
    return rule(y + 4);
  }

  // Each idea: id, label, about (one line), the category ids it fits, and either
  // fixed(today) -> {date, start, label?, milestones?} or offsets for a date the reader picks.
  // optional(reader) -> true keeps an idea out of the suggestions (it stays in "More ideas").
  const IDEAS = [
    { id: "federal-retirement", label: "Days to retirement", about: "Your federal retirement date, with the paperwork on the way.",
      cats: ["federal-retirement", "federal-workforce", "federal-pay"],
      offsets: [[-365, "Ask HR for a retirement estimate"], [-180, "Review TSP withdrawals and FEHB choices"],
        [-120, "Apply for Social Security if it starts then (up to 4 months ahead)"],
        [-90, "Give HR your retirement application (agencies need at least 60 days)"], [-14, "Check final leave and the last paycheck"]] },
    { id: "retirement", label: "Days to retirement", about: "Your retirement date, with the decisions on the way.",
      cats: ["retirement-planning"],
      offsets: [[-365, "Check the retirement budget and savings"], [-180, "Decide when to start Social Security and Medicare"],
        [-120, "Apply for Social Security if it starts then (up to 4 months ahead)"], [-60, "Give notice at work"]] },
    { id: "open-season", label: "Days to Federal Benefits Open Season",
      about: "FEHB, PSHB, FEDVIP and FSAFEDS: the second Monday of November to the second Monday of December.",
      cats: ["federal-retirement", "federal-workforce", "federal-pay"],
      fixed: t => {
        const y = Number(t.slice(0, 4));
        const [open, close] = openSeason(y);
        if (t >= open && t < close) {
          return { label: "Days left in Federal Benefits Open Season", date: close, start: open,
            milestones: [[-14, "Compare health, dental and vision plans for next year"],
              [-7, "Re-enroll in FSAFEDS if you use it (it does not carry over)"], [-2, "Make any change on your benefits site"]] };
        }
        const next = t < open ? open : openSeason(y + 1)[0];
        return { date: next, start: t, milestones: [[-14, "Read next year's plan changes and premiums"]] };
      } },
    { id: "election", label: "Days to Election Day", about: "The next federal general election.",
      cats: ["politics", "local-government", "us-news"],
      fixed: t => {
        const y = Number(t.slice(0, 4));
        const even = y % 2 === 0 && electionDay(y) >= t ? y : y + (y % 2 === 0 ? 2 : 1);
        return { date: electionDay(even), start: t, milestones: [] };
      } },
    { id: "hurricane", label: "Days to hurricane season", about: "The Atlantic and Gulf hurricane season, June 1 to November 30.",
      cats: ["local-weather", "severe-weather", "weather-outlook"],
      optional: reader => STORM_COAST.indexOf(E.stateCode(reader && reader.region)) < 0,
      fixed: t => {
        const y = Number(t.slice(0, 4));
        if (t >= ymd(y, 6, 1) && t < ymd(y, 11, 30)) {
          return { label: "Days left in hurricane season", date: ymd(y, 11, 30), start: ymd(y, 6, 1), milestones: [] };
        }
        const open = t < ymd(y, 6, 1) ? ymd(y, 6, 1) : ymd(y + 1, 6, 1);
        return { date: open, start: ymd(Number(open.slice(0, 4)) - 1, 12, 1),
          milestones: [[-30, "Check the emergency kit and evacuation plan"], [-14, "Review home and flood insurance"]] };
      } },
    { id: "medicare", label: "Days to Medicare Open Enrollment",
      about: "For people on Medicare: October 15 to December 7, when Medicare plans can change for next year.",
      cats: ["retirement-planning", "federal-retirement", "health-wellness"],
      optional: () => true,
      fixed: t => {
        const y = Number(t.slice(0, 4));
        if (t >= ymd(y, 10, 15) && t < ymd(y, 12, 7)) {
          return { label: "Days left in Medicare Open Enrollment", date: ymd(y, 12, 7), start: ymd(y, 10, 15),
            milestones: [[-21, "Compare plans for next year"], [-7, "Make any change"]] };
        }
        const open = t < ymd(y, 10, 15) ? ymd(y, 10, 15) : ymd(y + 1, 10, 15);
        return { date: open, start: t, milestones: [[-14, "Read your plan's changes for next year"]] };
      } },
    { id: "tax", label: "Days to Tax Day", about: "Federal returns are due April 15, or the next business day.",
      cats: ["personal-finance", "small-business"],
      fixed: t => {
        const d = next(taxDay, t);
        return { date: d, start: t, milestones: [["02-01", "Gather W-2s, 1099s and receipts"], [-30, "File, or ask for an extension"]] };
      } },
    { id: "thanksgiving", label: "Days to Thanksgiving", about: "The fourth Thursday in November.",
      cats: ["food-dining", "parenting-family"],
      fixed: t => ({ date: next(thanksgiving, t), start: t,
        milestones: [[-21, "Plan the menu and the guest list"], [-7, "Shop for groceries"], [-2, "Cook what can be made ahead"]] }) },
    { id: "trip", label: "Days to the trip", about: "A trip you are planning.",
      cats: ["travel", "outdoors"],
      offsets: [[-60, "Book travel and places to stay"], [-30, "Check IDs, passports and reservations"],
        [-7, "Check the forecast and pack"], [-1, "Check in and confirm"]] },
    { id: "move", label: "Days to moving day", about: "A move to a new home.",
      cats: ["housing", "home-garden"],
      offsets: [[-60, "Book movers or a truck"], [-30, "Set up utilities and change your address"], [-14, "Start packing"],
        [-2, "Confirm the movers and pack the essentials"]] },
    { id: "launch", label: "Days to the launch", about: "A product, shop or project going live.",
      cats: ["small-business", "open-source"],
      offsets: [[-30, "Finish the plan"], [-14, "Tell customers it is coming"], [-7, "Final test run"], [-1, "Last check"]] },
    { id: "school", label: "Days to the first day of school", about: "The start of a school year or term.",
      cats: ["education", "parenting-family"],
      offsets: [[-30, "Check supply lists and forms"], [-14, "Book checkups and buy supplies"], [-7, "Practice the morning routine"]] },
    { id: "exam", label: "Days to the exam", about: "A certification or licensing exam.",
      cats: ["career-skills", "cybersecurity", "cloud-infrastructure", "network-security"],
      offsets: [[-60, "Book the exam"], [-30, "Take a practice test"], [-7, "Review weak spots"], [-1, "Rest and check the location"]] },
    { id: "race", label: "Days to race day", about: "A run, ride or other event you are training for.",
      cats: ["health-wellness", "outdoors"],
      offsets: [[-21, "Longest training session"], [-14, "Start to taper"], [-1, "Lay out the gear"]] },
    { id: "draft", label: "Days to draft day", about: "Your fantasy league's draft.",
      cats: ["fantasy-sports"],
      offsets: [[-14, "Check injuries and rankings"], [-7, "Do a mock draft"], [-1, "Set your draft list"]] },
    { id: "season", label: "Days to the season opener", about: "The first game of the season you follow.",
      cats: ["nfl", "college-football", "nba", "college-basketball", "mlb", "nhl", "soccer", "golf", "motorsports", "tennis",
        "sports-headlines", "local-sports"],
      offsets: [] }
  ];

  /* Milestone dates for a target: kept only when they fall after today and before the target. */
  function milestones(list, target, today) {
    return (list || []).map(m => {
      const date = typeof m[0] === "number" ? shift(target, m[0]) : target.slice(0, 4) + "-" + m[0];
      return { date: date, label: m[1], note: "" };
    }).filter(m => E.isDateStr(m.date) && m.date > today && m.date < target);
  }

  /* An idea as the page shows it: label, about, the category it came from (or ""),
     whether its date is fixed, that date, and the milestone names. */
  function card(idea, from, today) {
    const o = { id: idea.id, label: idea.label, about: idea.about, from: from, fixed: !!idea.fixed };
    if (idea.fixed) {
      const f = idea.fixed(today);
      o.label = f.label || idea.label;
      o.date = f.date;
      o.steps = milestones(f.milestones, f.date, today).map(m => m.label);
    } else {
      o.steps = idea.offsets.map(m => m[1]);
    }
    return o;
  }

  const optional = (idea, reader) => typeof idea.optional === "function" && idea.optional(reader || {});
  const name = c => E.collapse(c && c.name) || (c && c.id) || "";

  /* Up to `limit` (default MAX) suggestions for the chosen categories, in the order of
     the categories. Ideas that fit only some readers are left for moreIdeas. */
  function ideasFor(categories, today, reader, limit) {
    const most = typeof limit === "number" && limit > 0 ? limit : MAX;
    const out = [];
    for (const c of categories || []) {
      const id = c && c.id;
      for (const idea of IDEAS) {
        if (out.length >= most || idea.cats.indexOf(id) < 0 || optional(idea, reader) ||
          out.some(o => o.id === idea.id || o.label === idea.label)) continue;
        out.push(card(idea, name(c), today));
      }
    }
    return out;
  }

  /* Every other idea, for the reader to pick from: first those that fit a chosen
     category (in the order of the categories), then the rest. */
  function moreIdeas(categories, today, reader, shown) {
    const skip = (shown || []).slice();
    const out = [];
    const take = (idea, from) => {
      if (skip.indexOf(idea.id) >= 0) return;
      skip.push(idea.id);
      out.push(card(idea, from, today));
    };
    for (const c of categories || []) for (const idea of IDEAS) if (idea.cats.indexOf(c && c.id) >= 0) take(idea, name(c));
    for (const idea of IDEAS) take(idea, "");
    return out;
  }

  function ideaById(id, today, from) {
    const idea = IDEAS.filter(i => i.id === id)[0];
    return idea ? card(idea, from || "", today) : null;
  }

  /* The countdown an idea makes: {label, date, start, milestones, idea}. `target` is the
     reader's own date for a personal idea and is ignored for a fixed one. Returns null
     for a date not after today. */
  function fill(id, target, today) {
    const idea = IDEAS.filter(i => i.id === id)[0];
    if (!idea) return null;
    if (idea.fixed) {
      const f = idea.fixed(today);
      return { label: f.label || idea.label, date: f.date, start: f.start < f.date ? f.start : today,
        milestones: milestones(f.milestones, f.date, today), idea: id };
    }
    if (!E.isDateStr(target) || target <= today) return null;
    return { label: idea.label, date: target, start: today, milestones: milestones(idea.offsets, target, today), idea: id };
  }

  return { IDEAS, MAX, STORM_COAST, electionDay, thanksgiving, taxDay, openSeason, ideasFor, moreIdeas, ideaById, fill };
});
