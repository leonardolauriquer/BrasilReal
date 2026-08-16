/* Brasil Real service worker. BUILD is stamped at `npm run build`. */
const BUILD = "__BR_BUILD__";
const CACHE = `brasil-real-${BUILD}`;

const PRECACHE = [
  "/",
  "/index.html",
  "/offline.html",
  "/manifest.webmanifest",
  "/icon.svg",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/version.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      await Promise.all(
        PRECACHE.map(async (url) => {
          try {
            const response = await fetch(new Request(url, { cache: "reload" }));
            if (response.ok) await cache.put(url, response);
          } catch {
            /* skip missing optional assets — SW must still activate */
          }
        }),
      );
    })(),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)));
      await self.clients.claim();
      const clients = await self.clients.matchAll({ type: "window" });
      for (const client of clients) {
        client.postMessage({ type: "BR_UPDATED", build: BUILD, builtAt: "__BR_BUILT_AT__" });
      }
    })(),
  );
});

function isHtmlRequest(request) {
  if (request.mode === "navigate") return true;
  const accept = request.headers.get("accept") || "";
  return accept.includes("text/html");
}

function shouldBypassCache(url) {
  const path = url.pathname;
  return path.endsWith("/sw.js") || path.endsWith("/version.json");
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (shouldBypassCache(url)) {
    event.respondWith(fetch(request, { cache: "no-store" }));
    return;
  }

  if (isHtmlRequest(request)) {
    event.respondWith(
      (async () => {
        try {
          const fresh = await fetch(request, { cache: "no-store" });
          if (fresh.ok) {
            const cache = await caches.open(CACHE);
            cache.put("/index.html", fresh.clone());
          }
          return fresh;
        } catch {
          return (
            (await caches.match("/index.html")) ||
            (await caches.match("/offline.html")) ||
            new Response("Atlas offline", { status: 503, headers: { "Content-Type": "text/plain" } })
          );
        }
      })(),
    );
    return;
  }

  event.respondWith(
    (async () => {
      const cached = await caches.match(request);
      if (cached) return cached;
      try {
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(CACHE);
          cache.put(request, response.clone());
        }
        return response;
      } catch {
        return cached || new Response("", { status: 504 });
      }
    })(),
  );
});
