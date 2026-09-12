/**
 * App Root Component
 * ------------------
 * Configures application routing, global authentication context,
 * and route access control.
 * 
 * Routes:
 * - `/admin-login` -> Admin Login Page (Screenshot 1)
 * - `/user-login`  -> User Login Page (Screenshot 3)
 * - `/admin/users` -> Admin User Management (Screenshot 2, Admin Only)
 * - `/dashboard`, `/ore-prediction`, `/production-forecast`, `/recommendations`
 *   -> Existing application pages (Protected: requires authenticated active session)
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import Dashboard from './pages/Dashboard';
import OrePrediction from './pages/OrePrediction';
import ProductionForecast from './pages/ProductionForecast';
import Recommendations from './pages/Recommendations';
import AdminLogin from './pages/AdminLogin';
import UserLogin from './pages/UserLogin';
import AdminUserManagement from './pages/AdminUserManagement';

// Route Guard: Admin Only Access
const AdminRoute = ({ children }) => {
  const { isAdmin } = useAuth();
  if (!isAdmin) {
    return <Navigate to="/admin-login" replace />;
  }
  return children;
};

// Route Guard & Shell for Standard Application Pages
const ProtectedAppLayout = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/user-login" replace />;
  }

  return (
    <div className="app-layout">
      {/* Shared Single Instance Left Sidebar */}
      <Sidebar />

      {/* Main Content Viewport */}
      <div className="main-wrapper">
        {/* Shared Top Navigation Bar */}
        <Topbar />

        {/* Page Content Viewport Driven by Routes */}
        <div className="page-body-container">
          <Routes>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="ore-prediction" element={<OrePrediction />} />
            <Route path="production-analysis" element={<ProductionForecast />} />
            <Route path="production-forecast" element={<Navigate to="/production-analysis" replace />} />
            <Route path="recommendations" element={<Recommendations />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

// Smart Root Redirect based on role and auth state
const RootRedirect = () => {
  const { isAdmin, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/user-login" replace />;
  }
  if (isAdmin) {
    return <Navigate to="/admin/users" replace />;
  }
  return <Navigate to="/dashboard" replace />;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Authentication Pages */}
      <Route path="/admin-login" element={<AdminLogin />} />
      <Route path="/user-login" element={<UserLogin />} />

      {/* Admin User Management (Admin Only) */}
      <Route
        path="/admin/users"
        element={
          <AdminRoute>
            <AdminUserManagement />
          </AdminRoute>
        }
      />

      {/* Root Path Redirect */}
      <Route path="/" element={<RootRedirect />} />

      {/* Protected Application Routes */}
      <Route path="/*" element={<ProtectedAppLayout />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

export default App;
