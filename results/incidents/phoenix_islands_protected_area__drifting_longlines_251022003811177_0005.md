# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0005`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Phoenix Islands EEZ (Kiribati) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-05T09:54:39Z → 2014-12-05T16:21:08Z (6.441 h)
- **Apparent fishing:** 230 of 230 in-MPA positions; mean p=0.85, max p=0.97
- **Where:** -3.264, -170.201 (centroid)
- **Track:** 230 positions, (-3.311, -170.345) → (-3.278, -170.303)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 230)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 5.384 | +0.127 |
| `speed` | 5.388 | +0.121 |
| `distance_from_shore` | 76615.002 | +0.082 |
| `speed_roll_std` | 0.480 | +0.033 |
| `distance_from_port` | 175494.784 | -0.006 |

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
- **Integrity (SHA-256 of canonical facts):** `31c0953c9d76fa0483033f665c20a8942fe7918f0228870a79b070a67e55b303`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
