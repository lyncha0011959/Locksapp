/* Shinnecock Gate Clock — service worker.
   Bump CACHE when you change any file; the new version installs on the next
   online visit and takes over immediately. */
var CACHE = "gateclock-v7";

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

  /* The page itself: NETWORK FIRST. Cache-first meant a viewer kept seeing the
     old app for a load or more after an update, with no way to tell. Online you
     now always get the current page; the cache catches you the moment there is
     no signal, which is the part that actually matters on the water. */
  if (req.mode === "navigate" || (sameOrigin && url.pathname.slice(-5) === ".html")) {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
        }
        return res;
      }).catch(function () {
        return caches.open(CACHE).then(function (c) {
          return c.match(req, { ignoreSearch: true }).then(function (hit) {
            if (hit) return hit;
            return c.match("./index.html").then(function (h2) {
              return h2 || c.match("./");
            });
          });
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
