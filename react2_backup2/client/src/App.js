import './App.css';
import React, { useState, useCallback } from 'react';
import UploadPage from './components/UploadPage';
import Sidebar from './components/Sidebar';
import DataSummary from './components/DataSummary';
import TransformModal from './components/TransformModal';
import { API_ENDPOINTS, fetchAPI, TRANSFORMATIONS } from './utils/transformations';

/**
 * Main Dashboard Component
 * Manages the state and interactions between components
 * 
 * @param {Object} props
 * @param {Object} props.dataInfo - Initial dataset information
 */
function Dashboard({ dataInfo }) {
  // State management
  const [selectedColumns, setSelectedColumns] = useState({});
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [transformedColumns, setTransformedColumns] = useState([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [availableParameters, setAvailableParameters] = useState({});

  // Transform modal state
  const [showTransformModal, setShowTransformModal] = useState(false);
  const [selectedParameter, setSelectedParameter] = useState('');
  const [selectedTransformation, setSelectedTransformation] = useState('');
  const [transformVisualization, setTransformVisualization] = useState(null);
  const [transformedVisualization, setTransformedVisualization] = useState(null);
  const [newParameterName, setNewParameterName] = useState('');

  // Initialize columns and fetch summary on mount
  React.useEffect(() => {
    if (dataInfo && dataInfo.columns) {
      const initialColumns = {};
      const initialParams = {};
      dataInfo.columns.forEach(col => {
        initialColumns[col] = true;
        initialParams[col] = {
          type: dataInfo.column_types[col] || 'numeric',
          selected: true
        };
      });
      setSelectedColumns(initialColumns);
      setAvailableParameters(initialParams);
      // Fetch summary immediately after setting initial columns
      setTimeout(() => {
        fetchSummary(initialColumns);
      }, 0);
    }
  }, [dataInfo]);

  // Memoized fetchSummary to prevent unnecessary recreations
  const fetchSummary = useCallback(async (columns = selectedColumns) => {
    try {
      setIsRefreshing(true);
      const data = await fetchAPI(API_ENDPOINTS.SUMMARY, {
        method: 'POST',
        body: JSON.stringify({
          columns: Object.keys(columns).filter(col => columns[col])
        })
      });

      if (data.success) {
        setSummary(data);
        // Update available parameters with any new columns
        const updatedParams = { ...availableParameters };
        Object.keys(data.summary).forEach(col => {
          if (!updatedParams[col]) {
            // Determine type based on whether the column has numeric statistics
            const isNumeric = data.summary[col].hasOwnProperty('mean');
            updatedParams[col] = {
              type: isNumeric ? 'numeric' : 'categorical',
              selected: true
            };
          }
        });
        setAvailableParameters(updatedParams);
        setError(null);
      }
    } catch (err) {
      console.error('Summary error:', err);
      setError(`Failed to fetch summary: ${err.message}`);
    } finally {
      setIsRefreshing(false);
    }
  }, [selectedColumns, availableParameters]);

  /**
   * Handle column selection toggle
   */
  const handleColumnToggle = useCallback((column, isSelected) => {
    setSelectedColumns(prev => ({
      ...prev,
      [column]: isSelected
    }));
    setAvailableParameters(prev => ({
      ...prev,
      [column]: {
        ...prev[column],
        selected: isSelected
      }
    }));
  }, []);

  /**
   * Handle parameter selection in transform modal
   */
  const handleParameterSelect = (parameter, visualization) => {
    setSelectedParameter(parameter);
    setTransformVisualization(visualization);
    setTransformedVisualization(null);
    setSelectedTransformation('');
  };

  /**
   * Handle transformation selection in transform modal
   */
  const handleTransformationSelect = (transformation, visualization, defaultName) => {
    setSelectedTransformation(transformation);
    setTransformedVisualization(visualization);
    if (defaultName) {
      setNewParameterName(defaultName);
    }
  };

  /**
   * Apply transformation
   */
  const handleTransformApply = async () => {
    if (!newParameterName.trim()) {
      setError('Please provide a parameter name');
      return;
    }

    try {
      const data = await fetchAPI(API_ENDPOINTS.TRANSFORM, {
        method: 'POST',
        body: JSON.stringify({
          column: selectedParameter,
          transformation: selectedTransformation,
          new_column_name: newParameterName
        })
      });

      if (data.success) {
        // Handle created columns (multiple for one-hot encoding, single for others)
        const createdColumns = data.created_columns || [newParameterName];
        
        // Add transformed columns
        setTransformedColumns(prev => [...prev, ...createdColumns]);
        
        // Update selected columns
        setSelectedColumns(prev => {
          const updated = { ...prev };
          createdColumns.forEach(col => {
            updated[col] = true;
          });
          return updated;
        });
        
        // Update available parameters
        setAvailableParameters(prev => {
          const updated = { ...prev };
          createdColumns.forEach(col => {
            updated[col] = {
              type: selectedTransformation === 'one_hot_encoding' ? 'numeric' : 
                    ['log', 'sqrt', 'standard', 'minmax', 'label_encoding'].includes(selectedTransformation) ? 
                    'numeric' : 'categorical',
              selected: true
            };
          });
          return updated;
        });

        // Reset transform modal
        setShowTransformModal(false);
        setSelectedParameter('');
        setSelectedTransformation('');
        setTransformVisualization(null);
        setTransformedVisualization(null);
        setNewParameterName('');

        // Refresh summary
        await fetchSummary();
      }
    } catch (err) {
      console.error('Transform error:', err);
      setError(`Failed to transform data: ${err.message}`);
    }
  };

  /**
   * Save selected columns to CSV
   */
  const handleSave = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.SAVE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          columns: Object.keys(selectedColumns).filter(col => selectedColumns[col])
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle file download
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>Data Analysis Dashboard</h1>
        
        <div className="dashboard-container">
          {/* Sidebar */}
          <Sidebar
            dataInfo={dataInfo}
            selectedColumns={selectedColumns}
            transformedColumns={transformedColumns}
            onColumnToggle={handleColumnToggle}
          />

          {/* Main Content */}
          <div className="main-content">
            {/* Action Buttons */}
            <div className="top-buttons">
              <button 
                className="action-button" 
                onClick={() => setShowTransformModal(true)}
              >
                Transform
              </button>
              <button 
                className="action-button" 
                onClick={handleSave}
              >
                Save
              </button>
              <button 
                className="action-button refresh-button"
                onClick={() => fetchSummary()}
                disabled={isRefreshing}
              >
                {isRefreshing ? 'Refreshing...' : '↻ Refresh'}
              </button>
            </div>

            {/* Error Messages */}
            {error && <p className="error-message">{error}</p>}

            {/* Data Summary */}
            {summary && (
              <DataSummary
                summary={summary.summary}
                correlation={summary.correlation}
                pca={summary.pca}
                onRefresh={fetchSummary}
                isLoading={isRefreshing}
                availableParameters={availableParameters}
              />
            )}
          </div>
        </div>

        {/* Transform Modal */}
        {showTransformModal && (
          <TransformModal
            selectedParameter={selectedParameter}
            selectedTransformation={selectedTransformation}
            newParameterName={newParameterName}
            transformVisualization={transformVisualization}
            transformedVisualization={transformedVisualization}
            onClose={() => {
              setShowTransformModal(false);
              setSelectedParameter('');
              setSelectedTransformation('');
              setTransformVisualization(null);
              setTransformedVisualization(null);
              setNewParameterName('');
            }}
            onParameterSelect={handleParameterSelect}
            onTransformationSelect={handleTransformationSelect}
            onParameterNameChange={setNewParameterName}
            onApply={handleTransformApply}
            availableParameters={availableParameters}
            transformedColumns={transformedColumns}
          />
        )}
      </header>
    </div>
  );
}

/**
 * Main App Component
 * Handles initial file upload and switches to dashboard
 */
function App() {
  const [dataInfo, setDataInfo] = useState(null);

  return dataInfo ? (
    <Dashboard dataInfo={dataInfo} />
  ) : (
    <UploadPage onUploadSuccess={setDataInfo} />
  );
}

export default App;
