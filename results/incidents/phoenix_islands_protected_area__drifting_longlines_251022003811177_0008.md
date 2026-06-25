# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0008`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-07T09:24:41Z → 2014-12-07T13:05:21Z (3.678 h)
- **Apparent fishing:** 172 of 172 in-MPA positions; mean p=0.91, max p=0.98
- **Where:** -3.379, -170.758 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 172)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 4.312 | +0.160 |
| `speed` | 4.274 | +0.157 |
| `distance_from_shore` | 38810.639 | +0.033 |
| `speed_roll_std` | 0.588 | +0.027 |
| `hour_sin` | 0.300 | +0.017 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
