import React from 'react';
import { useNavigate } from 'react-router-dom';

const ProductionPredictionResult = ({
  result,
  onBack,
}) => {
  if (!result) return null;

  const target = Math.round(result.target_production || 0);
  const predicted = Math.round(result.predicted_production || 0);
  const shortfall = Math.round(result.shortfall || 0);

  const reasons = result.reasons && result.reasons.length > 0
    ? result.reasons
    : [
        'High wind speed reducing operational efficiency',
        'Increased soil moisture affecting haulage and movement',
        'Adverse weather conditions (precipitation)',
        'Equipment downtime',
      ];

  const navigate = useNavigate();

  const handleViewRecommendations = () => {
    // Navigate directly to the Recommendations page with latest production shortfall run state
    navigate('/recommendations', { state: { predictionData: result } });
  };

  // Historical data from user input (Part 11 & 12)
  const rawHistory = (result.historical_production && result.historical_production.length > 0)
    ? result.historical_production
    : (result.recent_history && result.recent_history.length > 0)
      ? result.recent_history
      : [
          { date: '07 Sep', actual_production: 8450 },
          { date: '08 Sep', actual_production: 8200 },
          { date: '09 Sep', actual_production: 8750 },
          { date: '10 Sep', actual_production: 8100 },
          { date: '11 Sep', actual_production: 8600 },
          { date: '12 Sep', actual_production: 8400 },
          { date: '13 Sep', actual_production: 8300 },
        ];

  const historySeries = rawHistory.map((d) => ({
    date: d.date || '',
    actual_production: Number(d.actual_production !== undefined ? d.actual_production : (d.production !== undefined ? d.production : 0)),
    isPrediction: false,
  }));

  // Today's AIML prediction point (Part 11 & 12)
  const todayDate = result.date || 'Today';
  const todayPredictionPoint = {
    date: todayDate,
    predicted_production: predicted,
    isPrediction: true,
  };

  const allPoints = [...historySeries, todayPredictionPoint];

  // Dynamic SVG Chart Scaling (adapts cleanly to any target scale e.g. 588 tonnes or 10,000 tonnes)
  const allValues = [
    ...historySeries.map((d) => d.actual_production),
    todayPredictionPoint.predicted_production,
    target,
  ];
  const maxValRaw = Math.max(...allValues, 10);
  const chartMax = Math.ceil((maxValRaw * 1.25) / 10) * 10 || 1000;

  const width = 540;
  const height = 220;
  const paddingLeft = 50;
  const paddingBottom = 30;
  const paddingTop = 20;
  const paddingRight = 25;

  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;
  const stepX = chartW / Math.max(1, allPoints.length - 1);

  const getY = (val) => {
    const clamped = Math.max(0, Math.min(chartMax, val));
    return paddingTop + chartH - (clamped / chartMax) * chartH;
  };

  // Historical solid polyline
  const histPoints = historySeries
    .map((d, i) => `${paddingLeft + i * stepX},${getY(d.actual_production)}`)
    .join(' ');

  // Connect last historical point to today's prediction point via dashed green line
  const lastHistIdx = Math.max(0, historySeries.length - 1);
  const lastHistX = paddingLeft + lastHistIdx * stepX;
  const lastHistY = historySeries.length > 0 ? getY(historySeries[lastHistIdx].actual_production) : getY(0);
  const predX = paddingLeft + (allPoints.length - 1) * stepX;
  const predY = getY(todayPredictionPoint.predicted_production);
  const predPoints = `${lastHistX},${lastHistY} ${predX},${predY}`;

  // 5 evenly spaced Y-axis ticks
  const yTicks = [0, 0.25, 0.5, 0.75, 1.0].map((frac) => Math.round(chartMax * frac));

  const handleGenerateReport = () => {
    const csvContent = [
      'Report,MOIL Production Shortfall Forecast',
      `Date,${result.date || '2026-09-14'}`,
      `Mine,${result.mine || 'Balaghat'}`,
      `Target Production (tonnes),${target}`,
      `Predicted Production (tonnes),${predicted}`,
      `Shortfall (tonnes),${shortfall}`,
      `Shortfall Percentage,${result.shortfall_percentage || 0}%`,
      `Risk Level,${result.risk_level || 'LOW'}`,
      `Late Fusion Risk Score,${result.final_risk_score || 0}`,
      '',
      'Possible Reasons for Shortfall,',
      ...reasons.map((r, i) => `Reason ${i + 1},${r.replace(/,/g, ';')}`)
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `production_forecast_report_${result.mine || 'mine'}_${result.date || 'date'}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="forecast-step-container">
      <div className="forecast-step-header">
        <h2 className="step-title">Step 4 : Production Shortfall Prediction</h2>
        <p className="step-subtitle">Results and key insights</p>
      </div>

      {/* Top 3 KPI Cards */}
      <div className="forecast-kpi-row">
        <div className="kpi-metric-card green-card">
          <div className="kpi-icon-badge green">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" />
            </svg>
          </div>
          <div className="kpi-metric-info">
            <span className="kpi-metric-label">Target Production</span>
            <div className="kpi-metric-value green-text">
              {target.toLocaleString()} <span className="unit-label">tonnes</span>
            </div>
          </div>
        </div>

        <div className="kpi-metric-card blue-card">
          <div className="kpi-icon-badge blue">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z" />
            </svg>
          </div>
          <div className="kpi-metric-info">
            <span className="kpi-metric-label">Predicted Production</span>
            <div className="kpi-metric-value blue-text">
              {predicted.toLocaleString()} <span className="unit-label">tonnes</span>
            </div>
          </div>
        </div>

        <div className="kpi-metric-card red-card">
          <div className="kpi-icon-badge red">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
            </svg>
          </div>
          <div className="kpi-metric-info">
            <span className="kpi-metric-label">Shortfall</span>
            <div className="kpi-metric-value red-text">
              {shortfall.toLocaleString()} <span className="unit-label">tonnes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Results Grid */}
      <div className="forecast-step4-grid">
        {/* Left Line Chart Card */}
        <div className="forecast-chart-card">
          <h3 className="chart-card-title">Past Production vs Today's Prediction</h3>

          <div className="svg-chart-container">
            <svg viewBox={`0 0 ${width} ${height}`} className="production-svg-chart">
              {/* Horizontal Grid lines using dynamic yTicks */}
              {yTicks.map((tick) => {
                const y = getY(tick);
                return (
                  <g key={tick}>
                    <line
                      x1={paddingLeft}
                      y1={y}
                      x2={width - paddingRight}
                      y2={y}
                      stroke="#f1f5f9"
                      strokeWidth="1"
                    />
                    <text
                      x={paddingLeft - 8}
                      y={y + 4}
                      textAnchor="end"
                      fontSize="9"
                      fill="#94a3b8"
                    >
                      {tick >= 1000 ? `${(tick / 1000).toFixed(tick % 1000 === 0 ? 0 : 1)}K` : tick}
                    </text>
                  </g>
                );
              })}

              {/* Y axis label */}
              <text
                x={-height / 2}
                y={12}
                transform="rotate(-90)"
                textAnchor="middle"
                fontSize="9"
                fill="#94a3b8"
              >
                Production (tonnes)
              </text>

              {/* Solid Blue Line: Actual Production from User Data */}
              <polyline
                fill="none"
                stroke="#2563eb"
                strokeWidth="2.4"
                points={histPoints}
              />
              {historySeries.map((d, i) => (
                <circle
                  key={`hist-dot-${i}`}
                  cx={paddingLeft + i * stepX}
                  cy={getY(d.actual_production)}
                  r="3.5"
                  fill="#2563eb"
                />
              ))}

              {/* Dashed Green Line: Connects Last Historical to Today's AIML Prediction Point */}
              <polyline
                fill="none"
                stroke="#10b981"
                strokeWidth="2.4"
                strokeDasharray="4 4"
                points={predPoints}
              />
              {/* Outer halo and dot on today's prediction point */}
              <circle
                cx={predX}
                cy={predY}
                r="7"
                fill="none"
                stroke="#10b981"
                strokeWidth="1.5"
                strokeOpacity="0.4"
              />
              <circle
                cx={predX}
                cy={predY}
                r="4"
                fill="#10b981"
              />

              {/* X Axis Labels */}
              {allPoints.map((d, i) => {
                let lbl = d.date;
                if (lbl && lbl.includes('-')) {
                  const parts = lbl.split('-');
                  const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                  if (parts[0].length === 4) {
                    lbl = `${parts[2]} ${monthNames[parseInt(parts[1], 10) - 1] || 'Sep'}`;
                  } else {
                    lbl = `${parts[0]} ${monthNames[parseInt(parts[1], 10) - 1] || 'Sep'}`;
                  }
                }
                return (
                  <text
                    key={`label-${i}`}
                    x={paddingLeft + i * stepX}
                    y={height - 10}
                    textAnchor="middle"
                    fontSize="8.5"
                    fill={d.isPrediction ? '#10b981' : '#64748b'}
                    fontWeight={d.isPrediction ? '600' : 'normal'}
                  >
                    {lbl}
                  </text>
                );
              })}
            </svg>

            {/* Chart Legend */}
            <div className="chart-legend-row">
              <div className="legend-item">
                <span className="legend-line blue-solid"></span>
                <span className="legend-dot blue"></span>
                <span className="legend-text">Actual Production</span>
              </div>
              <div className="legend-item">
                <span className="legend-line green-dashed"></span>
                <span className="legend-dot green"></span>
                <span className="legend-text">Predicted Production</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Insights Column */}
        <div className="forecast-insights-col">
          {/* Possible Reasons Card */}
          <div className="forecast-reasons-card">
            <h3 className="insights-card-title">Possible Reasons for Shortfall</h3>
            <div className="reasons-badge-list">
              {reasons.slice(0, 4).map((reason, idx) => {
                const badgeColors = ['red', 'amber', 'green', 'teal'];
                const colorClass = badgeColors[idx % badgeColors.length];
                return (
                  <div key={idx} className="reason-item-row">
                    <span className={`number-badge ${colorClass}`}>{idx + 1}</span>
                    <span className="reason-text">{reason}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* View Recommendations Button */}
          <button
            type="button"
            className="forecast-btn-view-recommendations"
            onClick={handleViewRecommendations}
          >
            View Recommendations
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="forecast-action-bar">
        <button
          type="button"
          className="forecast-btn-outline"
          onClick={onBack}
        >
          &larr; Back
        </button>
        <button
          type="button"
          className="forecast-btn-primary report-btn"
          onClick={handleGenerateReport}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          Generate Report
        </button>
      </div>
    </div>
  );
};

export default ProductionPredictionResult;
