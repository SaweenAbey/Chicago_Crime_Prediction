# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 13 - Final Model | Shared handover from Member 4
# MAGIC ## 1. What I am doing
# MAGIC Evaluate the validation-selected model on the final test split and verify raw-input prediction.
# MAGIC ## 2. Why I am doing it
# MAGIC An untouched temporal holdout estimates performance on later incidents. The same saved
# MAGIC preprocessing must be used by the backend; the model predicts crime type, not future crime occurrence.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Install notebook libraries
# MAGIC Run on Databricks serverless notebook compute using Python 3.11 or newer.
# MAGIC Dependencies are installed directly in this cell; no separate setup file is needed.
# MAGIC Use the same pinned versions in every Member 4 notebook.
# MAGIC Run the restart cell immediately after installation, then continue with Imports.

# COMMAND ----------

# MAGIC %pip install numpy==2.4.6 scipy==1.17.1 scikit-learn==1.9.0 joblib==1.5.3 matplotlib==3.11.0 xgboost==3.4.1
# MAGIC %pip install "pandas<3.0"

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Imports

# COMMAND ----------

from pathlib import Path
import importlib.metadata
import json
import time
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Databricks table, artifact location and split configuration
# MAGIC Keep these settings identical in all Member 4 notebooks.
# MAGIC Train: before July 2025; validation: July-December 2025; test: from January 2026.
# MAGIC The first baseline run freezes the clean-table snapshot in a shared volume.
# MAGIC Later notebooks reuse the same data and fitted preprocessing.
# MAGIC Change EXPERIMENT everywhere to intentionally start a new experiment.

# COMMAND ----------

CATALOG_SCHEMA = 'workspace.default'
SOURCE_TABLE = f'{CATALOG_SCHEMA}.chicago_crime_clean'
VOLUME_NAME = 'chicago_crime_member4'
ARTIFACT_ROOT = Path(f'/Volumes/workspace/default/{VOLUME_NAME}')
EXPERIMENT = 'member4_v1'
SEED = 42
MAX_LOCAL_ROWS = 750000
TRAIN_END = '2025-07-01'
VALIDATION_END = '2026-01-01'
MODEL_NAMES = ['Logistic_Regression', 'Decision_Tree', 'Random_Forest', 'XGBoost']
RAW_FEATURES = ['date', 'location_description', 'beat', 'district', 'ward', 'community_area', 'latitude', 'longitude', 'domestic']
CATEGORICAL = ['location_description', 'beat', 'district', 'ward', 'community_area', 'area_group']
NUMERIC = ['latitude', 'longitude', 'year', 'hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'month_sin', 'month_cos', 'is_weekend', 'domestic_int', 'coordinates_missing']
LEAKAGE_EXCLUSIONS = ['iucr', 'description', 'fbi_code', 'arrest', 'updated_on', 'case_number']

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Local data and evaluation functions
# MAGIC These cells define the functions used by this notebook. Execute them from top to bottom.
# MAGIC All required code is included here; there are no imports from another project notebook.

# COMMAND ----------

def experiment_dir():
    return ARTIFACT_ROOT / EXPERIMENT

# COMMAND ----------

def save_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")

# COMMAND ----------

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

# COMMAND ----------

def versions():
    return {p: importlib.metadata.version(p) for p in
            ["numpy", "pandas", "scipy", "scikit-learn", "joblib", "matplotlib"]}

# COMMAND ----------

def configuration():
    return dict(source_table=SOURCE_TABLE, train_end=TRAIN_END, validation_end=VALIDATION_END,
                seed=SEED, raw_features=RAW_FEATURES, categorical=CATEGORICAL, numeric=NUMERIC,
                preprocessing_version=1)

# COMMAND ----------

def load_manifest():
    path = experiment_dir() / "manifest.json"
    if not path.exists():
        raise RuntimeError("Run a baseline notebook (07-10) to prepare the shared data first.")
    manifest = read_json(path)
    if manifest["configuration"] != configuration():
        raise ValueError("Configuration changed. Use a new EXPERIMENT and prepare data again.")
    if manifest["versions"] != versions():
        raise ValueError("Package versions differ from preparation. Use the saved environment versions.")
    return manifest

# COMMAND ----------

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

# COMMAND ----------

def load_split(split):
    load_manifest()
    return (sparse.load_npz(experiment_dir() / f"{split}_features.npz"),
            np.load(experiment_dir() / f"{split}_labels.npy"))

# COMMAND ----------

def metric_details(y_true, y_pred, classes):
    labels = list(range(len(classes)))
    names = list(classes)
    if np.any(y_true == -1):
        labels.append(-1)
        names.append("UNSEEN_IN_TRAINING")
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0,
    )
    metrics = dict(accuracy=float(accuracy_score(y_true, y_pred)),
                   macro_precision=float(precision.mean()), macro_recall=float(recall.mean()),
                   macro_f1=float(f1.mean()), weighted_f1=float(np.average(f1, weights=support)))
    per_class = pd.DataFrame(dict(primary_type=names, precision=precision, recall=recall, f1=f1, support=support))
    cm = pd.DataFrame(confusion_matrix(y_true, y_pred, labels=labels), index=names, columns=names)
    return metrics, per_class, cm

# COMMAND ----------

