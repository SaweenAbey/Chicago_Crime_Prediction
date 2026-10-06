import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR.parent / "data"

# Final selected model exported by databricks notebook 12 (tuned XGBoost + fitted preprocessing)
FINAL_BUNDLE_FILE = MODELS_DIR / "final_model_bundle.joblib"
FINAL_METRICS_FILE = MODELS_DIR / "final_model_metrics.json"

# Interim model from backend/train_model.py, used only until the final bundle is present
MODEL_FILE = MODELS_DIR / "chicago_crime_model.joblib"
LABEL_ENCODER_FILE = MODELS_DIR / "label_encoder.joblib"

CLEAN_DATA_FILE = DATA_DIR / "clean" / "chicago_crime_clean.csv"
RAW_DATA_FILE = DATA_DIR / "raw" / "chicago_crime_raw.csv"

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
).split(",")
