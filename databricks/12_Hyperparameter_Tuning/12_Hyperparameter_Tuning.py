# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 12 - Hyperparameter Tuning | Member 4 lead
# MAGIC ## 1. What I am doing
# MAGIC Run a small, reproducible grid over the two strongest converged baseline families.
# MAGIC ## 2. Why I am doing it
# MAGIC Depth, regularization, leaf size, class weights and learning rate can improve generalization.
# MAGIC A fixed chronological validation split preserves time ordering; random cross-validation would not.
# MAGIC Repeated validation selection can overfit validation, so one untouched test evaluation follows.

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
import warnings
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.model_selection import ParameterGrid
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, FunctionTransformer

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

TUNING_GRIDS = {
    "Logistic_Regression": {"classifier__C": [0.1, 1.0], "classifier__class_weight": [None, "balanced"],
                            "classifier__max_iter": [1200]},
    "Decision_Tree": {"max_depth": [12, 20], "min_samples_leaf": [5, 20], "class_weight": [None, "balanced"]},
    "Random_Forest": {"max_depth": [16, 24], "min_samples_leaf": [5, 15],
                      "class_weight": [None, "balanced_subsample"]},
    "XGBoost": {"max_depth": [4, 6], "learning_rate": [0.05, 0.1], "n_estimators": [150]},
}

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

def load_split(split):
    load_manifest()
    return (sparse.load_npz(experiment_dir() / f"{split}_features.npz"),
            np.load(experiment_dir() / f"{split}_labels.npy"))

# COMMAND ----------

def build_model(name, overrides=None):
    if name == "Logistic_Regression":
        # Center only the small numeric block. Centering the whole sparse matrix
        # would densify hundreds of one-hot columns; leaving coordinates uncentered
        # creates very large offsets and can prevent SAGA convergence.
        numeric_scaling = ColumnTransformer([
            ("numbers", Pipeline([
                ("dense", FunctionTransformer(sparse.csr_matrix.toarray, accept_sparse=True)),
                ("standardize", StandardScaler()),
            ]), slice(-len(NUMERIC), None)),
        ], remainder="passthrough", sparse_threshold=1.0)
        model = Pipeline([
            ("scale", numeric_scaling),
            ("classifier", LogisticRegression(C=1.0, solver="saga", max_iter=600, tol=1e-3, random_state=SEED)),
        ])
    elif name == "Decision_Tree":
        model = DecisionTreeClassifier(max_depth=16, min_samples_leaf=10, random_state=SEED)
    elif name == "Random_Forest":
        model = RandomForestClassifier(n_estimators=100, max_depth=20, min_samples_leaf=5,
                                       max_features="sqrt", n_jobs=2, random_state=SEED)
    elif name == "XGBoost":
        try:
            from xgboost import XGBClassifier
        except ImportError as exc:
            raise RuntimeError("Run the package installation cell at the top of this notebook to install xgboost.") from exc
        model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1,
                              subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                              objective="multi:softprob", eval_metric="mlogloss", n_jobs=2,
                              random_state=SEED)
    else:
        raise ValueError(f"Unknown model: {name}")
    return model.set_params(**(overrides or {}))

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

def train_candidate(name, tag="baseline", overrides=None):
    manifest = load_manifest()
    if (experiment_dir() / "final" / "selection.json").exists():
        raise RuntimeError("Model selection is frozen. Use a new EXPERIMENT for further training.")
    x_train, y_train = load_split("train")
    x_val, y_val = load_split("validation")
    model = build_model(name, overrides)
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model.fit(x_train, y_train)
    training_seconds = time.perf_counter() - start
    warning_messages = [str(w.message) for w in caught]
    for message in warning_messages:
        print("Training warning:", message)
    directory = experiment_dir() / "models" / f"{name}_{tag}"
    directory.mkdir(parents=True, exist_ok=True)
    val, per_class, cm = evaluate(model, x_val, y_val, manifest["classes"])
    train, train_classes, train_cm = evaluate(model, x_train, y_train, manifest["classes"])
    save_evaluation(directory, "validation", val, per_class, cm)
    save_evaluation(directory, "train", train, train_classes, train_cm)
    joblib.dump(model, directory / "model.joblib", compress=3)
    result = dict(model=name, tag=tag, experiment_id=manifest["experiment_id"],
                  basis="validation", training_seconds=training_seconds,
                  train_macro_f1=train["macro_f1"], parameters=repr(model.get_params()),
                  overrides=overrides or {}, warnings=warning_messages,
                  converged=not any(issubclass(w.category, ConvergenceWarning) for w in caught),
                  model_path=str(directory / "model.joblib"), **val)
    if name == "XGBoost":
        result["xgboost_version"] = importlib.metadata.version("xgboost")
    save_json(directory / "result.json", result)
    (directory / "findings.txt").write_text(interpretation(per_class, cm), encoding="utf-8")
    print(pd.DataFrame([result]).drop(columns=["parameters", "model_path", "warnings"]).to_string(index=False))
    print(interpretation(per_class, cm))
    return result

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

