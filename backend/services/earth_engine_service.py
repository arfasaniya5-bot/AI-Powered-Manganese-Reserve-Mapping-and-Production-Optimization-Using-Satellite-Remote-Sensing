"""
Google Earth Engine (GEE) Service
---------------------------------
This service module handles real authentication, initialization, and data retrieval
from Google Earth Engine for multi-spectral Sentinel-2 satellite imagery, SRTM DEM
terrain indices (elevation and slope), and Land Surface Temperature (LST).

IMPORTANT SECURITY NOTICE:
All Google Earth Engine credentials, service account secrets, and private keys MUST
remain strictly on the backend server, loaded from environment variables (.env).
They must NEVER be exposed or passed to the React frontend client.
"""

import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from google.auth.credentials import Credentials as BaseCredentials
from config.settings import settings

try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    ee = None
    EE_AVAILABLE = False


class GCloudCredentials(BaseCredentials):
    """
    Auto-refreshing Google Cloud credentials using local gcloud CLI.
    Automatically obtains a fresh access token whenever Google Auth attempts a refresh,
    preventing 1-hour session expiration and RefreshError.
    """
    def __init__(self):
        super().__init__()
        self.refresh(None)

    def refresh(self, request=None):
        try:
            token = subprocess.check_output("gcloud auth print-access-token", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if not token:
                raise ValueError("Empty token returned by gcloud auth print-access-token")
            self.token = token
            # google-auth uses naive UTC for self.expiry comparison
            self.expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=50)
        except Exception as e:
            raise Exception(f"Failed to refresh gcloud token: {e}")



# ==============================================================================
# METHODOLOGY CONFIGURATION CONSTANTS (SECTIONS 2, 3, 4, 5, 14, 15, 16)
# ==============================================================================
# Centralized configurable parameters for dynamic live observations:
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
LIVE_WINDOW_DAYS = 90              # Rolling observation window duration in days (Section 14)
MAX_CLOUD_PERCENT = 30             # Cloud filter threshold (Section 14)
COMPOSITE_METHOD = "median"        # Temporal composite method (Section 3, 14)
S2_POINT_BUFFER_METERS = 50        # Spatial buffer for point reduction (Section 3, 6)
S2_SCALE_FACTOR = 0.0001           # Exactly 1 / 10000.0 applied once for SR reflectance (Section 3)
S2_PB04_OFFSET = 0.1000            # ESA Processing Baseline 04.00 offset (+1000 DN / 10000)
REDUCER = "mean"                   # Spatial reducer within buffer

# Aliases for backwards compatibility
S2_CLOUDY_PERCENTAGE = MAX_CLOUD_PERCENT
S2_COMPOSITE_REDUCER = COMPOSITE_METHOD

DEM_DATASET = "USGS/SRTMGL1_003"
TERRAIN_POINT_BUFFER_METERS = 200  # Used when coordinates are outside known mines

LST_DATASET = "MODIS/061/MOD11A2"  # MODIS 8-day 1km composite
LST_DEFAULT_WINDOW_DAYS = 365      # Dynamic rolling window for LST observations
LST_POINT_BUFFER_METERS = 1000

# Concession-wide reduction flag: Disabled (False) to match point-level
# reduceRegion extraction methodology used in training dataset generation.
USE_MINE_CONCESSION_BOUNDS_FOR_REGIONAL_TERRAIN = False

# Known mine concession bounding boxes empirically identified from the training dataset
# Format: "Mine_Name": (min_lat, max_lat, min_lon, max_lon)
MINE_CONCESSION_BOUNDS = {
    "Balaghat": (21.8246, 21.8753, 80.1995, 80.2538),
    "Beldongri": (21.3147, 21.3659, 79.2650, 79.3200),
    "Chikla": (21.5176, 21.5684, 79.7265, 79.7813),
    "Dongri_Buzurg": (21.5232, 21.5740, 79.6554, 79.7101),
    "Gumgaon": (21.3720, 21.4234, 78.9456, 79.0012),
    "Kandri": (21.3863, 21.4373, 79.2387, 79.2939),
    "Munsar": (21.3761, 21.4270, 79.2535, 79.3087),
    "Sitapatore": (21.6412, 21.6921, 79.6392, 79.6942),
    "Tirodi": (21.6581, 21.7089, 79.6972, 79.7521),
    "Ukwa": (21.9490, 21.9995, 80.4395, 80.4937),
}


