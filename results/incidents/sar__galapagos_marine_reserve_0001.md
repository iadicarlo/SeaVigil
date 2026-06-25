# Dark-vessel detection `sar__galapagos_marine_reserve_0001`

- **MPA:** Galápagos Marine Reserve
- **Vessel:** (dark -- no AIS identity)  ·  **source:** SAR (dark)
- **When (UTC):** 2024-03-01T05:10:00Z
- **Length:** 61 m  ·  **broadcasting AIS:** no (dark)  ·  **GFW fishing-score:** 0.88
- **Where:** -0.200, -90.500

## Why this was flagged

_SAR detection attributes (no AIS track or identity; not SHAP-explainable)._

- inside MPA: Galápagos Marine Reserve
- not broadcasting AIS (dark vessel)
- GFW fishing-score: 0.88
- length: 61 m (industrial)

## Caveats

- Dark vessel: detected by satellite SAR but not broadcasting AIS.
- Not SHAP-explainable -- a SAR detection has no movement track to attribute.
- length_m and fishing_score are GFW model estimates from imagery, not ground truth.
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
