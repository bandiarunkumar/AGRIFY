"""
Agri-Connect — Retrain Models Script
Run this when pickle models are incompatible with new numpy/sklearn
Usage: python retrain_models.py
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 60)
print("  Agri-Connect — Model Retraining")
print("=" * 60)

# ============================================================
# CROP MODEL
# ============================================================
crop_file = os.path.join(DATA_DIR, 'Crop_recommendation.csv')
if os.path.exists(crop_file):
    print(f"\n[1/2] Training CROP model from: {crop_file}")
    df = pd.read_csv(crop_file)
    print(f"  Dataset: {len(df)} rows, columns: {list(df.columns)}")

    feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    available_cols = [c for c in feature_cols if c in df.columns]
    X = df[available_cols].values.astype(np.float32)
    y = df['label'].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"  Accuracy: {acc * 100:.1f}%")
    print(f"  Crops: {list(le.classes_)}")

    joblib.dump(model, os.path.join(MODEL_DIR, 'crop_model.pkl'))
    joblib.dump(le, os.path.join(MODEL_DIR, 'crop_encoder.pkl'))
    print(f"  Saved crop_model.pkl + crop_encoder.pkl")
else:
    print(f"\n[1/2] SKIP: {crop_file} not found")

# ============================================================
# FERTILIZER MODEL
# ============================================================
fert_file = os.path.join(DATA_DIR, 'fertilizer_recommendation.csv')
if os.path.exists(fert_file):
    print(f"\n[2/2] Training FERTILIZER model from: {fert_file}")
    df2 = pd.read_csv(fert_file)
    print(f"  Dataset: {len(df2)} rows, columns: {list(df2.columns)}")

    # Find target column
    target_col = None
    for candidate in ['Fertilizer Name', 'Fertilizer', 'fertilizer', 'label']:
        if candidate in df2.columns:
            target_col = candidate
            break
    if not target_col:
        target_col = df2.columns[-1]
    print(f"  Target column: {target_col}")

    # Encode target
    le_fert = LabelEncoder()
    y2 = le_fert.fit_transform(df2[target_col].astype(str))

    # Work on feature columns only
    df3 = df2.drop(columns=[target_col]).copy()

    # Encode ALL object dtype columns
    encoders = {}
    for col in list(df3.columns):
        if df3[col].dtype == object:
            le_col = LabelEncoder()
            df3[col] = le_col.fit_transform(df3[col].astype(str))
            encoders[col] = le_col
            print(f"  Encoded '{col}': {list(le_col.classes_)[:5]}")

    # Ensure all numeric
    df3 = df3.apply(pd.to_numeric, errors='coerce').fillna(0)
    feature_cols2 = list(df3.columns)
    X2 = df3.values.astype(np.float32)

    X_train2, X_test2, y_train2, y_test2 = train_test_split(X2, y2, test_size=0.2, random_state=42)

    model2 = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    model2.fit(X_train2, y_train2)

    acc2 = accuracy_score(y_test2, model2.predict(X_test2))
    print(f"  Accuracy: {acc2 * 100:.1f}%")
    print(f"  Fertilizers: {list(le_fert.classes_)}")
    print(f"  Feature columns: {feature_cols2}")

    joblib.dump(model2, os.path.join(MODEL_DIR, 'fertilizer_model.pkl'))
    joblib.dump(le_fert, os.path.join(MODEL_DIR, 'fertilizer_encoder.pkl'))
    joblib.dump(feature_cols2, os.path.join(MODEL_DIR, 'fertilizer_feature_cols.pkl'))

    if encoders:
        soil_key = next((k for k in encoders if 'soil' in k.lower()), None)
        crop_key = next((k for k in encoders if 'crop' in k.lower()), None)
        soil_enc = encoders.get(soil_key, list(encoders.values())[0])
        crop_enc = encoders.get(crop_key, list(encoders.values())[-1])
        joblib.dump(soil_enc, os.path.join(MODEL_DIR, 'soil_encoder.pkl'))
        joblib.dump(crop_enc, os.path.join(MODEL_DIR, 'crop_type_encoder.pkl'))
        joblib.dump(encoders, os.path.join(MODEL_DIR, 'all_encoders.pkl'))

    print(f"  Saved fertilizer_model.pkl + fertilizer_encoder.pkl")
else:
    print(f"\n[2/2] SKIP: {fert_file} not found")

print(f"\n{'=' * 60}")
print("  Retraining Complete! Restart api.py")
print("=" * 60)
