# Incident `live_ais__ba9bf254dd6783`

- **MPA:** AIS disabling (going dark)
- **Severity:** HIGH (foreign vessel, no authorization on record)
- **EEZ:** Australian Exclusive Economic Zone (Australia) -- FOREIGN-flagged vessel
- **Authorization:** No authorization on record
- **Vessel:** 🇮🇪 KAYBEANNA 5-99%  ·  **signal:** AIS gap
- **When (UTC):** 2026-06-25T15:45:16.000Z → 2026-06-26T22:51:06.000Z
- **Gap:** 31.1 h dark, 69.0 nm offshore
- **Where:** -38.102, 151.147

## Why this was flagged

_GFW Events gaps dataset (satellite AIS).._

- went dark 69 nm offshore for 31 h
- satellite-confirmed AIS gap (GFW Events)

## Caveats

- AIS gaps can be reception loss, not always intentional disabling.
- The position is where AIS dropped; the path while dark is unknown.
- An inspection lead from GFW Events, not proof of illegal activity.

## Provenance & integrity

- NOAA Marine Cadastre AIS (marinecadastre.gov/ais (vessel positions)). US public domain.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Integrity (SHA-256 of canonical facts):** `7e075b01dfdcf705ea86e63c668e21014117c5796933029922f01173da1ac3b1`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
