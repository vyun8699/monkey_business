import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import './App.css';
import * as api from './utils/apiHelpers';
import * as transformUtils from './utils/transformHelpers';

function App() {
  const [file, setFile] = useState(null);
  const [dataInfo, setDataInfo] = useState(null);
  const [preview, setPreview] = useState(null);
  const [transformations, setTransformations] = useState(null);
  const [selectedColumn, setSelectedColumn] = useState('');
  const [selectedTransform, setSelectedTransform] = useState('');
  const [transformationLog, setTransformationLog] = useState([]);
  const [previewTransformation, setPreviewTransformation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [transformedColumns, setTransformedColumns] = useState(new Set());
  const [selectedParameters, setSelectedParameters] = useState(new Set());
  const [collapsedSections, setCollapsedSections] = useState({
    dataPreview: false,
    transformations: false,
    log: false,
    nullAnalysis: false
  });
  const [selectedNullColumn, setSelectedNullColumn] = useState('');

  // Fetch available transformations on component mount
  useEffect(() => {
    api.fetchTransformations()
      .then(data => setTransformations(data))
      .catch(error => {
        console.error('Error fetching transformations:', error);
        setError('Failed to load transformations');
      });
  }, []);

  // Fetch column preview when column changes
  useEffect(() => {
    if (selectedColumn) {
      const fetchColumnPreview = async () => {
        try {
          setLoading(true);
          setError(null);
          const data = await api.previewColumn(selectedColumn);
          if (data.success) {
            setPreviewTransformation(data.preview);
          } else {
            throw new Error(data.error || 'Failed to preview column');
          }
        } catch (error) {
          setError('Error previewing column: ' + error.message);
          console.error('Error previewing column:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchColumnPreview();
    }
  }, [selectedColumn]);

  // Fetch transformation preview when transformation changes
  useEffect(() => {
    if (selectedColumn && selectedTransform) {
      previewTransform();
    }
  }, [selectedTransform]); // Only trigger on transformation change

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      setLoading(true);
      setError(null);
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const data = await api.uploadFile(e.target.result);
          if (data.success) {
            setDataInfo(data.info);
            setTransformedColumns(new Set());
            setSelectedParameters(new Set(data.info.columns)); // Initially select all columns
            fetchPreview();
          } else {
            setError(data.error || 'Failed to upload file');
          }
        } catch (error) {
          setError('Error uploading file');
          console.error('Error uploading file:', error);
        } finally {
          setLoading(false);
        }
      };
      reader.readAsDataURL(file);
      setFile(file);
    }
  };

  const fetchPreview = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.fetchPreview();
      if (data && data.data && Array.isArray(data.data)) {
        setPreview(data);
      } else {
        throw new Error('Invalid preview data format');
      }
    } catch (error) {
      setError('Error fetching preview: ' + error.message);
      console.error('Error fetching preview:', error);
    } finally {
      setLoading(false);
    }
  };

  const previewTransform = async () => {
    if (!selectedColumn || !selectedTransform) return;

    try {
      setLoading(true);
      setError(null);
      const data = await api.previewTransform(selectedColumn, selectedTransform);
      if (data.success) {
        setPreviewTransformation(data.preview);
      } else {
        throw new Error(data.error || 'Failed to preview transformation');
      }
    } catch (error) {
      setError('Error previewing transformation: ' + error.message);
      console.error('Error previewing transformation:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTransform = async () => {
    if (!selectedColumn || !selectedTransform) return;

    try {
      setLoading(true);
      setError(null);
      const data = await api.applyTransform(selectedColumn, selectedTransform);
      if (data.success) {
        setPreview({
          data: data.preview.data,
          columns: data.preview.columns,
        });
        
        // Get new columns based on transformation type
        const getNewColumns = transformUtils.getTransformedColumnNames(selectedColumn, selectedTransform);
        const newColumns = getNewColumns(data.preview.columns);

        // Update dataInfo with new columns and types
        setDataInfo(data.info);

        setTransformationLog(prev => [...prev, {
          timestamp: new Date().toLocaleString(),
          column: selectedColumn,
          transformation: selectedTransform,
          newColumns
        }]);

        setTransformedColumns(prev => new Set([...prev, ...newColumns]));
        setSelectedParameters(prev => new Set([...prev, ...newColumns]));

        setSelectedColumn('');
        setSelectedTransform('');
        setPreviewTransformation(null);
      } else {
        throw new Error(data.error || 'Failed to apply transformation');
      }
    } catch (error) {
      setError('Error applying transformation: ' + error.message);
      console.error('Error applying transformation:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveNulls = async () => {
    if (!selectedNullColumn) return;

    try {
      setLoading(true);
      setError(null);
      const data = await api.applyTransform(selectedNullColumn, 'remove_nulls');
      if (data.success) {
        setPreview({
          data: data.preview.data,
          columns: data.preview.columns,
        });

        setDataInfo(data.info);

        setTransformationLog(prev => [...prev, {
          timestamp: new Date().toLocaleString(),
          column: selectedNullColumn,
          transformation: 'Remove Null Values',
          newColumns: [] // No new columns are created
        }]);

        setSelectedNullColumn('');
      } else {
        throw new Error(data.error || 'Failed to remove null values');
      }
    } catch (error) {
      setError('Error removing null values: ' + error.message);
      console.error('Error removing null values:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      await api.saveToCSV(Array.from(selectedParameters));
    } catch (error) {
      setError('Error saving file: ' + error.message);
      console.error('Error saving file:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const toggleParameter = (parameter) => {
    setSelectedParameters(prev => {
      const newSet = new Set(prev);
      if (newSet.has(parameter)) {
        newSet.delete(parameter);
      } else {
        newSet.add(parameter);
      }
      return newSet;
    });
  };

  const isTransformationDisabled = (column, transformation) => {
    if (transformation === 'onehot' && dataInfo?.categorical_info?.[column] > 10) {
      return true;
    }
    return false;
  };

  const getTransformationWarning = (column, transformation) => {
    if (transformation === 'onehot' && dataInfo?.categorical_info?.[column] > 10) {
      return `This column has ${dataInfo.categorical_info[column]} unique values. One-hot encoding is limited to columns with 10 or fewer unique values.`;
    }
    return null;
  };

  const renderChart = (data, column, type) => {
    if (!data || data.length === 0 || !column) return null;

    // Extract the actual data array from the API response format
    const chartData = transformUtils.prepareChartData(
      // If data is an array of objects with the column as key, use it directly
      Array.isArray(data) ? data : Object.values(data)[0],
      // If column is an object key, get the first key
      typeof column === 'string' ? column : Object.keys(data[0])[0],
      type
    );

    if (chartData.length === 0) return null;

    const CustomTooltip = ({ active, payload, label }) => {
      if (active && payload && payload.length) {
        return (
          <div className="custom-tooltip" style={{ 
            backgroundColor: 'white', 
            padding: '10px', 
            border: '1px solid #ccc' 
          }}>
            <p>{`Range: ${label}`}</p>
            <p>{`Count: ${payload[0].value}`}</p>
          </div>
        );
      }
      return null;
    };

    return (
      <BarChart 
        width={400} 
        height={300} 
        data={chartData} 
        margin={{ 
          top: 20, 
          right: 30, 
          left: type === 'numeric' ? 40 : 20, 
          bottom: 60 
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="category"
          angle={-45}
          textAnchor="end"
          height={70}
          interval={0}
          fontSize={10}
          tickFormatter={label => type === 'numeric' ? label : (label.length > 15 ? `${label.substring(0, 15)}...` : label)}
        />
        <YAxis 
          dataKey="count"
          label={{ 
            value: 'Count', 
            angle: -90, 
            position: 'insideLeft',
            offset: -5
          }} 
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar 
          dataKey="count" 
          fill="#8884d8"
          maxBarSize={50}
        />
      </BarChart>
    );
  };

  return (
    <div className="App">
      <div className="sidebar">
        <div className="section">
          <h2>Input</h2>
          <div className="file-upload">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="file-input"
              disabled={loading}
            />
            {file && <p>Selected file: {file.name}</p>}
            {loading && <p>Loading...</p>}
            {error && <p className="error-message">{error}</p>}
          </div>
        </div>

        {dataInfo && (
          <div className="section">
            <h2>Dataset Info</h2>
            <div className="info-grid">
              <div>
                <h3>Rows: {dataInfo.rows}</h3>
              </div>
              <div>
                <h3>Parameters:</h3>
                <ul className="parameter-list">
                  {dataInfo.columns.map(col => (
                    <li key={col} className={transformedColumns.has(col) ? 'transformed' : ''}>
                      <label>
                        <input
                          type="checkbox"
                          checked={selectedParameters.has(col)}
                          onChange={() => toggleParameter(col)}
                        />
                        {col}
                        {dataInfo.categorical_info?.[col] > 10 && (
                          <span className="category-count" title="Number of unique values">
                            ({dataInfo.categorical_info[col]})
                          </span>
                        )}
                      </label>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <button 
              onClick={handleSave} 
              disabled={loading || selectedParameters.size === 0}
              className="save-button"
            >
              Save Selected Parameters
            </button>
          </div>
        )}
      </div>

      <div className="main-content">
        <header className="App-header">
          <h1>No-Code EDA Platform</h1>
        </header>

        {preview && preview.data && preview.data.length > 0 && (
          <section className="section">
            <h2 onClick={() => toggleSection('dataPreview')}>
              Data Preview
              <span className={`toggle-icon ${collapsedSections.dataPreview ? 'collapsed' : ''}`}>
                ▼
              </span>
            </h2>
            <div className={`section-content ${collapsedSections.dataPreview ? 'collapsed' : ''}`}>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      {preview.columns.map(col => (
                        <th key={col} className={transformedColumns.has(col) ? 'transformed' : ''}>
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.data.slice(0, 5).map((row, i) => (
                      <tr key={i}>
                        {preview.columns.map(col => (
                          <td key={col} title={row[col]}>
                            {row[col]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {dataInfo?.null_info && (
          <section className="section">
            <h2 onClick={() => toggleSection('nullAnalysis')}>
              Null Value Analysis
              <span className={`toggle-icon ${collapsedSections.nullAnalysis ? 'collapsed' : ''}`}>
                ▼
              </span>
            </h2>
            <div className={`section-content ${collapsedSections.nullAnalysis ? 'collapsed' : ''}`}>
              <div className="null-analysis-controls">
                <div className="control-group">
                  <label>Select Column to Remove Nulls:</label>
                  <select
                    value={selectedNullColumn}
                    onChange={(e) => setSelectedNullColumn(e.target.value)}
                    disabled={loading}
                  >
                    <option value="">Choose a column</option>
                    {Object.entries(dataInfo.null_info)
                      .filter(([_, info]) => info.null_count > 0)
                      .sort((a, b) => b[1].null_percentage - a[1].null_percentage)
                      .map(([column, info]) => (
                        <option key={column} value={column}>
                          {column} ({info.null_percentage.toFixed(2)}% nulls)
                        </option>
                      ))}
                  </select>
                  <button
                    onClick={handleRemoveNulls}
                    disabled={!selectedNullColumn || loading}
                    className="remove-nulls-button"
                  >
                    Remove Nulls
                  </button>
                </div>
              </div>
              <div className="table-container">
                <table className="null-analysis-table">
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Null Count</th>
                      <th>Null %</th>
                      <th>Total Rows</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(dataInfo.null_info)
                      .sort((a, b) => b[1].null_percentage - a[1].null_percentage)
                      .map(([column, info]) => (
                        <tr key={column}>
                          <td>{column}</td>
                          <td>{info.null_count}</td>
                          <td>{info.null_percentage.toFixed(2)}%</td>
                          <td>{info.total_rows}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        )}

        {dataInfo && transformations && (
          <section className="section">
            <h2 onClick={() => toggleSection('transformations')}>
              Transformations
              <span className={`toggle-icon ${collapsedSections.transformations ? 'collapsed' : ''}`}>
                ▼
              </span>
            </h2>
            <div className={`section-content ${collapsedSections.transformations ? 'collapsed' : ''}`}>
              <div className="transformation-controls">
                <div className="control-group">
                  <label>Select Column:</label>
                  <select
                    value={selectedColumn}
                    onChange={(e) => {
                      setSelectedColumn(e.target.value);
                      setSelectedTransform('');
                      setError(null);
                    }}
                    disabled={loading}
                  >
                    <option value="">Choose a column</option>
                    {dataInfo.columns.map(col => (
                      <option key={col} value={col}>
                        {col} {dataInfo.categorical_info?.[col] > 10 ? `(${dataInfo.categorical_info[col]} categories)` : ''}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedColumn && (
                  <div className="control-group">
                    <label>Select Transformation:</label>
                    <select
                      value={selectedTransform}
                      onChange={(e) => {
                        setSelectedTransform(e.target.value);
                        setError(null);
                      }}
                      disabled={loading}
                    >
                      <option value="">Choose a transformation</option>
                      {dataInfo.numeric_columns.includes(selectedColumn) ? (
                        Object.entries(transformations.numeric).map(([key, desc]) => (
                          <option key={key} value={key} disabled={isTransformationDisabled(selectedColumn, key)}>
                            {desc}
                          </option>
                        ))
                      ) : (
                        Object.entries(transformations.categorical).map(([key, desc]) => (
                          <option key={key} value={key} disabled={isTransformationDisabled(selectedColumn, key)}>
                            {desc}
                          </option>
                        ))
                      )}
                    </select>
                    {selectedTransform && getTransformationWarning(selectedColumn, selectedTransform) && (
                      <div className="warning-message">
                        {getTransformationWarning(selectedColumn, selectedTransform)}
                      </div>
                    )}
                  </div>
                )}

                {previewTransformation && (
                  <div className="preview-comparison">
                    <div className="preview-panel">
                      <h3>Before</h3>
                      <div className="table-container">
                        <table>
                          <thead>
                            <tr>
                              <th>{selectedColumn}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {previewTransformation.original.preview.map((row, i) => (
                              <tr key={i}>
                                <td title={Object.values(row)[0]}>
                                  {Object.values(row)[0]}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="chart-container">
                        {renderChart(
                          previewTransformation.original.full,
                          selectedColumn,
                          dataInfo.numeric_columns.includes(selectedColumn) ? 'numeric' : 'categorical'
                        )}
                      </div>
                    </div>
                    <div className="preview-panel">
                      <h3>After</h3>
                      <div className="table-container">
                        <table>
                          <thead>
                            <tr>
                              {selectedTransform === 'onehot' ? (
                                Object.keys(previewTransformation.transformed.preview[0]).map(col => (
                                  <th key={col}>{col}</th>
                                ))
                              ) : (
                                <th>{Object.keys(previewTransformation.transformed.preview[0])[0]}</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {previewTransformation.transformed.preview.map((row, i) => (
                              <tr key={i}>
                                {selectedTransform === 'onehot' ? (
                                  Object.values(row).map((value, j) => (
                                    <td key={j}>{value}</td>
                                  ))
                                ) : (
                                  <td title={Object.values(row)[0]}>
                                    {Object.values(row)[0]}
                                  </td>
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {selectedTransform !== 'onehot' && (
                        <div className="chart-container">
                          {renderChart(
                            previewTransformation.transformed.full,
                            Object.keys(previewTransformation.transformed.preview[0])[0],
                            'numeric'
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <button
                  onClick={handleTransform}
                  disabled={!selectedColumn || !selectedTransform || loading || isTransformationDisabled(selectedColumn, selectedTransform)}
                  className="transform-button"
                >
                  {loading ? 'Applying...' : 'Apply Transformation'}
                </button>
              </div>
            </div>
          </section>
        )}

        <section className="section">
          <h2 onClick={() => toggleSection('log')}>
            Log
            <span className={`toggle-icon ${collapsedSections.log ? 'collapsed' : ''}`}>
              ▼
            </span>
          </h2>
          <div className={`section-content ${collapsedSections.log ? 'collapsed' : ''}`}>
            {transformationLog.map((log, index) => (
              <div key={index} className="log-entry">
                <div className="timestamp">{log.timestamp}</div>
                <div>
                  Applied <strong>{log.transformation}</strong> to column <strong>{log.column}</strong>
                  {log.newColumns && log.newColumns.length > 0 && (
                    <div className="new-columns">
                      Created columns: {log.newColumns.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {transformationLog.length === 0 && (
              <p>No transformations applied yet.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
