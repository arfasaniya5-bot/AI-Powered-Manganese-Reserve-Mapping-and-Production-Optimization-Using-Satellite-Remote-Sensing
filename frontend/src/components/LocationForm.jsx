/**
 * LocationForm Component
 * ----------------------
 * Allows the user to enter geographic coordinates (Latitude and Longitude)
 * and trigger potential prediction.
 * 
 * Strict constraints adhered to:
 * - Contains ONLY Latitude, Longitude, and "Predict Potential" button.
 * - Elevation, Rock Type, Soil Type, Magnetic Anomaly, Satellite Feature Index,
 *   Upload CSV, and "View on Map" are strictly excluded from code.
 * 
 * Client-Side Validation Logic:
 * Before sending any request to the FastAPI backend, this component verifies:
 * 1. Both fields are non-empty.
 * 2. Both values parse as valid finite numbers.
 * 3. Latitude is between -90.0 and +90.0.
 * 4. Longitude is between -180.0 and +180.0.
 * 
 * Why validate on client-side?
 * Immediate UI feedback prevents invalid network calls and gives the user
 * instant corrections. The backend still performs secondary validation via Pydantic.
 */

import React, { useState } from 'react';

const LocationForm = ({ onSubmit, isLoading, serverError }) => {
  // Controlled input states for coordinates
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [clientError, setClientError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setClientError('');

    // 1. Check for empty fields
    if (!latitude.trim()) {
      setClientError('Please enter a Latitude value.');
      return;
    }
    if (!longitude.trim()) {
      setClientError('Please enter a Longitude value.');
      return;
    }

    // 2. Parse numbers
    const latNum = parseFloat(latitude.trim());
    const lonNum = parseFloat(longitude.trim());

    if (isNaN(latNum)) {
      setClientError('Latitude must be a valid number.');
      return;
    }
    if (isNaN(lonNum)) {
      setClientError('Longitude must be a valid number.');
      return;
    }

    // 3. Boundary validation
    if (latNum < -90 || latNum > 90) {
      setClientError('Latitude must be between -90 and 90 degrees.');
      return;
    }
    if (lonNum < -180 || lonNum > 180) {
      setClientError('Longitude must be between -180 and 180 degrees.');
      return;
    }

    // Coordinates are valid on the client side: trigger parent submit handler
    onSubmit(latNum, lonNum);
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

      <form onSubmit={handleSubmit} className="coordinates-form" noValidate>
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
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              disabled={isLoading}
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
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              disabled={isLoading}
              required
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn-predict"
            disabled={isLoading}
            aria-busy={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner" aria-hidden="true"></span>
                <span>Validating...</span>
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
