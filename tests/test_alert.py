"""Offline wiring test for the alert entrypoint (score -> overlay -> incident -> dossier).

Does not touch the network or the real dataset; uses a synthetic feature frame, a
tiny fitted model, and a custom MPA box.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from shapely.geometry import Polygon
from sklearn.ensemble import RandomForestClassifier

from seavigil import alert, mpa
from seavigil.features import FEATURE_COLUMNS


def _fit_low_speed_is_fishing():
    rng = np.random.default_rng(1)
    n = 300
    fishing = rng.random(n) < 0.5
    cols = {c: rng.normal(size=n) for c in FEATURE_COLUMNS}
    cols["speed"] = np.where(fishing, rng.uniform(0, 2, n), rng.uniform(7, 12, n))
    X = pd.DataFrame(cols)[FEATURE_COLUMNS].to_numpy()
    rf = RandomForestClassifier(n_estimators=40, random_state=1, min_samples_leaf=5)
    rf.fit(X, fishing.astype(int))
    return rf


def _feats_frame():
    """Two vessels: vA fishes inside the unit-square MPA, vB fishes far outside it."""
    base = 1_350_000_000
    rows = []
    for k in range(4):  # vA inside box [0,1]x[0,1], slow -> fishing
        rows.append({"vessel_id": "vA", "gear": "trawlers", "lon": 0.5, "lat": 0.5,
                     "timestamp": float(base + k * 600), "speed": 1.0})
    for k in range(3):  # vB far outside, slow
        rows.append({"vessel_id": "vB", "gear": "trawlers", "lon": 50.0, "lat": 50.0,
                     "timestamp": float(base + k * 600), "speed": 1.0})
    df = pd.DataFrame(rows)
    rng = np.random.default_rng(2)
    for c in FEATURE_COLUMNS:
        if c not in df.columns:
            df[c] = rng.normal(size=len(df))
    df["turning_rate"] = 12.0
    df["label"] = 1
    return df


def _box_index():
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    return mpa.MPAIndex([mpa.MPA(name="Test Reserve", geometry=poly)])


def test_score_positions_assigns_mpa_and_proba():
    rf = _fit_low_speed_is_fishing()
    feats = _feats_frame()
    scored = alert.score_positions(feats, rf, _box_index())

    assert "fishing_proba" in scored and "mpa_idx" in scored and "datetime" in scored
    inside = scored[scored["vessel_id"] == "vA"]
    outside = scored[scored["vessel_id"] == "vB"]
    assert (inside["mpa_idx"] == 0).all()
    assert (inside["mpa_name"] == "Test Reserve").all()
    assert (outside["mpa_idx"] == -1).all()
    assert (inside["fishing_proba"] > 0.5).all()  # slow vessel -> flagged fishing


def test_run_alert_writes_one_incident(tmp_path):
    rf = _fit_low_speed_is_fishing()
    scored = alert.score_positions(_feats_frame(), rf, _box_index())
    manifest = alert.run_alert(scored, rf, out_dir=tmp_path)

    assert manifest["n_incidents"] == 1
    data = json.loads((tmp_path / "incidents.json").read_text())
    assert data[0]["mpa_name"] == "Test Reserve"
    assert data[0]["vessel_id"] == "vA"
    assert data[0]["explanation"] is not None
    assert (tmp_path / "INDEX.md").exists()
