/* Shinnecock Gate Clock — service worker.
   Bump CACHE when you change any file; the new version installs on the next
   online visit and takes over immediately. */
var CACHE = "gateclock-v12";

/* How long to wait on the network before giving up and drawing the cached app.
   A marginal signal can leave a fetch hanging far longer than a boater will
   stand there holding a phone. */
var NAV_TIMEOUT = 1200;

var ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-512.png",
  "./icons/favicon-32.png"
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(ASSETS); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.map(function (k) {
          return k === CACHE ? null : caches.delete(k);
        }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;

  var url;
  try { url = new URL(req.url); } catch (err) { return; }

  var sameOrigin = url.origin === self.location.origin;
  var isFont = url.host === "fonts.googleapis.com" || url.host === "fonts.gstatic.com";
  if (!sameOrigin && !isFont) return;

  /* The page itself: try the network, but never make the user wait on it.
     Plain cache-first served a stale app after an update; plain network-first
     hung for 10-15s on a weak signal. So: race the network against a short
     timer, and hand over the cached app the moment the timer wins. The fetch
     keeps running either way and refreshes the cache, so an update is still
     never more than one open away. */
  if (req.mode === "navigate" || (sameOrigin && url.pathname.slice(-5) === ".html")) {
    e.respondWith(
      caches.open(CACHE).then(function (cache) {
        return cache.match(req, { ignoreSearch: true }).then(function (cached) {
          var net = fetch(req).then(function (res) {
            if (res && res.ok) cache.put(req, res.clone()).catch(function () {});
            return res;
          });
          e.waitUntil(net.catch(function () {}));   /* let it finish caching regardless */

          if (!cached) {                            /* nothing stored yet — we must wait */
            return net.catch(function () {
              return cache.match("./index.html").then(function (h) {
                return h || cache.match("./");
              });
            });
          }
          return Promise.race([
            net.catch(function () { return cached; }),
            new Promise(function (resolve) {
              setTimeout(function () { resolve(cached); }, NAV_TIMEOUT);
            })
          ]);
        });
      })
    );
    return;
  }

  /* Everything else (icons, manifest, fonts): cache first, refresh in background. */
  e.respondWith(
    caches.open(CACHE).then(function (cache) {
      return cache.match(req).then(function (hit) {
        var net = fetch(req).then(function (res) {
          if (res && (res.ok || res.type === "opaque")) {
            cache.put(req, res.clone()).catch(function () {});
          }
          return res;
        }).catch(function () {
          if (hit) return hit;
          if (req.mode === "navigate") return cache.match("./index.html");
          return Response.error();
        });
        return hit || net;
      });
    })
  );
});
