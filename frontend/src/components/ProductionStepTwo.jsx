import React, { useState, useRef } from 'react';

const DEFAULT_HISTORY = [
  { date: '07-09-2026', actual_production: 8450 },
  { date: '08-09-2026', actual_production: 8200 },
  { date: '09-09-2026', actual_production: 8750 },
  { date: '10-09-2026', actual_production: 8100 },
  { date: '11-09-2026', actual_production: 8600 },
  { date: '12-09-2026', actual_production: 8400 },
  { date: '13-09-2026', actual_production: 8300 },
];

const ProductionStepTwo = ({
  history = [],
  onChangeHistory,
  onBack,
  onNext,
  loading = false,
}) => {
  const [inputMode, setInputMode] = useState('manual'); // 'manual' or 'csv'
  const [fileName, setFileName] = useState('');
  const [csvError, setCsvError] = useState(null);
  const [editedCells, setEditedCells] = useState({});
  const fileInputRef = useRef(null);

  const displayHistory = history && history.length === 7 ? history : DEFAULT_HISTORY;

  const isCellEdited = (idx, field) => {
    return Boolean(editedCells[`${idx}_${field}`]);
  };

  const handleRowChange = (index, field, value) => {
    setEditedCells((prev) => ({ ...prev, [`${index}_${field}`]: true }));
    const updated = [...displayHistory];
    updated[index] = {
      ...updated[index],
      [field]: field === 'actual_production' ? (value === '' ? '' : parseFloat(value) || 0) : value,
    };
    onChangeHistory(updated);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setCsvError(null);
    setFileName(file.name);

    if (!file.name.endsWith('.csv')) {
      setCsvError('Please upload a valid .csv file.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target.result;
        const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
        if (lines.length < 2) {
          setCsvError('CSV file is empty or missing data rows.');
          return;
        }

        const header = lines[0].split(',').map((h) => h.trim().toLowerCase());
        const dateIdx = header.findIndex((h) => h.includes('date'));
        const prodIdx = header.findIndex((h) => h.includes('actual') || h.includes('production'));

        if (dateIdx === -1 || prodIdx === -1) {
          setCsvError('CSV must contain "Date" and "Actual_Production (tonnes)" columns.');
          return;
        }

        const parsedRows = [];
        for (let i = 1; i < lines.length; i++) {
          const cols = lines[i].split(',').map((c) => c.trim());
          if (cols.length > Math.max(dateIdx, prodIdx)) {
            const dVal = cols[dateIdx];
            const pVal = parseFloat(cols[prodIdx].replace(/[^0-9.]/g, '')) || 0;
            parsedRows.push({ date: dVal, actual_production: pVal });
          }
        }

        if (parsedRows.length === 0) {
          setCsvError('No valid data rows found in CSV.');
          return;
        }

        // Take last 7 rows or slice
        const finalRows = parsedRows.slice(-7);
        while (finalRows.length < 7) {
          finalRows.unshift({ date: `2026-09-0${finalRows.length + 1}`, actual_production: 8000 });
        }

        const newEdited = {};
        for (let i = 0; i < 7; i++) {
          newEdited[`${i}_date`] = true;
          newEdited[`${i}_actual_production`] = true;
        }
        setEditedCells(newEdited);

        onChangeHistory(finalRows);
      } catch (err) {
        setCsvError('Failed to parse CSV file: ' + err.message);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="forecast-step-container">
      <div className="forecast-step-header">
        <h2 className="step-title">Step 2 : Historical Production Data</h2>
        <p className="step-subtitle">Provide recent production data for better prediction</p>
      </div>

      <div className="forecast-card-panel">
        <div className="panel-subhead-row">
          <h3 className="panel-title">Recent Production Data (Last 7 Days)</h3>
          <div className="mode-toggle-group">
            <label className="radio-label">
              <input
                type="radio"
                name="historyMode"
                value="manual"
                checked={inputMode === 'manual'}
                onChange={() => setInputMode('manual')}
              />
              <span>Enter manually</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="historyMode"
                value="csv"
                checked={inputMode === 'csv'}
                onChange={() => setInputMode('csv')}
              />
              <span>Upload CSV file</span>
            </label>
          </div>
        </div>

        <div className="forecast-step2-grid">
          {/* Left Table Section */}
          <div className="forecast-table-wrapper">
            <table className="forecast-history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Actual Production (tonnes)</th>
                </tr>
              </thead>
              <tbody>
                {displayHistory.map((row, idx) => (
                  <tr key={idx}>
                    <td>
                      {inputMode === 'manual' ? (
                        <input
                          type="text"
                          className={`table-input-cell ${isCellEdited(idx, 'date') ? 'user-typed' : 'sample-placeholder'}`}
                          value={row.date}
                          onChange={(e) => handleRowChange(idx, 'date', e.target.value)}
                        />
                      ) : (
                        <span className={isCellEdited(idx, 'date') ? 'table-value-text' : 'table-sample-text'}>{row.date}</span>
                      )}
                    </td>
                    <td>
                      {inputMode === 'manual' ? (
                        <input
                          type="number"
                          className={`table-input-cell numeric ${isCellEdited(idx, 'actual_production') ? 'user-typed' : 'sample-placeholder'}`}
                          value={row.actual_production}
                          step="10"
                          onChange={(e) =>
                            handleRowChange(idx, 'actual_production', e.target.value)
                          }
                        />
                      ) : (
                        <span className={isCellEdited(idx, 'actual_production') ? 'table-value-text' : 'table-sample-text'}>
                          {Number(row.actual_production).toLocaleString()}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Right CSV Upload Card */}
          <div className="forecast-upload-subcard">
            <div className="upload-doc-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <h4 className="upload-title">Or upload a CSV file</h4>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".csv"
              onChange={handleFileUpload}
            />
            <button
              type="button"
              className="forecast-btn-secondary"
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              Choose File
            </button>
            {fileName && <span className="upload-filename">Selected: {fileName}</span>}
            {csvError && <span className="upload-error">{csvError}</span>}
            <p className="upload-note">
              CSV should contain: Date, Actual_Production (tonnes)
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="forecast-action-bar">
        <button
          type="button"
          className="forecast-btn-outline"
          onClick={onBack}
          disabled={loading}
        >
          &larr; Back
        </button>
        <button
          type="button"
          className="forecast-btn-primary"
          onClick={onNext}
          disabled={loading}
        >
          Next &rarr;
        </button>
      </div>
    </div>
  );
};

export default ProductionStepTwo;