def tune_and_select():
    final = experiment_dir() / "final"
    if (final / "selection.json").exists():
        print("Selection already frozen; reusing saved recommendation.")
        return read_json(final / "selection.json")
    baseline = comparison()
    eligible = baseline.loc[baseline.converged]
    if len(eligible) < 2:
        raise RuntimeError("At least two converged baselines are required. Review training warnings.")
    # Fixed, chronological validation search. Never random CV across time or test tuning.
    candidates = baseline.to_dict("records")
    for name in eligible.head(2).model:
        for i, parameters in enumerate(ParameterGrid(TUNING_GRIDS[name]), start=1):
            print(f"Tuning {name}, trial {i}: {parameters}")
            candidates.append(train_candidate(name, f"tuned_{i:02d}", parameters))
    ranking = rank_results(pd.DataFrame(candidates))
    winner = ranking.loc[ranking.converged].iloc[0].to_dict()
    final.mkdir(parents=True, exist_ok=True)
    ranking.to_csv(final / "baseline_vs_tuned.csv", index=False)
    # Keep the exact train-fitted candidate that won validation; no hidden refit.
    model = joblib.load(winner["model_path"])
    bundle = joblib.load(experiment_dir() / "preprocessing.joblib")
    bundle.update(model=model, manifest=load_manifest())
    joblib.dump(bundle, final / "final_model_bundle.joblib", compress=3)
    environment_versions = versions()
    if winner["model"] == "XGBoost":
        environment_versions["xgboost"] = winner["xgboost_version"]
    save_json(final / "environment_versions.json", environment_versions)
    selected_baseline = baseline.loc[baseline.model == winner["model"]].iloc[0]
    selection = dict(model=winner["model"], tag=winner["tag"], validation_macro_f1=float(winner["macro_f1"]),
                     validation_weighted_f1=float(winner["weighted_f1"]),
                     baseline_macro_f1=float(selected_baseline.macro_f1),
                     macro_f1_change=float(winner["macro_f1"] - selected_baseline.macro_f1),
                     training_seconds=float(winner["training_seconds"]),
                     rule="Converged candidates: highest validation macro F1, then weighted F1, then shorter training time.",
                     artifact=str(final / "final_model_bundle.joblib"),
                     experiment_id=load_manifest()["experiment_id"],
                     test_used_for_selection=False)
    save_json(final / "selection.json", selection)
    return selection

# COMMAND ----------

# MEMBER4 EXECUTION CELLS

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Code / analysis
# MAGIC The small grids are printed below. All trials use the same full training/validation snapshot.
# MAGIC Baselines remain eligible: if tuning does not improve a baseline, the baseline can win.
# MAGIC Ranking: highest macro F1, then weighted F1, then shorter training time. Convergence is required.
# MAGIC Save the exact winning train-fitted estimator, preprocessing, mapping and package versions.
# MAGIC This intentionally avoids refitting on validation after selection.

# COMMAND ----------

print(json.dumps(TUNING_GRIDS, indent=2))
selection = tune_and_select()
display(pd.read_csv(experiment_dir() / "final" / "baseline_vs_tuned.csv"))
print(json.dumps(selection, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Findings / conclusion
# MAGIC The recommendation above records baseline-vs-selected F1, runtime and artifact location.
# MAGIC Selection is now frozen. Notebook 13 evaluates the chosen model once on the held-out test set.
# MAGIC Do not change model selection after seeing test results. Use a new future holdout for a new study.