import React, { useState } from 'react';

const SavePrompt = ({ onSave, onCancel }) => {
  const [fileName, setFileName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (fileName.trim()) {
      onSave(fileName.trim());
    }
  };

  return (
    <div className="upload-section">
      <form onSubmit={handleSubmit} className="save-form">
        <h2>Save Dataset</h2>
        <input
          type="text"
          value={fileName}
          onChange={(e) => setFileName(e.target.value)}
          placeholder="Enter file name"
          className="file-input"
          autoFocus
        />
        <div className="button-group">
          <button type="submit" className="upload-button">
            Save
          </button>
          <button type="button" className="upload-button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default SavePrompt;
