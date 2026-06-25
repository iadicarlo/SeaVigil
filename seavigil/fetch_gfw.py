"""Fetch real GFW Sentinel-1 SAR vessel detections for the dark-fleet dossiers.

GFW does NOT publish raw AIS positions (speed/course per point), so the per-position
model is fed by YOUR OWN AIS/VMS feed (see data.load_positions_file / alert --positions).
What GFW *does* publish consumably is SAR vessel detections (Paolo et al., Nature 2024):
this module pulls them via the 4Wings report API for a region + date range and writes a
GeoJSON the SAR dossier path (sar.py) consumes.

Each detection comes back matched or unmatched to AIS -- **unmatched = dark**. Matched
detections carry identity (flag, ship name, vessel type, gear). The API does NOT return
per-detection length_m / fishing_score (those are Data-Download-Portal only), so dossiers
built from API data use identity/geartype/dark-status as the rationale instead.

Auth: reads the token from the GFW_TOKEN env var (never hard-code it). Data is CC BY-NC
(non-commercial); attribute "Global Fishing Watch".

Run:  GFW_TOKEN=... uv run python -m seavigil.fetch_gfw --date-range 2024-01-01,2025-01-01
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

from seavigil.mpa import MPAIndex

ROOT = Path(__file__).resolve().parent.parent
REPORT_URL = "https://gateway.api.globalfishingwatch.org/v3/4wings/report"
SAR_DATASET = "public-global-sar-presence:latest"
DEFAULT_OUT = ROOT / "data" / "sar" / "gfw_sar_detections.geojson"


def _token(token: str | None) -> str:
    t = token or os.environ.get("GFW_TOKEN")
    if not t:
        raise RuntimeError("GFW_TOKEN not set — export it or pass token=… (see docs/DEPLOY.md)")
    return t


def parse_sar_report(payload: dict) -> list[dict]:
    """Flatten a 4Wings SAR report JSON into detection records (pure; no network)."""
    out: list[dict] = []
    for entry in payload.get("entries", []) or []:
        for _dataset_key, rows in entry.items():
            for r in rows or []:
                if r.get("lat") is None or r.get("lon") is None:
                    continue
                out.append(
                    {
                        "lon": float(r["lon"]),
                        "lat": float(r["lat"]),
                        "detection_time": r.get("entryTimestamp") or r.get("date"),
                        "matched_to_ais": bool(r.get("mmsi")),
                        "flag": r.get("flag") or None,
                        "ship_name": r.get("shipName") or None,
                        "vessel_type": r.get("vesselType") or None,
                        "geartype": r.get("geartype") or None,
                        "mmsi": r.get("mmsi") or None,
                        "detections": r.get("detections"),
                        # Present only in Data-Download-Portal exports, not the API:
                        "length_m": r.get("length_m"),
                        "fishing_score": r.get("fishing_score"),
                    }
                )
    return out


def fetch_sar_region(geometry: dict, date_range: str, *, token: str | None = None,
                     dataset: str = SAR_DATASET, timeout: int = 120) -> list[dict]:
    """Fetch SAR detections whose footprint falls in `geometry` over `date_range`.

    geometry: a GeoJSON geometry dict (Polygon). date_range: "YYYY-MM-DD,YYYY-MM-DD".
    """
    qs = (
        "spatial-resolution=HIGH&temporal-resolution=ENTIRE"
        f"&datasets[0]={dataset}&date-range={date_range}"
        "&format=JSON&spatial-aggregation=false"
    )
    resp = requests.post(
        f"{REPORT_URL}?{qs}",
        headers={"Authorization": f"Bearer {_token(token)}", "Content-Type": "application/json"},
        json={"geojson": geometry},
        timeout=timeout,
    )
    resp.raise_for_status()
    return parse_sar_report(resp.json())


def to_geojson(records: list[dict]) -> dict:
    feats = []
    for r in records:
        props = {k: v for k, v in r.items() if k not in ("lon", "lat")}
        feats.append(
            {"type": "Feature",
             "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
             "properties": props}
        )
    return {
        "type": "FeatureCollection",
        "_attribution": "Vessel detections: Global Fishing Watch (CC BY-NC 4.0), Paolo et al. Nature 2024.",
        "features": feats,
    }


def fetch_sar_for_mpas(mpa_index: MPAIndex, date_range: str, out_path: str | Path = DEFAULT_OUT,
                       *, token: str | None = None) -> dict:
    """Fetch SAR detections for every MPA polygon and write one GeoJSON."""
    token = _token(token)
    records: list[dict] = []
    for m in mpa_index.mpas:
        geom = m.geometry.__geo_interface__
        recs = fetch_sar_region(geom, date_range, token=token)
        for r in recs:
            r["queried_mpa"] = m.name
        records.extend(recs)
        print(f"[fetch_gfw] {m.name}: {len(recs)} detections")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(to_geojson(records)))
    n_dark = sum(1 for r in records if not r["matched_to_ais"])
    print(f"[fetch_gfw] wrote {len(records)} detections ({n_dark} dark) -> {out_path}")
    return {"n": len(records), "n_dark": n_dark, "out": str(out_path)}


def main() -> dict:
    ap = argparse.ArgumentParser(description="Fetch GFW SAR detections for the MPA set")
    ap.add_argument("--date-range", default="2024-01-01,2025-01-01", help="YYYY-MM-DD,YYYY-MM-DD")
    ap.add_argument("--mpa", default=None, help="MPA GeoJSON (default: bundled sample)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    return fetch_sar_for_mpas(MPAIndex.from_geojson(args.mpa), args.date_range, args.out)


if __name__ == "__main__":
    main()
