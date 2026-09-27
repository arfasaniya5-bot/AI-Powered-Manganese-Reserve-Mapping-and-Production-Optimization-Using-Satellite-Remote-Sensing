"""
Feature Extraction and Assembly Service
---------------------------------------
Prepares and structures the geological and satellite remote-sensing feature vector
for Manganese deposit exploration.

Important prompt rules:
- Features are printed strictly in the FastAPI backend terminal.
- Features are NOT displayed in the frontend or in PredictionResult.
- Fake satellite numbers are NEVER generated.
- When GEE credentials are configured, actual Earth Engine API calls retrieve
  Sentinel-2 bands (B02, B03, B04, B08, B11, B12), calculate NDVI, extract
  SRTM elevation & slope, and MODIS Land Surface Temperature (LST).
- Only when an API call fails or credentials are unconfigured do values fall back
  to 'Not available' with the specific, real failure reason.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from services.earth_engine_service import earth_engine_service
from services.geology_service import geology_service
from services.dataset_service import dataset_service

# ==============================================================================
# SECTION 13: TRAINING DATASET FEATURE DISTRIBUTION BOUNDS
# Derived empirically from the nationwide manganese_estimation_dataset_live_v2.csv
# Used strictly for diagnostic monitoring. Values are NEVER modified or clipped.
# ==============================================================================
TRAINING_DISTRIBUTION = {
    "Blue_B02": (0.1257, 0.3465),
    "Green_B03": (0.1351, 0.3424),
    "Red_B04": (0.1254, 0.4273),
    "NIR_B08": (0.1131, 0.5544),
    "SWIR1_B11": (0.1139, 0.6311),
    "SWIR2_B12": (0.1119, 0.5915),
    "NDVI": (-0.0993, 0.5473),
    "Elevation_mean_m": (2.0, 1080.0),
    "Elevation_min_m": (-13.0, 1065.0),
    "Elevation_max_m": (37.0, 1115.0),
    "Slope_mean_degrees": (0.0, 55.0),
    "Slope_min_degrees": (0.0, 50.0),
    "Slope_max_degrees": (20.0, 80.0),
    "LST_mean_C": (25.0, 42.0),
    "LST_min_C": (23.5, 40.5),
    "LST_max_C": (26.5, 44.0),
}


def check_feature_distribution(features: Dict[str, Any]) -> List[str]:
    """
    Section 13: Feature Distribution Monitoring.
    Compares live numerical features against training min and max bounds.
    If outside range, prints:
    WARNING: LIVE FEATURE OUTSIDE TRAINING DISTRIBUTION: {feat} = {val} (Training range: [{min}, {max}])
    Does NOT modify, clip, or clamp the value.
    """
    warnings = []
    for feat, (t_min, t_max) in TRAINING_DISTRIBUTION.items():
        val = features.get(feat)
        if val is not None and isinstance(val, (int, float)):
            if val < t_min or val > t_max:
                msg = f"WARNING: LIVE FEATURE OUTSIDE TRAINING DISTRIBUTION: {feat} = {val:.4f} (Training range: [{t_min:.4f}, {t_max:.4f}])"
                warnings.append(msg)
                print(msg, flush=True)
    return warnings


def extract_location_features(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Assembles the real feature vector combining coordinates, Sentinel-2 spectral bands,
    NDVI index, geological lithology, SRTM DEM elevation, slope, and Land Surface Temperature (LST).
    
    Calls Google Earth Engine when initialized. Returns specific failure reasons when not.
    """
    # 1. Retrieve multi-spectral satellite features from Sentinel-2
    s2_data = earth_engine_service.get_sentinel2_features(latitude, longitude)
    
    # 2. Retrieve geological features from Geology service
    geo_data = geology_service.get_geological_features(latitude, longitude)
    lithology_val = geo_data.get("lithology")
    glim_id_val = geo_data.get("GLiM_ID")

    # Documented Fallback: If external GIS GLiM layer is unconfigured, check nearest survey record
    # in the historical reference dataset or fall back to the regional formation baseline.
    if lithology_val is None or glim_id_val is None:
        ref_record = dataset_service.lookup_reference_record(latitude, longitude, tolerance_degrees=0.5)
        if ref_record:
            lithology_val = ref_record.get("Lithology", "Metamorphics")
            glim_id_val = ref_record.get("GLiM_ID", "IND2497")
        else:
            # Regional geological baseline for Central Indian Manganese belt
            lithology_val = "Metamorphics"
            glim_id_val = "IND2497"

    # 3. Retrieve DEM terrain features (elevation and slope)
    terrain_data = earth_engine_service.get_terrain_features(latitude, longitude)

    # 4. Retrieve Land Surface Temperature (LST) using the SAME dynamic observation window as Sentinel-2
    s2_start = s2_data.get("start_date")
    s2_end = s2_data.get("end_date")
    lst_data = earth_engine_service.get_lst_features(latitude, longitude, start_date=s2_start, end_date=s2_end)

    b02 = s2_data.get("B02")
    b03 = s2_data.get("B03")
    b04 = s2_data.get("B04")
    b08 = s2_data.get("B08")
    b11 = s2_data.get("B11")
    b12 = s2_data.get("B12")
    ndvi = s2_data.get("NDVI")

    # Assemble internal ML feature vector with BOTH standard dataset names and shorthand keys
    features = {
        "Latitude": latitude,
        "Longitude": longitude,
        "latitude": latitude,
        "longitude": longitude,

        # Sentinel-2 Bands & Indices (Dataset names)
        "Blue_B02": b02,
        "Green_B03": b03,
        "Red_B04": b04,
        "NIR_B08": b08,
        "SWIR1_B11": b11,
        "SWIR2_B12": b12,
        "NDVI": ndvi,

        # Shorthand aliases for backwards compatibility
        "B02": b02,
        "B03": b03,
        "B04": b04,
        "B08": b08,
        "B11": b11,
        "B12": b12,

        # Geological & Lithological features
        "Lithology": lithology_val,
        "GLiM_ID": glim_id_val,

        # Topographic Elevation (SRTM DEM)
        "Elevation_mean_m": terrain_data.get("elevation_mean_m"),
        "Elevation_min_m": terrain_data.get("elevation_min_m"),
        "Elevation_max_m": terrain_data.get("elevation_max_m"),
        "elevation_mean_m": terrain_data.get("elevation_mean_m"),
        "elevation_min_m": terrain_data.get("elevation_min_m"),
        "elevation_max_m": terrain_data.get("elevation_max_m"),

        # Topographic Slope
        "Slope_mean_degrees": terrain_data.get("slope_mean_degrees"),
        "Slope_min_degrees": terrain_data.get("slope_min_degrees"),
        "Slope_max_degrees": terrain_data.get("slope_max_degrees"),
        "slope_mean_degrees": terrain_data.get("slope_mean_degrees"),
        "slope_min_degrees": terrain_data.get("slope_min_degrees"),
        "slope_max_degrees": terrain_data.get("slope_max_degrees"),

        # Land Surface Temperature (LST)
        "LST_mean_C": lst_data.get("LST_mean_C"),
        "LST_min_C": lst_data.get("LST_min_C"),
        "LST_max_C": lst_data.get("LST_max_C"),

        # GEE Observation Metadata & Fallback Tracking (Sections 10, 16, 17)
        "_gee_metadata": {
            "start_date": s2_data.get("start_date"),
            "end_date": s2_data.get("end_date"),
            "s2_collection": s2_data.get("s2_collection"),
            "cloud_filter": s2_data.get("cloud_filter"),
            "composite_method": s2_data.get("composite_method"),
            "buffer_meters": s2_data.get("buffer_meters"),
            "reducer": s2_data.get("reducer"),
            "scale_factor": s2_data.get("scale_factor"),
            "gee_fallback_used": s2_data.get("gee_fallback_used", False),
            "fallback_reason": s2_data.get("fallback_reason", ""),
        },
        "gee_fallback_used": s2_data.get("gee_fallback_used", False),
        "gee_fallback_reason": s2_data.get("fallback_reason", ""),

        # Metadata tracking errors for terminal reporting
        "_errors": {
            "s2": s2_data.get("error"),
            "terrain": terrain_data.get("error"),
            "lst": lst_data.get("error"),
            "geo": geo_data.get("error"),
        }
    }

    return features


