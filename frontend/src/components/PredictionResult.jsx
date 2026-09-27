/**
 * PredictionResult Component
 * --------------------------
 * Displays the outcome of the Manganese ore potential prediction model.
 * 
 * Strict behavior specification:
 * 1. Placeholder Mode (Default):
 *    When `result` prop is null or undefined, renders the clean placeholder message:
 *    "Prediction results will appear here after the AI/ML model is connected."
 *    No fake mock values, percentages, or high/medium/low states are displayed.
 * 
 * 2. Active Model Mode:
 *    When the trained model returns real data:
 *    - Renders matching the design in user reference image:
 *      - Green result card for High Potential (with appropriate themes for Medium and Low)
 *      - Circular badge with checkmark icon
 *      - Potential label (e.g. "High Potential")
 *      - Descriptive text ("This area has a high probability of containing Manganese deposits.")
 *      - Circular probability indicator showing dynamic percentage (e.g. 87% or actual model value)
 *    - Never hardcodes 87% or any fixed percentage.
 */

import React from 'react';

const PredictionResult = ({
  result = null,
  location = null,
  geoDetails = null,
  onSelectDeposit = null,
}) => {
  // If no AI/ML result is provided, render the strict placeholder
  if (!result) {
    return (
      <section className="card prediction-card placeholder-state" aria-labelledby="prediction-heading">
        <h2 id="prediction-heading" className="card-title">
          Prediction Result
        </h2>
        <div className="empty-prediction-box">
          <div className="placeholder-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <p className="prediction-placeholder-text">
            Prediction results will appear here after the AI/ML model is connected.
          </p>
        </div>
      </section>
    );
  }

  // Extract dynamic values from real model output
  const potentialCategory = result.potential || (typeof result.prediction === 'string' ? result.prediction : 'High Potential');
  const probability = result.probability ?? 0;
  const percentage = result.probability_percentage != null 
    ? Math.round(result.probability_percentage) 
    : Math.round(probability * 100);
  
  const displayMessage = result.message || (
    probability >= 0.70
      ? 'This area has a high probability of containing Manganese deposits.'
      : probability >= 0.40
        ? 'This area has a moderate probability of containing Manganese deposits.'
        : 'This area has a low probability of containing Manganese deposits.'
  );

  const keyFactors = result.key_factors || [];

  // Determine potential tone (High = emerald green, Medium = amber, Low = red)
  const isHigh = potentialCategory.toLowerCase().includes('high');
  const isMedium = potentialCategory.toLowerCase().includes('medium');
  const statusClass = isHigh ? 'status-high' : isMedium ? 'status-medium' : 'status-low';

  return (
    <section className="card prediction-card active-state" aria-labelledby="prediction-heading">
      <h2 id="prediction-heading" className="card-title">
        Prediction Result
      </h2>

      {/* Primary Prediction Banner & Circular Gauge (matching reference screenshot) */}
      <div className={`prediction-banner ${statusClass}`}>
        <div className="banner-left">
          <div className="status-icon-circle">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
          </div>
          <div className="status-text-group">
            <h3 className="prediction-outcome-text">{potentialCategory}</h3>
            <p className="prediction-description">{displayMessage}</p>
          </div>
        </div>

        {/* Circular Gauge */}
        <div className="probability-gauge-wrapper">
          <svg className="circular-chart" viewBox="0 0 36 36">
            <path
              className="circle-bg"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className="circle-fill"
              strokeDasharray={`${percentage}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <div className="gauge-text">
            <span className="gauge-percent">{percentage}%</span>
            <span className="gauge-label">Probability</span>
          </div>
        </div>
      </div>

      {/* Mineral Belt Proximity Context (Solution B) */}
      {result.nearby_deposit && result.nearby_deposit.found && (
        <div className="nearby-deposit-banner">
          <div className="nearby-banner-badge-row">
            <span className="nearby-badge">📍 {result.nearby_deposit.belt}</span>
            <span className="nearby-dist-tag">{result.nearby_deposit.distance_km} km away</span>
          </div>
          <p className="nearby-message">
            {result.nearby_deposit.message}
          </p>
          {onSelectDeposit && (
            <button
              type="button"
              className="btn-inspect-nearby"
              onClick={() => onSelectDeposit(result.nearby_deposit.latitude, result.nearby_deposit.longitude)}
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="btn-icon">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
              </svg>
              <span>Inspect {result.nearby_deposit.mine} Deposit ({result.nearby_deposit.deposit_potential}) →</span>
            </button>
          )}
        </div>
      )}

      {/* Key Factors Checklist (if available from model analysis) */}
      {keyFactors.length > 0 && (
        <div className="factors-section">
          <h4 className="subcard-title">Key Factors</h4>
          <ul className="factors-list">
            {keyFactors.map((factor, index) => (
              <li key={index} className="factor-item">
                <svg className="check-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                </svg>
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Location Details Subcard matching Reference Mockup */}
      {location && (
        <div className="location-details-subcard">
          <h4 className="subcard-title">Location Details</h4>
          <div className="location-detail-grid">
            <div className="detail-row">
              <span className="detail-icon-key">
                <svg className="detail-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                </svg>
                <span className="detail-key">Latitude</span>
              </span>
              <span className="detail-colon">:</span>
              <span className="detail-val">
                {typeof location.latitude === 'number' ? location.latitude.toFixed(4) : location.latitude}
              </span>
            </div>

            <div className="detail-row">
              <span className="detail-icon-key">
                <svg className="detail-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
                <span className="detail-key">Longitude</span>
              </span>
              <span className="detail-colon">:</span>
              <span className="detail-val">
                {typeof location.longitude === 'number' ? location.longitude.toFixed(4) : location.longitude}
              </span>
            </div>

            <div className="detail-row">
              <span className="detail-icon-key">
                <svg className="detail-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/>
                </svg>
                <span className="detail-key">State</span>
              </span>
              <span className="detail-colon">:</span>
              <span className="detail-val">
                {geoDetails?.state || 'Not available'}
              </span>
            </div>

            <div className="detail-row">
              <span className="detail-icon-key">
                <svg className="detail-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M15 11V5l-3-3-3 3v2H3v14h18V11h-6zm-8 8H5v-2h2v2zm0-4H5v-2h2v2zm0-4H5V9h2v2zm6 8h-2v-2h2v2zm0-4h-2v-2h2v2zm0-4h-2V9h2v2zm0-4h-2V5h2v2zm6 12h-2v-2h2v2zm0-4h-2v-2h2v2z"/>
                </svg>
                <span className="detail-key">District</span>
              </span>
              <span className="detail-colon">:</span>
              <span className="detail-val">
                {geoDetails?.district || 'Not available'}
              </span>
            </div>

            <div className="detail-row">
              <span className="detail-icon-key">
                <svg className="detail-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
                </svg>
                <span className="detail-key">Village</span>
              </span>
              <span className="detail-colon">:</span>
              <span className="detail-val">
                {geoDetails?.village || 'Not available'}
              </span>
            </div>

            <div className="detail-row">
              <span className="detail-icon-key">
                <svg className="detail-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z"/>
                </svg>
                <span className="detail-key">Model Confidence</span>
              </span>
              <span className="detail-colon">:</span>
              <span className="detail-val">
                {percentage}%
              </span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default PredictionResult;
