#!/usr/bin/env python3
"""Rebuild ../index.html from the template and the encoded tide table.

  shinnecock.tpl.html + encoded.txt  ->  ../index.html

Run from this folder:  python3 build.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT.parent

# ---- 1. inject the tide table into the template -----------------------------
t0, enc = (ROOT / "encoded.txt").read_text().split("\n")[:2]
src = (ROOT / "shinnecock.tpl.html").read_text()
src = src.replace("__T0__", t0.strip()).replace("__ENC__", enc.strip())
assert "__T0__" not in src and "__ENC__" not in src, "data injection failed"

# ---- 2. split head / body ---------------------------------------------------
MARK = '</style>\n\n<div class="wrap">'
assert MARK in src, "split marker not found"
head, rest = src.split(MARK, 1)
head += "</style>"
body = '<div class="wrap">' + rest

# the display face is the only one without a real fallback stack
head = head.replace('"Archivo",sans-serif',
                    '"Archivo","Helvetica Neue",Helvetica,Arial,sans-serif')

FOOT = """<footer class="foot">
    <span>Locks Open? v3 &middot; tide table 1&nbsp;Sep&nbsp;2026 &ndash; 31&nbsp;Dec&nbsp;2028</span>
    <span id="swstate">Checking device storage&hellip;</span>
  </footer>"""
assert '<div id="buildinfo"></div>' in body, "buildinfo placeholder missing"
body = body.replace('<div id="buildinfo"></div>', FOOT, 1)

EXTRA_CSS = """
<style>
/* --- standalone / PWA additions (not present in the hosted artifact) --- */
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
  var SAVED = "Saved to this device \\u2014 works with no signal";
  if (!("serviceWorker" in navigator)) { say("This browser can't store the app offline.", false); return; }
  say(navigator.serviceWorker.controller ? SAVED : "Saving to this device\\u2026 keep a connection for a moment",
      !!navigator.serviceWorker.controller);
  window.addEventListener("load", function(){
    navigator.serviceWorker.register("./sw.js").then(function(reg){
      if (navigator.serviceWorker.controller) say(SAVED, true);
      reg.addEventListener("updatefound", function(){
        var w = reg.installing; if (!w) return;
        w.addEventListener("statechange", function(){ if (w.state === "activated") say(SAVED, true); });
      });
    }).catch(function(){
      say("Couldn't save offline \\u2014 needs an https:// address, not a local file.", false);
    });
  });
})();
</script>"""

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Predicts when the Shinnecock Canal tide gates are open or closed, from NOAA Sandy Hook high water. Works with no signal.">
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
{extra}
</head>
<body>
{body}
{swjs}
</body>
</html>
"""

doc = SHELL.format(head=head, extra=EXTRA_CSS, body=body, swjs=SW_JS)
(OUT / "index.html").write_text(doc)

print("wrote ../index.html  %d bytes" % len(doc))
print("remember to bump CACHE in ../sw.js")
