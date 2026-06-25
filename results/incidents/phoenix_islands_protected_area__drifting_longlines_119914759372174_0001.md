# Incident `phoenix_islands_protected_area__drifting_longlines_119914759372174_0001`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_119914759372174`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-08-15T06:38:37Z → 2014-08-18T18:51:14Z (84.21 h)
- **Apparent fishing:** 176 of 200 in-MPA positions; mean p=0.90, max p=1.00
- **Where:** -2.208, -171.509 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 176)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 4.302 | +0.147 |
| `speed` | 4.490 | +0.136 |
| `distance_from_shore` | 68715.103 | +0.078 |
| `speed_roll_std` | 0.902 | +0.046 |
| `abs_course_change` | 17.740 | +0.003 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
