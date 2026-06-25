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


# GFW geartypes that count as fishing (matched detections of these are kept even
# when broadcasting; everything else relies on being dark to be flagged).
FISHING_GEARTYPES = {
    "FISHING", "TUNA_PURSE_SEINES", "PURSE_SEINES", "TRAWLERS", "DRIFTING_LONGLINES",
    "SET_LONGLINES", "SQUID_JIGGER", "POTS_AND_TRAPS", "FIXED_GEAR", "SET_GILLNETS",
}

_OPTIONAL = ("flag", "ship_name", "vessel_type", "geartype", "mmsi", "detections")


def _opt_float(p: dict, key: str):
    v = p.get(key)
    return float(v) if v is not None and v != "" else None


def load_sar_detections(path: str | Path | None = None) -> pd.DataFrame:
    """Read SAR detection points (GeoJSON) into a frame: lon, lat + properties.

    Handles two sources: the synthetic sample (carries length_m + fishing_score) and
    GFW API pulls (carry identity: flag/ship_name/vessel_type/geartype/mmsi but no
    length_m/fishing_score). Missing fields become None.
    """
    path = Path(path) if path is not None else DEFAULT_SAR_GEOJSON
    data = json.loads(path.read_text())
    rows = []
    for feat in data.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        p = feat.get("properties") or {}
        row = {
            "lon": float(geom["coordinates"][0]),
            "lat": float(geom["coordinates"][1]),
            "detection_time": p.get("detection_time"),
            "matched_to_ais": bool(p.get("matched_to_ais", False)),
            "length_m": _opt_float(p, "length_m"),
            "fishing_score": _opt_float(p, "fishing_score"),
        }
        for k in _OPTIONAL:
            if k not in row:
                row[k] = p.get(k)
        rows.append(row)
    return pd.DataFrame(rows)


def _sar_drivers(r: dict, mpa_name: str) -> list[str]:
    drivers = [f"inside MPA: {mpa_name}"]
    if not r["matched_to_ais"]:
        drivers.append("not broadcasting AIS (dark vessel)")
    else:
        who = r.get("ship_name") or (f"MMSI {r['mmsi']}" if r.get("mmsi") else "matched vessel")
        flag = f", flag {r['flag']}" if r.get("flag") else ""
        drivers.append(f"broadcasting AIS: {who}{flag}")
    if r.get("geartype"):
        drivers.append(f"gear type: {r['geartype']}")
    if r.get("fishing_score") is not None:
        drivers.append(f"GFW fishing-score: {r['fishing_score']:.2f}")
    if r.get("length_m") is not None:
        size = "industrial" if r["length_m"] >= 24 else "small"
        drivers.append(f"length: {r['length_m']:.0f} m ({size})")
    if r.get("detections"):
        drivers.append(f"satellite detections in window: {int(r['detections'])}")
    return drivers


