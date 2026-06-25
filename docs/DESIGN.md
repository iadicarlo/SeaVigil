# SeaVigil — design sketch

_Last updated: 2026-06-25. This is the working spec: what we're building, why, what's
genuinely new, what already exists, what we implement now, and with which tools._

---

## 1. Thesis (one paragraph)

Detecting apparent fishing from vessel tracks is solved and industrialised — it is Global
Fishing Watch's (GFW) flagship product, trained on AIS labels GFW released openly. SeaVigil
does **not** re-detect. It occupies the **last-mile seam** GFW deliberately leaves to
partners: turn a fishing signal into a **per-incident, explainable dossier** that flags
**fishing inside a specific Marine Protected Area (MPA)**, and make it **run on a laptop** so
an under-resourced coastal authority can use it. The unit of value is not "a vessel is
fishing" (GFW already says that) but **"this vessel is apparently fishing inside _this_
protected area, here is the auditable reason, go inspect."**

## 2. Why — the problem and who it's for

- **Problem.** IUU fishing erodes coastal food security and marine ecosystems. MPAs are the
  main legal instrument, but monitoring whether vessels actually fish inside them is manual,
  retrospective, and locked behind tooling that low-capacity states can't run.
- **The seam.** Across the field, *detection* is crowded and *the last mile is thin*. The
  documented gaps (see §4) are: no per-position explanation, no turnkey fishing-in-MPA
  alerting, and no admissible/usable tooling for low-capacity enforcers.
- **Primary user.** A fisheries/MPA enforcement officer or a small marine NGO in a coastal
  state — someone who needs a *defensible, readable reason to send a patrol*, on a machine
  they already have.
- **Secondary users.** Researchers and advocacy groups (e.g. National Geographic Pristine
  Seas, oceans NGOs) who need auditable, reproducible evidence of pressure on specific MPAs.

## 3. What has been done (v1, in repo)

The `seavigil/` package, evaluated honestly:

- `data.py` — downloads + cleans GFW labeled AIS positions (Kroodsma et al., *Science* 2018);
  binarises fractional labels; builds stable vessel IDs.
- `features.py` — per-position, physically interpretable movement features computed
  *within each track*: speed (+ rolling mean/std), turning rate, course change, time gap,
  distance from shore/port, cyclic hour-of-day.
- `model.py` — `RandomForestClassifier` (balanced) with a **vessel-grouped `GroupShuffleSplit`**
  (no vessel in both train and test) and a **tuned speed-threshold baseline** the model must
  beat. ROC-AUC, PR-AUC, F1, confusion matrix.
- `explain.py` — `shap.TreeExplainer` → global ranking + a beeswarm plot + per-position local
  attributions.
- `run.py` — orchestrates the above; writes `results/metrics.json` and `results/SUMMARY.md`.
- `tests/test_pipeline.py` — offline smoke tests (cleaning rules, feature shapes, split
  invariant, baseline logic).

This reproduces **GFW's fishing-detection _target_** with a simpler, interpretable method.
It is a foundation, not the contribution.

## 4. What already exists in the world (so we don't claim it)

Verified 2026-06-25 from primary sources. **Do not pitch any of these as novel.**

| Capability | Who ships it | Source |
|---|---|---|
| Fishing classification from AIS | **GFW** flagship "apparent fishing effort" (two CNNs), open-source `vessel-classification`, trained on the **same 2018 labels we use** | globalfishingwatch.org/data |
| AIS-gap / "going dark" | **GFW** real-time `GAP` event (Welch et al., *Sci. Adv.* 2022) | GFW Events API |
| Loitering / transshipment proxy | **GFW** `LOITERING` event type | GFW Events API |
| Dark-vessel detection (satellite) | **GFW** Sentinel-1 SAR layer, ~20M detections (Paolo et al., *Nature* 2024) | nature.com s41586-023-06825-8 |
| Interactive global map | **GFW** public map, ~70k vessels | globalfishingwatch.org/map |
| Vessel identity / IUU risk | **GFW** Vessel Insights API v3 (30–40+ registries, 400k+ ships) | GFW APIs |
| Detection→prosecution last mile | **TMT, OceanMind, Skylight, Starboard** — via *human analysts*, not per-flag model explanations | tm-tracking.org |

**The one roadmap item GFW does _not_ ship turnkey:** automated *fishing-inside-a-specific-MPA*
alerting. As of the Aug-2024 Marine Manager release it is an analysis/collaboration tool with
**no real-time alerts**. _(Re-verify before any pitch — this is ~22 months old and GFW ships
fast.)_

