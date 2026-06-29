"""Detect suspected AIS disabling ("going dark") from continuous AIS tracks.

A fishing vessel that broadcasts steadily, then stops for a long stretch far from
shore, then reappears, may have intentionally disabled its transponder, a known IUU
behavior. This reproduces the core of Global Fishing Watch's published methodology
(Welch et al., Science Advances 2022, DOI 10.1126/sciadv.abq2109): an intentional
disabling gap is a gap of at least 12 hours that begins well offshore (so it is not a
port stop), with good AIS coverage in the hours just before (so the silence is not a
reception artifact). Each event records the exact criteria it meets, so the dossier
shows an auditable pass/fail table rather than a black-box flag, and it is always
phrased as "suspected disabling", never "illegal".

Needs a positions frame with vessel_id, timestamp (epoch s), lat, lon, speed, and
distance_from_shore (metres, from seavigil.enrich).
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd

NM_M = 1852.0

CAVEATS = [
    "Suspected AIS disabling, not proven and not necessarily illegal.",
    "A gap can also be a receiver outage, satellite coverage hole, or equipment fault.",
    "Reproduces Welch et al. (2022) intentional-disabling criteria; an inspection lead.",
    "AIS identity (MMSI/name) can itself be spoofed; verify against authoritative records.",
]
_METHOD = "AIS gap analysis (Welch et al. 2022 intentional-disabling criteria)"


def _haversine_nm(lon1, lat1, lon2, lat2) -> float:
    r = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return float(2 * r * np.arcsin(np.sqrt(a)) / NM_M)


_GFW_CAVEATS = [
    "Suspected intentional AIS disabling (Global Fishing Watch, Welch et al. 2022).",
    "A gap can also be a receiver outage or coverage hole; GFW's filter targets disabling.",
    "Apparent, not proven illegal; an inspection lead.",
    "GFW data is CC BY-NC; only derived in-EEZ dossiers are shown here, with attribution.",
]
_GFW_METHOD = "GFW satellite AIS-disabling events (Welch et al. 2022, DOI 10.1126/sciadv.abq2109)"


def build_from_gfw_disabling(
    csv_path: str | Path,
    eez_index,
    *,
    max_events: int = 40,
    cap_per_eez: int = 10,
    min_gap_hours: float = 18.0,
    max_gap_hours: float = 168.0,
) -> list[dict]:
    """Build going-dark dossiers from GFW's published satellite disabling events.

    Terrestrial AIS cannot see offshore disabling, so the showcase consumes GFW's
    satellite-detected events (the same consume-not-recompute pattern as the SAR dark
    fleet) and adds the explanation + evidence layer. Events inside any coastal-state
    EEZ worldwide are kept, selected round-robin across EEZs and by gap-start time for
    a spread of durations (high-seas disabling, outside every EEZ, is not tagged here).
    """
    cand = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r["gap_start_lat"])
                lon = float(r["gap_start_lon"])
                gap_h = float(r["gap_hours"])
            except (ValueError, KeyError):
                continue
            if not (min_gap_hours <= gap_h <= max_gap_hours):
                continue  # plausible disabling window (skip implausible months-long gaps)
            r["_gap"] = gap_h
            cand.append((r, lon, lat))

    idx = eez_index.assign_many([c[1] for c in cand], [c[2] for c in cand])
    rows = []
    for (r, _lon, _lat), fi in zip(cand, idx):
        if fi < 0:
            continue
        r["_eez"] = eez_index.features[int(fi)]["properties"].get("name")
        rows.append(r)

    by_eez: dict = {}
    # Sort by time for a spread of gap durations (not just the longest outliers).
    for r in sorted(rows, key=lambda r: r.get("gap_start_timestamp") or ""):
        by_eez.setdefault(r["_eez"], []).append(r)

    picked: list[dict] = []
    buckets = list(by_eez.values())
    per_eez: dict = {}
    while len(picked) < max_events:
        progressed = False
        for b in buckets:
            if b and per_eez.get(b[0]["_eez"], 0) < cap_per_eez:
                r = b.pop(0)
                per_eez[r["_eez"]] = per_eez.get(r["_eez"], 0) + 1
                picked.append(r)
                progressed = True
            if len(picked) >= max_events:
                break
        if not progressed:  # every remaining bucket is empty or capped
            break

    dossiers = []
    for seq, r in enumerate(picked):
        s_lat, s_lon = float(r["gap_start_lat"]), float(r["gap_start_lon"])
        e_lat, e_lon = float(r["gap_end_lat"]), float(r["gap_end_lon"])
        off_nm = float(r.get("gap_start_distance_from_shore_m") or 0) / NM_M
        disp_nm = _haversine_nm(s_lon, s_lat, e_lon, e_lat)
        gap_h = r["_gap"]
        flag = (r.get("flag") or "").strip()
        length = r.get("vessel_length_m")
        drivers = [
            f"went dark {off_nm:.0f} nm offshore for {gap_h:.0f} h",
            f"reappeared {disp_nm:.0f} nm away",
            "satellite-confirmed disabling event (GFW)",
        ]
        if length:
            try:
                drivers.append(f"vessel length {float(length):.0f} m")
            except ValueError:
                pass
        dossiers.append({
            "type": "ais_disabling",
            "incident_id": f"darkgap__{r.get('mmsi', seq)}_{seq:04d}",
            "mpa_name": "AIS disabling",
            "severity": "high" if gap_h >= 24 else "medium",
            "severity_reason": "suspected intentional AIS disabling offshore",
            "vessel_id": str(r.get("mmsi") or "(unknown)"),
            "ship_name": "",
            "flag": flag,
            "ship_type": (r.get("vessel_class") or "vessel").title(),
            "gear": "AIS gap",
            "time_start_utc": (r.get("gap_start_timestamp") or "")[:19].replace(" ", "T") + "Z",
            "time_end_utc": (r.get("gap_end_timestamp") or "")[:19].replace(" ", "T") + "Z",
            "duration_hours": round(gap_h, 1),
            "n_positions": 0, "n_fishing_positions": 0,
            "mean_fishing_proba": None, "max_fishing_proba": None,
            "centroid_lat": s_lat, "centroid_lon": s_lon,
            "gap_hours": round(gap_h, 1),
            "off_distance_nm": round(off_nm, 1),
            "displacement_nm": round(disp_nm, 1),
            "track": [[s_lon, s_lat], [e_lon, e_lat]],
            "explanation": {"method": _GFW_METHOD, "drivers": drivers},
            "caveats": _GFW_CAVEATS,
        })
    return dossiers


def build_disabling_dossiers(
    df: pd.DataFrame,
    *,
    min_gap_hours: float = 12.0,
    min_offshore_nm: float = 50.0,
    min_positions_before: int = 14,
    before_window_hours: float = 12.0,
    max_events_per_vessel: int = 2,
    region_label: str = "AIS disabling",
) -> list[dict]:
    """Return dark-gap dossier dicts (type ``ais_disabling``) from continuous tracks."""
    needed = {"vessel_id", "timestamp", "lat", "lon", "distance_from_shore"}
    if not needed.issubset(df.columns):
        raise ValueError(f"missing columns: {needed - set(df.columns)}")

    dossiers: list[dict] = []
    seq = 0
    for mmsi, g in df.groupby("vessel_id"):
        g = g.sort_values("timestamp")
        t = g["timestamp"].to_numpy(dtype="float64")
        lat = g["lat"].to_numpy(dtype="float64")
        lon = g["lon"].to_numpy(dtype="float64")
        dshore = g["distance_from_shore"].to_numpy(dtype="float64")
        name = next((str(v) for v in g.get("ship_name", pd.Series([], dtype=object)) if v), "")
        flag = next((str(v) for v in g.get("flag", pd.Series([], dtype=object)) if v), "")
        n = len(g)
        if n < 2:
            continue
        per_vessel = 0
        for i in range(n - 1):
            gap_h = (t[i + 1] - t[i]) / 3600.0
            off_nm = dshore[i] / NM_M
            before = int(((t > t[i] - before_window_hours * 3600) & (t <= t[i])).sum())
            checks = [
                ("gap >= 12 h", min_gap_hours, round(gap_h, 1), gap_h >= min_gap_hours),
                ("offshore > 50 nm", min_offshore_nm, round(off_nm, 1), off_nm >= min_offshore_nm),
                (f"coverage before (>={min_positions_before} fixes / {before_window_hours:.0f} h)",
                 min_positions_before, before, before >= min_positions_before),
            ]
            if not all(c[3] for c in checks):
                continue
            disp_nm = _haversine_nm(lon[i], lat[i], lon[i + 1], lat[i + 1])
            off_iso = pd.to_datetime(t[i], unit="s", utc=True).strftime("%Y-%m-%dT%H:%M:%SZ")
            on_iso = pd.to_datetime(t[i + 1], unit="s", utc=True).strftime("%Y-%m-%dT%H:%M:%SZ")
            drivers = [
                f"went dark {off_nm:.0f} nm offshore for {gap_h:.1f} h",
                f"reappeared {disp_nm:.0f} nm away",
                f"{before} AIS fixes in the {before_window_hours:.0f} h before going dark "
                "(so not a reception gap)",
            ]
            dossiers.append({
                "type": "ais_disabling",
                "incident_id": f"darkgap__{mmsi}_{seq:04d}",
                "mpa_name": region_label,
                "severity": "high",
                "severity_reason": "suspected intentional AIS disabling offshore",
                "vessel_id": str(mmsi),
                "ship_name": name,
                "flag": flag,
                "ship_type": "Fishing",
                "gear": "AIS gap",
                "time_start_utc": off_iso,
                "time_end_utc": on_iso,
                "duration_hours": round(gap_h, 1),
                "n_positions": n,
                "n_fishing_positions": 0,
                "mean_fishing_proba": None,
                "max_fishing_proba": None,
                "centroid_lat": float(lat[i]),
                "centroid_lon": float(lon[i]),
                "gap_hours": round(gap_h, 1),
                "off_distance_nm": round(off_nm, 1),
                "displacement_nm": round(disp_nm, 1),
                # the dark segment: where it vanished -> where it returned
                "track": [[float(lon[i]), float(lat[i])], [float(lon[i + 1]), float(lat[i + 1])]],
                "criteria": [{"check": c[0], "threshold": c[1], "measured": c[2], "met": c[3]}
                             for c in checks],
                "explanation": {"method": _METHOD, "drivers": drivers},
                "caveats": CAVEATS,
            })
            seq += 1
            per_vessel += 1
            if per_vessel >= max_events_per_vessel:
                break
    return dossiers