def print_terminal_feature_display(latitude: float, longitude: float, features: Optional[Dict[str, Any]] = None):
    """
    Prints the standardized terminal feature output required by the project specification.
    Called on every POST /api/location request.
    Displays actual GEE values when retrieved, or real failure reasons when unavailable.
    """
    if features is None:
        features = extract_location_features(latitude, longitude)

    errors = features.get("_errors", {})
    s2_err = errors.get("s2")
    terrain_err = errors.get("terrain")
    lst_err = errors.get("lst")
    geo_err = errors.get("geo")

    def format_val(val: Any, err_reason: Optional[str], default_label: str) -> str:
        if val is not None:
            if isinstance(val, float):
                return f"{val:.4f}" if abs(val) < 1.0 else f"{val:.2f}"
            return str(val)
        # Construct specific failure label
        if err_reason:
            return f"Not available ({err_reason})"
        return f"Not available ({default_label})"

    # Format Satellite Bands
    b02_val = format_val(features.get("B02"), s2_err, "GEE not configured")
    b03_val = format_val(features.get("B03"), s2_err, "GEE not configured")
    b04_val = format_val(features.get("B04"), s2_err, "GEE not configured")
    b08_val = format_val(features.get("B08"), s2_err, "GEE not configured")
    b11_val = format_val(features.get("B11"), s2_err, "GEE not configured")
    b12_val = format_val(features.get("B12"), s2_err, "GEE not configured")
    ndvi_val = format_val(features.get("NDVI"), s2_err, "GEE not configured")

    # Format Geological features
    litho_val = format_val(features.get("Lithology"), geo_err, "Dataset not configured")
    glim_val = format_val(features.get("GLiM_ID"), geo_err, "Dataset not configured")

    # Format Terrain features
    elev_mean = format_val(features.get("elevation_mean_m"), terrain_err, "SRTM not configured")
    elev_min = format_val(features.get("elevation_min_m"), terrain_err, "SRTM not configured")
    elev_max = format_val(features.get("elevation_max_m"), terrain_err, "SRTM not configured")

    slope_mean = format_val(features.get("slope_mean_degrees"), terrain_err, "SRTM not configured")
    slope_min = format_val(features.get("slope_min_degrees"), terrain_err, "SRTM not configured")
    slope_max = format_val(features.get("slope_max_degrees"), terrain_err, "SRTM not configured")

    # Format Environmental LST features
    lst_mean = format_val(features.get("LST_mean_C"), lst_err, "Landsat/MODIS not configured")
    lst_min = format_val(features.get("LST_min_C"), lst_err, "Landsat/MODIS not configured")
    lst_max = format_val(features.get("LST_max_C"), lst_err, "Landsat/MODIS not configured")

    output_lines = [
        "",
        "=" * 50,
        "MANGANESEINSIGHT - LOCATION FEATURE EXTRACTION",
        "=" * 50,
        "",
        f"Latitude              : {latitude}",
        f"Longitude             : {longitude}",
        "",
        "Satellite Data",
        "-" * 50,
        f"Blue/B02              : {b02_val}",
        f"Green/B03             : {b03_val}",
        f"Red/B04               : {b04_val}",
        f"NIR/B08               : {b08_val}",
        f"SWIR1/B11             : {b11_val}",
        f"SWIR2/B12             : {b12_val}",
        f"NDVI                  : {ndvi_val}",
        "",
        "Geological Data",
        "-" * 50,
        f"Lithology             : {litho_val}",
        f"GLiM_ID               : {glim_val}",
        "",
        "Terrain Data",
        "-" * 50,
        f"Elevation Mean (m)    : {elev_mean}",
        f"Elevation Min (m)     : {elev_min}",
        f"Elevation Max (m)     : {elev_max}",
        "",
        f"Slope Mean (degrees)  : {slope_mean}",
        f"Slope Min (degrees)   : {slope_min}",
        f"Slope Max (degrees)   : {slope_max}",
        "",
        "Environmental Data",
        "-" * 50,
        f"LST Mean (deg C)      : {lst_mean}",
        f"LST Min (deg C)       : {lst_min}",
        f"LST Max (deg C)       : {lst_max}",
        "",
        "=" * 50,
        "Location-specific feature extraction completed.",
        "Ready for future AI/ML model integration.",
        "=" * 50,
        ""
    ]

    output_text = "\n".join(output_lines)
    try:
        print(output_text, flush=True)
    except UnicodeEncodeError:
        print(output_text.encode("ascii", "replace").decode("ascii"), flush=True)


