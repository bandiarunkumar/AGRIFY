"""
Train Crop Recommendation Model
Dataset: Crop_recommendation.csv (Kaggle - real data)
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

from config import CROP_DATA_FILE, MODEL_DIR, CROP_MODEL_FILE, CROP_ENCODER_FILE


def train():
    # ==========================================
    # 1. LOAD DATASET
    # ==========================================
    print("=" * 60)
    print("TRAINING CROP RECOMMENDATION MODEL")
    print("=" * 60)

    if not os.path.exists(CROP_DATA_FILE):
        print(f"Dataset not found: {CROP_DATA_FILE}")
        print("Place Crop_recommendation.csv in backend/data/")
        return

    df = pd.read_csv(CROP_DATA_FILE)
    print(f"\nDataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
    print(f"Crops found: {df['label'].nunique()} types")
    print(f"  {sorted(df['label'].unique())}")

    # ==========================================
    # 2. CHECK FOR PROBLEMS
    # ==========================================
    print(f"\nMissing values:\n{df.isnull().sum()}")
    print(f"\nSamples per crop:")
    print(df['label'].value_counts())

    # ==========================================
    # 3. PREPARE DATA
    # ==========================================
    feature_columns = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    X = df[feature_columns].values
    y = df['label'].values

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    print(f"\nFeatures shape: {X.shape}")
    print(f"Labels encoded: {len(label_encoder.classes_)} classes")

    # ==========================================
    # 4. SPLIT DATA (80% train, 20% test)
    # ==========================================
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    print(f"\nTrain: {X_train.shape[0]} samples")
    print(f"Test:  {X_test.shape[0]} samples")

    # ==========================================
    # 5. TRAIN MODEL
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
    # 6. EVALUATE
    # ==========================================
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'=' * 60}")
    print(f"MODEL ACCURACY: {accuracy * 100:.2f}%")
    print(f"{'=' * 60}")
    print(f"\nClassification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_
    ))

    # ==========================================
    # 7. FEATURE IMPORTANCE
    # ==========================================
    importances = model.feature_importances_
    print(f"\nFeature Importance:")
    for feat, imp in sorted(zip(feature_columns, importances), key=lambda x: -x[1]):
        bar = "#" * int(imp * 50)
        print(f"   {feat:15s} {imp:.4f} {bar}")

    # ==========================================
    # 8. SAVE MODEL
    # ==========================================
    os.makedirs(MODEL_DIR, exist_ok=True)

    pickle.dump(model, open(CROP_MODEL_FILE, "wb"))
    pickle.dump(label_encoder, open(CROP_ENCODER_FILE, "wb"))

    print(f"\nModel saved to:   {CROP_MODEL_FILE}")
    print(f"Encoder saved to: {CROP_ENCODER_FILE}")
    print(f"\nCROP MODEL TRAINING COMPLETE!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    train()