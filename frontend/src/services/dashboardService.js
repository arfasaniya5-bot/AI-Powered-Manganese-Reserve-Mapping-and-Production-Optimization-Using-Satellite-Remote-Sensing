/**
 * Dashboard Service
 * -----------------
 * Handles fetching aggregated dashboard data from FastAPI (/api/dashboard).
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const dashboardService = {
  /**
   * Fetches aggregated dashboard metrics, trends, reserves, and summaries.
   */
  async getDashboardData() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard`, {
        timeout: 10000,
      });
      return response.data;
    } catch (error) {
      console.warn('[DashboardService] Failed to load dashboard from API:', error.message);
      throw error;
    }
  },
};

export default dashboardService;
