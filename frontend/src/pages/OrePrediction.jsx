/**
 * OrePrediction Page Component
 * ----------------------------
 * Handles manganese deposit exploration by coordinating location input,
 * FastAPI backend validation, and interactive map visualization.
 * 
 * Flow:
 * 1. User enters latitude and longitude.
 * 2. LocationForm validates values client-side.
 * 3. OrePrediction sends the validated coordinates to FastAPI via Axios (`sendLocationCoordinates`).
 * 4. FastAPI validates server-side via Pydantic and returns confirmation.
 * 5. State updates: `selectedLocation` updates, triggering `LocationMap` to place a marker and flyTo coordinates.
 * 6. Explicit loading and error handling:
 *    - Network error / backend down -> Friendly alert
 *    - 422 Unprocessable Entity -> Shows exact Pydantic detail
 * 7. PredictionResult displays clean placeholder:
 *    "Prediction results will appear here after the AI/ML model is connected."
 */

import React, { useState } from 'react';
import LocationForm from '../components/LocationForm';
import LocationMap from '../components/LocationMap';
import PredictionResult from '../components/PredictionResult';
import { sendLocationCoordinates } from '../services/api';

const OrePrediction = () => {
  // State management
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Future AI/ML prediction result state (kept null today to satisfy strict placeholder constraint)
  const [predictionResult, setPredictionResult] = useState(null);

  /**
   * Handles submission from LocationForm after client-side checks succeed.
   * Sends coordinates to FastAPI backend and updates map upon confirmation.
   */
  const handleLocationSubmit = async (lat, lon) => {
    setIsLoading(true);
    setErrorMessage('');

    try {
      // Step 2 & 3: React sends coordinates to FastAPI via Axios
      const response = await sendLocationCoordinates(lat, lon);

      // Step 4 & 5: FastAPI returned validated coordinates; update map state
      if (response && response.success) {
        setSelectedLocation({
          latitude: response.latitude,
          longitude: response.longitude,
        });

        // WHERE AI/ML PREDICTION HOOK WILL GO LATER:
        // When teammates deploy their model endpoint (e.g. POST /api/predict),
        // we will fetch the prediction and call setPredictionResult(resultData).
        // For now, predictionResult remains null to show the clean placeholder.
        setPredictionResult(null);
      }
    } catch (error) {
      // Step 6: Handle network errors or server validation failures gracefully
      setErrorMessage(error.message || 'An unexpected error occurred while contacting the server.');
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
          onSubmit={handleLocationSubmit}
          isLoading={isLoading}
          serverError={errorMessage}
        />
      </div>

      {/* Section 2: Two-column grid with Interactive Map on left and Prediction Result on right */}
      <div className="prediction-grid-layout">
        <div className="grid-col-map">
          <LocationMap selectedLocation={selectedLocation} />
        </div>
        <div className="grid-col-result">
          <PredictionResult
            result={predictionResult}
            location={selectedLocation}
          />
        </div>
      </div>
    </div>
  );
};

export default OrePrediction;
