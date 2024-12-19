import React from 'react';
import { formatNumber } from '../utils/transformations';

const SummaryTable = ({ summary, sortConfig, handleSort, availableParameters }) => {
  const renderValue = (value) => {
    if (value === null || value === undefined || value === '' || value === 'N/A') {
      return <span className="na-value">N/A</span>;
    }
    return value;
  };

  const getSortedData = () => {
    if (!sortConfig.key) return Object.entries(summary);

    return [...Object.entries(summary)].sort((a, b) => {
      let aValue, bValue;

      if (sortConfig.key === 'parameter') {
        aValue = a[0];
        bValue = b[0];
      } else if (sortConfig.key === 'type') {
        aValue = availableParameters[a[0]]?.type || '';
        bValue = availableParameters[b[0]]?.type || '';
      } else {
        aValue = a[1][sortConfig.key];
        bValue = b[1][sortConfig.key];
      }
      
      // Handle empty/null values
      if (aValue === null || aValue === undefined || aValue === '') return 1;
      if (bValue === null || bValue === undefined || bValue === '') return -1;
      if (aValue === bValue) return 0;

      // For numeric values
      if (!isNaN(aValue) && !isNaN(bValue)) {
        const numA = Number(aValue);
        const numB = Number(bValue);
        return sortConfig.direction === 'ascending' ? numA - numB : numB - numA;
      }

      // For non-numeric values, use case-insensitive string comparison
      const strA = String(aValue).toLowerCase();
      const strB = String(bValue).toLowerCase();
      return sortConfig.direction === 'ascending' 
        ? strA.localeCompare(strB)
        : strB.localeCompare(strA);
    });
  };

  return (
    <div className="summary-table">
      <table>
        <thead>
          <tr>
            <th onClick={() => handleSort('parameter')} className="sortable">
              Parameter {sortConfig.key === 'parameter' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('type')} className="sortable">
              Type {sortConfig.key === 'type' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('count')} className="sortable">
              Count {sortConfig.key === 'count' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('unique_count')} className="sortable">
              Unique Count {sortConfig.key === 'unique_count' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('null_count')} className="sortable">
              Null Count {sortConfig.key === 'null_count' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('mean')} className="sortable">
              Mean {sortConfig.key === 'mean' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('std')} className="sortable">
              Std {sortConfig.key === 'std' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('min')} className="sortable">
              Min {sortConfig.key === 'min' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('25%')} className="sortable">
              25% {sortConfig.key === '25%' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('50%')} className="sortable">
              50% {sortConfig.key === '50%' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('75%')} className="sortable">
              75% {sortConfig.key === '75%' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
            <th onClick={() => handleSort('max')} className="sortable">
              Max {sortConfig.key === 'max' && <span>{sortConfig.direction === 'ascending' ? '↑' : '↓'}</span>}
            </th>
          </tr>
        </thead>
        <tbody>
          {getSortedData()
            .filter(([col, _]) => availableParameters[col]?.selected)
            .map(([col, stats]) => {
              const isTransformed = availableParameters[col]?.isTransformed;
              const type = availableParameters[col]?.type;
              const nullCount = stats.null_count || 0;
              return (
                <tr key={col}>
                  <td className={isTransformed ? 'transformed-parameter' : ''}>{col}</td>
                  <td className={`type-${type}`}>{renderValue(type)}</td>
                  <td>{renderValue(stats.count)}</td>
                  <td>{renderValue(stats.unique_count)}</td>
                  <td className={nullCount > 0 ? 'has-nulls' : 'na-value'}>{nullCount}</td>
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
};

export default SummaryTable;
