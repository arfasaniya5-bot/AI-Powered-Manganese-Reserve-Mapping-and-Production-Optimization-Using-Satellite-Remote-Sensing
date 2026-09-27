"""
Weather Feature Mapper Adapter
------------------------------
Isolates unit conversion, aggregation, and feature naming transformations
between raw Open-Meteo responses and the production ML model's expected inputs.

Ensures strict downstream compatibility with:
- Model 1: RandomForestRegressor (Historical Production)
- Model 2: RandomForestRegressor (Weather + Soil Moisture)
- Model 3: RandomForestClassifier (Rock Classification)
- Model 4: XGBRegressor (Equipment Failure)
"""

from typing import Dict, Any, Optional, Tuple


def calculate_depth_weighted_soil_moisture(
    sm_0_7: Optional[float],
    sm_7_28: Optional[float],
    sm_28_100: Optional[float]
) -> Optional[float]:
    """
    Computes depth-weighted volumetric soil moisture (0-100 cm) from layer components:
    - 0 to 7 cm: weight 7% (0.07)
    - 7 to 28 cm: weight 21% (0.21)
    - 28 to 100 cm: weight 72% (0.72)
    
    Total depth: 7 + 21 + 72 = 100 cm.
    Formula: (sm_0_7 * 7 + sm_7_28 * 21 + sm_28_100 * 72) / 100

    Returns None if any required layer is None or missing (gap detection).
    """
    if sm_0_7 is None or sm_7_28 is None or sm_28_100 is None:
        return None

    try:
        val_0_7 = float(sm_0_7)
        val_7_28 = float(sm_7_28)
        val_28_100 = float(sm_28_100)

        # Sanity check: soil moisture ratios are typically between 0.0 and 1.0 m³/m³
        if val_0_7 < 0 or val_7_28 < 0 or val_28_100 < 0:
            return None

        weighted = (val_0_7 * 7.0 + val_7_28 * 21.0 + val_28_100 * 72.0) / 100.0
        return round(weighted, 3)
    except (ValueError, TypeError):
        return None


def map_open_meteo_to_features(
    raw_hourly: Dict[str, Any],
    target_hour_index: int = 12
) -> Dict[str, Any]:
    """
    Extracts weather features from raw Open-Meteo hourly response arrays
    at the given hour index (defaulting to midday 12:00).

    Returns a normalized dictionary containing:
    1. Clean descriptive keys:
       - temperature_c: float (°C)
       - wind_speed_ms: float (m/s)
       - relative_humidity_pct: float (%)
       - precipitation_mm: float (mm)
       - soil_moisture_0_100cm: Optional[float] (0-100cm depth-weighted m³/m³)
       - soil_moisture_available: bool
       - forecast_time: str
    2. Model-compatible alias keys for seamless downstream inference:
       - temperature
       - wind_speed
       - humidity
       - precipitation
       - soil_moisture
    """
    times = raw_hourly.get("time") or []
    if not times:
        raise ValueError("Open-Meteo response contains no hourly time intervals.")

    idx = max(0, min(target_hour_index, len(times) - 1))
    forecast_time = str(times[idx])

    # Extract raw parameters at index
    def get_val(key: str) -> Optional[float]:
        arr = raw_hourly.get(key)
        if arr and idx < len(arr):
            v = arr[idx]
            if v is not None:
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None
        return None

    temp_val = get_val("temperature_2m")
    wind_val = get_val("wind_speed_10m")
    humidity_val = get_val("relative_humidity_2m")
    precip_val = get_val("precipitation")

    sm_0_7 = get_val("soil_moisture_0_to_7cm")
    sm_7_28 = get_val("soil_moisture_7_to_28cm")
    sm_28_100 = get_val("soil_moisture_28_to_100cm")

    soil_moisture = calculate_depth_weighted_soil_moisture(sm_0_7, sm_7_28, sm_28_100)
    soil_moisture_available = soil_moisture is not None

    return {
        "forecast_time": forecast_time,
        "temperature_c": round(temp_val, 1) if temp_val is not None else None,
        "wind_speed_ms": round(wind_val, 2) if wind_val is not None else None,
        "relative_humidity_pct": round(humidity_val, 1) if humidity_val is not None else None,
        "precipitation_mm": round(precip_val, 2) if precip_val is not None else None,
        "soil_moisture_0_100cm": soil_moisture,
        "soil_moisture_available": soil_moisture_available,
        # Sub-layer breakdown for detailed inspection if needed
        "soil_moisture_sublayers": {
            "soil_moisture_0_7cm": sm_0_7,
            "soil_moisture_7_28cm": sm_7_28,
            "soil_moisture_28_100cm": sm_28_100,
        },
        # Downstream ML Model Compatibility Aliases
        "temperature": round(temp_val, 1) if temp_val is not None else None,
        "wind_speed": round(wind_val, 2) if wind_val is not None else None,
        "humidity": round(humidity_val, 1) if humidity_val is not None else None,
        "precipitation": round(precip_val, 2) if precip_val is not None else None,
        "soil_moisture": soil_moisture,
    }
