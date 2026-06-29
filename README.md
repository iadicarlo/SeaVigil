# SeaVigil

**A near-real-time, explainable, open-source monitor for illegal-fishing behaviors - with a reason, an authorization check, and an auditable evidence dossier for every flag.**

Live: **https://iadicarlo.github.io/seavigil** - the front page is the near-real-time monitor (our own Sentinel-1 dark-vessel detection merged with live AIS and consumed GFW events); the historical worldwide sample is at `?showcase`, with an [alerts feed](https://iadicarlo.github.io/seavigil/alerts.html).

SeaVigil flags vessels that show seemingly illegal behavior and, for each one, answers the questions a monitoring platform usually leaves open: *why* was it flagged, *is the vessel authorized* to be there, and *can the record be audited*. It runs as a static site (no server, no cloud account) and the whole pipeline is open source.

It does not try to out-detect [Global Fishing Watch](https://globalfishingwatch.org) (GFW) or reinvent dark-vessel detection; it builds on and consumes their open data. The wedge is the last mile: **per-flag explanation + authorization grading + auditable evidence + near-real-time alerts + offline deployment**, all open.

---

## The five behaviors it flags

| Behavior | How | Source |
|---|---|---|
| Apparent fishing in an MPA | RandomForest + SHAP attribution (our model) | GFW labeled AIS (Kroodsma 2018) |
| Dark vessel (SAR) in an EEZ / reserve | consumed, not recomputed | GFW Sentinel-1 (Paolo 2024) |
| AIS spoofing (impossible movement) | our detector | NOAA AIS + live aisstream |
| Going dark (AIS disabling) | consumed | GFW gaps (Welch 2022) |
| At-sea encounter (transshipment) | consumed | GFW encounters (Miller 2018) |

Every flag is tagged with the EEZ it falls in (global Marine Regions boundaries) and graded for **authorization**: a foreign-flagged vessel is looked up in the GFW vessel-identity registry and checked against the RFMO / regional authorizations on record (FFA, WCPFC, IOTC, ICCAT, IATTC, CCSBT, CCAMLR), so a bare "foreign" becomes *authorized / authorization lapsed / no authorization on record / domestic*. National EEZ licences are not public, so an empty record means "no public record", not proof.

## Three ways to see it

- **Near-real-time monitor** (the homepage): our own Sentinel-1 dark-vessel detections merged with live AIS spoofing and the GFW Events API (gaps + encounters, about a 3-4 day lag), filtered to the high-signal subset (a foreign or unauthorized vessel inside another state's EEZ, or a no-take incursion). Our SAR engine refreshes within hours of each satellite pass; the events refresh hourly, by GitHub Actions.
- **Worldwide showcase** (`?showcase`): an illustrative 584 records across 132 EEZs and 59 flag states, on real WDPA + EEZ boundaries.
- **Alerts** ([alerts.html](https://iadicarlo.github.io/seavigil/alerts.html) + an [RSS feed](https://iadicarlo.github.io/seavigil/alerts.xml)): new high-severity leads, each carrying its flag, EEZ, authorization status, and reason.

The SAR (dark-vessel) layer can be either **consumed** from GFW or **run by us on demand**. The `?sar` view shows a real run: our own pass of the open, pre-trained **Allen Institute** Sentinel-1 detector (Apache-2.0, the model behind Skylight) over a June 2026 Copernicus scene of the **Galapagos Marine Reserve**, reading just the chosen area of interest straight from the Cloud-Optimized GeoTIFFs on S3 (no bulk download). [`scripts/run_sentinel1_detection.py`](scripts/run_sentinel1_detection.py) runs it locally on CPU, and [`notebooks/sentinel1_vessel_detection.ipynb`](notebooks/sentinel1_vessel_detection.ipynb) runs the same path on a free Colab GPU; [`scripts/sar_detections_to_incidents.py`](scripts/sar_detections_to_incidents.py) then folds the detections (length, heading, fishing-vessel class) into the `?sar` view with jurisdiction, dark-vessel AIS matching, and evidence. So we control where and when we look, instead of waiting for GFW to publish.

The interface is available in **English, Spanish, French, and Portuguese**, and the site loads **zero external resources** (every library, font, glyph, and the basemap are vendored locally), so it runs fully offline.

## Why it is not a GFW clone

Detecting apparent fishing from vessel tracks is a solved, industrialised problem - GFW's flagship product. Even MPA-incursion alerting is shipped: **Skylight** (Allen Institute for AI) does it free for 70+ countries. SeaVigil reinvents neither. What no one ships together is:

- a **per-flag explanation** - a SHAP attribution for *why a position scored as fishing*, and an explicit rule/evidence trail for the other behaviors;
- an **authorization grade** - "foreign" checked against real RFMO records, not just flag-vs-coast;
- an **auditable dossier** - a SHA-256 integrity hash over the incident's canonical facts plus full data provenance, downloadable as JSON;
- **near-real-time alerts that carry all of the above**; and
- **offline, open-source deployment** - it runs on a laptop with no account, and the whole pipeline is public.

> **Honest scope.** A SeaVigil flag is an *inspection lead*, not courtroom proof. Encrypted VMS outranks public AIS/SAR in fisheries law, and remote-sensing-only prosecutions are rare. SeaVigil tells an officer where to look and why; it does not convict.

## Compared to other tools

| Tool | Alerts | Per-flag explanation | Authorization grade | Offline / open |
|---|---|---|---|---|
| Skylight (Allen Institute) | free, 70+ countries | no | no | no (vetted account) |
| Starboard | paid | no | partial | no |
| OceanMind | managed service | no (human analysts) | yes (analysts) | no |
| Global Fishing Watch | data / portal | no | registry data | no (cloud / API) |
| **SeaVigil** | RSS + page, with reasons | **SHAP + rules** | **RFMO records** | **laptop, open source** |

## How it works

```
AIS / SAR / GFW events ─▶ behavior detection ─▶ per-flag reason (SHAP or rule)
                                  │
        global EEZ + WDPA ──▶ jurisdiction tag ──▶ foreign?
                                  │
        GFW vessel registry ─▶ authorization grade (authorized / lapsed / none)
                                  │
                                  ▼
          auditable dossier (who · where · when · why · authorization ·
                             SHA-256 integrity hash · data provenance)
```

- **Detection.** A `scikit-learn` RandomForest scores fishing-vs-not per AIS position from interpretable movement features, evaluated on a **vessel-grouped split** against a speed-threshold baseline it must beat, **calibrated** (Brier 0.092 on ~408k held-out positions), with a **SHAP** attribution for every call. The other four behaviors are consumed from GFW's published datasets / API and carry rule-based reasons.
- **Jurisdiction + authorization.** Every incident is point-in-polygon tagged with its EEZ (the global Marine Regions set) and, where a vessel identity exists, graded against the GFW registry's RFMO authorizations.
- **Evidence.** Each incident is a structured dossier with a SHA-256 integrity hash and full provenance, downloadable as JSON.
- **Near-real-time.** An hourly GitHub Action pulls recent GFW events and streams live AIS into a rolling 12h buffer for spoofing, republishing the `?live` view and the alerts feed.

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

Run our own Sentinel-1 SAR detection over a scene we choose (needs the open Allen model cloned, a small conda env, and Copernicus S3 keys; the one-time setup is in the script header):

```bash
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... ./vds-env/bin/python scripts/run_sentinel1_detection.py \
  --vds /path/to/vessel-detection-sentinels \
  --scene S1D_IW_GRDH_1SDV_20260627T114116_20260627T114145_003421_006075_6BE9_COG.SAFE \
  --bbox -90.5 -0.85 -90.0 -0.35 --out results/sar/predictions.csv
uv run python scripts/sar_detections_to_incidents.py --detections results/sar/predictions.csv
```

Run the near-real-time monitor (needs `GFW_TOKEN`; `AISSTREAM_KEY` adds live spoofing):

```bash
GFW_TOKEN=... AIS_BUFFER=data/positions/ais_buffer.csv uv run python scripts/live_monitor.py
```

Serve the site locally (Range-capable, required for the PMTiles):

```bash
python3 scripts/serve.py 8000   # then open http://localhost:8000  (and ?live)
```

## Data sources and licenses

| Dataset | Reference | License |
|---|---|---|
| GFW labeled AIS training data | Kroodsma et al., *Science* 2018 | CC BY 4.0 |
| GFW Sentinel-1 SAR detections | Paolo et al., *Nature* 2024 | CC BY-NC 4.0 |
| Sentinel-1 SAR vessel detector (our on-demand runs) | Allen Institute, vessel-detection-sentinels | Apache-2.0 |
| Sentinel-1 GRD imagery (our on-demand runs) | Copernicus Data Space Ecosystem (ESA) | free and open |
| GFW events + vessel identity / authorizations | globalfishingwatch.org API | CC BY-NC 4.0 |
| AIS disabling (going dark) | Welch et al., *Science Advances* 2022 | CC BY-NC |
| At-sea transshipment | Miller et al., *Frontiers in Marine Science* 2018 | CC BY-NC |
| Marine Protected Areas (WDPA / WD-OECM) | UNEP-WCMC and IUCN (2026), Protected Planet | non-commercial, display-only |
| Exclusive Economic Zones (v12) | Flanders Marine Institute (2024), DOI 10.14284/632 | CC BY 4.0 |
| Basemap land + borders | Natural Earth | public domain |
| Live AIS | aisstream.io | free tier |

Consuming GFW's SAR / events (CC BY-NC) and the WDPA layer (non-commercial, display-only) binds SeaVigil to **non-commercial** use. WDPA is shown under the Protected Planet Terms of Use as non-extractable vector tiles, never redistributed as raw GeoJSON. Citation: UNEP-WCMC and IUCN (2026), Protected Planet: The World Database on Protected Areas (WDPA), June 2026, Cambridge, UK, www.protectedplanet.net. Full methodology, calibration, and DOIs: the [About page](https://iadicarlo.github.io/seavigil/about.html).

## Honest caveats

- A flag is an **inspection lead**, not proof of illegal activity.
- "Fishing" is **apparent** (inferred from movement); classifier metrics are on **unseen vessels**, and the labels cover a few gear types (2012-2015).
- AIS is blind to the **~75% of industrial vessels that don't broadcast** (the dark fleet) and is spoofable; SAR sees them but carries no identity.
- National EEZ fishing **licences are not public**, so an empty authorization record means "no public record", not proof of illegality.
- The near-real-time feed has a **~3-4 day lag** (GFW events), and the showcase is an **illustrative curated sample**, not global live coverage.

## Credits

Author: Isma Abdelkader Di Carlo. Built on open data from Global Fishing Watch, Marine Regions (Flanders VLIZ), UNEP-WCMC / IUCN, and Natural Earth. License: MIT (code).
