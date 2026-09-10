import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { fetchLatestRecommendations, generateRecommendations } from '../services/recommendationService';

/**
 * Recommendations Page
 * --------------------
 * Displays AI/ML + Rule-Based + Knowledge-Based recommendations
 * generated dynamically from the Production Shortfall process.
 * 
 * Design strictly matches reference screenshot (media_1789023564838.jpg).
 */
const Recommendations = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        // If state passed from Production Forecast Step 4
        if (location.state && location.state.predictionData) {
          const res = await generateRecommendations(location.state.predictionData);
          setData(res);
        } else {
          // Fetch latest stored recommendation from MySQL
          const res = await fetchLatestRecommendations();
          if (res && res.success !== false) {
            setData(res);
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

  // Render SVG icon by icon_type
  const renderCardIcon = (iconType) => {
    switch (iconType) {
      case 'sprout':
        return (
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z" />
          </svg>
        );
      case 'gear':
        return (
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
          </svg>
        );
      case 'weather':
        return (
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z" />
          </svg>
        );
      case 'drill':
      case 'target':
      default:
        return (
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
        );
    }
  };

  const getPriorityClass = (priority) => {
    const p = (priority || '').toLowerCase();
    if (p.includes('high')) return 'priority-high';
    if (p.includes('medium')) return 'priority-medium';
    return 'priority-low';
  };

  const cards = data?.cards && data.cards.length > 0 ? data.cards : [];

  return (
    <div className="recommendations-page-container">
      {/* Page Header matching screenshot */}
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
              AI/ML + Rule Based + Knowledge Based suggestions to improve manganese production
            </p>
          </div>
        </div>

        {/* Top Right Badges */}
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
          <p>Analyzing production shortfall constraints and generating recommendations...</p>
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
          <h3 className="empty-title">No production shortfall recommendation is available yet.</h3>
          <p className="empty-desc">
            Execute a Production Forecast to run your mine parameters through the recommendation engine.
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

      {/* Dynamic Recommendation Cards */}
      {!loading && !error && data && cards.length > 0 && (
        <div className="recommendations-cards-list">
          {cards.map((card, idx) => {
            const cardClass = card.card_style || (idx % 3 === 0 ? 'green-card' : idx % 3 === 1 ? 'blue-card' : 'purple-card');
            const iconBg = cardClass.includes('green') ? 'icon-green' : cardClass.includes('purple') ? 'icon-purple' : 'icon-blue';
            const dotColor = cardClass.includes('green') ? 'dot-green' : cardClass.includes('purple') ? 'dot-purple' : 'dot-blue';

            return (
              <div key={card.id || idx} className={`recommendation-card-item ${cardClass}`}>
                {/* Priority Pill Badge in Top-Right */}
                <div className="rec-card-top-row">
                  <span className={`rec-priority-pill ${getPriorityClass(card.priority)}`}>
                    {card.priority || 'Medium Priority'}
                  </span>
                </div>

                <div className="rec-card-main-content">
                  {/* Left Circular Icon Badge */}
                  <div className={`rec-card-icon-badge ${iconBg}`}>
                    {renderCardIcon(card.icon_type)}
                  </div>

                  {/* Card Body */}
                  <div className="rec-card-body">
                    <h3 className="rec-card-title">{card.title}</h3>
                    <p className="rec-card-explanation">{card.explanation}</p>

                    {/* Supporting Points Bullets */}
                    {card.supporting_points && card.supporting_points.length > 0 && (
                      <ul className="rec-card-bullets-list">
                        {card.supporting_points.map((point, pIdx) => (
                          <li key={pIdx} className="rec-card-bullet-item">
                            <span className={`bullet-dot ${dotColor}`}></span>
                            <span className="bullet-text">{point}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Recommendations;