def evaluate(model, x, y, classes):
    start = time.perf_counter()
    prediction = model.predict(x)
    metrics, per_class, cm = metric_details(y, prediction, classes)
    metrics["evaluation_seconds"] = time.perf_counter() - start
    return metrics, per_class, cm

# COMMAND ----------

def save_evaluation(directory, split, metrics, per_class, cm):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    save_json(directory / f"{split}_metrics.json", metrics)
    per_class.to_csv(directory / f"{split}_per_class.csv", index=False)
    cm.to_csv(directory / f"{split}_confusion_matrix.csv", index_label="actual / predicted")
    fig, ax = plt.subplots(figsize=(13, 11))
    normalized = cm.to_numpy() / np.maximum(cm.sum(axis=1).to_numpy()[:, None], 1)
    plot = ax.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
    ax.set(xticks=range(len(cm)), yticks=range(len(cm)), xticklabels=cm.columns,
           yticklabels=cm.index, xlabel="Predicted crime type", ylabel="Actual crime type",
           title=f"{split.title()} confusion matrix (row-normalized)")
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=7)
    plt.setp(ax.get_yticklabels(), fontsize=7)
    fig.colorbar(plot, ax=ax)
    fig.tight_layout()
    fig.savefig(directory / f"{split}_confusion_matrix.png", dpi=150)
    plt.close(fig)

# COMMAND ----------

def show_confusion(path):
    fig, ax = plt.subplots(figsize=(13, 11))
    ax.imshow(plt.imread(path))
    ax.axis("off")
    fig.tight_layout()
    plt.show()
    plt.close(fig)

# COMMAND ----------

def interpretation(per_class, cm):
    supported = per_class.loc[per_class.support > 0].sort_values("f1")
    errors = cm.to_numpy().copy()
    np.fill_diagonal(errors, 0)
    lines = []
    if not supported.empty:
        best, worst = supported.iloc[-1], supported.iloc[0]
        lines += [f"Strongest supported class: {best.primary_type} (F1={best.f1:.3f}).",
                  f"Weakest supported class: {worst.primary_type} (F1={worst.f1:.3f}, support={int(worst.support)})."]
    if errors.max() > 0:
        i, j = np.unravel_index(errors.argmax(), errors.shape)
        lines.append(f"Largest error pair: {cm.index[i]} predicted as {cm.columns[j]} ({errors[i, j]} rows).")
    lines.append("Compare macro and weighted F1: common classes can conceal weak rare-class performance.")
    return "\n".join(lines)

# COMMAND ----------

def predict_raw(bundle, raw_rows):
    """Backend entry point: supply a pandas DataFrame with RAW_FEATURES only."""
    frame = engineer_features(raw_rows, bundle["coordinate_medians"])
    features = sparse.csr_matrix(bundle["preprocessor"].transform(frame), dtype=np.float32)
    codes = bundle["model"].predict(features).astype(int)
    return np.asarray(bundle["classes"])[codes]

# COMMAND ----------

def final_evaluation():
    final = experiment_dir() / "final"
    if not (final / "selection.json").exists():
        raise RuntimeError("Run notebook 12 to freeze the selected model first.")
    selection = read_json(final / "selection.json")
    manifest = load_manifest()
    if selection["experiment_id"] != manifest["experiment_id"]:
        raise ValueError("Selected model belongs to a different data snapshot.")
    if (final / "test_complete.json").exists():
        print("Returning the recorded test evaluation. Do not use it to retune.")
        return read_json(final / "test_complete.json")
    bundle = joblib.load(final / "final_model_bundle.joblib")
    x_test, y_test = load_split("test")
    metrics, per_class, cm = evaluate(bundle["model"], x_test, y_test, bundle["classes"])
    save_evaluation(final, "test", metrics, per_class, cm)
    (final / "test_findings.txt").write_text(interpretation(per_class, cm), encoding="utf-8")
    save_json(final / "test_complete.json", metrics)
    return metrics

# COMMAND ----------

# MEMBER4 EXECUTION CELLS

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Code / analysis
# MAGIC Selection must already be frozen by notebook 12. Reruns return the recorded test metrics.

# COMMAND ----------

test_metrics = final_evaluation()
display(pd.DataFrame([test_metrics]))
final_directory = experiment_dir() / "final"
display(pd.read_csv(final_directory / "test_per_class.csv"))
show_confusion(final_directory / "test_confusion_matrix.png")
print((final_directory / "test_findings.txt").read_text(encoding="utf-8"))

# COMMAND ----------

bundle = joblib.load(final_directory / "final_model_bundle.joblib")
example_inputs = joblib.load(experiment_dir() / "train_rows.joblib")[RAW_FEATURES].head(5)
display(example_inputs)
print("Predicted primary_type:", predict_raw(bundle, example_inputs).tolist())
print("Required backend fields:", RAW_FEATURES)
print("Feature names:", bundle["feature_names"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Findings / conclusion
# MAGIC Hand over final_model_bundle.joblib, environment_versions.json and manifest.json.
# MAGIC The engineer_features and predict_raw functions are included in this notebook.
# MAGIC Backend developers can copy these functions and the feature constants into their application,
# MAGIC load the trusted bundle with joblib.load, and call predict_raw(bundle, pandas_dataframe).
# MAGIC Predictions are incident crime types, not forecasts of future crime occurrence.
# MAGIC Run 17_Report_Evidence/Member_4/Member_4_Results to export the completed results PDF.