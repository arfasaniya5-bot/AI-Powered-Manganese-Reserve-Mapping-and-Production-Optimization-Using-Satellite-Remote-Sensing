/**
 * AuthContext Component
 * ---------------------
 * Global authentication state provider for the ManganeseInsight application.
 * Manages user/admin login states, session synchronization with localStorage,
 * and handles protected route authorization.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(() => authService.getCurrentUser());
  const [currentAdmin, setCurrentAdmin] = useState(() => authService.getCurrentAdmin());
  const [role, setRole] = useState(() => authService.getCurrentRole());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Sync state on mount
    setCurrentUser(authService.getCurrentUser());
    setCurrentAdmin(authService.getCurrentAdmin());
    setRole(authService.getCurrentRole());
  }, []);

  const loginAdmin = async (adminId, password) => {
    setLoading(true);
    try {
      const data = await authService.adminLogin(adminId, password);
      setCurrentAdmin(data.admin);
      setRole('ADMIN');
      return data;
    } finally {
      setLoading(false);
    }
  };

  const loginUser = async (employeeId, password) => {
    setLoading(true);
    try {
      const data = await authService.userLogin(employeeId, password);
      setCurrentUser(data.user);
      setRole('USER');
      return data;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await authService.logout();
    setCurrentUser(null);
    setCurrentAdmin(null);
    setRole(null);
  };

  const value = {
    currentUser,
    currentAdmin,
    role,
    isAuthenticated: authService.isAuthenticated(),
    isAdmin: role === 'ADMIN' && !!currentAdmin,
    isUser: role === 'USER' && !!currentUser,
    loginAdmin,
    loginUser,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
