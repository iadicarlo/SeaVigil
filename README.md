# SeaVigil

**A near-real-time, explainable, open-source monitor for illegal-fishing behaviors - with a reason, an authorization check, and an auditable evidence dossier for every flag.**

Live: **https://seavigil.org** - the front page is the near-real-time monitor (our own Sentinel-1 SAR and Sentinel-2 optical dark-vessel detection, merged with live AIS vessel tracks, going-dark, and at-sea encounters); the historical worldwide sample is at [`?showcase`](https://seavigil.org/?showcase), with an [alerts feed](https://seavigil.org/alerts.html).

SeaVigil flags vessels that show seemingly illegal behavior and, for each one, answers the questions a monitoring platform usually leaves open: *why* was it flagged, *is the vessel authorized* to be there, and *can the record be audited*. It degrades to a fully static, offline site (no server, no cloud account); the live deployment runs on a single independent, renewable-powered European VPS, with no hyperscaler. The whole pipeline is open source.

It does not try to out-detect [Global Fishing Watch](https://globalfishingwatch.org) (GFW) at planetary scale. SeaVigil runs its **own** vessel detection over the areas it watches and leans on GFW's open data for the open ocean. The wedge is the last mile: **per-flag explanation + authorization grading + auditable evidence + near-real-time alerts + offline deployment**, all open.

---

## What it flags

| Behavior | How | Source |
|---|---|---|
| Apparent fishing in an MPA | RandomForest + SHAP attribution (our model) | GFW labeled AIS (Kroodsma 2018) |
| Dark vessel, SAR and optical, in an EEZ or reserve | **our own detection** on fresh Copernicus scenes | Allen Institute / Skylight model (Beukema 2023); dark-fleet scale (Paolo 2024) |
| Position anomaly (possible GNSS jamming / spoofing) | our detector | NOAA AIS + live aisstream |
| Going dark (AIS disabling) | **our own live detection** from the AIS stream, GFW offshore | Welch 2022 |
| At-sea encounter (transshipment) | **our own live detection**, GFW offshore | Miller 2018 |

Plus three **data-integrity leads** on the live monitor, the AIS anomalies working mariners say they actually trust: **nav-status vs motion** (broadcasting *moored* while the track shows real transit), **identity change** (one MMSI carrying more than one vessel name), and the position anomaly above. Each is context for an analyst to check, never proof, and never rolled into a flag's confidence. Every flag also carries its most likely **innocent explanation**, so it reads as a lead to check, not an accusation.

Every flag is tagged with the EEZ it falls in (global Marine Regions boundaries) and graded for **authorization**: a foreign-flagged vessel is looked up in the GFW vessel-identity registry and checked against the RFMO / regional authorizations on record (FFA, WCPFC, IOTC, ICCAT, IATTC, CCSBT, CCAMLR), so a bare "foreign" becomes *authorized / authorization lapsed / no authorization on record / domestic*. National EEZ licences are not public, so an empty record means "no public record", not proof.

## Three ways to see it

- **Near-real-time monitor** (the homepage): our own Sentinel-1 SAR and Sentinel-2 optical dark-vessel detections, merged with live AIS - vessel tracks, going-dark, and at-sea encounters read straight from the stream - and GFW's offshore events, filtered to the high-signal subset (a foreign or unauthorized vessel inside another state's EEZ, or a no-take incursion). Our own detection refreshes within hours of each satellite pass; live AIS is seconds to minutes.
- **Worldwide showcase** ([`?showcase`](https://seavigil.org/?showcase)): an illustrative 584 records across 132 EEZs and 61 flag states, on real WDPA + EEZ boundaries.
- **Alerts** ([alerts.html](https://seavigil.org/alerts.html) + an [RSS feed](https://seavigil.org/alerts.xml)): new high-severity leads, each carrying its flag, EEZ, authorization status, and reason.

Each dark-vessel detection also saves a **true-color satellite image chip** of the boat, shown in its dossier: the visual proof behind the dot.

SeaVigil runs its **own** Sentinel-1 SAR and Sentinel-2 optical vessel detection on demand over a scene it chooses. [`?sar`](https://seavigil.org/?sar) and [`?s2`](https://seavigil.org/?s2) show real runs of the open, pre-trained **Allen Institute / Skylight** detectors (Apache-2.0, the models behind Skylight) over a recent Copernicus scene of the **Galapagos Marine Reserve**, reading just the chosen area of interest straight from the Cloud-Optimized GeoTIFFs on S3 (no bulk download). [`scripts/run_sentinel1_detection.py`](scripts/run_sentinel1_detection.py) and [`scripts/run_sentinel2_detection.py`](scripts/run_sentinel2_detection.py) run them locally on CPU, and [`scripts/sar_detections_to_incidents.py`](scripts/sar_detections_to_incidents.py) folds the detections (length, heading, fishing-vessel class) into the map with jurisdiction, dark-vessel AIS matching, and evidence. So we control where and when we look, instead of waiting for GFW to publish.

The interface is available in **English, Spanish, French, and Portuguese**, and the site loads **zero external resources** (every library, font, glyph, and the basemap are vendored locally), so it runs fully offline.

## Compared to other tools

| Tool | Alerts | Per-flag explanation | Authorization grade | Offline / open |
|---|---|---|---|---|
| Skylight (Allen Institute) | free, 70+ countries | no | no | no (vetted account) |
| Starboard | paid | no | partial | no |
| OceanMind | managed service | no (human analysts) | yes (analysts) | no |
| Global Fishing Watch | data / portal | no | registry data | no (cloud / API) |
| **SeaVigil** | RSS + page, with reasons | **SHAP + rules** | **RFMO records** | **laptop, open source** |

> Two honest caveats on the SeaVigil row. The **RSS feed** inherits Global Fishing Watch's ~3-4 day event lag for going-dark and encounters (the live map's own AIS behaviors are real-time). The **SHAP** attribution is genuine but shows the fishing classifier leans heavily on vessel speed, so read it as "why this looks like fishing", not evidence of a deep model.

## How it works

```
AIS / SAR / optical ─────▶ behavior detection ─▶ per-flag reason (SHAP or rule)
                                  │
        global EEZ + WDPA ──▶ jurisdiction tag ──▶ foreign?
                                  │
        GFW vessel registry ─▶ authorization grade (authorized / lapsed / none)
                                  │
                                  ▼
          auditable dossier (who · where · when · why · authorization ·
                             SHA-256 integrity hash · data provenance)
```

- **Detection.** A `scikit-learn` RandomForest scores fishing-vs-not per AIS position from interpretable movement features, evaluated on a **vessel-grouped split** against a speed-threshold baseline it must beat, **calibrated** (Brier 0.092 on ~408k held-out positions), with a **SHAP** attribution for every call. Dark (non-broadcasting) vessels are found by **our own** runs of the open Allen Institute / Skylight Sentinel-1 SAR and Sentinel-2 optical detectors over Copernicus scenes; going-dark and at-sea encounters are detected **live from the AIS stream**, with GFW's published datasets supplementing the open ocean. Each non-AIS behavior carries a rule-based reason.
- **Jurisdiction + authorization.** Every incident is point-in-polygon tagged with its EEZ (the global Marine Regions set) and, where a vessel identity exists, graded against the GFW registry's RFMO authorizations.
- **Evidence.** Each incident is a structured dossier with a SHA-256 integrity hash, full provenance, and (for a satellite detection) a true-color image chip of the boat, downloadable as JSON.
- **Near-real-time.** A continuous AIS ingest ([`tracker/ingest.py`](tracker/ingest.py)) writes positions to a local SQLite database, and [`tracker/server.py`](tracker/server.py) serves the live vessel tracks, going-dark, and encounters from `/live/*` endpoints; the SAR and optical detectors run over fresh Copernicus scenes within hours of each satellite pass. On a static host the `/live/*` endpoints are simply absent and the site falls back to its committed snapshot.

## Model card and validation

- **[Model card](docs/MODEL_CARD.md)** for the apparent-fishing classifier: ROC-AUC **0.946**, PR-AUC 0.928, F1 0.871 on held-out vessels (grouped split), Brier 0.0915 (0.0878 calibrated), with intended use, ethical considerations, and limitations.
- **[Validation](docs/VALIDATION.md)** against an independent authority: of the 18 vessels on the **CCAMLR IUU list**, GFW's registry (which SeaVigil's authorization layer queries) resolves 8, tags 5 as `IUU` outright, and SeaVigil grades all 8 as **unauthorized** - the high-severity flag the listing implies. The rest predate or evade AIS (the dark fleet). Reproduce with `uv run python scripts/validate_iuu.py`.

## Reproduce

```bash
uv sync                                                   # CPU-only, no GPU
uv run python -m seavigil.run                             # train + evaluate the classifier (+ SHAP)
uv run python -m seavigil.alert --scope all --sample-sar  # fishing-in-MPA + dark-fleet dossiers
uv run --group dev pytest -q                              # tests (no network)
```

Rebuild the worldwide showcase (needs the gitignored source datasets + a GFW token for authorization):

```bash
uv run --with pyogrio --with geopandas python scripts/build_eez_tag.py   # global EEZ tagging set
uv run python scripts/fetch_authorizations.py                            # GFW registry authorizations
uv run python scripts/swap_real_sar.py && uv run python -m seavigil.site # regenerate web/data
```

Run our own Sentinel-1 SAR or Sentinel-2 optical detection over a scene we choose (needs the open Allen models cloned, a small env, and Copernicus S3 keys; the one-time setup is in each script header):

```bash
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... ./vds-env/bin/python scripts/run_sentinel1_detection.py \
  --vds /path/to/vessel-detection-sentinels \
  --scene S1D_IW_GRDH_1SDV_20260627T114116_20260627T114145_003421_006075_6BE9_COG.SAFE \
  --bbox -90.5 -0.85 -90.0 -0.35 --out results/sar/predictions.csv
uv run python scripts/sar_detections_to_incidents.py --detections results/sar/predictions.csv
# Sentinel-2 optical follows the same path: scripts/run_sentinel2_detection.py
```

Run the live tracker (needs `AISSTREAM_KEY`; the same database backs the live map):

```bash
AISSTREAM_KEY=... uv run --with websockets python tracker/ingest.py   # continuous AIS -> SQLite
python3 tracker/server.py 8100                                        # serve the site + the /live/* endpoints
```

Serve the static site locally (Range-capable, required for the PMTiles basemap):

```bash
python3 scripts/serve.py 8000   # then open http://localhost:8000  (and ?sar, ?s2, ?showcase)
```

## Data sources and licenses

| Dataset | Reference | License |
|---|---|---|
| GFW labeled AIS training data | Kroodsma et al., *Science* 2018 | CC BY 4.0 |
| Dark-fleet scale (SAR) | Paolo et al., *Nature* 2024 | CC BY-NC 4.0 |
| Sentinel-1 SAR + Sentinel-2 optical vessel detectors (our own runs) | Allen Institute / Skylight - Beukema et al., *NeurIPS Computational Sustainability* 2023; SatlasPretrain, Bastani et al., *ICCV* 2023 | Apache-2.0 |
| Sentinel-1 / Sentinel-2 imagery (our own runs) | Copernicus Data Space Ecosystem (ESA) | free and open |
| GFW events + vessel identity / authorizations | globalfishingwatch.org API | CC BY-NC 4.0 |
| AIS disabling (going dark) | Welch et al., *Science Advances* 2022 | CC BY-NC |
| At-sea transshipment | Miller et al., *Frontiers in Marine Science* 2018 | CC BY-NC |
| Marine Protected Areas (WDPA / WD-OECM) | UNEP-WCMC and IUCN (2026), Protected Planet | non-commercial, display-only |
| Exclusive Economic Zones (v12) | Flanders Marine Institute (2024), DOI 10.14284/632 | CC BY 4.0 |
| Basemap land + borders | Natural Earth | public domain |
| Live AIS | aisstream.io | free tier |

Consuming GFW's SAR / events (CC BY-NC) and the WDPA layer (non-commercial, display-only) binds SeaVigil to **non-commercial** use. WDPA is shown under the Protected Planet Terms of Use as non-extractable vector tiles, never redistributed as raw GeoJSON. Citation: UNEP-WCMC and IUCN (2026), Protected Planet: The World Database on Protected Areas (WDPA), June 2026, Cambridge, UK, www.protectedplanet.net. Full methodology, calibration, and DOIs: the [About page](https://seavigil.org/about.html).

## Honest caveats

- A flag is an **inspection lead, not courtroom proof**: encrypted VMS outranks public AIS/SAR in fisheries law and remote-sensing-only prosecutions are rare, so it tells an officer where to look and why, it does not convict.
- "Fishing" is **apparent** (inferred from movement); classifier metrics are on **unseen vessels**, and the labels cover a few gear types (2012-2015).
- AIS is blind to the **~75% of industrial vessels that don't broadcast** (the dark fleet) and is spoofable; SAR and optical see them but carry no identity.
- SeaVigil is a **targeting and evidence layer, not an enforcement one**: it does not supply the patrol asset, jurisdiction, or state will an interdiction needs, and it is blind to crew and labor conditions and to small artisanal (under ~12 m) boats. Its value is a better-targeted inspection per patrol-day, and a defensible packet to attach to the hull.
- National EEZ fishing **licences are not public**, so an empty authorization record means "no public record", not proof of illegality.
- Coverage is **focused, not omniscient**: live AIS is seconds to minutes and our own SAR / optical detection lands within hours of each satellite pass, but coverage is bounded by satellite revisit and the reach of terrestrial AIS, and GFW's offshore events carry their own multi-day lag. The showcase is a fixed historical sample.

## Credits

Author: Isma Abdelkader Di Carlo. Built on open data and open models from Global Fishing Watch, the Allen Institute for AI / Skylight, Marine Regions (Flanders VLIZ), UNEP-WCMC / IUCN, and Natural Earth. License: MIT (code).
