/**
 * Recommendations API Service
 * ---------------------------
 * Connects the React frontend to the FastAPI Recommendation CBR endpoints.
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
 * Generates recommendations directly from production shortfall payload using the CBR engine.
 * Calls POST /api/recommendations/generate
 */
export const generateRecommendations = async (payload) => {
  try {
    const response = await apiClient.post('/api/recommendations/generate', payload);
    return response.data;
  } catch (error) {
    console.error('Error generating recommendations:', error);
    throw new Error(error.response?.data?.detail || 'Failed to generate recommendations.');
  }
};

/**
 * Fetches Top-K similar prototype cases for a specific recommendation run.
 * Calls GET /api/recommendations/{recommendationId}/similar-cases
 */
export const fetchSimilarCases = async (recommendationId) => {
  try {
    const response = await apiClient.get(`/api/recommendations/${recommendationId}/similar-cases`);
    return response.data;
  } catch (error) {
    console.error('Error fetching similar cases:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch similar prototype cases.');
  }
};

/**
 * Fetches recommendation history with progressive intervention tracking.
 * Calls GET /api/recommendations/history
 */
export const fetchRecommendationHistory = async (mine = null, limit = 50) => {
  try {
    const params = { limit };
    if (mine) params.mine = mine;
    const response = await apiClient.get('/api/recommendations/history', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching recommendation history:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch recommendation history.');
  }
};

/**
 * Updates action status, outcome, or follow-up action for progressive tracking.
 * Calls PATCH /api/recommendations/{recommendationId}/status
 */
export const updateRecommendationStatus = async (recommendationId, actionStatus, outcome = null, followUpAction = null) => {
  try {
    const response = await apiClient.patch(`/api/recommendations/${recommendationId}/status`, {
      action_status: actionStatus,
      outcome,
      follow_up_action: followUpAction
    });
    return response.data;
  } catch (error) {
    console.error('Error updating recommendation status:', error);
    throw new Error(error.response?.data?.detail || 'Failed to update recommendation status.');
  }
};
