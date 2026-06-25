# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0008`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Phoenix Islands EEZ (Kiribati) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-07T09:24:41Z → 2014-12-07T13:05:21Z (3.678 h)
- **Apparent fishing:** 172 of 172 in-MPA positions; mean p=0.91, max p=0.98
- **Where:** -3.379, -170.758 (centroid)
- **Track:** 172 positions, (-3.412, -170.845) → (-3.328, -170.612)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 172)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 4.312 | +0.160 |
| `speed` | 4.274 | +0.157 |
| `distance_from_shore` | 38810.639 | +0.033 |
| `speed_roll_std` | 0.588 | +0.027 |
| `hour_sin` | 0.300 | +0.017 |

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
- **Integrity (SHA-256 of canonical facts):** `918f77f4ffa430a715b7647f0d6bfad6728a095d63816af9bbbdb5f803d2df05`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
