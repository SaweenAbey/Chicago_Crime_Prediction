"""Build backend/models/final_model_bundle.joblib: the final XGBoost from notebook 14.

Run from the project root:  python -m backend.train_final_model
Reads data/clean/chicago_crime_clean.csv, trains on incidents before July 2025 with
early stopping on Jul-Dec 2025, evaluates once on 2026, and writes the bundle plus
backend/models/final_model_metrics.json (shown on the dashboard).
"""
import json
import time

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, top_k_accuracy_score
from sklearn.model_selection import KFold

from backend.app.config import CLEAN_DATA_FILE, FINAL_BUNDLE_FILE, FINAL_METRICS_FILE
from backend.app.final_pipeline import (RAW_FEATURES, TOP_K, normalise_raw, mix_keys, base_features, mix_table,
                                        mix_lookup, add_mix_columns, add_categories)

SEED = 42
TRAIN_END, VALIDATION_END, DATA_END = '2025-07-01', '2026-01-01', '2026-09-17'
# Validation macro F1 of the untuned XGBoost baseline (notebook 11)
BASELINE_MACRO_F1 = 0.1164


def evaluate(y_true, proba, k):
    pred = proba.argmax(1)
    p, r, f, s = precision_recall_fscore_support(y_true, pred, labels=range(k), zero_division=0)
    keep = y_true >= 0
    return dict(accuracy=accuracy_score(y_true, pred), macro_precision=p.mean(), macro_recall=r.mean(),
                macro_f1=f.mean(), weighted_f1=np.average(f, weights=s),
                top3_accuracy=top_k_accuracy_score(y_true[keep], proba[keep], k=3, labels=range(k)))


def main():
    df = pd.read_csv(CLEAN_DATA_FILE, dtype=str)
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df.date >= '2024-01-01') & (df.date < DATA_END)].reset_index(drop=True)
    train_m = (df.date < TRAIN_END).values
    val_m = ((df.date >= TRAIN_END) & (df.date < VALIDATION_END)).values
    test_m = (df.date >= VALIDATION_END).values
    print(f'Rows {len(df):,} | train {train_m.sum():,} | validation {val_m.sum():,} | test {test_m.sum():,}')

    classes = sorted(df.loc[train_m, 'primary_type'].unique())
    y = df.primary_type.map({c: i for i, c in enumerate(classes)}).fillna(-1).astype(int).values
    k = len(classes)

    x = normalise_raw(df[RAW_FEATURES])
    frequencies = {c: x.loc[train_m, c].value_counts(normalize=True) for c in ['location_description', 'beat']}
    f = base_features(x, frequencies)

    # Historical crime mix: out-of-fold for training rows, full-training statistics for everything else
    one_hot = np.zeros((len(df), k), np.float32)
    tr_idx = np.where(train_m)[0]
    one_hot[tr_idx, y[tr_idx]] = 1
    prior_all = one_hot[tr_idx].mean(0)
    top = np.argsort(-prior_all)[:TOP_K]
    prior = prior_all[top]
    top_names = [classes[i] for i in top]
    other = np.where(~train_m)[0]
    folds = list(KFold(5, shuffle=True, random_state=SEED).split(tr_idx))
    mix_tables = {}
    for tag, keys in mix_keys(x).items():
        keys = keys.astype(str).values
        values = np.zeros((len(df), TOP_K), np.float32)
        mix_tables[tag] = mix_table(keys[tr_idx], one_hot[tr_idx][:, top], prior)
        values[other] = mix_lookup(mix_tables[tag], keys[other], prior)
        for a, b in folds:
            table = mix_table(keys[tr_idx[a]], one_hot[tr_idx[a]][:, top], prior)
            values[tr_idx[b]] = mix_lookup(table, keys[tr_idx[b]], prior)
        add_mix_columns(f, values, tag, top_names)
    categories = {c: list(pd.Series(x[c]).astype('category').cat.categories) for c in ['location_description', 'district']}
    f = add_categories(f, x, categories)

    start = time.perf_counter()
    model = xgb.XGBClassifier(n_estimators=2000, max_depth=7, learning_rate=0.06, subsample=0.8, colsample_bytree=0.7,
                              min_child_weight=5, reg_lambda=2.0, enable_categorical=True, max_cat_to_onehot=1,
                              tree_method='hist', n_jobs=-1, random_state=SEED, early_stopping_rounds=50,
                              eval_metric='mlogloss')
    model.fit(f[train_m], y[train_m], eval_set=[(f[val_m], y[val_m])], verbose=100)
    print(f'Training time {time.perf_counter() - start:.0f}s | best iteration {model.best_iteration}')

    val = evaluate(y[val_m], model.predict_proba(f[val_m]), k)
    test = evaluate(y[test_m], model.predict_proba(f[test_m]), k)
    print('validation', {m: round(v, 4) for m, v in val.items()})
    print('test', {m: round(v, 4) for m, v in test.items()})

    bundle = dict(model=model, classes=classes, feature_names=list(f.columns), frequencies=frequencies,
                  mix_tables=mix_tables, mix_prior=prior.tolist(), top_classes=top_names, categories=categories,
                  on_the_hour_share=float(f.loc[train_m, 'on_the_hour'].mean()),
                  split=dict(train_end=TRAIN_END, validation_end=VALIDATION_END))
    joblib.dump(bundle, FINAL_BUNDLE_FILE, compress=3)

    metrics = json.loads(FINAL_METRICS_FILE.read_text(encoding='utf-8'))
    metrics['source'] = ('backend/train_final_model.py, same features and settings as '
                         'databricks/14_Improved_Model (baselines from notebook 11)')
    metrics.pop('experiment_id', None)
    metrics['selection'] = dict(
        model='XGBoost', tag='final', rule=metrics['selection']['rule'],
        validation_macro_f1=round(val['macro_f1'], 4), validation_weighted_f1=round(val['weighted_f1'], 4),
        validation_top3_accuracy=round(val['top3_accuracy'], 4), baseline_macro_f1=BASELINE_MACRO_F1,
        macro_f1_change=round(val['macro_f1'] - BASELINE_MACRO_F1, 4), best_iteration=int(model.best_iteration),
        test_used_for_selection=False)
    metrics['test'] = {m: round(float(v), 4) for m, v in test.items()} | dict(num_classes=k)
    metrics['test']['majority_class_accuracy'] = round(float((y[test_m] == np.bincount(y[train_m]).argmax()).mean()), 4)
    FINAL_METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print('Saved', FINAL_BUNDLE_FILE, 'and', FINAL_METRICS_FILE)


if __name__ == '__main__':
    main()
