# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0012`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-14T06:56:25Z → 2014-12-14T11:43:42Z (4.788 h)
- **Apparent fishing:** 160 of 160 in-MPA positions; mean p=0.93, max p=0.98
- **Where:** -3.471, -170.251 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 160)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 3.278 | +0.173 |
| `speed` | 3.270 | +0.169 |
| `distance_from_shore` | 57698.559 | +0.058 |
| `speed_roll_std` | 0.579 | +0.032 |
| `distance_from_port` | 179125.385 | -0.017 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
