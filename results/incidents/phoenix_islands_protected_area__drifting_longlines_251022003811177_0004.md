# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0004`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Phoenix Islands EEZ (Kiribati) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-04T17:12:23Z → 2014-12-05T02:13:13Z (9.014 h)
- **Apparent fishing:** 111 of 354 in-MPA positions; mean p=0.74, max p=0.92
- **Where:** -3.629, -171.023 (centroid)
- **Track:** 354 positions, (-4.043, -171.982) → (-3.536, -170.912)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 111)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 4.840 | +0.128 |
| `speed_roll_mean` | 4.871 | +0.120 |
| `speed_roll_std` | 0.527 | +0.022 |
| `distance_from_port` | 118198.793 | -0.022 |
| `hour_cos` | 0.932 | -0.018 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.

## Provenance & integrity

- Global Fishing Watch labelled AIS training data (Kroodsma et al., Science 2018). CC BY 4.0.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Model confidence:** Fishing probabilities are well-calibrated (Brier 0.0915 on 408,194 held-out positions from vessels not seen in training); read the score as a probability.
- **Integrity (SHA-256 of canonical facts):** `65d7c236948bdd2a510806c3040023407372f6b71b1f73979f03d234a5629cfa`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
