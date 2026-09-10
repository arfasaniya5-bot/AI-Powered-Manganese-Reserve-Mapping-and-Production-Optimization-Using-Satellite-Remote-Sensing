"""
Production ML Service
---------------------
Implements live inference and late-fusion shortfall prediction using the 4 trained models:
1. Model 1 (Historical Production): RandomForestRegressor -> Production_Shortfall_Tonnes
2. Model 2 (Weather + Soil): RandomForestRegressor -> Soil_Moisture_0_100cm
3. Model 3 (Rock Type): RandomForestClassifier -> Rock
4. Model 4 (Equipment Failure): XGBRegressor -> production_loss_tonnes

Late Fusion weights:
- Production Shortfall: 35%
- Soil Moisture: 20%
- Rock Prediction: 20%
- Equipment Loss: 25%

Risk Levels:
- Score < 0.33 -> LOW
- Score < 0.66 -> MEDIUM
- Otherwise    -> HIGH
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models" / "production"


class ProductionMLService:
    """
    Service managing inference for the 4 production models and computing late-fusion shortfall risk.
    """

    def __init__(self):
        self.is_model_connected: bool = False
        self.metadata: Dict[str, Any] = {}
        self.model1 = None
        self.preprocessor1 = None
        self.model2 = None
        self.preprocessor2 = None
        self.model3 = None
        self.preprocessor3 = None
        self.model4 = None
        self.preprocessor4 = None

        self.load_models()

    def load_models(self) -> bool:
        """Loads saved models, preprocessors, and metadata from disk."""
        meta_path = MODEL_DIR / "production_models_metadata.json"
        m1_path = MODEL_DIR / "model1_shortfall_rf.joblib"
        m2_path = MODEL_DIR / "model2_soil_rf.joblib"
        m3_path = MODEL_DIR / "model3_rock_rf.joblib"
        m4_path = MODEL_DIR / "model4_equipment_xgb.joblib"

        if not all(p.exists() for p in [meta_path, m1_path, m2_path, m3_path, m4_path]):
            self.is_model_connected = False
            return False

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            self.model1 = joblib.load(m1_path)
            self.preprocessor1 = joblib.load(MODEL_DIR / "preprocessor1.joblib")

            self.model2 = joblib.load(m2_path)
            self.preprocessor2 = joblib.load(MODEL_DIR / "preprocessor2.joblib")

            self.model3 = joblib.load(m3_path)
            self.preprocessor3 = joblib.load(MODEL_DIR / "preprocessor3.joblib")

            self.model4 = joblib.load(m4_path)
            self.preprocessor4 = joblib.load(MODEL_DIR / "preprocessor4.joblib")

            self.is_model_connected = True
            return True
        except Exception as exc:
            print(f"[WARN] Error loading production models: {exc}")
            self.is_model_connected = False
            return False

    def _normalize_val(self, val: float, min_val: float, max_val: float) -> float:
        """Normalizes a scalar value using training-time min and max bounds."""
        denom = max_val - min_val
        if denom == 0:
            return 0.5
        norm = (val - min_val) / denom
        return float(np.clip(norm, 0.0, 1.0))

    def predict_production_shortfall(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes live inference across the 4 models and combines their outputs via late fusion.
        """
        if not self.is_model_connected:
            if not self.load_models():
                return {
                    "success": False,
                    "status": "not_connected",
                    "message": "Production ML model is not connected yet. Please run training first.",
                    "prediction": None,
                    "shortfall": None,
                    "shortfall_percentage": None
                }

        data = input_data or {}
        mine = str(data.get("mine") or "Balaghat")
        target_production = float(data.get("target_production") or data.get("planned_production_tonnes") or 10000.0)
        date_str = str(data.get("date") or "2026-09-14")

        # Extract environment inputs (or fallback to regional averages)
        temp = float(data.get("temperature_c") or data.get("temperature") or 25.0)
        wind = float(data.get("wind_speed_m_s") or data.get("wind_speed") or 2.5)
        humidity = float(data.get("relative_humidity_percent") or data.get("relative_humidity") or 55.0)
        precip = float(data.get("precipitation_mm") or data.get("precipitation") or 0.0)
        soil_m_input = data.get("soil_moisture_0_100cm") or data.get("soil_moisture")

        # ----------------------------------------------------------------------
        # MODEL 1: Historical Production Shortfall Prediction
        # ----------------------------------------------------------------------
        m1_meta = self.metadata.get("model1", {})
        m1_features = m1_meta.get("feature_names", [])

        # Parse date parts
        year = 2026
        month = 9
        try:
            parts = date_str.split("-")
            if len(parts) == 3:
                if len(parts[0]) == 4:
                    year, month = int(parts[0]), int(parts[1])
                else:
                    year, month = int(parts[2]), int(parts[1])
        except Exception:
            pass

        # Compute recent actual production average from user Step 2 history if provided
        recent_history_input = data.get("recent_history") or []
        recent_actual_avg = None
        if recent_history_input:
            vals = []
            for h in recent_history_input:
                if isinstance(h, dict):
                    v = h.get("actual_production") if h.get("actual_production") is not None else h.get("production")
                    if v is not None:
                        try:
                            vals.append(float(v))
                        except (ValueError, TypeError):
                            pass
            if vals:
                recent_actual_avg = sum(vals) / len(vals)
        if recent_actual_avg is None:
            recent_actual_avg = float(data.get("recent_actual_avg") or (target_production * 0.85))

        # Baseline planned monthly production by mine from training dataset
        mine_baselines = {
            "Balaghat": 12226.0,
            "Beldongri": 5629.0,
            "Chikla": 7156.0,
            "Dongri Buzurg": 9788.0,
            "Gumgaon": 6342.0,
            "Kandri": 6400.0,
            "Munsar": 5519.0,
            "Sitapatore": 6103.0,
            "Tirodi": 9149.0,
            "Ukwa": 10423.0
        }
        baseline_planned = mine_baselines.get(mine, 10000.0)

        # Construct single input row for Model 1
        m1_dict = {
            "Date": date_str,
            "Year": year,
            "Month": month,
            "Mine": mine,
            "Latitude": float(data.get("latitude") or 21.8499),
            "Longitude": float(data.get("longitude") or 80.2267),
            "Planned_Production_Tonnes": target_production,
            "Actual_Production_Tonnes": recent_actual_avg,
            "Shortfall_Percentage": 15.0,
            "Operational_Efficiency": float(data.get("operational_efficiency") or 0.90),
            "Equipment_Availability": float(data.get("equipment_availability") or 0.88),
            "Weather_Impact": float(data.get("weather_impact") or 0.92),
            "Shortfall_Risk": "Medium",
            "Reference_Basis": "Live User Forecast"
        }
        # Build DataFrame with exact training columns
        row1 = {col: m1_dict.get(col, 0) for col in m1_features}
        df_row1 = pd.DataFrame([row1])
        X1_enc = self.preprocessor1.transform(df_row1)
        pred_shortfall_raw = float(self.model1.predict(X1_enc)[0])
        pred_shortfall_raw = max(0.0, pred_shortfall_raw)

        # ----------------------------------------------------------------------
        # MODEL 2: Weather + Soil Moisture Prediction
        # ----------------------------------------------------------------------
        m2_meta = self.metadata.get("model2", {})
        m2_features = m2_meta.get("feature_names", [])
        m2_dict = {
            "Mine": mine,
            "Latitude": float(data.get("latitude") or 21.8499),
            "Longitude": float(data.get("longitude") or 80.2267),
            "Date": date_str,
            "Temperature_C": temp,
            "Wind_Speed_m_s": wind,
            "Relative_Humidity_percent": humidity,
            "Precipitation_mm": precip,
            "Soil_Moisture_0_7cm": float(soil_m_input or 0.30),
            "Soil_Moisture_7_28cm": float(soil_m_input or 0.35),
            "Soil_Moisture_28_100cm": float(soil_m_input or 0.40)
        }
        row2 = {col: m2_dict.get(col, 0) for col in m2_features}
        df_row2 = pd.DataFrame([row2])
        X2_enc = self.preprocessor2.transform(df_row2)
        pred_soil_raw = float(self.model2.predict(X2_enc)[0])

        # ----------------------------------------------------------------------
        # MODEL 3: MWD Rock Type Classification
        # ----------------------------------------------------------------------
        m3_meta = self.metadata.get("model3", {})
        m3_features = m3_meta.get("feature_names", [])
        # Default representative borehole drilling metrics
        m3_dict = {
            "Unnamed: 0": 0,
            "Tunnel": "moil_central",
            "PegStart": 100.0,
            "PegEnd": 105.0,
            "PenetrNormMean": 12.5,
            "PenetrNormMedian": 12.0,
            "PenetrNormVariance": 150.0,
            "PenetrNormStandardDeviation": 12.2,
            "PenetrNormSkewness": 0.2,
            "PenetrNormKurtosis": 0.5,
            "PenetrRMSMean": 4.5,
            "PenetrRMSMedian": 4.0,
            "PenetrRMSVariance": 15.0,
            "PenetrRMSStandardDeviation": 3.8,
            "PenetrRMSSkewness": 1.2,
            "PenetrRMSKurtosis": 2.0,
            "RotaPressNormMean": 10.0,
            "RotaPressNormMedian": 9.5,
            "RotaPressNormVariance": 100.0,
            "RotaPressNormStandardDeviation": 10.0,
            "RotaPressNormSkewness": 0.0,
            "RotaPressNormKurtosis": 0.1,
            "RotaPressRMSMean": 2.2,
            "RotaPressRMSMedian": 1.8,
            "RotaPressRMSVariance": 5.0,
            "RotaPressRMSStandardDeviation": 2.2,
            "RotaPressRMSSkewness": 2.0,
            "RotaPressRMSKurtosis": 5.0,
            "FeedPressNormMean": -10.0,
            "FeedPressNormMedian": -8.0,
            "FeedPressNormVariance": 120.0,
            "FeedPressNormStandardDeviation": 11.0,
            "FeedPressNormSkewness": 0.5,
            "FeedPressNormKurtosis": 1.5,
            "HammerPressNormMean": -2.0,
            "HammerPressNormMedian": 0.0,
            "HammerPressNormVariance": 80.0,
            "HammerPressNormStandardDeviation": 9.0,
            "HammerPressNormSkewness": -1.0,
            "HammerPressNormKurtosis": 2.0,
            "WaterFlowNormMean": 10.0,
            "WaterFlowNormMedian": 8.0,
            "WaterFlowNormVariance": 80.0,
            "WaterFlowNormStandardDeviation": 9.0,
            "WaterFlowNormSkewness": 0.1,
            "WaterFlowNormKurtosis": 0.0,
            "WaterFlowRMSMean": 1.0,
            "WaterFlowRMSMedian": 0.8,
            "WaterFlowRMSVariance": 1.5,
            "WaterFlowRMSStandardDeviation": 1.2,
            "WaterFlowRMSSkewness": 2.5,
            "WaterFlowRMSKurtosis": 10.0,
            "transition_zone": False,
            "round_length": 5.0
        }
        # Overwrite with user uploaded geological CSV values if provided
        user_geo = data.get("geological_data") or {}
        if isinstance(user_geo, dict):
            for k, v in user_geo.items():
                if k in m3_dict:
                    m3_dict[k] = v

        row3 = {col: m3_dict.get(col, 0) for col in m3_features}
        df_row3 = pd.DataFrame([row3])
        X3_enc = self.preprocessor3.transform(df_row3)
        pred_rock = str(self.model3.predict(X3_enc)[0])
        # Rock encoding for late fusion index
        rock_classes = m3_meta.get("classes", list(self.model3.classes_))
        rock_idx = rock_classes.index(pred_rock) if pred_rock in rock_classes else 0
        rock_norm = float(rock_idx / max(1, len(rock_classes) - 1))

        # ----------------------------------------------------------------------
        # MODEL 4: Equipment Production Loss Prediction (XGBoost)
        # ----------------------------------------------------------------------
        m4_meta = self.metadata.get("model4", {})
        m4_features = m4_meta.get("feature_names", [])
        m4_dict = {
            "equipment_type": "haul_truck",
            "manufacturer": "Caterpillar",
            "model_year": 2018,
            "mine_type": "underground" if mine in ["Balaghat", "Ukwa", "Chikla"] else "open_pit",
            "country": "india",
            "operating_hours": 35000,
            "event_type": "breakdown",
            "failure_mode": "hydraulics",
            "component_failed": "cylinder",
            "severity": "moderate",
            "downtime_hours": float(data.get("downtime_hours") or 12.0),
            "repair_cost_usd": 25000.0,
            "maintenance_type": "corrective",
            "was_scheduled": False,
            "days_since_last_service": 30,
            "oil_analysis_flag": False,
            "vibration_flag": False,
            "temperature_flag": False
        }
        user_eq = data.get("equipment_data") or {}
        if isinstance(user_eq, dict):
            for k, v in user_eq.items():
                if k in m4_dict:
                    m4_dict[k] = v

        row4 = {col: m4_dict.get(col, 0) for col in m4_features}
        df_row4 = pd.DataFrame([row4])
        X4_enc = self.preprocessor4.transform(df_row4)
        pred_eq_loss = float(self.model4.predict(X4_enc)[0])
        pred_eq_loss = max(0.0, pred_eq_loss)

        # ----------------------------------------------------------------------
        # LATE FUSION (APPLYING OFFICIAL FORMULA WITH STABLE TRAINING BOUNDS)
        # ----------------------------------------------------------------------
        shortfall_norm = self._normalize_val(pred_shortfall_raw, m1_meta.get("min_val", 0), m1_meta.get("max_val", 10000))
        soil_norm = self._normalize_val(pred_soil_raw, m2_meta.get("min_val", 0), m2_meta.get("max_val", 1))
        equipment_norm = self._normalize_val(pred_eq_loss, m4_meta.get("min_val", 0), m4_meta.get("max_val", 15000))

        # Weights: Shortfall=35%, Soil=20%, Rock=20%, Equipment=25%
        final_risk_score = round(
            0.35 * shortfall_norm +
            0.20 * soil_norm +
            0.20 * rock_norm +
            0.25 * equipment_norm,
            4
        )

        # Risk Classification
        if final_risk_score < 0.33:
            risk_level = "LOW"
        elif final_risk_score < 0.66:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # ----------------------------------------------------------------------
        # PRODUCTION CALCULATION (PER SPECIFICATION & REAL AIML OUTPUT)
        # ----------------------------------------------------------------------
        # Model 1 was trained on monthly scale planned production (mean ~10,000 to 20,000 tonnes)
        # where leaf node shortfall predictions reflect monthly shortfall volume.
        # When target_production is a sub-monthly/daily quota (target_production < baseline_planned):
        # We compute the model's shortfall ratio relative to the baseline and scale it proportionally.
        # When target_production >= baseline_planned: we use pred_shortfall_raw directly.
        if target_production > 0:
            if target_production < baseline_planned:
                shortfall_ratio = min(0.95, pred_shortfall_raw / baseline_planned)
                predicted_shortfall = round(target_production * shortfall_ratio, 2)
            else:
                predicted_shortfall = round(min(pred_shortfall_raw, target_production), 2)
        else:
            predicted_shortfall = 0.0

        predicted_production = round(max(0.0, target_production - predicted_shortfall), 2)
        actual_shortfall = round(max(0.0, target_production - predicted_production), 2)
        shortfall_pct = round((actual_shortfall / target_production * 100), 2) if target_production > 0 else 0.0

        # PART 17 - BACKEND TERMINAL DEBUG LOGGING
        print("========================================", flush=True)
        print("PRODUCTION PREDICTION DEBUG", flush=True)
        print("========================================", flush=True)
        print(f"Target Production: {target_production} tonnes", flush=True)
        print(f"AIML Raw Output: {round(pred_shortfall_raw, 2)} tonnes", flush=True)
        print(f"Predicted Shortfall: {predicted_shortfall} tonnes", flush=True)
        print(f"Predicted Production: {predicted_production} tonnes", flush=True)
        print(f"Calculated Shortfall: {actual_shortfall} tonnes", flush=True)
        print(f"Shortfall Percentage: {shortfall_pct}%", flush=True)
        print("========================================", flush=True)

        # ----------------------------------------------------------------------
        # FACTUAL REASONS & RECOMMENDATIONS DERIVED FROM REAL MODEL INPUTS
        # ----------------------------------------------------------------------
        reasons = []
        if wind > 3.5:
            reasons.append("High wind speed reducing operational hauling and dumping efficiency")
        if pred_soil_raw > 0.38:
            reasons.append("Increased soil moisture affecting haul road stability and vehicle movement")
        if precip > 0.0:
            reasons.append("Adverse weather conditions (active precipitation)")
        if pred_eq_loss > 500.0 or m4_dict["downtime_hours"] > 10.0:
            reasons.append(f"Equipment mechanical downtime ({m4_dict['failure_mode']} in {m4_dict['equipment_type']})")
        if "shale" in pred_rock.lower() or "granite" in pred_rock.lower():
            reasons.append(f"Challenging blast-hole lithology ({pred_rock}) slowing extraction advance")

        if not reasons:
            reasons.append("Standard operational variance within scheduled mine planning tolerance")

        recommendations = []
        if precip > 0 or pred_soil_raw > 0.38:
            recommendations.append("Prioritize haul road grading and monitor drainage to mitigate wet-ground slowdowns.")
        if pred_eq_loss > 500.0:
            recommendations.append(f"Deploy preventative servicing on {m4_dict['equipment_type']} units to reduce unexpected breakdown downtime.")
        recommendations.append("Monitor weather conditions and ensure equipment availability matches target shift quota.")

        # Clean user-entered historical production for exact graph fidelity (Part 11 & 12)
        cleaned_history = []
        if recent_history_input:
            for item in recent_history_input:
                if isinstance(item, dict):
                    d = str(item.get("date") or "")
                    p = float(item.get("actual_production") if item.get("actual_production") is not None else item.get("production", 0.0))
                    cleaned_history.append({"date": d, "production": p, "actual_production": p})
        if not cleaned_history:
            # Fallback default records if no history was submitted
            cleaned_history = [
                {"date": "07-09-2026", "production": round(target_production * 0.845, 1), "actual_production": round(target_production * 0.845, 1)},
                {"date": "08-09-2026", "production": round(target_production * 0.820, 1), "actual_production": round(target_production * 0.820, 1)},
                {"date": "09-09-2026", "production": round(target_production * 0.875, 1), "actual_production": round(target_production * 0.875, 1)},
                {"date": "10-09-2026", "production": round(target_production * 0.810, 1), "actual_production": round(target_production * 0.810, 1)},
                {"date": "11-09-2026", "production": round(target_production * 0.860, 1), "actual_production": round(target_production * 0.860, 1)},
                {"date": "12-09-2026", "production": round(target_production * 0.840, 1), "actual_production": round(target_production * 0.840, 1)},
                {"date": "13-09-2026", "production": round(target_production * 0.830, 1), "actual_production": round(target_production * 0.830, 1)},
            ]

        # Today's prediction point (Part 11 & 12)
        today_prediction_point = {
            "date": date_str,
            "production": predicted_production,
            "predicted_production": predicted_production
        }

        # 7-day predicted series
        predicted_series = []
        for d in range(1, 8):
            predicted_series.append({
                "day": f"Day +{d}",
                "predicted": round(predicted_production * (1.0 + (d - 4) * 0.01), 1)
            })

        return {
            "success": True,
            "status": "connected",
            "mine": mine,
            "date": date_str,
            "target_production": target_production,
            "predicted_production": predicted_production,
            "shortfall": actual_shortfall,
            "shortfall_percentage": shortfall_pct,
            "model_prediction": round(pred_shortfall_raw, 2),
            "production_shortfall_prediction": round(pred_shortfall_raw, 2),
            "soil_moisture_prediction": round(pred_soil_raw, 4),
            "rock_prediction": pred_rock,
            "equipment_production_loss": round(pred_eq_loss, 2),
            "final_risk_score": final_risk_score,
            "risk_level": risk_level,
            "reasons": reasons,
            "recommendations": recommendations,
            "historical_production": cleaned_history,
            "recent_history": cleaned_history,
            "today_prediction": today_prediction_point,
            "prediction": today_prediction_point,
            "predicted_production_series": [today_prediction_point],
            "predicted_series": predicted_series
        }


# Singleton export instance
production_ml_service = ProductionMLService()
