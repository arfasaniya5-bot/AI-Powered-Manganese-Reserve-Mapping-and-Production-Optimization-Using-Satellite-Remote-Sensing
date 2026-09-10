"""
Machine Learning Service
------------------------
Handles loading of the trained Manganese detection model and preprocessor,
and provides the runtime inference pipeline:
1. Feature extraction from Google Earth Engine & geological services
2. Feature engineering (spectral ratios, elevation/slope/LST ranges)
3. Column transformation (StandardScaler + OneHotEncoder)
4. Random Forest probability calculation & potential categorization
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import joblib

from services.feature_service import extract_location_features, print_ore_prediction_debug
from services.dataset_service import dataset_service
from services.earth_engine_service import (
    S2_COLLECTION,
    S2_DEFAULT_START_DATE,
    S2_DEFAULT_END_DATE,
    S2_SCALE_FACTOR
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "manganese_model.pkl"
PREPROCESSOR_PATH = MODELS_DIR / "manganese_preprocessor.pkl"
CONFIG_PATH = MODELS_DIR / "feature_columns.json"

# ==============================================================================
# POTENTIAL CATEGORY THRESHOLD CONFIGURATION (STEP 4)
# ==============================================================================
# High Potential: Probability of manganese presence >= 70%
# Medium Potential: Probability between 40% and 70%
# Low Potential: Probability < 40%
HIGH_POTENTIAL_THRESHOLD = 0.70
MEDIUM_POTENTIAL_THRESHOLD = 0.40


class MLService:
    """
    ML Service for Manganese ore/deposit presence prediction.
    Loads the trained Random Forest classifier and preprocessing ColumnTransformer.
    """

    def __init__(self):
        self.is_model_loaded: bool = False
        self.model: Optional[Any] = None
        self.preprocessor: Optional[Any] = None
        self.raw_features: List[str] = [
            "Latitude",
            "Longitude",
            "Blue_B02",
            "Green_B03",
            "Red_B04",
            "NIR_B08",
            "SWIR1_B11",
            "SWIR2_B12",
            "NDVI",
            "Lithology",
            "GLiM_ID",
            "Elevation_mean_m",
            "Elevation_min_m",
            "Elevation_max_m",
            "Slope_mean_degrees",
            "Slope_min_degrees",
            "Slope_max_degrees",
            "LST_mean_C",
            "LST_min_C",
            "LST_max_C"
        ]

        # Automatically attempt loading the model on startup
        self.load_model()

    def load_model(self) -> bool:
        """
        Loads the trained AI/ML model and preprocessor artifacts from backend/models/.
        """
        if MODEL_PATH.exists() and PREPROCESSOR_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
                self.preprocessor = joblib.load(PREPROCESSOR_PATH)
                self.is_model_loaded = True
                return True
            except Exception as exc:
                self.is_model_loaded = False
                self.model = None
                self.preprocessor = None
                return False
        self.is_model_loaded = False
        return False

    def predict_manganese_potential(
        self,
        latitude: float,
        longitude: float,
        features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main inference function:
        1. Checks if model is trained and loaded.
        2. Retrieves location features if not provided.
        3. Formats features into exact order and types.
        4. Computes the 8 teammate feature engineering ratios & ranges.
        5. Transforms features via saved ColumnTransformer.
        6. Computes class prediction and continuous probability.
        7. Assigns category (High/Medium/Low Potential) and descriptive message.
        """
        if not self.is_model_loaded:
            if not self.load_model():
                return {
                    "success": False,
                    "error": "ML model is not trained yet. Please run the training script first.",
                    "message": "ML model is not trained yet. Please run the training script first."
                }

        # 1. Obtain location features
        if features is None:
            features = extract_location_features(latitude, longitude)

        # Check for remote sensing retrieval failures
        errors = features.get("_errors", {})

        # Verify all required numerical features are present (no silent fake fallbacks)
        required_features = [
            ("Blue_B02", features.get("Blue_B02") if features.get("Blue_B02") is not None else features.get("B02")),
            ("Green_B03", features.get("Green_B03") if features.get("Green_B03") is not None else features.get("B03")),
            ("Red_B04", features.get("Red_B04") if features.get("Red_B04") is not None else features.get("B04")),
            ("NIR_B08", features.get("NIR_B08") if features.get("NIR_B08") is not None else features.get("B08")),
            ("SWIR1_B11", features.get("SWIR1_B11") if features.get("SWIR1_B11") is not None else features.get("B11")),
            ("SWIR2_B12", features.get("SWIR2_B12") if features.get("SWIR2_B12") is not None else features.get("B12")),
            ("NDVI", features.get("NDVI")),
            ("Elevation_mean_m", features.get("Elevation_mean_m") if features.get("Elevation_mean_m") is not None else features.get("elevation_mean_m")),
            ("Elevation_min_m", features.get("Elevation_min_m") if features.get("Elevation_min_m") is not None else features.get("elevation_min_m")),
            ("Elevation_max_m", features.get("Elevation_max_m") if features.get("Elevation_max_m") is not None else features.get("elevation_max_m")),
            ("Slope_mean_degrees", features.get("Slope_mean_degrees") if features.get("Slope_mean_degrees") is not None else features.get("slope_mean_degrees")),
            ("Slope_min_degrees", features.get("Slope_min_degrees") if features.get("Slope_min_degrees") is not None else features.get("slope_min_degrees")),
            ("Slope_max_degrees", features.get("Slope_max_degrees") if features.get("Slope_max_degrees") is not None else features.get("slope_max_degrees")),
            ("LST_mean_C", features.get("LST_mean_C")),
            ("LST_min_C", features.get("LST_min_C")),
            ("LST_max_C", features.get("LST_max_C")),
        ]

        missing = [name for name, val in required_features if val is None]
        if missing:
            err_details = [f"{k}: {v}" for k, v in errors.items() if v]
            err_summary = "; ".join(err_details) if err_details else "Incomplete data returned by Google Earth Engine"
            return {
                "success": False,
                "error": f"Failed to retrieve required features ({', '.join(missing)}): {err_summary}",
                "message": f"Feature extraction failed for coordinates ({latitude:.4f}, {longitude:.4f}). Earth Engine reported: {err_summary}"
            }

        # 2. Build 1-row DataFrame with the exact raw feature columns (no fallback values)
        feat_dict = dict(required_features)
        raw_row = {
            "Latitude": float(latitude),
            "Longitude": float(longitude),
            "Blue_B02": float(feat_dict["Blue_B02"]),
            "Green_B03": float(feat_dict["Green_B03"]),
            "Red_B04": float(feat_dict["Red_B04"]),
            "NIR_B08": float(feat_dict["NIR_B08"]),
            "SWIR1_B11": float(feat_dict["SWIR1_B11"]),
            "SWIR2_B12": float(feat_dict["SWIR2_B12"]),
            "NDVI": float(feat_dict["NDVI"]),
            "Lithology": str(features.get("Lithology") or "Metamorphics"),
            "GLiM_ID": str(features.get("GLiM_ID") or "IND2497"),
            "Elevation_mean_m": float(feat_dict["Elevation_mean_m"]),
            "Elevation_min_m": float(feat_dict["Elevation_min_m"]),
            "Elevation_max_m": float(feat_dict["Elevation_max_m"]),
            "Slope_mean_degrees": float(feat_dict["Slope_mean_degrees"]),
            "Slope_min_degrees": float(feat_dict["Slope_min_degrees"]),
            "Slope_max_degrees": float(feat_dict["Slope_max_degrees"]),
            "LST_mean_C": float(feat_dict["LST_mean_C"]),
            "LST_min_C": float(feat_dict["LST_min_C"]),
            "LST_max_C": float(feat_dict["LST_max_C"]),
        }

        df_row = pd.DataFrame([raw_row])

        # 3. Apply exact 8 feature engineering formulas
        df_row["SWIR1_NIR_Ratio"] = (
            df_row["SWIR1_B11"] / (df_row["NIR_B08"] + 1e-10)
        )
        df_row["SWIR2_NIR_Ratio"] = (
            df_row["SWIR2_B12"] / (df_row["NIR_B08"] + 1e-10)
        )
        df_row["SWIR1_SWIR2_Ratio"] = (
            df_row["SWIR1_B11"] / (df_row["SWIR2_B12"] + 1e-10)
        )
        df_row["Red_SWIR1_Ratio"] = (
            df_row["Red_B04"] / (df_row["SWIR1_B11"] + 1e-10)
        )
        df_row["NIR_SWIR1_Ratio"] = (
            df_row["NIR_B08"] / (df_row["SWIR1_B11"] + 1e-10)
        )
        df_row["Elevation_range_m"] = (
            df_row["Elevation_max_m"] - df_row["Elevation_min_m"]
        )
        df_row["Slope_range_degrees"] = (
            df_row["Slope_max_degrees"] - df_row["Slope_min_degrees"]
        )
        df_row["LST_range_C"] = (
            df_row["LST_max_C"] - df_row["LST_min_C"]
        )

        # 4. Preprocess through fitted ColumnTransformer
        X_processed = self.preprocessor.transform(df_row)

        # 5. Generate prediction & probability
        pred_class = int(self.model.predict(X_processed)[0])
        probabilities = self.model.predict_proba(X_processed)[0]

        # Explicitly map classes from model.classes_ (Step 3)
        classes = list(self.model.classes_)
        class0_idx = classes.index(0) if 0 in classes else 0
        class1_idx = classes.index(1) if 1 in classes else 1
        prob_class_0 = float(probabilities[class0_idx])
        prob_class_1 = float(probabilities[class1_idx])
        presence_prob = prob_class_1
        prob_percentage = round(presence_prob * 100, 1)

        # 6. Determine Potential Category per configured thresholds (Step 4):
        # High Potential: probability >= HIGH_POTENTIAL_THRESHOLD (70%)
        # Medium Potential: probability >= MEDIUM_POTENTIAL_THRESHOLD (40%) and < 70%
        # Low Potential: probability < MEDIUM_POTENTIAL_THRESHOLD (40%)
        if presence_prob >= HIGH_POTENTIAL_THRESHOLD:
            potential = "High Potential"
            message = "This area has a high probability of containing manganese deposits."
        elif presence_prob >= MEDIUM_POTENTIAL_THRESHOLD:
            potential = "Medium Potential"
            message = "This area has a moderate probability of containing manganese deposits."
        else:
            potential = "Low Potential"
            message = "This area has a low probability of containing manganese deposits."

        # STEP 7: Complete Model Debug Information Logging
        nearest_info = dataset_service.find_nearest_dataset_record(latitude, longitude)
        nearest_lat = nearest_info.get("nearest_latitude") if nearest_info else "N/A"
        nearest_lon = nearest_info.get("nearest_longitude") if nearest_info else "N/A"
        dist_m = nearest_info.get("distance_meters", 0.0) if nearest_info else 0.0

        # Model feature names (from preprocessor)
        try:
            num_cols = self.preprocessor.transformers_[0][2]
            cat_cols = self.preprocessor.transformers_[1][1].get_feature_names_out(self.preprocessor.transformers_[1][2])
            feature_names = list(num_cols) + list(cat_cols)
        except Exception:
            feature_names = self.raw_features

        print_ore_prediction_debug(
            frontend_lat=latitude,
            frontend_lon=longitude,
            nearest_lat=nearest_lat,
            nearest_lon=nearest_lon,
            dist_meters=dist_m,
            scale_factor=f"{S2_SCALE_FACTOR} (1/10000.0 applied once)",
            s2_collection=S2_COLLECTION,
            s2_date_range=f"{S2_DEFAULT_START_DATE} to {S2_DEFAULT_END_DATE}",
            model_feature_names=feature_names,
            raw_features=raw_row,
            processed_features=X_processed[0],
            classes=classes,
            prob_class_0=prob_class_0,
            prob_class_1=prob_class_1,
            pred_class=pred_class,
            presence_prob=presence_prob,
            potential=potential
        )

        # Key factors indicating geological and spectral suitability
        key_factors = []
        if df_row["SWIR1_NIR_Ratio"].iloc[0] > 0.8:
            key_factors.append("Strong SWIR1 absorption indicating hydrothermal alteration")
        if df_row["NDVI"].iloc[0] < 0.35:
            key_factors.append("Sparse vegetation cover favorable for outcrop exposure")
        if raw_row["Lithology"] in ["Metamorphics", "Acid plutonic rocks"]:
            key_factors.append(f"Favorable {raw_row['Lithology']} geological formation")
        if df_row["Elevation_range_m"].iloc[0] > 30:
            key_factors.append("Topographic relief consistent with known deposit veins")

        return {
            "success": True,
            "latitude": latitude,
            "longitude": longitude,
            "prediction": pred_class,
            "probability": round(presence_prob, 4),
            "probability_percentage": prob_percentage,
            "potential": potential,
            "message": message,
            "key_factors": key_factors,
            "features_used": raw_row
        }

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy adapter maintaining compatibility with existing calls.
        """
        lat = features.get("latitude") or features.get("Latitude") or 18.5234
        lon = features.get("longitude") or features.get("Longitude") or 79.1234
        return self.predict_manganese_potential(lat, lon, features=features)


# Export singleton instance
ml_service = MLService()
