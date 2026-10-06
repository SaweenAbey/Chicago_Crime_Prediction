"""Inference pipeline for the final selected model (tuned XGBoost, notebook 12 `tuned_04`).

The constants and `engineer_features` below are copied verbatim from
databricks/13_Final_Model/13_Final_Model.ipynb so that the backend applies exactly
the same preprocessing that was used during model development. Do not edit them
here without changing the notebooks too.
"""
import numpy as np
import pandas as pd
from scipy import sparse

RAW_FEATURES = ['date', 'location_description', 'beat', 'district', 'ward', 'community_area', 'latitude', 'longitude', 'domestic']
CATEGORICAL = ['location_description', 'beat', 'district', 'ward', 'community_area', 'area_group']
NUMERIC = ['latitude', 'longitude', 'year', 'hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos', 'is_weekend', 'domestic_int', 'coordinates_missing']


def engineer_features(raw, coordinate_medians):
    """Identical deterministic transformation for training and backend prediction."""
    missing = set(RAW_FEATURES) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing input columns: {sorted(missing)}")
    x = raw[RAW_FEATURES].copy()
    dates = pd.to_datetime(x["date"], errors="coerce")
    if dates.isna().any() or dates.dt.tz is not None:
        raise ValueError("date must contain valid timezone-naive Chicago incident timestamps.")
    x["year"] = dates.dt.year
    hour, weekday, month = dates.dt.hour, dates.dt.dayofweek, dates.dt.month
    for name, values, period in [("hour", hour, 24), ("day_of_week", weekday, 7), ("month", month - 1, 12)]:
        x[f"{name}_sin"] = np.sin(2 * np.pi * values / period)
        x[f"{name}_cos"] = np.cos(2 * np.pi * values / period)
    x["is_weekend"] = (weekday >= 5).astype(int)
    domestic = x["domestic"].astype("string").str.lower().str.strip()
    if not domestic.dropna().isin(["true", "false", "1", "0", "1.0", "0.0"]).all():
        raise ValueError("domestic must be a Boolean, 0/1, or missing.")
    # Matches Member 3: missing domestic is mapped to 0.
    x["domestic_int"] = domestic.isin(["true", "1", "1.0"]).astype(int)
    for col in ["latitude", "longitude"]:
        x[col] = pd.to_numeric(x[col], errors="raise").astype(float)
        if np.isinf(x[col]).any():
            raise ValueError(f"Infinite {col} values are invalid.")
    absent = x[["latitude", "longitude"]].isna().any(axis=1)
    x["coordinates_missing"] = absent.astype(int)
    north = x["latitude"] >= coordinate_medians["latitude"]
    west = x["longitude"] < coordinate_medians["longitude"]
    x["area_group"] = np.select(
        [absent, north & west, north & ~west, ~north & west],
        ["Unknown", "North-West", "North-East", "South-West"], default="South-East",
    )
    for col in CATEGORICAL:
        if col in ["beat", "district", "ward", "community_area"]:
            codes = pd.to_numeric(x[col], errors="raise")
            if (codes.dropna() % 1 != 0).any():
                raise ValueError(f"{col} must contain whole-number geographic codes.")
            x[col] = codes.astype("Int64").astype("string")
        x[col] = x[col].astype("string").fillna("Unknown").astype(str)
    return x[CATEGORICAL + NUMERIC]


def predict_proba_raw(bundle, raw_rows):
    """Same path as notebook 13 `predict_raw`, returning class probabilities instead of labels."""
    frame = engineer_features(raw_rows, bundle["coordinate_medians"])
    features = sparse.csr_matrix(bundle["preprocessor"].transform(frame), dtype=np.float32)
    return bundle["model"].predict_proba(features)


def known_locations(bundle):
    """location_description values the fitted one-hot encoder saw during training."""
    encoder = bundle["preprocessor"].named_transformers_["categories"]
    return set(encoder.categories_[CATEGORICAL.index("location_description")])
