/**
 * LocationForm Component
 * ----------------------
 * Provides coordinate input fields (Latitude and Longitude) and a placeholder Predict Potential button.
 * 
 * Strict constraints adhered to:
 * - Contains ONLY Latitude, Longitude, and "Predict Potential" button.
 * - Elevation, Rock Type, Soil Type, Magnetic Anomaly, Satellite Feature Index,
 *   Upload CSV, and "View on Map" are strictly excluded from code.
 * 
 * Automatic Map Update Behavior:
 * - Latitude and Longitude default to 18.5234 and 79.1234.
 * - Whenever the user changes either value, this component validates the number client-side.
 * - If valid, it immediately informs the parent component via `onCoordinatesChange(lat, lon)`.
 * - The map updates automatically WITHOUT requiring the user to click any button!
 * 
 * Predict Potential Button Behavior:
 * - Kept visible as required by the UI specification.
 * - Does not perform AI/ML prediction or call fake APIs.
 * - If clicked, displays: "AI/ML prediction will be connected later."
 */

import React, { useState } from 'react';

const LocationForm = ({
  latitude,
  longitude,
  onCoordinatesChange,
  onPredict,
  isLoading = false,
  serverError = '',
}) => {
  // Local input string states allow smooth typing (e.g. while typing decimals "18.")
  const [latInput, setLatInput] = useState(String(latitude ?? '18.5234'));
  const [lonInput, setLonInput] = useState(String(longitude ?? '79.1234'));
  const [clientError, setClientError] = useState('');

  // Validate numbers and propagate changes locally to the parent and map
  const validateAndPropagate = (newLatStr, newLonStr) => {
    setClientError('');

    const trimmedLat = newLatStr.trim();
    const trimmedLon = newLonStr.trim();

    // If either field is currently blank during typing, don't crash or error immediately
    if (!trimmedLat || !trimmedLon) {
      return;
    }

    const latNum = parseFloat(trimmedLat);
    const lonNum = parseFloat(trimmedLon);

    if (isNaN(latNum) || isNaN(lonNum)) {
      return;
    }

    // Boundary check: update map locally only if within valid geographic coordinates
    if (latNum >= -90 && latNum <= 90 && lonNum >= -180 && lonNum <= 180) {
      onCoordinatesChange(latNum, lonNum);
    }
  };

  // Handler for latitude change
  const handleLatChange = (e) => {
    const val = e.target.value;
    setLatInput(val);
    validateAndPropagate(val, lonInput);
  };

  // Handler for longitude change
  const handleLonChange = (e) => {
    const val = e.target.value;
    setLonInput(val);
    validateAndPropagate(latInput, val);
  };

  // Predict Potential button click handler: initiates FastAPI backend analysis
  const handlePredictClick = (e) => {
    e.preventDefault();
    setClientError('');

    const trimmedLat = latInput.trim();
    const trimmedLon = lonInput.trim();

    if (!trimmedLat) {
      setClientError('Latitude cannot be empty.');
      return;
    }
    if (!trimmedLon) {
      setClientError('Longitude cannot be empty.');
      return;
    }

    const latNum = parseFloat(trimmedLat);
    const lonNum = parseFloat(trimmedLon);

    if (isNaN(latNum)) {
      setClientError('Latitude must be a valid number.');
      return;
    }
    if (isNaN(lonNum)) {
      setClientError('Longitude must be a valid number.');
      return;
    }

    if (latNum < -90 || latNum > 90) {
      setClientError('Latitude must be between -90 and 90 degrees.');
      return;
    }
    if (lonNum < -180 || lonNum > 180) {
      setClientError('Longitude must be between -180 and 180 degrees.');
      return;
    }

    // Trigger backend analysis
    if (onPredict) {
      onPredict(latNum, lonNum);
    }
  };

  const displayError = clientError || serverError;

  return (
    <section className="card location-form-card" aria-labelledby="form-heading">
      <h2 id="form-heading" className="card-title">
        Enter Location Details
      </h2>

      {/* Inline Error Alert Message */}
      {displayError && (
        <div className="form-error-banner" role="alert">
          <svg className="error-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
          <span>{displayError}</span>
        </div>
      )}

      <form onSubmit={handlePredictClick} className="coordinates-form" noValidate>
        {/* Latitude Input Field */}
        <div className="form-group">
          <label htmlFor="latitude-input" className="input-label">
            Latitude
          </label>
          <div className="input-with-icon">
            <svg className="input-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
            </svg>
            <input
              id="latitude-input"
              type="number"
              step="any"
              className="coord-input"
              placeholder="18.5234"
              value={latInput}
              onChange={handleLatChange}
              required
            />
          </div>
        </div>

        {/* Longitude Input Field */}
        <div className="form-group">
          <label htmlFor="longitude-input" className="input-label">
            Longitude
          </label>
          <div className="input-with-icon">
            <svg className="input-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
            </svg>
            <input
              id="longitude-input"
              type="number"
              step="any"
              className="coord-input"
              placeholder="79.1234"
              value={lonInput}
              onChange={handleLonChange}
              required
            />
          </div>
        </div>

        {/* Predict Potential Button (Placeholder: does not run prediction now) */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn-predict"
            title="AI/ML prediction will be connected later."
          >
            {isLoading ? (
              <>
                <span className="spinner" aria-hidden="true"></span>
                <span>Connecting...</span>
              </>
            ) : (
              <>
                <svg className="btn-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="11" cy="11" r="7" />
                  <line x1="21" y1="21" x2="16" y2="16" />
                </svg>
                <span>Predict Potential</span>
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
};

export default LocationForm;
