"""
Database Service Layer
----------------------
Handles persistence and retrieval of Production Shortfall predictions
and Manganese Ore Potential predictions in MySQL.
"""

import json
from typing import Dict, Any, List, Optional
from config.database import db_manager


class DBService:
    """Database operations service for predictions and logs."""

    def save_production_prediction(self, pred: Dict[str, Any]) -> Optional[int]:
        """
        Saves a completed, valid production prediction into the database.
        Returns the inserted record ID, or None if save failed.
        """
        try:
            conn = db_manager.get_connection()
            query = """
                INSERT INTO `production_predictions` (
                    `mine`, `prediction_date`, `target_production`, `predicted_production`,
                    `shortfall`, `shortfall_percentage`, `model1_shortfall`, `model2_soil_moisture`,
                    `model3_rock`, `model4_equipment_loss`, `risk_score`, `risk_level`,
                    `temperature`, `wind_speed`, `humidity`, `precipitation`, `soil_moisture`,
                    `blasting_file_name`, `equipment_file_name`, `historical_data_json`,
                    `reasons_json`
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s
                );
            """
            hist_json = json.dumps(pred.get("historical_production") or pred.get("recent_history") or [])
            reasons_json = json.dumps(pred.get("reasons") or [])

            params = (
                str(pred.get("mine", "Unknown")),
                str(pred.get("date", "")),
                float(pred.get("target_production", 0.0)),
                float(pred.get("predicted_production", 0.0)),
                float(pred.get("shortfall", 0.0)),
                float(pred.get("shortfall_percentage", 0.0)),
                float(pred.get("production_shortfall_prediction") or 0.0),
                float(pred.get("soil_moisture_prediction") or 0.0),
                str(pred.get("rock_prediction") or ""),
                float(pred.get("equipment_production_loss") or 0.0),
                float(pred.get("final_risk_score") or 0.0),
                str(pred.get("risk_level", "LOW")),
                float(pred.get("temperature") or 0.0),
                float(pred.get("wind_speed") or 0.0),
                float(pred.get("humidity") or 0.0),
                float(pred.get("precipitation") or 0.0),
                float(pred.get("soil_moisture") or 0.0),
                str(pred.get("blasting_file_name") or pred.get("geological_file_name") or ""),
                str(pred.get("equipment_file_name") or ""),
                hist_json,
                reasons_json
            )

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                record_id = cursor.lastrowid
            conn.close()
            print(f"[DB] Saved production prediction #{record_id} for mine '{pred.get('mine')}' into MySQL.")
            return record_id
        except Exception as exc:
            print(f"[DB Error] Could not save production prediction: {exc}")
            return None

    def get_production_history(self, mine: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves past production prediction records from MySQL."""
        try:
            conn = db_manager.get_connection()
            if mine:
                query = "SELECT * FROM `production_predictions` WHERE LOWER(`mine`) = LOWER(%s) ORDER BY `id` DESC LIMIT %s;"
                params = (mine.strip(), limit)
            else:
                query = "SELECT * FROM `production_predictions` ORDER BY `id` DESC LIMIT %s;"
                params = (limit,)

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            conn.close()

            # Parse JSON fields
            for r in rows:
                if r.get("historical_data_json"):
                    try:
                        r["historical_production"] = json.loads(r["historical_data_json"])
                    except Exception:
                        r["historical_production"] = []
                if r.get("reasons_json"):
                    try:
                        r["reasons"] = json.loads(r["reasons_json"])
                    except Exception:
                        r["reasons"] = []
            return rows
        except Exception as exc:
            print(f"[DB Error] Could not fetch production history: {exc}")
            return []

    def save_manganese_prediction(
        self,
        latitude: float,
        longitude: float,
        predicted_class: int,
        probability: float,
        potential_category: str,
        features: Dict[str, Any]
    ) -> Optional[int]:
        """
        Saves a completed Manganese Ore / Deposit prediction into MySQL.
        """
        try:
            conn = db_manager.get_connection()
            query = """
                INSERT INTO `manganese_predictions` (
                    `latitude`, `longitude`, `predicted_class`, `probability`,
                    `potential_category`, `blue_b02`, `green_b03`, `red_b04`,
                    `nir_b08`, `swir1_b11`, `swir2_b12`, `ndvi`,
                    `lithology`, `glim_id`, `elevation_mean_m`, `slope_mean_degrees`,
                    `lst_mean_c`, `features_json`
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s
                );
            """
            params = (
                float(latitude),
                float(longitude),
                int(predicted_class),
                float(probability),
                str(potential_category),
                float(features.get("Blue_B02") or 0.0),
                float(features.get("Green_B03") or 0.0),
                float(features.get("Red_B04") or 0.0),
                float(features.get("NIR_B08") or 0.0),
                float(features.get("SWIR1_B11") or 0.0),
                float(features.get("SWIR2_B12") or 0.0),
                float(features.get("NDVI") or 0.0),
                str(features.get("Lithology") or ""),
                str(features.get("GLiM_ID") or ""),
                float(features.get("Elevation_mean_m") or 0.0),
                float(features.get("Slope_mean_degrees") or 0.0),
                float(features.get("LST_mean_C") or 0.0),
                json.dumps(features)
            )

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                record_id = cursor.lastrowid
            conn.close()
            print(f"[DB] Saved Manganese Ore prediction #{record_id} at ({latitude}, {longitude}) into MySQL.")
            return record_id
        except Exception as exc:
            print(f"[DB Error] Could not save manganese prediction: {exc}")
            return None

    def get_manganese_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves past Manganese Ore prediction records from MySQL."""
        try:
            conn = db_manager.get_connection()
            query = "SELECT * FROM `manganese_predictions` ORDER BY `id` DESC LIMIT %s;"
            with conn.cursor() as cursor:
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
            conn.close()

            for r in rows:
                if r.get("features_json"):
                    try:
                        r["features"] = json.loads(r["features_json"])
                    except Exception:
                        r["features"] = {}
            return rows
        except Exception as exc:
            print(f"[DB Error] Could not fetch manganese history: {exc}")
            return []

    def save_recommendation(self, rec: Dict[str, Any], prediction_id: Optional[int] = None) -> Optional[int]:
        """
        Persists a completed Production Shortfall recommendation into MySQL.
        """
        try:
            conn = db_manager.get_connection()
            query = """
                INSERT INTO `production_recommendations` (
                    `prediction_id`, `mine`, `recommendation_date`, `target_production`,
                    `predicted_production`, `shortfall_tonnes`, `shortfall_percentage`,
                    `status`, `possible_reasons_json`, `recommended_actions_json`, `cards_json`
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            reasons_json = json.dumps(rec.get("possible_reasons") or [])
            actions_json = json.dumps(rec.get("recommended_actions") or [])
            cards_json = json.dumps(rec.get("cards") or [])

            params = (
                prediction_id,
                str(rec.get("mine") or "Balaghat"),
                str(rec.get("date") or ""),
                float(rec.get("target_production") or 0.0),
                float(rec.get("predicted_production") or 0.0),
                float(rec.get("shortfall_tonnes") or 0.0),
                float(rec.get("shortfall_percentage") or 0.0),
                str(rec.get("status") or "LOW RISK"),
                reasons_json,
                actions_json,
                cards_json
            )

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rec_id = cursor.lastrowid
            conn.close()
            print(f"[DB] Saved production recommendation #{rec_id} for mine '{rec.get('mine')}' in MySQL.")
            return rec_id
        except Exception as exc:
            print(f"[DB Error] Could not save recommendation: {exc}")
            return None

    def get_latest_recommendation(self, mine: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent production recommendation from MySQL.
        """
        try:
            conn = db_manager.get_connection()
            if mine:
                query = "SELECT * FROM `production_recommendations` WHERE LOWER(`mine`) = LOWER(%s) ORDER BY `id` DESC LIMIT 1;"
                params = (mine.strip(),)
            else:
                query = "SELECT * FROM `production_recommendations` ORDER BY `id` DESC LIMIT 1;"
                params = ()

            with conn.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            if row.get("possible_reasons_json"):
                try:
                    row["possible_reasons"] = json.loads(row["possible_reasons_json"])
                except Exception:
                    row["possible_reasons"] = []
            else:
                row["possible_reasons"] = []

            if row.get("recommended_actions_json"):
                try:
                    row["recommended_actions"] = json.loads(row["recommended_actions_json"])
                except Exception:
                    row["recommended_actions"] = []
            else:
                row["recommended_actions"] = []

            if row.get("cards_json"):
                try:
                    row["cards"] = json.loads(row["cards_json"])
                except Exception:
                    row["cards"] = []
            else:
                row["cards"] = []

            return row
        except Exception as exc:
            print(f"[DB Error] Could not retrieve latest recommendation: {exc}")
            return None


db_service = DBService()
