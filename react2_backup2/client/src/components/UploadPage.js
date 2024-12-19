import React, { useState, useEffect } from 'react';
import { API_ENDPOINTS, fetchAPI } from '../utils/transformations';

/**
 * UploadPage Component
 * Handles file upload and server connection status
 * 
 * @param {Object} props
 * @param {Function} props.onUploadSuccess - Callback when file is successfully uploaded
 */
const UploadPage = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');

  // Check server connection on component mount
  useEffect(() => {
    const checkServer = async () => {
      try {
        const data = await fetchAPI(API_ENDPOINTS.TEST);
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
      const response = await fetch(API_ENDPOINTS.UPLOAD, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        onUploadSuccess(data.info);
      } else {
        setError(data.error || 'Upload failed');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(`Upload failed: ${err.message}. Make sure the server is running and accessible.`);
    }
  };

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
};

export default UploadPage;
