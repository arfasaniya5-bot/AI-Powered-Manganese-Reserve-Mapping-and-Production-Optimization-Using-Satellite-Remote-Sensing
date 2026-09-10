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
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Topbar = () => {
  const navigate = useNavigate();
  const { currentUser, currentAdmin, logout, isAdmin } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);

  const displayName = currentUser?.name || currentAdmin?.name || (isAdmin ? 'Admin' : 'MOIL User');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      alert(`Search for "${searchTerm}" will be supported in a future release.`);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/user-login');
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

      {/* Right Controls: Notifications & Profile */}
      <div className="topbar-actions">
        {/* Notification Bell with Badge */}
        <button className="notification-btn" aria-label="Notifications" title="1 new notification">
          <svg className="bell-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span className="notification-badge" aria-hidden="true"></span>
        </button>

        {/* Profile Section with Logout Dropdown */}
        <div className="profile-menu-wrapper" style={{ position: 'relative' }}>
          <div
            className="admin-profile-pill"
            title={`Logged in as ${displayName}`}
            onClick={() => setShowDropdown(!showDropdown)}
            style={{ cursor: 'pointer' }}
          >
            <div className="admin-avatar">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            </div>
            <span className="admin-name">{displayName}</span>
            <svg className="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>

          {showDropdown && (
            <div
              className="topbar-dropdown-menu"
              style={{
                position: 'absolute',
                right: 0,
                top: 'calc(100% + 8px)',
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                padding: '8px',
                minWidth: '160px',
                zIndex: 100,
              }}
            >
              {isAdmin && (
                <button
                  type="button"
                  onClick={() => {
                    setShowDropdown(false);
                    navigate('/admin/users');
                  }}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '8px 12px',
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                    borderRadius: '6px',
                    fontSize: '13.5px',
                    color: '#1e293b',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}>
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                  User Management
                </button>
              )}
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 12px',
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  borderRadius: '6px',
                  fontSize: '13.5px',
                  color: '#ef4444',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}>
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Topbar;
