import React from 'react';

/**
 * Sidebar Component
 * Displays dataset information and parameter selection checkboxes
 * 
 * @param {Object} props
 * @param {Object} props.dataInfo - Dataset information (rows, columns)
 * @param {Object} props.selectedColumns - Object mapping column names to their selected state
 * @param {Array} props.transformedColumns - Array of transformed column names
 * @param {Function} props.onColumnToggle - Callback when a column is toggled
 */
const Sidebar = ({ 
  dataInfo, 
  selectedColumns, 
  transformedColumns, 
  onColumnToggle 
}) => {
  return (
    <div className="sidebar">
      {/* Dataset Information */}
      <h2>Dataset Information</h2>
      <p>Number of rows: {dataInfo.num_rows}</p>
      <p>Number of columns: {dataInfo.num_columns}</p>
      
      {/* Parameter Selection */}
      <h3>Parameters</h3>
      <div className="parameter-list">
        {Object.keys(selectedColumns).map(col => (
          <div key={col} className="column-checkbox">
            <input
              type="checkbox"
              id={col}
              checked={selectedColumns[col]}
              onChange={(e) => onColumnToggle(col, e.target.checked)}
            />
            <label htmlFor={col} className={transformedColumns.includes(col) ? 'transformed-badge' : ''}>
              {col}
            </label>
          </div>
        ))}
      </div>

      {/* Parameter Groups */}
      <div className="parameter-groups">
        <button 
          className="action-button"
          onClick={() => {
            const allSelected = Object.values(selectedColumns).every(v => v);
            const newState = !allSelected;
            Object.keys(selectedColumns).forEach(col => {
              onColumnToggle(col, newState);
            });
          }}
        >
          {Object.values(selectedColumns).every(v => v) ? 'Deselect All' : 'Select All'}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
