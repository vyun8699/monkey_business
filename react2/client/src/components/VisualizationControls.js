import React from 'react';
import { getVisualizationsForType } from '../utils/transformations';

const VisualizationControls = ({ 
  selectedParams,
  setSelectedParams,
  visualizationType,
  setVisualizationType,
  selectedParametersList,
  availableParameters,
  onGenerateVisualization
}) => {
  const getAvailableVisualizations = () => {
    if (selectedParams.length === 0) return [];
    
    // For two parameters, check if we're dealing with mixed types
    if (selectedParams.length === 2) {
      const xType = availableParameters[selectedParams[0]]?.type;
      const yType = availableParameters[selectedParams[1]]?.type;
      
      // If x is categorical and y is numeric, use MIXED visualizations
      if (xType === 'categorical' && yType === 'numeric') {
        return getVisualizationsForType('categorical', 2);
      }
      
      // Otherwise use the first parameter's type
      return getVisualizationsForType(xType, 2);
    }
    
    // For single parameter, use its type
    const paramType = availableParameters[selectedParams[0]]?.type;
    return getVisualizationsForType(paramType, 1);
  };

  return (
    <div className="visualization-controls">
      {/* X-axis Parameter Selection */}
      <div className="control-group">
        <label>X-axis Parameter:</label>
        <select 
          value={selectedParams[0] || ''}
          onChange={(e) => {
            const param = e.target.value;
            setSelectedParams(prev => [param, prev[1]].filter(Boolean));
            setVisualizationType(''); // Reset visualization type when parameter changes
          }}
        >
          <option value="">Select parameter...</option>
          {selectedParametersList.map(param => (
            <option key={param} value={param}>
              {param} ({availableParameters[param]?.type})
            </option>
          ))}
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
            setVisualizationType(''); // Reset visualization type when parameter changes
          }}
        >
          <option value="">Select parameter...</option>
          {selectedParametersList
            .filter(param => param !== selectedParams[0]) // Don't show already selected X parameter
            .map(param => (
              <option key={param} value={param}>
                {param} ({availableParameters[param]?.type})
              </option>
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
                onClick={() => {
                  console.log('Selected visualization type:', type.id);
                  setVisualizationType(type.id);
                }}
              >
                {type.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Generate Visualization Button */}
      {selectedParams.length > 0 && visualizationType && (
        <div className="control-group">
          <button 
            className="generate-visualization-button"
            onClick={onGenerateVisualization}
          >
            Generate Visualization
          </button>
        </div>
      )}

      {/* Debug Info */}
      {process.env.NODE_ENV === 'development' && (
        <div className="debug-info" style={{color: '#666', fontSize: '0.8em', marginTop: '10px'}}>
          <div>Selected Parameters: {selectedParams.join(', ')}</div>
          <div>Parameter Types: {selectedParams.map(p => availableParameters[p]?.type).join(', ')}</div>
          <div>Visualization Type: {visualizationType}</div>
          <div>Available Types: {getAvailableVisualizations().map(t => t.id).join(', ')}</div>
        </div>
      )}
    </div>
  );
};

export default VisualizationControls;
