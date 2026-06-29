# Incident `phoenix_islands_protected_area__drifting_longlines_119914759372174_0001`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** `drifting_longlines_119914759372174`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-08-15T06:38:37Z → 2014-08-18T18:51:14Z (84.21 h)
- **Apparent fishing:** 176 of 200 in-MPA positions; mean p=0.90, max p=1.00
- **Where:** -2.208, -171.509 (centroid)
- **Track:** 200 positions, (-2.201, -171.286) → (-2.184, -171.272)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

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

## Provenance & integrity

- Global Fishing Watch labelled AIS training data (Kroodsma et al., Science 2018). CC BY 4.0.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Model confidence:** Fishing probabilities are well-calibrated (Brier 0.0915 on 408,194 held-out positions from vessels not seen in training); read the score as a probability.
- **Integrity (SHA-256 of canonical facts):** `45c8e69ef9d44401494bf3bcd2fdeed91968ae1d04eeffea7e0b409105831540`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
