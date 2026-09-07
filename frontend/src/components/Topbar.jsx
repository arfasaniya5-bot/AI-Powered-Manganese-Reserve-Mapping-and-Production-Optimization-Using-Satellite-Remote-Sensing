/**
 * Topbar Component
 * ----------------
 * Renders the top navigation header across the application.
 * 
 * Features matching reference images:
 * - Search bar with magnifying glass icon and placeholder "Search location, mine or report..."
 * - Notification bell icon with active red indicator dot
 * - Admin profile section displaying user avatar, name "Admin", and dropdown arrow
 */

import React, { useState } from 'react';

const Topbar = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      alert(`Search for "${searchTerm}" will be supported in a future release.`);
    }
  };

  return (
    <header className="app-topbar">
      {/* Search Input Bar */}
      <div className="topbar-search-container">
        <form onSubmit={handleSearchSubmit} className="search-form">
          <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            className="search-input"
            placeholder="Search location, mine or report..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search"
          />
        </form>
      </div>

      {/* Right Controls: Notifications & Admin Profile */}
      <div className="topbar-actions">
        {/* Notification Bell with Badge */}
        <button className="notification-btn" aria-label="Notifications" title="1 new notification">
          <svg className="bell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span className="notification-badge" aria-hidden="true"></span>
        </button>

        {/* Admin Profile Section */}
        <div className="admin-profile-pill" title="Logged in as Admin">
          <div className="admin-avatar">
            {/* SVG silhouette / avatar icon */}
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
            </svg>
          </div>
          <span className="admin-name">Admin</span>
          <svg className="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
