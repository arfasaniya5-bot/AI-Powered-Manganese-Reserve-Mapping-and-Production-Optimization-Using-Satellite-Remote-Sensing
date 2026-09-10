/**
 * OrePrediction Page Component
 * ----------------------------
 * Coordinates the live exploration workflow:
 * 1. Default latitude (18.5234) and longitude (79.1234) are initialized on load.
 * 2. The map immediately renders the default location and marker.
 * 3. When the user changes latitude or longitude, the map updates immediately locally via React state.
 *    NO API request is sent on typing or keystrokes!
 * 4. When the user clicks "Predict Potential", FastAPI backend analysis is initiated (POST /api/location).
 * 5. Feature extraction occurs in the backend and prints in the terminal.
 * 6. PredictionResult displays the clean placeholder message:
 *    "Prediction results will appear here after the AI/ML model is connected."
 */

import React, { useState } from 'react';
import LocationForm from '../components/LocationForm';
import LocationMap from '../components/LocationMap';
import PredictionResult from '../components/PredictionResult';
import { predictPotential } from '../services/api';

const OrePrediction = () => {
  // Default coordinates matching project specification
  const [coordinates, setCoordinates] = useState({
    latitude: 18.5234,
    longitude: 79.1234,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Future AI/ML prediction result state (kept null today per prompt constraint)
  const [predictionResult, setPredictionResult] = useState(null);

  /**
   * Callback invoked by LocationForm whenever the user changes latitude or longitude.
   * Updates state immediately so the Leaflet map and marker update locally without network requests.
   */
  const handleCoordinatesChange = (newLat, newLon) => {
    setCoordinates({
      latitude: newLat,
      longitude: newLon,
    });
    setErrorMessage('');
  };

  /**
   * Predict Potential Handler:
   * Initiated strictly when the user clicks the "Predict Potential" button.
   * Sends the validated coordinates to FastAPI (POST /api/location) to trigger
   * location feature extraction and backend terminal reporting.
   */
  const handlePredict = async (lat, lon) => {
    const targetLat = lat ?? coordinates.latitude;
    const targetLon = lon ?? coordinates.longitude;

    // Validate coordinates
    if (
      typeof targetLat !== 'number' ||
      typeof targetLon !== 'number' ||
      isNaN(targetLat) ||
      isNaN(targetLon) ||
      targetLat < -90 ||
      targetLat > 90 ||
      targetLon < -180 ||
      targetLon > 180
    ) {
      setErrorMessage('Coordinates must be between -90 and 90 latitude, and -180 and 180 longitude.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');

    try {
      // Call trained AI/ML prediction endpoint (POST /api/predict-ore)
      const response = await predictPotential(targetLat, targetLon);

      if (response && response.success) {
        setPredictionResult(response);
        setErrorMessage('');
      }
    } catch (error) {
      // Catch connection or validation errors gracefully
      setErrorMessage(error.message || 'Error communicating with FastAPI backend.');
      setPredictionResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-content ore-prediction-page">
      {/* Page Header */}
      <header className="page-header">
        <h1 className="page-title">Ore / Deposit Prediction</h1>
        <p className="page-subtitle">
          Predict the potential of unknown areas for Manganese deposits using AI/ML and satellite data.
        </p>
      </header>

      {/* Section 1: Location Input Form */}
      <div className="form-section-wrapper">
        <LocationForm
          latitude={coordinates.latitude}
          longitude={coordinates.longitude}
          onCoordinatesChange={handleCoordinatesChange}
          onPredict={handlePredict}
          isLoading={isLoading}
          serverError={errorMessage}
        />
      </div>

      {/* Section 2: Two-column grid with Interactive Map on left and Prediction Result on right */}
      <div className="prediction-grid-layout">
        <div className="grid-col-map">
          <LocationMap selectedLocation={coordinates} />
        </div>
        <div className="grid-col-result">
          <PredictionResult
            result={predictionResult}
            location={coordinates}
          />
        </div>
      </div>
    </div>
  );
};

export default OrePrediction;
