/**
 * App Root Component
 * ------------------
 * Configures application routing and unified layout.
 * 
 * Architecture:
 * - Persistent Sidebar on the left (never re-mounted when changing pages).
 * - Persistent Topbar on the top.
 * - Dynamic route view in the main container:
 *   - `/` redirects to `/dashboard`
 *   - `/dashboard` renders the Dashboard view
 *   - `/ore-prediction` renders the Ore / Deposit Prediction view
 *   - All unmatched paths fallback cleanly to `/dashboard`
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import Dashboard from './pages/Dashboard';
import OrePrediction from './pages/OrePrediction';

function App() {
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
            {/* Default route redirects to /dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* Dashboard Route */}
            <Route path="/dashboard" element={<Dashboard />} />

            {/* Ore / Deposit Prediction Route */}
            <Route path="/ore-prediction" element={<OrePrediction />} />

            {/* Fallback for undefined routes */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default App;