## 5. What is genuinely new (the wedge)

**Re-verified mid-2026.** One leg of the original wedge is dead: *automated
fishing-inside-an-MPA alerting is NOT novel.* **Skylight** (Allen Institute) ships real-time
MPA-entry + dark-vessel alerts **free** to 70+ countries; **Starboard** ships it paid;
**OceanMind** as a managed service. Do not claim it. The "dark vessel in an MPA" question is
also scientifically closed (Mayorga & Sala et al., *Science* 2025). What survives, in
priority order:

1. **Per-flag (per-position) SHAP explanation.** No dedicated IUU-fishing tool ships a
   per-event "why-flagged" narrative (only Windward's paywalled *sanctions* product does, not
   fishing). GFW disclaims output as "not evidence", with no per-position why. **This is the
   defensible core.**
2. **Offline / no-account / laptop-CPU + auditable dossier.** Every incumbent (Skylight,
   Starboard, OceanMind, GFW) is cloud/web/managed; Skylight's full version needs a vetted
   account. A sovereign, air-gappable, reproducible triage layer for a low-capacity authority
   is unoccupied.

The MPA *alert* is a commodity we **package** on top of consumed signal — not invent. The
posture is **a thin, auditable layer _on top of_ GFW-style signals**, consuming detection.

**Honest limits we state ourselves** (so we read as sober collaborators, not a hype clone):
output is an *inspection-triggering intelligence prompt*, not courtroom proof (VMS outranks
public AIS/SAR in court); AIS-only is blind to the ~75% dark fleet — consume GFW's published
SAR detections to close part of it (see §6.5); GFW data and WDPA boundaries are both
**non-commercial**.

### 5.1 Re-verify before any public deploy

Three claims are load-bearing and ~time-sensitive — re-check immediately before shipping:
(1) Skylight still ships **no** per-event explanation; (2) GFW's per-event AI (was "early
trials" 2026-03) hasn't shipped explainability; (3) UNEP-WCMC sign-off / non-downloadable
tiles for the MPA layer (the biggest legal blocker — see §6.5).

## 6. What we are actually implementing now (v2)

The headline gap — **MPA-overlay alerting + dossiers** — promoted from "v2 someday" to the
next thing we build. Demonstrable end-to-end on data we already have: the 2018 labeled set
carries **real lat/lon** (2012–2015), so we can show which scored fishing positions fall
inside real MPA boundaries.

### 6.1 New modules

| Module | Responsibility |
|---|---|
| `seavigil/mpa.py` | Load MPA polygons (GeoJSON/WDPA); build a `shapely.STRtree` spatial index; assign each (lat, lon) to an MPA or `None` via point-in-polygon. |
| `seavigil/incidents.py` | Group consecutive in-MPA, model-flagged-fishing positions of one vessel into **incidents** (vessel, MPA, time span, n positions, mean fishing probability, gear). |
| `seavigil/dossier.py` | Render each incident to a **dossier**: JSON (machine) + Markdown (human), including the aggregated SHAP "why" and the model's honest caveats. |
| `seavigil/alert.py` | Entrypoint (`python -m seavigil.alert`): load → feature → score → overlay → incidents → dossiers → `results/incidents/`. |
| `data/mpa/sample_mpas.geojson` | Small bundled set of large MPAs (committed reference data) so the demo runs with no extra download. |

### 6.2 Data contract (incident record)

```json
{
  "incident_id": "galapagos_gmr__trawlers_0001",
  "mpa": {"name": "Galápagos Marine Reserve", "wdpa_id": null},
  "vessel_id": "trawlers_412...",
  "gear": "trawlers",
  "time_start_utc": "2014-03-02T01:10:00Z",
  "time_end_utc":   "2014-03-02T06:40:00Z",
  "n_positions": 33,
  "n_fishing_positions": 27,
  "mean_fishing_proba": 0.81,
  "max_fishing_proba": 0.97,
  "centroid": {"lat": -0.74, "lon": -91.1},
  "explanation": {
    "method": "mean per-position SHAP over the incident's fishing points",
    "top_drivers": [
      {"feature": "speed", "mean_value": 1.3, "mean_shap": 0.21},
      {"feature": "turning_rate", "mean_value": 14.2, "mean_shap": 0.12}
    ]
  },
  "caveats": ["apparent fishing, not proven illegal", "AIS-only; dark fleet unseen"]
}
```

### 6.3 Algorithms / decisions

