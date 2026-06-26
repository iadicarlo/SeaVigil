# Incident `great_barrier_reef_marine_park__503006170_0000`

- **MPA:** Great Barrier Reef Marine Park
- **Severity:** LOW (multi-use protected area)  ·  boundary sample-approx-2024
- **EEZ:** Australia EEZ (Australia)  (flag matches coastal state)
- **Vessel:** 🇦🇺 BANDICOOT  ·  **gear:** unknown  ·  Other  ·  to CAIRNS
- **When (UTC):** 2026-06-26T13:03:18Z → 2026-06-26T13:04:19Z (0.017 h)
- **Apparent fishing:** 2 of 2 in-MPA positions; mean p=0.51, max p=0.51
- **Where:** -16.945, 145.774 (centroid)
- **Track:** 2 positions, (-16.945, 145.774) → (-16.945, 145.774)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `distance_from_shore` | 9278.357 | +0.159 |
| `distance_from_port` | 1687.454 | -0.108 |
| `hour_cos` | -0.962 | -0.031 |
| `speed` | 0.000 | +0.030 |
| `speed_roll_std` | 0.000 | -0.021 |

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
- **Integrity (SHA-256 of canonical facts):** `1332482ca0c8a44862e9bf2768c3fe5f2caa13bf6a638acb3b2f54d4225d199b`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
