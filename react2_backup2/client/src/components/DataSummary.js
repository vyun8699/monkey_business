import React, { useState, useEffect } from 'react';
import { formatNumber, VISUALIZATION_TYPES, getVisualizationsForType, fetchAPI, API_ENDPOINTS } from '../utils/transformations';

const DataSummary = ({ summary, correlation, pca, onRefresh, isLoading, availableParameters }) => {
  const [selectedVisualization, setSelectedVisualization] = useState('summary');
  const [selectedParams, setSelectedParams] = useState([]);
  const [visualizationType, setVisualizationType] = useState('');
  const [customVisualization, setCustomVisualization] = useState(null);
  const [headData, setHeadData] = useState(null);
  const [lastParamKeys, setLastParamKeys] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'ascending' });

  // Fetch head data when parameters actually change
  useEffect(() => {
    const currentKeys = availableParameters ? Object.keys(availableParameters).sort().join(',') : '';
    if (currentKeys !== lastParamKeys) {
      fetchHeadData();
      if (lastParamKeys !== null) { // Skip initial load
        onRefresh(); // Refresh summary data, including PCA
      }
      setLastParamKeys(currentKeys);
    }
  }, [availableParameters, onRefresh, lastParamKeys]);

  // Reset visualization when parameters change
  useEffect(() => {
    setCustomVisualization(null);
    setVisualizationType('');
  }, [selectedParams]);

  if (!summary) return null;

  const handleVisualizationRequest = async () => {
    try {
      const response = await fetchAPI(API_ENDPOINTS.VISUALIZE, {
        method: 'POST',
        body: JSON.stringify({
          parameters: selectedParams,
          type: visualizationType
        })
      });

      if (response.success) {
        setCustomVisualization(response.visualization);
      }
    } catch (error) {
      console.error('Failed to generate visualization:', error);
    }
  };

  const fetchHeadData = async () => {
    try {
      const response = await fetchAPI(API_ENDPOINTS.HEAD);
      if (response.success) {
        setHeadData(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch head data:', error);
    }
  };

  const getAvailableVisualizations = () => {
    if (selectedParams.length === 0) return [];
    const paramTypes = selectedParams.map(param => 
      availableParameters[param]?.type || 'numeric'
    );
    return getVisualizationsForType(paramTypes[0], selectedParams.length);
  };

  const handleSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const getSortedData = () => {
    if (!sortConfig.key) return Object.entries(summary);

    return [...Object.entries(summary)].sort((a, b) => {
      const aValue = a[1][sortConfig.key] ?? '';
      const bValue = b[1][sortConfig.key] ?? '';
      
      if (aValue === bValue) return 0;
      if (aValue === '') return 1;
      if (bValue === '') return -1;
      
      return sortConfig.direction === 'ascending' 
        ? (aValue < bValue ? -1 : 1)
        : (aValue > bValue ? -1 : 1);
    });
  };

  const renderValue = (value) => {
    if (value === null || value === undefined || value === '' || value === 'N/A') {
      return <span className="na-value">N/A</span>;
    }
    return value;
  };

  const renderVisualizationContent = () => {
    switch (selectedVisualization) {
      case 'summary':
        return (
          <div className="summary-table">
            <table>
              <thead>
                <tr>
                  <th onClick={() => handleSort('parameter')}>Parameter</th>
                  <th onClick={() => handleSort('type')}>Type</th>
                  <th onClick={() => handleSort('count')}>Count</th>
                  <th onClick={() => handleSort('unique_count')}>Unique Count</th>
                  <th onClick={() => handleSort('null_count')}>Null Count</th>
                  <th onClick={() => handleSort('mean')}>Mean</th>
                  <th onClick={() => handleSort('std')}>Std</th>
                  <th onClick={() => handleSort('min')}>Min</th>
                  <th onClick={() => handleSort('25%')}>25%</th>
                  <th onClick={() => handleSort('50%')}>50%</th>
                  <th onClick={() => handleSort('75%')}>75%</th>
                  <th onClick={() => handleSort('max')}>Max</th>
                </tr>
              </thead>
              <tbody>
                {getSortedData().map(([col, stats]) => {
                  const isTransformed = availableParameters[col]?.isTransformed;
                  return (
                    <tr key={col}>
                      <td className={isTransformed ? 'transformed-parameter' : ''}>{col}</td>
                      <td>{renderValue(availableParameters[col]?.type)}</td>
                      <td>{renderValue(stats.count)}</td>
                      <td>{renderValue(stats.unique_count)}</td>
                      <td className="na-value">{stats.null_count || 0}</td>
                      <td>{renderValue(formatNumber(stats.mean))}</td>
                      <td>{renderValue(formatNumber(stats.std))}</td>
                      <td>{renderValue(formatNumber(stats.min))}</td>
                      <td>{renderValue(formatNumber(stats['25%']))}</td>
                      <td>{renderValue(formatNumber(stats['50%']))}</td>
                      <td>{renderValue(formatNumber(stats['75%']))}</td>
                      <td>{renderValue(formatNumber(stats.max))}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );

      case 'correlation':
        return correlation ? (
          <img 
            src={`data:image/png;base64,${correlation}`}
            alt="Correlation Matrix"
          />
        ) : (
          <p>No correlation data available</p>
        );

      case 'pca':
        return pca ? (
          <>
            <img 
              src={`data:image/png;base64,${pca.image}`}
              alt="PCA Plot"
            />
            <p>
              Explained Variance Ratio: {
                pca.explained_variance_ratio
                  .map(v => `${(v * 100).toFixed(2)}%`)
                  .join(', ')
              }
            </p>
          </>
        ) : (
          <p>No PCA data available</p>
        );

      case 'custom':
        return (
          <div className="custom-visualization">
            <div className="visualization-controls">
              {/* X-axis Parameter Selection */}
              <div className="control-group">
                <label>X-axis Parameter:</label>
                <select 
                  value={selectedParams[0] || ''}
                  onChange={(e) => {
                    const param = e.target.value;
                    setSelectedParams(prev => [param, prev[1]].filter(Boolean));
                  }}
                >
                  <option value="">Select parameter...</option>
                  {Object.entries(availableParameters || {})
                    .filter(([_, info]) => info.selected)
                    .map(([param, _]) => (
                      <option key={param} value={param}>{param}</option>
                    ))
                  }
                </select>
              </div>

              {/* Y-axis Parameter Selection */}
              <div className="control-group">
                <label>Y-axis Parameter (optional):</label>
                <select 
                  value={selectedParams[1] || ''}
                  onChange={(e) => {
                    const param = e.target.value;
                    setSelectedParams(prev => [prev[0], param].filter(Boolean));
                  }}
                >
                  <option value="">Select parameter...</option>
                  {Object.entries(availableParameters || {})
                    .filter(([_, info]) => info.selected)
                    .map(([param, _]) => (
                      <option key={param} value={param}>{param}</option>
                    ))
                  }
                </select>
              </div>

              {/* Chart Type Selection */}
              {selectedParams.length > 0 && (
                <div className="control-group">
                  <label>Chart Type:</label>
                  <div className="chart-type-buttons">
                    {getAvailableVisualizations().map(type => (
                      <button
                        key={type.id}
                        className={`chart-type-button ${visualizationType === type.id ? 'active' : ''}`}
                        onClick={() => setVisualizationType(type.id)}
                      >
                        {type.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {selectedParams.length > 0 && visualizationType && (
                <button 
                  className="action-button"
                  onClick={handleVisualizationRequest}
                >
                  Generate Visualization
                </button>
              )}
            </div>

            {customVisualization && (
              <div className="visualization-display">
                <img 
                  src={`data:image/png;base64,${customVisualization}`}
                  alt="Custom Visualization"
                />
              </div>
            )}
          </div>
        );

      case 'head':
        return headData ? (
          <div className="head-data">
            <table>
              <thead>
                <tr>
                  {Object.keys(headData[0] || {}).map(key => (
                    <th key={key}>{key}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {headData.map((row, i) => (
                  <tr key={i}>
                    {Object.values(row).map((value, j) => (
                      <td key={j}>{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>Loading data preview...</p>
        );

      default:
        return null;
    }
  };

  return (
    <div className="analysis-content">
      {/* Visualization Selection Buttons */}
      <div className="visualization-buttons">
        <button 
          className={`viz-button ${selectedVisualization === 'summary' ? 'active' : ''}`}
          onClick={() => setSelectedVisualization('summary')}
        >
          Dashboard
        </button>
        <button 
          className={`viz-button ${selectedVisualization === 'correlation' ? 'active' : ''}`}
          onClick={() => setSelectedVisualization('correlation')}
        >
          Correlation Matrix
        </button>
        <button 
          className={`viz-button ${selectedVisualization === 'pca' ? 'active' : ''}`}
          onClick={() => setSelectedVisualization('pca')}
        >
          PCA
        </button>
        <button 
          className={`viz-button ${selectedVisualization === 'custom' ? 'active' : ''}`}
          onClick={() => setSelectedVisualization('custom')}
        >
          Custom Visualization
        </button>
        <button 
          className={`viz-button ${selectedVisualization === 'head' ? 'active' : ''}`}
          onClick={() => setSelectedVisualization('head')}
        >
          Head
        </button>
      </div>

      {/* Visualization Content */}
      <div className="visualization-content">
        {renderVisualizationContent()}
      </div>
    </div>
  );
};

export default DataSummary;
