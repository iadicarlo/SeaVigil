"""Dark-fleet dossiers from satellite SAR vessel detections.

Consumes GFW's already-processed Sentinel-1 SAR detections (Paolo et al., Nature
2024) -- no imagery, CNN, or GPU. Each detection is a point with an estimated
length, a fishing score, and an AIS match flag; an **unmatched** detection is a
**dark** vessel (present but not broadcasting AIS).

These flow through the same MPA overlay as AIS positions (``mpa.py``) but produce
a *distinct* dossier type: a SAR detection has no movement track and no AIS
identity, so the per-position SHAP model cannot explain it. Its rationale is
attribute-based (length + fishing-score + not-broadcasting + inside-MPA), which
is often a *stronger* lead -- a dark, industrial-sized vessel inside a no-take MPA.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from seavigil.incidents import _slug
from seavigil.mpa import MPAIndex

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SAR_GEOJSON = ROOT / "data" / "sar" / "sample_sar_detections.geojson"

CAVEATS_SAR = [
    "Dark vessel: detected by satellite SAR but not broadcasting AIS.",
    "Not SHAP-explainable -- a SAR detection has no movement track to attribute.",
    "length_m and fishing_score are GFW model estimates from imagery, not ground truth.",
    "MPA boundary may be approximate; verify against official WDPA limits.",
    "An inspection lead, not courtroom evidence.",
]

_SAR_METHOD = "SAR detection attributes (no AIS track or identity; not SHAP-explainable)"


def load_sar_detections(path: str | Path | None = None) -> pd.DataFrame:
    """Read SAR detection points (GeoJSON) into a frame: lon, lat + properties.

    Expected per-feature properties: detection_time (ISO), length_m, fishing_score,
    matched_to_ais (bool). Missing fields are tolerated with sensible defaults.
    """
    path = Path(path) if path is not None else DEFAULT_SAR_GEOJSON
    data = json.loads(path.read_text())
    rows = []
    for feat in data.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"][0], geom["coordinates"][1]
        p = feat.get("properties") or {}
        rows.append(
            {
                "lon": float(lon),
                "lat": float(lat),
                "detection_time": p.get("detection_time"),
                "length_m": float(p.get("length_m", float("nan"))),
                "fishing_score": float(p.get("fishing_score", float("nan"))),
                "matched_to_ais": bool(p.get("matched_to_ais", False)),
            }
        )
    return pd.DataFrame(rows)


def build_sar_dossiers(
    detections: pd.DataFrame,
    mpa_index: MPAIndex,
    *,
    dark_only: bool = True,
    min_fishing_score: float = 0.5,
    min_length_m: float = 0.0,
) -> list[dict]:
    """Build dark-vessel dossiers for SAR detections that fall inside an MPA.

    By default keeps only **dark** (unmatched) detections with a fishing score
    above ``min_fishing_score`` -- the actionable "dark vessel apparently fishing
    inside a protected area" leads.
    """
    if detections.empty:
        return []

    mpa_idx = mpa_index.assign(detections["lon"].to_numpy(), detections["lat"].to_numpy())
    names = mpa_index.names(mpa_idx)
    wdpa_lut = np.array([m.wdpa_id for m in mpa_index.mpas], dtype=object)

    df = detections.copy()
    df["mpa_idx"] = mpa_idx
    df["mpa_name"] = names

    keep = df["mpa_idx"] >= 0
    if dark_only:
        keep &= ~df["matched_to_ais"].to_numpy(dtype=bool)
    keep &= df["fishing_score"].to_numpy() >= min_fishing_score
    keep &= df["length_m"].fillna(0.0).to_numpy() >= min_length_m
    df = df[keep]
    if df.empty:
        return []

    seq: dict[str, int] = {}
    dossiers = []
    for _, r in df.sort_values("detection_time").iterrows():
        mpa_name = str(r["mpa_name"])
        wdpa_id = wdpa_lut[int(r["mpa_idx"])]
        n = seq.get(mpa_name, 0)
        seq[mpa_name] = n + 1
        score = float(r["fishing_score"])
        length = float(r["length_m"])
        size_note = "industrial" if length >= 24 else "small"
        drivers = [
            f"inside MPA: {mpa_name}",
            "not broadcasting AIS (dark vessel)",
            f"GFW fishing-score: {score:.2f}",
            f"length: {length:.0f} m ({size_note})",
        ]
        dossiers.append(
            {
                "type": "dark_vessel_sar",
                "incident_id": f"sar__{_slug(mpa_name)}_{n:04d}",
                "mpa_name": mpa_name,
                "wdpa_id": str(wdpa_id) if wdpa_id is not None else None,
                "vessel_id": "(dark -- no AIS identity)",
                "gear": "SAR detection",
                "time_start_utc": r["detection_time"],
                "time_end_utc": r["detection_time"],
                "duration_hours": 0.0,
                "n_positions": 1,
                "n_fishing_positions": 1,
                "mean_fishing_proba": score,
                "max_fishing_proba": score,
                "centroid_lat": float(r["lat"]),
                "centroid_lon": float(r["lon"]),
                "length_m": length,
                "matched_to_ais": bool(r["matched_to_ais"]),
                "explanation": {"method": _SAR_METHOD, "drivers": drivers},
                "caveats": CAVEATS_SAR,
            }
        )
    return dossiers


if __name__ == "__main__":
    idx = MPAIndex.from_geojson()
    dets = load_sar_detections()
    out = build_sar_dossiers(dets, idx)
    print(f"{len(dets)} detections -> {len(out)} dark-vessel-in-MPA dossiers")
    for d in out:
        print(f"  {d['incident_id']}: {d['mpa_name']} len={d['length_m']:.0f}m score={d['mean_fishing_proba']:.2f}")
