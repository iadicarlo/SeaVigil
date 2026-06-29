#!/usr/bin/env python3
"""Merge freshly streamed AIS positions into the rolling buffer and prune to the last N
hours, so the spoofing detector accumulates enough per-vessel track across cron runs.
The buffer is persisted between runs by the GitHub Actions cache (it is not committed).

    uv run python scripts/update_ais_buffer.py --new data/positions/ais_new.csv \
        --buffer data/positions/ais_buffer.csv --hours 12
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Append new AIS positions to the rolling buffer")
    ap.add_argument("--new", required=True, help="freshly streamed positions CSV")
    ap.add_argument("--buffer", required=True, help="rolling buffer CSV (read + rewritten)")
    ap.add_argument("--hours", type=float, default=12.0, help="keep only the last N hours")
    a = ap.parse_args()

    frames = []
    for path in (a.buffer, a.new):
        p = Path(path)
        if p.exists():
            try:
                frames.append(pd.read_csv(p))
            except pd.errors.EmptyDataError:
                pass
    if not frames:
        print("no positions to buffer (nothing streamed yet)")
        return

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["vessel_id", "timestamp", "lat", "lon"])
    if "timestamp" in df.columns and len(df):
        tmax = float(df["timestamp"].max())
        df = df[df["timestamp"] >= tmax - a.hours * 3600.0]

    buf = Path(a.buffer)
    buf.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(buf, index=False)
    vc = df["vessel_id"].value_counts()
    print(f"buffer: {len(df)} positions, {df['vessel_id'].nunique()} vessels, "
          f"{int((vc >= 3).sum())} with >=3 fixes (last {a.hours:g} h) -> {buf}")


if __name__ == "__main__":
    main()
