# Incident `phoenix_islands_protected_area__drifting_longlines_271347251834362_0000`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** `drifting_longlines_271347251834362`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-06-06T01:39:29Z → 2014-06-10T17:13:17Z (111.563 h)
- **Apparent fishing:** 639 of 672 in-MPA positions; mean p=0.91, max p=1.00
- **Where:** -4.102, -171.862 (centroid)
- **Track:** 672 positions, (-4.099, -172.450) → (-4.167, -171.474)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 639)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 3.304 | +0.146 |
| `speed_roll_mean` | 3.480 | +0.143 |
| `distance_from_shore` | 51934.752 | +0.077 |
| `distance_from_port` | 145735.464 | +0.020 |
| `hour_cos` | -0.108 | +0.018 |

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
- **Integrity (SHA-256 of canonical facts):** `bccd43a5af594387485afd9855a61dba66cd40fdf439ae53fe7267d77b620972`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
