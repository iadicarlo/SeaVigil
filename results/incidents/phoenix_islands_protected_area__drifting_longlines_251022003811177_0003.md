# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0003`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-03T11:06:38Z → 2014-12-03T22:57:41Z (11.851 h)
- **Apparent fishing:** 160 of 366 in-MPA positions; mean p=0.92, max p=0.98
- **Where:** -3.949, -174.244 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 160)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 4.313 | +0.171 |
| `speed` | 4.196 | +0.166 |
| `distance_from_shore` | 41937.780 | +0.034 |
| `speed_roll_std` | 0.570 | +0.033 |
| `hour_sin` | -0.050 | +0.006 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
