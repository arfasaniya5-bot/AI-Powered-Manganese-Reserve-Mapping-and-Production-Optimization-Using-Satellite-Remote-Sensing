/**
 * Production Analysis API Service
 * -------------------------------
 * Connects the React frontend to the FastAPI Production Analysis endpoints.
 * Reuses the existing apiClient instance from api.js (matching port 8000 and CORS setup).
 */

import apiClient from './api';

/**
 * Checks connectivity and readiness of the 4 production datasets.
 * Calls GET /api/production/health
 */
export const fetchProductionHealth = async () => {
  try {
    const response = await apiClient.get('/api/production/health');
    return response.data;
  } catch (error) {
    console.error('Error fetching production health:', error);
    throw new Error(error.response?.data?.detail || 'Failed to connect to Production Analysis backend.');
  }
};

/**
 * Retrieves metadata for all four production datasets.
 * Calls GET /api/production/datasets
 */
export const fetchProductionDatasets = async () => {
  try {
    const response = await apiClient.get('/api/production/datasets');
    return response.data;
  } catch (error) {
    console.error('Error fetching production datasets:', error);
    throw new Error(error.response?.data?.detail || 'Failed to retrieve production dataset metadata.');
  }
};

/**
 * Retrieves aggregated production, equipment, weather, and drill metrics.
 * Calls GET /api/production/summary
 */
export const fetchProductionSummary = async () => {
  try {
    const response = await apiClient.get('/api/production/summary');
    return response.data;
  } catch (error) {
    console.error('Error fetching production summary:', error);
    throw new Error(error.response?.data?.detail || 'Failed to retrieve production summary.');
  }
};

/**
 * Retrieves column definitions, data types, and sample values for a specific dataset.
 * Calls GET /api/production/columns/{datasetKey}
 */
export const fetchDatasetColumns = async (datasetKey) => {
  try {
    const response = await apiClient.get(`/api/production/columns/${datasetKey}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching columns for ${datasetKey}:`, error);
    throw new Error(error.response?.data?.detail || `Failed to retrieve columns for dataset ${datasetKey}.`);
  }
};

/**
 * Retrieves paginated records from a dataset with optional mine filtering.
 * Calls GET /api/production/records/{datasetKey}
 */
export const fetchDatasetRecords = async (datasetKey, limit = 50, offset = 0, mine = null) => {
  try {
    const params = { limit, offset };
    if (mine) params.mine = mine;
    const response = await apiClient.get(`/api/production/records/${datasetKey}`, { params });
    return response.data;
  } catch (error) {
    console.error(`Error fetching records for ${datasetKey}:`, error);
    throw new Error(error.response?.data?.detail || `Failed to retrieve records for dataset ${datasetKey}.`);
  }
};

/**
 * Retrieves list of distinct mine locations.
 * Calls GET /api/production/mines
 */
export const fetchProductionMines = async () => {
  try {
    const response = await apiClient.get('/api/production/mines');
    return response.data?.mines || [];
  } catch (error) {
    console.error('Error fetching mines list:', error);
    return [];
  }
};

/**
 * Retrieves past 7-day production history for a given mine.
 * Calls GET /api/production/history/{mine}
 */
export const fetchMineHistory = async (mine) => {
  try {
    const response = await apiClient.get(`/api/production/history/${encodeURIComponent(mine)}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching history for mine ${mine}:`, error);
    return { success: false, history: [] };
  }
};

/**
 * ML Inference for production shortfall prediction using the 4-model Late Fusion pipeline.
 * Calls POST /api/production/predict
 */
export const predictProductionShortfall = async (payload) => {
  try {
    const response = await apiClient.post('/api/production/predict', payload);
    return response.data;
  } catch (error) {
    console.error('Error in predictProductionShortfall:', error);
    throw new Error(error.response?.data?.detail || 'Production ML prediction request failed.');
  }
};
