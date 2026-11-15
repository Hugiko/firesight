/* FireSight offline support: cache the app shell, data and media; never cache the live API. */
const CACHE = "firesight-v5";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png",
  "data/analytics.json", "data/tests.json", "data/investigations.json", "data/meta.json", "data/scenarios.json",
  "data/timeline.json", "data/earth.json", "data/gallery.json", "data/graph.json", "data/publications.json",
  "data/similarity.json", "data/summaries.json", "media/space/earth.jpg", "media/space/moon.jpg", "media/space/mars.jpg",
  "media/space/earth-day.jpg", "media/space/earth-night.jpg"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin || u.pathname.includes("/api/")) return;
  const immutable = u.pathname.includes("/assets/") || u.pathname.includes("/media/");
  e.respondWith(caches.open(CACHE).then(async (c) => {
    if (immutable) { // hashed bundles and images never change: cache first
      const hit = await c.match(e.request);
      if (hit) return hit;
      const r = await fetch(e.request); if (r.ok) c.put(e.request, r.clone()); return r;
    }
    try { // page and data: network first, so a redeploy is picked up immediately
      const r = await fetch(e.request); if (r.ok) c.put(e.request, r.clone()); return r;
    } catch {
      return (await c.match(e.request, { ignoreSearch: true })) || (await c.match("index.html")) || Response.error();
    }
  }));
});
