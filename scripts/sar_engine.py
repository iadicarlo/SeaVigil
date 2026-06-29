#!/usr/bin/env python3
"""SeaVigil sub-day dark-vessel engine.

Runs on a schedule, within hours of each Sentinel-1 pass (Copernicus NRT products land under
3h after acquisition). For each priority area in data/watchlist.json it:

  1. asks the Copernicus catalogue for new Sentinel-1 IW GRDH (Cloud-Optimized) scenes acquired
     in the last --since-hours that it has not already processed (tracked in --state);
  2. runs our detector over a bounded AOI of each new scene (scripts/run_sentinel1_detection.py);
  3. cross-matches the detections against the live AIS buffer, three ways (matched / dark /
     no-coverage), so a vessel is flagged dark only where reception proves it would have been seen;
  4. republishes the ?sar view + alerts and records the processed scenes.

Honest scope of this v1: CPU detection is bounded to an --aoi-deg box per scene (a full IW scene
is ~250 km and would need a GPU or tiling to cover whole at radar resolution), and AIS is sparse
offshore, so many detections fall to "no coverage / unverified" rather than a confident dark flag.
Both limits are surfaced, never hidden.

Run (in the conda env that has gdal + torch for the detector subprocess, or pass --detect-python):
  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... \
  uv run python scripts/sar_engine.py --vds /path/to/vessel-detection-sentinels \
    --detect-python /path/to/vds-env/bin/python --ais-buffer data/positions/ais_buffer.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
WATCHLIST = ROOT / "data" / "watchlist.json"
STATE = ROOT / "data" / "sar_state.json"


def _query_new_scenes(bbox, since_iso, top=10):
    """COG IW GRDH Sentinel-1 scenes intersecting bbox, acquired after since_iso."""
    w, s, e, n = bbox
    poly = f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"
    flt = (f"Collection/Name eq 'SENTINEL-1' and contains(Name,'GRDH') and contains(Name,'COG') "
           f"and OData.CSC.Intersects(area=geography'SRID=4326;{poly}') "
           f"and ContentDate/Start gt {since_iso}")
    url = CATALOG + "?" + urllib.parse.urlencode(
        {"$filter": flt, "$orderby": "ContentDate/Start desc", "$top": str(top),
         "$select": "Name,ContentDate,Footprint"})
    req = urllib.request.Request(url, headers={"User-Agent": "SeaVigil/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    out = []
    for v in data.get("value", []):
        out.append((v["Name"], v["ContentDate"]["Start"], v.get("Footprint", "")))
    return out


def _footprint_centroid(wkt):
    """Rough centroid (mean of vertices) of a geography'SRID=...;POLYGON((...))' footprint."""
    try:
        inner = wkt[wkt.index("((") + 2: wkt.index("))")]
        pts = [p.strip().split() for p in inner.split(",")]
        xs = [float(p[0]) for p in pts]
        ys = [float(p[1]) for p in pts]
        return sum(xs) / len(xs), sum(ys) / len(ys)
    except (ValueError, IndexError):
        return None


def _aoi_for(scene_wkt, area_bbox, aoi_deg):
    """A bounded AOI: an aoi_deg box around the scene centroid, clamped inside the area bbox."""
    w, s, e, n = area_bbox
    c = _footprint_centroid(scene_wkt)
    cx, cy = c if c else ((w + e) / 2, (s + n) / 2)
    cx = min(max(cx, w), e)
    cy = min(max(cy, s), n)
    h = aoi_deg / 2
    return [max(cx - h, w), max(cy - h, s), min(cx + h, e), min(cy + h, n)]


def main() -> None:
    ap = argparse.ArgumentParser(description="SeaVigil sub-day dark-vessel engine")
    ap.add_argument("--vds", required=True, help="cloned allenai/vessel-detection-sentinels repo")
    ap.add_argument("--detect-python", default=sys.executable,
                    help="interpreter with gdal+torch for the detector (the conda env python)")
    ap.add_argument("--ais-buffer", default="data/positions/ais_buffer.csv")
    ap.add_argument("--watchlist", default=str(WATCHLIST))
    ap.add_argument("--state", default=str(STATE))
    ap.add_argument("--since-hours", type=float, default=24.0)
    ap.add_argument("--max-scenes", type=int, default=2, help="cap scenes processed per run (CPU bound)")
    ap.add_argument("--aoi-deg", type=float, default=0.6, help="bounded AOI side per scene (CPU bound)")
    ap.add_argument("--conf", type=float, default=0.8)
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    a = ap.parse_args()

    areas = json.loads(Path(a.watchlist).read_text())["areas"]
    state = json.loads(Path(a.state).read_text()) if Path(a.state).exists() else {"processed": []}
    done = set(state.get("processed", []))
    since_iso = (datetime.now(timezone.utc) - timedelta(hours=a.since_hours)).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z")

    # 1. discover new scenes across the watchlist (dedupe a scene that spans several areas)
    todo = {}
    for area in areas:
        try:
            scenes = _query_new_scenes(area["bbox"], since_iso)
        except Exception as ex:  # a single area's catalogue hiccup must not sink the run
            print(f"  [{area['name']}] catalogue query failed: {ex}")
            continue
        for name, start, wkt in scenes:
            if name in done or name in todo:
                continue
            todo[name] = {"area": area, "start": start, "wkt": wkt}
    print(f"discovery: {len(todo)} new scene(s) across {len(areas)} areas since {since_iso}")
    if not todo:
        print("nothing new to process.")
        return

    # 2. detect a bounded AOI of each new scene (cap per run)
    work = Path(tempfile.mkdtemp(prefix="sar_engine_"))   # intermediates only; outputs go to results/sar
    combined = work / "engine_predictions.csv"
    rows, header, processed = [], None, []
    for name, info in list(todo.items())[: a.max_scenes]:
        aoi = _aoi_for(info["wkt"], info["area"]["bbox"], a.aoi_deg)
        per = work / "engine_one.csv"
        print(f"  detect {name}\n    area={info['area']['name']} aoi={aoi}")
        cmd = [a.detect_python, str(ROOT / "scripts" / "run_sentinel1_detection.py"),
               "--vds", a.vds, "--scene", name, "--bbox", *[str(x) for x in aoi],
               "--out", str(per), "--conf", str(a.conf), "--device", a.device]
        r = subprocess.run(cmd)
        if r.returncode != 0 or not per.exists():
            print(f"    detection failed for {name}; will retry next run")
            continue
        processed.append(name)   # mark done only on a successful detection (transient failures retry)
        with open(per) as f:
            rd = csv.reader(f)
            h = next(rd, None)
            if header is None:
                header = h
            rows.extend(list(rd))

    # 3 + 4. publish (3-way AIS match happens inside the converter) and record state
    if rows and header:
        with open(combined, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        cmd = [sys.executable, str(ROOT / "scripts" / "sar_detections_to_incidents.py"),
               "--detections", str(combined)]
        if Path(a.ais_buffer).exists():
            cmd += ["--ais", a.ais_buffer]
        else:
            print(f"  note: AIS buffer {a.ais_buffer} absent; detections will be broadcasting-unverified")
        print(f"publish: {len(rows)} detections from {len(processed)} scene(s)")
        subprocess.run(cmd, check=True)
    else:
        print("no detections produced this run; ?sar view left unchanged")

    state["processed"] = sorted(done | set(processed))[-2000:]  # keep the tail bounded
    state["last_run_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    Path(a.state).write_text(json.dumps(state, indent=1))
    print(f"state: {len(processed)} scene(s) processed this run -> {a.state}")


if __name__ == "__main__":
    main()
