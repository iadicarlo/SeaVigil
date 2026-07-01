#!/usr/bin/env python3
"""Satellite-image chips for SeaVigil detections: the "see the boat" view.

For each recent detection in results/<source>/incidents.json, crop a true-color window from
the source Copernicus scene around the detection and save web/data/<source>/chips/<id>.png,
with an index.json mapping detection id -> {url, label, ts}. The dossier shows the chip, so a
dark vessel stops being a dot and becomes a picture, which is the difference between "a blip"
and "here is the boat, fishing, broadcasting nothing." Chips older than --keep-days, or whose
detection has aged out of the view, are pruned, so the gallery stays current and small.

Runs on the always-on box, where the CDSE S3 keys (CDSE_S3_KEY / CDSE_S3_SECRET) and the geo
deps (rasterio, boto3, pillow, numpy) live. Two sources: --source s2 crops a true-color optical
window; --source sar crops a grayscale Sentinel-1 window. S1 GRD is delivered in radar geometry
(GCP-geolocated, no north-up affine), so the SAR path warps each scene through a WarpedVRT to
map (lat, lon) to pixels correctly, which a plain windowed read cannot do.

  CDSE_S3_KEY=... CDSE_S3_SECRET=... ~/geoenv/bin/python scripts/make_chips.py --source s2
  CDSE_S3_KEY=... CDSE_S3_SECRET=... ~/geoenv/bin/python scripts/make_chips.py --source sar --max 200
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S2_L1C = "Sentinel-2/MSI/L1C"
S1_SAR = "Sentinel-1/SAR"


def _s2_bands(s3, scene: str) -> dict:
    """Locate the true-color image bands (B02/B03/B04) of an S2 L1C scene on CDSE S3."""
    y, m, d = scene[11:15], scene[15:17], scene[17:19]
    prefix = f"{S2_L1C}/{y}/{m}/{d}/{scene}.SAFE/"
    bands: dict = {}
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket="eodata", Prefix=prefix):
        for o in page.get("Contents", []):
            k = o["Key"]
            if "/IMG_DATA/" in k and k.endswith(".jp2"):
                for b in ("B02", "B03", "B04"):
                    if f"_{b}.jp2" in k:
                        bands[b] = k
    return bands


def _crop_rgb(bands: dict, lat: float, lon: float, half_m: float = 750.0, size: int = 256):
    """A size x size true-color crop centered on (lat, lon), read straight from CDSE via gdal."""
    import numpy as np
    import rasterio
    from rasterio.warp import transform as warp_transform
    from rasterio.windows import from_bounds

    def stretch(a):
        lo, hi = np.percentile(a, (2, 98))
        return np.clip((a - lo) / (hi - lo + 1e-6) * 255, 0, 255).astype("uint8")

    def band(key):
        with rasterio.open(f"/vsis3/eodata/{key}") as ds:
            xs, ys = warp_transform("EPSG:4326", ds.crs, [lon], [lat])
            win = from_bounds(xs[0] - half_m, ys[0] - half_m, xs[0] + half_m, ys[0] + half_m,
                              ds.transform)
            return ds.read(1, window=win, out_shape=(size, size), boundless=True, fill_value=0)

    return np.dstack([stretch(band(bands["B04"])), stretch(band(bands["B03"])),
                      stretch(band(bands["B02"]))])


def _s1_date(scene: str) -> str:
    """YYYY-MM-DD from an S1 scene stem (…_20260620T190819_…)."""
    import re
    m = re.search(r"_(\d{8})T\d{6}_", scene)
    d = m.group(1) if m else "00000000"
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"


def _s1_vv_key(s3, scene: str):
    """The vv (else vh) measurement GeoTIFF key for an S1 GRD scene stem, or None."""
    import re
    m = re.search(r"_(\d{8})T\d{6}_", scene)
    if not m:
        return None
    d = m.group(1)
    coll = "IW_GRDH_1S-COG" if scene.endswith("_COG") else "IW_GRDH_1S"
    prefix = f"{S1_SAR}/{coll}/{d[:4]}/{d[4:6]}/{d[6:8]}/{scene}.SAFE/measurement/"
    got: dict = {}
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket="eodata", Prefix=prefix):
        for o in page.get("Contents", []):
            parts = o["Key"].split("/")[-1].split("-")
            if len(parts) > 3 and parts[3] in ("vv", "vh"):
                got[parts[3]] = o["Key"]
    return got.get("vv") or got.get("vh")


def _crop_sar(key: str, lat: float, lon: float, half_m: float = 750.0, size: int = 256):
    """A size x size grayscale SAR crop centered on (lat, lon).

    S1 GRD COGs are geolocated by ground-control points, not a north-up affine, so we open the
    scene through a WarpedVRT (EPSG:3857) and let gdal resolve (lat, lon) -> pixel. A percentile
    stretch on the in-scene pixels leaves calm sea near black and the bright vessel return white.
    """
    import numpy as np
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_bounds as transform_from_bounds
    from rasterio.vrt import WarpedVRT
    from rasterio.warp import transform as warp_transform

    xs, ys = warp_transform("EPSG:4326", "EPSG:3857", [lon], [lat])
    cx, cy = xs[0], ys[0]
    dst = transform_from_bounds(cx - half_m, cy - half_m, cx + half_m, cy + half_m, size, size)
    with rasterio.open(f"/vsis3/eodata/{key}") as src:
        # Warp straight into the crop grid, so no boundless read is needed (WarpedVRT forbids it)
        # and any pixels off the scene footprint come back as 0.
        with WarpedVRT(src, crs="EPSG:3857", transform=dst, width=size, height=size,
                       nodata=0, resampling=Resampling.bilinear) as vrt:
            a = vrt.read(1).astype("float32")
    inside = a[a > 0]
    lo, hi = (np.percentile(inside, (2, 98)) if inside.size else (0.0, 1.0))
    return np.clip((a - lo) / (hi - lo + 1e-6) * 255, 0, 255).astype("uint8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Crop Copernicus image chips for SeaVigil detections")
    ap.add_argument("--source", default="s2", choices=["s2", "sar"],
                    help="s2 optical true-color, or sar Sentinel-1 grayscale")
    ap.add_argument("--keep-days", type=float, default=30.0, help="prune chips older than this")
    ap.add_argument("--max", type=int, default=60, help="cap chips generated per run")
    a = ap.parse_args()

    import boto3
    import numpy as np
    from PIL import Image

    key, sec = os.environ.get("CDSE_S3_KEY"), os.environ.get("CDSE_S3_SECRET")
    if not (key and sec):
        raise SystemExit("CDSE_S3_KEY / CDSE_S3_SECRET not set (needed to read Copernicus scenes)")
    os.environ.update({"AWS_S3_ENDPOINT": "eodata.dataspace.copernicus.eu",
                       "AWS_ACCESS_KEY_ID": key, "AWS_SECRET_ACCESS_KEY": sec,
                       "AWS_VIRTUAL_HOSTING": "FALSE", "AWS_HTTPS": "YES"})
    s3 = boto3.client("s3", endpoint_url="https://eodata.dataspace.copernicus.eu",
                      aws_access_key_id=key, aws_secret_access_key=sec)

    inc_path = ROOT / "results" / a.source / "incidents.json"
    chips_dir = ROOT / "web" / "data" / a.source / "chips"
    chips_dir.mkdir(parents=True, exist_ok=True)
    index_path = chips_dir / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}

    dets = json.loads(inc_path.read_text()) if inc_path.exists() else []
    now = time.time()

    # Prune: drop chips that aged out (keep-days) or whose detection is gone from the view.
    cur_ids = {d.get("incident_id") for d in dets}
    for cid in list(index):
        ent = index[cid]
        aged = (now - ent.get("ts", now)) > a.keep_days * 86400
        if aged or cid not in cur_ids:
            (chips_dir / Path(ent["url"]).name).unlink(missing_ok=True)
            del index[cid]

    is_sar = a.source == "sar"
    scene_cache: dict = {}
    made = 0
    for d in dets:
        cid, scene = d.get("incident_id"), d.get("scene_id")
        lat, lon = d.get("centroid_lat"), d.get("centroid_lon")
        if not (cid and scene and lat is not None and lon is not None):
            continue
        if cid in index and (chips_dir / Path(index[cid]["url"]).name).exists():
            continue
        if made >= a.max:
            break
        try:
            if scene not in scene_cache:
                scene_cache[scene] = _s1_vv_key(s3, scene) if is_sar else _s2_bands(s3, scene)
            res = scene_cache[scene]
            if is_sar:
                if not res:
                    print(f"  no vv/vh tiff for {scene[:24]}; skipping {cid}")
                    continue
                arr = _crop_sar(res, float(lat), float(lon))
                pil, label = Image.fromarray(arr, mode="L"), f"Sentinel-1 SAR · {_s1_date(scene)}"
            else:
                if not (res and all(b in res for b in ("B02", "B03", "B04"))):
                    print(f"  no RGB bands for {scene[:24]}; skipping {cid}")
                    continue
                arr = _crop_rgb(res, float(lat), float(lon))
                pil = Image.fromarray(arr)
                label = f"Sentinel-2 · {scene[11:15]}-{scene[15:17]}-{scene[17:19]}"
            if int(np.asarray(arr).max()) == 0:
                print(f"  blank crop for {cid}; skipping")
                continue
            fname = f"{cid}.png"
            pil.save(chips_dir / fname)
            index[cid] = {"url": f"./data/{a.source}/chips/{fname}", "label": label, "ts": now}
            made += 1
            print(f"  chip {cid} <- {scene[:24]}")
        except Exception as e:  # noqa: BLE001 - one bad scene must not stop the rest
            print(f"  chip failed for {cid}: {type(e).__name__}: {e}")

    index_path.write_text(json.dumps(index, indent=0))
    print(f"{a.source}: {made} new chip(s), {len(index)} in the index")


if __name__ == "__main__":
    main()
