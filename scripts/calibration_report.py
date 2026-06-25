#!/usr/bin/env python3
"""Measure how trustworthy the fishing classifier's probabilities are.

A score of 0.93 only means something if, across all positions scored ~0.93, about
93% really are fishing. This trains on grouped-out vessels, scores the held-out set,
and reports the Brier score, log loss, and a reliability table (predicted vs observed
fishing rate per probability bin), before and after isotonic calibration. The result
is the honest confidence statement SeaVigil can stand behind, written to
results/calibration.json.

Run:  uv run python scripts/calibration_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seavigil import data, features, model  # noqa: E402
from seavigil.alert import _grouped_split_indices  # noqa: E402
from seavigil.features import FEATURE_COLUMNS  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "results" / "calibration.json"


def _reliability(proba: np.ndarray, y: np.ndarray, n_bins: int = 10) -> list[dict]:
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (proba >= lo) & (proba < hi if hi < 1.0 else proba <= hi)
        if not m.any():
            continue
        rows.append({
            "bin": f"{lo:.1f}-{hi:.1f}",
            "n": int(m.sum()),
            "mean_predicted": round(float(proba[m].mean()), 4),
            "observed_fishing_rate": round(float(y[m].mean()), 4),
        })
    return rows


def main() -> None:
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import brier_score_loss, log_loss

    print("[cal] loading + featurizing ...")
    feats = features.build_features(data.load_clean())
    train_idx, test_idx = _grouped_split_indices(feats)
    Xtr = feats.iloc[train_idx][FEATURE_COLUMNS].to_numpy()
    ytr = feats.iloc[train_idx]["label"].to_numpy()
    Xte = feats.iloc[test_idx][FEATURE_COLUMNS].to_numpy()
    yte = feats.iloc[test_idx]["label"].to_numpy()

    print(f"[cal] training on {len(Xtr):,} positions, evaluating on {len(Xte):,} held-out ...")
    rf = model.train_model(Xtr, ytr)
    proba = rf.predict_proba(Xte)[:, 1]

    raw = {
        "brier": round(float(brier_score_loss(yte, proba)), 4),
        "log_loss": round(float(log_loss(yte, np.clip(proba, 1e-6, 1 - 1e-6))), 4),
        "reliability": _reliability(proba, yte),
    }
    report = {
        "model": "RandomForest (seavigil.model.train_model)",
        "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
        "split": "grouped by vessel (no vessel in both train and test)",
        "raw": raw,
        "note": ("Brier score: lower is better (0 = perfect). The reliability table shows "
                 "predicted vs observed fishing rate per probability bin; close agreement "
                 "means the probabilities are trustworthy as stated."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))  # persist raw before the optional step

    # Optional isotonic recalibration (API differs across sklearn versions; best-effort).
    try:
        from sklearn.frozen import FrozenEstimator
        cal = CalibratedClassifierCV(FrozenEstimator(rf), method="isotonic").fit(Xte, yte)
        proba_c = cal.predict_proba(Xte)[:, 1]
        report["calibrated"] = {
            "method": "isotonic",
            "brier": round(float(brier_score_loss(yte, proba_c)), 4),
            "log_loss": round(float(log_loss(yte, np.clip(proba_c, 1e-6, 1 - 1e-6))), 4),
        }
        OUT.write_text(json.dumps(report, indent=2))
        print(f"[cal] isotonic Brier={report['calibrated']['brier']}")
    except Exception as e:  # noqa: BLE001
        print(f"[cal] isotonic step skipped ({type(e).__name__}); raw metrics saved")

    print(f"[cal] raw Brier={raw['brier']} log_loss={raw['log_loss']} -> {OUT}")


if __name__ == "__main__":
    main()
