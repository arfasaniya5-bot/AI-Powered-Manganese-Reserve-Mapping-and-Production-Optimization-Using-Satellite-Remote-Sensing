/**
 * API Service Module (Axios Client)
 * ---------------------------------
 * Handles HTTP communication between the React frontend and FastAPI backend.
 * 
 * How React communicates with FastAPI:
 * 1. The browser initiates an asynchronous HTTP POST request using Axios.
 * 2. Axios sends the payload as JSON (`{"latitude": 18.5234, "longitude": 79.1234}`)
 *    to http://localhost:8000/api/location.
 * 3. FastAPI receives, parses, and validates the request.
 * 4. Axios returns a JavaScript Promise containing the response data or catches errors.
 */

import axios from 'axios';

// Base URL points to the local FastAPI backend server
const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 8000, // 8-second timeout to detect unreachable backend quickly
});

/**
 * Sends validated latitude and longitude coordinates to FastAPI.
 * 
 * @param {number} latitude - Decimal degrees latitude between -90 and 90
 * @param {number} longitude - Decimal degrees longitude between -180 and 180
 * @returns {Promise<Object>} The response data from FastAPI { success, latitude, longitude, message }
 */
export const sendLocationCoordinates = async (latitude, longitude) => {
  try {
    const response = await apiClient.post('/api/location', {
      latitude: Number(latitude),
      longitude: Number(longitude),
    });
    return response.data;
  } catch (error) {
    // Detailed error categorization for clear user feedback:
    if (!error.response) {
      // Network error / Server down (no HTTP response received)
      throw new Error(
        'Cannot connect to backend server. Please make sure the FastAPI server is running on http://localhost:8000.'
      );
    }

    // Backend responded with an HTTP status code (4xx, 5xx)
    const detail = error.response.data?.detail;
    if (typeof detail === 'string') {
      throw new Error(detail);
    } else if (Array.isArray(detail) && detail.length > 0) {
      // Pydantic validation error format
      const fieldError = detail.map((err) => `${err.loc?.slice(-1)[0]}: ${err.msg}`).join(', ');
      throw new Error(`Validation Error: ${fieldError}`);
    } else {
      throw new Error(
        `Server returned error ${error.response.status}: ${error.response.statusText || 'Unable to validate location'}`
      );
    }
  }
};

/**
 * Checks if the FastAPI backend is online and healthy.
 * Calls GET /api/health.
 */
export const checkBackendHealth = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return response.data?.status === 'ok';
  } catch {
    return false;
  }
};

export default apiClient;
