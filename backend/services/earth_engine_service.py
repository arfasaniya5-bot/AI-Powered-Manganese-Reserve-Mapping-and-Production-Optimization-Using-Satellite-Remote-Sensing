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
from typing import Dict, Any, Optional
from config.settings import settings

try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    ee = None
    EE_AVAILABLE = False


# ==============================================================================
# METHODOLOGY CONFIGURATION CONSTANTS
# ==============================================================================
# CONFIRMED METHODOLOGY:
# - Sentinel-2 Collection: COPERNICUS/S2_SR_HARMONIZED (confirmed: backend/services/earth_engine_service.py:159)
# - DEM Dataset: USGS/SRTMGL1_003 (confirmed: backend/services/earth_engine_service.py:247)
# - Spectral Bands: B02, B03, B04, B08, B11, B12, NDVI formula (confirmed: feature_columns.json, train_model.py:91-100)
#
# UNCONFIRMED / PENDING TEAMMATE INPUT (TODO: UNCONFIRMED_METHODOLOGY):
# - S2 Composite Date Range: Uses pre-monsoon dry season (Feb 15 - May 31)
#   matching the bare-ground / un-vegetated outcrop spectral signature of the training dataset.
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
S2_DEFAULT_START_DATE = "2023-02-15"  # Dry season (pre-monsoon) window matching bare-earth signature
S2_DEFAULT_END_DATE = "2023-05-31"    # Avoids monsoon wet-season vegetative canopy bloom
S2_CLOUDY_PERCENTAGE = 30             # Cloud filter percentage
S2_COMPOSITE_REDUCER = "median"       # Composite reducer
S2_POINT_BUFFER_METERS = 50           # Point reduction buffer
S2_SCALE_FACTOR = 0.0001              # Exactly 1 / 10000.0 applied once for SR reflectance

DEM_DATASET = "USGS/SRTMGL1_003"
TERRAIN_POINT_BUFFER_METERS = 200     # TODO: UNCONFIRMED_METHODOLOGY - Used when coordinates are outside known mines

LST_DATASET = "MODIS/061/MOD11A2"     # TODO: UNCONFIRMED_METHODOLOGY - MODIS 1km vs Landsat 8 ST unconfirmed in repo
LST_DEFAULT_START_DATE = "2023-01-01" # TODO: UNCONFIRMED_METHODOLOGY
LST_DEFAULT_END_DATE = "2024-01-01"   # TODO: UNCONFIRMED_METHODOLOGY
LST_POINT_BUFFER_METERS = 1000        # TODO: UNCONFIRMED_METHODOLOGY

# Concession-wide reduction flag: In the training dataset, Elevation and LST metrics
# were computed at the mine concession level (all rows in a mine share identical values).
# When enabled, coordinates falling within known mine concession bounds use the concession AOI.
USE_MINE_CONCESSION_BOUNDS_FOR_REGIONAL_TERRAIN = True

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

    def initialize_earth_engine(self) -> bool:
        """
        Initializes Google Earth Engine using Service Account credentials or Application Default Credentials.
        Supported credential sources via environment variables:
        1. GEE_SERVICE_ACCOUNT_KEY_PATH: Path to service account JSON key file.
        2. GEE_SERVICE_ACCOUNT + GEE_PRIVATE_KEY: Service account email and private key string.
        3. GEE_PROJECT_ID: Cloud project ID for Earth Engine initialization.
        """
        if self.is_initialized:
            return True

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
                    import subprocess
                    from google.oauth2.credentials import Credentials
                    token = subprocess.check_output("gcloud auth print-access-token", shell=True).decode().strip()
                    if token:
                        credentials = Credentials(token)
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

    def get_sentinel2_features(
        self,
        latitude: float,
        longitude: float,
        start_date: str = S2_DEFAULT_START_DATE,
        end_date: str = S2_DEFAULT_END_DATE,
        buffer_meters: int = S2_POINT_BUFFER_METERS
    ) -> Dict[str, Any]:
        """
        Retrieves real Sentinel-2 surface reflectance bands (B02, B03, B04, B08, B11, B12)
        and computes NDVI = (B08 - B04) / (B08 + B04) for the selected geographic location.
        """
        if not self.is_initialized:
            # Retry initialization in case credentials were set dynamically
            if not self.initialize_earth_engine():
                return {"error": self.auth_error or "GEE not configured"}

        try:
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(buffer_meters)

            # Query Copernicus Sentinel-2 Surface Reflectance Harmonized
            s2_collection = (
                ee.ImageCollection(S2_COLLECTION)
                .filterBounds(point)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", S2_CLOUDY_PERCENTAGE))
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
                # Broaden search to wider cloud filter and dates if initial query returned empty
                s2_fallback = (
                    ee.ImageCollection(S2_COLLECTION)
                    .filterBounds(point)
                    .filterDate("2022-01-01", "2024-12-31")
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
                )
                composite_fb = s2_fallback.select(bands).median()
                reduced = composite_fb.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=region,
                    scale=10,
                    maxPixels=1000000
                ).getInfo()

            if not reduced or reduced.get("B2") is None:
                return {"error": "Sentinel-2 pixel reduction returned empty values for this coordinate"}

            # Sentinel-2 Harmonized surface reflectance is scaled by 10000 (0.0001 factor)
            def scale_band(val):
                if val is None:
                    return None
                return round(float(val) / 10000.0, 4)

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
                "error": None
            }
        except Exception as exc:
            return {"error": f"GEE Sentinel-2 retrieval failed ({type(exc).__name__}: {str(exc)})"}

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
        start_date: str = LST_DEFAULT_START_DATE,
        end_date: str = LST_DEFAULT_END_DATE,
        buffer_meters: int = LST_POINT_BUFFER_METERS
    ) -> Dict[str, Any]:
        """
        Retrieves real Land Surface Temperature (LST) from MODIS 8-day 1km composite (MOD11A2),
        scales the raw sensor Kelvin values to degrees Celsius, and reduces Mean, Min, Max.
        If coordinates fall within a known mine concession, reduces across the concession AOI.
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
                # Try wider date range if initial window yielded no observations
                modis_fallback = (
                    ee.ImageCollection(LST_DATASET)
                    .filterBounds(point)
                    .filterDate("2022-01-01", "2024-12-31")
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
