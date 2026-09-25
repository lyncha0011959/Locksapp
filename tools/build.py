#!/usr/bin/env python3
"""Build both deliverables from one source of truth.

  shinnecock.tpl.html + seed.txt + sponsor/logo.png
        -> shinnecock.html       (artifact body, layout preview only)
        -> gateclock/index.html  (the live app)

Tide data is fetched from NOAA at runtime; seed.txt is only a first-paint
fallback and what the preview artifact runs on.

Run:  python3 build.py
"""
import base64
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT.parent
VERSION = "v10"

# ---- sponsor -----------------------------------------------------------------
# To change sponsor: drop a new logo at gateclock/sponsor/logo.png (transparent
# PNG, brand colour, ~440px wide) and edit the two lines below. Nothing else.
SPONSOR_NAME = "Hampton Jitney"
SPONSOR_URL = "https://www.hamptonjitney.com/"

logo_b64 = base64.b64encode((OUT / "sponsor" / "logo.png").read_bytes()).decode()
SPONSOR_LOGO = "data:image/png;base64," + logo_b64

# ---- 1. inject data and sponsor ---------------------------------------------
t0, enc = (ROOT / "seed.txt").read_text().split("\n")[:2]
src = (ROOT / "shinnecock.tpl.html").read_text()
src = (src.replace("__T0__", t0.strip())
          .replace("__ENC__", enc.strip())
          .replace("__SPONSOR_LOGO__", SPONSOR_LOGO)
          .replace("__SPONSOR_NAME__", SPONSOR_NAME)
          .replace("__SPONSOR_URL__", SPONSOR_URL))
for token in ("__T0__", "__ENC__", "__SPONSOR_LOGO__", "__SPONSOR_NAME__", "__SPONSOR_URL__"):
    assert token not in src, "unreplaced placeholder: " + token

# ---- 2. split head / body ----------------------------------------------------
MARK = '</style>\n\n<div class="splash"'
assert MARK in src, "split marker not found"
head, rest = src.split(MARK, 1)
head += "</style>"
body = '<div class="splash"' + rest

head = head.replace('"Archivo",sans-serif',
                    '"Archivo","Helvetica Neue",Helvetica,Arial,sans-serif')

FOOT = """<footer class="foot">
    <span>Shinnecock Locks &middot; Locks Open? """ + VERSION + """</span>
    <span id="swstate">Checking device storage&hellip;</span>
  </footer>"""
assert '<div id="buildinfo"></div>' in body, "buildinfo placeholder missing"
body = body.replace('<div id="buildinfo"></div>', FOOT, 1)

EXTRA_CSS = """
<style>
/* --- standalone / PWA additions (not present in the preview artifact) --- */
:root{color-scheme:light dark}
html,body{margin:0;padding:0}
img{max-width:100%}
[hidden]{display:none!important}
body{padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}
.foot{
  display:flex;flex-direction:column;gap:3px;padding-top:14px;
  border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:11px;letter-spacing:.04em;color:var(--ink-3);
}
.foot #swstate{color:var(--ink-2)}
.foot #swstate.ready::before{content:"\\2713\\00a0"}
</style>"""

SW_JS = """
<script>
(function(){
  var el = document.getElementById("swstate");
  function say(t, ok){ if(!el) return; el.textContent = t; el.className = ok ? "ready" : ""; }
  var SAVED = "App shell saved to this device";
  if (!("serviceWorker" in navigator)) { say("This browser can't store the app shell.", false); return; }
  say(navigator.serviceWorker.controller ? SAVED : "Saving app shell\\u2026", !!navigator.serviceWorker.controller);
  window.addEventListener("load", function(){
    navigator.serviceWorker.register("./sw.js").then(function(reg){
      if (navigator.serviceWorker.controller) say(SAVED, true);
      reg.addEventListener("updatefound", function(){
        var w = reg.installing; if (!w) return;
        w.addEventListener("statechange", function(){ if (w.state === "activated") say(SAVED, true); });
      });
    }).catch(function(){
      say("Couldn't store the app shell \\u2014 needs an https:// address.", false);
    });
  });
})();
</script>"""

# ---- 3. usage measurement ----------------------------------------------------
# Put your Cloudflare Web Analytics token in cf_token.txt and rebuild. Until
# then nothing is emitted, so no third party sees your users.
token_file = ROOT / "cf_token.txt"
if token_file.exists() and token_file.read_text().strip():
    ANALYTICS = ('\n<!-- Cloudflare Web Analytics: no cookies, no consent banner -->\n'
                 '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
                 'data-cf-beacon=\'{"token": "%s"}\'></script>' % token_file.read_text().strip())
else:
    ANALYTICS = ("\n<!-- Usage measurement: add your Cloudflare Web Analytics token to\n"
                 "     cf_token.txt and rebuild, and the beacon tag lands here. -->")

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Is the Shinnecock Canal lock open or closed? Live gate status, next change, and passage routing for the Shinnecock Locks.">
<link rel="manifest" href="./manifest.webmanifest">
<meta name="theme-color" content="#E6ECEE" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#07131A" media="(prefers-color-scheme: dark)">
<link rel="icon" href="./icons/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="./icons/icon-192.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Locks Open?">
{head}
{extra}{analytics}
</head>
<body>
{body}
{swjs}
</body>
</html>
"""

doc = SHELL.format(head=head, extra=EXTRA_CSS, body=body, swjs=SW_JS, analytics=ANALYTICS)
(OUT / "index.html").write_text(doc)
(OUT / ".nojekyll").write_text("")

print("shinnecock.html      %6d bytes  (preview artifact)" % len(src))
print("gateclock/index.html %6d bytes  (live app, %s)" % (len(doc), VERSION))
print("sponsor              %s  (%.1f KB inline)" % (SPONSOR_NAME, len(logo_b64) / 1024))
print("analytics            %s" % ("Cloudflare token present" if token_file.exists() else "not configured"))
