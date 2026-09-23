/* Service worker Compagnon — network-first pour HTML/JS (évite Actions rapides fantômes).
 * L'install PWA native exige souvent HTTPS ; sur .10 préférer le raccourci --app=
 * (voir desktop/Install-CompagnonShortcut.ps1).
 */
const CACHE = "lbg-compagnon-shell-v5";
const PRECACHE = ["/manifest.webmanifest", "/pwa-icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  if (event.data === "SKIP_WAITING") self.skipWaiting();
  if (event.data === "CLEAR_CACHES") {
    event.waitUntil(
      caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
    );
  }
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;

  const isShell =
    url.pathname === "/" ||
    url.pathname.endsWith(".html") ||
    url.pathname.endsWith(".js") ||
    url.pathname.endsWith(".css");

  // HTML/JS/CSS : toujours réseau d'abord (pas de shell obsolète)
  if (isShell) {
    event.respondWith(
      fetch(req)
        .then((res) => res)
        .catch(() => caches.match(req).then((hit) => hit || caches.match("/")))
    );
    return;
  }

  event.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        if (res.ok) {
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() => caches.match(req))
  );
});
