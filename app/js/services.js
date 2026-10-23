/* Daily Brief services: the desktop app connection, saving files, the
   clipboard and browser storage. Everything else lives in engine.js. */
(function (root) {
  "use strict";

  const STORE_KEY = "db.state.v1";
  const LEDGER_KEY = "db.history.v1";

  function key() {
    const m = document.querySelector('meta[name="db-key"]');
    return m ? m.getAttribute("content") || "" : "";
  }

  /* Calls the desktop app on this computer. Only works when the page was
     opened by the desktop launcher, which writes a fresh key into it. */
  async function api(path, body) {
    const opts = { method: body === undefined ? "GET" : "POST", headers: { "X-Brief-Key": key() } };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok) {
      const err = new Error((data && data.error) || ("The desktop app answered " + res.status));
      err.details = data;
      throw err;
    }
    return data;
  }

  async function detectDesktop() {
    if (!key() || location.protocol === "file:") return null;
    try { return await api("/api/health"); } catch (e) { return null; }
  }

  function readStore(k, fallback) {
    try {
      const raw = localStorage.getItem(k);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeStore(k, value) {
    try {
      localStorage.setItem(k, JSON.stringify(value));
      return true;
    } catch (e) {
      return false;
    }
  }

  function removeStore(k) {
    try { localStorage.removeItem(k); } catch (e) { /* storage blocked */ }
  }

  function storageBytes() {
    let n = 0;
    try {
      for (const k of [STORE_KEY, LEDGER_KEY]) n += (localStorage.getItem(k) || "").length;
    } catch (e) { n = 0; }
    return n;
  }

  /* Saves a file to the device: Downloads on a computer or Android, the
     Files sheet on an iPad or iPhone. */
  function download(name, text, mime) {
    const blob = new Blob([text], { type: (mime || "text/plain") + ";charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1500);
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
      ta.remove();
      return ok;
    }
  }

  /* Copies the newsletter as formatted content, so pasting into a new email
     in Gmail, Outlook or Apple Mail keeps the layout. Browsers without rich
     clipboard support get the plain-text version; the newsletter HTML is never
     put into this page. Returns "rich", "text" or "". */
  async function copyRich(html, text) {
    try {
      if (root.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
        await navigator.clipboard.write([new ClipboardItem({
          "text/html": new Blob([html], { type: "text/html" }),
          "text/plain": new Blob([text], { type: "text/plain" })
        })]);
        return "rich";
      }
    } catch (e) { /* fall back to plain text */ }
    return (await copyText(text)) ? "text" : "";
  }

  /* On GitHub Pages the address names the project, so feedback links can
     point at its issues page without hard-coding an account name. */
  function projectUrl() {
    const host = location.hostname;
    const m = /^([a-z0-9-]+)\.github\.io$/i.exec(host);
    const seg = location.pathname.split("/").filter(Boolean)[0];
    return m && seg ? "https://github.com/" + m[1] + "/" + seg : "";
  }

  root.DB_SERVICES = {
    STORE_KEY, LEDGER_KEY, key, api, detectDesktop, readStore, writeStore, removeStore, storageBytes,
    download, copyText, copyRich, projectUrl
  };
})(typeof self !== "undefined" ? self : this);
