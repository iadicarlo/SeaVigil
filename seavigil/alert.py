"""SeaVigil v2 entrypoint: fishing-inside-an-MPA alerting.

Pipeline:
  1. load + clean GFW labeled positions, build features,
  2. vessel-grouped split, train the random forest on the train vessels,
  3. score positions (held-out test vessels by default; --scope all for everything),
  4. overlay scored positions onto MPA boundaries,
  5. segment in-MPA fishing into incidents,
  6. write a SHAP-backed dossier per incident to results/incidents/.

Run with:  uv run python -m seavigil.alert
           uv run python -m seavigil.alert --mpa path/to/wdpa.geojson --scope test

The scoring is out-of-sample by default (test vessels the model never saw), so the
alerts are honest. --scope all scores every position, including in-sample train
vessels -- useful to exercise the mechanism, but those scores are fitted, not
generalization estimates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from seavigil import data, dossier, features, incidents, model, sar
from seavigil.features import FEATURE_COLUMNS
from seavigil.mpa import MPAIndex

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def _grouped_split_indices(feats: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Positional train/test row indices with whole vessels on one side only."""
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=model.TEST_SIZE, random_state=model.RANDOM_STATE
    )
    groups = feats["vessel_id"].to_numpy()
    train_idx, test_idx = next(splitter.split(feats, feats["label"].to_numpy(), groups))
    return train_idx, test_idx


def score_positions(feats: pd.DataFrame, rf, mpa_index: MPAIndex, *, scope_rows=None) -> pd.DataFrame:
    """Attach fishing_proba, UTC datetime, and MPA assignment to a positions frame."""
    scope = feats if scope_rows is None else feats.iloc[scope_rows]
    scored = scope.copy()
    scored["fishing_proba"] = rf.predict_proba(scored[FEATURE_COLUMNS].to_numpy())[:, 1]
    scored["datetime"] = pd.to_datetime(scored["timestamp"], unit="s", utc=True)

    mpa_idx = mpa_index.assign(scored["lon"].to_numpy(), scored["lat"].to_numpy())
    scored["mpa_idx"] = mpa_idx
    scored["mpa_name"] = mpa_index.names(mpa_idx)

    wdpa_lut = np.array([m.wdpa_id for m in mpa_index.mpas], dtype=object)
    wdpa = np.full(len(scored), None, dtype=object)
    inside = mpa_idx >= 0
    wdpa[inside] = wdpa_lut[mpa_idx[inside]]
    scored["wdpa_id"] = wdpa
    return scored


def run_alert(
    scored: pd.DataFrame,
    rf,
    *,
    threshold: float = incidents.DEFAULT_PROBA_THRESHOLD,
    gap_minutes: float = incidents.DEFAULT_GAP_MINUTES,
    out_dir: str | Path = RESULTS / "incidents",
) -> dict:
    """Build incidents + dossiers from a scored frame and write them out."""
    incs = incidents.build_incidents(
        scored, proba_threshold=threshold, gap_minutes=gap_minutes
    )
    dossiers = dossier.build_dossiers(incs, scored, rf)
    manifest = dossier.write_dossiers(dossiers, out_dir)
    return manifest


def main() -> dict:
    parser = argparse.ArgumentParser(description="SeaVigil fishing-in-MPA alerting")
    parser.add_argument("--mpa", default=None, help="GeoJSON of MPA polygons (default: bundled sample)")
    parser.add_argument("--positions", default=None,
                        help="score an external AIS positions file (CSV/Parquet) instead of the GFW labels")
    parser.add_argument("--scope", choices=["test", "all"], default="test",
                        help="score held-out test vessels (default) or all positions (ignored with --positions)")
    parser.add_argument("--threshold", type=float, default=incidents.DEFAULT_PROBA_THRESHOLD)
    parser.add_argument("--gap-minutes", type=float, default=incidents.DEFAULT_GAP_MINUTES)
    parser.add_argument("--sar", default=None, help="GeoJSON of SAR vessel detections (dark fleet)")
    parser.add_argument("--sample-sar", action="store_true", help="use the bundled synthetic SAR sample")
    parser.add_argument("--sar-min-score", type=float, default=0.5)
    parser.add_argument("--out", default=str(RESULTS / "incidents"))
    args = parser.parse_args()

    print("[alert] 1/5 loading + cleaning data ...")
    clean = data.load_clean()

    print("[alert] 2/5 building features + training the model ...")
    feats = features.build_features(clean)
    mpa_index = MPAIndex.from_geojson(args.mpa)

    if args.positions:
        # Train on ALL labeled data; score the external (BYO / live-GFW) positions.
        rf = model.train_model(feats[FEATURE_COLUMNS].to_numpy(), feats["label"].to_numpy())
        ext = features.build_features(data.load_positions_file(args.positions))
        print(f"[alert] 3/5 scoring {len(ext):,} external positions "
              f"({args.positions}) against {len(mpa_index)} MPAs ...")
        scored = score_positions(ext, rf, mpa_index)
        scope_desc = f"positions:{args.positions}"
    else:
        train_idx, test_idx = _grouped_split_indices(feats)
        rf = model.train_model(
            feats.iloc[train_idx][FEATURE_COLUMNS].to_numpy(),
            feats.iloc[train_idx]["label"].to_numpy(),
        )
        print(f"[alert] 3/5 scoring scope='{args.scope}' against {len(mpa_index)} MPAs ...")
        if args.scope == "all":
            print("[alert]   note: --scope all includes in-sample train vessels (fitted scores).")
        scope_rows = None if args.scope == "all" else test_idx
        scored = score_positions(feats, rf, mpa_index, scope_rows=scope_rows)
        scope_desc = args.scope

    n_inside = int((scored["mpa_idx"] >= 0).sum())
    print(f"[alert]   {n_inside:,} of {len(scored):,} scored positions fall inside an MPA")

    print("[alert] 4/5 segmenting incidents (AIS) ...")
    incs = incidents.build_incidents(
        scored, proba_threshold=args.threshold, gap_minutes=args.gap_minutes
    )
    dossiers = dossier.build_dossiers(incs, scored, rf)
    n_ais = len(dossiers)

    n_sar = 0
    if args.sar is not None or args.sample_sar:
        dets = sar.load_sar_detections(args.sar)  # None -> bundled sample
        sar_dossiers = sar.build_sar_dossiers(
            dets, mpa_index, min_fishing_score=args.sar_min_score
        )
        dossiers += sar_dossiers
        n_sar = len(sar_dossiers)
        print(f"[alert]   {len(dets)} SAR detections -> {n_sar} dark-vessel-in-MPA dossiers")

    print("[alert] 5/5 writing dossiers ...")
    manifest = dossier.write_dossiers(dossiers, args.out)

    summary = {
        "scope": scope_desc,
        "positions_source": args.positions,
        "mpa_source": args.mpa or "bundled sample (approximate)",
        "sar_source": (args.sar or "bundled sample") if (args.sar or args.sample_sar) else None,
        "n_mpas": len(mpa_index),
        "n_scored_positions": int(len(scored)),
        "n_positions_in_mpa": n_inside,
        "proba_threshold": args.threshold,
        "gap_minutes": args.gap_minutes,
        "n_incidents": manifest["n_incidents"],
        "n_ais_incidents": n_ais,
        "n_dark_vessel_sar": n_sar,
        "out_dir": manifest["out_dir"],
    }
    Path(args.out).mkdir(parents=True, exist_ok=True)
    (Path(args.out) / "alert_summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\n[alert] done. {manifest['n_incidents']} incident(s) -> {manifest['out_dir']}")
    return summary


if __name__ == "__main__":
    main()
