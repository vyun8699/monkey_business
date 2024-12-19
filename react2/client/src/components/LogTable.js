import React from 'react';

const LogTable = ({ logs }) => {
  return (
    <div className="log-table">
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Action</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {logs && logs.map((log, index) => (
            <tr key={index}>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
              <td>{log.action}</td>
              <td>{log.details}</td>
            </tr>
          ))}
          {(!logs || logs.length === 0) && (
            <tr>
              <td colSpan="3" className="no-data">No changes logged yet</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default LogTable;
