# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 11 - Model Comparison | Member 1
# MAGIC ## 1. What I am doing
# MAGIC Compare all four completed baselines on the same validation snapshot.
# MAGIC ## 2. Why I am doing it
# MAGIC Accuracy alone can conceal errors on rare crime categories. Rank by macro F1 first,
# MAGIC weighted F1 second, then shorter training time. Inspect convergence and per-class errors too.

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
import matplotlib.pyplot as plt
import pandas as pd

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

def comparison(require_all=True):
    manifest = load_manifest()
    rows = []
    for name in MODEL_NAMES:
        path = experiment_dir() / "models" / f"{name}_baseline" / "result.json"
        if not path.exists():
            if require_all:
                raise RuntimeError(f"Run the {name} baseline notebook before comparison/tuning.")
            continue
        result = read_json(path)
        if result["experiment_id"] != manifest["experiment_id"]:
            raise ValueError("Results belong to different data snapshots. Retrain baselines.")
        rows.append(result)
    if not rows:
        raise RuntimeError("No baseline results available.")
    return rank_results(pd.DataFrame(rows))

# COMMAND ----------

def rank_results(frame):
    return frame.sort_values(["macro_f1", "weighted_f1", "training_seconds", "model", "tag"],
                             ascending=[False, False, True, True, True]).reset_index(drop=True)

# COMMAND ----------

def write_comparison(spark=None):
    table = comparison()
    columns = ["model", "basis", "accuracy", "macro_precision", "macro_recall", "macro_f1",
               "weighted_f1", "train_macro_f1", "training_seconds", "evaluation_seconds", "converged"]
    output = experiment_dir() / "evidence"
    output.mkdir(parents=True, exist_ok=True)
    table[columns].to_csv(output / "model_comparison.csv", index=False)
    if spark is not None:
        (spark.createDataFrame(table[columns].assign(experiment=EXPERIMENT))
         .write.mode("overwrite").option("overwriteSchema", "true")
         .saveAsTable(f"{CATALOG_SCHEMA}.chicago_crime_member4_comparison"))
    return table[columns]

# COMMAND ----------

# MEMBER4 EXECUTION CELLS

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Code / analysis
# MAGIC Missing baseline results stop the comparison, preventing an incomplete ranking.
# MAGIC This writes only `workspace.default.chicago_crime_member4_comparison`.

# COMMAND ----------

comparison_table = write_comparison(spark)
display(comparison_table)
fig, ax = plt.subplots(figsize=(10, 5))
comparison_table.set_index("model")[["macro_f1", "weighted_f1", "accuracy"]].plot.bar(ax=ax)
ax.set(ylabel="Validation score", ylim=(0, 1), title="Same validation data - four baselines")
plt.xticks(rotation=15)
fig.tight_layout()
fig.savefig(experiment_dir() / "evidence" / "model_comparison.png", dpi=150)
display(fig)
plt.close(fig)

# COMMAND ----------

for name in MODEL_NAMES:
    directory = experiment_dir() / "models" / f"{name}_baseline"
    print(name)
    print((directory / "findings.txt").read_text(encoding="utf-8"))
    display(pd.read_csv(directory / "validation_per_class.csv").sort_values("support").head(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Findings / conclusion
# MAGIC Review whether the macro-F1 leader also has acceptable rare-class recall and runtime.
# MAGIC The two leading converged candidates are tuned in folder 12. Final recommendation follows tuning.
# MAGIC Validation performance is selection evidence; it is not an unbiased final test estimate.