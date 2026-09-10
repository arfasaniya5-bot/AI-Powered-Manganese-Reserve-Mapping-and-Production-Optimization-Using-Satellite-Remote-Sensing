"""
Recommendation Service
----------------------
MOIL ManganeseInsight - Production Shortfall Recommendation Engine.
This module incorporates the exact recommendation logic provided by the team
as the authoritative SOURCE OF TRUTH.
"""

import pandas as pd
from typing import Dict, Any, List, Optional


def generate_recommendations(
    target_production,
    predicted_production,
    temperature,
    wind_speed,
    humidity,
    precipitation,
    soil_moisture,
    equipment_df=None,
    mwd_df=None
):
    """
    Generate possible reasons and corrective actions
    for production shortfall.
    SOURCE OF TRUTH - exact logic provided by team.
    """

    reasons = []
    recommendations = []

    # ========================================================
    # 1. PRODUCTION SHORTFALL
    # ========================================================

    shortfall = max(
        0,
        target_production - predicted_production
    )

    if shortfall == 0:
        return {
            "status": "ON TARGET",
            "shortfall_tonnes": 0,
            "possible_reasons": [],
            "recommended_actions": [
                "Production is expected to meet the target. Continue current mine operations."
            ]
        }

    shortfall_percentage = (
        shortfall / target_production
    ) * 100

    # ========================================================
    # 2. WEATHER CONDITIONS
    # ========================================================

    if wind_speed >= 8:
        reasons.append(
            "High wind speed may reduce operational efficiency."
        )

        recommendations.append(
            "Monitor wind conditions and temporarily adjust "
            "haulage and exposed mining operations."
        )

    elif wind_speed >= 5:
        reasons.append(
            "Elevated wind speed may affect mining operations."
        )

        recommendations.append(
            "Monitor wind conditions and maintain safe operating speeds."
        )

    if precipitation >= 20:
        reasons.append(
            "Heavy rainfall may disrupt mining and haulage activities."
        )

        recommendations.append(
            "Adjust the mine schedule during heavy rainfall "
            "and prioritize safe operating areas."
        )

    elif precipitation >= 10:
        reasons.append(
            "Rainfall may reduce mining and haulage efficiency."
        )

        recommendations.append(
            "Plan critical excavation and haulage activities "
            "around rainfall periods."
        )

    # ========================================================
    # 3. SOIL MOISTURE
    # ========================================================

    if soil_moisture >= 0.45:
        reasons.append(
            "High soil moisture may affect haulage and ground movement."
        )

        recommendations.append(
            "Monitor haul roads and drainage conditions and "
            "prioritize stable haulage routes."
        )

    elif soil_moisture >= 0.35:
        reasons.append(
            "Increased soil moisture may reduce ground and haulage efficiency."
        )

        recommendations.append(
            "Inspect haul roads and drainage before moving heavy equipment."
        )

    # ========================================================
    # 4. TEMPERATURE
    # ========================================================

    if temperature >= 40:
        reasons.append(
            "High temperature may reduce equipment operating efficiency."
        )

        recommendations.append(
            "Schedule equipment-intensive activities during cooler periods "
            "and monitor equipment temperature."
        )

    # ========================================================
    # 5. HUMIDITY
    # ========================================================

    if humidity >= 85:
        reasons.append(
            "High humidity may contribute to difficult operating conditions."
        )

        recommendations.append(
            "Increase equipment inspection and monitor operating conditions."
        )

    # ========================================================
    # 6. EQUIPMENT DATA
    # ========================================================

    if equipment_df is not None and not equipment_df.empty:

        # -----------------------------------------------
        # Downtime
        # -----------------------------------------------

        if "downtime_hours" in equipment_df.columns:

            total_downtime = pd.to_numeric(
                equipment_df["downtime_hours"],
                errors="coerce"
            ).fillna(0).sum()

            if total_downtime >= 8:

                reasons.append(
                    f"Equipment downtime is high ({total_downtime:.1f} hours)."
                )

                recommendations.append(
                    "Re-deploy available equipment to critical mining activities "
                    "and prioritize repair of high-downtime equipment."
                )

            elif total_downtime >= 4:

                reasons.append(
                    f"Equipment downtime may affect production ({total_downtime:.1f} hours)."
                )

                recommendations.append(
                    "Inspect affected equipment and reduce unnecessary downtime."
                )

        # -----------------------------------------------
        # Equipment availability
        # -----------------------------------------------

        if "operating_hours" in equipment_df.columns:

            operating_hours = pd.to_numeric(
                equipment_df["operating_hours"],
                errors="coerce"
            ).fillna(0)

            if len(operating_hours) > 0:

                avg_hours = operating_hours.mean()

                if avg_hours < 5:

                    reasons.append(
                        "Low equipment operating activity may constrain production."
                    )

                    recommendations.append(
                        "Re-deploy available equipment to the highest-priority "
                        "production areas."
                    )

        # -----------------------------------------------
        # Unscheduled failures
        # -----------------------------------------------

        if "was_scheduled" in equipment_df.columns:

            unscheduled = (
                equipment_df["was_scheduled"]
                .astype(str)
                .str.lower()
                .isin(["false", "0", "no"])
                .sum()
            )

            if unscheduled > 0:

                reasons.append(
                    "Unscheduled equipment failures were detected."
                )

                recommendations.append(
                    "Prioritize corrective maintenance and keep backup equipment "
                    "available for critical production operations."
                )

        # -----------------------------------------------
        # Severity
        # -----------------------------------------------

        if "severity" in equipment_df.columns:

            severity = (
                equipment_df["severity"]
                .astype(str)
                .str.lower()
            )

            high_severity = severity.isin(
                ["high", "critical", "severe"]
            ).sum()

            if high_severity > 0:

                reasons.append(
                    f"{high_severity} high-severity equipment issue(s) detected."
                )

                recommendations.append(
                    "Prioritize high-severity equipment for immediate inspection "
                    "or replacement."
                )

        # -----------------------------------------------
        # Equipment production loss
        # -----------------------------------------------

        if "production_loss_tonnes" in equipment_df.columns:

            equipment_loss = pd.to_numeric(
                equipment_df["production_loss_tonnes"],
                errors="coerce"
            ).fillna(0).sum()

            if equipment_loss > 0:

                reasons.append(
                    f"Equipment-related production loss is estimated at "
                    f"{equipment_loss:.0f} tonnes."
                )

                recommendations.append(
                    "Re-deploy functioning equipment and prioritize maintenance "
                    "to recover the expected production loss."
                )

    # ========================================================
    # 7. MWD / BLASTING DATA
    # ========================================================

    if mwd_df is not None and not mwd_df.empty:

        # -----------------------------------------------
        # Rock condition
        # -----------------------------------------------

        if "Rock" in mwd_df.columns:

            difficult_rocks = [
                "Drammensgranite",
                "Granittic_gneiss",
                "Hornfels",
                "Augen_gneiss",
                "Amphibolittic_gneiss"
            ]

            rock_values = (
                mwd_df["Rock"]
                .astype(str)
            )

            difficult_count = rock_values.isin(
                difficult_rocks
            ).sum()

            if difficult_count > 0:

                reasons.append(
                    "Difficult rock conditions were identified from MWD/blasting data."
                )

                recommendations.append(
                    "Optimize blasting parameters and review drilling patterns "
                    "for difficult rock zones."
                )

        # -----------------------------------------------
        # Penetration rate
        # -----------------------------------------------

        if "PenetrNormMean" in mwd_df.columns:

            penetration = pd.to_numeric(
                mwd_df["PenetrNormMean"],
                errors="coerce"
            ).dropna()

            if len(penetration) > 0:

                avg_penetration = penetration.mean()

                if avg_penetration < 5:

                    reasons.append(
                        "Low drilling penetration indicates difficult drilling conditions."
                    )

                    recommendations.append(
                        "Inspect drill bits and optimize rotation, feed pressure "
                        "and hammer pressure."
                    )

        # -----------------------------------------------
        # Transition zone
        # -----------------------------------------------

        if "transition_zone" in mwd_df.columns:

            transition = (
                mwd_df["transition_zone"]
                .astype(str)
                .str.lower()
                .isin(["true", "1", "yes"])
                .sum()
            )

            if transition > 0:

                reasons.append(
                    "Transition-zone conditions were detected in MWD data."
                )

                recommendations.append(
                    "Increase drilling monitoring and adjust blasting parameters "
                    "for transition zones."
                )

        # -----------------------------------------------
        # Round length
        # -----------------------------------------------

        if "round_length" in mwd_df.columns:

            round_length = pd.to_numeric(
                mwd_df["round_length"],
                errors="coerce"
            ).dropna()

            if len(round_length) > 0:

                avg_round = round_length.mean()

                if avg_round < 2:

                    reasons.append(
                        "Short drilling rounds may reduce blasting productivity."
                    )

                    recommendations.append(
                        "Review blast design and drilling plan to improve "
                        "round length where operationally feasible."
                    )

    # ========================================================
    # 8. SHORTFALL SEVERITY
    # ========================================================

    if shortfall_percentage >= 20:

        status = "HIGH RISK"

        recommendations.append(
            "Prioritize production recovery by adjusting the mine schedule "
            "and allocating available equipment to critical production areas."
        )

    elif shortfall_percentage >= 10:

        status = "MEDIUM RISK"

        recommendations.append(
            "Review the daily mine schedule and address the highest-impact "
            "equipment, weather and blasting constraints."
        )

    else:

        status = "LOW RISK"

        recommendations.append(
            "Monitor the identified constraints and make minor operational "
            "adjustments to maintain the production target."
        )

    # ========================================================
    # 9. REMOVE DUPLICATE RECOMMENDATIONS
    # ========================================================

    recommendations = list(
        dict.fromkeys(recommendations)
    )

    reasons = list(
        dict.fromkeys(reasons)
    )

    # ========================================================
    # 10. FALLBACK
    # ========================================================

    if not reasons:

        reasons.append(
            "No major operational constraint was detected "
            "from the supplied data."
        )

    if not recommendations:

        recommendations.append(
            "Continue monitoring production, equipment and environmental conditions."
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "status": status,

        "target_production": round(
            target_production, 2
        ),

        "predicted_production": round(
            predicted_production, 2
        ),

        "shortfall_tonnes": round(
            shortfall, 2
        ),

        "shortfall_percentage": round(
            shortfall_percentage, 2
        ),

        "possible_reasons": reasons,

        "recommended_actions": recommendations
    }


