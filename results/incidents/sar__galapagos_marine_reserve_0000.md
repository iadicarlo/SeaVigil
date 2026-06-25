# Dark-vessel detection `sar__galapagos_marine_reserve_0000`

- **MPA:** Galápagos Marine Reserve
- **Vessel:** (dark -- no AIS identity)  ·  **source:** SAR detection
- **When (UTC):** 2024-03-01T04:00:00Z
- **Length:** 48 m  ·  **broadcasting AIS:** no (dark)  ·  **GFW fishing-score:** 0.92
- **Where:** -0.500, -91.000

## Why this was flagged

_SAR detection attributes (no AIS track or identity; not SHAP-explainable)._

- inside MPA: Galápagos Marine Reserve
- not broadcasting AIS (dark vessel)
- GFW fishing-score: 0.92
- length: 48 m (industrial)

## Caveats

- Dark vessel: detected by satellite SAR but not broadcasting AIS.
- Not SHAP-explainable -- a SAR detection has no movement track to attribute.
- length_m and fishing_score are GFW model estimates from imagery, not ground truth.
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
