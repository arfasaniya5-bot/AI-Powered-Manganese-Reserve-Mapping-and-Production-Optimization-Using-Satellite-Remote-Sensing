/**
 * Dashboard Page Component
 * ------------------------
 * Primary landing view of ManganeseInsight.
 * 
 * Strict constraints adhered to:
 * - Heading: "Dashboard"
 * - Subtitle: "AI/ML + Space Technology for Manganese Exploration and Production"
 * - Content area: Renders a single centered placeholder line:
 *   "Dashboard widgets coming soon."
 * - No charts, cards, statistics, or production graphs added yet.
 * - "Interactive Map" and "Data Records" do not appear anywhere.
 */

import React from 'react';

const Dashboard = () => {
  return (
    <div className="page-content dashboard-page">
      {/* Page Header */}
      <header className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          AI/ML + Space Technology for Manganese Exploration and Production
        </p>
      </header>

      {/* Main Content Area: Centered placeholder line per prompt instruction */}
      <main className="dashboard-content-area">
        <div className="placeholder-container">
          <p className="dashboard-placeholder-text">Dashboard widgets coming soon.</p>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
