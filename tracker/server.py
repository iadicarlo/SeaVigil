#!/usr/bin/env python3
"""SeaVigil live server: serves the real SeaVigil site, made live.

This is the always-on read half of the live tracker. It serves the actual web/ site (the
rich map: MPAs, EEZ, the Sentinel-1 SAR and Sentinel-2 optical dark-vessel layers, IUU
flags, evidence dossiers, all four languages) and adds ONE dynamic endpoint,
/live/positions.geojson, rebuilt on each request from the SQLite database that
tracker/ingest.py keeps current. The site polls that endpoint and draws every broadcasting
vessel as a live layer beneath the incident flags, so the same rich page ticks in real time
instead of showing a committed snapshot.

PMTiles needs byte-range requests, so file responses honour Range (206 Partial Content).
On a static host (GitHub Pages) the endpoint is simply absent and the live layer stays empty;
everything else renders as before.

  python3 tracker/server.py 8100
  TRACKER_WINDOW_MIN=120 python3 tracker/server.py 8100
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import sqlite3
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WEB = ROOT / "web"
DB = HERE / "tracker.db"
LIVE_ENDPOINT = "/live/positions.geojson"
MAX_FEATURES = 8000   # backstop so a very busy window cannot produce a pathological payload


def _positions_geojson(window_min: float) -> bytes:
    """Every vessel seen in the last window_min minutes, as a GeoJSON FeatureCollection."""
    feats = []
    if DB.exists():
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        try:
            now = int(time.time())
            cutoff = now - int(window_min * 60)
            cur = con.execute(
                "SELECT mmsi,lat,lon,ts,speed,course,name,flag,ship_type,destination "
                "FROM vessels WHERE ts>=? ORDER BY ts DESC LIMIT ?", (cutoff, MAX_FEATURES))
            for mmsi, lat, lon, ts, sog, cog, name, flag, stype, dest in cur:
                feats.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "mmsi": mmsi, "name": name or "", "flag": flag or "",
                        "speed": round(sog or 0.0, 1), "course": round(cog or 0.0),
                        "ship_type": stype or "", "destination": dest or "",
                        "age_min": round((now - ts) / 60.0, 1),
                    },
                })
        finally:
            con.close()
    body = {"type": "FeatureCollection", "generated": int(time.time()),
            "window_min": window_min, "features": feats}
    return json.dumps(body).encode()


TRACKS_ENDPOINT = "/live/tracks.geojson"
TRACK_WINDOW_MIN = 180.0   # how far back each drawn track reaches
MIN_TRACK_POINTS = 3       # a line needs at least this many fixes to be worth drawing
MAX_TRACKS = 2000


def _tracks_geojson() -> bytes:
    """Each vessel's recent path (last TRACK_WINDOW_MIN minutes) as a GeoJSON LineString."""
    from itertools import groupby
    feats = []
    if DB.exists():
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        try:
            cutoff = int(time.time()) - int(TRACK_WINDOW_MIN * 60)
            ident = {m: (n, f) for m, n, f in con.execute(
                "SELECT mmsi,name,flag FROM vessels WHERE ts>=?", (cutoff,))}
            rows = con.execute(
                "SELECT mmsi,ts,lat,lon FROM positions WHERE ts>=? ORDER BY mmsi,ts",
                (cutoff,)).fetchall()
            for mmsi, grp in groupby(rows, key=lambda r: r[0]):
                pts = [[r[3], r[2]] for r in grp]   # [lon, lat] in time order
                if len(pts) < MIN_TRACK_POINTS:
                    continue
                name, flag = ident.get(mmsi, ("", ""))
                feats.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": pts},
                    "properties": {"mmsi": mmsi, "name": name or "", "flag": flag or ""},
                })
                if len(feats) >= MAX_TRACKS:
                    break
        finally:
            con.close()
    return json.dumps({"type": "FeatureCollection", "generated": int(time.time()),
                       "features": feats}).encode()


EVENTS_ENDPOINT = "/live/events.geojson"
# Going dark: a vessel that was moving and had a real track, then went quiet for a while.
DARK_GAP_MIN, DARK_LOOKBACK_MIN, DARK_MIN_SPEED, DARK_MIN_POINTS = 25.0, 90.0, 3.0, 5
# Encounter: two recent, near-stationary vessels essentially on top of each other.
ENC_RADIUS_DEG, ENC_MAX_SPEED, ENC_FRESH_MIN, ENC_MAX = 0.004, 1.2, 15.0, 400


