/**
 * Recommendations API Service
 * ---------------------------
 * Connects the React frontend to the FastAPI Recommendation endpoints.
 * Reuses the existing apiClient instance from api.js.
 */

import apiClient from './api';

/**
 * Fetches the latest production shortfall recommendations stored in MySQL.
 * Calls GET /api/recommendations/latest
 */
export const fetchLatestRecommendations = async (mine = null) => {
  try {
    const params = mine ? { mine } : {};
    const response = await apiClient.get('/api/recommendations/latest', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching latest recommendations:', error);
    throw new Error(error.response?.data?.detail || 'Failed to retrieve recommendations from backend.');
  }
};

/**
 * Generates recommendations directly from production shortfall payload.
 * Calls POST /api/recommendations
 */
export const generateRecommendations = async (payload) => {
  try {
    const response = await apiClient.post('/api/recommendations', payload);
    return response.data;
  } catch (error) {
    console.error('Error generating recommendations:', error);
    throw new Error(error.response?.data?.detail || 'Failed to generate recommendations.');
  }
};
