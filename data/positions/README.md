# Bring-your-own AIS positions

`sample_positions.csv` shows the schema for scoring **your own** AIS/VMS feed with SeaVigil:

```bash
uv run python -m seavigil.alert --positions data/positions/sample_positions.csv --sample-sar
```

The model is trained on the GFW labels; `--positions` runs inference on new, unlabeled
positions. This is the real deployment model — a coastal authority runs SeaVigil **offline on
its own AIS/VMS data** (no cloud, no account).

## Required columns

`vessel_id, timestamp, lat, lon, speed, course` (plus optional `gear`). `timestamp` is epoch
seconds; speed in knots. CSV or Parquet. **`distance_from_shore` / `distance_from_port` are
optional** — if absent they're computed on load from bundled coastline + ports
(`seavigil.enrich`), so a raw AIS feed works directly.

## Fetch a real open AIS sample

```bash
python scripts/fetch_open_ais.py --n 3000 --out data/positions/gulf_ais_real.csv
uv run python -m seavigil.alert --positions data/positions/gulf_ais_real.csv
```

Pulls real US Gulf AIS (NOAA Marine Cadastre via HuggingFace, Apache-2.0, no account). The
open API caps at ~100 rows; for a fuller feed download NOAA daily AIS in bulk (same columns).
Verified: a transiting cargo vessel scores out-of-sample as expected (median fishing prob
0.01; only its slow points score high) — the model isn't fooled by fast transit.

## Why not pull AIS from GFW?

GFW does **not** redistribute raw AIS positions (speed/course per point), so the per-position
model can't be fed from GFW. GFW's consumable products are **SAR detections** (→ the
dark-vessel dossiers, see `seavigil/sar.py` and `seavigil/fetch_gfw.py`) and gridded apparent
fishing effort (heatmaps). Raw AIS for scoring comes from your own receiver or a commercial
provider (Spire, ORBCOMM, AISHub, a national VMS, …).
