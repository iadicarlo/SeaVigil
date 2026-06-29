# Sentinel-2 optical vessel detection (the trained Ai2 model)

SeaVigil's optical sensor is the Ai2 (Allen Institute) Sentinel-2 vessel detector, run on demand on
scenes we choose. It is a trained model (Swin backbone + FPN + Faster R-CNN over nine bands,
including the two short-wave-infrared bands that let it tell a white hull from a white cloud), with a
companion model for length, width, speed, heading and vessel type. Ai2 report 80%+ F1. Both the model
code (`allenai/rslearn`, `allenai/rslearn_projects`) and the checkpoints are Apache-2.0 / openly
hosted.

This replaces, for real use, the model-free threshold detector in `scripts/run_sentinel2_detection.py`.
On a hazy Galapagos scene the threshold detector flagged 294 "vessels" that were mostly small cumulus
the cloud mask missed; the trained model rejects that cloud and classifies the real vessels. The
threshold detector stays as a zero-dependency clear-water quick-look; the trained model is the sensor.

## One-time setup

The model code is cloned under `vendor/` (gitignored) and run from an isolated virtualenv so it does
not disturb the Sentinel-1 / threshold-detector environment.

```sh
# 1. Code (Apache-2.0)
mkdir -p vendor && cd vendor
git clone --depth 1 https://github.com/allenai/rslearn.git
git clone --depth 1 https://github.com/allenai/rslearn_projects.git
cd ..

# 2. Isolated env. rslearn pulls torch + lightning + rasterio; these extra packages are optional
#    deps it imports at load time but does not list, plus the attribute model's backbone.
python3.11 -m venv .venv-rslp
./.venv-rslp/bin/pip install -U pip wheel
./.venv-rslp/bin/pip install -e vendor/rslearn -e vendor/rslearn_projects
./.venv-rslp/bin/pip install einops google-cloud-storage google-cloud-bigquery beaker-py scipy satlaspretrain_models

# 3. Checkpoints (~2.2 GB total) into the RSLP_PREFIX layout the configs expect
cd vendor/rslearn_projects
echo "RSLP_PREFIX=project_data/" > .env
mkdir -p project_data/projects/sentinel2_vessels/data_20250213_02_all_bands \
         project_data/projects/sentinel2_vessel_attribute/data_20250205_regress_00
wget -q https://storage.googleapis.com/ai2-rslearn-projects-data/projects/sentinel2_vessels/data_20250213_02_all_bands/checkpoints/best.ckpt \
     -O project_data/projects/sentinel2_vessels/data_20250213_02_all_bands/best.ckpt
wget -q https://storage.googleapis.com/ai2-rslearn-projects-data/projects/sentinel2_vessel_attribute/data_20250205_regress_00/checkpoints/best.ckpt \
     -O project_data/projects/sentinel2_vessel_attribute/data_20250205_regress_00/best.ckpt
cd ../..
```

On a machine without an NVIDIA GPU (e.g. an Apple Silicon Mac), set `accelerator: cpu`, `devices: 1`,
`strategy: auto` under `trainer:` in both `data/sentinel2_vessels/config.yaml` and
`data/sentinel2_vessel_attribute/config.yaml` (Lightning otherwise picks the MPS accelerator with a
DDP strategy, which it does not support).

## Run

The scene is pulled by ID from the public Sentinel-2 bucket anonymously (no GCP credentials), so you
only pass an L1C scene ID. `RSLP_PYTHON` points at the isolated env's interpreter.

```sh
RSLP_PYTHON=./.venv-rslp/bin/python python scripts/run_sentinel2_allen.py \
  --scene-id S2C_MSIL1C_20260613T151721_N0512_R125_T18LTM_20260613T184148 \
  --out results/s2/scene.csv --crop-dir results/s2/scene_crops

# fold the detections into the optical view (own AIS cross-match, severity, accumulation):
uv run python scripts/sar_detections_to_incidents.py --detections results/s2/scene.csv --source optical
```

The model outputs one detection per vessel with a confidence, an estimated length / width / speed /
heading and a vessel type, plus a true-color crop of each. `--source optical` writes a `web/data/s2`
view kept separate from the Sentinel-1 `web/data/sar` view.

## Scope

Optical only sees vessels in clear daylight, so cloud is the hard limit and SAR remains the
all-weather primary. The model runs on a full scene (CPU inference takes a few minutes per scene); for
production, target it at a hotspot the way `scripts/sar_engine.py` targets SAR.
