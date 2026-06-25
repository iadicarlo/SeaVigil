# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0006`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-05T22:31:41Z → 2014-12-06T03:55:45Z (5.401 h)
- **Apparent fishing:** 96 of 96 in-MPA positions; mean p=0.95, max p=0.99
- **Where:** -3.483, -171.058 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 96)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 2.368 | +0.187 |
| `speed_roll_mean` | 2.348 | +0.175 |
| `distance_from_shore` | 37570.602 | +0.051 |
| `speed_roll_std` | 0.398 | +0.016 |
| `hour_cos` | 0.929 | +0.014 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