def _events_geojson() -> bytes:
    """Live behavior events: vessels that went quiet (going dark) and near-stationary pairs
    (possible at-sea encounters), as point features keyed by kind. A lead, not proof."""
    feats = []
    if DB.exists():
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        try:
            now = int(time.time())
            gap, lookback = now - int(DARK_GAP_MIN * 60), now - int(DARK_LOOKBACK_MIN * 60)
            for mmsi, lat, lon, ts, spd, name, flag in con.execute(
                    "SELECT v.mmsi,v.lat,v.lon,v.ts,v.speed,v.name,v.flag "
                    "FROM vessels v JOIN positions p ON p.mmsi=v.mmsi "
                    "WHERE v.ts BETWEEN ? AND ? AND v.speed>=? "
                    "GROUP BY v.mmsi HAVING COUNT(p.ts)>=? LIMIT 400",
                    (lookback, gap, DARK_MIN_SPEED, DARK_MIN_POINTS)):
                feats.append({"type": "Feature",
                              "geometry": {"type": "Point", "coordinates": [lon, lat]},
                              "properties": {"kind": "ais_disabling", "mmsi": mmsi,
                                             "name": name or "", "flag": flag or "",
                                             "quiet_min": round((now - ts) / 60.0),
                                             "last_speed": round(spd or 0.0, 1)}})
            fresh = now - int(ENC_FRESH_MIN * 60)
            slow = con.execute("SELECT mmsi,lat,lon,name,flag FROM vessels "
                               "WHERE ts>=? AND speed<=? LIMIT 1500", (fresh, ENC_MAX_SPEED)).fetchall()
            n = 0
            for i in range(len(slow)):
                mi, la, lo, ni, fi = slow[i]
                for j in range(i + 1, len(slow)):
                    mj, lb, lob, nj, fj = slow[j]
                    if abs(la - lb) <= ENC_RADIUS_DEG and abs(lo - lob) <= ENC_RADIUS_DEG:
                        feats.append({"type": "Feature",
                                      "geometry": {"type": "Point",
                                                   "coordinates": [(lo + lob) / 2, (la + lb) / 2]},
                                      "properties": {"kind": "encounter", "mmsi": f"{mi} + {mj}",
                                                     "name": f"{ni or mi} / {nj or mj}",
                                                     "flag": ((fi or "") + " " + (fj or "")).strip()}})
                        n += 1
                        break  # one encounter per vessel is plenty
                if n >= ENC_MAX:
                    break
        finally:
            con.close()
    return json.dumps({"type": "FeatureCollection", "generated": int(time.time()),
                       "features": feats}).encode()


class Handler(SimpleHTTPRequestHandler):
    window_min = 60.0

    def end_headers(self):  # noqa: N802 (stdlib casing)
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def _send_json(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (stdlib casing)
        route = self.path.split("?", 1)[0]
        if route == LIVE_ENDPOINT:
            self._send_json(_positions_geojson(self.window_min))
            return
        if route == TRACKS_ENDPOINT:
            self._send_json(_tracks_geojson())
            return
        if route == EVENTS_ENDPOINT:
            self._send_json(_events_geojson())
            return
        super().do_GET()

    def translate_path(self, path: str) -> str:
        # The whole UI is the real web/ site; "/" is its index.
        clean = posixpath.normpath(unquote(path.split("?", 1)[0].split("#", 1)[0]))
        if clean in ("/", "/index.html", "."):
            return str(WEB / "index.html")
        rel = clean.lstrip("/")
        cand = (WEB / rel).resolve()
        if cand == WEB or WEB in cand.parents:   # contained within web/, no traversal
            return str(cand)
        return str(WEB / rel)  # outside web/: let the parent emit a clean 404

    def send_head(self):  # noqa: N802 - add Range support (PMTiles needs 206)
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        if not m:
            return super().send_head()
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        length = end - start + 1
        f = open(path, "rb")  # noqa: SIM115 (caller closes)
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self._range = (f, length)
        return f

    def copyfile(self, source, outputfile):
        rng = getattr(self, "_range", None)
        if rng is None:
            return super().copyfile(source, outputfile)
        f, length = rng
        remaining = length
        while remaining > 0:
            chunk = f.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8100
    Handler.window_min = float(os.environ.get("TRACKER_WINDOW_MIN", "60"))
    handler = partial(Handler, directory=str(WEB))
    print(f"SeaVigil live site on http://localhost:{port}  "
          f"(live layer {LIVE_ENDPOINT}, window {Handler.window_min:.0f} min, db {DB.name})")
    ThreadingHTTPServer(("0.0.0.0", port), handler).serve_forever()


if __name__ == "__main__":
    main()
