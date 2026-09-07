/**
 * PredictionResult Component
 * --------------------------
 * Displays the outcome of the Manganese ore potential prediction model.
 * 
 * Strict behavior specification:
 * 1. Placeholder Mode (Default today):
 *    When `result` prop is null or undefined, renders the clean placeholder message:
 *    "Prediction results will appear here after the AI/ML model is connected."
 *    No fake mock values, percentages, or high/medium/low states are displayed.
 * 
 * 2. Active Model Mode (Future):
 *    When teammates connect their AI/ML pipeline and pass a `result` prop shaped:
 *    {
 *      "prediction": "High Potential",
 *      "probability": 0.87,
 *      "key_factors": ["Favorable geological structure", ...],
 *      "location": { "latitude": 18.5234, "longitude": 79.1234 }
 *    }
 *    The component dynamically renders the full prediction card, circular probability
 *    gauge, key factors checklist, and location summary matching Reference Image 2.
 */

import React from 'react';

const PredictionResult = ({ result = null, location = null }) => {
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

  // --- FUTURE ACTIVE STATE: Rendered when teammates' ML model returns real data ---
  const { prediction = 'Unknown Potential', probability = 0, key_factors = [] } = result;
  const percentage = Math.round(probability * 100);

  // Determine potential tone (High = emerald green, Medium = amber, Low = red)
  const isHigh = prediction.toLowerCase().includes('high');
  const isMedium = prediction.toLowerCase().includes('medium');
  const statusClass = isHigh ? 'status-high' : isMedium ? 'status-medium' : 'status-low';

  return (
    <section className="card prediction-card active-state" aria-labelledby="prediction-heading">
      <h2 id="prediction-heading" className="card-title">
        Prediction Result
      </h2>

      {/* Primary Prediction Banner & Circular Gauge */}
      <div className={`prediction-banner ${statusClass}`}>
        <div className="banner-left">
          <div className="status-icon-circle">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
          </div>
          <div className="status-text-group">
            <h3 className="prediction-outcome-text">{prediction}</h3>
            <p className="prediction-description">
              This area has a {probability > 0.5 ? 'high' : 'moderate'} probability of containing Manganese deposits.
            </p>
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

      {/* Key Factors Checklist */}
      {key_factors.length > 0 && (
        <div className="factors-section">
          <h4 className="subcard-title">Key Factors</h4>
          <ul className="factors-list">
            {key_factors.map((factor, index) => (
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

      {/* Location Details Subcard */}
      {location && (
        <div className="location-details-subcard">
          <h4 className="subcard-title">Location Details</h4>
          <div className="location-detail-grid">
            <div className="detail-row">
              <span className="detail-key">Latitude</span>
              <span className="detail-val">: {location.latitude.toFixed(4)}</span>
            </div>
            <div className="detail-row">
              <span className="detail-key">Longitude</span>
              <span className="detail-val">: {location.longitude.toFixed(4)}</span>
            </div>
            <div className="detail-row">
              <span className="detail-key">Model Confidence</span>
              <span className="detail-val">: {percentage}%</span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default PredictionResult;
