/* Offline support for the app shell. Files come from the network first, so a
   connected device always gets the newest version; the cached copy is used only
   when offline. Every request asks the server whether the file changed
   ("no-cache"), because GitHub Pages lets browsers keep files for 10 minutes.
   Bump VERSION when the file list changes. */
const VERSION = "db-v0.9.0";
const FILES = ["./", "index.html", "css/style.css", "js/engine.js", "js/newsletter.js", "js/collect.js", "js/ideas.js", "js/services.js", "js/app.js",
  "data/library.js", "data/prompts.js", "data/sample.js", "data/icons.js", "data/calendars.js", "manifest.webmanifest", "icon.svg", "icon-180.png",
  "icon-192.png", "icon-512.png", "icon-maskable-512.png"];
self.addEventListener("install", e => e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener("activate", e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin || url.pathname.indexOf("/api/") >= 0) return;
  e.respondWith(fetch(new Request(e.request.url, { cache: "no-cache", credentials: "same-origin" })).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); }
    return res;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(hit => hit || caches.match("index.html"))));
});
