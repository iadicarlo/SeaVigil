"""Build static GeoJSON for the SeaVigil web map from a dossier set.

GitHub Pages is static and cannot call the GFW API from the browser (token in a
header, no CORS, non-commercial, rate limits). The pattern is precompute-and-ship-
static: this converts ``results/incidents/incidents.json`` (+ the MPA polygons)
into ``web/data/*.geojson`` that the browser loads directly. In production a
scheduled job pulls fresh GFW data and re-runs this; here it runs locally.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from seavigil import evidence
from seavigil.flags import emoji_for, to_iso2

ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_JSON = ROOT / "results" / "incidents" / "incidents.json"
MPA_GEOJSON = ROOT / "data" / "mpa" / "sample_mpas.geojson"
WEB_DATA = ROOT / "web" / "data"


def _why(d: dict, *, full: bool = False) -> str:
    expl = d.get("explanation")
    if not expl:
        return ""
    if "top_drivers" in expl:  # AIS: SHAP drivers
        rows = expl["top_drivers"] if full else expl["top_drivers"][:3]
        return " · ".join(f"{r['feature']} ({r['mean_shap']:+.2f})" for r in rows)
    if "drivers" in expl:  # SAR: attribute bullets
        return " · ".join(expl["drivers"])
    return ""


def _baseline_line(d: dict) -> str:
    if d.get("baseline_agreement") is None:
        return ""
    agree = d["baseline_agreement"] * 100
    tail = f"; model adds {100 - agree:.0f}%" if (100 - agree) >= 1 else "; rule alone suffices"
    return f"speed rule (<{d['baseline_speed_threshold_knots']} kn) flags {agree:.0f}%{tail}"


def _count(dossiers: list[dict], key, default="unknown") -> dict:
    out: dict = {}
    for d in dossiers:
        k = d.get(key, default) if isinstance(key, str) else key(d)
        out[str(k)] = out.get(str(k), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def summarize(dossiers: list[dict]) -> dict:
    """Breakdown counts for the map's stats panel.

    The flag-state tally normalizes every code to ISO2 first (sources mix ISO2 and ISO3,
    so otherwise one country splits across two rows). The anonymized AIS training labels
    carry no flag and simply do not contribute to it.
    """
    return {
        "total": len(dossiers),
        "by_type": _count(dossiers, "type", default="ais_fishing_incident"),
        "by_severity": _count([d for d in dossiers if d.get("severity")], "severity"),
        "by_mpa": _count(dossiers, "mpa_name"),
        # Jurisdiction (EEZ) breakdown: every incident inside an EEZ worldwide carries one.
        "by_eez": _count([d for d in dossiers if d.get("eez_name")], "eez_name"),
        "by_gear": _count(dossiers, "gear"),
        # Flag-state breakdown, keyed by normalized ISO2 so codes do not double-count.
        "by_flag": _count(
            [d for d in dossiers if d.get("flag")],
            lambda d: to_iso2(d.get("flag")) or str(d.get("flag")).strip().upper(),
        ),
        # Authorization status: foreign vessels graded against registry/RFMO records.
        "by_authorization": _count(
            [d for d in dossiers if d.get("authorization_status")], "authorization_status"),
    }


def incidents_to_geojson(dossiers: list[dict]) -> dict:
    features = []
    for d in dossiers:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [d["centroid_lon"], d["centroid_lat"]],
                },
                "properties": {
                    "id": d["incident_id"],
                    "kind": d.get("type", "ais_fishing_incident"),
                    "mpa": d["mpa_name"],
                    "severity": d.get("severity") or "",
                    "severity_reason": d.get("severity_reason") or "",
                    "when": d["time_start_utc"],
                    "score": (round(float(d["mean_fishing_proba"]), 2)
                              if d.get("mean_fishing_proba") is not None else None),
                    "vessel": d.get("vessel_id", ""),
                    "ship_name": d.get("ship_name") or "",
                    "ship_type": d.get("ship_type") or "",
                    "destination": d.get("destination") or "",
                    "gear": d.get("gear", ""),
                    "flag": to_iso2(d.get("flag")) or (d.get("flag") or ""),
                    "flag_emoji": emoji_for(d.get("flag")),
                    "eez": d.get("eez_name") or "",
                    "eez_sovereign": d.get("eez_sovereign") or "",
                    "eez_foreign": d.get("eez_foreign"),
                    "authorization": d.get("authorization_status") or "",
                    "authorities": ", ".join(d.get("authorization_authorities") or []),
                    "imo": d.get("registry_imo") or "",
                    "evidence_hash": d.get("evidence_hash") or "",
                    "evidence_schema": d.get("evidence_schema") or "",
                    "why": _why(d),
                    "why_full": _why(d, full=True),
                    "baseline": _baseline_line(d),
                    # whole caveat list joined for the full dossier view
                    "caveats": " | ".join(d.get("caveats") or []),
                    "caveat": (d.get("caveats") or [""])[0],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def build_site(
    incidents_json: str | Path = INCIDENTS_JSON,
    mpa_geojson: str | Path = MPA_GEOJSON,  # kept for signature compatibility; unused
    out_dir: str | Path = WEB_DATA,
) -> dict:
    """Write web/data/incidents.geojson, tracks.geojson and summary.json.

    MPA boundaries are NOT written here: the real WDPA polygons are non-commercial
    and may not be shipped as a downloadable GeoJSON, so the map renders them from
    non-extractable vector tiles (web/tiles/mpas.pmtiles) built by
    scripts/extract_showcase_mpas.py + tippecanoe instead.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dossiers = json.loads(Path(incidents_json).read_text())
    (out_dir / "incidents.geojson").write_text(
        json.dumps(incidents_to_geojson(dossiers))
    )
    summary = summarize(dossiers)
    summary["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cal = evidence.calibration_summary()
    if cal:
        summary["model_calibration"] = cal
    (out_dir / "summary.json").write_text(json.dumps(summary))

    # Tracks are written alongside incidents.json by dossier.write_dossiers; copy
    # the LineStrings through to the web data (incidents.json itself is track-free).
    tracks_src = Path(incidents_json).parent / "tracks.geojson"
    tracks = (json.loads(tracks_src.read_text()) if tracks_src.exists()
              else {"type": "FeatureCollection", "features": []})
    (out_dir / "tracks.geojson").write_text(json.dumps(tracks))

    return {"n_records": len(dossiers), "out_dir": str(out_dir)}


if __name__ == "__main__":
    print(build_site())
