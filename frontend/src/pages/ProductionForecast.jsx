import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchProductionMines,
  fetchMineHistory,
  fetchWeatherForecast,
  predictProductionShortfall,
} from '../services/productionService';
import ProductionStepOne from '../components/ProductionStepOne';
import ProductionStepTwo from '../components/ProductionStepTwo';
import ProductionStepThree from '../components/ProductionStepThree';
import ProductionPredictionResult from '../components/ProductionPredictionResult';

const ProductionForecast = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mines, setMines] = useState([]);

  // Form Data spanning all steps (Zero hardcoded weather values)
  const [formData, setFormData] = useState({
    mine: 'Balaghat',
    date: '2026-09-14',
    target_production: 10000,
    region: 'Madhya Pradesh',
    temperature: null,
    wind_speed: null,
    humidity: null,
    precipitation: null,
    soil_moisture: null,
  });

  // Weather Forecast state from live Open-Meteo API
  const [weatherData, setWeatherData] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState(null);
  const [soilMoistureUnavailable, setSoilMoistureUnavailable] = useState(false);

  // Step 2 Historical production records (last 7 days)
  const [history, setHistory] = useState([
    { date: '07-09-2026', actual_production: 8450 },
    { date: '08-09-2026', actual_production: 8200 },
    { date: '09-09-2026', actual_production: 8750 },
    { date: '10-09-2026', actual_production: 8100 },
    { date: '11-09-2026', actual_production: 8600 },
    { date: '12-09-2026', actual_production: 8400 },
    { date: '13-09-2026', actual_production: 8300 },
  ]);

  // Step 4 ML Prediction Response Result
  const [predictionResult, setPredictionResult] = useState(null);

  // Initial load of mines list
  useEffect(() => {
    const loadMines = async () => {
      try {
        const list = await fetchProductionMines();
        if (list && list.length > 0) {
          setMines(list);
          if (!list.includes(formData.mine)) {
            setFormData((prev) => ({ ...prev, mine: list[0] }));
          }
        }
      } catch (err) {
        console.error('Failed to load mines:', err);
      }
    };
    loadMines();
  }, []);

  // When mine changes, fetch real historical series from backend
  useEffect(() => {
    if (!formData.mine) return;
    const loadHistory = async () => {
      try {
        const res = await fetchMineHistory(formData.mine);
        if (res && res.success && res.history && res.history.length > 0) {
          setHistory(res.history);
        }
      } catch (err) {
        console.warn('Could not auto-fetch mine history:', err);
      }
    };
    loadHistory();
  }, [formData.mine]);

  // Automatically fetch live weather forecast from Open-Meteo when mine or date changes
  const loadWeather = useCallback(async () => {
    if (!formData.mine) return;
    setWeatherLoading(true);
    setWeatherError(null);
    try {
      const res = await fetchWeatherForecast({
        mine: formData.mine,
        date: formData.date,
      });

      if (res && res.success) {
        setWeatherData(res);
        const temp = res.temperature_c ?? res.temperature;
        const wind = res.wind_speed_ms ?? res.wind_speed;
        const hum = res.relative_humidity_pct ?? res.humidity;
        const prec = res.precipitation_mm ?? res.precipitation;
        const sm = res.soil_moisture_0_100cm ?? res.soil_moisture;

        const isSmUnavailable = sm === null || sm === undefined || res.soil_moisture_available === false;
        setSoilMoistureUnavailable(isSmUnavailable);

        setFormData((prev) => ({
          ...prev,
          temperature: temp,
          wind_speed: wind,
          humidity: hum,
          precipitation: prec,
          soil_moisture: sm,
        }));
      } else {
        throw new Error('Weather data could not be retrieved from provider.');
      }
    } catch (err) {
      console.error('Weather forecast fetch error:', err);
      setWeatherError(err.message || 'Failed to fetch live weather forecast.');
      setWeatherData(null);
      setSoilMoistureUnavailable(true);
      setFormData((prev) => ({
        ...prev,
        temperature: null,
        wind_speed: null,
        humidity: null,
        precipitation: null,
        soil_moisture: null,
      }));
    } finally {
      setWeatherLoading(false);
    }
  }, [formData.mine, formData.date]);

  useEffect(() => {
    loadWeather();
  }, [loadWeather]);

  const updateFormData = (patch) => {
    setFormData((prev) => ({ ...prev, ...patch }));
  };

  // Step transitions
  const handleNextFromStepOne = () => {
    setError(null);
    setCurrentStep(2);
  };

  const handleNextFromStepTwo = () => {
    setError(null);
    setCurrentStep(3);
  };

  const handleRunPrediction = async () => {
    // Soil moisture gating: block prediction if soil moisture is unavailable
    if (soilMoistureUnavailable || formData.soil_moisture === null || formData.soil_moisture === undefined) {
      setError('Soil moisture data unavailable for this location/date — cannot proceed');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const targetNum = formData.target_production !== undefined && formData.target_production !== ''
        ? Number(formData.target_production)
        : 10000;

      const payload = {
        mine: formData.mine,
        date: formData.date,
        target_production: isNaN(targetNum) ? 10000 : targetNum,
        region: formData.region || 'Madhya Pradesh',
        // Model expected keys (with aliases for full compatibility, zero hardcoded numbers)
        temperature: formData.temperature,
        temperature_c: formData.temperature,
        wind_speed: formData.wind_speed,
        wind_speed_m_s: formData.wind_speed,
        humidity: formData.humidity,
        relative_humidity_percent: formData.humidity,
        precipitation: formData.precipitation,
        precipitation_mm: formData.precipitation,
        soil_moisture: formData.soil_moisture,
        soil_moisture_0_100cm: formData.soil_moisture,
        blasting_file_name: formData.geological_file_name || '',
        equipment_file_name: formData.equipment_file_name || '',
        weather_file_name: formData.weather_file_name || '',
        geological_data: formData.geological_data || {},
        equipment_data: formData.equipment_data || {},
        recent_history: history,
      };

      const res = await predictProductionShortfall(payload);
      setPredictionResult(res);
      setCurrentStep(4);
    } catch (err) {
      console.error('Prediction failed:', err);
      setError(err.message || 'Production ML prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="production-forecast-page">
      {currentStep === 1 && (
        <ProductionStepOne
          formData={formData}
          onChange={updateFormData}
          onNext={handleNextFromStepOne}
          mines={mines}
          loading={loading}
          error={error}
        />
      )}

      {currentStep === 2 && (
        <ProductionStepTwo
          history={history}
          onChangeHistory={setHistory}
          onBack={() => setCurrentStep(1)}
          onNext={handleNextFromStepTwo}
          loading={loading}
        />
      )}

      {currentStep === 3 && (
        <ProductionStepThree
          formData={formData}
          onChange={updateFormData}
          onBack={() => setCurrentStep(2)}
          onNext={handleRunPrediction}
          loading={loading}
          error={error}
          weatherData={weatherData}
          weatherLoading={weatherLoading}
          weatherError={weatherError}
          soilMoistureUnavailable={soilMoistureUnavailable}
          onRetryWeather={loadWeather}
        />
      )}

      {currentStep === 4 && (
        <ProductionPredictionResult
          result={predictionResult}
          onBack={() => setCurrentStep(3)}
        />
      )}
    </div>
  );
};

export default ProductionForecast;
