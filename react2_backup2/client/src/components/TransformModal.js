import React from 'react';
import { TRANSFORMATIONS, API_ENDPOINTS, fetchAPI, getTransformationsForType } from '../utils/transformations';

/**
 * TransformModal Component
 * Handles parameter transformation with visualization and preview
 * 
 * @param {Object} props
 * @param {string} props.selectedParameter - Currently selected parameter
 * @param {string} props.selectedTransformation - Currently selected transformation
 * @param {string} props.newParameterName - Name for transformed parameter
 * @param {string} props.transformVisualization - Base64 image of original distribution
 * @param {string} props.transformedVisualization - Base64 image of transformed distribution
 * @param {Function} props.onClose - Callback when modal is closed
 * @param {Function} props.onParameterSelect - Callback when parameter is selected
 * @param {Function} props.onTransformationSelect - Callback when transformation is selected
 * @param {Function} props.onParameterNameChange - Callback when parameter name is changed
 * @param {Function} props.onApply - Callback when transformation is applied
 * @param {Object} props.availableParameters - Object of available parameters
 * @param {Array} props.transformedColumns - Array of already transformed column names
 */
const TransformModal = ({
  selectedParameter,
  selectedTransformation,
  newParameterName,
  transformVisualization,
  transformedVisualization,
  onClose,
  onParameterSelect,
  onTransformationSelect,
  onParameterNameChange,
  onApply,
  availableParameters,
  transformedColumns
}) => {
  // Handler for parameter selection
  const handleParameterSelect = async (parameter) => {
    try {
      const data = await fetchAPI(API_ENDPOINTS.TRANSFORM, {
        method: 'POST',
        body: JSON.stringify({
          column: parameter,
          visualization_only: true
        })
      });
      
      if (data.success) {
        onParameterSelect(parameter, data.visualization);
      }
    } catch (error) {
      console.error('Failed to get parameter visualization:', error);
    }
  };

  // Handler for transformation selection
  const handleTransformationSelect = async (transformation) => {
    if (!selectedParameter) return;

    try {
      const data = await fetchAPI(API_ENDPOINTS.TRANSFORM, {
        method: 'POST',
        body: JSON.stringify({
          column: selectedParameter,
          transformation,
          preview: true
        })
      });
      
      if (data.success) {
        // Generate default parameter name
        let defaultName;
        if (transformation === 'one_hot_encoding' && data.created_columns?.length > 0) {
          defaultName = data.created_columns[0];
        } else {
          // Create default name based on transformation type
          const transformName = TRANSFORMATIONS[transformation].name.toLowerCase().replace(/\s+/g, '_');
          defaultName = `${selectedParameter}_${transformName}`;
        }
        onTransformationSelect(transformation, data.visualization, defaultName);
      }
    } catch (error) {
      console.error('Failed to preview transformation:', error);
    }
  };

  // Handler for applying transformation
  const handleApply = async () => {
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
        // Pass created columns back to parent for proper state update
        onApply(data.visualization, data.created_columns || [newParameterName]);
      }
    } catch (error) {
      console.error('Failed to apply transformation:', error);
    }
  };

  // Get available transformations based on parameter type
  const getAvailableTransformations = () => {
    if (!selectedParameter || !availableParameters[selectedParameter]) return [];
    const paramType = availableParameters[selectedParameter].type || 'numeric';
    return getTransformationsForType(paramType);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Transform Data</h2>
        <div className="transform-form">
          {/* Parameter Selection */}
          <div className="form-group">
            <label>Select Parameter:</label>
            <select 
              value={selectedParameter}
              onChange={(e) => handleParameterSelect(e.target.value)}
            >
              <option value="">Select a parameter...</option>
              {Object.keys(availableParameters)
                .filter(col => availableParameters[col] && !transformedColumns.includes(col))
                .map(col => (
                  <option key={col} value={col}>{col}</option>
                ))
              }
            </select>
          </div>

          {/* Transformation Selection */}
          {selectedParameter && (
            <div className="form-group">
              <label>Select Transformation:</label>
              <select 
                value={selectedTransformation}
                onChange={(e) => handleTransformationSelect(e.target.value)}
              >
                <option value="">Select a transformation...</option>
                {getAvailableTransformations().map(transform => (
                  <option key={transform.id} value={transform.id}>
                    {transform.name}
                  </option>
                ))}
              </select>
              {selectedTransformation && (
                <small className="transform-description">
                  {TRANSFORMATIONS[selectedTransformation].description}
                  <br />
                  Requirements: {TRANSFORMATIONS[selectedTransformation].requirements.join(', ')}
                </small>
              )}
            </div>
          )}

          {/* Parameter Name Input */}
          {selectedParameter && selectedTransformation && (
            <div className="form-group">
              <label>New Parameter Name:</label>
              <input
                type="text"
                value={newParameterName}
                onChange={(e) => onParameterNameChange(e.target.value)}
                placeholder={`${selectedParameter}_transformed`}
              />
            </div>
          )}

          {/* Visualizations */}
          {transformVisualization && (
            <div className="visualization-container">
              <div className="visualization-box">
                <h3>Original Distribution</h3>
                <img 
                  src={`data:image/png;base64,${transformVisualization}`}
                  alt="Original Distribution"
                />
              </div>
              {transformedVisualization && (
                <div className="visualization-box">
                  <h3>Transformed Distribution</h3>
                  <img 
                    src={`data:image/png;base64,${transformedVisualization}`}
                    alt="Transformed Distribution"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="modal-buttons">
          <button className="action-button" onClick={onClose}>
            Cancel
          </button>
          {selectedParameter && selectedTransformation && (
            <button 
              className="action-button"
              onClick={handleApply}
              disabled={!newParameterName.trim()}
            >
              Apply
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransformModal;
