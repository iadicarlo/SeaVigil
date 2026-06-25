# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0013`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Phoenix Islands EEZ (Kiribati) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-14T19:02:23Z → 2014-12-14T22:16:53Z (3.242 h)
- **Apparent fishing:** 174 of 176 in-MPA positions; mean p=0.84, max p=0.96
- **Where:** -3.466, -170.168 (centroid)
- **Track:** 176 positions, (-3.579, -170.142) → (-3.375, -170.297)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 174)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 6.110 | +0.088 |
| `speed` | 6.098 | +0.077 |
| `distance_from_shore` | 66842.888 | +0.068 |
| `hour_sin` | -0.719 | +0.044 |
| `hour_cos` | 0.657 | +0.043 |

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
- **Integrity (SHA-256 of canonical facts):** `925d05bb6fadace311c4176df681191cdbcd8adff2c667948cd3b757e9c030dc`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