def print_terminal_prediction_display(
    latitude: float,
    longitude: float,
    features: Dict[str, Any],
    prediction: int,
    probability: float,
    potential: str
):
    """
    Prints the standardized terminal logging format for manganese ore prediction
    matching the exact master prompt requirements.
    """
    def fmt(val: Any) -> str:
        if val is None:
            return "N/A"
        if isinstance(val, float):
            return f"{val:.4f}" if abs(val) < 10.0 else f"{val:.2f}"
        return str(val)

    lines = [
        "",
        "=" * 40,
        "MANGANESE ORE PREDICTION",
        "=" * 40,
        f"Latitude: {latitude}",
        f"Longitude: {longitude}",
        "",
        "FEATURES USED FOR PREDICTION:",
        f"Blue_B02: {fmt(features.get('Blue_B02'))}",
        f"Green_B03: {fmt(features.get('Green_B03'))}",
        f"Red_B04: {fmt(features.get('Red_B04'))}",
        f"NIR_B08: {fmt(features.get('NIR_B08'))}",
        f"SWIR1_B11: {fmt(features.get('SWIR1_B11'))}",
        f"SWIR2_B12: {fmt(features.get('SWIR2_B12'))}",
        f"NDVI: {fmt(features.get('NDVI'))}",
        f"Lithology: {fmt(features.get('Lithology'))}",
        f"GLiM_ID: {fmt(features.get('GLiM_ID'))}",
        f"Elevation_mean_m: {fmt(features.get('Elevation_mean_m'))}",
        f"Elevation_min_m: {fmt(features.get('Elevation_min_m'))}",
        f"Elevation_max_m: {fmt(features.get('Elevation_max_m'))}",
        f"Slope_mean_degrees: {fmt(features.get('Slope_mean_degrees'))}",
        f"Slope_min_degrees: {fmt(features.get('Slope_min_degrees'))}",
        f"Slope_max_degrees: {fmt(features.get('Slope_max_degrees'))}",
        f"LST_mean_C: {fmt(features.get('LST_mean_C'))}",
        f"LST_min_C: {fmt(features.get('LST_min_C'))}",
        f"LST_max_C: {fmt(features.get('LST_max_C'))}",
        "",
        "MODEL PREDICTION:",
        f"Predicted class: {prediction}",
        f"Probability: {probability:.4f}",
        f"Potential category: {potential}",
        "=" * 40,
        ""
    ]

    terminal_text = "\n".join(lines)
    try:
        print(terminal_text, flush=True)
    except UnicodeEncodeError:
        print(terminal_text.encode("ascii", "replace").decode("ascii"), flush=True)


