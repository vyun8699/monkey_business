import React from 'react';

const HeadDataTable = ({ headData, headError }) => {
  if (headError) {
    return <p className="error-message">{headError}</p>;
  }

  if (!headData) {
    return <p>Loading data preview...</p>;
  }

  return (
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
                <td key={j}>{value !== null ? value : ''}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default HeadDataTable;
