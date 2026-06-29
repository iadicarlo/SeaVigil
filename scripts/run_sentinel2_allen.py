#!/usr/bin/env python3
"""Run the Ai2 (Allen Institute) Sentinel-2 vessel-detection model and fold it into SeaVigil.

This drives allenai/rslearn_projects' `sentinel2_vessels predict` pipeline: a trained, cloud-robust
optical detector (Swin + FPN + Faster R-CNN over 9 bands including the two SWIR bands that let it tell
a white hull from a white cloud), with a companion model for length / width / speed / heading / type.
Apache-2.0; Ai2 report 80%+ F1. We then convert its GeoJSON to the detections CSV that
scripts/sar_detections_to_incidents.py consumes.

This is the trained counterpart to scripts/run_sentinel2_detection.py (our model-free threshold
quick-look). The threshold detector flagged cumulus as vessels on a hazy scene; this one is trained to
reject cloud and to classify the vessel, so it is the real optical sensor.

The scene is pulled by ID from the public Sentinel-2 bucket anonymously (no GCP credentials), so you
only pass an L1C scene ID. The model code + 1.15 GB checkpoint live in an isolated venv; see the repo
setup notes (vendor/rslearn_projects, RSLP_PREFIX, /tmp/rslp-env).

  python scripts/run_sentinel2_allen.py \
    --scene-id S2C_MSIL1C_20260613T151721_N0512_R125_T18LTM_20260613T184148 \
    --out results/s2/callao.csv --crop-dir results/s2/callao_crops
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RSLP_DIR = ROOT / "vendor" / "rslearn_projects"
RSLP_PY = os.environ.get("RSLP_PYTHON", "/tmp/rslp-env/bin/python")
FIELDS = ["lon", "lat", "score", "vessel_length_m", "vessel_width_m", "vessel_speed_k",
          "heading_deg", "is_fishing_vessel", "vessel_type", "scene_id"]


def run_predict(scene_id: str, geojson_path: Path, crop_dir: Path, scratch: Path) -> None:
    """Invoke the rslearn sentinel2_vessels predict pipeline for one scene."""
    tasks = json.dumps([{"scene_id": scene_id, "geojson_path": str(geojson_path.resolve()),
                         "crop_path": str(crop_dir.resolve())}])
    env = dict(os.environ, RSLP_PREFIX="project_data/", PYTORCH_ENABLE_MPS_FALLBACK="1",
               RSLEARN_NUM_DATA_LOADER_WORKERS=os.environ.get("RSLEARN_NUM_DATA_LOADER_WORKERS", "2"))
    cmd = [RSLP_PY, "-m", "rslp.main", "sentinel2_vessels", "predict",
           "--tasks", tasks, "--scratch_path", str(scratch.resolve())]
    if not Path(RSLP_PY).exists():
        raise SystemExit(f"rslearn venv python not found at {RSLP_PY} (set RSLP_PYTHON).")
    print(f"running the Ai2 Sentinel-2 model on {scene_id} (CPU, full scene; a few minutes) ...")
    subprocess.run(cmd, cwd=str(RSLP_DIR), check=True, env=env)


def geojson_to_rows(geojson_path: Path, scene_id: str) -> list[dict]:
    """Convert the model's GeoJSON detections to our detector CSV schema."""
    d = json.loads(geojson_path.read_text())
    rows = []
    for f in d.get("features", []):
        lon, lat = f["geometry"]["coordinates"]
        p = f.get("properties", {})
        attr = p.get("attributes") or {}
        vtype = (attr.get("vessel_type") or "")
        rows.append({
            "lon": round(float(lon), 5), "lat": round(float(lat), 5),
            "score": round(float(p.get("score") or 0), 3),
            "vessel_length_m": _num(attr.get("length")),
            "vessel_width_m": _num(attr.get("width")),
            "vessel_speed_k": _num(attr.get("speed")),
            "heading_deg": _num(attr.get("heading")),
            "is_fishing_vessel": 1 if "fish" in vtype.lower() else 0,
            "vessel_type": vtype,
            "scene_id": p.get("scene_id") or scene_id,
        })
    return rows


def _num(v):
    return round(float(v), 1) if isinstance(v, (int, float)) else ""


def main() -> None:
    ap = argparse.ArgumentParser(description="Ai2 Sentinel-2 vessel detection -> SeaVigil CSV")
    ap.add_argument("--scene-id", required=True, help="Sentinel-2 L1C scene ID (no .SAFE)")
    ap.add_argument("--out", default="results/s2/predictions.csv")
    ap.add_argument("--geojson", default=None, help="also keep the raw GeoJSON here")
    ap.add_argument("--crop-dir", default=None, help="also keep per-vessel RGB crops here")
    a = ap.parse_args()

    work = Path(tempfile.mkdtemp(prefix="s2allen_"))
    geojson_path = Path(a.geojson) if a.geojson else work / "out.geojson"
    crop_dir = Path(a.crop_dir) if a.crop_dir else work / "crops"
    geojson_path.parent.mkdir(parents=True, exist_ok=True)
    run_predict(a.scene_id, geojson_path, crop_dir, work / "scratch")

    rows = geojson_to_rows(geojson_path, a.scene_id)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    n_fish = sum(1 for r in rows if r["is_fishing_vessel"])
    print(f"{len(rows)} vessel detections ({n_fish} classified fishing-type) -> {out}")
    print(f"Fold into the optical view:\n  uv run python scripts/sar_detections_to_incidents.py "
          f"--detections {out} --source optical")


if __name__ == "__main__":
    main()
