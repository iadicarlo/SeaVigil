# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0002`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-02T23:51:10Z → 2014-12-03T04:47:09Z (4.933 h)
- **Apparent fishing:** 141 of 144 in-MPA positions; mean p=0.76, max p=0.89
- **Where:** -3.969, -174.199 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 141)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `hour_cos` | 0.887 | +0.096 |
| `distance_from_port` | 304191.076 | +0.076 |
| `speed_roll_mean` | 7.414 | +0.029 |
| `speed_roll_std` | 0.234 | +0.018 |
| `hour_sin` | 0.396 | +0.011 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