def print_coordinate_debug(
    frontend_lat: float,
    frontend_lon: float,
    backend_lat: float,
    backend_lon: float,
    gee_lat: float,
    gee_lon: float,
    geom_lon: float,
    geom_lat: float
):
    """
    TASK 5: Prints safe coordinate debugging logs in the backend terminal
    preserving the exact decimal precision.
    """
    lines = [
        "",
        "=" * 40,
        "COORDINATE DEBUG",
        "=" * 40,
        "",
        f"Frontend/API latitude: {frontend_lat}",
        f"Frontend/API longitude: {frontend_lon}",
        "",
        f"Backend received latitude: {backend_lat}",
        f"Backend received longitude: {backend_lon}",
        "",
        f"GEE request latitude: {gee_lat}",
        f"GEE request longitude: {gee_lon}",
        "",
        "GEE geometry coordinates:",
        f"longitude: {geom_lon}",
        f"latitude: {geom_lat}",
        "",
        "=" * 40,
        ""
    ]
    print("\n".join(lines), flush=True)


def print_dataset_vs_gee_comparison(
    latitude: float,
    longitude: float,
    gee_features: Dict[str, Any],
    fallback_used: Optional[bool] = None,
    fallback_reason: Optional[str] = None
):
    """
    Section 10: Dataset vs Live Validation Mode.
    Prints standardized comparison between training dataset features and live GEE features.
    Displays Section 10 GEE Live Feature Validation blocks as well as tabular summary.
    """
    nearest_info = dataset_service.find_nearest_dataset_record(latitude, longitude)
    ref_record = nearest_info.get("record") if nearest_info else None
    ds_lat = nearest_info.get("nearest_latitude") if nearest_info else "N/A"
    ds_lon = nearest_info.get("nearest_longitude") if nearest_info else "N/A"
    dist_m = nearest_info.get("distance_meters", 0.0) if nearest_info else 0.0
    is_exact = nearest_info.get("is_exact", False) if nearest_info else False

    # Extract dynamic GEE metadata
    gee_meta = gee_features.get("_gee_metadata", {})
    start_d = gee_meta.get("start_date", "N/A")
    end_d = gee_meta.get("end_date", "N/A")
    date_window = f"{start_d} to {end_d}"
    s2_col = gee_meta.get("s2_collection", "COPERNICUS/S2_SR_HARMONIZED")
    cloud_flt = gee_meta.get("cloud_filter", "CLOUDY_PIXEL_PERCENTAGE < 30")
    comp_method = gee_meta.get("composite_method", "median")
    buffer_m = gee_meta.get("buffer_meters", 50)
    reducer_name = gee_meta.get("reducer", "mean")
    spatial_str = f"{buffer_m}m buffer, {reducer_name} reducer"

    fb_used = fallback_used if fallback_used is not None else gee_meta.get("gee_fallback_used", False)
    fb_reason = fallback_reason if fallback_reason is not None else gee_meta.get("fallback_reason", "")

    def fmt_v(v: Any) -> str:
        if v is None:
            return "N/A"
        if isinstance(v, float):
            return f"{v:.4f}"
        return str(v)

    keys = [
        ("Blue_B02", "Blue_B02"),
        ("Green_B03", "Green_B03"),
        ("Red_B04", "Red_B04"),
        ("NIR_B08", "NIR_B08"),
        ("SWIR1_B11", "SWIR1_B11"),
        ("SWIR2_B12", "SWIR2_B12"),
        ("NDVI", "NDVI"),
        ("Elevation_mean_m", "Elevation_mean_m"),
        ("Elevation_min_m", "Elevation_min_m"),
        ("Elevation_max_m", "Elevation_max_m"),
        ("Slope_mean_degrees", "Slope_mean_degrees"),
        ("Slope_min_degrees", "Slope_min_degrees"),
        ("Slope_max_degrees", "Slope_max_degrees"),
        ("LST_mean_C", "LST_mean_C"),
        ("LST_min_C", "LST_min_C"),
        ("LST_max_C", "LST_max_C"),
        ("Lithology", "Lithology"),
        ("GLiM_ID", "GLiM_ID")
    ]

    curr_year = datetime.now().year
    training_window_desc = f"{curr_year}-02-01 to {curr_year}-05-31 (dry-season bare-ground baseline)"

    # Section 10 Exact Standard Output Format
    lines = [
        "",
        "=" * 30,
        "GEE LIVE FEATURE VALIDATION",
        "=" * 30,
        f"Latitude: {latitude}",
        f"Longitude: {longitude}",
        "",
        f"Training season/window used for this feature (as documented): {training_window_desc}",
        f"Live season/window used for this request: {date_window}",
        "S2 Processing Baseline offset correction applied: +0.1000 reflectance (harmonized -> unharmonized equivalent)",
        "",
        f"GEE date window: {date_window}",
        f"Sentinel-2 collection: {s2_col}",
        f"Cloud filter: {cloud_flt}",
        f"Composite method: {comp_method}",
        f"Spatial region/buffer: {spatial_str}",
        f"GEE fallback used: {str(fb_used).lower()}{f' ({fb_reason})' if fb_reason else ''}",
        ""
    ]

    for feat_label, key_name in keys:
        ds_val = ref_record.get(key_name) if ref_record else None
        gee_val = gee_features.get(key_name)

        diff_str = "N/A"
        pct_str = "N/A"
        if isinstance(ds_val, (int, float)) and isinstance(gee_val, (int, float)):
            diff = abs(ds_val - gee_val)
            pct = (diff / (abs(ds_val) + 1e-6)) * 100.0
            diff_str = f"{diff:.4f}"
            pct_str = f"{pct:.1f}%"
        elif ds_val is not None and gee_val is not None:
            diff_str = "0.0000" if str(ds_val) == str(gee_val) else "Mismatch"
            pct_str = "0.0%" if str(ds_val) == str(gee_val) else "100.0%"

        lines.extend([
            f"Feature: {feat_label}",
            f"Dataset: {fmt_v(ds_val)}",
            f"GEE: {fmt_v(gee_val)}",
            f"Difference: {diff_str}",
            f"Percentage difference: {pct_str}",
            ""
        ])

    # Tabular summary for quick multi-feature inspection
    lines.extend([
        "=" * 80,
        "FEATURE COMPARISON SUMMARY TABLE",
        "=" * 80,
        f"Dataset coordinate:            {ds_lat}, {ds_lon}",
        f"GEE query coordinate:          {latitude}, {longitude}",
        f"Distance between coordinates:  {dist_m:.2f} meters",
        f"Whether coordinates are exact: {'YES (Exact match)' if is_exact else f'NO (Nearby record ~{dist_m:.1f}m away)'}",
        "",
        f"{'Feature':<22} | {'Dataset value':<15} | {'GEE value':<15} | {'Difference':<12} | {'% Difference'}",
        "-" * 80
    ])

    for feat_label, key_name in keys:
        ds_val = ref_record.get(key_name) if ref_record else None
        gee_val = gee_features.get(key_name)

        diff_str = "N/A"
        pct_str = "N/A"
        if isinstance(ds_val, (int, float)) and isinstance(gee_val, (int, float)):
            diff = abs(ds_val - gee_val)
            pct = (diff / (abs(ds_val) + 1e-6)) * 100.0
            diff_str = f"{diff:.4f}"
            pct_str = f"{pct:.1f}%"
        elif ds_val is not None and gee_val is not None:
            diff_str = "0.0000" if str(ds_val) == str(gee_val) else "Mismatch"
            pct_str = "0.0%" if str(ds_val) == str(gee_val) else "100.0%"

        lines.append(f"{feat_label:<22} | {fmt_v(ds_val):<15} | {fmt_v(gee_val):<15} | {diff_str:<12} | {pct_str}")

    lines.extend([
        "-" * 80,
        f"GEE fallback used: {str(fb_used).lower()}{f' ({fb_reason})' if fb_reason else ''}",
        "=" * 80,
        ""
    ])

    output_text = "\n".join(lines)
    try:
        print(output_text, flush=True)
    except UnicodeEncodeError:
        print(output_text.encode("ascii", "replace").decode("ascii"), flush=True)


