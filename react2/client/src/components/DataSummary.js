import React, { useState, useEffect, useCallback } from 'react';
import { fetchAPI, API_ENDPOINTS } from '../utils/transformations';
import SummaryTable from './SummaryTable';
import VisualizationControls from './VisualizationControls';
import HeadDataTable from './HeadDataTable';
import VisualizationButtons from './VisualizationButtons';
import LogTable from './LogTable';
import SavePrompt from './SavePrompt';

const DataSummary = ({ summary, correlation, pca, onRefresh, isLoading, availableParameters, logs }) => {
  const [selectedVisualization, setSelectedVisualization] = useState('summary');
  const [selectedParams, setSelectedParams] = useState([]);
  const [visualizationType, setVisualizationType] = useState('');
  const [customVisualization, setCustomVisualization] = useState(null);
  const [headData, setHeadData] = useState(null);
  const [headError, setHeadError] = useState(null);
  const [lastParamKeys, setLastParamKeys] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'ascending' });
  const [visualizationError, setVisualizationError] = useState(null);
  const [showSavePrompt, setShowSavePrompt] = useState(false);

  // Get selected parameters
  const selectedParametersList = Object.entries(availableParameters || {})
    .filter(([_, info]) => info.selected)
    .map(([param]) => param);

  const handleVisualizationRequest = useCallback(async () => {
    if (!visualizationType || selectedParams.length === 0) {
      setCustomVisualization(null);
      setVisualizationError(null);
      return;
    }
    
    try {
      setVisualizationError(null);
      
      const response = await fetchAPI(API_ENDPOINTS.VISUALIZE, {
        method: 'POST',
        body: JSON.stringify({
          parameters: selectedParams,
          type: visualizationType
        })
      });

      if (response.success && response.visualization) {
        try {
          atob(response.visualization);
          setCustomVisualization(response.visualization);
        } catch (e) {
          setVisualizationError('Invalid visualization data received');
          setCustomVisualization(null);
        }
      } else {
        setVisualizationError(response.error || 'Failed to generate visualization');
        setCustomVisualization(null);
      }
    } catch (error) {
      setVisualizationError(error.message || 'Failed to generate visualization');
      setCustomVisualization(null);
    }
  }, [visualizationType, selectedParams]);

  // Fetch head data when parameters actually change
  useEffect(() => {
    const currentKeys = selectedParametersList.sort().join(',');
    if (currentKeys !== lastParamKeys) {
      fetchHeadData();
      if (lastParamKeys !== null) { // Skip initial load
        onRefresh(); // Refresh summary data, including PCA
      }
      setLastParamKeys(currentKeys);
    }
  }, [selectedParametersList, onRefresh, lastParamKeys]);

  // Clean up selected params if they become unselected
  useEffect(() => {
    setSelectedParams(prev => prev.filter(param => selectedParametersList.includes(param)));
  }, [selectedParametersList]);

  if (!summary) return null;

  const fetchHeadData = async () => {
    try {
      setHeadError(null);
      setHeadData(null);
      const response = await fetchAPI(API_ENDPOINTS.HEAD);
      if (response.success) {
        // Filter head data to only show selected parameters
        const filteredData = response.data.map(row => {
          const filteredRow = {};
          selectedParametersList.forEach(param => {
            filteredRow[param] = row[param];
          });
          return filteredRow;
        });
        setHeadData(filteredData);
      } else {
        setHeadError(response.error || 'Failed to fetch data preview');
      }
    } catch (error) {
      setHeadError('Failed to fetch data preview. Please try again.');
    }
  };

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'ascending' 
        ? 'descending' 
        : 'ascending'
    }));
  };

  const handleSave = async (fileName) => {
    try {
      const response = await fetchAPI(API_ENDPOINTS.SAVE, {
        method: 'POST',
        body: JSON.stringify({ fileName })
      });
      
      if (!response.success) {
        throw new Error('Failed to save file');
      }
    } catch (error) {
      console.error('Failed to save:', error);
    }
    setShowSavePrompt(false);
  };

  const renderVisualizationContent = () => {
    switch (selectedVisualization) {
      case 'summary':
        return (
          <SummaryTable 
            summary={summary}
            sortConfig={sortConfig}
            handleSort={handleSort}
            availableParameters={availableParameters}
          />
        );

      case 'correlation':
        return correlation ? (
          <img 
            src={`data:image/png;base64,${correlation}`}
            alt="Correlation Matrix"
            style={{ maxWidth: '100%', height: 'auto' }}
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
              style={{ maxWidth: '100%', height: 'auto' }}
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
            <VisualizationControls 
              selectedParams={selectedParams}
              setSelectedParams={setSelectedParams}
              visualizationType={visualizationType}
              setVisualizationType={setVisualizationType}
              selectedParametersList={selectedParametersList}
              availableParameters={availableParameters}
              onGenerateVisualization={handleVisualizationRequest}
            />

            {visualizationError && (
              <p className="error-message">{visualizationError}</p>
            )}

            {customVisualization && (
              <div className="visualization-display">
                <img 
                  src={`data:image/png;base64,${customVisualization}`}
                  alt="Custom Visualization"
                  style={{ maxWidth: '100%', height: 'auto' }}
                  onError={(e) => {
                    setVisualizationError('Failed to load visualization');
                    setCustomVisualization(null);
                  }}
                />
              </div>
            )}
          </div>
        );

      case 'head':
        return (
          <HeadDataTable 
            headData={headData}
            headError={headError}
          />
        );

      case 'log':
        return <LogTable logs={logs} />;

      default:
        return null;
    }
  };

  return (
    <div className="analysis-content">
      <VisualizationButtons 
        selectedVisualization={selectedVisualization}
        setSelectedVisualization={setSelectedVisualization}
        fetchHeadData={fetchHeadData}
        headData={headData}
        headError={headError}
      />

      <div className="visualization-content">
        {renderVisualizationContent()}
      </div>

      {showSavePrompt && (
        <SavePrompt 
          onSave={handleSave}
          onCancel={() => setShowSavePrompt(false)}
        />
      )}
    </div>
  );
};

export default DataSummary;
