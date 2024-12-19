import React from 'react';

const VisualizationButtons = ({ 
  selectedVisualization, 
  setSelectedVisualization,
  fetchHeadData,
  headData,
  headError
}) => {
  return (
    <div className="visualization-buttons">
      <button 
        className={`viz-button ${selectedVisualization === 'summary' ? 'active' : ''}`}
        onClick={() => setSelectedVisualization('summary')}
      >
        Dashboard
      </button>
      <button 
        className={`viz-button ${selectedVisualization === 'correlation' ? 'active' : ''}`}
        onClick={() => setSelectedVisualization('correlation')}
      >
        Correlation Matrix
      </button>
      <button 
        className={`viz-button ${selectedVisualization === 'pca' ? 'active' : ''}`}
        onClick={() => setSelectedVisualization('pca')}
      >
        PCA
      </button>
      <button 
        className={`viz-button ${selectedVisualization === 'custom' ? 'active' : ''}`}
        onClick={() => setSelectedVisualization('custom')}
      >
        Custom Visualization
      </button>
      <button 
        className={`viz-button ${selectedVisualization === 'head' ? 'active' : ''}`}
        onClick={() => {
          setSelectedVisualization('head');
          if (!headData && !headError) {
            fetchHeadData();
          }
        }}
      >
        Head
      </button>
      <button 
        className={`viz-button ${selectedVisualization === 'log' ? 'active' : ''}`}
        onClick={() => setSelectedVisualization('log')}
      >
        Log
      </button>
    </div>
  );
};

export default VisualizationButtons;
