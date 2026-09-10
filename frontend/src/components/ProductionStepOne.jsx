import React from 'react';

const MINE_REGIONS = {
  'Balaghat': 'Madhya Pradesh',
  'Ukwa': 'Madhya Pradesh',
  'Tirodi': 'Madhya Pradesh',
  'Beldongri': 'Maharashtra',
  'Chikla': 'Maharashtra',
  'Dongri Buzurg': 'Maharashtra',
  'Gumgaon': 'Maharashtra',
  'Kandri': 'Maharashtra',
  'Mansar': 'Maharashtra'
};

const ProductionStepOne = ({
  formData,
  onChange,
  onNext,
  mines = [],
  loading = false,
  error = null
}) => {
  const handleMineChange = (e) => {
    const mine = e.target.value;
    const region = MINE_REGIONS[mine] || 'Madhya Pradesh';
    onChange({ mine, region });
  };

  const isFormValid = formData.mine && formData.date && Number(formData.target_production) > 0;

  return (
    <div className="forecast-step-container">
      <div className="forecast-step-header">
        <h2 className="step-title">Step 1 : Basic Information</h2>
        <p className="step-subtitle">Enter the basic details for prediction</p>
      </div>

      {error && (
        <div className="forecast-alert error">
          <span>{error}</span>
        </div>
      )}

      <div className="forecast-step1-grid">
        {/* Left Form Section */}
        <div className="forecast-form-card">
          <div className="forecast-field-group">
            <label className="forecast-label">
              Mine / Site <span className="required-star">*</span>
            </label>
            <select
              className="forecast-input forecast-select"
              value={formData.mine || ''}
              onChange={handleMineChange}
              disabled={loading}
            >
              <option value="">Select Mine / Site</option>
              {mines.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div className="forecast-field-group">
            <label className="forecast-label">
              Date <span className="required-star">*</span>
            </label>
            <input
              type="date"
              className="forecast-input"
              value={formData.date || '2026-09-14'}
              onChange={(e) => onChange({ date: e.target.value })}
              disabled={loading}
            />
          </div>

          <div className="forecast-field-group">
            <label className="forecast-label">
              Target Production (tonnes) <span className="required-star">*</span>
            </label>
            <input
              type="number"
              className="forecast-input"
              value={formData.target_production || ''}
              placeholder="e.g. 10000"
              min="1"
              step="100"
              onChange={(e) => onChange({ target_production: parseFloat(e.target.value) || 0 })}
              disabled={loading}
            />
          </div>

          <div className="forecast-field-group">
            <label className="forecast-label">Region / State</label>
            <input
              type="text"
              className="forecast-input forecast-readonly"
              value={formData.region || 'Madhya Pradesh'}
              readOnly
            />
          </div>
        </div>

        {/* Right Branding Image Panel */}
        <div className="forecast-branding-card">
          <img
            src="/moil_mine_pit.jpg"
            alt="MOIL Open-cast Mine Pit"
            className="branding-image"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          <div className="branding-overlay">
            <h3 className="branding-title">Sustainable Mining for a Stronger India</h3>
            <p className="branding-sub">MOIL Limited</p>
          </div>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="forecast-action-bar right-only">
        <button
          type="button"
          className="forecast-btn-primary"
          onClick={onNext}
          disabled={!isFormValid || loading}
        >
          Next &rarr;
        </button>
      </div>
    </div>
  );
};

export default ProductionStepOne;
