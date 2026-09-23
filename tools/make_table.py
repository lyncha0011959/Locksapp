#!/usr/bin/env python3
"""Pull Sandy Hook high waters from NOAA and write the encoded table.

    python3 make_table.py 20280101 20301231

Writes ../tools/encoded.txt, which build.py bakes into index.html.
Needs internet. No API key. Refuses to write a table that fails integrity checks.
"""
import datetime
import json
import pathlib
import sys
import urllib.request

STATION = "8531680"          # Sandy Hook, NJ
API = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
       "?product=predictions&application=shinnecock-gate-clock"
       "&begin_date={a}&end_date={b}&datum=MLLW&station=" + STATION +
       "&time_zone=gmt&units=english&interval=hilo&format=json")

HERE = pathlib.Path(__file__).resolve().parent


def d(s):
    return datetime.datetime.strptime(s, "%Y%m%d").date()


def fetch(a, b):
    """NOAA caps a single hilo request; walk the range in 1-year slices."""
    rows, cur = [], a
    while cur <= b:
        end = min(b, cur + datetime.timedelta(days=364))
        url = API.format(a=cur.strftime("%Y%m%d"), b=end.strftime("%Y%m%d"))
        print("  fetching %s .. %s" % (cur, end))
        with urllib.request.urlopen(url, timeout=60) as r:
            payload = json.load(r)
        if "predictions" not in payload:
            sys.exit("NOAA returned no predictions: %s" % payload)
        for p in payload["predictions"]:
            if p["type"] != "H":
                continue
            t = datetime.datetime.strptime(p["t"], "%Y-%m-%d %H:%M").replace(
                tzinfo=datetime.timezone.utc)
            rows.append((t, float(p["v"])))
        cur = end + datetime.timedelta(days=1)
    return rows


def check(rows):
    rows.sort(key=lambda r: r[0])
    seen, out = set(), []
    for r in rows:                       # slices overlap at the seams
        if r[0] not in seen:
            seen.add(r[0])
            out.append(r)
    gaps = [(out[i][0] - out[i - 1][0]).total_seconds() / 3600
            for i in range(1, len(out))]
    bad = [g for g in gaps if not 11.0 <= g <= 14.0]
    mean = sum(gaps) / len(gaps)
    print("  %d high waters, %s .. %s" % (len(out), out[0][0].date(), out[-1][0].date()))
    print("  gap min/max %.2f/%.2f h, mean %.4f h (M2 = 12.4206)" % (min(gaps), max(gaps), mean))
    if bad:
        sys.exit("FAILED: %d gaps outside 11-14 h — data is incomplete" % len(bad))
    if abs(mean - 12.4206) > 0.02:
        sys.exit("FAILED: mean interval %.4f h is off the semidiurnal period" % mean)
    print("  integrity checks passed")
    return out


def b36(n, w):
    s = ""
    while n:
        s = "0123456789abcdefghijklmnopqrstuvwxyz"[n % 36] + s
        n //= 36
    return s.rjust(w, "0")


def encode(rows):
    """4 base-36 chars per high water: 2 = minutes since the previous, 2 = tenths of a foot."""
    t0 = int(rows[0][0].timestamp() // 60)
    prev, parts = t0, []
    for t, h in rows:
        m = int(t.timestamp() // 60)
        delta, prev = m - prev, m
        tenths = round(h * 10)
        if not 0 <= delta < 1296 or not 0 <= tenths < 1296:
            sys.exit("FAILED: value out of encodable range (%d, %d)" % (delta, tenths))
        parts.append(b36(delta, 2) + b36(tenths, 2))
    return t0, "".join(parts)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    a, b = d(sys.argv[1]), d(sys.argv[2])
    print("Sandy Hook (%s) high waters, %s .. %s" % (STATION, a, b))
    rows = check(fetch(a, b))
    t0, enc = encode(rows)
    (HERE / "encoded.txt").write_text("%d\n%s\n" % (t0, enc))
    print("  wrote encoded.txt — %d chars for %d high waters" % (len(enc), len(rows)))
    print("\nNow run:  python3 build.py    then bump CACHE in ../sw.js")
