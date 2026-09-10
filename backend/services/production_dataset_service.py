"""
Production Dataset Service
--------------------------
Handles loading, caching, column inspection, and retrieval for the four production datasets:
1. Mining Equipment Failure Data (mining_equipment_failure_data.xlsx / .csv)
2. MOIL Historical Production Prototype (moil_historical_production_prototype.xlsx / .csv)
3. MOIL Weather & Soil 2025 (moil_weather_soil_2025.xlsx / .csv)
4. MWD Rock Type & Blast-Holes Model Ready (mwd_rocktype_blastholes_model_ready_training.xlsx / .csv)

Features:
- Supports both Excel (.xlsx, .xls via openpyxl) and CSV (.csv) formats.
- Caches DataFrames in memory to avoid repeated disk reads.
- Safely handles missing values for JSON serialization.
- Converts date columns to standard ISO format strings.
- Emits required terminal logs upon loading datasets.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Base directory pointing to backend/data/production
PRODUCTION_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "production"

# Dataset definitions with potential file candidates
DATASET_DEFINITIONS = {
    "equipment_failure": {
        "name": "Mining Equipment Failure Data",
        "primary_filename": "mining_equipment_failure_data.xlsx",
        "candidates": [
            "mining_equipment_failure_data.xlsx",
            "mining_equipment_failure_data.csv"
        ],
        "date_columns": ["event_date"],
        "target_columns": ["downtime_hours", "production_loss_tonnes", "repair_cost_usd", "failure_mode", "severity"]
    },
    "historical_production": {
        "name": "MOIL Historical Production Prototype",
        "primary_filename": "moil_historical_production_prototype.xlsx",
        "candidates": [
            "moil_historical_production_prototype.xlsx",
            "moil_historical_production_prototype.csv"
        ],
        "date_columns": ["Date"],
        "target_columns": ["Planned_Production_Tonnes", "Actual_Production_Tonnes", "Production_Shortfall_Tonnes", "Shortfall_Percentage", "Shortfall_Risk"]
    },
    "weather_soil": {
        "name": "MOIL Weather & Soil 2025",
        "primary_filename": "moil_weather_soil_2025.xlsx",
        "candidates": [
            "moil_weather_soil_2025.xlsx",
            "moil_weather_soil_2025.csv"
        ],
        "date_columns": ["Date"],
        "target_columns": ["Temperature_C", "Precipitation_mm", "Wind_Speed_m_s", "Soil_Moisture_0_100cm"]
    },
    "rocktype_blastholes": {
        "name": "MWD Rock Type & Blast-Holes Model Ready",
        "primary_filename": "mwd_rocktype_blastholes_model_ready_training.xlsx",
        "candidates": [
            "mwd_rocktype_blastholes_model_ready_training.xlsx",
            "mwd_rocktype_blastholes_model_ready_training.csv",
            "mwd_rocktype_blastholes_model_ready_train.xlsx",
            "mwd_rocktype_blastholes_model_ready_train.csv"
        ],
        "date_columns": [],
        "target_columns": ["Rock", "transition_zone", "round_length"]
    }
}


class ProductionDatasetService:
    """
    Singleton service managing the lifecycle, inspection, and memory-caching
    of production datasets.
    """

    def __init__(self):
        self._cached_dfs: Dict[str, pd.DataFrame] = {}
        self._resolved_paths: Dict[str, Path] = {}
        self._dataset_metadata: Dict[str, Dict[str, Any]] = {}
        # Pre-scan and resolve paths on initialization
        self._scan_and_resolve_files()

    def _scan_and_resolve_files(self):
        """Scans the production data folder to locate existing dataset files."""
        for key, defn in DATASET_DEFINITIONS.items():
            resolved = None
            for candidate in defn["candidates"]:
                candidate_path = PRODUCTION_DATA_DIR / candidate
                if candidate_path.exists() and candidate_path.is_file():
                    resolved = candidate_path
                    break
            if resolved:
                self._resolved_paths[key] = resolved

    def _print_dataset_status(self, key: str, df: pd.DataFrame, file_path: Path):
        """Prints standardized terminal status log per project specification."""
        defn = DATASET_DEFINITIONS.get(key, {})
        target_cols = [c for c in defn.get("target_columns", []) if c in df.columns]
        missing_count = int(df.isnull().sum().sum())

        print("\n" + "=" * 50)
        print("PRODUCTION DATASET STATUS")
        print(f"Dataset key:               {key}")
        print(f"Dataset name:              {defn.get('name', key)}")
        print(f"File path:                 {file_path}")
        print(f"Number of records:         {len(df)}")
        print(f"Number of columns:         {len(df.columns)}")
        print(f"Available target columns:  {', '.join(target_cols) if target_cols else 'None'}")
        print(f"Missing values:            {missing_count}")
        print("Dataset loaded successfully: True")
        print("=" * 50 + "\n")

    def load_dataset(self, key: str, force_reload: bool = False) -> Optional[pd.DataFrame]:
        """
        Loads and caches a dataset by key.
        Supports both Excel (.xlsx, .xls) and CSV (.csv).
        """
        if not force_reload and key in self._cached_dfs:
            return self._cached_dfs[key]

        if key not in DATASET_DEFINITIONS:
            raise ValueError(f"Unknown dataset key: '{key}'. Available: {list(DATASET_DEFINITIONS.keys())}")

        file_path = self._resolved_paths.get(key)
        if not file_path or not file_path.exists():
            # Try rescanning
            self._scan_and_resolve_files()
            file_path = self._resolved_paths.get(key)

        if not file_path or not file_path.exists():
            defn = DATASET_DEFINITIONS[key]
            expected = defn["primary_filename"]
            raise FileNotFoundError(
                f"Production dataset '{defn['name']}' not found in {PRODUCTION_DATA_DIR}. Expected file: {expected}"
            )

        try:
            if file_path.suffix.lower() in [".xlsx", ".xls"]:
                # Load Excel via openpyxl engine
                df = pd.read_excel(file_path, engine="openpyxl")
            else:
                # Load CSV
                df = pd.read_csv(file_path)

            # Standardize date columns if present
            defn = DATASET_DEFINITIONS[key]
            for date_col in defn.get("date_columns", []):
                if date_col in df.columns:
                    try:
                        df[date_col] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass

            # Cache the DataFrame
            self._cached_dfs[key] = df

            # Cache metadata
            self._dataset_metadata[key] = {
                "key": key,
                "name": defn["name"],
                "filename": file_path.name,
                "file_format": file_path.suffix.lower(),
                "file_path": str(file_path),
                "exists": True,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns),
                "date_columns": [c for c in defn.get("date_columns", []) if c in df.columns],
                "target_columns": [c for c in defn.get("target_columns", []) if c in df.columns],
                "missing_values_count": int(df.isnull().sum().sum()),
            }

            # Emit terminal status log
            self._print_dataset_status(key, df, file_path)

            return df
        except Exception as exc:
            raise RuntimeError(f"Failed to read production dataset '{key}' from {file_path}: {exc}") from exc

    def get_dataset(self, key: str) -> pd.DataFrame:
        """Retrieves a cached DataFrame, loading it if not already loaded."""
        return self.load_dataset(key)

    def get_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """Loads and returns all 4 production datasets."""
        result = {}
        for key in DATASET_DEFINITIONS:
            try:
                result[key] = self.load_dataset(key)
            except Exception as e:
                print(f"[WARN] Could not load dataset '{key}': {e}")
        return result

    def get_metadata(self, key: str) -> Dict[str, Any]:
        """Retrieves metadata for a specific dataset."""
        if key not in self._dataset_metadata:
            self.load_dataset(key)
        return self._dataset_metadata.get(key, {})

    def get_all_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Retrieves metadata for all configured production datasets."""
        for key in DATASET_DEFINITIONS:
            if key not in self._dataset_metadata:
                try:
                    self.load_dataset(key)
                except Exception:
                    file_path = self._resolved_paths.get(key)
                    defn = DATASET_DEFINITIONS[key]
                    self._dataset_metadata[key] = {
                        "key": key,
                        "name": defn["name"],
                        "filename": file_path.name if file_path else defn["primary_filename"],
                        "file_format": file_path.suffix.lower() if file_path else "unknown",
                        "file_path": str(file_path) if file_path else "Not found",
                        "exists": bool(file_path and file_path.exists()),
                        "total_rows": 0,
                        "total_columns": 0,
                        "columns": [],
                        "date_columns": [],
                        "target_columns": [],
                        "missing_values_count": 0,
                    }
        return self._dataset_metadata

    def get_columns_info(self, key: str) -> List[Dict[str, Any]]:
        """Returns detailed column inspection including dtype, null count, and sample values."""
        df = self.get_dataset(key)
        columns_info = []
        for col in df.columns:
            series = df[col]
            nulls = int(series.isnull().sum())
            non_null_samples = series.dropna().head(3).tolist()
            # Clean sample values for JSON serialization
            cleaned_samples = []
            for val in non_null_samples:
                if isinstance(val, (np.integer, int)):
                    cleaned_samples.append(int(val))
                elif isinstance(val, (np.floating, float)):
                    cleaned_samples.append(round(float(val), 4))
                elif isinstance(val, (bool, np.bool_)):
                    cleaned_samples.append(bool(val))
                else:
                    cleaned_samples.append(str(val))

            columns_info.append({
                "name": col,
                "data_type": str(series.dtype),
                "null_count": nulls,
                "sample_values": cleaned_samples,
            })
        return columns_info

    def get_records(
        self,
        key: str,
        limit: int = 50,
        offset: int = 0,
        mine_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Returns paginated, JSON-safe records from a dataset."""
        df = self.get_dataset(key)

        # Apply optional mine filtering if dataset has a 'Mine' column
        if mine_filter and isinstance(mine_filter, str) and "Mine" in df.columns:
            df = df[df["Mine"].astype(str).str.lower() == mine_filter.strip().lower()]

        total = len(df)
        sliced = df.iloc[offset : offset + limit]

        # Convert to dictionary with safe handling for NaN / infinite values
        records = []
        for row in sliced.to_dict(orient="records"):
            clean_row = {}
            for k, v in row.items():
                if pd.isna(v):
                    clean_row[k] = None
                elif isinstance(v, (np.floating, float)):
                    clean_row[k] = round(float(v), 4)
                elif isinstance(v, (np.integer, int)):
                    clean_row[k] = int(v)
                elif isinstance(v, (np.bool_, bool)):
                    clean_row[k] = bool(v)
                else:
                    clean_row[k] = str(v)
            records.append(clean_row)

        return {
            "dataset_key": key,
            "dataset_name": DATASET_DEFINITIONS[key]["name"],
            "total_records": total,
            "limit": limit,
            "offset": offset,
            "records": records,
        }


# Singleton export instance
production_dataset_service = ProductionDatasetService()
