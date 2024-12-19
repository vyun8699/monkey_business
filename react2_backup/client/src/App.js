import './App.css';
import { useState, useEffect } from 'react';

// This is for the CSV upload page
function App1() {
  const [file, setFile] = useState(null);
  const [uploaded, setUploaded] = useState(false);
  const [error, setError] = useState(null);
  const [dataInfo, setDataInfo] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');

  // Check server connection on component mount
  useEffect(() => {
    const checkServer = async () => {
      try {
        const response = await fetch('http://localhost:5001/test');
        const data = await response.json();
        if (data.status === "Server is running!") {
          setServerStatus('connected');
          setError(null);
        } else {
          setServerStatus('error');
          setError('Server response invalid');
        }
      } catch (err) {
        setServerStatus('error');
        setError('Cannot connect to server. Please make sure the Flask server is running on port 5001.');
      }
    };

    checkServer();
  }, []);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setError(null);
  };

  const handleUpload = async () => {
    if (serverStatus !== 'connected') {
      setError('Server is not connected. Please make sure the Flask server is running.');
      return;
    }

    if (!file) {
      setError('Please select a file');
      return;
    }

    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5001/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setDataInfo(data.info);
        setUploaded(true);
        setError(null);
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(`Upload failed: ${err.message}. Make sure the server is running and accessible.`);
    }
  };

  if (uploaded && dataInfo) {
    return <App2 dataInfo={dataInfo} />;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>EDA Platform</h1>
        <div className="server-status">
          Server Status: {
            serverStatus === 'checking' ? '🟡 Checking...' :
            serverStatus === 'connected' ? '🟢 Connected' :
            '🔴 Not Connected'
          }
        </div>
        <div className="upload-section">
          <h2>Upload your CSV file</h2>
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="file-input"
          />
          <button 
            onClick={handleUpload} 
            className="upload-button"
            disabled={serverStatus !== 'connected'}
          >
            Upload
          </button>
          {error && <p className="error-message">{error}</p>}
        </div>
      </header>
    </div>
  );
}

