# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0011`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-13T19:07:29Z → 2014-12-13T19:07:29Z (0.0 h)
- **Apparent fishing:** 2 of 8 in-MPA positions; mean p=0.52, max p=0.52
- **Where:** -3.374, -170.439 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `distance_from_shore` | 48413.688 | -0.026 |
| `speed` | 7.400 | -0.025 |
| `distance_from_port` | 154543.938 | +0.025 |
| `hour_sin` | -0.958 | +0.024 |
| `speed_roll_std` | 0.184 | +0.015 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
