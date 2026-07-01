# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0004`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-04T17:12:23Z → 2014-12-05T02:13:13Z (9.014 h)
- **Apparent fishing:** 110 of 354 in-MPA positions; mean p=0.75, max p=0.92
- **Where:** -3.628, -171.023 (centroid)
- **Track:** 354 positions, (-4.043, -171.982) → (-3.536, -170.912)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 110)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 4.742 | +0.127 |
| `speed_roll_mean` | 4.902 | +0.123 |
| `speed_roll_std` | 0.581 | +0.022 |
| `distance_from_port` | 118285.861 | -0.021 |
| `hour_cos` | 0.929 | -0.016 |

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
- **Integrity (SHA-256 of canonical facts):** `c83db29144a55f31dee05b2150766e80bcb2a11823cbf5cf732c72367092ff60`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
