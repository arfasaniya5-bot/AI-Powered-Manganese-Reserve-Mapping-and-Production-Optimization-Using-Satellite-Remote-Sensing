/**
 * User Login Page
 * ---------------
 * Implements Screenshot 3 design reference.
 * Authenticates MOIL Employee, strictly enforces Active status approval,
 * and navigates to the existing application dashboard upon successful login.
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const UserLogin = () => {
  const navigate = useNavigate();
  const { loginUser } = useAuth();

  const [employeeId, setEmployeeId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isPendingApproval, setIsPendingApproval] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setIsPendingApproval(false);

    if (!employeeId.trim() || !password) {
      setErrorMsg('Please enter both Employee ID and Password.');
      return;
    }

    setSubmitting(true);
    try {
      await loginUser(employeeId.trim(), password);
      // Navigate to existing application dashboard on successful login
      navigate('/dashboard');
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 403 || (detail && detail.includes('approval'))) {
        setIsPendingApproval(true);
        setErrorMsg('Your account is pending administrator approval.');
      } else if (status === 401 || (detail && detail.includes('Invalid'))) {
        setErrorMsg('Invalid Employee ID or password.');
      } else {
        setErrorMsg(detail || err.message || 'Login failed. Please check your credentials.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page-wrapper">
      <div className="auth-card-container">
        {/* Left Side: MOIL Mining Brand Visual */}
        <div className="auth-brand-pane">
          <div className="brand-pane-overlay" />
          <div className="brand-pane-content">
            {/* Top Brand Logo */}
            <div className="brand-header-box">
              <div className="brand-logo-symbol">
                <svg viewBox="0 0 40 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="auth-mountain-svg">
                  <path d="M14 2L2 28H18L24 16L14 2Z" fill="#0ea5e9" />
                  <path d="M24 10L14 28H38L24 10Z" fill="#10b981" />
                </svg>
              </div>
              <h1 className="brand-moil-title">MOIL</h1>
              <h2 className="brand-platform-name">ManganeseInsight</h2>
              <p className="brand-platform-motto">Predict Today, Mine Tomorrow</p>
            </div>

            {/* Bottom Tagline */}
            <div className="brand-footer-box">
              <h3 className="brand-slogan-text">Sustainable Mining for a Stronger India</h3>
              <p className="brand-company-name">MOIL Limited</p>
            </div>
          </div>
        </div>

        {/* Right Side: User Login Form */}
        <div className="auth-form-pane">
          <div className="auth-form-box">
            <div className="auth-form-heading">
              <h2 className="auth-title">User Login</h2>
              <p className="auth-subtitle">Access your dashboard</p>
            </div>

            {/* Error / Approval Message Banner */}
            {errorMsg && (
              <div
                className={isPendingApproval ? 'auth-alert-warning' : 'auth-alert-error'}
                role="alert"
              >
                <svg viewBox="0 0 20 20" fill="currentColor" className="alert-icon">
                  {isPendingApproval ? (
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  ) : (
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  )}
                </svg>
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              {/* Employee ID Field */}
              <div className="auth-input-group">
                <div className="input-with-icon">
                  <span className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                  </span>
                  <input
                    type="text"
                    id="employee-id-input"
                    className="auth-text-input"
                    placeholder="Employee ID"
                    value={employeeId}
                    onChange={(e) => setEmployeeId(e.target.value)}
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              {/* Password Field with Show/Hide Toggle */}
              <div className="auth-input-group">
                <div className="input-with-icon">
                  <span className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  </span>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="user-password-input"
                    className="auth-text-input"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    tabIndex="-1"
                  >
                    {showPassword ? (
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    ) : (
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Login Button */}
              <button
                type="submit"
                className="auth-submit-btn"
                disabled={submitting}
              >
                {submitting ? 'Authenticating...' : 'Login'}
              </button>

              {/* Informational Message Box */}
              <div className="auth-info-card">
                <div className="info-icon-wrapper">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" strokeWidth="2" className="info-blue-icon">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                  </svg>
                </div>
                <span className="info-card-text">Contact your administrator for account access.</span>
              </div>

              {/* Switch to Admin Login */}
              <div className="auth-switch-link">
                <Link to="/admin-login">Administrator Login →</Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserLogin;
