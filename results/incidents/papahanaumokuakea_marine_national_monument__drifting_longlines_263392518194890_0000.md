# Incident `papahanaumokuakea_marine_national_monument__drifting_longlines_263392518194890_0000`

- **MPA:** Papahānaumokuākea Marine National Monument
- **Vessel:** `drifting_longlines_263392518194890`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-09-30T21:54:30Z → 2014-09-30T21:54:30Z (0.0 h)
- **Apparent fishing:** 1 of 42 in-MPA positions; mean p=0.51, max p=0.51
- **Where:** 28.225, -163.434 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `distance_from_shore` | 592259.875 | +0.123 |
| `speed` | 10.100 | -0.103 |
| `speed_roll_mean` | 10.100 | -0.101 |
| `distance_from_port` | 626661.562 | +0.081 |
| `speed_roll_std` | 0.245 | +0.029 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
