# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0011`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-13T19:04:29Z → 2014-12-13T19:04:29Z (0.0 h)
- **Apparent fishing:** 1 of 8 in-MPA positions; mean p=0.50, max p=0.50
- **Where:** -3.375, -170.445 (centroid)
- **Track:** 8 positions, (-3.375, -170.445) → (-3.374, -170.437)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 6.540 | +0.074 |
| `speed` | 7.200 | -0.053 |
| `distance_from_port` | 153625.656 | -0.021 |
| `distance_from_shore` | 47800.500 | -0.018 |
| `hour_cos` | 0.276 | +0.018 |

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
- **Integrity (SHA-256 of canonical facts):** `7a61a25324875adf78b7a29f18ccbd3aed0a5f04e026fcbf8aeb3c5369b41d69`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
