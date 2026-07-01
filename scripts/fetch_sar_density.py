#!/usr/bin/env python3
"""Fetch Global Fishing Watch's Sentinel-1 SAR dark-vessel detection density and ship it as a static
map layer, so SeaVigil shows the worldwide footprint of the dark fleet (the ~75% of industrial
vessels that do not broadcast AIS).

This is DISPLAY context, not our own detection: GFW's global SAR detections (Paolo et al., Nature
2024) are free and authoritative, so we aggregate them once via the 4Wings API (server-side, so we
never download the ~20M raw points), and serve the resulting coarse density grid statically. No live
GFW dependency in the browser; attribution travels with the file (CC BY-NC, non-commercial).

The API rejects a single global polygon, so the world is tiled into bounded boxes and merged.

  GFW_TOKEN=... python3 scripts/fetch_sar_density.py
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data" / "sar_density.geojson"
API = "https://gateway.api.globalfishingwatch.org/v3/4wings/report"
UA = "SeaVigil/1.0 (research; github.com/iadicarlo/seavigil)"
DATASET = "public-global-sar-presence:latest"
DATE_RANGE = "2024-01-01,2024-12-31"   # a full year is a good footprint
TILE_DEG = 30                          # a single global polygon is rejected; fetch in bounded tiles
ATTRIBUTION = "Sentinel-1 SAR dark-vessel detections (c) Global Fishing Watch (Paolo et al., Nature 2024), CC BY-NC 4.0"


def _token() -> str:
    t = os.environ.get("GFW_TOKEN")
    if not t and (ROOT / ".env").exists():
        for ln in (ROOT / ".env").read_text().splitlines():
            if ln.startswith("GFW_TOKEN="):
                t = ln.split("=", 1)[1].strip().strip('"').strip("'")
    if not t:
        raise SystemExit("GFW_TOKEN not set (in .env or the environment)")
    return t


def _fetch_tile(tok: str, lon0: float, lat0: float, lon1: float, lat1: float):
    poly = {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [
        [[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]]}}
    q = urllib.parse.urlencode({"datasets[0]": DATASET, "date-range": DATE_RANGE, "format": "JSON",
                                "spatial-resolution": "LOW", "temporal-resolution": "ENTIRE"}, safe="[]:,")
    req = urllib.request.Request(f"{API}?{q}", data=json.dumps({"geojson": poly}).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "User-Agent": UA,
                                          "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503):
                time.sleep(2 + attempt * 3)
                continue
            print(f"  tile ({lon0},{lat0}) HTTP {e.code}: {e.read().decode()[:120]}")
            return None
        except Exception as e:  # noqa: BLE001
            print(f"  tile ({lon0},{lat0}) error: {e}")
            return None
    return None


GRID = 4   # aggregate to a 1/GRID-degree grid (0.25 deg): a heatmap background needs no finer, and it
           # keeps the shipped file small (a few hundred KB instead of many MB).
TILE_SLEEP = 4.0   # the 4Wings API rate-limits aggressive callers; pace the tiles so a run completes


def _write(agg: dict) -> None:
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
              "properties": {"n": n}} for (lon, lat), n in agg.items()]
    feats.sort(key=lambda f: -f["properties"]["n"])
    OUT.write_text(json.dumps({"type": "FeatureCollection", "_attribution": ATTRIBUTION,
                               "date_range": DATE_RANGE, "features": feats}))


def main() -> None:
    tok = _token()
    agg: dict = {}
    tiles = [(lo, la) for lo in range(-180, 180, TILE_DEG) for la in range(-80, 80, TILE_DEG)]
    print(f"fetching SAR density in {len(tiles)} tiles ({DATE_RANGE}); writing incrementally...")
    for i, (lo, la) in enumerate(tiles):
        d = _fetch_tile(tok, lo, la, lo + TILE_DEG, la + TILE_DEG)
        if d:
            got = 0
            for e in d.get("entries") or []:
                for _key, rows in e.items():
                    for row in (rows or []):
                        lat, lon, det = row.get("lat"), row.get("lon"), row.get("detections")
                        if lat is not None and lon is not None and det:
                            key = (round(lon * GRID) / GRID, round(lat * GRID) / GRID)
                            agg[key] = agg.get(key, 0) + det
                            got += 1
            if got:
                _write(agg)   # incremental: a partial run still leaves a usable file
                print(f"  [{i + 1}/{len(tiles)}] tile ({lo},{la}): +{got} raw cells "
                      f"(grid cells {len(agg)})", flush=True)
        time.sleep(TILE_SLEEP)
    _write(agg)
    print(f"\nwrote {len(agg)} SAR density grid cells ({sum(agg.values()):,} detections) -> {OUT} "
          f"({OUT.stat().st_size / 1024:.0f} KB)", flush=True)


if __name__ == "__main__":
    main()
