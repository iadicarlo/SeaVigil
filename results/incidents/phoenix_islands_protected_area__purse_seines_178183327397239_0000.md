# Incident `phoenix_islands_protected_area__purse_seines_178183327397239_0000`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `purse_seines_178183327397239`  ·  **gear:** purse_seines
- **When (UTC):** 2013-11-07T03:03:07Z → 2013-11-08T15:27:28Z (36.406 h)
- **Apparent fishing:** 92 of 172 in-MPA positions; mean p=0.67, max p=0.89
- **Where:** -3.477, -171.915 (centroid)
- **Track:** 172 positions, (-4.010, -171.873) → (-3.439, -172.042)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 92)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 2.662 | +0.132 |
| `speed_roll_mean` | 2.918 | +0.107 |
| `distance_from_port` | 76022.828 | -0.044 |
| `hour_cos` | -0.034 | -0.031 |
| `hour_sin` | 0.206 | -0.025 |

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
- **Integrity (SHA-256 of canonical facts):** `cdd3f49f4cbcea166c5a5acc6e464fbf76008e51f84089da3ee2632e22edbaae`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
