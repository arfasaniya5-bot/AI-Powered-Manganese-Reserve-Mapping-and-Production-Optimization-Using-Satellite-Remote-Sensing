/**
 * Dashboard Service
 * -----------------
 * Handles fetching aggregated dashboard data from FastAPI (/api/dashboard).
 * Supports optional mine parameter for connected cross-filtering.
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const dashboardService = {
  /**
   * Fetches aggregated dashboard metrics, trends, reserves, and summaries.
   * @param {string|null} mine - Optional mine name to filter data
   */
  async getDashboardData(mine = null) {
    try {
      const params = {};
      if (mine && mine !== 'All Mines') {
        params.mine = mine;
      }
      const response = await axios.get(`${API_BASE_URL}/api/dashboard`, {
        params,
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
