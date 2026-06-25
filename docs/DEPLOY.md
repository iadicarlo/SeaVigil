# SeaVigil — pre-deploy checklist

Gates to clear before publishing the site / pitching publicly. Status as of 2026-06-25.

Legend: ✅ done · ⚠️ action needed (you) · ⏳ time-sensitive.

## 1. Positioning is scoped correctly ✅

Re-verification (2026-06-25) says the per-flag-explanation wedge is **still open, but only
when scoped**:

- ✅ **Claim to make:** *"per-flag SHAP / per-feature attribution **of the fishing detection
  itself** is something no IUU-fishing tool ships."* Lead with **SHAP / feature attribution** —
  a scalar confidence score (which several tools show) is **not** an attribution.
- ❌ **Do NOT claim:** the unscoped *"no tool explains why a vessel was flagged."* That is now
  attackable: **Windward MAI Expert** explains vessel-behaviour **anomalies / IUU risk** in
  plain language (cited sources) — it just doesn't explain the **fishing-detection
  classification** itself. GFW also now ships a risk-indicator dataset (see §2).

README and `docs/DESIGN.md` §5 use the scoped wording.

## 2. Competitive re-verification ⏳

Verified 2026-06-25 against live vendor docs:

| Tool | Per-fishing-detection explanation? |
|---|---|
| **Skylight** (Ai2) | No — event card + GraphQL `EventV2` expose metadata + a scalar `fishingScore`; no reason/attribution field. "Shippy" agent does traceability (cites sources), not explanation. **Gap intact.** |
| **GFW** | Per-event AI agents still "highly experimental"/internal. New (2026-06-03) IUU Fishing Risk Insights = downloadable 11-indicator risk **scoring**, not per-detection narrative. |
| **Windward MAI Expert** | Explains **anomalies / risk** (incl. IUU) in plain language — borderline, but **not** the fishing-detection classification. Closest to the line; monitor. |
| Starboard / OceanMind / Spire / Pole Star | No per-fishing-detection explanation. |

⏳ **Time-bomb:** GFW IUU Risk Insights integrates into the **public map in October 2026**, and
GFW per-event AI agents are in active trials. **Re-verify before any post-Oct-2026 marketing.**

## 3. WDPA / MPA boundaries ⚠️ (biggest legal blocker)

The bundled `data/mpa/sample_mpas.geojson` boxes are fine to ship (we authored them). **Real
WDPA boundaries are not.** The UNEP-WCMC license forbids redistributing them through an
interactive web map that lets users **download** the source polygons.

- ⚠️ **Ship as non-extractable vector tiles**, not raw GeoJSON: run
  `scripts/wdpa_to_pmtiles.sh <wdpa_marine.geojson> web/data/mpas.pmtiles` and point the
  MapLibre `mpas` source at the PMTiles (needs the pmtiles JS protocol plugin).
- ⚠️ **Get written sign-off** from UNEP-WCMC for a public tool (contact details on
  protectedplanet.net). Draft request:

  > *Subject: Permission to display WDPA marine boundaries in a non-commercial public web map*
  > *We run SeaVigil, a free, non-commercial tool that overlays public fishing-activity*
  > *signals on MPA boundaries for enforcement triage. We would display WDPA marine*
  > *boundaries as non-downloadable vector tiles, with the IUCN/UNEP-WCMC citation and a*
  > *protectedplanet.net link clearly visible, and no commercial use. May we proceed?*

- ⚠️ Keep the **IUCN/UNEP-WCMC citation** + a protectedplanet.net link visible on the map.

## 4. Licensing / non-commercial ✅ understood, ⚠️ enforce

- Training labels: **CC BY 4.0** (commercial OK).
- GFW SAR / live-API data **and** WDPA: **CC BY-NC** (non-commercial). Consuming either binds
  SeaVigil to **non-commercial** use. Keep it a public-good tool; attribute "Global Fishing
  Watch".

## 5. Secrets & data refresh ✅

- GFW token lives **only** in a gitignored `.env` locally and in **GitHub Actions secrets**
  (`GFW_TOKEN`) for CI — never in any shipped/committed file. `seavigil.fetch_gfw` reads it
  from the env.
- Raw GFW pulls (`data/sar/gfw_*.geojson`) are **gitignored** — regenerate with the token;
  don't redistribute GFW's raw dataset in bulk (CC BY-NC).
- `.github/workflows/refresh-data.yml`: with the `GFW_TOKEN` secret set it pulls **live** SAR
  detections via `fetch_gfw` and commits the derived dossiers (opt-in to CC BY-NC redistribution);
  without it, it regenerates the synthetic demo. Per-position AIS scoring needs your own feed
  (`--positions`) — GFW publishes no raw AIS.

## 6. Basemap ⚠️

The demo uses OpenStreetMap raster tiles (no key). For a real public deployment, use a proper
tile provider per OSM's tile usage policy.

## 7. Data-honesty before claiming real findings ⚠️

The committed sample uses **approximate** MPA boxes, **in-sample** model scores, and a
**synthetic** SAR sample. Before presenting any result as a real finding: swap in real WDPA
boundaries (§3), score **out-of-sample** (`--scope test` or a true holdout), and ingest real
GFW SAR detections. Dossiers remain *inspection leads, not proof*.
