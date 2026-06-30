# Incident `live_ais__10a9a73b4a66d8`

- **MPA:** AIS disabling (going dark)
- **Severity:** HIGH (foreign vessel, no authorization on record)
- **EEZ:** Japanese Exclusive Economic Zone (Japan) -- FOREIGN-flagged vessel
- **Authorization:** No authorization on record
- **Vessel:** 🇨🇾 VENUS HISTORY  ·  **signal:** AIS gap
- **When (UTC):** 2026-06-25T08:47:31.000Z → 2026-06-26T06:45:28.000Z
- **Gap:** 22.0 h dark, 154.0 nm offshore
- **Where:** 23.110, 128.907

## Why this was flagged

_GFW Events gaps dataset (satellite AIS).._

- went dark 154 nm offshore for 22 h
- satellite-confirmed AIS gap (GFW Events)

## Caveats

- AIS gaps can be reception loss, not always intentional disabling.
- The position is where AIS dropped; the path while dark is unknown.
- An inspection lead from GFW Events, not proof of illegal activity.

## Provenance & integrity

- NOAA Marine Cadastre AIS (marinecadastre.gov/ais (vessel positions)). US public domain.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Integrity (SHA-256 of canonical facts):** `ecc5ff7db9ca81f2b6f659a6539878b8a0f2d131f0b55a76286619e7b81d69af`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
