"""Turn in-MPA fishing incidents into auditable dossiers.

A dossier is the artifact a human acts on: the incident facts (who/where/when/how
strong) plus the model's *reason* -- the SHAP attribution averaged over the
incident's fishing positions -- plus the standing honesty caveats. Rendered both
as JSON (machine) and Markdown (human).

SHAP is computed once across all incidents' fishing positions, then sliced per
incident, reusing the positive-class machinery from ``explain.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from seavigil.explain import _positive_class_shap
from seavigil.authorization import summary_label as authorization_label
from seavigil.features import FEATURE_COLUMNS
from seavigil.flags import emoji_for
from seavigil.mpa import grade_severity

_IDENTITY = ("ship_name", "flag", "destination", "ship_type")


def _na(v):
    return None if (isinstance(v, float) and v != v) else v

# Carried into every dossier so a flag is never read without its limits.
CAVEATS = [
    "Apparent fishing inferred from AIS movement, not proven illegal fishing.",
    "AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).",
    "MPA boundary may be approximate; verify against official WDPA limits.",
    "An inspection lead, not courtroom evidence.",
]

_SHAP_METHOD = "mean per-position SHAP (fishing class) over the incident's fishing positions"


def _aggregate_shap(values: np.ndarray, X: np.ndarray, feature_columns, top_k: int) -> list[dict]:
    mean_shap = values.mean(axis=0)
    mean_val = X.mean(axis=0)
    order = np.argsort(np.abs(mean_shap))[::-1][:top_k]
    return [
        {
            "feature": feature_columns[i],
            "mean_value": round(float(mean_val[i]), 4),
            "mean_shap": round(float(mean_shap[i]), 4),
        }
        for i in order
    ]


def build_dossiers(
    incidents,
    scored,
    model,
    *,
    feature_columns: list[str] = FEATURE_COLUMNS,
    top_k: int = 5,
    max_shap_per_incident: int = 50,
    random_state: int = 42,
    baseline_threshold: float | None = None,
) -> list[dict]:
    """Build dossier dicts for a list of incidents.

    If ``model`` is None, dossiers are built without a SHAP explanation (the facts
    still stand). Otherwise SHAP is computed once over the incidents' fishing
    positions. To stay fast on large incidents, SHAP is estimated from at most
    ``max_shap_per_incident`` positions per incident (the per-incident mean is
    well estimated from a sample); the dossier still reports the full counts.
    """
    if not incidents:
        return []

    explanations: dict = {}
    if model is not None:
        rng = np.random.default_rng(random_state)
        sampled_ids: dict = {}
        for inc in incidents:
            ids = inc.fishing_ids
            if len(ids) > max_shap_per_incident:
                pick = sorted(rng.choice(len(ids), size=max_shap_per_incident, replace=False))
                ids = [ids[i] for i in pick]
            sampled_ids[inc.incident_id] = ids

        all_ids = sorted({i for ids in sampled_ids.values() for i in ids}, key=str)
        X_all = scored.loc[all_ids, feature_columns].to_numpy(dtype="float64")
        import shap  # local import: heavy, only needed when explaining

        shap_all = _positive_class_shap(shap.TreeExplainer(model), X_all)
        row_of = {rid: r for r, rid in enumerate(all_ids)}
        for inc in incidents:
            rows = [row_of[i] for i in sampled_ids[inc.incident_id]]
            n_full = len(inc.fishing_ids)
            method = _SHAP_METHOD
            if n_full > max_shap_per_incident:
                method += f" (sampled {max_shap_per_incident} of {n_full})"
            explanations[inc.incident_id] = {
                "method": method,
                "top_drivers": _aggregate_shap(
                    shap_all[rows], X_all[rows], feature_columns, top_k
                ),
            }

    dossiers = []
    for inc in incidents:
        d = inc.to_dict()
        ids = d.pop("fishing_ids", None)  # internal pointer, not part of the dossier
        d["type"] = "ais_fishing_incident"
        sev, reason = grade_severity(d.get("mpa_iucn_cat"), d.get("mpa_no_take"))
        d["severity"], d["severity_reason"] = sev, reason
        # Vessel identity (present for live / BYO AIS; absent for anonymized labels).
        if ids:
            for col in _IDENTITY:
                if col in scored.columns:
                    d[col] = _na(scored.loc[ids[0], col])
        # Does the trivial tuned speed-rule also flag these positions, or is the
        # model earning its complexity here?
        if baseline_threshold is not None and ids:
            speeds = scored.loc[ids, "speed"].to_numpy(dtype="float64")
            d["baseline_speed_threshold_knots"] = round(float(baseline_threshold), 2)
            d["baseline_agreement"] = round(float((speeds < baseline_threshold).mean()), 3)
        d["explanation"] = explanations.get(inc.incident_id)
        d["caveats"] = CAVEATS
        dossiers.append(d)
    return dossiers


def render_markdown(dossier: dict) -> str:
    """Render one dossier (AIS incident with SHAP, or SAR dark-vessel detection)."""
    d = dossier
    is_sar = d.get("type") == "dark_vessel_sar"
    title = "Dark-vessel detection" if is_sar else "Incident"

    lines = [
        f"# {title} `{d['incident_id']}`",
        "",
        f"- **MPA:** {d['mpa_name']}"
        + (f" (WDPA {d['wdpa_id']})" if d.get("wdpa_id") else ""),
    ]
    if d.get("severity"):
        ver = f"  ·  boundary {d['mpa_version']}" if d.get("mpa_version") else ""
        lines.append(
            f"- **Severity:** {d['severity'].upper()} ({d.get('severity_reason', '')}){ver}"
        )
    if d.get("eez_name"):
        foreign = d.get("eez_foreign")
        tag = (" -- FOREIGN-flagged vessel" if foreign is True
               else "  (flag matches coastal state)" if foreign is False else "")
        lines.append(f"- **EEZ:** {d['eez_name']} ({d.get('eez_sovereign')}){tag}")
    if d.get("authorization_status"):
        imo = d.get("registry_imo")
        imo_str = f"  ·  IMO {imo}" if imo else ""
        lines.append(f"- **Authorization:** {authorization_label(d)}{imo_str}")
    if is_sar:
        broadcasting = "yes" if d.get("matched_to_ais") else "no (dark)"
        length_str = f"{d['length_m']:.0f} m" if d.get("length_m") is not None else "n/a"
        score = d.get("mean_fishing_proba")
        score_str = f"{score:.2f}" if score is not None else "n/a (Portal-only)"
        flag_str = (f"  ·  **flag:** {emoji_for(d.get('flag'))} {d['flag']}".rstrip()
                    if d.get("flag") else "")
        lines += [
            f"- **Vessel:** {d['vessel_id']}  ·  **source:** {d['gear']}{flag_str}",
            f"- **When (UTC):** {d['time_start_utc']}",
            f"- **Length:** {length_str}  ·  **broadcasting AIS:** {broadcasting}  ·  "
            f"**GFW fishing-score:** {score_str}",
            f"- **Where:** {d['centroid_lat']:.3f}, {d['centroid_lon']:.3f}",
            "",
        ]
    elif d.get("type") in ("ais_disabling", "ais_spoofing", "encounter"):
        flag_e = emoji_for(d.get("flag"))
        who = (f"{flag_e} " if flag_e else "") + (
            d["ship_name"] if d.get("ship_name") else f"`{d['vessel_id']}`")
        if d.get("type") == "ais_disabling":
            metric = (f"- **Gap:** {d.get('gap_hours')} h dark, {d.get('off_distance_nm')} nm "
                      f"offshore, reappeared {d.get('displacement_nm')} nm away")
        elif d.get("type") == "encounter":
            metric = (f"- **Encounter:** {d.get('duration_hours')} h with carrier "
                      f"`{d.get('carrier_mmsi', '?')}` (apparent transshipment)")
        else:
            metric = (f"- **Anomalies:** {d.get('anomaly_count')} impossible movements; "
                      f"max implied speed {d.get('max_implied_speed_kn', 0):,.0f} kn; "
                      f"positions span {d.get('spread_nm', 0):,.0f} nm")
        lines += [
            f"- **Vessel:** {who}  ·  **signal:** {d['gear']}",
            f"- **When (UTC):** {d['time_start_utc']} → {d['time_end_utc']}",
            metric,
            f"- **Where:** {d['centroid_lat']:.3f}, {d['centroid_lon']:.3f}",
            "",
        ]
    else:
        flag_e = emoji_for(d.get("flag"))
        who = (f"{flag_e} " if flag_e else "") + (
            d["ship_name"] if d.get("ship_name") else f"`{d['vessel_id']}`")
        extra = []
        if d.get("ship_type"):
            extra.append(str(d["ship_type"]))
        if d.get("destination"):
            extra.append(f"to {d['destination']}")
        extra_s = ("  ·  " + "  ·  ".join(extra)) if extra else ""
        ais_lines = [
            f"- **Vessel:** {who}  ·  **gear:** {d['gear']}{extra_s}",
            f"- **When (UTC):** {d['time_start_utc']} → {d['time_end_utc']} "
            f"({d['duration_hours']} h)",
            f"- **Apparent fishing:** {d['n_fishing_positions']} of {d['n_positions']} "
            f"in-MPA positions; mean p={d['mean_fishing_proba']:.2f}, "
            f"max p={d['max_fishing_proba']:.2f}",
            f"- **Where:** {d['centroid_lat']:.3f}, {d['centroid_lon']:.3f} (centroid)",
        ]
        trk = d.get("track") or []
        if len(trk) >= 2:
            (lo0, la0), (lo1, la1) = trk[0], trk[-1]
            ais_lines.append(
                f"- **Track:** {d['n_positions']} positions, "
                f"({la0:.3f}, {lo0:.3f}) → ({la1:.3f}, {lo1:.3f})"
            )
        if d.get("baseline_agreement") is not None:
            agree = d["baseline_agreement"] * 100
            tail = (f"; the model additionally flags the other {100 - agree:.0f}%."
                    if (100 - agree) >= 1 else "; here the speed rule alone suffices.")
            ais_lines.append(
                f"- **Vs. speed baseline:** the trivial rule (speed < "
                f"{d['baseline_speed_threshold_knots']} kn) also flags {agree:.0f}% of "
                f"these positions{tail}"
            )
        lines += ais_lines + [""]

    expl = d.get("explanation")
    if expl:
        lines += ["## Why this was flagged", "", f"_{expl['method']}._", ""]
        if "top_drivers" in expl:  # AIS: SHAP table
            lines += ["| feature | mean value | mean SHAP |", "|---|---:|---:|"]
            for row in expl["top_drivers"]:
                lines.append(
                    f"| `{row['feature']}` | {row['mean_value']:.3f} | "
                    f"{row['mean_shap']:+.3f} |"
                )
        elif "drivers" in expl:  # SAR: attribute bullets (no movement track to SHAP)
            lines += [f"- {x}" for x in expl["drivers"]]
        lines.append("")

    lines += ["## Caveats", ""]
    lines += [f"- {c}" for c in d["caveats"]]
    lines.append("")

    if d.get("evidence_hash"):
        from seavigil.evidence import DISCLAIMER, calibration_summary, provenance_for  # noqa: PLC0415
        lines += ["## Provenance & integrity", ""]
        for s in provenance_for(d.get("type")):
            ver = f", {s['version']}" if s.get("version") else ""
            lines.append(f"- {s['dataset']} ({s['reference']}{ver}). {s['license']}.")
        if d.get("type") == "ais_fishing_incident":
            cal = calibration_summary()
            if cal:
                lines.append(f"- **Model confidence:** {cal['statement']}")
        lines += [
            f"- **Integrity (SHA-256 of canonical facts):** `{d['evidence_hash']}`",
            f"- **Evidence schema:** {d.get('evidence_schema', '')}",
            "",
            f"_{DISCLAIMER}_",
            "",
        ]
    return "\n".join(lines)


def write_dossiers(dossiers: list[dict], out_dir: str | Path) -> dict:
    """Write incidents.json, per-incident Markdown, and an INDEX.md summary.

    Returns a small manifest of what was written.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Render Markdown first (it uses the per-incident track), then write tracks to
    # their own GeoJSON and a SLIM incidents.json (track stripped - it would bloat
    # the machine artifact ~20x).
    md_paths = []
    for d in dossiers:
        p = out_dir / f"{d['incident_id']}.md"
        p.write_text(render_markdown(d))
        md_paths.append(p.name)

    track_feats = [
        {"type": "Feature",
         "geometry": {"type": "LineString", "coordinates": d["track"]},
         "properties": {"id": d["incident_id"], "kind": d.get("type", "ais_fishing_incident")}}
        for d in dossiers if len(d.get("track") or []) >= 2
    ]
    (out_dir / "tracks.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": track_feats})
    )

    slim = [{k: v for k, v in d.items() if k != "track"} for d in dossiers]
    (out_dir / "incidents.json").write_text(json.dumps(slim, indent=2))

    index = ["# In-MPA records", ""]
    if not dossiers:
        index += ["No records found.", ""]
    else:
        n_sar = sum(1 for d in dossiers if d.get("type") == "dark_vessel_sar")
        n_ais = len(dossiers) - n_sar
        index += [
            f"{len(dossiers)} record(s): {n_ais} AIS fishing incident(s), "
            f"{n_sar} dark-vessel SAR detection(s).",
            "",
        ]
        index += ["| id | type | MPA | start (UTC) | score / mean p |", "|---|---|---|---|---:|"]
        for d in dossiers:
            typ = "dark SAR" if d.get("type") == "dark_vessel_sar" else "AIS fishing"
            score = d.get("mean_fishing_proba")
            score_s = f"{score:.2f}" if score is not None else "-"
            index.append(
                f"| [{d['incident_id']}]({d['incident_id']}.md) | {typ} | {d['mpa_name']} | "
                f"{d['time_start_utc']} | {score_s} |"
            )
        index.append("")
    (out_dir / "INDEX.md").write_text("\n".join(index))

    return {
        "out_dir": str(out_dir),
        "n_incidents": len(dossiers),
        "json": "incidents.json",
        "index": "INDEX.md",
        "markdown": md_paths,
    }