class EarthEngineService:
    """
    Service for real Google Earth Engine operations.
    Handles authentication, Sentinel-2 image extraction, NDVI calculation,
    SRTM DEM elevation & slope reduction, and Land Surface Temperature (LST).
    """

    def __init__(self):
        self.is_initialized: bool = False
        self.auth_error: Optional[str] = None
        self.project_id: str = settings.GEE_PROJECT_ID
        self.service_account: str = settings.GEE_SERVICE_ACCOUNT
        self.private_key: str = settings.GEE_PRIVATE_KEY
        self.service_account_key_path: str = settings.GEE_SERVICE_ACCOUNT_KEY_PATH

        # Automatically attempt initialization on startup
        self.initialize_earth_engine()

    def initialize_earth_engine(self, force_reload: bool = False) -> bool:
        """
        Initializes Google Earth Engine using Service Account credentials or Application Default Credentials.
        Supported credential sources via environment variables:
        1. GEE_SERVICE_ACCOUNT_KEY_PATH: Path to service account JSON key file.
        2. GEE_SERVICE_ACCOUNT + GEE_PRIVATE_KEY: Service account email and private key string.
        3. GEE_PROJECT_ID: Cloud project ID for Earth Engine initialization.
        """
        if self.is_initialized and not force_reload:
            return True
        if force_reload:
            self.is_initialized = False

        if not EE_AVAILABLE:
            self.auth_error = "earthengine-api Python package is not installed."
            self.is_initialized = False
            return False

        # 1. Check if Service Account JSON key file is specified and exists
        if self.service_account_key_path:
            if not os.path.exists(self.service_account_key_path):
                self.auth_error = f"Service account key file not found at: {self.service_account_key_path}"
                self.is_initialized = False
                return False
            try:
                credentials = ee.ServiceAccountCredentials(
                    self.service_account or None,
                    key_file=self.service_account_key_path
                )
                ee.Initialize(credentials, project=self.project_id if self.project_id else None)
                self.is_initialized = True
                self.auth_error = None
                return True
            except Exception as exc:
                self.auth_error = f"GEE authentication failed with key file ({type(exc).__name__}: {str(exc)})"
                self.is_initialized = False
                return False

        # 2. Check if Service Account email and private key string are provided
        if self.service_account and self.private_key:
            try:
                credentials = ee.ServiceAccountCredentials(
                    self.service_account,
                    key_data=self.private_key
                )
                ee.Initialize(credentials, project=self.project_id if self.project_id else None)
                self.is_initialized = True
                self.auth_error = None
                return True
            except Exception as exc:
                self.auth_error = f"GEE authentication failed with service account ({type(exc).__name__}: {str(exc)})"
                self.is_initialized = False
                return False

        # 3. Check if Project ID alone is provided (try standard ADC, then gcloud CLI token)
        if self.project_id:
            # 3a. Standard ee.Initialize with project
            try:
                ee.Initialize(project=self.project_id)
                self.is_initialized = True
                self.auth_error = None
                return True
            except Exception as exc:
                # 3b. Fallback: Check if gcloud CLI has an active credentialed account
                try:
                    credentials = GCloudCredentials()
                    ee.Initialize(credentials=credentials, project=self.project_id)
                    self.is_initialized = True
                    self.auth_error = None
                    return True
                except Exception as gcloud_exc:
                    # Provide the specific error reason from GEE
                    msg = str(gcloud_exc) if "gcloud_exc" in locals() else str(exc)
                    # Clean up long exception strings for readable display
                    if "not registered to use Earth Engine" in msg:
                        self.auth_error = f"Project '{self.project_id}' is not registered with Earth Engine. Register at: https://console.cloud.google.com/earth-engine/configuration?project={self.project_id}"
                    else:
                        self.auth_error = f"GEE authentication failed with project '{self.project_id}' ({type(exc).__name__}: {str(exc)})"
                    self.is_initialized = False
                    return False

                self.auth_error = f"GEE authentication failed with project '{self.project_id}' ({type(exc).__name__}: {str(exc)})"
                self.is_initialized = False
                return False

        # 4. No credentials provided at all
        self.auth_error = "GEE not configured (missing credentials in .env: GEE_PROJECT_ID / GEE_SERVICE_ACCOUNT)"
        self.is_initialized = False
        return False

    def get_mine_concession_region(self, latitude: float, longitude: float) -> Optional[tuple]:
        """
        Checks if coordinates fall within known mine concession bounds from the training dataset.
        If found, returns (mine_name, ee.Geometry.BBox) for regional concession reduction.
        """
        if not USE_MINE_CONCESSION_BOUNDS_FOR_REGIONAL_TERRAIN or not EE_AVAILABLE:
            return None

        for mine_name, (min_lat, max_lat, min_lon, max_lon) in MINE_CONCESSION_BOUNDS.items():
            if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
                return (mine_name, ee.Geometry.BBox(min_lon, min_lat, max_lon, max_lat))
        return None

    def get_dynamic_date_window(self, point: Optional[Any] = None) -> Tuple[str, str, bool, str]:
        """
        Dynamically calculates the current/recent satellite observation window relative
        to the current system/GEE date (Sections 2, 5, 14, 15, 16).
        
        Hierarchy:
        1. Tier 1 (Normal Current Observation):
           Rolling LIVE_WINDOW_DAYS (90 days) ending today.
           If point is provided and collection has >= 3 cloud-free observations, uses this window.
        2. Tier 2 (Seasonal Consistency Fallback):
           Central Indian manganese deposits exhibit bare-ground outcrop signatures in the dry season.
           During rainy/monsoon periods when cloud-free images are scarce (<3) or clouded, falls back
           to the most recent dry season window (Feb 1 - May 31 of current or previous year)
           to maintain bare-ground spectral consistency with the training methodology.
        
        Returns:
            (start_date_str, end_date_str, gee_fallback_used, fallback_reason)
        """
        today = datetime.now().date()
        rolling_start = (today - timedelta(days=LIVE_WINDOW_DAYS)).strftime("%Y-%m-%d")
        rolling_end = today.strftime("%Y-%m-%d")

        # Determine most recent dry-season window (Feb 1 to May 31)
        current_year = today.year
        if today >= datetime(current_year, 5, 31).date():
            dry_start = f"{current_year}-02-01"
            dry_end = f"{current_year}-05-31"
        elif today >= datetime(current_year, 2, 1).date():
            dry_start = f"{current_year}-02-01"
            dry_end = today.strftime("%Y-%m-%d")
        else:
            dry_start = f"{current_year - 1}-02-01"
            dry_end = f"{current_year - 1}-05-31"

        # During Indian monsoon / post-monsoon months (June to October), dense cloud cover
        # and agricultural crop canopy obscure bare-ground rock and manganese absorption signatures.
        # Use the most recent dry season bare-ground composite (Feb 1 - May 31) to maintain
        # spectral consistency with training methodology.
        if today.month in [6, 7, 8, 9, 10]:
            return (
                dry_start,
                dry_end,
                True,
                f"Monsoon period (month {today.month}): bare-ground dry season window ({dry_start} to {dry_end}) "
                f"applied for bare-rock spectral consistency."
            )

        if not point or not EE_AVAILABLE or not self.is_initialized:
            return (rolling_start, rolling_end, False, "Dynamic rolling observation window")

        try:
            rolling_col = (
                ee.ImageCollection(S2_COLLECTION)
                .filterBounds(point)
                .filterDate(rolling_start, rolling_end)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
            )
            count = rolling_col.size().getInfo()

            if count >= 3:
                return (
                    rolling_start,
                    rolling_end,
                    False,
                    f"Dynamic rolling observation window with {count} cloud-free scenes"
                )
            else:
                return (
                    dry_start,
                    dry_end,
                    True,
                    f"Rolling window had insufficient cloud-free observations ({count} < 3). "
                    f"Fell back to most recent dry season window ({dry_start} to {dry_end}) "
                    f"for bare-ground spectral consistency."
                )
        except Exception as exc:
            return (
                dry_start,
                dry_end,
                True,
                f"Image availability query error ({str(exc)}); using recent dry season window ({dry_start} to {dry_end})"
            )

    def get_sentinel2_features(
        self,
        latitude: float,
        longitude: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        buffer_meters: int = S2_POINT_BUFFER_METERS
    ) -> Dict[str, Any]:
        """
        Retrieves real Sentinel-2 surface reflectance bands (B02, B03, B04, B08, B11, B12)
        and computes NDVI = (B08 - B04) / (B08 + B04) for the selected geographic location
        using dynamic observation windows and controlled seasonal fallback (Sections 2, 3, 4, 5, 14, 15, 16).
        """
        if not self.is_initialized:
            # Retry initialization in case credentials were set dynamically
            if not self.initialize_earth_engine():
                return {"error": self.auth_error or "GEE not configured"}

        point = None
        fallback_used = False
        fallback_reason = ""
        try:
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_meters)

            # Resolve observation date window dynamically if not explicitly specified
            if start_date is None or end_date is None:
                start_date, end_date, fallback_used, fallback_reason = self.get_dynamic_date_window(point)

            # Query Copernicus Sentinel-2 Surface Reflectance Harmonized
            s2_collection = (
                ee.ImageCollection(S2_COLLECTION)
                .filterBounds(point)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
            )

            # Composite using median reducer across multi-spectral bands
            # Band mapping: B2=Blue, B3=Green, B4=Red, B8=NIR, B11=SWIR1, B12=SWIR2
            bands = ["B2", "B3", "B4", "B8", "B11", "B12"]
            composite = s2_collection.select(bands).median()

            # Reduce region to retrieve pixel values at target location
            reduced = composite.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=10,
                maxPixels=1000000
            ).getInfo()

            if not reduced or reduced.get("B2") is None:
                # Tier 3 fallback: broaden cloud threshold to 60%
                s2_fallback = (
                    ee.ImageCollection(S2_COLLECTION)
                    .filterBounds(point)
                    .filterDate(start_date, end_date)
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
                )
                composite_fb = s2_fallback.select(bands).median()
                reduced = composite_fb.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=region,
                    scale=10,
                    maxPixels=1000000
                ).getInfo()
                if reduced and reduced.get("B2") is not None:
                    fallback_used = True
                    fallback_reason = f"Expanded cloud filter (60%) required for date window {start_date} to {end_date}"

            if not reduced or reduced.get("B2") is None:
                return {
                    "error": "Sentinel-2 pixel reduction returned empty values for this coordinate",
                    "start_date": start_date,
                    "end_date": end_date,
                    "s2_collection": S2_COLLECTION,
                    "cloud_filter": f"CLOUDY_PIXEL_PERCENTAGE < {MAX_CLOUD_PERCENT}",
                    "composite_method": COMPOSITE_METHOD,
                    "buffer_meters": buffer_meters,
                    "reducer": REDUCER,
                    "scale_factor": S2_SCALE_FACTOR,
                    "gee_fallback_used": fallback_used,
                    "fallback_reason": fallback_reason or "Insufficient cloud-free pixels"
                }

            # Sentinel-2 Harmonized surface reflectance is scaled by 10000 (0.0001 factor)
            def scale_band(val):
                if val is None:
                    return None
                # +0.1000 reflectance offset restores equivalence with
                # COPERNICUS/S2_SR (unharmonized), which is what the training dataset
                # was generated from. S2_SR_HARMONIZED subtracts the ESA Processing
                # Baseline 04.00 +1000 DN offset; this adds it back so live features
                # match the training methodology.
                raw_reflectance = float(val) * S2_SCALE_FACTOR
                return round(raw_reflectance + S2_PB04_OFFSET, 4)

            b02 = scale_band(reduced.get("B2"))
            b03 = scale_band(reduced.get("B3"))
            b04 = scale_band(reduced.get("B4"))
            b08 = scale_band(reduced.get("B8"))
            b11 = scale_band(reduced.get("B11"))
            b12 = scale_band(reduced.get("B12"))

            # Calculate NDVI from actual NIR (B08) and Red (B04) reflectance
            ndvi = None
            if b08 is not None and b04 is not None and (b08 + b04) != 0:
                ndvi = round((b08 - b04) / (b08 + b04), 4)

            return {
                "B02": b02,
                "B03": b03,
                "B04": b04,
                "B08": b08,
                "B11": b11,
                "B12": b12,
                "NDVI": ndvi,
                "start_date": start_date,
                "end_date": end_date,
                "s2_collection": S2_COLLECTION,
                "cloud_filter": f"CLOUDY_PIXEL_PERCENTAGE < {MAX_CLOUD_PERCENT}",
                "composite_method": COMPOSITE_METHOD,
                "buffer_meters": buffer_meters,
                "reducer": REDUCER,
                "scale_factor": S2_SCALE_FACTOR,
                "gee_fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "error": None
            }
        except Exception as exc:
            return {
                "error": f"GEE Sentinel-2 retrieval failed ({type(exc).__name__}: {str(exc)})",
                "start_date": start_date,
                "end_date": end_date,
                "s2_collection": S2_COLLECTION,
                "cloud_filter": f"CLOUDY_PIXEL_PERCENTAGE < {MAX_CLOUD_PERCENT}",
                "composite_method": COMPOSITE_METHOD,
                "buffer_meters": buffer_meters,
                "reducer": REDUCER,
                "scale_factor": S2_SCALE_FACTOR,
                "gee_fallback_used": fallback_used,
                "fallback_reason": fallback_reason
            }

    def get_terrain_features(
        self,
        latitude: float,
        longitude: float,
        buffer_meters: int = TERRAIN_POINT_BUFFER_METERS
    ) -> Dict[str, Any]:
        """
        Retrieves real elevation (SRTM GL1 30m DEM) and computes slope in degrees.
        If coordinates fall within a known mine concession, reduces across the concession AOI
        to replicate the training dataset methodology where terrain metrics are concession-level.
        Otherwise falls back to a localized buffer around the point.
        """
        if not self.is_initialized:
            if not self.initialize_earth_engine():
                return {"error": self.auth_error or "GEE not configured"}

        try:
            point = ee.Geometry.Point([longitude, latitude])
            concession_info = self.get_mine_concession_region(latitude, longitude)
            if concession_info is not None:
                mine_name, region = concession_info
            else:
                region = point.buffer(buffer_meters)

            # USGS SRTM GL1 30m Global DEM & Slope combined in single GEE operation
            dem = ee.Image(DEM_DATASET).select(["elevation"])
            slope = ee.Terrain.slope(dem).select(["slope"])
            terrain_img = ee.Image.cat([dem, slope])

            combined_reducer = ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True)

            stats = terrain_img.reduceRegion(
                reducer=combined_reducer,
                geometry=region,
                scale=30,
                maxPixels=10000000
            ).getInfo()

            def extract_stat(stats_dict, prefix):
                if not stats_dict:
                    return None, None, None
                mean_v = stats_dict.get(f"{prefix}_mean")
                min_v = stats_dict.get(f"{prefix}_min")
                max_v = stats_dict.get(f"{prefix}_max")
                return (
                    round(float(mean_v), 2) if mean_v is not None else None,
                    round(float(min_v), 2) if min_v is not None else None,
                    round(float(max_v), 2) if max_v is not None else None,
                )

            elev_mean, elev_min, elev_max = extract_stat(stats, "elevation")
            slope_mean, slope_min, slope_max = extract_stat(stats, "slope")

            return {
                "elevation_mean_m": elev_mean,
                "elevation_min_m": elev_min,
                "elevation_max_m": elev_max,
                "slope_mean_degrees": slope_mean,
                "slope_min_degrees": slope_min,
                "slope_max_degrees": slope_max,
                "error": None
            }
        except Exception as exc:
            return {"error": f"GEE SRTM DEM retrieval failed ({type(exc).__name__}: {str(exc)})"}

    def get_lst_features(
        self,
        latitude: float,
        longitude: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        buffer_meters: int = LST_POINT_BUFFER_METERS
    ) -> Dict[str, Any]:
        """
        Retrieves real Land Surface Temperature (LST) from MODIS 8-day 1km composite (MOD11A2),
        scales the raw sensor Kelvin values to degrees Celsius, and reduces Mean, Min, Max.
        Dynamically calculates rolling observation window relative to current date (Sections 2, 14).
        If coordinates fall within a known mine concession, reduces across the concession AOI.
        """
        if not self.is_initialized:
            if not self.initialize_earth_engine():
                return {"error": self.auth_error or "GEE not configured"}

        today = datetime.now().date()
        point = ee.Geometry.Point([longitude, latitude])
        fallback_used = False
        fallback_reason = ""

        # Remove standalone 365-day annual window logic. Use the same dynamic dry-season window
        # as Sentinel-2 feature generation. If dates are not explicitly passed, dynamically resolve
        # them via get_dynamic_date_window(point).
        if start_date is None or end_date is None:
            start_date, end_date, fallback_used, fallback_reason = self.get_dynamic_date_window(point)

        try:
            concession_info = self.get_mine_concession_region(latitude, longitude)
            if concession_info is not None:
                mine_name, region = concession_info
            else:
                region = point.buffer(buffer_meters)

            # MODIS Terra Land Surface Temperature and Emissivity 8-Day Global 1km
            modis_col = (
                ee.ImageCollection(LST_DATASET)
                .filterBounds(point)
                .filterDate(start_date, end_date)
                .select("LST_Day_1km")
            )

            composite = modis_col.median()
            # LST_Day_1km scale factor is 0.02 (Kelvin). Subtract 273.15 to convert to Celsius.
            lst_celsius = composite.multiply(0.02).subtract(273.15)

            combined_reducer = ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True)
            stats = lst_celsius.reduceRegion(
                reducer=combined_reducer,
                geometry=region,
                scale=1000,
                maxPixels=10000000
            ).getInfo()

            if not stats or stats.get("LST_Day_1km_mean") is None:
                # Try wider rolling 3-year date range if initial recent window yielded no observations
                fallback_start = (today - timedelta(days=365 * 3)).strftime("%Y-%m-%d")
                modis_fallback = (
                    ee.ImageCollection(LST_DATASET)
                    .filterBounds(point)
                    .filterDate(fallback_start, end_date)
                    .select("LST_Day_1km")
                )
                composite_fb = modis_fallback.median()
                lst_celsius_fb = composite_fb.multiply(0.02).subtract(273.15)
                stats = lst_celsius_fb.reduceRegion(
                    reducer=combined_reducer,
                    geometry=region,
                    scale=1000,
                    maxPixels=10000000
                ).getInfo()

            if not stats or stats.get("LST_Day_1km_mean") is None:
                return {"error": "MODIS LST pixel reduction returned empty values for this coordinate"}

            mean_v = stats.get("LST_Day_1km_mean")
            min_v = stats.get("LST_Day_1km_min")
            max_v = stats.get("LST_Day_1km_max")

            return {
                "LST_mean_C": round(float(mean_v), 2) if mean_v is not None else None,
                "LST_min_C": round(float(min_v), 2) if min_v is not None else None,
                "LST_max_C": round(float(max_v), 2) if max_v is not None else None,
                "start_date": start_date,
                "end_date": end_date,
                "error": None
            }
        except Exception as exc:
            return {"error": f"GEE MODIS LST retrieval failed ({type(exc).__name__}: {str(exc)})"}

    def generate_map_tile_url(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Generates dynamic XYZ map tile URL template via Earth Engine `image.getMapId()`.
        Used to feed satellite raster layers directly into Leaflet TileLayer.
        """
        if not self.is_initialized:
            return None

        try:
            point = ee.Geometry.Point([longitude, latitude])
            s2 = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(point)
                .filterDate("2023-01-01", "2024-01-01")
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
                .median()
            )
            # Natural Color visualization (Red: B4, Green: B3, Blue: B2)
            vis_image = s2.visualize(bands=["B4", "B3", "B2"], min=0, max=3000)
            map_id_dict = ee.data.getMapId({"image": vis_image})
            return map_id_dict.get("tile_fetcher", {}).url_format
        except Exception:
            return None


# Export singleton instance for reuse across the backend
earth_engine_service = EarthEngineService()
