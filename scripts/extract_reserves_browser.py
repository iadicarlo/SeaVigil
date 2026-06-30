#!/usr/bin/env python3
"""Extract the famous marine reserves' real WDPA boundaries for the Reserves browser.

Expands the original five-reserve showcase to the full set of world-famous marine
reserves so the web map's "Reserves browser" can zoom to each. Geometries are
simplified for the web and carry a NAME property (`name`, matching the map's
`['get','name']` label expression).

WDPA/WD-OECM is UNEP-WCMC and IUCN (2026), Protected Planet, NON-COMMERCIAL. Only a
handful of named, simplified boundaries are produced here, with attribution carried in
the FeatureCollection. The .gdb and the intermediate .geojson stay out of git; the
SERVED map data is non-extractable vector tiles (PMTiles), never raw GeoJSON.

Run (geopandas/pyogrio are not project deps; pull them just for this):
  uv run --with pyogrio --with geopandas python scripts/extract_reserves_browser.py
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd

GDB = Path("/Users/Abdel042/Downloads/WDPA_WDOECM_Jun2026_Public_marine/"
           "WDPA_WDOECM_Jun2026_Public_marine.gdb")
LAYER = "WDPA_WDOECM_poly_Jun2026_marine"
OUT = Path(__file__).resolve().parent.parent / "data" / "mpa" / "wdpa_reserves_browser.geojson"
SIMPLIFY_DEG = 0.004  # ~440 m; keeps shape, drops the millions of coastal vertices
VERSION = "WDPA/WD-OECM Jun2026"
ATTRIBUTION = ("UNEP-WCMC and IUCN (2026), Protected Planet: The World Database on "
               "Protected Areas (WDPA) and WD-OECM, June 2026, Cambridge, UK. "
               "www.protectedplanet.net")

# Each target reserve -> the GDB SITE_ID(s) to dissolve into one display feature, and
# the display NAME the browser will show. SITE_IDs were resolved by name/ISO3 search
# against the Jun2026 marine layer (see commit message / report). Where a reserve is
# split into IUCN management zones (Great Barrier Reef, Coiba), all zones for that
# SITE_ID are unioned into one boundary.
RESERVES: list[dict] = [
    # --- original showcase five (kept) ---
    {"name": "Galapagos Marine Reserve",                         "site_ids": ["11753"]},
    {"name": "Great Barrier Reef Marine Park",                   "site_ids": ["2628"]},
    {"name": "Phoenix Islands Protected Area",                   "site_ids": ["309888"]},
    {"name": "Papahanaumokuakea Marine National Monument",       "site_ids": ["220201"]},
    {"name": "Rapa Nui Multiple-Use Marine Protected Area",      "site_ids": ["555786064"]},
    # --- the expanded famous-reserve set ---
    {"name": "Palau National Marine Sanctuary",                  "site_ids": ["555622118"]},
    {"name": "Ascension Island Marine Protected Area",           "site_ids": ["555651558"]},
    {"name": "Revillagigedo National Park",                      "site_ids": ["555629385"]},
    {"name": "Niue Moana Mahu Marine Protected Area",            "site_ids": ["555705568"]},
    {"name": "Cocos Island (Isla del Coco) National Park",       "site_ids": ["170"]},
    {"name": "Coiba National Park & Cordillera de Coiba",        "site_ids": ["17831", "555705293"]},
    {"name": "Tristan da Cunha Marine Protection Zone",          "site_ids": ["555720256"]},
    {"name": "Marae Moana (Cook Islands Marine Park)",           "site_ids": ["555624907"]},
    # --- representatives for nations with no single national reserve in WDPA ---
    {"name": "South Ari Marine Protected Area (Maldives)",       "site_ids": ["555576579"]},
    {"name": "Yadua Taba Locally Managed Marine Area (Fiji)",    "site_ids": ["555547846"]},
]

# Build the SITE_ID -> display-name map and the WHERE clause (read the layer ONCE).
SITE_TO_NAME: dict[str, str] = {}
for r in RESERVES:
    for sid in r["site_ids"]:
        SITE_TO_NAME[sid] = r["name"]
WHERE = "SITE_ID IN ({})".format(", ".join(f"'{s}'" for s in SITE_TO_NAME))


def _is_no_take(no_take, iucn) -> bool:
    nt = (no_take or "").strip().lower()
    return nt in ("all", "part") or (iucn or "").strip() == "Ia"


def main() -> None:
    g = gpd.read_file(GDB, layer=LAYER, where=WHERE, engine="pyogrio")
    g = g.to_crs(4326)
    g["disp"] = g["SITE_ID"].astype(str).map(SITE_TO_NAME)
    missing = g[g["disp"].isna()]
    if len(missing):
        print("WARN: rows with no display name:", missing["SITE_ID"].tolist())
    g = g.dropna(subset=["disp"])

    feats = []
    summary = []
    for name in dict.fromkeys(r["name"] for r in RESERVES):  # preserve order
        rows = g[g["disp"] == name]
        if not len(rows):
            print(f"MISSING (no geometry): {name}")
            continue
        merged = rows.geometry.union_all()
        merged = merged.simplify(SIMPLIFY_DEG, preserve_topology=True)
        if merged is None or merged.is_empty:
            print(f"MISSING (empty geometry): {name}")
            continue
        # representative point keeps the label inside the polygon
        c = merged.representative_point()
        cx, cy = c.x, c.y
        any_no_take = any(_is_no_take(r.get("NO_TAKE"), r.get("IUCN_CAT")) for _, r in rows.iterrows())
        iso3 = next((v for v in rows["ISO3"].tolist() if v), None)
        area = round(float(rows["REP_M_AREA"].fillna(0).sum()), 1)
        gj = json.loads(gpd.GeoSeries([merged], crs=4326).to_json())["features"][0]["geometry"]
        feats.append({
            "type": "Feature",
            "geometry": gj,
            "properties": {
                "name": name,
                "no_take": any_no_take,
                "area_km2": area,
                "iso3": iso3,
                "approximate": False,
            },
        })
        # bounds -> suggest a zoom that frames the reserve.
        # Antimeridian-aware: a polygon clamped to [-180,180] reports a full-width
        # x-span that is wrong. Recompute centroid + span from the union of per-part
        # bounds shifted into a continuous [0,360) longitude frame.
        import math
        parts = list(getattr(merged, "geoms", [merged]))
        xs0, xs1, lys, hys = [], [], [], []
        for p in parts:
            a, b, cc, dd = p.bounds
            # shift negative lons by +360 so dateline-spanning parts stay contiguous
            xs0.append(a + 360 if a < 0 else a)
            xs1.append(cc + 360 if cc < 0 else cc)
            lys.append(b); hys.append(dd)
        lon_lo, lon_hi = min(xs0), max(xs1)
        lon_span = lon_hi - lon_lo
        # if the shift made it worse (no dateline crossing), fall back to raw bounds
        rminx, rminy, rmaxx, rmaxy = merged.bounds
        if (rmaxx - rminx) < lon_span:
            lon_lo, lon_hi, lon_span = rminx, rmaxx, rmaxx - rminx
        lat_span = max(hys) - min(lys)
        span = max(lon_span, lat_span)
        ctr_lon = (lon_lo + lon_hi) / 2.0
        if ctr_lon > 180:
            ctr_lon -= 360
        zoom = max(2.0, min(9.0, round(math.log2(360.0 / max(span, 0.4)), 1)))
        summary.append((name, round(ctr_lon, 4), round(cy, 4), zoom, area, iso3, any_no_take))

    fc = {"type": "FeatureCollection", "wdpa_version": VERSION,
          "_attribution": ATTRIBUTION, "features": feats}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fc))
    size_kb = OUT.stat().st_size / 1024

    print("\n=== RESERVES INCLUDED (name, lon, lat, suggested_zoom, area_km2, iso3, no_take) ===")
    for s in summary:
        print(f"{s[0]:52} lon={s[1]:>9}  lat={s[2]:>8}  z={s[3]:>4}  area={s[4]:>11} km2  {s[5]}  no_take={s[6]}")
    print(f"\nwrote {len(feats)} reserves -> {OUT}  ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
