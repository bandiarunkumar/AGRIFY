"""
Train Fertilizer Prediction Model
Dataset: fertilizer_recommendation.csv (Kaggle - real data)
Model: Random Forest Classifier
"""

import os
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder

from config import (
    FERTILIZER_DATA_FILE, MODEL_DIR,
    FERTILIZER_MODEL_FILE, FERTILIZER_ENCODER_FILE
)


def train():
    # ==========================================
    # 1. LOAD DATASET
    # ==========================================
    print("=" * 60)
    print("TRAINING FERTILIZER PREDICTION MODEL")
    print("=" * 60)

    if not os.path.exists(FERTILIZER_DATA_FILE):
        print(f"Dataset not found: {FERTILIZER_DATA_FILE}")
        return

    df = pd.read_csv(FERTILIZER_DATA_FILE)
    print(f"\nDataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")

    # ==========================================
    # 2. CLEAN AND RENAME COLUMNS
    # ==========================================
    df.columns = df.columns.str.strip()

    # Use exact column names from YOUR dataset
    col_map = {
        'Soil_Type': 'soil_type',
        'Soil_pH': 'soil_ph',
        'Soil_Moisture': 'soil_moisture',
        'Organic_Carbon': 'organic_carbon',
        'Electrical_Conductivity': 'electrical_conductivity',
        'Nitrogen_Level': 'N',
        'Phosphorus_Level': 'P',
        'Potassium_Level': 'K',
        'Temperature': 'temperature',
        'Humidity': 'humidity',
        'Rainfall': 'rainfall',
        'Crop_Type': 'crop_type',
        'Crop_Growth_Stage': 'growth_stage',
        'Season': 'season',
        'Irrigation_Type': 'irrigation',
        'Previous_Crop': 'previous_crop',
        'Region': 'region',
        'Fertilizer_Used_Last_Season': 'fertilizer_usage',
        'Yield_Last_Season': 'yield_last',
        'Recommended_Fertilizer': 'fertilizer'
    }
    df.rename(columns=col_map, inplace=True)
    print(f"\nRenamed columns: {list(df.columns)}")

    # ==========================================
    # 3. EXPLORE DATA
    # ==========================================
    print(f"\nFertilizers found: {df['fertilizer'].nunique()} types")
    print(f"  {sorted(df['fertilizer'].unique())}")
    print(f"\nSoil types: {sorted(df['soil_type'].unique())}")
    print(f"Crop types: {sorted(df['crop_type'].unique())}")

    print(f"\nSamples per fertilizer:")
    print(df['fertilizer'].value_counts())

    # ==========================================
    # 4. DROP MISSING VALUES
    # ==========================================
    before = len(df)
    df.dropna(inplace=True)
    after = len(df)
    if before != after:
        print(f"\nDropped {before - after} rows with missing values")

    # ==========================================
    # 5. ENCODE ALL CATEGORICAL COLUMNS
    # ==========================================
    encoders = {}

    categorical_cols = [
        'soil_type', 'crop_type', 'growth_stage',
        'season', 'irrigation', 'previous_crop',
        'region', 'fertilizer_usage', 'fertilizer'
    ]

    for col in categorical_cols:
        enc = LabelEncoder()
        df[col + '_enc'] = enc.fit_transform(df[col].astype(str))
        encoders[col] = enc
        print(f"Encoded {col}: {len(enc.classes_)} categories")

    # ==========================================
    # 6. PREPARE FEATURES
    # ==========================================
    feature_columns = [
        'soil_type_enc', 'soil_ph', 'soil_moisture', 'organic_carbon',
        'electrical_conductivity', 'N', 'P', 'K',
        'temperature', 'humidity', 'rainfall',
        'crop_type_enc', 'growth_stage_enc', 'season_enc',
        'irrigation_enc', 'previous_crop_enc', 'region_enc',
        'fertilizer_usage_enc', 'yield_last'
    ]

    X = df[feature_columns].values
    y = df['fertilizer_enc'].values

    print(f"\nFeatures used: {len(feature_columns)}")
    print(f"Features shape: {X.shape}")
    print(f"Labels: {len(encoders['fertilizer'].classes_)} classes")

    # ==========================================
    # 7. SPLIT DATA
    # ==========================================
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nTrain: {X_train.shape[0]} samples")
    print(f"Test:  {X_test.shape[0]} samples")

    # ==========================================
    # 8. TRAIN MODEL
    # ==========================================
    print(f"\nTraining Random Forest...")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=25,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    print(f"Model trained!")

    # ==========================================
    # 9. EVALUATE
    # ==========================================
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'=' * 60}")
    print(f"MODEL ACCURACY: {accuracy * 100:.2f}%")
    print(f"{'=' * 60}")
    print(f"\nClassification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=encoders['fertilizer'].classes_
    ))

    # ==========================================
    # 10. FEATURE IMPORTANCE
    # ==========================================
    importances = model.feature_importances_
    print(f"\nFeature Importance:")
    for feat, imp in sorted(zip(feature_columns, importances), key=lambda x: -x[1]):
        bar = "#" * int(imp * 50)
        print(f"   {feat:25s} {imp:.4f} {bar}")

    # ==========================================
    # 11. SAVE EVERYTHING
    # ==========================================
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Save encoders + feature list together
    encoders['feature_columns'] = feature_columns

    pickle.dump(model, open(FERTILIZER_MODEL_FILE, "wb"))
    pickle.dump(encoders, open(FERTILIZER_ENCODER_FILE, "wb"))

    print(f"\nModel saved:    {FERTILIZER_MODEL_FILE}")
    print(f"Encoders saved: {FERTILIZER_ENCODER_FILE}")
    print(f"\nFERTILIZER MODEL TRAINING COMPLETE!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    train()