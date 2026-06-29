#!/usr/bin/env python3
"""Run our own Sentinel-1 vessel detection over a chosen scene and AOI.

This is the path that produced the ?sar showcase. It runs the open, pre-trained
Allen Institute Sentinel-1 detector (Apache-2.0) on a Copernicus scene we choose,
reading only the AOI we ask for straight from the Cloud-Optimized GeoTIFFs on S3
(no multi-GB download), and writes a predictions.csv that
scripts/sar_detections_to_incidents.py folds into the ?sar view.

It calls the detector + attribute postprocessor directly (the repo's FastAPI server
is broken at the published commit: main.py calls detect_vessels with the wrong arg
count). A single scene gives 2 channels (vh, vv); the detector wants 6 (two historical
overlap passes), so the overlaps are zero-filled. Supplying --hist scenes would use
real overlaps for fewer false positives.

Prerequisites (all free, open):
  1. The model code + weights (Git LFS, free):
       git clone --depth 1 https://github.com/allenai/vessel-detection-sentinels.git
       cd vessel-detection-sentinels
       git lfs pull --include='data/model_artifacts/sentinel-1/**' --include='torch_weights/**'
  2. A conda env with the geo + torch stack (prebuilt, no GDAL build):
       micromamba create -p ./vds-env -c conda-forge python=3.11 \
         pytorch torchvision gdal rasterio pyproj shapely scikit-image scikit-learn \
         numpy pandas boto3
  3. Copernicus Data Space S3 credentials in the environment (never commit them):
       export AWS_ACCESS_KEY_ID=...  AWS_SECRET_ACCESS_KEY=...

Run it with the conda env's interpreter (it needs that GDAL + torch):
  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... \
  ./vds-env/bin/python scripts/run_sentinel1_detection.py \
    --vds /path/to/vessel-detection-sentinels \
    --scene S1D_IW_GRDH_1SDV_20260627T114116_20260627T114145_003421_006075_6BE9_COG.SAFE \
    --bbox -90.5 -0.85 -90.0 -0.35 \
    --out results/sar/predictions.csv

Then fold it in:
  uv run python scripts/sar_detections_to_incidents.py --detections results/sar/predictions.csv
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# Make PROJ and GDAL find their data dirs even when this interpreter is invoked directly (the SAR
# engine does, in CI, with no conda activation). Without PROJ_DATA, gdal.Warp with an SRS fails
# with "PROJ: proj_create_from_database ... failed / Invalid SRS for -te_srs".
for _var, _sub in (("PROJ_DATA", "proj"), ("PROJ_LIB", "proj"), ("GDAL_DATA", "gdal")):
    _cand = os.path.join(sys.prefix, "share", _sub)
    if os.path.isdir(_cand):
        os.environ.setdefault(_var, _cand)

# zoom-13 web-mercator pixel: exactly what the model's preprocessing warps S1 GRD to.
PX_3857 = 2 * math.pi * 6378137 / 512 / (2 ** 13)  # 9.5547 m
S3_ENDPOINT = "eodata.dataspace.copernicus.eu"


def _s3_keys() -> tuple[str, str]:
    k = os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("CDSE_S3_KEY")
    s = os.environ.get("AWS_SECRET_ACCESS_KEY") or os.environ.get("CDSE_S3_SECRET")
    if not (k and s):
        raise SystemExit(
            "Copernicus S3 credentials not found. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY (or CDSE_S3_KEY / CDSE_S3_SECRET) in the environment."
        )
    return k, s


def _patch_pipeline(vds: Path) -> None:
    """Idempotent pandas-2.x compatibility fix for the vendored Allen pipeline.

    The repo (written for pandas 1.4) seeds the detection DataFrame's 20 attribute
    columns with int 0, so the columns become int64; pandas 2.x then refuses to write
    the float length / speed / class the postprocessor produces. Seeding with 0.0
    makes them float from creation. Raises if the target line is missing (no silent
    no-op), so a future upstream change is surfaced, not swallowed.
    """
    pl = vds / "src" / "inference" / "pipeline.py"
    txt = pl.read_text()
    good = "data=[output + [0.0] * 20 for output in outputs],"
    bad = "data=[output + [0] * 20 for output in outputs],"
    if good in txt:
        return
    if bad not in txt:
        raise SystemExit(f"Cannot apply pandas-2.x patch: expected line not found in {pl}")
    pl.write_text(txt.replace(bad, good))
    print(f"patched (pandas-2.x dtype): {pl}")


def _scene_s3_prefix(scene: str) -> str:
    """Build the eodata S3 measurement/ prefix from the .SAFE scene name."""
    m = re.search(r"_(\d{8})T\d{6}_", scene)
    if not m:
        raise SystemExit(f"Cannot parse acquisition date from scene name: {scene}")
    d = m.group(1)
    coll = "IW_GRDH_1S-COG" if scene.endswith("_COG.SAFE") else "IW_GRDH_1S"
    return f"Sentinel-1/SAR/{coll}/{d[:4]}/{d[4:6]}/{d[6:8]}/{scene}/measurement"


def _find_pols(s3, prefix: str) -> dict[str, str]:
    r = s3.list_objects_v2(Bucket="eodata", Prefix=prefix + "/")
    pols = {}
    for o in r.get("Contents", []):
        name = o["Key"].split("/")[-1]
        parts = name.split("-")
        if len(parts) > 3 and parts[3] in ("vh", "vv"):
            pols[parts[3]] = o["Key"]
    if "vh" not in pols or "vv" not in pols:
        raise SystemExit(f"Did not find vh and vv measurement tiffs under {prefix} (got {list(pols)})")
    return pols


def main() -> None:
    ap = argparse.ArgumentParser(description="Run our own Sentinel-1 vessel detection over a chosen AOI")
    ap.add_argument("--vds", required=True, help="Path to the cloned allenai/vessel-detection-sentinels repo")
    ap.add_argument("--scene", required=True, help="Sentinel-1 IW GRDH .SAFE scene name (COG variant preferred)")
    ap.add_argument("--bbox", required=True, nargs=4, type=float, metavar=("W", "S", "E", "N"),
                    help="AOI bounds in lon/lat (WGS84)")
    ap.add_argument("--out", default="results/sar/predictions.csv", help="Output detections CSV")
    ap.add_argument("--conf", type=float, default=0.75, help="Detector confidence threshold")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Inference device")
    a = ap.parse_args()

    vds = Path(a.vds).resolve()
    if not (vds / "src" / "inference" / "pipeline.py").exists():
        raise SystemExit(f"{vds} does not look like the vessel-detection-sentinels repo")
    det = vds / "data" / "model_artifacts" / "sentinel-1" / "frcnn_cmp2" / "3dff445"
    post = vds / "data" / "model_artifacts" / "sentinel-1" / "attr" / "c34aa37"
    for d in (det, post):
        w = d / "best.pth"
        if not (w.exists() and w.stat().st_size > 1_000_000):
            raise SystemExit(f"Missing model weights at {w}. Run: git lfs pull --include='data/model_artifacts/sentinel-1/**'")

    _patch_pipeline(vds)
    key, secret = _s3_keys()

    import boto3
    from botocore.config import Config
    from osgeo import gdal
    import numpy as np
    import torch

    gdal.DontUseExceptions()
    for k, v in {"AWS_S3_ENDPOINT": S3_ENDPOINT, "AWS_VIRTUAL_HOSTING": "FALSE", "AWS_HTTPS": "YES",
                 "AWS_ACCESS_KEY_ID": key, "AWS_SECRET_ACCESS_KEY": secret}.items():
        gdal.SetConfigOption(k, v)

    s3 = boto3.client("s3", endpoint_url=f"https://{S3_ENDPOINT}", aws_access_key_id=key,
                      aws_secret_access_key=secret, config=Config(s3={"addressing_style": "path"}),
                      region_name="default")
    prefix = _scene_s3_prefix(a.scene)
    pols = _find_pols(s3, prefix)
    W, S, E, N = a.bbox
    print(f"scene {a.scene}\nAOI {W},{S},{E},{N}  | warping at {PX_3857:.4f} m (EPSG:3857)")

    work = Path(tempfile.mkdtemp(prefix="s1det_"))
    crops = {}
    for pol, key_ in pols.items():
        dst = str(work / f"{pol}.tif")
        ds = gdal.Warp(dst, f"/vsis3/eodata/{key_}", dstSRS="EPSG:3857", xRes=PX_3857, yRes=PX_3857,
                       outputBounds=[W, S, E, N], outputBoundsSRS="EPSG:4326", resampleAlg="bilinear",
                       multithread=True)
        if ds is None:
            raise SystemExit(f"GDAL warp failed for {pol}: {gdal.GetLastErrorMsg() or 'check S3 creds / scene path'}")
        arr = ds.GetRasterBand(1).ReadAsArray()  # read from the warp result directly (no re-open race)
        crops[pol] = np.clip(arr, 0, 255).astype(np.uint8)
        ds.FlushCache()
        ds = None
        print(f"  {pol}: {crops[pol].shape}  (mean {crops[pol].mean():.0f})")

    vh8, vv8 = crops["vh"], crops["vv"]
    z = np.zeros_like(vh8)
    cat = np.stack([vh8, vv8, z, z, z, z], axis=0)  # 6 channels; overlaps zero-filled
    scene_stem = a.scene.replace(".SAFE", "")
    cat_path = str(work / f"{scene_stem}_cat.npy")
    np.save(cat_path, cat)
    base_path = str(work / f"{scene_stem}_base.tif")
    shutil.copy(str(work / "vh.tif"), base_path)
    meas = work / "raw" / scene_stem / "measurement"
    meas.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(work / "vh.tif"), str(meas / "base.tif"))

    sys.path.insert(0, str(vds / "src"))
    sys.path.insert(0, str(vds))
    from inference.pipeline import detect_vessels  # noqa: E402

    out_dir = work / "out"
    out_dir.mkdir(exist_ok=True)
    print(f"running detector + attribute postprocessor on {a.device} ...")
    detect_vessels(str(det), str(post), str(work / "raw"), scene_stem, cat_path, base_path,
                   str(out_dir), 2048, 400, 20, a.conf, 10, False, torch.device(a.device),
                   "sentinel1", None)

    import pandas as pd
    df = pd.read_csv(out_dir / "predictions.csv")
    df["scene_id"] = scene_stem
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    n_fish = int((df.get("is_fishing_vessel", pd.Series(dtype=float)) >= 0.5).sum())
    print(f"\n{len(df)} detections -> {out}  ({n_fish} classified fishing-type)")
    print("Fold into the ?sar view:")
    print(f"  uv run python scripts/sar_detections_to_incidents.py --detections {out}")


if __name__ == "__main__":
    main()
