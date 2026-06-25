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
from seavigil.features import FEATURE_COLUMNS

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
        d.pop("fishing_ids", None)  # internal pointer, not part of the dossier
        d["type"] = "ais_fishing_incident"
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
    if is_sar:
        broadcasting = "yes" if d.get("matched_to_ais") else "no (dark)"
        length_str = f"{d['length_m']:.0f} m" if d.get("length_m") is not None else "n/a"
        score = d.get("mean_fishing_proba")
        score_str = f"{score:.2f}" if score is not None else "n/a (Portal-only)"
        flag_str = f"  ·  **flag:** {d['flag']}" if d.get("flag") else ""
        lines += [
            f"- **Vessel:** {d['vessel_id']}  ·  **source:** {d['gear']}{flag_str}",
            f"- **When (UTC):** {d['time_start_utc']}",
            f"- **Length:** {length_str}  ·  **broadcasting AIS:** {broadcasting}  ·  "
            f"**GFW fishing-score:** {score_str}",
            f"- **Where:** {d['centroid_lat']:.3f}, {d['centroid_lon']:.3f}",
            "",
        ]
    else:
        lines += [
            f"- **Vessel:** `{d['vessel_id']}`  ·  **gear:** {d['gear']}",
            f"- **When (UTC):** {d['time_start_utc']} → {d['time_end_utc']} "
            f"({d['duration_hours']} h)",
            f"- **Apparent fishing:** {d['n_fishing_positions']} of {d['n_positions']} "
            f"in-MPA positions; mean p={d['mean_fishing_proba']:.2f}, "
            f"max p={d['max_fishing_proba']:.2f}",
            f"- **Where:** {d['centroid_lat']:.3f}, {d['centroid_lon']:.3f} (centroid)",
            "",
        ]

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
    return "\n".join(lines)


def write_dossiers(dossiers: list[dict], out_dir: str | Path) -> dict:
    """Write incidents.json, per-incident Markdown, and an INDEX.md summary.

    Returns a small manifest of what was written.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "incidents.json").write_text(json.dumps(dossiers, indent=2))

    md_paths = []
    for d in dossiers:
        p = out_dir / f"{d['incident_id']}.md"
        p.write_text(render_markdown(d))
        md_paths.append(p.name)

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
            score_s = f"{score:.2f}" if score is not None else "—"
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