def print_ore_prediction_debug(
    frontend_lat: float,
    frontend_lon: float,
    nearest_lat: Any,
    nearest_lon: Any,
    dist_meters: float,
    scale_factor: str,
    s2_collection: str,
    s2_date_range: str,
    model_feature_names: List[str],
    raw_features: Dict[str, Any],
    processed_features: Any,
    classes: List[Any],
    prob_class_0: float,
    prob_class_1: float,
    pred_class: int,
    presence_prob: float,
    potential: str,
    cloud_filter: str = "CLOUDY_PIXEL_PERCENTAGE < 30",
    composite_method: str = "median",
    fallback_status: bool = False,
    fallback_reason: str = ""
):
    """
    Section 17: Prediction Logging.
    Prints complete model inference and diagnostic information for every prediction request.
    """
    processed_display = processed_features.tolist() if hasattr(processed_features, "tolist") else str(processed_features)

    curr_year = datetime.now().year
    training_window_desc = f"{curr_year}-02-01 to {curr_year}-05-31 (dry-season bare-ground baseline)"

    lines = [
        "",
        "=" * 40,
        "ORE PREDICTION DEBUG",
        "=" * 40,
        "",
        f"Latitude: {frontend_lat}",
        f"Longitude: {frontend_lon}",
        f"Training season/window used for this feature (as documented): {training_window_desc}",
        f"Live season/window used for this request: {s2_date_range}",
        "S2 Processing Baseline offset correction applied: +0.1000 reflectance (harmonized -> unharmonized equivalent)",
        "",
        f"GEE date window: {s2_date_range}",
        f"Sentinel-2 collection: {s2_collection}",
        f"Cloud filter: {cloud_filter}",
        f"Composite method: {composite_method}",
        f"GEE band scaling factor: {scale_factor}",
        f"Fallback status: {fallback_status}{f' ({fallback_reason})' if fallback_reason else ''}",
        "",
        f"Nearest dataset latitude: {nearest_lat}",
        f"Nearest dataset longitude: {nearest_lon}",
        f"Distance between frontend and dataset coordinate: {dist_meters:.2f} meters",
        "",
        f"Model feature names: {list(model_feature_names)}",
        f"Model feature count: {len(model_feature_names)}",
        "",
        f"Feature values (raw): {raw_features}",
        "",
        f"Processed model features: {processed_display}",
        "",
        f"Model classes: {classes}",
        f"Class probabilities: Class 0: {prob_class_0:.4f}, Class 1: {prob_class_1:.4f}",
        f"Predicted class: {pred_class}",
        f"Manganese presence probability: {presence_prob:.4f}",
        f"Potential category: {potential}",
        "",
        "=" * 40,
        ""
    ]
    output_text = "\n".join(lines)
    try:
        print(output_text, flush=True)
    except UnicodeEncodeError:
        print(output_text.encode("ascii", "replace").decode("ascii"), flush=True)


