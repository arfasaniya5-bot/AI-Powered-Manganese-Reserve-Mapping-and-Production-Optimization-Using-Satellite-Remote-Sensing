/**
 * Main User Dashboard Page
 * ------------------------
 * Fully interactive monitoring and decision-support dashboard for GeoMineAI.
 * 
 * Interactive Features:
 * 1. Active Mines Card: Dynamic count + "View Mines" popover showing active mines list with click-to-filter.
 * 2. Full India Reserves Map: Interactive nationwide map in one consistent highlight color (#0284c7), hover tooltips, click details, and zoom.
 * 3. Connected Production Trend Graph: Filter by selected mine or "All Mines", toggle between Actual/Predicted/All, point hover tooltips.
 * 4. Recent Production Summary Table: Clickable mine rows updating Trend Graph and Shortfall Analysis.
 * 5. Shortfall Analysis Donut: Dynamic metrics per selected mine or cluster, with interactive slice hover.
 * 6. Connected Dashboard State: Seamless bidirectional synchronization between components with an easy "All Mines" reset.
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { dashboardService } from '../services/dashboardService';
import IndiaReservesMap from '../components/IndiaReservesMap';

const Dashboard = () => {
  const navigate = useNavigate();
  const { currentUser, currentAdmin, logout } = useAuth();

  // Dynamic user name from authentication state
  const userName = currentUser?.name || currentAdmin?.name || 'Ravi Kumar';

  // Dynamic formatted current date
  const currentDateStr = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date());

  // Dashboard Data & Loading State
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Connected Dashboard State: Selected Mine (null = All Mines)
  const [selectedMine, setSelectedMine] = useState(null);

  // Active Mines Popover State
  const [viewMinesOpen, setViewMinesOpen] = useState(false);
  const popoverRef = useRef(null);

  // Production Trend Line Toggle State: 'all' | 'actual' | 'predicted'
  const [trendViewMode, setTrendViewMode] = useState('all');
  const [hoveredTrendPoint, setHoveredTrendPoint] = useState(null);

  // Shortfall Donut Slice Hover State
  const [hoveredDonutSlice, setHoveredDonutSlice] = useState(null);

  // Load dashboard data from FastAPI backend
  const loadData = async (filterMine = null) => {
    try {
      const data = await dashboardService.getDashboardData(filterMine);
      setDashboardData(data);
      setLoading(false);
    } catch (err) {
      console.warn('[Dashboard] Error loading data, using local fallback:', err.message);
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Close Active Mines popover on outside click
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        setViewMinesOpen(false);
      }
    };
    if (viewMinesOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [viewMinesOpen]);

  // Handler for selecting a mine (from table, popover, or map)
  const handleSelectMine = (mineName) => {
    if (!mineName || mineName === 'All Mines' || mineName === selectedMine) {
      setSelectedMine(null);
      setViewMinesOpen(false);
    } else {
      setSelectedMine(mineName);
      setViewMinesOpen(false);
    }
  };

  const d = dashboardData || {};

  // Extract Active Mines
  const activeMinesList = d.active_mines?.names || ['Balaghat', 'Ukwa', 'Tirodi', 'Chikla'];
  const activeMinesCount = d.active_mines?.count || activeMinesList.length;
  const activeMinesLabel = d.active_mines?.label || 'Based on recent analysis';

  // Derive active view metrics (selected mine vs overall cluster)
  const activeProfile = (selectedMine && d.by_mine && d.by_mine[selectedMine]) ? d.by_mine[selectedMine] : null;

  const totalProductionFormatted = activeProfile
    ? activeProfile.total_estimated_production.formatted
    : (d.total_estimated_production?.formatted || '34,200');

  const totalProductionLabel = activeProfile
    ? activeProfile.total_estimated_production.label
    : (d.total_estimated_production?.label || '(From active mines)');

  const shortfallFormatted = activeProfile
    ? activeProfile.estimated_shortfall.formatted
    : (d.estimated_shortfall?.formatted || '4,800');

  const shortfallPercent = activeProfile
    ? activeProfile.estimated_shortfall.percentage
    : (d.estimated_shortfall?.percentage || 12.3);

  const shortfallLabel = activeProfile
    ? activeProfile.estimated_shortfall.label
    : (d.estimated_shortfall?.label || `(${shortfallPercent}% below target)`);

  const shortfallAnalysis = activeProfile
    ? activeProfile.shortfall_analysis
    : (d.shortfall_analysis || {
        shortfall_tonnes: 4800,
        achieved_tonnes: 34200,
        total_target: 39000,
        shortfall_percentage: 12.3,
      });

  const trendData = (activeProfile ? activeProfile.production_trend : d.production_trend) || [];
  const recentTable = d.recent_production || [];

  // Shortfall donut chart angle calculation
  const circumference = 2 * Math.PI * 46;
  const currentShortfallPct = Math.min(100, Math.max(0, shortfallPercent));
  const shortfallDash = (currentShortfallPct / 100) * circumference;
  const achievedDash = circumference - shortfallDash;

  // Dynamic Mathematical Coordinate Mapping for Production Trend SVG Chart
  const svgPadLeft = 75;
  const svgPadRight = 20;
  const svgWidth = 520;
  const chartWidth = svgWidth - svgPadLeft - svgPadRight;
  const chartTopY = 30;
  const chartBottomY = 200;
  const chartHeight = chartBottomY - chartTopY;

  // Calculate dynamic max value for Y-axis scaling
  const allValues = trendData.flatMap(pt => [pt.actual, pt.predicted]).filter(v => v !== null && v !== undefined);
  const rawMax = allValues.length > 0 ? Math.max(...allValues) : 10000;
  const maxY = Math.max(10000, Math.ceil(rawMax / 2000) * 2000);
  const minY = 0;

  // Coordinate conversion helper
  const getX = (index) => {
    if (trendData.length <= 1) return svgPadLeft + chartWidth / 2;
    return svgPadLeft + (index / (trendData.length - 1)) * chartWidth;
  };

  const getY = (val) => {
    if (val === null || val === undefined) return null;
    const clamped = Math.max(minY, Math.min(maxY, val));
    return chartBottomY - ((clamped - minY) / (maxY - minY)) * chartHeight;
  };

  // Build actual line points
  const actualPolyPoints = trendData
    .map((pt, i) => {
      const y = getY(pt.actual);
      return y !== null ? `${getX(i).toFixed(1)},${y.toFixed(1)}` : null;
    })
    .filter(Boolean)
    .join(' ');

  // Build predicted line points
  const predictedPolyPoints = trendData
    .map((pt, i) => {
      const y = getY(pt.predicted);
      return y !== null ? `${getX(i).toFixed(1)},${y.toFixed(1)}` : null;
    })
    .filter(Boolean)
    .join(' ');

  // Y-axis grid lines
  const gridSteps = 5;
  const gridLines = Array.from({ length: gridSteps + 1 }, (_, i) => {
    const val = (maxY / gridSteps) * (gridSteps - i);
    const y = chartTopY + (chartHeight / gridSteps) * i;
    const label = val >= 1000 ? `${(val / 1000).toFixed(0)}K` : `${val}`;
    return { val, y, label };
  });

  return (
    <div className="dashboard-root-view">
      {/* Top Header Bar */}
      <div className="dash-top-header">
        <div className="dash-top-date-pill">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="dash-cal-icon">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span className="dash-date-text">{currentDateStr}</span>
        </div>

        {selectedMine && (
          <div className="dash-active-filter-pill">
            <span className="filter-pill-label">Filtered by:</span>
            <span className="filter-pill-mine">{selectedMine}</span>
            <button
              type="button"
              className="filter-pill-clear"
              onClick={() => handleSelectMine(null)}
              title="Reset to All Mines"
            >
              ✕
            </button>
          </div>
        )}

        <div className="dash-top-user-group">
          <div className="dash-avatar-circle" title={userName}>
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
            </svg>
          </div>
          <button
            type="button"
            className="dash-login-btn"
            onClick={async () => {
              await logout();
              navigate('/user-login');
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* 1. Welcome Section Hero Banner */}
      <div className="dash-hero-banner">
        <div className="dash-hero-text-side">
          <h1 className="dash-welcome-title">Welcome, {userName}</h1>
          <p className="dash-welcome-subtitle">
            Monitor active mines, production and shortfall at a glance.
          </p>
        </div>
        <div className="dash-hero-image-side">
          <div className="dash-hero-image-overlay" />
          <div className="dash-hero-quote-box">
            <p className="dash-quote-heading">“Minerals for A Better Tomorrow”</p>
            <p className="dash-quote-author">— MOIL Limited</p>
          </div>
        </div>
      </div>

      {/* 2. Three Summary Cards */}
      <div className="dash-cards-grid">
        {/* Card 1: Active Mines with Attached Popup */}
        <div className="card-mines-container" ref={popoverRef}>
          <div className="dash-summary-card card-mines">
            <div className="card-icon-wrapper icon-wagon-green">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M4 6h16l-1.5 8.5H5.5L4 6zm2.5 13a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm11 0a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM2 4h20v2H2V4z" />
              </svg>
            </div>
            <div className="card-info-block">
              <div className="card-header-with-btn">
                <span className="card-meta-label">Active Mines</span>
                <button
                  type="button"
                  className={`view-mines-btn ${viewMinesOpen ? 'active' : ''}`}
                  onClick={() => setViewMinesOpen(!viewMinesOpen)}
                  title="View dynamic active mines list"
                >
                  View Mines {viewMinesOpen ? '▲' : '▼'}
                </button>
              </div>
              <div className="card-main-metric">
                <span className="metric-number">{activeMinesCount}</span>
              </div>
              <span className="card-sub-annotation">{activeMinesLabel}</span>
            </div>
          </div>

          {/* Active Mines Popup directly below the card */}
          {viewMinesOpen && (
            <div className="active-mines-popup-attached">
              <div className="popup-attached-header">
                <strong>Active Operational Mines ({activeMinesList.length})</strong>
                <button
                  type="button"
                  className="popup-attached-close"
                  onClick={() => setViewMinesOpen(false)}
                  title="Close popup"
                >
                  ✕
                </button>
              </div>
              <p className="popup-attached-sub">Select any mine to filter dashboard:</p>
              <div className="popup-attached-list">
                <button
                  type="button"
                  className={`popup-attached-item ${!selectedMine ? 'active' : ''}`}
                  onClick={() => handleSelectMine(null)}
                >
                  <span className="mine-dot dot-all" />
                  <span className="mine-item-name">All Mines (Cluster Overview)</span>
                  {!selectedMine && <span className="check-badge">✓ Active</span>}
                </button>
                {activeMinesList.map((mName, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={`popup-attached-item ${selectedMine === mName ? 'active' : ''}`}
                    onClick={() => handleSelectMine(mName)}
                  >
                    <span className="mine-dot dot-mine" />
                    <span className="mine-item-name">{mName}</span>
                    {selectedMine === mName && <span className="check-badge">✓ Filtered</span>}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Card 2: Total Estimated Production */}
        <div className="dash-summary-card card-production">
          <div className="card-icon-wrapper icon-chart-purple">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z" />
            </svg>
          </div>
          <div className="card-info-block">
            <span className="card-meta-label">
              {selectedMine ? `Estimated Production (${selectedMine})` : 'Total Estimated Production'}
            </span>
            <div className="card-main-metric">
              <span className="metric-number">{totalProductionFormatted}</span>
              <span className="metric-unit">tonnes</span>
            </div>
            <span className="card-sub-annotation">{totalProductionLabel}</span>
          </div>
        </div>

        {/* Card 3: Estimated Shortfall */}
        <div className="dash-summary-card card-shortfall">
          <div className="card-icon-wrapper icon-warning-red">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L1 21h22L12 2zm1 15h-2v-2h2v2zm0-4h-2V8h2v5z" />
            </svg>
          </div>
          <div className="card-info-block">
            <span className="card-meta-label">
              {selectedMine ? `Estimated Shortfall (${selectedMine})` : 'Estimated Shortfall'}
            </span>
            <div className="card-main-metric text-danger-metric">
              <span className="metric-number">{shortfallFormatted}</span>
              <span className="metric-unit">tonnes</span>
            </div>
            <span className="card-sub-annotation text-danger-annotation">{shortfallLabel}</span>
          </div>
        </div>
      </div>

      {/* 3. Middle Row: Production Trend (Left 58%) + Manganese Reserves Full India Map (Right 42%) */}
      <div className="dash-middle-grid">
        {/* Interactive Production Trend Chart */}
        <div className="dash-widget-box widget-production-trend">
          <div className="widget-header-row">
            <div className="widget-title-group">
              <h2 className="widget-box-title">
                Production Trend <span className="widget-title-light">(Last 7 Days)</span>
              </h2>
              {selectedMine ? (
                <div className="selected-mine-badge-group">
                  <span className="selected-mine-tag">{selectedMine}</span>
                  <button
                    type="button"
                    className="dash-reset-filter-btn"
                    onClick={() => handleSelectMine(null)}
                    title="Return to All Mines view"
                  >
                    Reset to All Mines ✕
                  </button>
                </div>
              ) : (
                <span className="cluster-tag">Cluster Aggregate (All Active Mines)</span>
              )}
            </div>

            {/* Interactive View Toggles & Legend */}
            <div className="chart-legend-box">
              <div className="chart-view-toggles">
                <button
                  type="button"
                  className={`toggle-pill ${trendViewMode === 'all' ? 'active' : ''}`}
                  onClick={() => setTrendViewMode('all')}
                >
                  All
                </button>
                <button
                  type="button"
                  className={`toggle-pill ${trendViewMode === 'actual' ? 'active' : ''}`}
                  onClick={() => setTrendViewMode('actual')}
                >
                  Actual
                </button>
                <button
                  type="button"
                  className={`toggle-pill ${trendViewMode === 'predicted' ? 'active' : ''}`}
                  onClick={() => setTrendViewMode('predicted')}
                >
                  Predicted
                </button>
              </div>

              {(trendViewMode === 'all' || trendViewMode === 'actual') && (
                <div className="legend-item">
                  <span className="legend-dot dot-actual" />
                  <span className="legend-line line-actual" />
                  <span className="legend-text">Actual</span>
                </div>
              )}
              {(trendViewMode === 'all' || trendViewMode === 'predicted') && (
                <div className="legend-item">
                  <span className="legend-dot dot-predicted" />
                  <span className="legend-line line-predicted" />
                  <span className="legend-text">Predicted</span>
                </div>
              )}
            </div>
          </div>

          {/* Dynamic Responsive SVG Chart */}
          <div className="trend-svg-container" style={{ position: 'relative' }}>
            <svg viewBox={`0 0 ${svgWidth} 230`} className="trend-svg-chart">
              {/* Y Axis Title */}
              <text x="24" y="115" className="axis-title" transform="rotate(-90 24 115)">
                Production (tonnes)
              </text>

              {/* Dynamic Y Axis Grid Lines and Numeric Ticks */}
              {gridLines.map((grid, idx) => (
                <g key={idx}>
                  <text x="60" y={grid.y + 4} className="y-axis-text">{grid.label}</text>
                  <line
                    x1={svgPadLeft}
                    y1={grid.y}
                    x2={svgWidth - svgPadRight}
                    y2={grid.y}
                    className="chart-grid-line"
                  />
                </g>
              ))}

              {/* X Axis Date Labels */}
              {trendData.map((pt, i) => (
                <text key={i} x={getX(i)} y="222" className="x-axis-text">
                  {pt.date}
                </text>
              ))}

              {/* Actual Production Line (Solid Blue) */}
              {(trendViewMode === 'all' || trendViewMode === 'actual') && actualPolyPoints && (
                <polyline
                  fill="none"
                  stroke="#0284c7"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={actualPolyPoints}
                />
              )}

              {/* Predicted Production Line (Dashed Green) */}
              {(trendViewMode === 'all' || trendViewMode === 'predicted') && predictedPolyPoints && (
                <polyline
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2.5"
                  strokeDasharray="5,4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={predictedPolyPoints}
                />
              )}

              {/* Actual Point Circles with Hover Events */}
              {(trendViewMode === 'all' || trendViewMode === 'actual') && trendData.map((pt, i) => {
                const y = getY(pt.actual);
                if (y === null) return null;
                const x = getX(i);
                return (
                  <circle
                    key={`actual-${i}`}
                    cx={x}
                    cy={y}
                    r={hoveredTrendPoint?.index === i && hoveredTrendPoint?.type === 'Actual' ? '6.5' : '4.5'}
                    fill="#0284c7"
                    stroke="#ffffff"
                    strokeWidth="2"
                    className="trend-point-dot"
                    onMouseEnter={() => setHoveredTrendPoint({
                      index: i,
                      x,
                      y,
                      date: pt.date,
                      mine: pt.mine || selectedMine || 'Cluster',
                      actual: pt.actual,
                      predicted: pt.predicted,
                      type: 'Actual',
                    })}
                    onMouseLeave={() => setHoveredTrendPoint(null)}
                  />
                );
              })}

              {/* Predicted Point Circles with Hover Events */}
              {(trendViewMode === 'all' || trendViewMode === 'predicted') && trendData.map((pt, i) => {
                const y = getY(pt.predicted);
                if (y === null) return null;
                const x = getX(i);
                return (
                  <circle
                    key={`predicted-${i}`}
                    cx={x}
                    cy={y}
                    r={hoveredTrendPoint?.index === i && hoveredTrendPoint?.type === 'Predicted' ? '6.5' : '4.5'}
                    fill="#10b981"
                    stroke="#ffffff"
                    strokeWidth="2"
                    className="trend-point-dot"
                    onMouseEnter={() => setHoveredTrendPoint({
                      index: i,
                      x,
                      y,
                      date: pt.date,
                      mine: pt.mine || selectedMine || 'Cluster',
                      actual: pt.actual,
                      predicted: pt.predicted,
                      type: 'Predicted',
                    })}
                    onMouseLeave={() => setHoveredTrendPoint(null)}
                  />
                );
              })}
            </svg>

            {/* Hover Tooltip Overlay */}
            {hoveredTrendPoint && (
              <div
                className="trend-tooltip-floating"
                style={{
                  left: `${(hoveredTrendPoint.x / svgWidth) * 100}%`,
                  top: `${Math.max(10, hoveredTrendPoint.y - 45)}px`,
                }}
              >
                <div className="tooltip-head">
                  <strong>{hoveredTrendPoint.mine}</strong> • {hoveredTrendPoint.date}
                </div>
                <div className="tooltip-body">
                  {hoveredTrendPoint.actual !== null && (
                    <div className="tooltip-row">
                      <span className="tooltip-dot blue" />
                      <span>Actual:</span>
                      <strong>{hoveredTrendPoint.actual.toLocaleString()} t</strong>
                    </div>
                  )}
                  {hoveredTrendPoint.predicted !== null && (
                    <div className="tooltip-row">
                      <span className="tooltip-dot green" />
                      <span>Predicted:</span>
                      <strong>{hoveredTrendPoint.predicted.toLocaleString()} t</strong>
                    </div>
                  )}
                  {hoveredTrendPoint.actual !== null && hoveredTrendPoint.predicted !== null && (
                    <div className="tooltip-row variance">
                      <span>Variance:</span>
                      <strong className={hoveredTrendPoint.actual >= hoveredTrendPoint.predicted ? 'text-green' : 'text-red'}>
                        {(hoveredTrendPoint.actual - hoveredTrendPoint.predicted).toFixed(0)} t
                      </strong>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Full Interactive India Manganese Reserves Map */}
        <div className="dash-widget-box widget-manganese-reserves">
          <div className="widget-header-row">
            <div className="widget-title-group">
              <h2 className="widget-box-title">Manganese Reserves in India</h2>
              <span className="widget-subhead">Full Geographic Distribution (IBM/GSI Data)</span>
            </div>
          </div>

          <IndiaReservesMap
            reserves={d.manganese_reserves}
            selectedMine={selectedMine}
            onSelectMine={handleSelectMine}
            onReset={() => handleSelectMine(null)}
          />
        </div>
      </div>

      {/* 4. Bottom Row: Interactive Recent Production Table + Interactive Shortfall Donut + Quick Access */}
      <div className="dash-bottom-grid">
        {/* Left: Interactive Recent Production Summary Table (Clickable Rows) */}
        <div className="dash-widget-box widget-recent-production">
          <div className="widget-header-row">
            <h2 className="widget-box-title">Recent Production Summary</h2>
            <span className="table-interactive-hint">Click a mine to filter dashboard</span>
          </div>

          <div className="recent-table-wrapper">
            <table className="dash-recent-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Mine / Site</th>
                  <th style={{ textAlign: 'right' }}>
                    Actual Production<br /><span className="th-sub">(tonnes)</span>
                  </th>
                  <th style={{ textAlign: 'right' }}>
                    Target Production<br /><span className="th-sub">(tonnes)</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentTable.map((row, idx) => {
                  const isSelected = selectedMine === row.mine;
                  return (
                    <tr
                      key={idx}
                      className={`clickable-table-row ${isSelected ? 'selected-table-row' : ''}`}
                      onClick={() => handleSelectMine(row.mine)}
                      title={`Click to view ${row.mine} trends and shortfall`}
                    >
                      <td className="col-date">{row.date}</td>
                      <td className="col-mine">
                        <span className="mine-cell-badge">
                          {isSelected && <span className="active-dot" />}
                          {row.mine}
                        </span>
                      </td>
                      <td className="col-val" style={{ textAlign: 'right' }}>
                        {row.actual.toLocaleString()}
                      </td>
                      <td className="col-val" style={{ textAlign: 'right' }}>
                        {row.target.toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {selectedMine && (
            <div className="table-active-footer">
              <span>Showing records for <strong>{selectedMine}</strong></span>
              <button
                type="button"
                className="table-reset-btn"
                onClick={() => handleSelectMine(null)}
              >
                Clear Selection
              </button>
            </div>
          )}
        </div>

        {/* Center: Interactive Shortfall Analysis Donut Chart */}
        <div className="dash-widget-box widget-shortfall-analysis">
          <div className="widget-header-row">
            <h2 className="widget-box-title">Shortfall Analysis</h2>
            {selectedMine && (
              <span className="donut-mine-tag">{selectedMine}</span>
            )}
          </div>

          <div className="shortfall-donut-container">
            <svg viewBox="0 0 160 160" className="donut-svg">
              {/* Background Arc: Achieved Production (Light Blue) */}
              <circle
                cx="80"
                cy="80"
                r="46"
                fill="none"
                stroke="#bfdbfe"
                strokeWidth="20"
                strokeDasharray={`${circumference} 0`}
                className="donut-slice-achieved"
                onMouseEnter={() => setHoveredDonutSlice({
                  name: 'Achieved Production',
                  tonnes: shortfallAnalysis.achieved_tonnes,
                  pct: (100 - currentShortfallPct).toFixed(1),
                  color: '#bfdbfe',
                })}
                onMouseLeave={() => setHoveredDonutSlice(null)}
              />

              {/* Foreground Arc: Shortfall (Red) */}
              <circle
                cx="80"
                cy="80"
                r="46"
                fill="none"
                stroke="#ef4444"
                strokeWidth="20"
                strokeDasharray={`${shortfallDash} ${achievedDash}`}
                strokeDashoffset={circumference * 0.25}
                strokeLinecap="butt"
                className="donut-slice-shortfall"
                onMouseEnter={() => setHoveredDonutSlice({
                  name: 'Production Shortfall',
                  tonnes: shortfallAnalysis.shortfall_tonnes,
                  pct: currentShortfallPct.toFixed(1),
                  color: '#ef4444',
                })}
                onMouseLeave={() => setHoveredDonutSlice(null)}
              />

              {/* Center Metrics (Dynamically changes on hover or mine select) */}
              {hoveredDonutSlice ? (
                <>
                  <text x="80" y="70" textAnchor="middle" className="donut-center-tonnes hovered">
                    {Number(hoveredDonutSlice.tonnes || 0).toLocaleString()}
                  </text>
                  <text x="80" y="85" textAnchor="middle" className="donut-center-unit">
                    tonnes
                  </text>
                  <text x="80" y="103" textAnchor="middle" className="donut-center-pct">
                    {hoveredDonutSlice.pct}%
                  </text>
                </>
              ) : (
                <>
                  <text x="80" y="74" textAnchor="middle" className="donut-center-tonnes">
                    {shortfallFormatted}
                  </text>
                  <text x="80" y="88" textAnchor="middle" className="donut-center-unit">
                    tonnes
                  </text>
                  <text x="80" y="104" textAnchor="middle" className="donut-center-pct">
                    {shortfallPercent}%
                  </text>
                </>
              )}
            </svg>

            {/* Donut Legend with Exact Tonnes */}
            <div className="donut-legend-row">
              <div
                className={`donut-legend-entry ${hoveredDonutSlice?.name === 'Production Shortfall' ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredDonutSlice({
                  name: 'Production Shortfall',
                  tonnes: shortfallAnalysis.shortfall_tonnes,
                  pct: currentShortfallPct.toFixed(1),
                  color: '#ef4444',
                })}
                onMouseLeave={() => setHoveredDonutSlice(null)}
              >
                <span className="donut-legend-dot dot-shortfall" />
                <span>Shortfall ({shortfallPercent}%)</span>
              </div>
              <div
                className={`donut-legend-entry ${hoveredDonutSlice?.name === 'Achieved Production' ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredDonutSlice({
                  name: 'Achieved Production',
                  tonnes: shortfallAnalysis.achieved_tonnes,
                  pct: (100 - currentShortfallPct).toFixed(1),
                  color: '#bfdbfe',
                })}
                onMouseLeave={() => setHoveredDonutSlice(null)}
              >
                <span className="donut-legend-dot dot-achieved" />
                <span>Achieved ({(100 - currentShortfallPct).toFixed(1)}%)</span>
              </div>
            </div>

            {/* Exact Targets Readout */}
            <div className="donut-target-readout">
              <span>Target: <strong>{Number(shortfallAnalysis.total_target || 39000).toLocaleString()} tonnes</strong></span>
            </div>
          </div>
        </div>

        {/* Right: Quick Access Cards */}
        <div className="dash-widget-box widget-quick-access">
          <h2 className="widget-box-title">Quick Access</h2>
          <div className="quick-access-cards">
            {/* 1. Manganese Estimation */}
            <div
              className="quick-card quick-card-green"
              onClick={() => navigate('/ore-prediction')}
              role="button"
              tabIndex="0"
            >
              <div className="quick-icon-box icon-box-green">
                <svg viewBox="0 0 40 32" fill="none" className="quick-mountain-svg">
                  <path d="M14 2L2 28H18L24 16L14 2Z" fill="#10b981" />
                  <path d="M24 10L14 28H38L24 10Z" fill="#059669" />
                </svg>
              </div>
              <div className="quick-card-text">
                <h3 className="quick-card-title">Manganese Estimation</h3>
                <p className="quick-card-desc">Estimate manganese reserves using geological and operational data</p>
              </div>
              <div className="quick-arrow-icon arrow-green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>
            </div>

            {/* 2. Production Shortfall Estimation */}
            <div
              className="quick-card quick-card-purple"
              onClick={() => navigate('/production-forecast')}
              role="button"
              tabIndex="0"
            >
              <div className="quick-icon-box icon-box-purple">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z" />
                </svg>
              </div>
              <div className="quick-card-text">
                <h3 className="quick-card-title">Production Shortfall Estimation</h3>
                <p className="quick-card-desc">Predict shortfall and analyse trends (stored in database)</p>
              </div>
              <div className="quick-arrow-icon arrow-purple">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