def build_sar_dossiers(
    detections: pd.DataFrame,
    mpa_index: MPAIndex,
    *,
    min_fishing_score: float = 0.5,
    keep_geartypes: set | None = None,
    include_dark: bool = True,
    max_dossiers: int = 150,
) -> list[dict]:
    """Build dark-fleet / fishing-vessel-in-MPA dossiers from SAR detections.

    Keeps a detection inside an MPA when it is **dark** (unmatched, if
    ``include_dark``) OR its geartype is a fishing type. A ``fishing_score``, when
    present (Portal data), must be >= ``min_fishing_score``; when absent (API data)
    that filter is skipped. Caps output at ``max_dossiers`` (dark first, then by
    detection count) and logs how many were dropped.
    """
    if detections.empty:
        return []
    keep_geartypes = FISHING_GEARTYPES if keep_geartypes is None else keep_geartypes

    mpa_idx = mpa_index.assign(detections["lon"].to_numpy(), detections["lat"].to_numpy())
    wdpa_lut = np.array([m.wdpa_id for m in mpa_index.mpas], dtype=object)
    df = detections.copy()
    df["mpa_idx"] = mpa_idx
    df["mpa_name"] = mpa_index.names(mpa_idx)

    is_dark = ~df["matched_to_ais"].to_numpy(dtype=bool)
    is_fishing_gear = df["geartype"].isin(keep_geartypes).to_numpy() if "geartype" in df else np.zeros(len(df), bool)
    relevant = ((include_dark & is_dark) | is_fishing_gear)
    score = df["fishing_score"]
    score_ok = score.isna().to_numpy() | (score.fillna(0).to_numpy() >= min_fishing_score)
    df = df[(df["mpa_idx"].to_numpy() >= 0) & relevant & score_ok]
    if df.empty:
        return []

    # Dark first, then by detection count, so the cap keeps the strongest leads.
    df = df.assign(_dark=(~df["matched_to_ais"].astype(bool)).astype(int),
                   _det=df["detections"].fillna(1) if "detections" in df else 1)
    df = df.sort_values(["_dark", "_det"], ascending=[False, False])
    n_total = len(df)
    if n_total > max_dossiers:
        print(f"[sar] {n_total} relevant detections; capping dossiers at {max_dossiers} "
              f"(dropped {n_total - max_dossiers}). Raise max_dossiers to keep more.")
        df = df.head(max_dossiers)

    seq: dict[str, int] = {}
    dossiers = []
    for _, r in df.iterrows():
        # pandas turns missing values into float NaN (which is truthy) — normalize to None.
        rd = {k: (None if (isinstance(v, float) and v != v) else v) for k, v in r.to_dict().items()}
        mpa_name = str(rd["mpa_name"])
        n = seq.get(mpa_name, 0)
        seq[mpa_name] = n + 1
        dark = not rd["matched_to_ais"]
        wdpa_id = wdpa_lut[int(rd["mpa_idx"])]
        score_val = rd.get("fishing_score")
        if dark:
            vessel_id = "(dark -- no AIS identity)"
        else:
            vessel_id = rd.get("ship_name") or (f"MMSI {rd['mmsi']}" if rd.get("mmsi") else "(matched)")
        dossiers.append(
            {
                "type": "dark_vessel_sar",
                "incident_id": f"sar__{_slug(mpa_name)}_{n:04d}",
                "mpa_name": mpa_name,
                "wdpa_id": str(wdpa_id) if wdpa_id is not None else None,
                "vessel_id": vessel_id,
                "gear": ("SAR (dark)" if dark else f"SAR · {rd.get('geartype') or 'matched'}"),
                "flag": rd.get("flag"),
                "time_start_utc": rd["detection_time"],
                "time_end_utc": rd["detection_time"],
                "duration_hours": 0.0,
                "n_positions": 1,
                "n_fishing_positions": 1,
                "mean_fishing_proba": (float(score_val) if score_val is not None else None),
                "max_fishing_proba": (float(score_val) if score_val is not None else None),
                "centroid_lat": float(rd["lat"]),
                "centroid_lon": float(rd["lon"]),
                "length_m": (float(rd["length_m"]) if rd.get("length_m") is not None else None),
                "matched_to_ais": bool(rd["matched_to_ais"]),
                "explanation": {"method": _SAR_METHOD, "drivers": _sar_drivers(rd, mpa_name)},
                "caveats": CAVEATS_SAR,
            }
        )
    return dossiers


if __name__ == "__main__":
    idx = MPAIndex.from_geojson()
    dets = load_sar_detections()
    out = build_sar_dossiers(dets, idx)
    n_dark = sum(1 for d in out if d["matched_to_ais"] is False and "dark" in d["vessel_id"])
    print(f"{len(dets)} detections -> {len(out)} dossiers ({n_dark} dark)")
    for d in out[:8]:
        print(f"  {d['incident_id']}: {d['mpa_name']} | {d['gear']} | {d['vessel_id']}")
