// Runs one engine or newsletter function for the Python parity tests.
// Usage: node tests/js_bridge.js < request.json, where the request is
// {"fn": "selectBrief", "args": [...]}. Prints the JSON result.
"use strict";
const E = require("../app/js/engine.js");
const N = require("../app/js/newsletter.js");
const C = require("../app/js/collect.js");
let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", d => { input += d; });
process.stdin.on("end", () => {
  const reqs = JSON.parse(input);
  const out = (Array.isArray(reqs) ? reqs : [reqs]).map(req => {
    const fn = req.fn === "render" ? N.render : req.fn === "subjectLine" ? N.subjectLine
      : req.fn.indexOf("collect.") === 0 ? C[req.fn.slice(8)] : E[req.fn];
    if (typeof fn !== "function") return { error: "no function " + req.fn };
    try {
      const v = fn.apply(null, req.args || []);
      return { value: v === undefined ? null : v };
    } catch (e) {
      return { error: String(e && e.message || e) };
    }
  });
  process.stdout.write(JSON.stringify(Array.isArray(reqs) ? out : out[0]));
});
