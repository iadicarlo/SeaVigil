# Dark-vessel detection `sar__galapagos_marine_reserve_0016`

- **MPA:** Galapagos Marine Reserve (WDPA 11753)
- **Severity:** HIGH (dark vessel inside MPA)  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Ecuadorian Exclusive Economic Zone (Galapagos) (Ecuador)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** (dark -- no AIS identity)  ·  **source:** SAR (dark)
- **When (UTC):** 2024-03-31T11:51:02Z
- **Length:** n/a  ·  **broadcasting AIS:** no (dark)  ·  **GFW fishing-score:** n/a (Portal-only)
- **Where:** -0.290, -90.510

## Why this was flagged

_SAR detection attributes (no AIS track or identity; not SHAP-explainable)._

- inside MPA: Galapagos Marine Reserve (within Galapagos EEZ (Ecuador))
- not broadcasting AIS (dark vessel)

## Caveats

- Dark vessel: detected by satellite SAR but not broadcasting AIS.
- Not SHAP-explainable -- a SAR detection has no movement track to attribute.
- length_m and fishing_score are GFW model estimates from imagery, not ground truth.
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.

## Provenance & integrity

- Global Fishing Watch Sentinel-1 SAR vessel detections (Paolo et al., Nature 2024). CC BY-NC 4.0 (non-commercial).
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Integrity (SHA-256 of canonical facts):** `03171a406bed666afe0ebd973ac8475c3283151ed2e49fc21efa0750dcb4bc82`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