class RecommendationService:
    """
    Adapter and service layer wrapping the recommendation engine.
    Prepares DataFrames from request payloads and structures presentation cards.
    """

    def process_recommendations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts inputs from request dictionary, passes them to generate_recommendations,
        and enriches the result with card presentation metadata (title, category, priority, icon).
        """
        target = float(data.get("target_production") or 10000.0)
        predicted = float(data.get("predicted_production") or (target * 0.85))
        temp = float(data.get("temperature") if data.get("temperature") is not None else (data.get("temperature_c") or 16.4))
        wind = float(data.get("wind_speed") if data.get("wind_speed") is not None else (data.get("wind_speed_m_s") or 2.3))
        humidity = float(data.get("humidity") if data.get("humidity") is not None else (data.get("relative_humidity_percent") or 52.1))
        precip = float(data.get("precipitation") if data.get("precipitation") is not None else (data.get("precipitation_mm") or 0.0))
        soil_m = float(data.get("soil_moisture") if data.get("soil_moisture") is not None else (data.get("soil_moisture_0_100cm") or 0.304))

        # Build equipment DataFrame if provided
        equipment_df = None
        eq_data = data.get("equipment_data")
        if isinstance(eq_data, list) and eq_data:
            equipment_df = pd.DataFrame(eq_data)
        elif isinstance(eq_data, dict) and eq_data:
            equipment_df = pd.DataFrame([eq_data])
        else:
            # Check for discrete equipment fields
            downtime = float(data.get("downtime_hours") or 0.0)
            eq_loss = float(data.get("equipment_production_loss") or 0.0)
            if downtime > 0 or eq_loss > 0 or data.get("severity"):
                equipment_df = pd.DataFrame([{
                    "downtime_hours": downtime,
                    "production_loss_tonnes": eq_loss,
                    "severity": str(data.get("severity") or "moderate"),
                    "operating_hours": float(data.get("operating_hours") or 8.0),
                    "was_scheduled": False if downtime > 0 else True
                }])

        # Build MWD/blasting DataFrame if provided
        mwd_df = None
        geo_data = data.get("geological_data") or data.get("mwd_data")
        if isinstance(geo_data, list) and geo_data:
            mwd_df = pd.DataFrame(geo_data)
        elif isinstance(geo_data, dict) and geo_data:
            mwd_df = pd.DataFrame([geo_data])
        else:
            rock = str(data.get("rock_prediction") or data.get("rock") or "")
            if rock:
                mwd_df = pd.DataFrame([{
                    "Rock": rock,
                    "PenetrNormMean": float(data.get("penetration_rate") or 12.0),
                    "transition_zone": False,
                    "round_length": float(data.get("round_length") or 4.5)
                }])

        # Execute teammate's recommendation engine
        raw_result = generate_recommendations(
            target_production=target,
            predicted_production=predicted,
            temperature=temp,
            wind_speed=wind,
            humidity=humidity,
            precipitation=precip,
            soil_moisture=soil_m,
            equipment_df=equipment_df,
            mwd_df=mwd_df
        )

        status = raw_result.get("status", "LOW RISK")
        actions = raw_result.get("recommended_actions", [])
        reasons = raw_result.get("possible_reasons", [])

        # Build dynamic presentation cards
        cards = []
        for idx, action in enumerate(actions):
            act_lower = action.lower()
            if "schedule" in act_lower or "allocat" in act_lower or "recover" in act_lower or "target" in act_lower:
                title = "Adjust Shift Scheduling & Target Allocation"
                category = "Production Schedule"
                icon_type = "target"
                badge_class = "green-card"
                priority = "High Priority" if status == "HIGH RISK" else ("Medium Priority" if status == "MEDIUM RISK" else "Low Priority")
            elif "equipment" in act_lower or "repair" in act_lower or "maintenance" in act_lower or "downtime" in act_lower:
                title = "Optimize Heavy Equipment Availability & Maintenance"
                category = "Equipment Management"
                icon_type = "gear"
                badge_class = "purple-card"
                priority = "High Priority" if "prioritize" in act_lower or "repair" in act_lower else "Medium Priority"
            elif "blasting" in act_lower or "drilling" in act_lower or "rock" in act_lower:
                title = "Optimize Blasting Parameters & Drilling Patterns"
                category = "Drilling & Blasting"
                icon_type = "drill"
                badge_class = "green-card"
                priority = "Medium Priority"
            elif "wind" in act_lower or "rainfall" in act_lower or "rain" in act_lower:
                title = "Weather Mitigation & Safe Haulage Operations"
                category = "Weather & Environment"
                icon_type = "weather"
                badge_class = "blue-card"
                priority = "High Priority" if "heavy" in act_lower or "temporarily adjust" in act_lower else "Medium Priority"
            elif "soil" in act_lower or "haul road" in act_lower or "drainage" in act_lower:
                title = "Ground Drainage & Haul Road Stabilization"
                category = "Haul Road Infrastructure"
                icon_type = "sprout"
                badge_class = "blue-card"
                priority = "Medium Priority"
            else:
                title = f"Operational Recommendation #{idx + 1}"
                category = "General Mining Operations"
                icon_type = "bulb"
                badge_class = "blue-card"
                priority = "Low Priority"

            # Assign matching supporting reasons if available
            matched_reasons = []
            for r in reasons:
                r_low = r.lower()
                if ("wind" in act_lower and "wind" in r_low) or                    ("rain" in act_lower and ("rain" in r_low or "precip" in r_low)) or                    ("soil" in act_lower and ("soil" in r_low or "moisture" in r_low)) or                    ("equipment" in act_lower and "equipment" in r_low) or                    ("downtime" in act_lower and "downtime" in r_low) or                    ("rock" in act_lower and "rock" in r_low) or                    ("drilling" in act_lower and "drilling" in r_low):
                    matched_reasons.append(r)

            if not matched_reasons and reasons:
                matched_reasons.append(reasons[idx % len(reasons)])

            cards.append({
                "id": idx + 1,
                "title": title,
                "category": category,
                "action": action,
                "explanation": action,
                "supporting_points": matched_reasons if matched_reasons else [f"Shortfall context: {raw_result.get('shortfall_tonnes', 0)} tonnes ({raw_result.get('shortfall_percentage', 0)}%)"],
                "priority": priority,
                "icon_type": icon_type,
                "card_style": badge_class
            })

        return {
            "success": True,
            "mine": data.get("mine") or "Balaghat",
            "date": data.get("date") or "2026-09-14",
            "status": status,
            "target_production": raw_result.get("target_production", target),
            "predicted_production": raw_result.get("predicted_production", predicted),
            "shortfall_tonnes": raw_result.get("shortfall_tonnes", 0.0),
            "shortfall_percentage": raw_result.get("shortfall_percentage", 0.0),
            "possible_reasons": reasons,
            "recommended_actions": actions,
            "cards": cards
        }


recommendation_service = RecommendationService()
