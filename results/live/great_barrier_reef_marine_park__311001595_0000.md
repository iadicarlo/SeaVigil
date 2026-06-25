# Incident `great_barrier_reef_marine_park__311001595_0000`

- **MPA:** Great Barrier Reef Marine Park
- **Severity:** LOW (multi-use protected area)  ·  boundary sample-approx-2024
- **EEZ:** Australia EEZ (Australia) -- FOREIGN-flagged vessel (licensing not verified)
- **Vessel:** 🇧🇸 CARNIVAL ADVENTURE  ·  **gear:** unknown
- **When (UTC):** 2026-06-25T23:07:45Z → 2026-06-25T23:07:45Z (0.0 h)
- **Apparent fishing:** 1 of 1 in-MPA positions; mean p=0.59, max p=0.59
- **Where:** -16.925, 145.781 (centroid)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `distance_from_shore` | 7008.974 | +0.172 |
| `distance_from_port` | 761.312 | -0.092 |
| `speed` | 0.000 | +0.037 |
| `speed_roll_std` | 0.000 | -0.035 |
| `hour_cos` | 0.973 | +0.025 |

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
- **Integrity (SHA-256 of canonical facts):** `8c840b0cfe95a2ce02505eb5de912692e1fb57675299d5e3bb09fb03bebbf4d7`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
