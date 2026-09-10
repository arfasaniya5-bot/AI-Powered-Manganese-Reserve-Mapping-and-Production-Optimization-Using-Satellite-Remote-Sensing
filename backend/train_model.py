"""
Manganese Detection - Model Training Pipeline
=============================================
This script executes the exact AIML preprocessing, feature engineering,
and Random Forest training pipeline specified by the teammate code.

It trains on `backend/data/manganese_estimation_dataset.csv` (read-only)
and saves the serialized model, preprocessor, and feature metadata into
`backend/models/` for low-latency inference in the ManganeseInsight backend.
"""

import os
import json
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

# Define directories
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "manganese_estimation_dataset.csv"
MODELS_DIR = BASE_DIR / "models"


def run_training():
    print("============================================================")
    print("MANGANESE DETECTION - DATA PREPROCESSING & MODEL TRAINING")
    print("============================================================")

    # 1. LOAD DATASET (STRICTLY READ-ONLY)
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print("\nDataset loaded successfully!")
    print("Dataset shape:", df.shape)

    # 2. UNDERSTAND THE DATASET
    print("\nColumn names:", list(df.columns))

    # 3. CHECK MISSING VALUES
    total_missing = df.isnull().sum().sum()
    print("Total missing values:", total_missing)

    # 4. REMOVE DUPLICATE ROWS
    dup_count = df.duplicated().sum()
    print("Duplicate rows:", dup_count)
    df = df.drop_duplicates()
    print("Shape after removing duplicates:", df.shape)

    # 5. CHECK TARGET VARIABLE
    print("\nManganese Presence distribution:")
    print(df["Manganese_Presence"].value_counts())
    print("\nManganese Presence percentage:")
    print(df["Manganese_Presence"].value_counts(normalize=True) * 100)

    # 6. REMOVE TARGET LEAKAGE AND IDENTIFIER
    # Distance_to_Manganese_km reveals information about target.
    # Mine is an identifier so the model does not memorize mine names.
    df_ml = df.drop(
        columns=[
            "Distance_to_Manganese_km",
            "Mine"
        ]
    )
    print("\nRemoved: Distance_to_Manganese_km, Mine")

    # 7. SEPARATE FEATURES (X) AND TARGET (y)
    X = df_ml.drop(columns=["Manganese_Presence"])
    y = df_ml["Manganese_Presence"]
    raw_feature_names = list(X.columns)

    print("\nFeatures (X) shape:", X.shape)
    print("Target (y) shape:", y.shape)

    # 8. FEATURE ENGINEERING (EXACT TEAMMATE RATIOS AND RANGES)
    print("\nApplying feature engineering formulas...")
    X["SWIR1_NIR_Ratio"] = (
        X["SWIR1_B11"] / (X["NIR_B08"] + 1e-10)
    )
    X["SWIR2_NIR_Ratio"] = (
        X["SWIR2_B12"] / (X["NIR_B08"] + 1e-10)
    )
    X["SWIR1_SWIR2_Ratio"] = (
        X["SWIR1_B11"] / (X["SWIR2_B12"] + 1e-10)
    )
    X["Red_SWIR1_Ratio"] = (
        X["Red_B04"] / (X["SWIR1_B11"] + 1e-10)
    )
    X["NIR_SWIR1_Ratio"] = (
        X["NIR_B08"] / (X["SWIR1_B11"] + 1e-10)
    )
    X["Elevation_range_m"] = (
        X["Elevation_max_m"] - X["Elevation_min_m"]
    )
    X["Slope_range_degrees"] = (
        X["Slope_max_degrees"] - X["Slope_min_degrees"]
    )
    X["LST_range_C"] = (
        X["LST_max_C"] - X["LST_min_C"]
    )
    print("Feature engineering completed!")

    # 9. IDENTIFY NUMERICAL AND CATEGORICAL FEATURES
    numerical_features = X.select_dtypes(
        include=["int64", "float64"]
    ).columns.tolist()

    categorical_features = X.select_dtypes(
        include=["object"]
    ).columns.tolist()

    print("\nNumerical features ({}):".format(len(numerical_features)), numerical_features)
    print("Categorical features ({}):".format(len(categorical_features)), categorical_features)

    # 10. SPLIT DATA INTO TRAINING AND TESTING (80/20 STRATIFIED)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )
    print("\nTraining data:", X_train.shape)
    print("Testing data:", X_test.shape)

    # 11. ENCODING + SCALING
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numerical",
                StandardScaler(),
                numerical_features
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                categorical_features
            )
        ]
    )

    # 12. FIT PREPROCESSING ONLY ON TRAINING DATA
    print("\nFitting ColumnTransformer on training features...")
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    print("Preprocessing completed!")
    print("Training features shape:", X_train_processed.shape)
    print("Testing features shape:", X_test_processed.shape)

    # 13. CREATE RANDOM FOREST MODEL (EXACT TEAMMATE PARAMETERS)
    rf_model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    # 14. TRAIN RANDOM FOREST
    print("\nTraining Random Forest model (n_estimators=100, random_state=42)...")
    rf_model.fit(X_train_processed, y_train)
    print("Random Forest training completed!")

    # 15. MAKE PREDICTIONS & EVALUATE PERFORMANCE
    y_pred_rf = rf_model.predict(X_test_processed)
    y_prob_rf = rf_model.predict_proba(X_test_processed)[:, 1]

    accuracy = accuracy_score(y_test, y_pred_rf)
    precision = precision_score(y_test, y_pred_rf)
    recall = recall_score(y_test, y_pred_rf)
    f1 = f1_score(y_test, y_pred_rf)
    auc = roc_auc_score(y_test, y_prob_rf)

    print("\n================================")
    print("RANDOM FOREST MODEL RESULTS")
    print("================================")
    print("Accuracy :", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall   :", round(recall, 4))
    print("F1-Score :", round(f1, 4))
    print("ROC-AUC  :", round(auc, 4))

    print("\n================================")
    print("CLASSIFICATION REPORT")
    print("================================")
    print(classification_report(y_test, y_pred_rf))

    print("\n================================")
    print("CONFUSION MATRIX")
    print("================================")
    print(confusion_matrix(y_test, y_pred_rf))

    # 16. SAVE TRAINED MODEL & PREPROCESSOR ARTIFACTS
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "manganese_model.pkl"
    preprocessor_path = MODELS_DIR / "manganese_preprocessor.pkl"
    config_path = MODELS_DIR / "feature_columns.json"

    print(f"\nSaving model artifact to: {model_path}")
    joblib.dump(rf_model, model_path)

    print(f"Saving preprocessor artifact to: {preprocessor_path}")
    joblib.dump(preprocessor, preprocessor_path)

    metadata = {
        "model_type": "RandomForestClassifier",
        "n_estimators": 100,
        "random_state": 42,
        "raw_features": raw_feature_names,
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "engineered_features": [
            "SWIR1_NIR_Ratio",
            "SWIR2_NIR_Ratio",
            "SWIR1_SWIR2_Ratio",
            "Red_SWIR1_Ratio",
            "NIR_SWIR1_Ratio",
            "Elevation_range_m",
            "Slope_range_degrees",
            "LST_range_C"
        ],
        "metrics": {
            "accuracy": round(float(accuracy), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "roc_auc": round(float(auc), 4)
        }
    }

    with open(config_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saving feature metadata to: {config_path}")

    print("\n================================")
    print("ALL MODEL ARTIFACTS SAVED SUCCESSFULLY!")
    print("================================")


if __name__ == "__main__":
    run_training()