// This is for the dashboard page
function App2({ dataInfo }) {
  const [selectedColumns, setSelectedColumns] = useState({});
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [showTransformModal, setShowTransformModal] = useState(false);
  const [selectedParameter, setSelectedParameter] = useState('');
  const [selectedTransformation, setSelectedTransformation] = useState('');
  const [transformVisualization, setTransformVisualization] = useState(null);
  const [transformedVisualization, setTransformedVisualization] = useState(null);
  const [transformedColumns, setTransformedColumns] = useState([]);
  const [newParameterName, setNewParameterName] = useState('');

  // Initialize selected columns and fetch summary
  useEffect(() => {
    if (dataInfo && dataInfo.columns) {
      const initialColumns = {};
      dataInfo.columns.forEach(col => {
        initialColumns[col] = true;
      });
      setSelectedColumns(initialColumns);
    }
  }, [dataInfo]);

  useEffect(() => {
    if (Object.keys(selectedColumns).length > 0) {
      fetchSummary();
    }
  }, [selectedColumns]);

  // Update suggested parameter name when parameter or transformation changes
  useEffect(() => {
    if (selectedParameter && selectedTransformation) {
      setNewParameterName(`${selectedParameter}_${selectedTransformation}`);
    }
  }, [selectedParameter, selectedTransformation]);

  const fetchSummary = async () => {
    try {
      const response = await fetch('http://localhost:5001/summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ columns: Object.keys(selectedColumns).filter(col => selectedColumns[col]) }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        setSummary(data);
        setError(null);
      } else {
        setError(data.error);
      }
    } catch (err) {
      console.error('Summary error:', err);
      setError(`Failed to fetch summary: ${err.message}`);
    }
  };

  const handleParameterSelect = async (parameter) => {
    setSelectedParameter(parameter);
    try {
      const response = await fetch('http://localhost:5001/transform', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          column: parameter,
          visualization_only: true
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        setTransformVisualization(data.visualization);
        setTransformedVisualization(null); // Reset transformed visualization
        setSelectedTransformation(''); // Reset transformation selection
      } else {
        setError(data.error);
      }
    } catch (err) {
      console.error('Transform visualization error:', err);
      setError(`Failed to get visualization: ${err.message}`);
    }
  };

  const handleTransformationSelect = async (transformation) => {
    setSelectedTransformation(transformation);
    try {
      const response = await fetch('http://localhost:5001/transform', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          column: selectedParameter,
          transformation: transformation,
          preview: true // Just get the visualization without applying the transformation
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        setTransformedVisualization(data.visualization);
      } else {
        setError(data.error);
      }
    } catch (err) {
      console.error('Transform preview error:', err);
      setError(`Failed to preview transformation: ${err.message}`);
    }
  };

  const handleTransformApply = async () => {
    if (!newParameterName.trim()) {
      setError('Please provide a parameter name');
      return;
    }
    try {
      const response = await fetch('http://localhost:5001/transform', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          column: selectedParameter,
          transformation: selectedTransformation,
          new_column_name: newParameterName
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        // Add transformed column to the list
        setTransformedColumns([...transformedColumns, newParameterName]);
        setSelectedColumns(prev => ({
          ...prev,
          [newParameterName]: true
        }));
        // Reset transform modal state
        setShowTransformModal(false);
        setSelectedParameter('');
        setSelectedTransformation('');
        setTransformVisualization(null);
        setTransformedVisualization(null);
        setNewParameterName('');
        // Refresh summary
        fetchSummary();
      } else {
        setError(data.error);
      }
    } catch (err) {
      console.error('Transform error:', err);
      setError(`Failed to transform data: ${err.message}`);
    }
  };

  const handleSave = async () => {
    try {
      const response = await fetch('http://localhost:5001/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ columns: Object.keys(selectedColumns).filter(col => selectedColumns[col]) }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'transformed_data.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Save error:', err);
      setError(`Failed to save data: ${err.message}`);
    }
  };

  const TransformModal = () => (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Transform Data</h2>
        <div className="transform-form">
          <div className="form-group">
            <label>Select Parameter:</label>
            <select 
              value={selectedParameter}
              onChange={(e) => handleParameterSelect(e.target.value)}
            >
              <option value="">Select a parameter...</option>
              {Object.keys(selectedColumns)
                .filter(col => selectedColumns[col] && !transformedColumns.includes(col))
                .map(col => (
                  <option key={col} value={col}>{col}</option>
                ))
              }
            </select>
          </div>

          {selectedParameter && (
            <div className="form-group">
              <label>Select Transformation:</label>
              <select 
                value={selectedTransformation}
                onChange={(e) => handleTransformationSelect(e.target.value)}
              >
                <option value="">Select a transformation...</option>
                <option value="log">Log Transform</option>
                <option value="sqrt">Square Root</option>
                <option value="standard">Standardization</option>
                <option value="minmax">Min-Max Scaling</option>
              </select>
            </div>
          )}

          {selectedParameter && selectedTransformation && (
            <div className="form-group">
              <label>New Parameter Name:</label>
              <input
                type="text"
                value={newParameterName}
                onChange={(e) => setNewParameterName(e.target.value)}
                placeholder="Enter parameter name"
              />
            </div>
          )}

          {transformVisualization && (
            <div className="visualization-container">
              <div className="visualization-box">
                <h3>Original Distribution</h3>
                <img 
                  src={`data:image/png;base64,${transformVisualization}`}
                  alt="Original Distribution"
                  style={{maxWidth: '100%', height: 'auto'}}
                />
              </div>
              {transformedVisualization && (
                <div className="visualization-box">
                  <h3>Transformed Distribution</h3>
                  <img 
                    src={`data:image/png;base64,${transformedVisualization}`}
                    alt="Transformed Distribution"
                    style={{maxWidth: '100%', height: 'auto'}}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        <div className="modal-buttons">
          <button 
            className="action-button" 
            onClick={() => {
              setShowTransformModal(false);
              setSelectedParameter('');
              setSelectedTransformation('');
              setTransformVisualization(null);
              setTransformedVisualization(null);
              setNewParameterName('');
            }}
          >
            Cancel
          </button>
          {selectedParameter && selectedTransformation && (
            <button 
              className="action-button"
              onClick={handleTransformApply}
            >
              Apply
            </button>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      <header className="App-header">
        <h1>Data Analysis Dashboard</h1>
        
        <div className="dashboard-container">
          <div className="sidebar">
            <h2>Dataset Information</h2>
            <p>Number of rows: {dataInfo.num_rows}</p>
            <p>Number of columns: {dataInfo.num_columns}</p>
            <h3>Parameters</h3>
            {Object.keys(selectedColumns).map(col => (
              <div key={col} className="column-checkbox">
                <input
                  type="checkbox"
                  id={col}
                  checked={selectedColumns[col]}
                  onChange={(e) => setSelectedColumns({
                    ...selectedColumns,
                    [col]: e.target.checked
                  })}
                />
                <label htmlFor={col}>
                  {col}
                  {transformedColumns.includes(col) && ' (transformed)'}
                </label>
              </div>
            ))}
          </div>

          <div className="main-content">
            <div className="top-buttons">
              <button className="action-button" onClick={() => setShowTransformModal(true)}>Transform</button>
              <button className="action-button" onClick={handleSave}>Save</button>
            </div>

            {error && <p className="error-message">{error}</p>}

            {summary && (
              <div className="analysis-content">
                <h2>Summary</h2>
                <div className="summary-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Parameter</th>
                        <th>Mean</th>
                        <th>Std</th>
                        <th>Min</th>
                        <th>25%</th>
                        <th>50%</th>
                        <th>75%</th>
                        <th>Max</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(summary.summary).map(([col, stats]) => (
                        <tr key={col}>
                          <td>{col}</td>
                          <td>{stats.mean?.toFixed(2) ?? 'N/A'}</td>
                          <td>{stats.std?.toFixed(2) ?? 'N/A'}</td>
                          <td>{stats.min?.toFixed(2) ?? 'N/A'}</td>
                          <td>{stats['25%']?.toFixed(2) ?? 'N/A'}</td>
                          <td>{stats['50%']?.toFixed(2) ?? 'N/A'}</td>
                          <td>{stats['75%']?.toFixed(2) ?? 'N/A'}</td>
                          <td>{stats.max?.toFixed(2) ?? 'N/A'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="visualization-row">
                  <div className="visualization-column">
                    <h3>Correlation Matrix</h3>
                    {summary.correlation && (
                      <img 
                        src={`data:image/png;base64,${summary.correlation}`}
                        alt="Correlation Matrix"
                        style={{maxWidth: '100%', height: 'auto'}}
                      />
                    )}
                  </div>
                  <div className="visualization-column">
                    <h3>PCA Plot</h3>
                    {summary.pca && (
                      <>
                        <img 
                          src={`data:image/png;base64,${summary.pca.image}`}
                          alt="PCA Plot"
                          style={{maxWidth: '100%', height: 'auto'}}
                        />
                        <p>Explained Variance Ratio: {summary.pca.explained_variance_ratio.map(v => (v * 100).toFixed(2) + '%').join(', ')}</p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {showTransformModal && <TransformModal />}
      </header>
    </div>
  );
}

// Export the upload page as the initial view
export default App1;
