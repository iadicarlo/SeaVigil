# Dark-vessel detection `sar__great_barrier_reef_marine_park_0000`

- **MPA:** Great Barrier Reef Marine Park
- **Vessel:** (dark -- no AIS identity)  ·  **source:** SAR (dark)
- **When (UTC):** 2024-03-02T18:30:00Z
- **Length:** 40 m  ·  **broadcasting AIS:** no (dark)  ·  **GFW fishing-score:** 0.85
- **Where:** -18.000, 147.000

## Why this was flagged

_SAR detection attributes (no AIS track or identity; not SHAP-explainable)._

- inside MPA: Great Barrier Reef Marine Park
- not broadcasting AIS (dark vessel)
- GFW fishing-score: 0.85
- length: 40 m (industrial)

## Caveats

- Dark vessel: detected by satellite SAR but not broadcasting AIS.
- Not SHAP-explainable -- a SAR detection has no movement track to attribute.
- length_m and fishing_score are GFW model estimates from imagery, not ground truth.
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
