# Incident `phoenix_islands_protected_area__drifting_longlines_119914759372174_0000`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_119914759372174`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-06-04T03:53:41Z → 2014-06-04T13:13:20Z (9.328 h)
- **Apparent fishing:** 24 of 28 in-MPA positions; mean p=0.93, max p=0.99
- **Where:** -2.328, -170.271 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 3.417 | +0.162 |
| `speed_roll_mean` | 3.817 | +0.161 |
| `distance_from_shore` | 125720.178 | +0.071 |
| `speed_roll_std` | 1.241 | +0.037 |
| `hour_sin` | 0.517 | +0.005 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
