import React, { useState, useRef } from 'react';

const ProductionStepThree = ({
  formData,
  onChange,
  onBack,
  onNext,
  loading = false,
  error = null,
}) => {
  const [envMode, setEnvMode] = useState('manual');
  const [geoFile, setGeoFile] = useState(null);
  const [equipFile, setEquipFile] = useState(null);

  const geoInputRef = useRef(null);
  const equipInputRef = useRef(null);

  const handleEnvChange = (field, val) => {
    onChange({ [field]: parseFloat(val) || 0 });
  };

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
        {/* Card A: Environmental Information */}
        <div className="additional-card env-card">
          <div className="additional-card-header">
            <div className="card-badge green-badge">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z" />
              </svg>
            </div>
            <h3 className="additional-card-title">Environmental Information</h3>
          </div>

          <div className="mode-toggle-group compact">
            <label className="radio-label">
              <input
                type="radio"
                name="envMode"
                value="manual"
                checked={envMode === 'manual'}
                onChange={() => setEnvMode('manual')}
              />
              <span>Enter manually</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="envMode"
                value="csv"
                checked={envMode === 'csv'}
                onChange={() => setEnvMode('csv')}
              />
              <span>Upload CSV file</span>
            </label>
          </div>

          {envMode === 'manual' ? (
            <div className="env-fields-list">
              <div className="forecast-field-group mini">
                <label className="forecast-label">Temperature (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  className="forecast-input"
                  value={formData.temperature !== undefined ? formData.temperature : 16.4}
                  onChange={(e) => handleEnvChange('temperature', e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="forecast-field-group mini">
                <label className="forecast-label">Wind Speed (m/s)</label>
                <input
                  type="number"
                  step="0.1"
                  className="forecast-input"
                  value={formData.wind_speed !== undefined ? formData.wind_speed : 2.3}
                  onChange={(e) => handleEnvChange('wind_speed', e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="forecast-field-group mini">
                <label className="forecast-label">Relative Humidity (%)</label>
                <input
                  type="number"
                  step="0.1"
                  className="forecast-input"
                  value={formData.humidity !== undefined ? formData.humidity : 52.1}
                  onChange={(e) => handleEnvChange('humidity', e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="forecast-field-group mini">
                <label className="forecast-label">Precipitation (mm)</label>
                <input
                  type="number"
                  step="0.1"
                  className="forecast-input"
                  value={formData.precipitation !== undefined ? formData.precipitation : 0}
                  onChange={(e) => handleEnvChange('precipitation', e.target.value)}
                  disabled={loading}
                />
              </div>

              <div className="forecast-field-group mini">
                <label className="forecast-label">Soil Moisture (0–100 cm)</label>
                <input
                  type="number"
                  step="0.001"
                  className="forecast-input"
                  value={formData.soil_moisture !== undefined ? formData.soil_moisture : 0.304}
                  onChange={(e) => handleEnvChange('soil_moisture', e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>
          ) : (
            <div className="env-csv-upload-box">
              <p className="upload-note">Upload MOIL Weather & Soil CSV file</p>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => {
                  if (e.target.files[0]) {
                    onChange({ weather_file_name: e.target.files[0].name });
                  }
                }}
              />
            </div>
          )}
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
          disabled={loading}
        >
          {loading ? 'Running AI Model...' : 'Next →'}
        </button>
      </div>
    </div>
  );
};

export default ProductionStepThree;
