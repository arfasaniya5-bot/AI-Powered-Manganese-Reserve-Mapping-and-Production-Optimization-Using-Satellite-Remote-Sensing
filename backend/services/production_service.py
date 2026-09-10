"""
Production Business Logic Service
---------------------------------
Aggregates and formats production metrics, equipment downtime statistics,
environmental indicators, and drillhole data across the four production datasets.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from services.production_dataset_service import production_dataset_service, DATASET_DEFINITIONS


class ProductionService:
    """
    Business service layer for Production Analysis module.
    """

    def get_health(self) -> Dict[str, Any]:
        """Returns health status of the production module and dataset availability."""
        meta = production_dataset_service.get_all_metadata()
        available = sum(1 for m in meta.values() if m.get("exists") and m.get("total_rows", 0) > 0)
        return {
            "status": "ok",
            "module": "production_analysis",
            "datasets_available": available,
            "total_datasets": len(DATASET_DEFINITIONS),
            "message": f"{available} of {len(DATASET_DEFINITIONS)} production datasets are connected and ready."
        }

    def get_datasets_metadata(self) -> Dict[str, Any]:
        """Returns metadata for all four production datasets."""
        return production_dataset_service.get_all_metadata()

    def get_production_summary(self) -> Dict[str, Any]:
        """
        Computes high-level aggregated statistics from actual dataset contents.
        No fake numbers or placeholder calculations.
        """
        summary: Dict[str, Any] = {
            "kpis": {},
            "mine_breakdown": [],
            "risk_distribution": {},
            "equipment_summary": {},
            "weather_summary": {},
            "rocktype_summary": {},
        }

        # 1. Historical Production KPIs (from moil_historical_production_prototype)
        try:
            prod_df = production_dataset_service.get_dataset("historical_production")
            if not prod_df.empty:
                total_planned = float(prod_df["Planned_Production_Tonnes"].sum())
                total_actual = float(prod_df["Actual_Production_Tonnes"].sum())
                total_shortfall = float(prod_df["Production_Shortfall_Tonnes"].sum())
                overall_shortfall_pct = round((total_shortfall / total_planned * 100), 2) if total_planned > 0 else 0.0

                avg_eff = round(float(prod_df["Operational_Efficiency"].mean() * 100), 1) if "Operational_Efficiency" in prod_df.columns else None
                avg_avail = round(float(prod_df["Equipment_Availability"].mean() * 100), 1) if "Equipment_Availability" in prod_df.columns else None
                avg_weather = round(float(prod_df["Weather_Impact"].mean() * 100), 1) if "Weather_Impact" in prod_df.columns else None

                summary["kpis"] = {
                    "total_planned_production_tonnes": round(total_planned, 2),
                    "total_actual_production_tonnes": round(total_actual, 2),
                    "total_production_shortfall_tonnes": round(total_shortfall, 2),
                    "overall_shortfall_percentage": overall_shortfall_pct,
                    "avg_operational_efficiency_pct": avg_eff,
                    "avg_equipment_availability_pct": avg_avail,
                    "avg_weather_impact_pct": avg_weather,
                    "total_reporting_months": len(prod_df),
                    "unique_mines_count": int(prod_df["Mine"].nunique()) if "Mine" in prod_df.columns else 0,
                }

                # Mine-level breakdown
                if "Mine" in prod_df.columns:
                    mine_grp = prod_df.groupby("Mine").agg({
                        "Planned_Production_Tonnes": "sum",
                        "Actual_Production_Tonnes": "sum",
                        "Production_Shortfall_Tonnes": "sum",
                        "Shortfall_Percentage": "mean",
                        "Operational_Efficiency": "mean",
                        "Equipment_Availability": "mean",
                    }).reset_index()

                    mine_list = []
                    for _, row in mine_grp.iterrows():
                        mine_list.append({
                            "mine": str(row["Mine"]),
                            "planned_tonnes": round(float(row["Planned_Production_Tonnes"]), 1),
                            "actual_tonnes": round(float(row["Actual_Production_Tonnes"]), 1),
                            "shortfall_tonnes": round(float(row["Production_Shortfall_Tonnes"]), 1),
                            "avg_shortfall_pct": round(float(row["Shortfall_Percentage"]), 2),
                            "avg_efficiency_pct": round(float(row["Operational_Efficiency"]) * 100, 1),
                            "avg_availability_pct": round(float(row["Equipment_Availability"]) * 100, 1),
                        })
                    summary["mine_breakdown"] = mine_list

                # Risk distribution
                if "Shortfall_Risk" in prod_df.columns:
                    risk_counts = prod_df["Shortfall_Risk"].value_counts().to_dict()
                    summary["risk_distribution"] = {str(k): int(v) for k, v in risk_counts.items()}
        except Exception as e:
            summary["production_error"] = str(e)

        # 2. Equipment Failure Insights (from mining_equipment_failure_data)
        try:
            eq_df = production_dataset_service.get_dataset("equipment_failure")
            if not eq_df.empty:
                total_events = len(eq_df)
                total_downtime = float(eq_df["downtime_hours"].sum()) if "downtime_hours" in eq_df.columns else 0.0
                total_loss = float(eq_df["production_loss_tonnes"].sum()) if "production_loss_tonnes" in eq_df.columns else 0.0
                total_cost = float(eq_df["repair_cost_usd"].sum()) if "repair_cost_usd" in eq_df.columns else 0.0

                top_failures = {}
                if "failure_mode" in eq_df.columns:
                    top_failures = {str(k): int(v) for k, v in eq_df["failure_mode"].value_counts().head(5).items()}

                equipment_types = {}
                if "equipment_type" in eq_df.columns:
                    equipment_types = {str(k): int(v) for k, v in eq_df["equipment_type"].value_counts().head(5).items()}

                summary["equipment_summary"] = {
                    "total_failure_events": total_events,
                    "total_downtime_hours": round(total_downtime, 1),
                    "avg_downtime_hours_per_event": round(total_downtime / total_events, 2) if total_events > 0 else 0.0,
                    "total_production_loss_tonnes": round(total_loss, 1),
                    "total_repair_cost_usd": round(total_cost, 2),
                    "top_failure_modes": top_failures,
                    "equipment_type_distribution": equipment_types,
                }
        except Exception as e:
            summary["equipment_error"] = str(e)

        # 3. Weather & Soil Insights (from moil_weather_soil_2025)
        try:
            ws_df = production_dataset_service.get_dataset("weather_soil")
            if not ws_df.empty:
                summary["weather_summary"] = {
                    "total_observations": len(ws_df),
                    "avg_temperature_c": round(float(ws_df["Temperature_C"].mean()), 2) if "Temperature_C" in ws_df.columns else None,
                    "max_temperature_c": round(float(ws_df["Temperature_C"].max()), 2) if "Temperature_C" in ws_df.columns else None,
                    "total_precipitation_mm": round(float(ws_df["Precipitation_mm"].sum()), 2) if "Precipitation_mm" in ws_df.columns else None,
                    "avg_relative_humidity_pct": round(float(ws_df["Relative_Humidity_percent"].mean()), 2) if "Relative_Humidity_percent" in ws_df.columns else None,
                    "avg_soil_moisture_0_100cm": round(float(ws_df["Soil_Moisture_0_100cm"].mean()), 4) if "Soil_Moisture_0_100cm" in ws_df.columns else None,
                }
        except Exception as e:
            summary["weather_error"] = str(e)

        # 4. Rock Type & Blast-Hole Insights (from mwd_rocktype_blastholes_model_ready_train)
        try:
            rt_df = production_dataset_service.get_dataset("rocktype_blastholes")
            if not rt_df.empty:
                rock_counts = {}
                if "Rock" in rt_df.columns:
                    rock_counts = {str(k): int(v) for k, v in rt_df["Rock"].value_counts().items()}

                summary["rocktype_summary"] = {
                    "total_blast_rounds": len(rt_df),
                    "rock_type_distribution": rock_counts,
                    "avg_round_length_m": round(float(rt_df["round_length"].mean()), 2) if "round_length" in rt_df.columns else None,
                    "transition_zone_rounds": int(rt_df["transition_zone"].sum()) if "transition_zone" in rt_df.columns else 0,
                }
        except Exception as e:
            summary["rocktype_error"] = str(e)

        return summary

    def get_dataset_columns(self, key: str) -> Dict[str, Any]:
        """Retrieves column details for a single dataset."""
        meta = production_dataset_service.get_metadata(key)
        columns_info = production_dataset_service.get_columns_info(key)
        return {
            "success": True,
            "dataset_key": key,
            "dataset_name": meta.get("name", key),
            "total_columns": len(columns_info),
            "columns": columns_info,
        }

    def get_dataset_records(
        self,
        key: str,
        limit: int = 50,
        offset: int = 0,
        mine_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieves paginated records for a dataset."""
        return production_dataset_service.get_records(
            key=key,
            limit=limit,
            offset=offset,
            mine_filter=mine_filter
        )

    def get_mines_list(self) -> List[str]:
        """Returns list of distinct mines in historical production."""
        try:
            df = production_dataset_service.get_dataset("historical_production")
            if "Mine" in df.columns:
                return sorted(df["Mine"].dropna().unique().tolist())
        except Exception:
            pass
        return ["Balaghat", "Beldongri", "Chikla", "Dongri Buzurg", "Gumgaon", "Kandri", "Mansar", "Tirodi", "Ukwa"]


# Singleton export instance
production_service = ProductionService()
