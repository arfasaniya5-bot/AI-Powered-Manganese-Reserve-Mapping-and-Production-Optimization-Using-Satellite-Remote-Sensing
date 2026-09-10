/**
 * Auth Service Module
 * -------------------
 * Manages API requests for Admin Login, User Login, Logout,
 * and Admin User Management (Create, List, Update, Delete).
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('moil_admin_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const authService = {
  /**
   * Log in as Administrator
   */
  async adminLogin(adminId, password) {
    const response = await axios.post(`${API_BASE_URL}/api/auth/admin/login`, {
      admin_id: adminId,
      password: password,
    });
    if (response.data && response.data.token) {
      localStorage.setItem('moil_admin_token', response.data.token);
      localStorage.setItem('moil_admin_user', JSON.stringify(response.data.admin));
      localStorage.setItem('moil_role', 'ADMIN');
    }
    return response.data;
  },

  /**
   * Log in as Regular User (MOIL Employee)
   */
  async userLogin(employeeId, password) {
    const response = await axios.post(`${API_BASE_URL}/api/auth/user/login`, {
      employee_id: employeeId,
      password: password,
    });
    if (response.data && response.data.token) {
      localStorage.setItem('moil_user_token', response.data.token);
      localStorage.setItem('moil_current_user', JSON.stringify(response.data.user));
      localStorage.setItem('moil_role', 'USER');
    }
    return response.data;
  },

  /**
   * Logout session (clears local credentials & notifies backend)
   */
  async logout() {
    try {
      await axios.post(`${API_BASE_URL}/api/auth/logout`, {}, {
        headers: getAuthHeaders(),
      });
    } catch (e) {
      // Proceed with local storage clear regardless
    }
    localStorage.removeItem('moil_admin_token');
    localStorage.removeItem('moil_admin_user');
    localStorage.removeItem('moil_user_token');
    localStorage.removeItem('moil_current_user');
    localStorage.removeItem('moil_role');
  },

  getCurrentRole() {
    return localStorage.getItem('moil_role');
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('moil_current_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getCurrentAdmin() {
    const adminStr = localStorage.getItem('moil_admin_user');
    return adminStr ? JSON.parse(adminStr) : null;
  },

  isAdmin() {
    return localStorage.getItem('moil_role') === 'ADMIN' && !!localStorage.getItem('moil_admin_token');
  },

  isUser() {
    return localStorage.getItem('moil_role') === 'USER' && !!localStorage.getItem('moil_user_token');
  },

  isAuthenticated() {
    return this.isAdmin() || this.isUser();
  },

  // --------------------------------------------------------------------------
  // Admin User Management Operations
  // --------------------------------------------------------------------------

  async getUsers() {
    const response = await axios.get(`${API_BASE_URL}/api/users`, {
      headers: getAuthHeaders(),
    });
    return response.data?.users || [];
  },

  async createUser(employeeId, name, password) {
    const response = await axios.post(
      `${API_BASE_URL}/api/users`,
      {
        employee_id: employeeId,
        name: name,
        password: password,
      },
      {
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  },

  async updateUser(userId, data) {
    const response = await axios.put(
      `${API_BASE_URL}/api/users/${userId}`,
      data,
      {
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  },

  async deleteUser(userId) {
    const response = await axios.delete(
      `${API_BASE_URL}/api/users/${userId}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return response.data;
  },
};

export default authService;
