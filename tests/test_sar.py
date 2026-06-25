"""Tests for dark-fleet SAR detection dossiers."""

from __future__ import annotations

import json

from seavigil import dossier, sar
from seavigil.mpa import MPAIndex


def _index():
    return MPAIndex.from_geojson()  # bundled approximate sample MPAs


def test_load_sample_sar_detections():
    dets = sar.load_sar_detections()
    assert len(dets) == 7
    assert {"lon", "lat", "length_m", "fishing_score", "matched_to_ais"} <= set(dets.columns)


def test_dark_in_mpa_filtering():
    dets = sar.load_sar_detections()
    out = sar.build_sar_dossiers(dets, _index())  # dark_only, min_score 0.5
    # Galápagos x2, GBR x1, Papahanaumokuakea x1 (matched / low-score / open-ocean dropped).
    assert len(out) == 4
    mpas = sorted({d["mpa_name"] for d in out})
    assert "Galápagos Marine Reserve" in mpas
    assert all(d["type"] == "dark_vessel_sar" for d in out)
    assert all(d["matched_to_ais"] is False for d in out)
    assert all("drivers" in d["explanation"] for d in out)
    assert all("not broadcasting AIS (dark vessel)" in d["explanation"]["drivers"] for d in out)


def test_matched_detection_excluded_unless_dark_only_false():
    dets = sar.load_sar_detections()
    with_matched = sar.build_sar_dossiers(dets, _index(), dark_only=False)
    assert len(with_matched) == 5  # the matched Galápagos detection now included


def test_high_score_threshold_narrows():
    dets = sar.load_sar_detections()
    strict = sar.build_sar_dossiers(dets, _index(), min_fishing_score=0.9)
    assert len(strict) == 1  # only the 0.92 detection survives


def test_no_detections_returns_empty():
    import pandas as pd

    assert sar.build_sar_dossiers(pd.DataFrame(), _index()) == []


def test_render_sar_dossier_markdown():
    out = sar.build_sar_dossiers(sar.load_sar_detections(), _index())
    md = dossier.render_markdown(out[0])
    assert "Dark-vessel detection" in md
    assert "broadcasting AIS:** no (dark)" in md
    assert "Why this was flagged" in md
    assert "not broadcasting AIS" in md
    assert "inspection lead" in md.lower()


def test_write_mixed_index(tmp_path):
    sar_dossiers = sar.build_sar_dossiers(sar.load_sar_detections(), _index())
    # Fake one AIS dossier dict to mix in.
    ais = {
        "type": "ais_fishing_incident", "incident_id": "x_0000", "mpa_name": "Galápagos Marine Reserve",
        "wdpa_id": None, "vessel_id": "v", "gear": "trawlers",
        "time_start_utc": "2014-01-01T00:00:00Z", "time_end_utc": "2014-01-01T01:00:00Z",
        "duration_hours": 1.0, "n_positions": 2, "n_fishing_positions": 2,
        "mean_fishing_proba": 0.8, "max_fishing_proba": 0.9, "centroid_lat": -0.5, "centroid_lon": -91.0,
        "explanation": None, "caveats": dossier.CAVEATS,
    }
    manifest = dossier.write_dossiers([ais] + sar_dossiers, tmp_path)
    assert manifest["n_incidents"] == 5
    index = (tmp_path / "INDEX.md").read_text()
    assert "AIS fishing incident(s)" in index and "dark-vessel SAR detection(s)" in index
    assert "dark SAR" in index and "AIS fishing" in index
    loaded = json.loads((tmp_path / "incidents.json").read_text())
    assert any(d["type"] == "dark_vessel_sar" for d in loaded)
