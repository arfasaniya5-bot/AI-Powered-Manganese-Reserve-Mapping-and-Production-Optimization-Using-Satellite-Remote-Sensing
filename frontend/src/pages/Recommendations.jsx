import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  fetchLatestRecommendations,
  generateRecommendations,
  updateRecommendationStatus
} from '../services/recommendationService';

/**
 * Recommendations Page
 * --------------------
 * Simplified, user-friendly recommendations module for GeoMineAI.
 * 
 * Organized strictly into 6 clear sections:
 * 1. Production Status
 * 2. Possible Reasons
 * 3. What You Can Do
 * 4. Similar Past Cases
 * 5. Action Status
 * 6. Next Step
 */
const Recommendations = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [cardStatuses, setCardStatuses] = useState({});
  const [updatingId, setUpdatingId] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        if (location.state && location.state.predictionData) {
          const res = await generateRecommendations(location.state.predictionData);
          setData(res);
          if (res?.cards) {
            const initialStatuses = {};
            res.cards.forEach((c) => {
              initialStatuses[c.id] = c.is_escalated ? 'Unsuccessful' : 'Pending';
            });
            setCardStatuses(initialStatuses);
          }
        } else {
          const res = await fetchLatestRecommendations();
          if (res && res.success !== false) {
            setData(res);
            if (res?.cards) {
              const initialStatuses = {};
              res.cards.forEach((c) => {
                initialStatuses[c.id] = c.is_escalated ? 'Unsuccessful' : 'Pending';
              });
              setCardStatuses(initialStatuses);
            }
          } else {
            setData(null);
          }
        }
      } catch (err) {
        console.error('Failed to load recommendations:', err);
        setError(err.message || 'Could not load recommendations.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [location.state]);

  const handleStatusChange = async (cardId, newStatus) => {
    if (!data?.recommendation_id) {
      setCardStatuses((prev) => ({ ...prev, [cardId]: newStatus }));
      return;
    }
    setUpdatingId(cardId);
    try {
      // Map display status to backend status code
      let backendStatus = 'IN_PROGRESS';
      let outcome = null;
      if (newStatus === 'Completed') {
        backendStatus = 'COMPLETED';
        outcome = 'RESOLVED';
      } else if (newStatus === 'Successful') {
        backendStatus = 'COMPLETED';
        outcome = 'RESOLVED';
      } else if (newStatus === 'Unsuccessful') {
        backendStatus = 'ESCALATED';
        outcome = 'FAILED';
      } else if (newStatus === 'In Progress') {
        backendStatus = 'IN_PROGRESS';
        outcome = 'PENDING';
      } else {
        backendStatus = 'PROPOSED';
      }

      await updateRecommendationStatus(data.recommendation_id, backendStatus, outcome);
      setCardStatuses((prev) => ({ ...prev, [cardId]: newStatus }));
    } catch (err) {
      console.error('Failed to update status:', err);
      // Still update UI locally so the user sees their interaction
      setCardStatuses((prev) => ({ ...prev, [cardId]: newStatus }));
    } finally {
      setUpdatingId(null);
    }
  };

  // Helper formatting functions
  const formatStatusText = (status) => {
    if (!status) return 'Low Risk';
    const s = status.toUpperCase();
    if (s.includes('HIGH')) return 'High Risk';
    if (s.includes('MEDIUM')) return 'Medium Risk';
    if (s.includes('TARGET')) return 'On Target';
    return 'Low Risk';
  };

  const getStatusColorClass = (status) => {
    if (!status) return 'status-low-risk';
    const s = status.toUpperCase();
    if (s.includes('HIGH')) return 'status-high-risk';
    if (s.includes('MEDIUM')) return 'status-medium-risk';
    if (s.includes('TARGET')) return 'status-on-target';
    return 'status-low-risk';
  };

  const getPriorityClass = (priority) => {
    const p = (priority || '').toLowerCase();
    if (p.includes('high')) return 'priority-high';
    if (p.includes('medium')) return 'priority-medium';
    return 'priority-low';
  };

  // Strip technical strings from reasons (e.g. "matched with Case..." or similarity percentages)
  const cleanReasonText = (text) => {
    if (!text) return '';
    return text
      .replace(/\s*\(matched with Case [^)]+\)/gi, '')
      .replace(/Weather impact score [\d\.]+\s*[-—]?\s*/gi, '')
      .replace(/\s*\(2025 seasonal pattern used as proxy for this calendar date\)/gi, '')
      .replace(/[^\x20-\x7E]+/g, ' ')
      .trim();
  };

  const cards = data?.cards && data.cards.length > 0 ? data.cards : [];
  const rawReasons = data?.possible_reasons && data.possible_reasons.length > 0 ? data.possible_reasons : [];
  const cleanReasons = rawReasons.map(cleanReasonText).filter(Boolean);

  return (
    <div className="recommendations-page-container">
      {/* Page Header */}
      <div className="recommendations-header-row">
        <div className="recommendations-title-block">
          <div className="recommendations-bulb-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18h6" />
              <path d="M10 22h4" />
              <path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z" />
            </svg>
          </div>
          <div>
            <h1 className="recommendations-main-title">Recommendations</h1>
            <p className="recommendations-sub-title">
              Simple suggestions to help your mine meet production targets
            </p>
          </div>
        </div>

        {/* Location & Date Badges */}
        <div className="recommendations-meta-badges">
          <div className="meta-pill-badge">
            <div className="meta-pill-icon blue-pin">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
              </svg>
            </div>
            <div className="meta-pill-text">
              <span className="meta-pill-label">Location</span>
              <span className="meta-pill-val">{data?.mine || 'Balaghat'}</span>
            </div>
          </div>

          <div className="meta-pill-badge">
            <div className="meta-pill-icon blue-calendar">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z" />
              </svg>
            </div>
            <div className="meta-pill-text">
              <span className="meta-pill-label">Date</span>
              <span className="meta-pill-val">{data?.date || '14-09-2026'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="recommendations-state-box">
          <div className="recommendations-spinner"></div>
          <p>Analyzing mine conditions and preparing practical recommendations...</p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="recommendations-state-box error-box">
          <svg viewBox="0 0 24 24" fill="currentColor" width="36" height="36">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
          <p className="state-msg">{error}</p>
          <button
            type="button"
            className="forecast-btn-primary"
            onClick={() => navigate('/production-forecast')}
          >
            Run Production Forecast
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && (!data || cards.length === 0) && (
        <div className="recommendations-state-box empty-box">
          <div className="empty-bulb-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18h6" />
              <path d="M10 22h4" />
              <path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z" />
            </svg>
          </div>
          <h3 className="empty-title">No similar cases were found. Please review the situation with the site team.</h3>
          <p className="empty-desc">
            Execute a Production Forecast to check your mine parameters and view suggestions.
          </p>
          <button
            type="button"
            className="forecast-btn-primary"
            onClick={() => navigate('/production-forecast')}
          >
            Go to Production Forecast &rarr;
          </button>
        </div>
      )}

      {/* Content Area when Data is Ready */}
      {!loading && !error && data && (
        <>
          {/* ==============================================================
              SECTION 1: PRODUCTION STATUS (Replacing Production Risk)
              ============================================================== */}
          <div className="rec-section-card production-status-card">
            <div className="rec-section-header">
              <h2 className="rec-section-title">Production Status</h2>
              <span className={`status-pill ${getStatusColorClass(data.status)}`}>
                {formatStatusText(data.status)}
              </span>
            </div>

            <div className="production-status-grid">
              <div className="status-metric">
                <span className="metric-label">Target Production</span>
                <span className="metric-value">
                  {data.target_production ? Number(data.target_production).toLocaleString() : '10,000'} tonnes
                </span>
              </div>
              <div className="status-metric">
                <span className="metric-label">Expected Production</span>
                <span className="metric-value">
                  {data.predicted_production ? Number(data.predicted_production).toLocaleString() : '—'} tonnes
                </span>
              </div>
              <div className="status-metric">
                <span className="metric-label">Expected Shortfall</span>
                <span className={`metric-value ${Number(data.shortfall_tonnes) > 0 ? 'text-danger' : 'text-success'}`}>
                  {Number(data.shortfall_tonnes) > 0
                    ? `${Number(data.shortfall_tonnes).toLocaleString()} tonnes (${Number(data.shortfall_percentage || 0).toFixed(1)}%)`
                    : '0 tonnes (On Track)'}
                </span>
              </div>
            </div>

            <p className="status-summary-text">
              {Number(data.shortfall_tonnes) > 0
                ? `Production is expected to be ${Number(data.shortfall_tonnes).toLocaleString()} tonnes below the target.`
                : 'Production is on track to meet the planned target.'}
            </p>
          </div>

          {/* ==============================================================
              SECTION 2: POSSIBLE REASONS (Replacing Contributing Factors)
              ============================================================== */}
          <div className="rec-section-card possible-reasons-card">
            <h2 className="rec-section-title">Possible Reasons</h2>
            {cleanReasons.length > 0 ? (
              <ul className="reasons-clean-list">
                {cleanReasons.map((reason, idx) => (
                  <li key={idx} className="reason-clean-item">
                    <span className="reason-bullet" />
                    <span className="reason-text">{reason}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="no-cases-text">Some information is unavailable.</p>
            )}
          </div>

          {/* ==============================================================
              SECTION 3, 5, 6: WHAT YOU CAN DO (with Action Status & Next Step)
              ============================================================== */}
          <div className="rec-section-card what-you-can-do-section">
            <div className="rec-section-header">
              <h2 className="rec-section-title">What You Can Do</h2>
              <span className="section-sub-hint">Recommended actions supported by past mining cases</span>
            </div>

            {cards.length === 0 ? (
              <div className="no-actions-notice">
                <p>No similar cases were found. Please review the situation with the site team.</p>
              </div>
            ) : (
              <div className="action-items-list">
                {cards.map((card, idx) => {
                  const currentStatus = cardStatuses[card.id] || (card.is_escalated ? 'Unsuccessful' : 'Pending');
                  const isUnsuccessful = currentStatus === 'Unsuccessful' || card.is_escalated;
                  const nextStepText = card.follow_up_action || (card.is_escalated ? card.action : null);

                  // Extract clean priority: High / Medium / Low
                  const cleanPriority = card.priority
                    ? card.priority.replace(/ priority/gi, '').trim()
                    : null;

                  return (
                    <div key={card.id || idx} className="simple-action-card">
                      {/* Top Action Title & Priority */}
                      <div className="action-card-top">
                        <div className="action-num-title">
                          <span className="action-number">{idx + 1}.</span>
                          <h3 className="action-title">{card.title || `Action ${idx + 1}`}</h3>
                        </div>
                        {cleanPriority && (
                          <span className={`priority-pill ${getPriorityClass(cleanPriority)}`}>
                            Priority: {cleanPriority}
                          </span>
                        )}
                      </div>

                      {/* One short sentence explaining the action */}
                      <p className="action-simple-sentence">
                        {card.action}
                      </p>

                      {/* SECTION 5: ACTION STATUS */}
                      <div className="action-status-bar">
                        <div className="status-indicator-group">
                          <span className="status-indicator-label">Action Status:</span>
                          <span className={`status-pill-current status-${currentStatus.toLowerCase().replace(/\s+/g, '-')}`}>
                            {currentStatus}
                          </span>
                        </div>

                        <div className="status-buttons-row">
                          {['In Progress', 'Completed', 'Successful', 'Unsuccessful'].map((st) => (
                            <button
                              key={st}
                              type="button"
                              className={`simple-status-btn ${currentStatus === st ? 'active' : ''}`}
                              onClick={() => handleStatusChange(card.id, st)}
                              disabled={updatingId === card.id}
                            >
                              {st}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* SECTION 6: NEXT STEP (Displayed if Unsuccessful or if follow-up exists) */}
                      {isUnsuccessful && nextStepText && (
                        <div className="next-step-box">
                          <span className="next-step-label">Next Step:</span>
                          <span className="next-step-content">{nextStepText}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default Recommendations;
