import React, { useState, useEffect } from 'react';
import {
  fetchProductionMines,
  fetchMineHistory,
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

  // Form Data spanning all steps
  const [formData, setFormData] = useState({
    mine: 'Balaghat',
    date: '2026-09-14',
    target_production: 10000,
    region: 'Madhya Pradesh',
    temperature: 16.4,
    wind_speed: 2.3,
    humidity: 52.1,
    precipitation: 0,
    soil_moisture: 0.304,
  });

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
        temperature: Number(formData.temperature) || 16.4,
        wind_speed: Number(formData.wind_speed) || 2.3,
        humidity: Number(formData.humidity) || 52.1,
        precipitation: Number(formData.precipitation) || 0,
        soil_moisture: Number(formData.soil_moisture) || 0.304,
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
