# Model Card: SeaVigil apparent-fishing classifier

Following the model-card framework (Mitchell et al., 2019). Generated from the committed
results (`results/metrics.json`, `results/calibration.json`); reproduce with
`uv run python -m seavigil.run`.

## Model details

- **What.** A binary classifier that scores a single AIS position as *apparent fishing* vs
  *not fishing*, from interpretable vessel-movement features. It is the model behind the
  "AIS apparent fishing in an MPA" behavior; the other four SeaVigil behaviors are rule-based
  or consumed, and are not this model.
- **Architecture.** `scikit-learn` RandomForest (`seavigil.model.train_model`). CPU-only,
  no GPU.
- **Features (10).** `speed`, `speed_roll_mean`, `speed_roll_std`, `turning_rate`,
  `abs_course_change`, `time_gap_min`, `distance_from_shore`, `distance_from_port`,
  `hour_sin`, `hour_cos`. All derived from position, time, and a coastline/port reference;
  no vessel identity is used as a feature.
- **Output.** A calibrated probability per position. Per-incident, the mean SHAP attribution
  over the incident's positions is the human-readable "why".
- **Version / license.** Tracked in this repository; MIT (code). Training labels are GFW
  (CC BY 4.0).

## Intended use

- **Primary use.** Produce an *inspection lead*: surface positions/incidents that look like
  fishing inside a Marine Protected Area, with a per-position reason, for a human to review.
- **Primary users.** Fisheries enforcement and monitoring staff, conservation NGOs, and
  researchers, especially low-capacity authorities who need an offline, auditable tool.
- **Out of scope.** Not legal proof of illegal fishing. Not a detector of non-broadcasting
  (dark) vessels (that is the SAR layer). Not a real-time global map. Not a vessel-identity
  or authorization model (that is the separate authorization layer). Do not use it to make
  automated enforcement or penalty decisions without human review.

## Training data

- **Source.** Global Fishing Watch's openly published, human-labeled AIS dataset
  (Kroodsma et al., *Science* 2018), positions hand-labeled fishing vs not by gear type
  (drifting longlines, purse seines, trawlers), vessels circa 2012-2015. License CC BY 4.0.
  Raw data is not committed; the pipeline regenerates it.
- **Size.** 1,122,490 training positions.
- **Known composition limits.** A finite set of vessels and a few gear types; class balance
  varies by gear; the era is 2012-2015.

## Evaluation

- **Method.** A **vessel-grouped split**: no vessel appears in both train and test, so the
  reported numbers are generalisation to *unseen vessels*, not unseen rows of seen vessels.
  Vessel overlap is asserted to be zero in the pipeline.
- **Test size.** 408,194 held-out positions.
- **Baseline.** A tuned speed-threshold rule (fish if speed below a tuned knot threshold)
  that the model must beat, so the gain over a trivial heuristic is explicit.

## Quantitative results (held-out vessels)

| metric | RandomForest | speed-threshold baseline |
|---|---|---|
| ROC-AUC | **0.946** | 0.392 |
| PR-AUC (average precision) | **0.928** | 0.401 |
| F1 | **0.871** | 0.673 |
| precision | **0.883** | 0.516 |
| recall | 0.860 | 0.969 |

The baseline is a fixed threshold rule, so its ranking AUC is not meaningful; the fair
comparison is at the operating point, where the model beats it on F1 and precision while the
baseline only wins recall by flagging nearly everything slow. The model improves F1 from
0.673 to 0.871 and precision from 0.52 to 0.88.

### Calibration

Probabilities are meant to be read as probabilities, so calibration is reported alongside
discrimination (`results/calibration.json`):

- **Brier score 0.0915** raw, 0.0878 after isotonic recalibration (lower is better; 0 is
  perfect). Log loss 0.296 / 0.284.
- Reliability (predicted vs observed fishing rate per bin, held-out):

  | predicted bin | n | mean predicted | observed fishing rate |
  |---|---:|---:|---:|
  | 0.0-0.1 | 149,227 | 0.011 | 0.021 |
  | 0.4-0.5 | 14,469 | 0.449 | 0.511 |
  | 0.7-0.8 | 28,330 | 0.751 | 0.845 |
  | 0.9-1.0 | 87,686 | 0.949 | 0.952 |

  The model is slightly under-confident in the mid range and well calibrated at the extremes,
  so a score near 0.9 can be read honestly as "about 90% of positions scored this high really
  are fishing". Every AIS dossier carries this calibration statement.

## Ethical considerations

- **Dual-use / enforcement context.** Output can inform inspection and enforcement against
  vessels and crews. It is therefore framed as a *lead, not a verdict*, with a standing
  disclaimer on every dossier, and it is explicitly not legal evidence.
- **False positives harm.** A wrong flag can send an inspector after a lawful vessel. This is
  mitigated by calibrated probabilities, an honest baseline comparison, the per-position SHAP
  reason (so a human can sanity-check the call), and the "apparent" framing.
- **Coverage equity.** AIS is blind to the roughly three-quarters of industrial vessels that
  do not broadcast; relying on AIS alone under-counts the dark fleet, which is why SeaVigil
  pairs it with consumed SAR detections.

## Caveats and recommendations

- "Fishing" is defined **behaviourally** from human-labeled AIS movement, not from catch
  records: it is **apparent** fishing, not proven illegal fishing.
- Metrics are on **unseen vessels** but the same era and gear mix; performance on very
  different fleets, gears, or years is unverified.
- AIS is **spoofable** and has reception gaps; treat a single flag as a prompt to look, not a
  conclusion.
- The model is one layer. For the end-to-end credibility of SeaVigil's *authorization*
  grading against confirmed IUU vessels, see [VALIDATION.md](VALIDATION.md).
