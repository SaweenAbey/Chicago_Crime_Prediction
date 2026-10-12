"""Feature pipeline for the final XGBoost (databricks/14_Improved_Model).

The transformations below reproduce notebook 14 exactly. They are shared by
backend/train_final_model.py (which builds the bundle) and by the API (which
serves it), so training and prediction can never drift apart. Do not edit them
here without changing notebook 14 too.
"""
import numpy as np
import pandas as pd

RAW_FEATURES = ['date', 'location_description', 'beat', 'district', 'ward', 'community_area', 'latitude', 'longitude', 'domestic']
GEO_CODES = ['beat', 'district', 'ward', 'community_area']
TOP_K = 12          # crime-mix features are kept for the 12 most common training classes
SMOOTHING = 20      # pseudo-count pulling rare keys towards the citywide crime mix


def normalise_raw(raw):
    """Clean the nine raw inputs the same way notebook 14 does."""
    missing = set(RAW_FEATURES) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing input columns: {sorted(missing)}")
    x = raw[RAW_FEATURES].copy()
    x['date'] = pd.to_datetime(x['date'])
    for c in GEO_CODES:
        x[c] = pd.to_numeric(x[c], errors='coerce').astype('Int64').astype(str).replace('<NA>', 'Unknown')
    x['location_description'] = x['location_description'].fillna('Unknown').astype(str).str.strip().str.upper()
    x['latitude'] = pd.to_numeric(x['latitude'], errors='coerce')
    x['longitude'] = pd.to_numeric(x['longitude'], errors='coerce')
    x['domestic_int'] = x['domestic'].astype(str).str.lower().isin(['true', '1', '1.0']).astype(int)
    return x


def mix_keys(x):
    """Grouping keys for the historical crime-mix features, in notebook 14 order."""
    hour_block = (x['date'].dt.hour // 6).astype(str)
    grid = (x['latitude'].round(3) // 0.005).astype(str) + '_' + (x['longitude'].round(3) // 0.006).astype(str)
    return {
        'loc': x['location_description'],
        'beat': x['beat'],
        'locdist': x['location_description'] + '|' + x['district'],
        'lochr': x['location_description'] + '|' + hour_block,
        'domloc': x['domestic_int'].astype(str) + '|' + x['location_description'],
        'grid': grid,
    }


def base_features(x, frequencies):
    """Time, reporting-pattern, geographic and frequency features (notebook 14, section 6.1)."""
    d = x['date']
    f = pd.DataFrame(index=x.index)
    f['hour'], f['minute'], f['dow'] = d.dt.hour, d.dt.minute, d.dt.dayofweek
    f['month'], f['day'] = d.dt.month, d.dt.day
    f['is_midnight'] = ((d.dt.hour == 0) & (d.dt.minute == 0)).astype(int)
    f['on_the_hour'] = (d.dt.minute == 0).astype(int)
    f['first_of_month'] = (d.dt.day == 1).astype(int)
    f['is_weekend'] = (d.dt.dayofweek >= 5).astype(int)
    f['domestic_int'] = x['domestic_int']
    f['latitude'], f['longitude'] = x['latitude'], x['longitude']
    f['rot45_a'], f['rot45_b'] = x['latitude'] + x['longitude'], x['latitude'] - x['longitude']
    f['coordinates_missing'] = x['latitude'].isna().astype(int)
    for c in GEO_CODES:
        f[c + '_num'] = pd.to_numeric(x[c], errors='coerce')
    for c in ['location_description', 'beat']:
        f[c + '_freq'] = x[c].map(frequencies[c]).fillna(0)
    return f


def mix_table(keys, one_hot, prior):
    """Smoothed share of each top crime type per key (rows of one_hot are training incidents)."""
    g = pd.DataFrame(one_hot).groupby(np.asarray(keys))
    s, n = g.sum(), g.size()
    return pd.DataFrame((s.values + SMOOTHING * prior) / (n.values[:, None] + SMOOTHING), index=s.index)


def mix_lookup(table, keys, prior):
    return table.reindex(np.asarray(keys)).fillna(pd.Series(prior, index=table.columns)).values


def add_mix_columns(f, values, tag, top_names):
    for j, name in enumerate(top_names):
        f[f'mix_{tag}_{name[:12]}'] = values[:, j]


def add_categories(f, x, categories):
    for c in ['location_description', 'district']:
        f[c] = pd.Categorical(x[c], categories=categories[c])
    return f


def build_features(raw_rows, bundle):
    """Model-ready features for new incidents, using the statistics stored in the bundle."""
    x = normalise_raw(raw_rows)
    f = base_features(x, bundle['frequencies'])
    prior = np.asarray(bundle['mix_prior'])
    for tag, keys in mix_keys(x).items():
        add_mix_columns(f, mix_lookup(bundle['mix_tables'][tag], keys.astype(str), prior), tag, bundle['top_classes'])
    f = add_categories(f, x, bundle['categories'])
    return f[bundle['feature_names']]


def predict_proba_raw(bundle, raw_rows):
    return bundle['model'].predict_proba(build_features(raw_rows, bundle))


def known_locations(bundle):
    """location_description values seen when the model was built."""
    return set(bundle['categories']['location_description'])
