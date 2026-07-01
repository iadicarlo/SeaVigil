# Incident `phoenix_islands_protected_area__purse_seines_178183327397239_0003`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `purse_seines_178183327397239`  ·  **gear:** purse_seines
- **When (UTC):** 2013-11-11T21:23:25Z → 2013-11-12T03:50:22Z (6.449 h)
- **Apparent fishing:** 30 of 66 in-MPA positions; mean p=0.70, max p=0.91
- **Where:** -3.372, -172.772 (centroid)
- **Track:** 66 positions, (-3.320, -172.605) → (-3.399, -172.858)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 3.253 | +0.069 |
| `speed_roll_std` | 1.414 | +0.060 |
| `speed` | 3.650 | +0.053 |
| `distance_from_shore` | 131620.585 | +0.039 |
| `distance_from_port` | 132076.275 | -0.024 |

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
- **Integrity (SHA-256 of canonical facts):** `926bea395acfe4e4a26c5e2080b33cb3defc40f6ae2744d71dca6b26c92e0717`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
