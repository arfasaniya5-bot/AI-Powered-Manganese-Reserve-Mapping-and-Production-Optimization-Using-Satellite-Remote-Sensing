"""
Manganese Detection - Model Training Pipeline (v2)
===================================================
Nationwide Indian Manganese Ore Classifier:
- Trained on `backend/data/manganese_estimation_dataset_live_v2.csv`
- Eliminates spatial memorization: raw coordinates (Latitude, Longitude) are excluded
  from decision features, forcing the model to learn physical spectral, terrain,
  and bare-ground thermal signatures that generalize across all of India.
- Eliminates target leakage: Distance_to_Manganese_km and metadata are excluded.
- Saves model v2 artifacts to `backend/models/`:
  * manganese_model_v2.pkl
  * manganese_preprocessor_v2.pkl
  * feature_columns_v2.json
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

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "manganese_estimation_dataset_live_v2.csv"
MODELS_DIR = BASE_DIR / "models"
MODEL_V2_PATH = MODELS_DIR / "manganese_model_v2.pkl"
PREPROCESSOR_V2_PATH = MODELS_DIR / "manganese_preprocessor_v2.pkl"
CONFIG_V2_PATH = MODELS_DIR / "feature_columns_v2.json"


def train_v2_model():
    print("=" * 80)
    print("MANGANESE ORE CLASSIFIER TRAINING PIPELINE (V2) - NATIONWIDE GENERALIZATION")
    print("=" * 80)

    # 1. Load Dataset v2
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset v2 not found at: {DATA_PATH}. Run build_dataset_v2.py first.")

    df = pd.read_csv(DATA_PATH)
    print(f"\n1. Loaded dataset from: {DATA_PATH}")
    print(f"   Shape: {df.shape[0]} rows, {df.shape[1]} columns")

    # 2. Quality Verification
    missing = df.isnull().sum()
    total_missing = missing.sum()
    print(f"\n2. Data Quality Check:")
    print(f"   Total missing values: {total_missing}")
    if total_missing > 0:
        print(missing[missing > 0])
        # Impute if any
        df = df.fillna(df.median(numeric_only=True))

    duplicates = df.duplicated(subset=["Latitude", "Longitude"]).sum()
    print(f"   Duplicate coordinate rows: {duplicates}")

    print("\n   Class Distribution (Manganese_Presence):")
    counts = df["Manganese_Presence"].value_counts()
    for label, count in counts.items():
        pct = (count / len(df)) * 100
        desc = "Positive (Ore Body)" if label == 1 else "Negative (Host Rock)"
        print(f"   - Class {label} ({desc}): {count} samples ({pct:.1f}%)")

    print("\n   State-wise Representation:")
    state_table = df.groupby(["State", "Manganese_Presence"]).size().unstack(fill_value=0)
    state_table.columns = ["Negative (Host)", "Positive (Ore)"]
    print(state_table)

    # 3. Feature Selection & Leakage Prevention
    # Section 9: Strictly exclude target leakage and metadata/identifiers
    # Exclude Latitude and Longitude to ensure nationwide generalization across India
    excluded_columns = [
        "Manganese_Presence",
        "Distance_to_Manganese_km",
        "Mine",
        "State",
        "Latitude",
        "Longitude",
        "Source_Citation",
        "Dataset_Version"
    ]

    feature_cols = [c for c in df.columns if c not in excluded_columns]
    X = df[feature_cols].copy()
    y = df["Manganese_Presence"].copy()

    print(f"\n3. Feature Selection:")
    print(f"   Excluded columns ({len(excluded_columns)}): {excluded_columns}")
    print(f"   Included ML features ({len(feature_cols)}): {feature_cols}")

    numerical_features = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_features = X.select_dtypes(include=["object"]).columns.tolist()

    print(f"   - Numerical features ({len(numerical_features)}): {numerical_features}")
    print(f"   - Categorical features ({len(categorical_features)}): {categorical_features}")

    # 4. Stratified Multi-State Train/Test Split (80/20)
    # Stratify by State + Class to ensure every state is equally represented in both splits
    strat_key = df["State"] + "_" + df["Manganese_Presence"].astype(str)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=strat_key
    )

    test_indices = X_test.index
    test_states = df.loc[test_indices, "State"]

    print(f"\n4. Dataset Split (80% Train, 20% Test):")
    print(f"   Train set: {X_train.shape[0]} samples (Class 1: {(y_train == 1).sum()}, Class 0: {(y_train == 0).sum()})")
    print(f"   Test set:  {X_test.shape[0]} samples (Class 1: {(y_test == 1).sum()}, Class 0: {(y_test == 0).sum()})")

    # 5. Fit Preprocessing Pipeline ONLY on Training Split
    print("\n5. Fitting ColumnTransformer on Training Split...")
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

    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    print(f"   Preprocessed training matrix: {X_train_proc.shape}")
    print(f"   Preprocessed testing matrix:  {X_test_proc.shape}")

    # 6. Train Random Forest Classifier
    print("\n6. Training Random Forest Classifier (n_estimators=100, random_state=42)...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
        max_depth=12,
        min_samples_leaf=3,
        max_features="sqrt",
        n_jobs=-1
    )
    rf_model.fit(X_train_proc, y_train)
    print("   Random Forest training complete.")

    # 7. Model Evaluation (Section 18 Metrics)
    y_pred = rf_model.predict(X_test_proc)
    y_prob = rf_model.predict_proba(X_test_proc)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print("\n" + "=" * 50)
    print("V2 MODEL TEST PERFORMANCE (SECTION 18 EVALUATION)")
    print("=" * 50)
    print(f"Accuracy : {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Precision: {prec:.4f} ({prec * 100:.2f}%)")
    print(f"Recall   : {rec:.4f} ({rec * 100:.2f}%)")
    print(f"F1-Score : {f1:.4f} ({f1 * 100:.2f}%)")
    print(f"ROC-AUC  : {auc:.4f}")

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"   [[TN={cm[0, 0]:4d},  FP={cm[0, 1]:4d}],")
    print(f"    [FN={cm[1, 0]:4d},  TP={cm[1, 1]:4d}]]")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Host Rock (0)", "Ore Body (1)"]))

    # 8. State-wise Performance Breakdown on Test Split
    print("=" * 50)
    print("STATE-WISE TEST SET GENERALIZATION BREAKDOWN")
    print("=" * 50)
    state_results = []
    for state in sorted(test_states.unique()):
        mask = (test_states == state).values
        s_y_true = y_test.values[mask]
        s_y_pred = y_pred[mask]
        s_y_prob = y_prob[mask]
        s_acc = accuracy_score(s_y_true, s_y_pred)
        s_f1 = f1_score(s_y_true, s_y_pred, zero_division=0)
        s_auc = roc_auc_score(s_y_true, s_y_prob) if len(np.unique(s_y_true)) > 1 else 1.0
        state_results.append({
            "State": state,
            "Samples": len(s_y_true),
            "Accuracy": f"{s_acc * 100:.1f}%",
            "F1-Score": f"{s_f1:.4f}",
            "ROC-AUC": f"{s_auc:.4f}"
        })
    print(pd.DataFrame(state_results).to_string(index=False))

    # 9. Feature Importances (Top 15 Physical Drivers)
    cat_encoder = preprocessor.named_transformers_["categorical"]
    cat_names = cat_encoder.get_feature_names_out(categorical_features).tolist() if hasattr(cat_encoder, "get_feature_names_out") else []
    all_feature_names = numerical_features + cat_names

    importances = rf_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    print("\n" + "=" * 50)
    print("TOP 15 PHYSICAL FEATURE IMPORTANCES (V2)")
    print("=" * 50)
    for rank, idx in enumerate(sorted_idx[:15], 1):
        feat_name = all_feature_names[idx] if idx < len(all_feature_names) else f"feature_{idx}"
        print(f"{rank:2d}. {feat_name:25s}: {importances[idx] * 100:6.2f}%")

    # 10. Save Artifacts (v2 versions, keeping original untouched)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf_model, MODEL_V2_PATH)
    joblib.dump(preprocessor, PREPROCESSOR_V2_PATH)

    config = {
        "model_version": "v2",
        "description": "Indian Manganese Ore Random Forest Classifier (Nationwide)",
        "excluded_features": excluded_columns,
        "input_features": feature_cols,
        "numerical_features": numerical_features,
        "categorical_features": categorical_features,
        "preprocessed_features": all_feature_names,
        "metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(auc), 4),
            "confusion_matrix": cm.tolist()
        }
    }
    with open(CONFIG_V2_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\nArtifacts successfully saved:")
    print(f" - Model:        {MODEL_V2_PATH}")
    print(f" - Preprocessor: {PREPROCESSOR_V2_PATH}")
    print(f" - Config:       {CONFIG_V2_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    train_v2_model()