- **Point-in-polygon:** `shapely.STRtree` over MPA polygons; candidate query by bounding box,
  then exact `.contains`. Vectorised over positions; O(n log m). Pure CPU, no GDAL/geopandas
  (keeps the stack light — `shapely` already a dependency).
- **Incident segmentation:** within one vessel's in-MPA, fishing-flagged points, start a new
  incident when the time gap to the previous in-MPA fishing point exceeds a threshold
  (default 6 h, reuse `features.MAX_GAP_MINUTES`) or the MPA changes.
- **Explanation aggregation:** mean per-position SHAP across the incident's fishing points →
  ranked drivers. Reuse `explain.py`'s positive-class SHAP machinery.
- **Honesty guard:** every dossier carries the model's caveats inline; the word "apparent" is
  load-bearing and stays.

### 6.4 Out of scope for v2 (named, not silently dropped)

Live GFW-API ingestion; SAR/AIS fusion; interactive map; prospective forecasting; small-boat
labels. Each is a deliberate later step (see README status table), not a claim we make now.

## 7. Tools & dependencies (and why)

All already in `pyproject.toml` — **v2 adds no new dependency.**

| Tool | Role | Why this one |
|---|---|---|
| `uv` | env + runner, Python pinned 3.12 | reproducible, fast, lockfile-backed |
| `numpy` / `pandas` | arrays / tabular | standard |
| `scikit-learn` | RandomForest + metrics | interpretable, CPU, no GPU |
| `shap` | per-flag attributions | the explanation wedge |
| `shapely>=2.0` | point-in-polygon, STRtree | lightweight geospatial, no GDAL/geopandas |
| `matplotlib` | SHAP/figures | headless `Agg` |
| `pyarrow` | parquet | fast columnar caching of scored positions |
| `pytest` / `ruff` (dev) | tests / lint | quality gate |

Deliberately **not** added: `geopandas`/`fiona`/GDAL (heavy, conflicts with "laptop"),
deep-learning frameworks (no GPU), any cloud SDK.

## 8. Build order (commit-per-step)

1. ✅ Commit v1 baseline + pytest config.
2. ✅ README rewrite (positioning).
3. ✅ This design sketch.
4. `mpa.py` + `data/mpa/sample_mpas.geojson` + tests → commit.
5. `incidents.py` + tests → commit.
6. `dossier.py` + tests → commit.
7. `alert.py` entrypoint wiring end-to-end + tests → commit.
8. Run on real labeled data, write `results/incidents/`, update README status → commit.

## 9. How we'll know it works (evaluation)

- **Unit:** point-in-polygon correct on known in/out coordinates; incident segmentation
  splits on gap/MPA change; dossier schema validates.
- **Integration:** on the real 2012–2015 labeled set, at least one large MPA yields
  incidents whose top SHAP drivers are kinematically sensible (low speed, high turning).
- **Sanity vs. baseline:** in-MPA incidents flagged by the model but **not** by the speed
  baseline are the ones whose dossiers should read most convincingly — that's the model
  "earning its complexity" at the incident level.

## 10. Risks & honest caveats (carried into every pitch)

- **Latency:** GFW feeds run ~3 days (AIS) / ~5 days (SAR) behind; "real-time alerting" is
  aspirational. We say "near-line triage", not "live".
- **Legal:** remote-sensing-only evidence rarely sustains prosecution; output is a lead.
- **Coverage:** AIS-only ⇒ blind to ~75% dark fleet; industrial gears only (2012–2015).
- **License:** GFW data is non-commercial ⇒ SeaVigil stays a public-good / NGO tool.
- **Freshness:** the "GFW has no MPA alerting" and "no competitor ships per-flag explanation"
  claims are ~22 months old — **re-verify before outreach.**

## 11. Outreach mapping (capability → audience)

| Capability | GFW | NGOs (TMT, OceanMind…) | National Geographic / advocacy |
|---|---|---|---|
| Per-flag SHAP explanation | "auditable layer on your API" | "explain the alerts your analysts triage" | "defensible, readable evidence" |
| Fishing-in-MPA dossiers | the synthesis you don't ship turnkey | enforcement-ready leads | "pressure on _this_ reserve, documented" |
| Laptop deployability | reaches users your stack can't | field-deployable | Global-South enforcement story |

**Approach order:** lead with shared lineage + humility (built on your data, reproduces your
target) → pivot to the three unshipped things → name the legal/latency limits yourself →
frame as non-commercial collaboration.
