# Incident `great_barrier_reef_marine_park__503476200_0000`

- **MPA:** Great Barrier Reef Marine Park
- **Severity:** LOW (multi-use protected area)  ·  boundary sample-approx-2024
- **Vessel:** 🇦🇺 REEFMAGIC 2  ·  **gear:** unknown  ·  Passenger  ·  to CAIRNS
- **When (UTC):** 2026-06-25T23:06:50Z → 2026-06-25T23:06:50Z (0.0 h)
- **Apparent fishing:** 1 of 1 in-MPA positions; mean p=0.64, max p=0.64
- **Where:** -16.920, 145.782 (centroid)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `distance_from_port` | 1335.896 | -0.240 |
| `speed` | 3.200 | +0.188 |
| `speed_roll_mean` | 3.200 | +0.174 |
| `distance_from_shore` | 6384.791 | +0.012 |
| `hour_cos` | 0.972 | +0.004 |

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
- **Integrity (SHA-256 of canonical facts):** `f4c81ba1c8b046806b388407203a7b393ca99b5bc96a59dbfa6fc6e0481e6e33`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
