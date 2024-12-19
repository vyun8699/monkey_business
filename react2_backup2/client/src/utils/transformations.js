/**
 * Available data transformations configuration
 * Each transformation has:
 * - id: unique identifier
 * - name: display name
 * - description: explanation of the transformation
 * - requirements: array of requirements that data must meet
 * - dataTypes: array of compatible data types
 * - defaultName: function to generate default parameter name
 */
export const TRANSFORMATIONS = {
  // Numeric Transformations
  log: {
    id: 'log',
    name: 'Log Transform',
    description: 'Natural logarithm transformation. Useful for right-skewed data.',
    requirements: ['positive values'],
    dataTypes: ['numeric'],
    defaultName: (param) => `${param}_log`
  },
  sqrt: {
    id: 'sqrt',
    name: 'Square Root',
    description: 'Square root transformation. Useful for right-skewed data, less extreme than log.',
    requirements: ['non-negative values'],
    dataTypes: ['numeric'],
    defaultName: (param) => `${param}_sqrt`
  },
  standard: {
    id: 'standard',
    name: 'Standardization',
    description: 'Standardize data to have mean=0 and std=1.',
    requirements: ['numeric values'],
    dataTypes: ['numeric'],
    defaultName: (param) => `${param}_standardized`
  },
  minmax: {
    id: 'minmax',
    name: 'Min-Max Scaling',
    description: 'Scale data to range [0,1].',
    requirements: ['numeric values'],
    dataTypes: ['numeric'],
    defaultName: (param) => `${param}_scaled`
  },
  // Null Handling
  dropna: {
    id: 'dropna',
    name: 'Drop Null Values',
    description: 'Remove rows with null values in selected column.',
    requirements: ['any data type'],
    dataTypes: ['numeric', 'categorical'],
    defaultName: (param) => `${param}_cleaned`
  },
  fillna_mean: {
    id: 'fillna_mean',
    name: 'Fill Nulls with Mean',
    description: 'Replace null values with column mean.',
    requirements: ['numeric values'],
    dataTypes: ['numeric'],
    defaultName: (param) => `${param}_filled_mean`
  },
  fillna_median: {
    id: 'fillna_median',
    name: 'Fill Nulls with Median',
    description: 'Replace null values with column median.',
    requirements: ['numeric values'],
    dataTypes: ['numeric'],
    defaultName: (param) => `${param}_filled_median`
  },
  // Categorical Transformations
  label_encoding: {
    id: 'label_encoding',
    name: 'Label Encoding',
    description: 'Convert categorical values to numeric labels.',
    requirements: ['categorical values'],
    dataTypes: ['categorical'],
    defaultName: (param) => `${param}_encoded`
  },
  one_hot_encoding: {
    id: 'one_hot_encoding',
    name: 'One-Hot Encoding',
    description: 'Create binary columns for each category.',
    requirements: ['categorical values'],
    dataTypes: ['categorical'],
    defaultName: (param) => `${param}_onehot`
  }
};

/**
 * Available visualization types
 */
export const VISUALIZATION_TYPES = {
  NUMERIC: [
    { id: 'histogram', name: 'Histogram' },
    { id: 'box', name: 'Box Plot' },
    { id: 'violin', name: 'Violin Plot' }
  ],
  CATEGORICAL: [
    { id: 'bar', name: 'Bar Chart' },
    { id: 'pie', name: 'Pie Chart' }
  ],
  RELATIONSHIP: [
    { id: 'scatter', name: 'Scatter Plot' },
    { id: 'line', name: 'Line Plot' }
  ]
};

/**
 * Get available transformations based on data type
 * @param {string} dataType - 'numeric' or 'categorical'
 * @returns {Array} Array of available transformations
 */
export const getTransformationsForType = (dataType) => {
  return Object.values(TRANSFORMATIONS).filter(t => 
    t.dataTypes.includes(dataType)
  );
};

/**
 * Get available visualizations based on data type and number of parameters
 * @param {string} dataType - 'numeric' or 'categorical'
 * @param {number} paramCount - Number of parameters selected
 * @returns {Array} Array of available visualization types
 */
export const getVisualizationsForType = (dataType, paramCount = 1) => {
  let types = [];
  
  if (paramCount === 1) {
    if (dataType === 'numeric') {
      types = [...VISUALIZATION_TYPES.NUMERIC];
    } else if (dataType === 'categorical') {
      types = [...VISUALIZATION_TYPES.CATEGORICAL];
    }
  } else if (paramCount === 2) {
    types = [...VISUALIZATION_TYPES.RELATIONSHIP];
  }
  
  return types;
};

/**
 * API endpoints for data operations
 */
export const API_ENDPOINTS = {
  TEST: 'http://localhost:5001/test',
  UPLOAD: 'http://localhost:5001/upload',
  SUMMARY: 'http://localhost:5001/summary',
  TRANSFORM: 'http://localhost:5001/transform',
  SAVE: 'http://localhost:5001/save',
  VISUALIZE: 'http://localhost:5001/visualize',
  HEAD: 'http://localhost:5001/head'  // Added HEAD endpoint
};

/**
 * Utility function to make API requests
 */
export const fetchAPI = async (endpoint, options = {}) => {
  try {
    const response = await fetch(endpoint, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

/**
 * Format numeric value with specified precision
 */
export const formatNumber = (value, precision = 2) => {
  return value?.toFixed(precision) ?? 'N/A';
};
