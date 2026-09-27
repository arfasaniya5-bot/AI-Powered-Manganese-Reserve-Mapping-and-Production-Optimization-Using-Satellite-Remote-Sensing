import React, { useState, useRef } from 'react';

const ProductionStepThree = ({
  formData,
  onChange,
  onBack,
  onNext,
  loading = false,
  error = null,
  weatherData = null,
  weatherLoading = false,
  weatherError = null,
  soilMoistureUnavailable = false,
  onRetryWeather = null,
}) => {
  const [geoFile, setGeoFile] = useState(null);
  const [equipFile, setEquipFile] = useState(null);

  const geoInputRef = useRef(null);
  const equipInputRef = useRef(null);

  const handleGeoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setGeoFile(file.name);
      onChange({ geological_data_uploaded: true, geological_file_name: file.name });
    }
  };

  const handleEquipUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setEquipFile(file.name);
      onChange({ equipment_data_uploaded: true, equipment_file_name: file.name });
    }
  };

  const isPredictionBlocked = (
    loading ||
    weatherLoading ||
    soilMoistureUnavailable ||
    formData.soil_moisture === null ||
    formData.soil_moisture === undefined
  );

  return (
    <div className="forecast-step-container">
      <div className="forecast-step-header">
        <h2 className="step-title">Step 3 : Additional Data</h2>
        <p className="step-subtitle">Provide environmental, geological and equipment data.</p>
      </div>

      {error && (
        <div className="forecast-alert error">
          <span>{error}</span>
        </div>
      )}

      <div className="forecast-step3-grid">
        {/* Card A: Weather Forecast (Live data via Open-Meteo, replacing manual inputs & CSV) */}
        <div className="additional-card env-card weather-forecast-card">
          <div className="additional-card-header">
            <div className="card-badge green-badge">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM19 18H6c-2.21 0-4-1.79-4-4 0-2.05 1.53-3.76 3.56-3.97l1.07-.11.5-.95C8.08 7.14 9.94 6 12 6c2.62 0 4.88 1.86 5.39 4.43l.3 1.5 1.53.11c1.56.1 2.78 1.41 2.78 2.96 0 1.65-1.35 3-3 3z" />
              </svg>
            </div>
            <div className="card-header-text">
              <h3 className="additional-card-title">Weather Forecast</h3>
              <span className="weather-site-badge">
                📍 {formData.mine || 'Balaghat'} • {formData.date || 'Today'}
              </span>
            </div>
          </div>

          {weatherLoading && (
            <div className="weather-status-box loading">
              <div className="weather-spinner"></div>
              <span>Fetching live forecast from Open-Meteo...</span>
            </div>
          )}

          {weatherError && !weatherLoading && (
            <div className="weather-status-box error">
              <div className="weather-error-header">
                <span className="error-icon">⚠️</span>
                <span>Weather data service error</span>
              </div>
              <p className="weather-error-detail">{weatherError}</p>
              {onRetryWeather && (
                <button
                  type="button"
                  className="weather-retry-btn"
                  onClick={onRetryWeather}
                >
                  Retry Connection
                </button>
              )}
            </div>
          )}

          <div className="weather-rows-list">
            <div className="weather-row">
              <span className="weather-label">Temperature (°C)</span>
              <span className="weather-value">
                {formData.temperature !== null && formData.temperature !== undefined
                  ? `${formData.temperature} °C`
                  : (weatherLoading ? '...' : '—')}
              </span>
            </div>

            <div className="weather-row">
              <span className="weather-label">Wind Speed (m/s)</span>
              <span className="weather-value">
                {formData.wind_speed !== null && formData.wind_speed !== undefined
                  ? `${formData.wind_speed} m/s`
                  : (weatherLoading ? '...' : '—')}
              </span>
            </div>

            <div className="weather-row">
              <span className="weather-label">Relative Humidity (%)</span>
              <span className="weather-value">
                {formData.humidity !== null && formData.humidity !== undefined
                  ? `${formData.humidity} %`
                  : (weatherLoading ? '...' : '—')}
              </span>
            </div>

            <div className="weather-row">
              <span className="weather-label">Precipitation (mm)</span>
              <span className="weather-value">
                {formData.precipitation !== null && formData.precipitation !== undefined
                  ? `${formData.precipitation} mm`
                  : (weatherLoading ? '...' : '—')}
              </span>
            </div>

            <div className="weather-row highlight-sm">
              <span className="weather-label">Soil Moisture (0–100 cm)</span>
              <span className={`weather-value ${soilMoistureUnavailable ? 'unavailable' : ''}`}>
                {soilMoistureUnavailable ? (
                  <span className="badge-unavailable">Not available</span>
                ) : (
                  formData.soil_moisture !== null && formData.soil_moisture !== undefined
                    ? `${formData.soil_moisture} m³/m³`
                    : (weatherLoading ? '...' : '—')
                )}
              </span>
            </div>
          </div>

          {soilMoistureUnavailable && !weatherLoading && (
            <div className="weather-warning-callout">
              <span className="callout-icon">⚠️</span>
              <div className="callout-content">
                <strong>Analysis Blocked</strong>
                <p>Soil moisture data unavailable for this location/date — cannot proceed.</p>
              </div>
            </div>
          )}

          <div className="weather-card-footer">
            <span className="weather-source-tag">Source: Open-Meteo live API</span>
            {weatherData?.forecast_time && (
              <span className="weather-time-tag">Observed: {weatherData.forecast_time}</span>
            )}
          </div>
        </div>

        {/* Card B: Geological Information */}
        <div className="additional-card geo-card">
          <div className="additional-card-header">
            <div className="card-badge blue-badge">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M14 6l-3.75 5 2.85 3.8-1.6 1.2L7 10l-6 8h22L14 6z" />
              </svg>
            </div>
            <h3 className="additional-card-title">Blasting Information</h3>
          </div>

          <div className="card-upload-center">
            <div className="upload-doc-icon blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <h4 className="upload-center-title">Upload Blasting Data (CSV file)</h4>
            <input
              type="file"
              ref={geoInputRef}
              style={{ display: 'none' }}
              accept=".csv"
              onChange={handleGeoUpload}
            />
            <button
              type="button"
              className="forecast-btn-secondary"
              onClick={() => geoInputRef.current && geoInputRef.current.click()}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              Choose File
            </button>
            {geoFile ? (
              <span className="upload-filename">✓ {geoFile}</span>
            ) : (
              <p className="upload-note text-center">
                CSV should contain relevant blasting features.
              </p>
            )}
          </div>
        </div>

        {/* Card C: Equipment & Operations */}
        <div className="additional-card equip-card">
          <div className="additional-card-header">
            <div className="card-badge purple-badge">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
              </svg>
            </div>
            <h3 className="additional-card-title">Equipment & Operations</h3>
          </div>

          <div className="card-upload-center">
            <div className="upload-doc-icon blue">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <h4 className="upload-center-title">Upload Equipment Data (CSV file)</h4>
            <input
              type="file"
              ref={equipInputRef}
              style={{ display: 'none' }}
              accept=".csv"
              onChange={handleEquipUpload}
            />
            <button
              type="button"
              className="forecast-btn-secondary"
              onClick={() => equipInputRef.current && equipInputRef.current.click()}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              Choose File
            </button>
            {equipFile ? (
              <span className="upload-filename">✓ {equipFile}</span>
            ) : (
              <p className="upload-note text-center">
                CSV should contain equipment status, downtime, maintenance records etc.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="forecast-action-bar">
        <button
          type="button"
          className="forecast-btn-outline"
          onClick={onBack}
          disabled={loading}
        >
          &larr; Back
        </button>
        <button
          type="button"
          className="forecast-btn-primary"
          onClick={onNext}
          disabled={isPredictionBlocked}
          title={soilMoistureUnavailable ? 'Soil moisture data unavailable for this location/date — cannot proceed' : ''}
        >
          {loading ? 'Running AI Model...' : 'Next →'}
        </button>
      </div>
    </div>
  );
};

export default ProductionStepThree;
