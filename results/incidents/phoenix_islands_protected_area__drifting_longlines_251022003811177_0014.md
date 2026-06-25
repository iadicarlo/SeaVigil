# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0014`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-15T06:25:57Z → 2014-12-15T08:53:04Z (2.452 h)
- **Apparent fishing:** 98 of 98 in-MPA positions; mean p=0.93, max p=0.97
- **Where:** -3.475, -170.915 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 98)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 3.426 | +0.173 |
| `speed_roll_mean` | 3.502 | +0.172 |
| `speed_roll_std` | 0.740 | +0.035 |
| `distance_from_shore` | 35579.989 | +0.026 |
| `hour_sin` | 0.896 | +0.008 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
