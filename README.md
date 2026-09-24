# Shinnecock Gate Clock

A one-page web app that predicts when the Shinnecock Canal tide gates are open or
closed, so you know whether you're looking at a 6-knot flush or a wait at the lock.

It installs to a phone home screen. Tide predictions are fetched live from NOAA on
every open, so the app never needs re-cutting by hand. The last good table is kept
on the device, so a dead spot or a slow cold start shows the previous answer rather
than a blank screen.

---

## What's in here

| File | What it is |
| --- | --- |
| `index.html` | The whole app: markup, styles, logic, the sponsor logo, and a small fallback tide sample. No build step. |
| `manifest.webmanifest` | Makes it installable — name, icons, standalone display. |
| `sw.js` | Service worker. Network-first for the page (so an update is never more than one load away), cache-first for icons. Either way the app opens with no signal. |
| `icons/` | App icons (192, 512, maskable, favicon). |
| `.nojekyll` | Stops GitHub Pages running Jekyll over the files. |
| `sponsor/logo.png` | The sponsor mark. Swap this file and two lines in `tools/build.py` to change sponsor. |
| `tools/` | Scripts to rebuild `index.html`. Not served. |

Every path in the app is relative, so it works at any URL — repo root, a subpath,
a custom domain, doesn't matter.

---

## Deploy on GitHub Pages

**Before you start:** GitHub Pages on a **private** repo requires a paid plan
(Pro/Team/Enterprise). On the free plan the repo has to be **public**. Nothing here is
sensitive — it's tide math and public NOAA data — but that's your call to make.

1. Put these files in the repo root (`index.html` must be at the top level, not in a
   subfolder). Easiest path in a browser: **Add file → Upload files**, drag the whole
   contents in, commit to `main`.
2. Repo **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to `Deploy from a branch`, branch
   `main`, folder `/ (root)`. Save.
4. Wait a minute or two. The page banner shows your URL:
   `https://<your-account>.github.io/<repo-name>/`

If you'd rather not have it at the repo root, put everything in a `docs/` folder and
pick `/docs` as the folder in step 3 instead.

### Confirm it actually installed offline

Open the URL on your phone. The line at the very bottom of the page tells you the truth:

- *"Saving to this device… keep a connection for a moment"* — first visit, not cached yet.
- *"✓ Saved to this device — works with no signal"* — done. Turn on airplane mode and
  reload to prove it.

Service workers only run over `https://`. GitHub Pages is https, so this works — but
opening `index.html` as a local file will **not** cache offline, and the footer will say so.

### Add to your home screen

Chrome on Android: **⋮ → Add to Home screen** (newer builds say *Install app*).
Safari on iPhone: **Share → Add to Home Screen**.

Launched from the icon it runs without browser chrome, like an app.

---

## When you change a file

Bump `CACHE` in `sw.js` — `gateclock-v1` → `gateclock-v2`. Phones that already installed
the app pick up the new version on their next visit with a connection. Skip this and they
keep serving the old cached copy indefinitely.

---

## Changing the sponsor

The sponsor appears twice: on the opening card, and as a persistent credit above the
About section. To change it:

1. Replace `sponsor/logo.png` — transparent PNG, brand colour, about 440px wide.
2. Edit `SPONSOR_NAME` and `SPONSOR_URL` near the top of `tools/build.py`.
3. `cd tools && python3 build.py`, bump `CACHE` in `sw.js`, push.

The logo is inlined into the page as a data URI, so there is no extra request and it
shows instantly on the opening card.

## Measuring usage

Sign in to Cloudflare, add this site under **Web Analytics**, copy the token, and put
it in `tools/cf_token.txt`. Rebuild and the beacon tag is emitted into the page. With
no token file, nothing is emitted and no third party sees your visitors.

You need these numbers before any sponsor conversation is worth having.

## The algorithm

- Gates **close 3 h 30 m before** high water at Sandy Hook, NJ.
- Gates **open 2 h 30 m after** high water at Sandy Hook, NJ.

That's a six-hour closed window and roughly 6 h 25 m open, alternating with the tide.
Reference station is NOAA **8531680 Sandy Hook, NJ**, heights in feet MLLW.

**Gates open** → water runs north to south through the gate openings, building to about
6 knots. **Gates closed** → flat water, but a single lock chamber and a wait for
opposing traffic.

### What this app does not know

It is a prediction from a tide table, not an observation of the gates.

- Wind and storm surge move real tides by an hour or more.
- Mechanical failure and county maintenance override the schedule outright. The canal
  has closed to all traffic on short notice before.
- The 3:30/2:30 offsets are local knowledge that **has not been checked against logged
  gate operations**, and it has not been confirmed that Suffolk County DPW actually
  references Sandy Hook rather than a nearer station.

Not for navigation. Lock operator monitors **VHF 13**, **631-852-8299**.
