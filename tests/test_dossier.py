"""Tests for dossier building and rendering (incident -> JSON/Markdown + SHAP)."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from seavigil import dossier, incidents
from seavigil.features import FEATURE_COLUMNS


def _tiny_model_and_scored():
    """A small fitted RF plus a scored frame carrying FEATURE_COLUMNS + scoring cols.

    Low speed / high turning -> fishing, so SHAP should rank `speed` highly.
    """
    rng = np.random.default_rng(0)
    n = 200
    fishing = rng.random(n) < 0.5
    speed = np.where(fishing, rng.uniform(0, 2, n), rng.uniform(7, 12, n))
    feats = {c: rng.normal(size=n) for c in FEATURE_COLUMNS}
    feats["speed"] = speed
    feats["turning_rate"] = np.where(fishing, rng.uniform(8, 20, n), rng.uniform(0, 3, n))
    X = pd.DataFrame(feats)[FEATURE_COLUMNS]
    y = fishing.astype(int)
    rf = RandomForestClassifier(n_estimators=40, random_state=0, min_samples_leaf=5)
    rf.fit(X.to_numpy(), y)
    return rf, X


def _scored_with_incident(rf, X):
    # Take 4 clearly-fishing rows (low speed) inside one MPA, same vessel.
    proba = rf.predict_proba(X.to_numpy())[:, 1]
    fish_rows = np.argsort(proba)[::-1][:4]  # most-fishing rows
    sub = X.iloc[fish_rows].reset_index(drop=True).copy()
    base = 1_350_000_000
    sub["vessel_id"] = "vA"
    sub["gear"] = "trawlers"
    sub["timestamp"] = [float(base + k * 600) for k in range(len(sub))]
    sub["datetime"] = pd.to_datetime(sub["timestamp"], unit="s", utc=True)
    sub["lat"] = -0.5
    sub["lon"] = -91.0
    sub["fishing_proba"] = proba[fish_rows]
    sub["mpa_idx"] = 0
    sub["mpa_name"] = "Galápagos Marine Reserve"
    sub["wdpa_id"] = None
    return sub


def test_build_dossier_has_explanation_and_caveats():
    rf, X = _tiny_model_and_scored()
    scored = _scored_with_incident(rf, X)
    inc = incidents.build_incidents(scored, proba_threshold=0.5)
    assert len(inc) == 1

    dossiers = dossier.build_dossiers(inc, scored, rf)
    assert len(dossiers) == 1
    d = dossiers[0]
    assert d["explanation"] is not None
    assert len(d["explanation"]["top_drivers"]) == 5
    assert {dr["feature"] for dr in d["explanation"]["top_drivers"]} <= set(FEATURE_COLUMNS)
    assert d["caveats"] == dossier.CAVEATS
    assert "fishing_ids" not in d  # internal pointer dropped


def test_render_markdown_contains_key_fields():
    rf, X = _tiny_model_and_scored()
    scored = _scored_with_incident(rf, X)
    inc = incidents.build_incidents(scored)
    md = dossier.render_markdown(dossier.build_dossiers(inc, scored, rf)[0])
    assert "Galápagos Marine Reserve" in md
    assert "Why this was flagged" in md
    assert "Caveats" in md
    assert "inspection lead" in md.lower()


def test_build_without_model_skips_explanation():
    rf, X = _tiny_model_and_scored()
    scored = _scored_with_incident(rf, X)
    inc = incidents.build_incidents(scored)
    d = dossier.build_dossiers(inc, scored, None)[0]
    assert d["explanation"] is None
    assert d["caveats"] == dossier.CAVEATS  # facts + caveats still stand


def test_write_dossiers_creates_files(tmp_path):
    rf, X = _tiny_model_and_scored()
    scored = _scored_with_incident(rf, X)
    inc = incidents.build_incidents(scored)
    dossiers = dossier.build_dossiers(inc, scored, rf)
    manifest = dossier.write_dossiers(dossiers, tmp_path)

    assert manifest["n_incidents"] == 1
    assert (tmp_path / "incidents.json").exists()
    assert (tmp_path / "INDEX.md").exists()
    loaded = json.loads((tmp_path / "incidents.json").read_text())
    assert loaded[0]["mpa_name"] == "Galápagos Marine Reserve"
    assert (tmp_path / f"{loaded[0]['incident_id']}.md").exists()


def test_shap_is_sampled_for_large_incidents():
    rf, X = _tiny_model_and_scored()
    scored = _scored_with_incident(rf, X)
    # Inflate the incident to 120 fishing positions by repeating rows.
    big = pd.concat([scored] * 30, ignore_index=True)
    base = 1_350_000_000
    big["timestamp"] = [float(base + k * 60) for k in range(len(big))]
    big["datetime"] = pd.to_datetime(big["timestamp"], unit="s", utc=True)
    inc = incidents.build_incidents(big)
    assert inc[0].n_fishing_positions > 50

    d = dossier.build_dossiers(inc, big, rf, max_shap_per_incident=50)[0]
    assert "sampled 50 of" in d["explanation"]["method"]
    assert len(d["explanation"]["top_drivers"]) == 5


def test_write_empty_dossiers(tmp_path):
    manifest = dossier.write_dossiers([], tmp_path)
    assert manifest["n_incidents"] == 0
    assert "No incidents found." in (tmp_path / "INDEX.md").read_text()
