"""Build static GeoJSON for the SeaVigil web map from a dossier set.

GitHub Pages is static and cannot call the GFW API from the browser (token in a
header, no CORS, non-commercial, rate limits). The pattern is precompute-and-ship-
static: this converts ``results/incidents/incidents.json`` (+ the MPA polygons)
into ``web/data/*.geojson`` that the browser loads directly. In production a
scheduled job pulls fresh GFW data and re-runs this; here it runs locally.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_JSON = ROOT / "results" / "incidents" / "incidents.json"
MPA_GEOJSON = ROOT / "data" / "mpa" / "sample_mpas.geojson"
WEB_DATA = ROOT / "web" / "data"


def _why(d: dict) -> str:
    expl = d.get("explanation")
    if not expl:
        return ""
    if "top_drivers" in expl:  # AIS: top SHAP drivers
        return "; ".join(
            f"{r['feature']} ({r['mean_shap']:+.2f})" for r in expl["top_drivers"][:3]
        )
    if "drivers" in expl:  # SAR: attribute bullets
        return "; ".join(expl["drivers"])
    return ""


def _count(dossiers: list[dict], key, default="unknown") -> dict:
    out: dict = {}
    for d in dossiers:
        k = d.get(key, default) if isinstance(key, str) else key(d)
        out[str(k)] = out.get(str(k), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def summarize(dossiers: list[dict]) -> dict:
    """Breakdown counts for the map's stats panel.

    Note: a *flag-state* breakdown (as in some monitors) is not possible here -- the
    GFW training labels are anonymized (no flag). That needs GFW vessel-identity data
    (a later, live-API step). We break down by what the data actually carries.
    """
    return {
        "total": len(dossiers),
        "by_type": _count(dossiers, "type", default="ais_fishing_incident"),
        "by_mpa": _count(dossiers, "mpa_name"),
        "by_gear": _count(dossiers, "gear"),
        # Flag-state breakdown is only populated when records carry a flag (real GFW
        # SAR matched detections); empty for the anonymized AIS training labels.
        "by_flag": _count([d for d in dossiers if d.get("flag")], "flag"),
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
                    "when": d["time_start_utc"],
                    "score": (round(float(d["mean_fishing_proba"]), 2)
                              if d.get("mean_fishing_proba") is not None else None),
                    "vessel": d.get("vessel_id", ""),
                    "gear": d.get("gear", ""),
                    "why": _why(d),
                    "caveat": (d.get("caveats") or [""])[0],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def build_site(
    incidents_json: str | Path = INCIDENTS_JSON,
    mpa_geojson: str | Path = MPA_GEOJSON,
    out_dir: str | Path = WEB_DATA,
) -> dict:
    """Write web/data/incidents.geojson and web/data/mpas.geojson."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dossiers = json.loads(Path(incidents_json).read_text())
    (out_dir / "incidents.geojson").write_text(
        json.dumps(incidents_to_geojson(dossiers))
    )
    (out_dir / "summary.json").write_text(json.dumps(summarize(dossiers)))

    # Sample MPA boxes pass through as-is. NOTE: real WDPA polygons are
    # non-commercial and must NOT be shipped as a downloadable GeoJSON -- convert
    # them to non-extractable vector tiles before deploying with real boundaries.
    mpas = json.loads(Path(mpa_geojson).read_text())
    (out_dir / "mpas.geojson").write_text(json.dumps(mpas))

    return {"n_records": len(dossiers), "out_dir": str(out_dir)}


if __name__ == "__main__":
    print(build_site())
