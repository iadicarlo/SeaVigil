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
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from itertools import groupby
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from urllib.parse import unquote


def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in nautical miles."""
    la1, la2 = radians(lat1), radians(lat2)
    dphi, dlmb = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(la1) * cos(la2) * sin(dlmb / 2) ** 2
    return 3440.065 * 2 * asin(min(1.0, sqrt(a)))


# TTL response cache: at global AIS scale the live endpoints recompute at most once per TTL no
# matter how many browsers poll, so a modest VPS stays responsive.
_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()


def _cached(key: str, ttl: float, build) -> bytes:
    now = time.time()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
    body = build()  # built outside the lock so a slow build does not serialize every request
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), body)
    return body


def _load_areas() -> list:
    """The IUU-priority boxes. Live positions/tracks are shown globally for context, but behavior
    and integrity detection is scoped to these offshore hotspots: run globally, going-dark and
    encounters would fire on every crowded port/anchorage (noise), not on illegal fishing."""
    try:
        wl = json.loads((ROOT / "data" / "watchlist.json").read_text())
        return [(a["bbox"][1], a["bbox"][0], a["bbox"][3], a["bbox"][2]) for a in wl.get("areas", [])]
    except Exception:  # noqa: BLE001 - a missing/broken watchlist must not take the server down
        return []


_AREAS = _load_areas()


def _area_clause(lat_col: str, lon_col: str):
    """SQL (fragment, params) restricting a query to the IUU-priority boxes. '1' means no boxes."""
    if not _AREAS:
        return "1", []
    parts, params = [], []
    for lat0, lon0, lat1, lon1 in _AREAS:
        parts.append(f"({lat_col} BETWEEN ? AND ? AND {lon_col} BETWEEN ? AND ?)")
        params += [lat0, lat1, lon0, lon1]
    return "(" + " OR ".join(parts) + ")", params


def _in_areas(lat: float, lon: float) -> bool:
    """True if a point is inside any IUU-priority box (or if no boxes are configured)."""
    if not _AREAS:
        return True
    return any(lat0 <= lat <= lat1 and lon0 <= lon <= lon1 for lat0, lon0, lat1, lon1 in _AREAS)

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
                "SELECT mmsi,lat,lon,ts,speed,course,name,flag,ship_type,destination,imo,callsign,nav_status "
                "FROM vessels WHERE ts>=? ORDER BY ts DESC LIMIT ?", (cutoff, MAX_FEATURES))
            for mmsi, lat, lon, ts, sog, cog, name, flag, stype, dest, imo, callsign, navst in cur:
                feats.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "mmsi": mmsi, "name": name or "", "flag": flag or "",
                        "speed": round(sog or 0.0, 1), "course": round(cog or 0.0),
                        "ship_type": stype or "", "destination": dest or "",
                        "imo": imo or "", "callsign": callsign or "",
                        "nav_status": navst if navst is not None else "",
                        "age_min": round((now - ts) / 60.0, 1),
                    },
                })
        finally:
            con.close()
    body = {"type": "FeatureCollection", "generated": int(time.time()),
            "window_min": window_min, "features": feats}
    return json.dumps(body).encode()


TRACKS_ENDPOINT = "/live/tracks.geojson"
TRACK_WINDOW_MIN = 180.0    # how far back each drawn track reaches
MIN_TRACK_POINTS = 3        # a line needs at least this many fixes to be worth drawing
MAX_TRACKS = 2000
TRACK_SPLIT_MAX_KN = 60.0   # a hop faster than this (and > 2 nm) is a duplicate-MMSI teleport


def _unwrap_lonlat(seg: list) -> list:
    """Shift longitudes so a track never draws the long way around the globe (antimeridian)."""
    if not seg:
        return seg
    out = [[seg[0][0], seg[0][1]]]
    for lon, lat in seg[1:]:
        prev = out[-1][0]
        while lon - prev > 180:
            lon -= 360
        while lon - prev < -180:
            lon += 360
        out.append([lon, lat])
    return out


def _split_track(fixes: list) -> list:
    """Split a vessel's (ts, lat, lon) fixes into plausible segments, breaking the line wherever a hop
    implies an impossible speed (a duplicate-MMSI teleport that otherwise draws a line across the whole
    map). Each returned segment is an unwrapped [lon, lat] list of >= 2 points."""
    segs, cur, prev = [], [], None
    for ts, lat, lon in fixes:
        if prev is not None:
            dnm = _haversine_nm(prev[1], prev[2], lat, lon)
            implied = dnm / max((ts - prev[0]) / 3600.0, 1e-6)
            if dnm > 2.0 and implied > TRACK_SPLIT_MAX_KN:   # teleport: end this segment, start a new one
                if len(cur) >= 2:
                    segs.append(_unwrap_lonlat(cur))
                cur = []
        cur.append([lon, lat])
        prev = (ts, lat, lon)
    if len(cur) >= 2:
        segs.append(_unwrap_lonlat(cur))
    return segs


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
                fixes = [(r[1], r[2], r[3]) for r in grp]   # (ts, lat, lon) in time order
                if len(fixes) < MIN_TRACK_POINTS:
                    continue
                segs = _split_track(fixes)
                if not segs:
                    continue
                name, flag = ident.get(mmsi, ("", ""))
                geom = ({"type": "LineString", "coordinates": segs[0]} if len(segs) == 1
                        else {"type": "MultiLineString", "coordinates": segs})
                feats.append({
                    "type": "Feature",
                    "geometry": geom,
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
# Position anomaly (kind ais_spoofing): impossible movement in a vessel's own fixes. Same
# thresholds as seavigil/spoofing.py: a jump of >= this many nm implying > this many knots,
# flagged only on a sustained pattern. GNSS jamming / faulty GPS as often as deliberate spoofing.
JUMP_MIN_NM, JUMP_MAX_SPEED_KN, JUMP_MIN_ANOM, JUMP_LOOKBACK_MIN = 2.0, 60.0, 3, 180.0
# Nav-status vs motion: broadcasting at-anchor(1)/moored(5) while the track shows real transit.
# Only the moving-while-moored branch (the clean, practitioner-named signal); a data-integrity lead.
NAV_MOORED, NAV_LOOKBACK_MIN, NAV_MIN_FIXES, NAV_MIN_SPEED, NAV_MIN_MOVE_NM = (1, 5), 30.0, 5, 1.0, 0.3
# Identity change: one MMSI broadcasting >= 2 distinct (aggressively normalized) names in the window.
IDENT_LOOKBACK_MIN = 360.0


def _integrity_features(con: sqlite3.Connection, now: int) -> list:
    """Data-integrity leads from the live AIS: position anomaly, nav-status-vs-motion, and identity
    change. Each is context for an analyst to check, never proof and never rolled into a case's
    confidence. Motivated by working mariners on r/AIS and r/maritime, who named these (impossible
    position variance, a wrong AIS status, a recycled identity) as the AIS anomalies they trust."""
    out: list = []

    # Position anomaly: a vessel's own fixes imply physically impossible movement.
    jstart = now - int(JUMP_LOOKBACK_MIN * 60)
    jident = {m: (nm, fl) for m, nm, fl in con.execute(
        "SELECT mmsi,name,flag FROM vessels WHERE ts>=?", (jstart,))}
    jclause, jp = _area_clause("lat", "lon")
    jrows = con.execute(
        "SELECT mmsi,ts,lat,lon FROM positions WHERE ts>=? AND " + jclause
        + " ORDER BY mmsi,ts LIMIT 120000", (jstart, *jp)).fetchall()
    for mmsi, grp in groupby(jrows, key=lambda r: r[0]):
        pts = list(grp)
        if len(pts) < JUMP_MIN_ANOM + 1:
            continue
        anom, worst, prev = 0, 0.0, None
        for _, ts_i, la, lo in pts:
            if prev is not None:
                dnm = _haversine_nm(prev[1], prev[2], la, lo)
                implied = dnm / max((ts_i - prev[0]) / 3600.0, 1e-6)
                if dnm >= JUMP_MIN_NM and implied > JUMP_MAX_SPEED_KN:
                    anom += 1
                    worst = max(worst, implied)
            prev = (ts_i, la, lo)
        if anom >= JUMP_MIN_ANOM:
            nm, fl = jident.get(mmsi, ("", ""))
            out.append({"type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [pts[-1][3], pts[-1][2]]},
                        "properties": {"kind": "ais_spoofing", "mmsi": mmsi,
                                       "name": nm or "", "flag": fl or "",
                                       "anomaly_count": anom, "max_implied_speed_kn": round(worst)}})

    # Nav-status vs motion: broadcasting moored / at anchor while the fixes show real transit.
    nstart = now - int(NAV_LOOKBACK_MIN * 60)
    nident = {m: (nm, fl, stt) for m, nm, fl, stt in con.execute(
        "SELECT mmsi,name,flag,nav_status FROM vessels WHERE ts>=?", (nstart,))}
    nclause, np_ = _area_clause("lat", "lon")
    nrows = con.execute(
        "SELECT mmsi,ts,lat,lon,speed FROM positions WHERE ts>=? AND nav_status IN (1,5) AND "
        + nclause + " ORDER BY mmsi,ts LIMIT 60000", (nstart, *np_)).fetchall()
    for mmsi, grp in groupby(nrows, key=lambda r: r[0]):
        pts = list(grp)
        if len(pts) < NAV_MIN_FIXES:
            continue
        nm, fl, cur = nident.get(mmsi, ("", "", None))
        if cur not in NAV_MOORED:   # must still be broadcasting moored / at anchor now
            continue
        max_sog = max((p[4] or 0.0) for p in pts)
        moved = _haversine_nm(pts[0][2], pts[0][3], pts[-1][2], pts[-1][3])  # net displacement
        if max_sog >= NAV_MIN_SPEED and moved >= NAV_MIN_MOVE_NM:
            sogs = sorted((p[4] or 0.0) for p in pts)
            out.append({"type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [pts[-1][3], pts[-1][2]]},
                        "properties": {"kind": "navstatus_mismatch", "mmsi": mmsi,
                                       "name": nm or "", "flag": fl or "",
                                       "reported_status": "moored" if cur == 5 else "at anchor",
                                       "sog_median": round(sogs[len(sogs) // 2], 1),
                                       "moved_nm": round(moved, 2),
                                       "window_min": round((pts[-1][1] - pts[0][1]) / 60.0)}})

    # Identity change: one MMSI carrying more than one distinct vessel name over the window. Names
    # normalized hard (uppercase, alphanumerics only) so punctuation / spacing / prefix noise does
    # not masquerade as a swap. Name-only, weaker than an IMO check; explicitly a lead.
    istart = now - int(IDENT_LOOKBACK_MIN * 60)
    hist: dict = {}
    for mmsi, nm in con.execute(
            "SELECT mmsi,name FROM identity_history WHERE ts>=? AND name<>''", (istart,)):
        key = re.sub(r"[^A-Z0-9]", "", (nm or "").upper())
        if len(key) >= 3:
            hist.setdefault(mmsi, {}).setdefault(key, nm)
    for mmsi, names in hist.items():
        if len(names) < 2:
            continue
        row = con.execute("SELECT lat,lon,flag FROM vessels WHERE mmsi=?", (mmsi,)).fetchone()
        if not row:
            continue
        la, lo, fl = row
        if not _in_areas(la, lo):   # scope identity leads to the IUU areas, like the others
            continue
        joined = " / ".join(list(names.values())[:4])
        out.append({"type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lo, la]},
                    "properties": {"kind": "identity_change", "mmsi": mmsi, "flag": fl or "",
                                   "name": joined, "names": joined, "name_count": len(names)}})
    return out


def _events_geojson() -> bytes:
    """Live behavior events: vessels that went quiet (going dark) and near-stationary pairs
    (possible at-sea encounters), as point features keyed by kind. A lead, not proof."""
    feats = []
    if DB.exists():
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        try:
            now = int(time.time())
            gap, lookback = now - int(DARK_GAP_MIN * 60), now - int(DARK_LOOKBACK_MIN * 60)
            gd_clause, gd_p = _area_clause("v.lat", "v.lon")
            for mmsi, lat, lon, ts, spd, name, flag in con.execute(
                    "SELECT v.mmsi,v.lat,v.lon,v.ts,v.speed,v.name,v.flag "
                    "FROM vessels v JOIN positions p ON p.mmsi=v.mmsi "
                    "WHERE v.ts BETWEEN ? AND ? AND v.speed>=? AND " + gd_clause + " "
                    "GROUP BY v.mmsi HAVING COUNT(p.ts)>=? LIMIT 400",
                    (lookback, gap, DARK_MIN_SPEED, *gd_p, DARK_MIN_POINTS)):
                feats.append({"type": "Feature",
                              "geometry": {"type": "Point", "coordinates": [lon, lat]},
                              "properties": {"kind": "ais_disabling", "mmsi": mmsi,
                                             "name": name or "", "flag": flag or "",
                                             "quiet_min": round((now - ts) / 60.0),
                                             "last_speed": round(spd or 0.0, 1)}})
            fresh = now - int(ENC_FRESH_MIN * 60)
            enc_clause, enc_p = _area_clause("lat", "lon")
            slow = con.execute("SELECT mmsi,lat,lon,name,flag FROM vessels "
                               "WHERE ts>=? AND speed<=? AND " + enc_clause + " LIMIT 4000",
                               (fresh, ENC_MAX_SPEED, *enc_p)).fetchall()
            # A real at-sea transshipment: at least one vessel TRANSITED to the meeting point (a fishing
            # boat coming to a drifting carrier), while two vessels parked in a port/anchorage never
            # moved. AIS nav-status is too unreliable to lean on (GIGO), so gate on observed motion:
            # pair each recently-under-way "arriver" (>= 3 kn in the last 90 min) with any near-stationary
            # partner. Kills the dominant port-cluster false positive at global scale.
            moved_recently = {m for (m,) in con.execute(
                "SELECT mmsi FROM positions WHERE ts>=? GROUP BY mmsi HAVING MAX(speed) >= 3.0",
                (now - int(90 * 60),))}
            arrivers = [r for r in slow if r[0] in moved_recently]
            n, seen = 0, set()
            for ma, la, lo, na, fa in arrivers:
                if ma in seen:
                    continue
                for mp, lb, lob, np_, fp in slow:
                    if mp == ma or mp in seen:
                        continue
                    if abs(la - lb) <= ENC_RADIUS_DEG and abs(lo - lob) <= ENC_RADIUS_DEG:
                        seen.add(ma)
                        seen.add(mp)
                        feats.append({"type": "Feature",
                                      "geometry": {"type": "Point",
                                                   "coordinates": [(lo + lob) / 2, (la + lb) / 2]},
                                      "properties": {"kind": "encounter", "mmsi": f"{ma} + {mp}",
                                                     "name": f"{na or ma} / {np_ or mp}",
                                                     "flag": ((fa or "") + " " + (fp or "")).strip()}})
                        n += 1
                        break  # one encounter per arriver is plenty
                if n >= ENC_MAX:
                    break

            # Data-integrity leads (position anomaly, nav-status vs motion, identity change), guarded
            # so a DB not yet migrated right after a deploy still returns the going-dark / encounter
            # events instead of failing the whole endpoint.
            try:
                feats.extend(_integrity_features(con, now))
            except sqlite3.OperationalError:
                pass
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
            self._send_json(_cached("positions", 7.0, lambda: _positions_geojson(self.window_min)))
            return
        if route == TRACKS_ENDPOINT:
            self._send_json(_cached("tracks", 25.0, _tracks_geojson))
            return
        if route == EVENTS_ENDPOINT:
            self._send_json(_cached("events", 20.0, _events_geojson))
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
