"""
Recommendation Engine - Case-Based Reasoning (CBR)
--------------------------------------------------
MOIL GeoMineAI: Case-Based Reasoning recommendation engine.
Retrieves and ranks similar prototype cases from the 898-case library
(`mining_recommendation_case_library.csv`), computes weighted Gower similarity,
tracks progressive intervention history, and provides full explainability.
"""

import math
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from config.recommendation_weights import (
    SIMILARITY_WEIGHTS,
    DEFAULT_TOP_K,
    MIN_SIMILARITY_THRESHOLD
)
from services.production_dataset_service import production_dataset_service
from services.db_service import db_service

PROTOTYPE_DISCLAIMER = (
    "PROTOTYPE RECOMMENDATION ENGINE: Recommendations are derived using Case-Based "
    "Reasoning across 898 historical prototype mining cases. Operational decisions "
    "should be validated by on-site mining engineers."
)


class RecommendationEngine:
    """
    Case-Based Reasoning (CBR) engine matching real-time mine constraints
    against the 898 historical prototype cases.
    """

    def __init__(self):
        self.disclaimer = PROTOTYPE_DISCLAIMER

    def get_case_library(self) -> pd.DataFrame:
        """Retrieves the 898 prototype cases through the dataset service."""
        cases = production_dataset_service.get_recommendation_cases()
        if cases is None or cases.empty:
            print("[RecommendationEngine Warning] Case library empty, attempting reload...")
            cases = production_dataset_service.get_dataset("recommendation_cases")
        return cases if cases is not None else pd.DataFrame()

    def build_situation_profile(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts and normalizes the situation profile from input parameters.
        Handles both single values and nested equipment / geological structures.
        """
        mine = str(input_data.get("mine") or "Balaghat").strip()
        date = str(input_data.get("date") or datetime.now().strftime("%Y-%m-%d"))

        target = float(input_data.get("target_production") or 10000.0)
        predicted = float(input_data.get("predicted_production") or (target * 0.85))
        shortfall = max(0.0, target - predicted)
        shortfall_pct = (shortfall / target * 100.0) if target > 0 else 0.0

        # Weather extraction
        temp = input_data.get("temperature")
        if temp is None:
            temp = input_data.get("temperature_c")
        temp = float(temp) if temp is not None else None

        wind = input_data.get("wind_speed")
        if wind is None:
            wind = input_data.get("wind_speed_m_s")
        wind = float(wind) if wind is not None else None

        precip = input_data.get("precipitation")
        if precip is None:
            precip = input_data.get("precipitation_mm")
        precip = float(precip) if precip is not None else None

        soil = input_data.get("soil_moisture")
        if soil is None:
            soil = input_data.get("soil_moisture_0_100cm")
        if soil is not None:
            soil = float(soil)
            # Normalize to 0-100 percentage if expressed as fraction (e.g. 0.41 -> 41.0)
            if soil <= 1.0 and soil > 0.0:
                soil_pct = soil * 100.0
            else:
                soil_pct = soil
        else:
            soil_pct = None

        humidity = input_data.get("humidity")
        if humidity is None:
            humidity = input_data.get("relative_humidity_percent")
        humidity = float(humidity) if humidity is not None else None

        # Equipment extraction
        eq_id = input_data.get("equipment_id")
        eq_type = input_data.get("equipment_type")
        failure_mode = input_data.get("failure_mode")
        component = input_data.get("component_failed")
        downtime = float(input_data.get("downtime_hours") or 0.0)
        maintenance_type = input_data.get("maintenance_type")
        failure_severity = input_data.get("severity") or input_data.get("failure_severity")
        was_scheduled = input_data.get("was_scheduled")

        # Check nested equipment data if top-level fields are absent
        eq_records = input_data.get("equipment_data")
        if isinstance(eq_records, list) and eq_records:
            first_eq = eq_records[0]
            eq_id = eq_id or first_eq.get("equipment_id") or first_eq.get("Equipment_ID")
            eq_type = eq_type or first_eq.get("equipment_type") or first_eq.get("Equipment_Type")
            component = component or first_eq.get("component_failed") or first_eq.get("Component_Failed")
            downtime = max(downtime, float(first_eq.get("downtime_hours") or first_eq.get("Downtime_Hours") or 0.0))
            failure_severity = failure_severity or first_eq.get("severity") or first_eq.get("Failure_Severity")
        elif isinstance(eq_records, dict) and eq_records:
            eq_id = eq_id or eq_records.get("equipment_id") or eq_records.get("Equipment_ID")
            eq_type = eq_type or eq_records.get("equipment_type") or eq_records.get("Equipment_Type")
            component = component or eq_records.get("component_failed") or eq_records.get("Component_Failed")
            downtime = max(downtime, float(eq_records.get("downtime_hours") or eq_records.get("Downtime_Hours") or 0.0))
            failure_severity = failure_severity or eq_records.get("severity") or eq_records.get("Failure_Severity")

        # Drilling / Geological extraction
        rock_type = input_data.get("rock_prediction") or input_data.get("rock_type") or input_data.get("rock")
        transition_zone = input_data.get("transition_zone")
        rot_variance = input_data.get("rotation_pressure_variance")

        geo_records = input_data.get("geological_data") or input_data.get("mwd_data")
        if isinstance(geo_records, list) and geo_records:
            first_geo = geo_records[0]
            rock_type = rock_type or first_geo.get("Rock") or first_geo.get("Rock_Type")
            if transition_zone is None:
                transition_zone = first_geo.get("transition_zone") or first_geo.get("Transition_Zone")
            if rot_variance is None:
                rot_variance = first_geo.get("Rotation_Pressure_Variance")
        elif isinstance(geo_records, dict) and geo_records:
            rock_type = rock_type or geo_records.get("Rock") or geo_records.get("Rock_Type")
            if transition_zone is None:
                transition_zone = geo_records.get("transition_zone") or geo_records.get("Transition_Zone")
            if rot_variance is None:
                rot_variance = geo_records.get("Rotation_Pressure_Variance")

        # Primary Cause Category Inference
        primary_cause = input_data.get("primary_cause_category")
        if not primary_cause:
            if precip and precip >= 15.0:
                primary_cause = "Weather"
            elif soil_pct and soil_pct >= 42.0:
                primary_cause = "Weather"
            elif downtime >= 4.0 or failure_severity in ["high", "critical", "severe"]:
                primary_cause = "Equipment"
            elif rock_type and str(rock_type).lower() in ["amphibolittic_gneiss", "hornfels", "augen_gneiss"]:
                primary_cause = "Geological/Drilling"
            elif shortfall_pct > 15.0:
                primary_cause = "Operational/Workforce"
            else:
                primary_cause = "Weather" if (precip and precip > 0) else "Operational/Workforce"

        return {
            "mine": mine,
            "date": date,
            "target_production": target,
            "predicted_production": predicted,
            "shortfall_tonnes": shortfall,
            "shortfall_percentage": shortfall_pct,
            "temperature_c": temp,
            "wind_speed_m_s": wind,
            "precipitation_mm": precip,
            "soil_moisture_pct": soil_pct,
            "humidity": humidity,
            "equipment_id": eq_id,
            "equipment_type": eq_type,
            "failure_mode": failure_mode,
            "component_failed": component,
            "downtime_hours": downtime,
            "maintenance_type": maintenance_type,
            "failure_severity": failure_severity,
            "was_scheduled": was_scheduled,
            "rock_type": rock_type,
            "transition_zone": transition_zone,
            "rotation_pressure_variance": float(rot_variance) if rot_variance is not None else None,
            "primary_cause_category": primary_cause
        }

    def compute_case_similarity(self, profile: Dict[str, Any], case: pd.Series) -> Tuple[float, Dict[str, float]]:
        """
        Calculates normalized weighted similarity between current situation profile
        and a historical case row across all active dimensions.
        """
        category_scores: Dict[str, float] = {}
        active_weights: Dict[str, float] = {}

        # 1. Problem / Cause Match (Weight: 0.20)
        c_cause = str(case.get("Primary_Cause_Category") or "").strip().lower()
        p_cause = str(profile.get("primary_cause_category") or "").strip().lower()
        if c_cause and p_cause:
            if c_cause == p_cause:
                cause_score = 1.0
            elif (c_cause in p_cause) or (p_cause in c_cause):
                cause_score = 0.8
            else:
                cause_score = 0.25
        else:
            cause_score = 0.6
        category_scores["problem_cause"] = cause_score
        active_weights["problem_cause"] = SIMILARITY_WEIGHTS["problem_cause"]

        # 2. Production Similarity (Weight: 0.20)
        c_shortfall_pct = float(case.get("Shortfall_Percentage") or 0.0)
        p_shortfall_pct = float(profile["shortfall_percentage"])
        shortfall_sim = max(0.0, 1.0 - abs(p_shortfall_pct - c_shortfall_pct) / 50.0)

        c_planned = float(case.get("Planned_Production_Tonnes") or 15000.0)
        p_target = float(profile["target_production"])
        planned_sim = max(0.0, 1.0 - abs(p_target - c_planned) / 35000.0)

        c_actual = float(case.get("Actual_Production_Tonnes") or 12000.0)
        p_actual = float(profile["predicted_production"])
        actual_sim = max(0.0, 1.0 - abs(p_actual - c_actual) / 30000.0)

        prod_score = (0.50 * shortfall_sim) + (0.25 * planned_sim) + (0.25 * actual_sim)
        category_scores["production"] = prod_score
        active_weights["production"] = SIMILARITY_WEIGHTS["production"]

        # 3. Weather Similarity (Weight: 0.12)
        weather_scores = []
        if profile.get("temperature_c") is not None:
            c_temp = float(case.get("Temperature_C") or 25.0)
            weather_scores.append(max(0.0, 1.0 - abs(profile["temperature_c"] - c_temp) / 20.0))

        if profile.get("precipitation_mm") is not None:
            c_precip = float(case.get("Precipitation_mm") or 0.0)
            weather_scores.append(max(0.0, 1.0 - abs(profile["precipitation_mm"] - c_precip) / 40.0))

        if profile.get("wind_speed_m_s") is not None:
            c_wind = float(case.get("Wind_Speed_m_s") or 2.5)
            weather_scores.append(max(0.0, 1.0 - abs(profile["wind_speed_m_s"] - c_wind) / 5.0))

        if profile.get("soil_moisture_pct") is not None:
            c_soil = float(case.get("Soil_Moisture_0_100cm_pct") or 35.0)
            weather_scores.append(max(0.0, 1.0 - abs(profile["soil_moisture_pct"] - c_soil) / 30.0))

        if weather_scores:
            category_scores["weather"] = sum(weather_scores) / len(weather_scores)
            active_weights["weather"] = SIMILARITY_WEIGHTS["weather"]

        # 4. Equipment & Component (Weight: 0.20)
        eq_scores = []
        has_eq_info = False

        if profile.get("equipment_type"):
            has_eq_info = True
            c_eq = str(case.get("Equipment_Type") or "").lower()
            p_eq = str(profile["equipment_type"]).lower()
            eq_scores.append(1.0 if c_eq == p_eq else 0.2)

        if profile.get("component_failed"):
            has_eq_info = True
            c_comp = str(case.get("Component_Failed") or "").lower()
            p_comp = str(profile["component_failed"]).lower()
            eq_scores.append(1.0 if c_comp == p_comp else 0.1)

        if profile.get("failure_mode"):
            has_eq_info = True
            c_mode = str(case.get("Failure_Mode") or "").lower()
            p_mode = str(profile["failure_mode"]).lower()
            eq_scores.append(1.0 if c_mode == p_mode else 0.2)

        if has_eq_info and eq_scores:
            category_scores["equipment_component"] = sum(eq_scores) / len(eq_scores)
            active_weights["equipment_component"] = SIMILARITY_WEIGHTS["equipment_component"]

        # 5. Drilling & Geology (Weight: 0.12)
        geo_scores = []
        has_geo_info = False

        if profile.get("rock_type"):
            has_geo_info = True
            c_rock = str(case.get("Rock_Type") or "").lower()
            p_rock = str(profile["rock_type"]).lower()
            geo_scores.append(1.0 if c_rock == p_rock else 0.3)

        if profile.get("transition_zone") is not None:
            has_geo_info = True
            c_tz = bool(case.get("Transition_Zone"))
            p_tz = bool(profile["transition_zone"])
            geo_scores.append(1.0 if c_tz == p_tz else 0.5)

        if profile.get("rotation_pressure_variance") is not None:
            has_geo_info = True
            c_var = float(case.get("Rotation_Pressure_Variance") or 500.0)
            p_var = float(profile["rotation_pressure_variance"])
            geo_scores.append(max(0.0, 1.0 - abs(p_var - c_var) / 1200.0))

        if has_geo_info and geo_scores:
            category_scores["drilling_geology"] = sum(geo_scores) / len(geo_scores)
            active_weights["drilling_geology"] = SIMILARITY_WEIGHTS["drilling_geology"]

        # 6. Mine Context (Weight: 0.08)
        c_mine = str(case.get("Mine") or "").strip().lower()
        p_mine = str(profile.get("mine") or "").strip().lower()
        mine_score = 1.0 if c_mine == p_mine else 0.55
        category_scores["mine_context"] = mine_score
        active_weights["mine_context"] = SIMILARITY_WEIGHTS["mine_context"]

        # 7. Downtime & Severity (Weight: 0.08)
        p_dt = float(profile.get("downtime_hours") or 0.0)
        c_dt = float(case.get("Downtime_Hours") or 0.0)
        if p_dt > 0 or profile.get("failure_severity"):
            dt_sim = max(0.0, 1.0 - abs(p_dt - c_dt) / 40.0)
            p_sev = str(profile.get("failure_severity") or "").lower()
            c_sev = str(case.get("Failure_Severity") or "").lower()
            sev_sim = 1.0 if (p_sev and c_sev and p_sev == c_sev) else 0.4
            dt_score = (0.6 * dt_sim) + (0.4 * sev_sim)
        else:
            # Baseline baseline if no downtime reported
            dt_score = 0.95 if c_dt <= 3.0 else 0.45
        category_scores["downtime_severity"] = dt_score
        active_weights["downtime_severity"] = SIMILARITY_WEIGHTS["downtime_severity"]

        # Compute dynamic renormalized weighted score
        total_weight = sum(active_weights.values())
        if total_weight > 0:
            final_similarity = sum(active_weights[k] * category_scores[k] for k in active_weights) / total_weight
        else:
            final_similarity = 0.0

        return round(float(final_similarity), 4), category_scores

    def retrieve_top_k_cases(
        self,
        profile: Dict[str, Any],
        k: int = DEFAULT_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Scores all 898 cases in the case library and retrieves the top K cases.
        """
        df = self.get_case_library()
        if df.empty:
            return []

        scored_cases = []
        for idx, row in df.iterrows():
            sim_score, cat_scores = self.compute_case_similarity(profile, row)
            scored_cases.append({
                "case_id": str(row.get("Case_ID") or f"CASE-{idx:04d}"),
                "case_sequence": int(row.get("Case_Sequence") or idx + 1),
                "mine": str(row.get("Mine") or "Balaghat"),
                "date": str(row.get("Date") or ""),
                "planned_tonnes": float(row.get("Planned_Production_Tonnes") or 0.0),
                "actual_tonnes": float(row.get("Actual_Production_Tonnes") or 0.0),
                "shortfall_pct": float(row.get("Shortfall_Percentage") or 0.0),
                "primary_cause": str(row.get("Primary_Cause_Category") or "Operational"),
                "problem_identified": str(row.get("Problem_Identified") or ""),
                "action_taken": str(row.get("Action_Taken") or ""),
                "action_outcome": str(row.get("Action_Outcome") or "Reduced"),
                "action_status": str(row.get("Action_Status") or "In Progress"),
                "follow_up_action": str(row.get("Follow_Up_Action") or ""),
                "equipment_id": str(row.get("Equipment_ID") or ""),
                "equipment_type": str(row.get("Equipment_Type") or ""),
                "component_failed": str(row.get("Component_Failed") or ""),
                "downtime_hours": float(row.get("Downtime_Hours") or 0.0),
                "weather_basis": str(row.get("Weather_Data_Basis") or "Proxy"),
                "equipment_basis": str(row.get("Equipment_Data_Basis") or "Proxy"),
                "rock_basis": str(row.get("Rock_Data_Basis") or "Proxy"),
                "similarity_score": sim_score,
                "similarity_pct": round(sim_score * 100.0, 1),
                "category_scores": cat_scores
            })

        # Rank descending by similarity score
        scored_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_cases[:k]

    def rank_candidate_actions(
        self,
        profile: Dict[str, Any],
        top_cases: List[Dict[str, Any]],
        prior_history: List[Dict[str, Any]],
        max_actions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Extracts, ranks, and adjusts candidate actions using historical effectiveness
        and progressive escalation checks from MySQL.
        Evaluates top matching cases to find distinct actions.
        """
        if not top_cases:
            return []

        # Map previously failed / escalated actions from DB history
        prior_failed_actions = set()
        for hist in prior_history:
            act_text = str(hist.get("recommended_action") or "").strip().lower()
            if act_text:
                status = str(hist.get("action_status") or "").upper()
                outcome = str(hist.get("outcome") or "").upper()
                if status == "ESCALATED" or outcome in ["FAILED", "FAIL"]:
                    prior_failed_actions.add(act_text)

        action_candidates = []
        seen_actions = set()

        # Step 1: Collect unique actions from top cases
        for case in top_cases:
            action_taken = case["action_taken"].strip()
            follow_up = case["follow_up_action"].strip()
            sim = case["similarity_score"]
            outcome = case["action_outcome"]

            # Outcome weighting multiplier
            if outcome in ["Resolved", "Successful"]:
                outcome_mult = 1.25
            elif outcome in ["Reduced", "In Progress"]:
                outcome_mult = 1.0
            else:
                outcome_mult = 0.65

            action_key = action_taken.lower()

            # Progressive Escalation Check:
            # If this action was already attempted and failed or escalated in MySQL history,
            # switch directly to the case's Follow_Up_Action!
            is_escalation = False
            effective_action = action_taken
            if any(failed in action_key for failed in prior_failed_actions) and follow_up:
                effective_action = f"Escalated Action: {follow_up}"
                is_escalation = True
                outcome_mult = 1.35

            if effective_action.lower() not in seen_actions and len(effective_action) > 5:
                seen_actions.add(effective_action.lower())
                combined_rank_score = sim * outcome_mult
                action_candidates.append({
                    "action": effective_action,
                    "case_id": case["case_id"],
                    "primary_cause": case["primary_cause"],
                    "similarity_score": sim,
                    "similarity_pct": case["similarity_pct"],
                    "outcome": outcome,
                    "status": "Escalated" if is_escalation else case["action_status"],
                    "is_escalation": is_escalation,
                    "follow_up_action": follow_up,
                    "problem_identified": case["problem_identified"],
                    "rank_score": round(combined_rank_score, 4),
                    "equipment_id": case["equipment_id"]
                })

        # Step 2: If fewer than max_actions, include follow-up actions from top cases
        if len(action_candidates) < max_actions:
            for case in top_cases:
                follow_up = case["follow_up_action"].strip()
                if follow_up and follow_up.lower() not in seen_actions and len(follow_up) > 5:
                    seen_actions.add(follow_up.lower())
                    action_candidates.append({
                        "action": f"Contingency / Follow-Up: {follow_up}",
                        "case_id": case["case_id"],
                        "primary_cause": case["primary_cause"],
                        "similarity_score": case["similarity_score"] * 0.95,
                        "similarity_pct": round(case["similarity_pct"] * 0.95, 1),
                        "outcome": case["action_outcome"],
                        "status": "Follow-Up",
                        "is_escalation": False,
                        "follow_up_action": follow_up,
                        "problem_identified": case["problem_identified"],
                        "rank_score": round(case["similarity_score"] * 0.95, 4),
                        "equipment_id": case["equipment_id"]
                    })
                if len(action_candidates) >= max_actions:
                    break

        action_candidates.sort(key=lambda x: x["rank_score"], reverse=True)
        return action_candidates[:max_actions]

    def get_similar_cases_for_recommendation(self, recommendation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the supporting prototype cases for a specific historical recommendation run.
        """
        try:
            records = db_service.get_recommendation_history(limit=100)
            target_rec = next((r for r in records if r.get("recommendation_id") == recommendation_id), None)
            if not target_rec:
                return []

            cases_str = target_rec.get("supporting_case_ids") or ""
            target_ids = [c.strip() for c in cases_str.split(",") if c.strip()]
            if not target_ids:
                return []

            df = self.get_case_library()
            if df.empty:
                return []

            matched_rows = df[df["Case_ID"].isin(target_ids)]
            results = []
            for _, row in matched_rows.iterrows():
                results.append({
                    "case_id": str(row.get("Case_ID")),
                    "mine": str(row.get("Mine")),
                    "date": str(row.get("Date")),
                    "primary_cause": str(row.get("Primary_Cause_Category")),
                    "planned_tonnes": float(row.get("Planned_Production_Tonnes") or 0.0),
                    "actual_tonnes": float(row.get("Actual_Production_Tonnes") or 0.0),
                    "shortfall_pct": float(row.get("Shortfall_Percentage") or 0.0),
                    "action_taken": str(row.get("Action_Taken")),
                    "action_outcome": str(row.get("Action_Outcome")),
                    "action_status": str(row.get("Action_Status")),
                    "follow_up_action": str(row.get("Follow_Up_Action")),
                    "similarity_score": float(target_rec.get("similarity_score") or 0.85)
                })
            return results
        except Exception as exc:
            print(f"[RecommendationEngine Error] get_similar_cases failed: {exc}")
            return []

    def generate_recommendations(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for generating CBR recommendations.
        - Builds situation profile
        - Retrieves Top-K similar cases from 898 cases
        - Ranks actions with progressive escalation
        - Formats explainability and card presentation
        - Persists recommendation history to MySQL
        """
        profile = self.build_situation_profile(input_data)
        top_k_cases = self.retrieve_top_k_cases(profile, k=DEFAULT_TOP_K)

        rec_id = f"REC-{profile['mine'][:3].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

        # Check prior recommendations from MySQL for progressive escalation
        prior_history = db_service.get_prior_recommendations_for_problem(
            mine=profile["mine"],
            problem_type=profile["primary_cause_category"],
            equipment_id=profile["equipment_id"]
        )

        # Check for Fallback condition (Low similarity threshold)
        max_similarity = top_k_cases[0]["similarity_score"] if top_k_cases else 0.0
        is_fallback = max_similarity < MIN_SIMILARITY_THRESHOLD

        if is_fallback or not top_k_cases:
            # Fallback response
            fallback_actions = [
                "Production is currently constrained below confidence threshold. Continue routine shift monitoring.",
                "Review heavy equipment availability and dispatch standby haul units where feasible.",
                "Inspect haul road conditions and verify drainage integrity under current weather."
            ]
            reasons = [
                "No similar cases were found. Please review the situation with the site team.",
                f"Active operational shortfall: {profile['shortfall_tonnes']:.1f} tonnes ({profile['shortfall_percentage']:.1f}%)."
            ]
            cards = self._build_cards(fallback_actions, reasons, "LOW RISK", profile)
            explanation = {
                "summary": "No similar cases were found. Please review the situation with the site team.",
                "best_case_id": None,
                "best_similarity_pct": round(max_similarity * 100.0, 1),
                "primary_cause": profile["primary_cause_category"],
                "key_factors": ["Operational shortfall within standard operational variance"],
                "data_basis_note": "Weather: MOIL Live / Proxy; Equipment: Proxy library; Rock: MWD reference"
            }
            return {
                "success": True,
                "recommendation_id": rec_id,
                "mine": profile["mine"],
                "date": profile["date"],
                "status": "LOW RISK",
                "target_production": profile["target_production"],
                "predicted_production": profile["predicted_production"],
                "shortfall_tonnes": profile["shortfall_tonnes"],
                "shortfall_percentage": profile["shortfall_percentage"],
                "disclaimer": self.disclaimer,
                "is_fallback": True,
                "explanation": explanation,
                "possible_reasons": reasons,
                "recommended_actions": fallback_actions,
                "similar_cases": [],
                "cards": cards
            }

        # Rank actions using CBR
        ranked_actions = self.rank_candidate_actions(profile, top_k_cases, prior_history)
        recommended_action_texts = [r["action"] for r in ranked_actions[:3]]

        # Determine overall operational status
        shortfall_pct = profile["shortfall_percentage"]
        if shortfall_pct >= 20.0:
            status = "HIGH RISK"
        elif shortfall_pct >= 10.0:
            status = "MEDIUM RISK"
        elif shortfall_pct > 0.0:
            status = "LOW RISK"
        else:
            status = "ON TARGET"

        # Build Reasons from Top Cases and Current Profile
        reasons = []
        top_case = top_k_cases[0]
        reasons.append(f"Main operational factor: {profile['primary_cause_category']}.")
        if top_case.get("problem_identified"):
            reasons.append(top_case["problem_identified"])
        if profile["shortfall_tonnes"] > 0:
            reasons.append(f"Predicted shortfall of {profile['shortfall_tonnes']:.1f} tonnes ({profile['shortfall_percentage']:.1f}% below planned target).")

        # Deduplicate reasons
        reasons = list(dict.fromkeys(reasons))

        # Explainability panel contents
        best_case = top_k_cases[0]
        key_factors = []
        cat_scores = best_case.get("category_scores", {})
        if cat_scores.get("weather", 0) > 0.7:
            key_factors.append(f"Strong weather alignment ({int(cat_scores['weather'] * 100)}% match)")
        if cat_scores.get("production", 0) > 0.7:
            key_factors.append(f"Comparable production scale & shortfall magnitude ({int(cat_scores['production'] * 100)}% match)")
        if cat_scores.get("equipment_component", 0) > 0.7:
            key_factors.append(f"Matched equipment type and component failure profile ({int(cat_scores['equipment_component'] * 100)}% match)")
        if cat_scores.get("drilling_geology", 0) > 0.7:
            key_factors.append(f"Consistent rock formation and drilling conditions ({int(cat_scores['drilling_geology'] * 100)}% match)")
        if not key_factors:
            key_factors.append(f"Overall multi-factor operational profile match ({best_case['similarity_pct']}%)")

        explanation = {
            "summary": (
                f"Matched Case {best_case['case_id']} with {best_case['similarity_pct']}% similarity. "
                f"{len(top_k_cases)} historical prototype cases in the 898-case library were evaluated, "
                f"confirming operational alignment on {', '.join(key_factors)}."
            ),
            "best_case_id": best_case["case_id"],
            "best_similarity_pct": best_case["similarity_pct"],
            "primary_cause": best_case["primary_cause"],
            "historical_outcome": best_case["action_outcome"],
            "key_factors": key_factors,
            "data_basis_note": (
                f"Weather: {best_case.get('weather_basis', 'MOIL Live/Proxy')}; "
                f"Equipment: {best_case.get('equipment_basis', 'Proxy library')}; "
                f"Rock: {best_case.get('rock_basis', 'MWD reference')}"
            )
        }

        # Build dynamic UI cards
        cards = self._build_cards(recommended_action_texts, reasons, status, profile, ranked_actions)

        # Build result payload
        result = {
            "success": True,
            "recommendation_id": rec_id,
            "mine": profile["mine"],
            "date": profile["date"],
            "status": status,
            "target_production": profile["target_production"],
            "predicted_production": profile["predicted_production"],
            "shortfall_tonnes": profile["shortfall_tonnes"],
            "shortfall_percentage": profile["shortfall_percentage"],
            "disclaimer": self.disclaimer,
            "is_fallback": False,
            "explanation": explanation,
            "possible_reasons": reasons,
            "recommended_actions": recommended_action_texts,
            "similar_cases": top_k_cases,
            "cards": cards
        }

        # Save to MySQL recommendation_history table for progressive tracking
        try:
            db_service.save_recommendation_history({
                "recommendation_id": rec_id,
                "date": profile["date"],
                "mine": profile["mine"],
                "equipment_id": profile.get("equipment_id") or (top_case.get("equipment_id") if top_case else None),
                "problem_type": profile["primary_cause_category"],
                "trigger_context": f"Target: {profile['target_production']}, Predicted: {profile['predicted_production']}, Shortfall: {profile['shortfall_tonnes']}t ({profile['shortfall_percentage']:.1f}%)",
                "recommended_action": recommended_action_texts[0] if recommended_action_texts else "Continue routine monitoring",
                "action_status": "PROPOSED",
                "action_date": profile["date"],
                "outcome": None,
                "follow_up_action": ranked_actions[0].get("follow_up_action") if ranked_actions else None,
                "supporting_case_ids": [c["case_id"] for c in top_k_cases],
                "similarity_score": max_similarity
            })
        except Exception as err:
            print(f"[RecommendationEngine Warning] Failed to log to recommendation_history: {err}")

        return result

    def _build_cards(
        self,
        actions: List[str],
        reasons: List[str],
        status: str,
        profile: Dict[str, Any],
        ranked_actions: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Formats actions and reasons into presentation cards for the UI."""
        cards = []
        for idx, action in enumerate(actions):
            act_lower = action.lower()

            if "schedule" in act_lower or "shift" in act_lower or "allocat" in act_lower or "target" in act_lower:
                title = "Adjust Shift Scheduling & Target Allocation"
                category = "Production Schedule"
                icon_type = "target"
                badge_class = "green-card"
                priority = "High Priority" if status == "HIGH RISK" else "Medium Priority"
            elif "equipment" in act_lower or "repair" in act_lower or "maintenance" in act_lower or "haul" in act_lower:
                title = "Optimize Heavy Equipment Availability & Maintenance"
                category = "Equipment Management"
                icon_type = "gear"
                badge_class = "purple-card"
                priority = "High Priority" if "prioritize" in act_lower or "emergency" in act_lower or "escalate" in act_lower else "Medium Priority"
            elif "blasting" in act_lower or "drilling" in act_lower or "rock" in act_lower:
                title = "Optimize Blasting Parameters & Drilling Patterns"
                category = "Drilling & Blasting"
                icon_type = "drill"
                badge_class = "green-card"
                priority = "Medium Priority"
            elif "drainage" in act_lower or "road" in act_lower or "haulage" in act_lower:
                title = "Ground Drainage & Haul Road Stabilization"
                category = "Haul Road Infrastructure"
                icon_type = "sprout"
                badge_class = "blue-card"
                priority = "Medium Priority"
            elif "weather" in act_lower or "rainfall" in act_lower or "rain" in act_lower:
                title = "Weather Mitigation & Safe Haulage Operations"
                category = "Weather & Environment"
                icon_type = "weather"
                badge_class = "blue-card"
                priority = "High Priority" if "heavy" in act_lower else "Medium Priority"
            else:
                title = f"Operational Recommendation #{idx + 1}"
                category = "General Mining Operations"
                icon_type = "bulb"
                badge_class = "blue-card"
                priority = "Medium Priority" if idx == 0 else "Low Priority"

            # Assign matching supporting reasons
            matched_reasons = []
            for r in reasons:
                r_low = r.lower()
                if (
                    ("weather" in act_lower and "weather" in r_low) or
                    ("rain" in act_lower and ("rain" in r_low or "precip" in r_low)) or
                    ("road" in act_lower and ("road" in r_low or "soil" in r_low)) or
                    ("equipment" in act_lower and "equipment" in r_low) or
                    ("shortfall" in act_lower and "shortfall" in r_low)
                ):
                    matched_reasons.append(r)

            if not matched_reasons and reasons:
                matched_reasons.append(reasons[idx % len(reasons)])

            # Check if this action was escalated
            is_escalated = False
            case_id = None
            if ranked_actions and idx < len(ranked_actions):
                is_escalated = ranked_actions[idx].get("is_escalation", False)
                case_id = ranked_actions[idx].get("case_id")

            cards.append({
                "id": idx + 1,
                "title": f"[Escalated] {title}" if is_escalated else title,
                "category": category,
                "action": action,
                "explanation": action,
                "supporting_points": matched_reasons,
                "priority": "High Priority" if is_escalated else priority,
                "icon_type": icon_type,
                "card_style": badge_class,
                "is_escalated": is_escalated,
                "matched_case_id": case_id
            })

        return cards


recommendation_engine = RecommendationEngine()
