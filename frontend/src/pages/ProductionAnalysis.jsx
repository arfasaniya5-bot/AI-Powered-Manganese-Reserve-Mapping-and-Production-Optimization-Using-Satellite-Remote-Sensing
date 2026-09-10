/**
 * Production Analysis Page Component
 * ----------------------------------
 * Connected view for the 4 production datasets:
 * 1. Mining Equipment Failure Data
 * 2. MOIL Historical Production Prototype
 * 3. MOIL Weather & Soil 2025
 * 4. MWD Rock Type & Blast-Holes Model Ready
 *
 * Adheres strictly to the ManganeseInsight design system:
 * - Displays dataset connection status, record counts, and available columns.
 * - Shows aggregated production summaries, equipment loss, and weather indicators.
 * - Displays a clear notice that the AI/ML model integration hook is ready.
 * - Includes robust loading, error, and empty states.
 */

import React, { useState, useEffect } from 'react';
import {
  fetchProductionHealth,
  fetchProductionDatasets,
  fetchProductionSummary,
  fetchDatasetColumns,
  fetchDatasetRecords,
  fetchProductionMines,
} from '../services/productionService';

const DATASET_KEYS = [
  { key: 'historical_production', label: 'MOIL Historical Production', icon: '📊' },
  { key: 'equipment_failure', label: 'Equipment Failure & Downtime', icon: '⚙️' },
  { key: 'weather_soil', label: 'Weather & Soil Monitoring (2025)', icon: '🌦️' },
  { key: 'rocktype_blastholes', label: 'MWD Rock Type & Blast-Holes', icon: '⛏️' },
];

const ProductionAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Core data states
  const [health, setHealth] = useState(null);
  const [datasets, setDatasets] = useState({});
  const [summary, setSummary] = useState(null);
  const [mines, setMines] = useState([]);

  // Active dataset inspector states
  const [activeDatasetKey, setActiveDatasetKey] = useState('historical_production');
  const [activeViewMode, setActiveViewMode] = useState('columns'); // 'columns' or 'records'
  const [columnsData, setColumnsData] = useState([]);
  const [recordsData, setRecordsData] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedMineFilter, setSelectedMineFilter] = useState('');
  const [inspectorLoading, setInspectorLoading] = useState(false);

  const pageSize = 20;

  // Initial load: health, metadata, summary, mines
  const loadInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, datasetsRes, summaryRes, minesRes] = await Promise.all([
        fetchProductionHealth(),
        fetchProductionDatasets(),
        fetchProductionSummary(),
        fetchProductionMines(),
      ]);
      setHealth(healthRes);
      setDatasets(datasetsRes.datasets || {});
      setSummary(summaryRes.summary || {});
      setMines(minesRes || []);
    } catch (err) {
      console.error('Failed to load production data:', err);
      setError(err.message || 'Error communicating with Production Analysis backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Load columns or records whenever active dataset, view mode, page, or filter changes
  useEffect(() => {
    const loadInspectorData = async () => {
      if (!activeDatasetKey) return;
      setInspectorLoading(true);
      try {
        if (activeViewMode === 'columns') {
          const colRes = await fetchDatasetColumns(activeDatasetKey);
          setColumnsData(colRes.columns || []);
        } else {
          const recRes = await fetchDatasetRecords(
            activeDatasetKey,
            pageSize,
            currentPage * pageSize,
            selectedMineFilter || null
          );
          setRecordsData(recRes.records || []);
          setTotalRecords(recRes.total_records || 0);
        }
      } catch (err) {
        console.error('Failed to load inspector data:', err);
      } finally {
        setInspectorLoading(false);
      }
    };

    loadInspectorData();
  }, [activeDatasetKey, activeViewMode, currentPage, selectedMineFilter]);

  // Reset page when switching dataset or filter
  const handleDatasetSwitch = (key) => {
    setActiveDatasetKey(key);
    setCurrentPage(0);
  };

  const handleFilterChange = (e) => {
    setSelectedMineFilter(e.target.value);
    setCurrentPage(0);
  };

  const kpis = summary?.kpis || {};
  const activeMeta = datasets[activeDatasetKey] || {};

  return (
    <div className="page-content production-analysis-page">
      {/* Page Header */}
      <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="page-title">Production Analysis & Shortfall</h1>
          <p className="page-subtitle">
            Integrated analysis of MOIL historical output, equipment failure downtime, weather impacts, and MWD blast-hole rock mechanics.
          </p>
        </div>

        {/* Backend Connectivity Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            className="status-pill"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12.5px',
              fontWeight: '600',
              backgroundColor: health?.datasets_available === 4 ? '#ecfdf5' : '#fffbeb',
              color: health?.datasets_available === 4 ? '#065f46' : '#92400e',
              border: `1px solid ${health?.datasets_available === 4 ? '#a7f3d0' : '#fde68a'}`,
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: health?.datasets_available === 4 ? '#10b981' : '#f59e0b',
              }}
            />
            {health?.datasets_available === 4
              ? '4 of 4 Datasets Connected'
              : `${health?.datasets_available || 0} of 4 Datasets Connected`}
          </span>
          <button
            onClick={loadInitialData}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: '#fff',
              fontSize: '12.5px',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
            }}
            title="Refresh datasets"
          >
            ↻ Refresh
          </button>
        </div>
      </header>

      {/* Model Pending Notice Banner */}
      <div
        style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          padding: '12px 18px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          color: '#1e40af',
          fontSize: '13.5px',
        }}
      >
        <span style={{ fontSize: '18px' }}>ℹ️</span>
        <div>
          <strong>AI/ML Model Status:</strong> Integration pipeline ready. The trained production shortfall model will be connected via <code>/api/production/predict-shortfall</code> once delivered. Currently displaying verified historical records and multi-dataset aggregates.
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-secondary)' }}>
          <div className="loading-spinner" style={{ margin: '0 auto 16px auto' }} />
          <p>Connecting and loading production datasets...</p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div
          className="form-error-banner"
          style={{ marginBottom: '24px', padding: '16px 20px' }}
        >
          <svg className="error-icon" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
          <div style={{ flex: 1 }}>
            <strong>Connection Error:</strong> {error}
          </div>
          <button
            onClick={loadInitialData}
            style={{
              padding: '6px 14px',
              backgroundColor: '#dc2626',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Section 1: Summary KPI Metrics Grid */}
          <section style={{ marginBottom: '28px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px',
              }}
            >
              {/* Card 1: Total Planned Production */}
              <div className="card" style={{ padding: '20px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Total Planned Output
                </div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--text-primary)', marginTop: '8px' }}>
                  {kpis.total_planned_production_tonnes
                    ? `${(kpis.total_planned_production_tonnes / 1000000).toFixed(2)} M Tonnes`
                    : 'N/A'}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Across {kpis.total_reporting_months || 0} reporting mine-months
                </div>
              </div>

              {/* Card 2: Total Actual Production */}
              <div className="card" style={{ padding: '20px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Total Actual Output
                </div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#0284c7', marginTop: '8px' }}>
                  {kpis.total_actual_production_tonnes
                    ? `${(kpis.total_actual_production_tonnes / 1000000).toFixed(2)} M Tonnes`
                    : 'N/A'}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Average Efficiency: {kpis.avg_operational_efficiency_pct || 0}%
                </div>
              </div>

              {/* Card 3: Total Shortfall */}
              <div className="card" style={{ padding: '20px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Total Production Shortfall
                </div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#dc2626', marginTop: '8px' }}>
                  {kpis.total_production_shortfall_tonnes
                    ? `${(kpis.total_production_shortfall_tonnes / 1000000).toFixed(2)} M Tonnes`
                    : 'N/A'}
                </div>
                <div style={{ fontSize: '12px', color: '#dc2626', fontWeight: '500', marginTop: '4px' }}>
                  Overall Shortfall: {kpis.overall_shortfall_percentage || 0}%
                </div>
              </div>

              {/* Card 4: Equipment & Weather Factors */}
              <div className="card" style={{ padding: '20px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Operational Health Index
                </div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#059669', marginTop: '8px' }}>
                  {kpis.avg_equipment_availability_pct || 0}%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Availability | Weather Factor: {kpis.avg_weather_impact_pct || 0}%
                </div>
              </div>
            </div>
          </section>

          {/* Section 2: Four Connected Datasets Overview */}
          <section style={{ marginBottom: '28px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '14px' }}>
              Connected Production Datasets ({Object.keys(datasets).length} files)
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: '16px',
              }}
            >
              {DATASET_KEYS.map((item) => {
                const meta = datasets[item.key] || {};
                const isSelected = activeDatasetKey === item.key;
                return (
                  <div
                    key={item.key}
                    onClick={() => handleDatasetSwitch(item.key)}
                    className="card"
                    style={{
                      padding: '18px',
                      cursor: 'pointer',
                      border: isSelected ? '2px solid var(--primary-blue)' : '1px solid var(--border-color)',
                      backgroundColor: isSelected ? '#f0f9ff' : '#ffffff',
                      transition: 'all 0.15s ease-in-out',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '24px' }}>{item.icon}</span>
                      <span
                        style={{
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          backgroundColor: meta.exists ? '#dcfce7' : '#fee2e2',
                          color: meta.exists ? '#166534' : '#991b1b',
                          fontWeight: '600',
                          textTransform: 'uppercase',
                        }}
                      >
                        {meta.file_format || 'FILE'}
                      </span>
                    </div>

                    <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', marginTop: '12px' }}>
                      {meta.name || item.label}
                    </h3>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px', wordBreak: 'break-all' }}>
                      {meta.filename || 'Loading filename...'}
                    </p>

                    <div style={{ display: 'flex', gap: '16px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12.5px' }}>
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Records:</span>{' '}
                        <strong>{meta.total_rows?.toLocaleString() ?? 0}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-secondary)' }}>Columns:</span>{' '}
                        <strong>{meta.total_columns ?? 0}</strong>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Section 3: Interactive Dataset Inspector */}
          <section className="card" style={{ padding: '24px', marginBottom: '32px' }}>
            {/* Inspector Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
              <div>
                <h2 style={{ fontSize: '17px', fontWeight: '600', color: 'var(--text-primary)' }}>
                  Dataset Inspector: {activeMeta.name || activeDatasetKey}
                </h2>
                <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {activeMeta.total_rows?.toLocaleString() ?? 0} rows × {activeMeta.total_columns ?? 0} columns ({activeMeta.file_format})
                </p>
              </div>

              {/* View Mode Toggle & Mine Filter */}
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                {activeDatasetKey === 'historical_production' && activeViewMode === 'records' && (
                  <select
                    value={selectedMineFilter}
                    onChange={handleFilterChange}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                      fontSize: '13px',
                      background: '#fff',
                    }}
                  >
                    <option value="">All Mines ({mines.length})</option>
                    {mines.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                )}

                <div style={{ display: 'inline-flex', borderRadius: '6px', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
                  <button
                    onClick={() => setActiveViewMode('columns')}
                    style={{
                      padding: '7px 16px',
                      fontSize: '13px',
                      fontWeight: '500',
                      border: 'none',
                      backgroundColor: activeViewMode === 'columns' ? 'var(--primary-blue)' : '#fff',
                      color: activeViewMode === 'columns' ? '#fff' : 'var(--text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    Column Schema ({activeMeta.total_columns ?? 0})
                  </button>
                  <button
                    onClick={() => setActiveViewMode('records')}
                    style={{
                      padding: '7px 16px',
                      fontSize: '13px',
                      fontWeight: '500',
                      border: 'none',
                      borderLeft: '1px solid var(--border-color)',
                      backgroundColor: activeViewMode === 'records' ? 'var(--primary-blue)' : '#fff',
                      color: activeViewMode === 'records' ? '#fff' : 'var(--text-secondary)',
                      cursor: 'pointer',
                    }}
                  >
                    Data Records ({activeMeta.total_rows?.toLocaleString() ?? 0})
                  </button>
                </div>
              </div>
            </div>

            {/* Inspector Body */}
            {inspectorLoading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                <div className="loading-spinner" style={{ margin: '0 auto 12px auto' }} />
                <p>Loading {activeViewMode === 'columns' ? 'columns schema' : 'data records'}...</p>
              </div>
            ) : activeViewMode === 'columns' ? (
              /* View 1: Columns Schema Table */
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border-color)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                      <th style={{ padding: '10px 12px' }}>#</th>
                      <th style={{ padding: '10px 12px' }}>Column Name</th>
                      <th style={{ padding: '10px 12px' }}>Data Type</th>
                      <th style={{ padding: '10px 12px' }}>Missing Values</th>
                      <th style={{ padding: '10px 12px' }}>Sample Values</th>
                    </tr>
                  </thead>
                  <tbody>
                    {columnsData.map((col, idx) => (
                      <tr
                        key={col.name}
                        style={{
                          borderBottom: '1px solid var(--border-color)',
                          backgroundColor: idx % 2 === 0 ? 'transparent' : '#f8fafc',
                        }}
                      >
                        <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>{idx + 1}</td>
                        <td style={{ padding: '10px 12px', fontWeight: '600', color: 'var(--text-primary)' }}>
                          <code>{col.name}</code>
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>
                          <span style={{ padding: '2px 8px', borderRadius: '4px', backgroundColor: '#f1f5f9', fontSize: '12px' }}>
                            {col.data_type}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ color: col.null_count === 0 ? '#059669' : '#dc2626', fontWeight: '500' }}>
                            {col.null_count} nulls
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>
                          {col.sample_values?.slice(0, 3).map((s, i) => (
                            <span
                              key={i}
                              style={{
                                display: 'inline-block',
                                backgroundColor: '#f8fafc',
                                border: '1px solid #e2e8f0',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontSize: '11.5px',
                                marginRight: '6px',
                              }}
                            >
                              {String(s)}
                            </span>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* View 2: Data Records Table */
              <div>
                {recordsData.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    No records found matching current criteria.
                  </div>
                ) : (
                  <>
                    <div style={{ overflowX: 'auto', maxHeight: '500px' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
                        <thead style={{ position: 'sticky', top: 0, backgroundColor: '#f8fafc', zIndex: 1 }}>
                          <tr style={{ borderBottom: '2px solid var(--border-color)', textAlign: 'left', color: 'var(--text-secondary)' }}>
                            <th style={{ padding: '10px 12px' }}>#</th>
                            {Object.keys(recordsData[0] || {}).map((header) => (
                              <th key={header} style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                                {header}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {recordsData.map((row, rIdx) => (
                            <tr
                              key={rIdx}
                              style={{
                                borderBottom: '1px solid var(--border-color)',
                                backgroundColor: rIdx % 2 === 0 ? 'transparent' : '#f8fafc',
                              }}
                            >
                              <td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>
                                {currentPage * pageSize + rIdx + 1}
                              </td>
                              {Object.entries(row).map(([k, val], cIdx) => (
                                <td
                                  key={cIdx}
                                  style={{
                                    padding: '8px 12px',
                                    whiteSpace: 'nowrap',
                                    color: val === null ? 'var(--text-muted)' : 'var(--text-primary)',
                                  }}
                                >
                                  {val === null ? '—' : String(val)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagination Controls */}
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginTop: '16px',
                        paddingTop: '12px',
                        borderTop: '1px solid var(--border-color)',
                        fontSize: '13px',
                      }}
                    >
                      <div style={{ color: 'var(--text-secondary)' }}>
                        Showing {currentPage * pageSize + 1} to{' '}
                        {Math.min((currentPage + 1) * pageSize, totalRecords)} of{' '}
                        {totalRecords.toLocaleString()} records
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 0))}
                          disabled={currentPage === 0}
                          style={{
                            padding: '6px 14px',
                            borderRadius: '6px',
                            border: '1px solid var(--border-color)',
                            backgroundColor: '#fff',
                            cursor: currentPage === 0 ? 'not-allowed' : 'pointer',
                            opacity: currentPage === 0 ? 0.5 : 1,
                            fontSize: '13px',
                          }}
                        >
                          Previous
                        </button>
                        <span style={{ display: 'flex', alignItems: 'center', padding: '0 8px', color: 'var(--text-secondary)' }}>
                          Page {currentPage + 1} of {Math.ceil(totalRecords / pageSize) || 1}
                        </span>
                        <button
                          onClick={() => setCurrentPage((prev) => prev + 1)}
                          disabled={(currentPage + 1) * pageSize >= totalRecords}
                          style={{
                            padding: '6px 14px',
                            borderRadius: '6px',
                            border: '1px solid var(--border-color)',
                            backgroundColor: '#fff',
                            cursor: (currentPage + 1) * pageSize >= totalRecords ? 'not-allowed' : 'pointer',
                            opacity: (currentPage + 1) * pageSize >= totalRecords ? 0.5 : 1,
                            fontSize: '13px',
                          }}
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
};

export default ProductionAnalysis;
