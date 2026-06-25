"""Tests for distance enrichment + auto-enrich on raw AIS positions."""

from __future__ import annotations

import pandas as pd

from seavigil import data, enrich


def test_add_distances_open_ocean_vs_coastal():
    # mid-Pacific (far from everything) vs a point near the English coast.
    df = pd.DataFrame({"lon": [-140.0, 0.0], "lat": [0.0, 51.5]})
    e = enrich.add_distances(df)
    assert {"distance_from_shore", "distance_from_port"} <= set(e.columns)
    assert (e["distance_from_shore"] >= 0).all()
    # Open ocean is much farther from shore than the coastal point.
    assert e["distance_from_shore"].iloc[0] > e["distance_from_shore"].iloc[1]
    assert e["distance_from_port"].iloc[1] < 5e5  # coastal point is near a port


def test_load_positions_auto_enriches_when_distances_absent(tmp_path):
    p = tmp_path / "ais.csv"
    pd.DataFrame({
        "vessel_id": ["a", "a"], "timestamp": [1_700_000_000, 1_700_000_600],
        "lat": [25.70, 25.80], "lon": [-95.10, -95.20], "speed": [10.0, 1.0],
        "course": [90.0, 120.0],
    }).to_csv(p, index=False)
    df = data.load_positions_file(p)  # no distance columns -> enriched
    assert {"distance_from_shore", "distance_from_port"} <= set(df.columns)
    assert (df["distance_from_shore"] > 0).all()


def test_load_positions_respects_supplied_distances(tmp_path):
    p = tmp_path / "ais.csv"
    pd.DataFrame({
        "vessel_id": ["a"], "timestamp": [1_700_000_000], "lat": [25.7], "lon": [-95.1],
        "speed": [1.0], "course": [90.0],
        "distance_from_shore": [12345.0], "distance_from_port": [67890.0],
    }).to_csv(p, index=False)
    df = data.load_positions_file(p)  # distances present -> used as-is, not recomputed
    assert df["distance_from_shore"].iloc[0] == 12345.0
    assert df["distance_from_port"].iloc[0] == 67890.0
