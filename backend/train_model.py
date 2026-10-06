import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

def train_and_save_model():
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'clean', 'chicago_crime_clean.csv')
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw', 'chicago_crime_raw.csv')
    
    print(f"Loading dataset from: {data_path}")
    df = pd.read_csv(data_path, nrows=150000)
    print(f"Loaded {len(df):,} records for model training.")

    # 1. Feature Engineering matching Databricks pipeline
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'primary_type']).copy()

    df['hour'] = df['date'].dt.hour
    df['month'] = df['date'].dt.month
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['domestic'] = df['domestic'].astype(int)
    
    # Coordinates & administrative bounds
    median_lat = df['latitude'].dropna().median() if 'latitude' in df else 41.865
    median_lon = df['longitude'].dropna().median() if 'longitude' in df else -87.661
    df['latitude'] = df['latitude'].fillna(median_lat).astype(float)
    df['longitude'] = df['longitude'].fillna(median_lon).astype(float)
    df['community_area'] = df['community_area'].fillna(0).astype(int)
    df['district'] = df['district'].fillna(0).astype(int)
    df['ward'] = df['ward'].fillna(0).astype(int)
    df['beat'] = df['beat'].fillna(0).astype(int)

    # Clean categorical location description
    df['location_description'] = df['location_description'].fillna('OTHER').astype(str).str.strip().str.upper()

    # Filter top crime categories for reliable multiclass predictions
    top_crimes = df['primary_type'].value_counts().head(15).index.tolist()
    df = df[df['primary_type'].isin(top_crimes)].copy()

    features = [
        'hour', 'month', 'day_of_week', 'is_weekend', 'domestic',
        'community_area', 'district', 'ward', 'beat', 'latitude', 'longitude',
        'location_description'
    ]
    target = 'primary_type'

    X = df[features]
    y = df[target]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    numeric_features = ['hour', 'month', 'day_of_week', 'is_weekend', 'domestic', 'community_area', 'district', 'ward', 'beat', 'latitude', 'longitude']
    categorical_features = ['location_description']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    print("Fitting preprocessing & Random Forest Classifier matching Databricks model pipeline...")
    clf = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            max_depth=18,
            min_samples_split=8,
            random_state=42,
            n_jobs=-1
        ))
    ])

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Model Training Complete! Test Accuracy: {acc * 100:.2f}%")

    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)

    model_file = os.path.join(models_dir, 'chicago_crime_model.joblib')
    encoder_file = os.path.join(models_dir, 'label_encoder.joblib')
    
    joblib.dump(clf, model_file, compress=3)
    joblib.dump(label_encoder, encoder_file)
    print(f"Saved compressed model to {model_file}")
    print(f"Saved label encoder to {encoder_file}")

if __name__ == '__main__':
    train_and_save_model()
