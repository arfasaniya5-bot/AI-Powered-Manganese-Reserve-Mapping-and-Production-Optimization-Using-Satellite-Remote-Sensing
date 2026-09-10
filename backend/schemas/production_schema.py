"""
Production Analysis Pydantic Schemas
------------------------------------
Defines request and response models for the Production Shortfall & Analysis module.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    name: str = Field(..., description="Human-readable dataset display name")
    key: str = Field(..., description="Unique dataset key identifier")
    filename: str = Field(..., description="Filename on disk")
    file_format: str = Field(..., description="File format (.csv or .xlsx)")
    file_path: str = Field(..., description="Path to dataset on disk")
    exists: bool = Field(..., description="Whether the file exists on disk")
    total_rows: int = Field(..., description="Total row count")
    total_columns: int = Field(..., description="Total column count")
    columns: List[str] = Field(..., description="List of column names")
    date_columns: List[str] = Field(default_factory=list, description="Identified date/time columns")
    target_columns: List[str] = Field(default_factory=list, description="Primary production/target columns")
    missing_values_count: int = Field(default=0, description="Total missing values across dataset")


class ProductionHealthResponse(BaseModel):
    status: str = Field("ok", description="Health status")
    module: str = Field("production_analysis", description="Module identifier")
    datasets_available: int = Field(..., description="Number of successfully loaded datasets")
    total_datasets: int = Field(4, description="Expected dataset count")
    message: str = Field(..., description="Informational message")


class ProductionDatasetsResponse(BaseModel):
    success: bool = True
    datasets: Dict[str, DatasetMetadata] = Field(..., description="Metadata dictionary keyed by dataset key")


class ProductionSummaryResponse(BaseModel):
    success: bool = True
    summary: Dict[str, Any] = Field(..., description="Aggregated production, equipment, and environmental metrics")


class DatasetColumnInfo(BaseModel):
    name: str
    data_type: str
    null_count: int
    sample_values: List[Any] = Field(default_factory=list)


class DatasetColumnsResponse(BaseModel):
    success: bool = True
    dataset_key: str
    dataset_name: str
    total_columns: int
    columns: List[DatasetColumnInfo]


class DatasetRecordsResponse(BaseModel):
    success: bool = True
    dataset_key: str
    dataset_name: str
    total_records: int
    limit: int
    offset: int
    records: List[Dict[str, Any]]


class ProductionShortfallPredictionRequest(BaseModel):
    mine: Optional[str] = Field("Balaghat", description="Mine / site name")
    date: Optional[str] = Field("2026-09-14", description="Selected forecast date")
    target_production: Optional[float] = Field(10000.0, description="Target production in tonnes")
    planned_production_tonnes: Optional[float] = Field(None, description="Alias for target_production")
    region: Optional[str] = Field("Madhya Pradesh", description="Geographic region / state")
    recent_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Recent actual production records")
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    temperature: Optional[float] = Field(None, description="Temperature alias")
    wind_speed_m_s: Optional[float] = Field(None, description="Wind speed in m/s")
    wind_speed: Optional[float] = Field(None, description="Wind speed alias")
    relative_humidity_percent: Optional[float] = Field(None, description="Relative humidity %")
    humidity: Optional[float] = Field(None, description="Relative humidity alias")
    precipitation_mm: Optional[float] = Field(None, description="Precipitation in mm")
    precipitation: Optional[float] = Field(None, description="Precipitation alias")
    soil_moisture_0_100cm: Optional[float] = Field(None, description="Soil moisture ratio (0-100cm)")
    soil_moisture: Optional[float] = Field(None, description="Soil moisture alias")
    blasting_file_name: Optional[str] = Field(None, description="Uploaded blasting file name")
    geological_file_name: Optional[str] = Field(None, description="Uploaded geological file name")
    equipment_file_name: Optional[str] = Field(None, description="Uploaded equipment file name")
    weather_file_name: Optional[str] = Field(None, description="Uploaded weather file name")
    geological_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom geological / blast-hole CSV features")
    equipment_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom equipment status / failure features")
    additional_features: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional custom features")


class ProductionShortfallPredictionResponse(BaseModel):
    success: bool = True
    status: str = Field("connected", description="ML Model status")
    mine: str = Field("Balaghat", description="Target mine")
    date: str = Field("2026-09-14", description="Forecast date")
    target_production: float = Field(..., description="Target production in tonnes")
    predicted_production: float = Field(..., description="Model predicted production in tonnes")
    shortfall: float = Field(..., description="Calculated production shortfall in tonnes")
    shortfall_percentage: float = Field(..., description="Shortfall percentage")
    model_prediction: Optional[float] = Field(None, description="Model 1 raw prediction")
    production_shortfall_prediction: Optional[float] = Field(None, description="Model 1 raw shortfall prediction")
    soil_moisture_prediction: Optional[float] = Field(None, description="Model 2 raw soil moisture prediction")
    rock_prediction: Optional[str] = Field(None, description="Model 3 predicted rock classification")
    equipment_production_loss: Optional[float] = Field(None, description="Model 4 raw equipment loss in tonnes")
    final_risk_score: Optional[float] = Field(None, description="Late fusion risk score (0-1)")
    risk_level: str = Field("LOW", description="Risk level (LOW, MEDIUM, HIGH)")
    reasons: List[str] = Field(default_factory=list, description="Factual reasons derived from input features and model importances")
    recommendations: List[str] = Field(default_factory=list, description="Operational recommendations")
    historical_production: List[Dict[str, Any]] = Field(default_factory=list, description="Historical production records")
    recent_history: List[Dict[str, Any]] = Field(default_factory=list, description="Past 7 days production records")
    today_prediction: Optional[Dict[str, Any]] = Field(None, description="Today's AIML prediction point")
    prediction: Optional[Dict[str, Any]] = Field(None, description="Today's prediction alias")
    predicted_production_series: List[Dict[str, Any]] = Field(default_factory=list, description="Predicted production series")
    predicted_series: List[Dict[str, Any]] = Field(default_factory=list, description="Next 7 days predicted series")
    message: Optional[str] = None
