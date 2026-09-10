"""
Dataset Service Module
----------------------
Manages safe, modular, read-only access to `backend/data/manganese_estimation_dataset.csv`.

Strict Constraints Adhered To:
- The dataset file is strictly READ-ONLY.
- No values, columns, or rows inside the CSV are modified or overwritten.
- No duplicate copies of the dataset are created.
- The dataset is NOT used as a runtime prediction lookup (no data leakage).
- Provides summary metadata and reference training information for future ML modeling.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Path to the dataset inside backend/data
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATASET_PATH = DATA_DIR / "manganese_estimation_dataset.csv"


class DatasetService:
    """
    Modular, read-only service for manganese estimation training/reference data.
    """

    def __init__(self, dataset_path: Path = DATASET_PATH):
        self.dataset_path = dataset_path
        self._df: Optional[pd.DataFrame] = None
        self._is_loaded: bool = False
        self._summary: Optional[Dict[str, Any]] = None

    def _load_dataset(self) -> bool:
        """
        Safely loads the dataset from disk into memory once.
        Ensures read-only access and avoids repeated I/O on every request.
        """
        if self._is_loaded and self._df is not None:
            return True

        if not self.dataset_path.exists():
            return False

        try:
            # Read CSV safely without modifying original file
            self._df = pd.read_csv(self.dataset_path)
            self._is_loaded = True
            self._generate_summary()
            return True
        except Exception as e:
            self._is_loaded = False
            return False

    def _generate_summary(self):
        """
        Calculates read-only metadata summary of the dataset.
        """
        if self._df is None:
            return

        cols = list(self._df.columns)
        dtypes = {col: str(dtype) for col, dtype in self._df.dtypes.items()}
        mines = [str(m) for m in self._df["Mine"].dropna().unique().tolist()] if "Mine" in self._df else []

        presence_counts = {}
        if "Manganese_Presence" in self._df:
            presence_counts = self._df["Manganese_Presence"].value_counts().to_dict()

        self._summary = {
            "file_name": self.dataset_path.name,
            "total_rows": int(len(self._df)),
            "total_columns": int(len(cols)),
            "columns": cols,
            "data_types": dtypes,
            "unique_mines": mines,
            "manganese_presence_distribution": {
                "positive_samples": int(presence_counts.get(1, 0)),
                "negative_samples": int(presence_counts.get(0, 0)),
            },
            "status": "Ready for ML training pipeline"
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns structural overview of the dataset without exposing full data.
        """
        if not self._is_loaded:
            self._load_dataset()

        if self._summary:
            return self._summary

        return {
            "file_name": self.dataset_path.name,
            "status": "Dataset not loaded",
            "exists": self.dataset_path.exists()
        }

    def get_feature_columns(self) -> List[str]:
        """
        Returns the independent remote-sensing, geological, terrain,
        and environmental feature columns expected by the ML model.
        Excludes targets and identifiers (Mine, Manganese_Presence, Distance_to_Manganese_km).
        """
        return [
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

    def lookup_reference_record(self, latitude: float, longitude: float, tolerance_degrees: float = 0.05) -> Optional[Dict[str, Any]]:
        """
        Reference lookup: Checks if coordinates fall near any historical survey point
        in the training dataset.
        
        IMPORTANT: This is provided purely as historical reference data and is NOT
        used as an AI/ML prediction or runtime substitute for satellite analysis.
        """
        if not self._load_dataset() or self._df is None:
            return None

        # Filter within bounding box
        nearby = self._df[
            (self._df["Latitude"] >= latitude - tolerance_degrees) &
            (self._df["Latitude"] <= latitude + tolerance_degrees) &
            (self._df["Longitude"] >= longitude - tolerance_degrees) &
            (self._df["Longitude"] <= longitude + tolerance_degrees)
        ]

        if nearby.empty:
            return None

        # Compute Euclidean distance to find closest reference point
        distances = np.sqrt(
            (nearby["Latitude"] - latitude) ** 2 +
            (nearby["Longitude"] - longitude) ** 2
        )
        closest_idx = distances.idxmin()
        closest_row = nearby.loc[closest_idx].to_dict()

        # Clean NaN values for JSON serialization
        cleaned = {k: (None if pd.isna(v) else v) for k, v in closest_row.items()}
        return cleaned

    def find_nearest_dataset_record(
        self, latitude: float, longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Finds the nearest training dataset record to the entered coordinates.
        Calculates exact Euclidean and spherical distance in meters,
        and determines whether the comparison is exact or nearby.
        Does not alter or replace user coordinates.
        """
        if not self._load_dataset() or self._df is None:
            return None

        d_lat = self._df["Latitude"] - latitude
        d_lon = (self._df["Longitude"] - longitude) * np.cos(np.radians(latitude))
        dist_sq = d_lat ** 2 + d_lon ** 2
        min_idx = dist_sq.idxmin()
        closest_row = self._df.loc[min_idx].to_dict()

        dist_deg = float(np.sqrt(dist_sq.loc[min_idx]))
        dist_meters = float(dist_deg * 111320.0)
        is_exact = dist_meters < 1.0

        cleaned = {k: (None if pd.isna(v) else v) for k, v in closest_row.items()}
        return {
            "record": cleaned,
            "nearest_latitude": cleaned.get("Latitude"),
            "nearest_longitude": cleaned.get("Longitude"),
            "distance_degrees": dist_deg,
            "distance_meters": dist_meters,
            "is_exact": is_exact,
            "comparison_type": "Exact match (< 1m)" if is_exact else f"Nearby record (~{dist_meters:.1f}m away)"
        }

    def get_reference_mines(self) -> List[Dict[str, Any]]:
        """
        Returns reference centroids of known mines present in the dataset.
        """
        if not self._load_dataset() or self._df is None or "Mine" not in self._df:
            return []

        mines_grouped = self._df.groupby("Mine").agg({
            "Latitude": "mean",
            "Longitude": "mean",
            "Manganese_Presence": "count"
        }).reset_index()

        mines_grouped.rename(columns={"Manganese_Presence": "sample_count"}, inplace=True)
        return mines_grouped.to_dict(orient="records")


# Export singleton instance
dataset_service = DatasetService()
