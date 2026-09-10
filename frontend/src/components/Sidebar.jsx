/**
 * Sidebar Component
 * -----------------
 * Renders the persistent dark navy left navigation sidebar.
 * 
 * Why this component is required:
 * Provides unified navigation across the ManganeseInsight application.
 * Using React Router's `NavLink`, the active route automatically receives
 * the 'active' CSS class, highlighting the current page without manual state tracking.
 * 
 * Specific constraints followed:
 * - Contains only the 5 required navigation items:
 *   1. Dashboard
 *   2. Ore Prediction
 *   3. Production Analysis
 *   4. Recommendations
 *   5. About
 * - "Interactive Map" and "Data Records" are strictly omitted.
 */

import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  return (
    <aside className="app-sidebar">
      {/* Brand Header: Logo and Subtitle */}
      <div className="sidebar-brand">
        <div className="brand-icon-wrapper">
          {/* Custom vector graphic matching the green & blue mineral mountain logo */}
          <svg
            className="brand-logo-svg"
            viewBox="0 0 40 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-label="ManganeseInsight Logo"
          >
            {/* Left peak: Sky Blue */}
            <path
              d="M14 2L2 28H18L24 16L14 2Z"
              fill="#0ea5e9"
            />
            {/* Right peak: Vibrant Emerald Green */}
            <path
              d="M24 10L14 28H38L24 10Z"
              fill="#10b981"
            />
          </svg>
        </div>
        <div className="brand-text-block">
          <span className="brand-title">ManganeseInsight</span>
          <span className="brand-tagline">Exploring a Sustainable Tomorrow</span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="sidebar-nav" aria-label="Main Navigation">
        <div className="nav-group-primary">
          {/* 1. Dashboard */}
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
            </svg>
            <span className="nav-label">Dashboard</span>
          </NavLink>

          {/* Production Forecast */}
          <NavLink
            to="/production-forecast"
            className={({ isActive }) =>
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14l-5-5 1.41-1.41L12 14.17l7.59-7.59L21 8l-9 9z" />
            </svg>
            <span className="nav-label">Production Forecast</span>
          </NavLink>

          {/* 2. Ore Prediction */}
          <NavLink
            to="/ore-prediction"
            className={({ isActive }) =>
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
            </svg>
            <span className="nav-label">Ore Prediction</span>
          </NavLink>

          {/* 3. Production Analysis */}
          <NavLink
            to="/production-analysis"
            className={({ isActive }) =>
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z" />
            </svg>
            <span className="nav-label">Production Analysis</span>
          </NavLink>

          {/* 4. Recommendations */}
          <NavLink
            to="/recommendations"
            className={({ isActive }) =>
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z" />
            </svg>
            <span className="nav-label">Recommendations</span>
          </NavLink>
        </div>

        {/* 5. About Section (Positioned with clean separation) */}
        <div className="nav-group-bottom">
          <NavLink
            to="/about"
            className={({ isActive }) =>
              `nav-link ${isActive ? 'nav-link-active' : ''}`
            }
            onClick={(e) => {
              e.preventDefault();
              alert('ManganeseInsight: Using AI/ML and Space Technology to Identify Manganese Reserves.');
            }}
          >
            <svg className="nav-icon" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11 17h2v-6h-2v6zm1-15C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zM11 9h2V7h-2v2z" />
            </svg>
            <span className="nav-label">About</span>
          </NavLink>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
