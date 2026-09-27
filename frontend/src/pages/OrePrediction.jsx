/**
 * OrePrediction Page Component
 * ----------------------------
 * Single source of truth for location exploration & manganese potential prediction:
 * 1. Default coordinates (18.5234°N, 79.1234°E) initialized on load.
 * 2. Reverse geocoding resolves real State, District, and Village via FastAPI endpoint.
 * 3. Unified state management:
 *    - Dragging map: live center coordinates display updates continuously (via RAF).
 *      On drag release (moveend): coordinates update and debounced reverse geocoding triggers.
 *      Prediction does NOT auto-trigger on drag.
 *    - Clicking/Tapping map: marker moves to clicked point, coordinates & reverse geocoding update,
 *      and prediction runs automatically without requiring button click.
 *    - Manual input: user types lat/lon, clicks "Predict Potential" button, camera flies to point,
 *      location details update, and prediction runs.
 */

import React, { useState, useEffect, useRef } from 'react';
import LocationForm from '../components/LocationForm';
import LocationMap from '../components/LocationMap';
import PredictionResult from '../components/PredictionResult';
import { predictPotential, reverseGeocode } from '../services/api';

const OrePrediction = () => {
  // Default coordinates matching project specification
  const [coordinates, setCoordinates] = useState({
    latitude: 18.5234,
    longitude: 79.1234,
  });

  // Dynamic reverse geocoded details
  const [geoDetails, setGeoDetails] = useState({
    state: 'Telangana',
    district: 'Karimnagar',
    village: 'Choppadandi',
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [predictionResult, setPredictionResult] = useState(null);

  const debounceTimerRef = useRef(null);

  /**
   * Helper to fetch reverse geocoding with optional debouncing.
   */
  const updateGeoDetails = (lat, lon, immediate = false) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }

    const fetchGeo = async () => {
      try {
        const geo = await reverseGeocode(lat, lon);
        if (geo) {
          setGeoDetails({
            state: geo.state || 'Not available',
            district: geo.district || 'Not available',
            village: geo.village || 'Not available',
          });
        }
      } catch (err) {
        console.warn('[OrePrediction] Geocoding update failed:', err);
      }
    };

    if (immediate) {
      fetchGeo();
    } else {
      // Debounce by 250ms on drag release
      debounceTimerRef.current = setTimeout(fetchGeo, 250);
    }
  };

  /**
   * Initial load: fetch real geocoding details and initial prediction for default coordinates.
   */
  useEffect(() => {
    updateGeoDetails(coordinates.latitude, coordinates.longitude, true);
    handlePredict(coordinates.latitude, coordinates.longitude);
  }, []);

  /**
   * Callback invoked by LocationForm whenever user types latitude or longitude.
   * Updates state locally without sending premature prediction requests.
   */
  const handleCoordinatesChange = (newLat, newLon) => {
    setCoordinates({
      latitude: newLat,
      longitude: newLon,
    });
    setErrorMessage('');
  };

  /**
   * Callback invoked when user finishes dragging the map (moveend).
   * Synchronizes page coordinates and reverse geocoding without running prediction.
   */
  const handleDragEnd = (newLat, newLon) => {
    setCoordinates({
      latitude: newLat,
      longitude: newLon,
    });
    updateGeoDetails(newLat, newLon, false);
  };

  /**
   * Predict Potential Handler:
   * Called automatically on map click/tap, and manually when clicking "Predict Potential".
   */
  const handlePredict = async (lat, lon) => {
    const targetLat = lat ?? coordinates.latitude;
    const targetLon = lon ?? coordinates.longitude;

    // Validate coordinates boundary
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

    // Ensure reverse geocoding is up-to-date
    updateGeoDetails(targetLat, targetLon, true);

    try {
      // Call trained AI/ML prediction endpoint (POST /api/predict-ore)
      const response = await predictPotential(targetLat, targetLon);

      if (response && response.success) {
        setPredictionResult(response);
        setErrorMessage('');
      }
    } catch (error) {
      setErrorMessage(error.message || 'Error communicating with FastAPI backend.');
      setPredictionResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Callback when user clicks or taps on the map:
   * Selects exact coordinates, moves marker, updates geocoding, and auto-triggers prediction.
   */
  const handleMapSelect = (newLat, newLon) => {
    setCoordinates({
      latitude: newLat,
      longitude: newLon,
    });
    setErrorMessage('');
    handlePredict(newLat, newLon);
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
          <LocationMap
            selectedLocation={coordinates}
            onLocationSelect={handleMapSelect}
            onDragEnd={handleDragEnd}
          />
        </div>
        <div className="grid-col-result">
          <PredictionResult
            result={predictionResult}
            location={coordinates}
            geoDetails={geoDetails}
            onSelectDeposit={(lat, lon) => {
              handleCoordinatesChange(lat, lon);
              handlePredict(lat, lon);
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default OrePrediction;
