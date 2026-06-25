# Incident `phoenix_islands_protected_area__drifting_longlines_119914759372174_0002`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_119914759372174`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-08-19T05:46:11Z → 2014-08-20T03:52:38Z (22.108 h)
- **Apparent fishing:** 49 of 54 in-MPA positions; mean p=0.88, max p=1.00
- **Where:** -2.629, -170.982 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 4.735 | +0.131 |
| `speed_roll_mean` | 5.025 | +0.120 |
| `distance_from_shore` | 56943.615 | +0.064 |
| `speed_roll_std` | 1.067 | +0.041 |
| `distance_from_port` | 84845.961 | +0.013 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
