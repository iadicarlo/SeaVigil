#!/usr/bin/env python3
"""Simplify the global EEZ into a small offline point-in-polygon tagging source.

The display layer uses web/tiles/eez.pmtiles; this is the matching geometry the
Python pipeline uses to tag any incident worldwide with its coastal-state EEZ (and
so to decide foreign vs domestic). Simplified hard (vessel positions carry GPS error
and the boundary is a reference anyway), kept small enough to commit. CC BY 4.0
(Marine Regions), so it is fine to redistribute as data.

Run:  uv run --with pyogrio --with geopandas python scripts/build_eez_tag.py
"""

from __future__ import annotations

import gzip
import os
import shutil
from pathlib import Path

os.environ.setdefault("OGR_GEOJSON_MAX_OBJ_SIZE", "0")  # some EEZ features exceed the default cap

import geopandas as gpd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "eez" / "eez_global.geojson"
OUT = ROOT / "data" / "eez_tag.geojson.gz"
_TMP = ROOT / "data" / "eez_tag.geojson"


def main() -> None:
    g = gpd.read_file(SRC)
    g["geometry"] = g.geometry.simplify(0.06, preserve_topology=True)  # ~6.6 km
    g = g[["geoname", "sovereign1", "iso_sov1", "pol_type", "geometry"]].rename(
        columns={"geoname": "name", "sovereign1": "sovereign", "iso_sov1": "iso_sov"})
    g = g[~g.geometry.is_empty & g.geometry.notna()]
    # 4 decimals (~11 m) keeps real geometry but drops float noise; gzip then takes the
    # full-resolution boundary from ~23 MB to a few MB so it is light to commit.
    for p in (OUT, _TMP):
        if p.exists():
            p.unlink()
    g.to_file(_TMP, driver="GeoJSON", COORDINATE_PRECISION=4)
    with open(_TMP, "rb") as f_in, gzip.open(OUT, "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
    _TMP.unlink()
    print(f"wrote {len(g)} EEZ polygons -> {OUT} ({OUT.stat().st_size // 1024} KB gzipped)")


if __name__ == "__main__":
    main()
