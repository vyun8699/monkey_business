# Data Analysis Platform

A modular platform for data analysis and transformation.

## Structure

### Frontend (React)

```
client/src/
├── components/
│   ├── UploadPage.js           # File upload and server connection
│   ├── Sidebar.js              # Dataset info and parameter selection
│   ├── DataSummary.js          # Core visualization logic and state management
│   ├── SummaryTable.js         # Dashboard table with statistics
│   ├── VisualizationControls.js # Custom visualization parameter controls
│   ├── HeadDataTable.js        # Data preview table component
│   ├── VisualizationButtons.js # Visualization type selection
│   └── TransformModal.js       # Parameter transformation interface
├── utils/
│   └── transformations.js      # Shared utilities and configurations
├── App.js                      # Main application and state management
└── App.css                     # Styles
```

### Backend (Flask)

```
flask-server/
├── server.py          # API endpoints and request handling
└── data_processor.py  # Data processing and visualization logic
```

## Features

### Data Summary
- Basic statistics (mean, std, min, max, quartiles)
- Null value counts for each column
- Data preview (first 5 rows)
- Correlation matrix
- PCA visualization
- Custom visualizations:
  * Histogram
  * Box Plot
  * Violin Plot
  * Bar Chart
  * Pie Chart
  * Scatter Plot
  * Line Plot

### Data Transformations

#### Numeric Data
- Log transformation (requires positive values)
- Square root transformation (requires non-negative values)
- Standardization (z-score)
- Min-Max scaling

#### Categorical Data
- Label encoding
- One-hot encoding (creates binary columns for each category)

#### Null Handling
- Drop null values
- Fill with mean (numeric only)
- Fill with median (numeric only)

## API Endpoints

- `GET /test` - Check server status
- `POST /upload` - Upload CSV file
- `POST /summary` - Get summary statistics and visualizations
- `POST /transform` - Transform parameters
- `POST /visualize` - Create custom visualizations
- `GET /head` - Get first 5 rows of data
- `POST /save` - Save selected parameters to CSV

## Data Flow

1. User uploads CSV file
2. Frontend displays dataset information and summary statistics
3. User can:
   - View different visualizations using the visualization buttons
   - Select parameters for transformation
   - Choose appropriate transformations based on data type
   - Preview transformations before applying
   - Create custom visualizations
4. Backend processes requests and returns results
5. Frontend updates visualizations and state

## Best Practices

1. **Data Type Handling**
   - Transformations are filtered based on data type
   - Proper handling of numeric and categorical data
   - Appropriate visualizations for each data type

2. **Visualization**
   - Consistent styling across all plots
   - Dark theme with white text
   - Clear titles and labels
   - Interactive visualization selection

3. **Error Handling**
   - Comprehensive error messages
   - Data validation at both frontend and backend
   - Proper cleanup of matplotlib figures

4. **Performance**
   - Efficient data processing
   - Proper memory management
   - JSON serialization of numpy types

## Adding New Features

### Adding New Transformations

1. Add the transformation to `transformations.js`:
```javascript
export const TRANSFORMATIONS = {
  newTransform: {
    id: 'newTransform',
    name: 'New Transform',
    description: 'Description',
    requirements: ['requirements'],
    dataTypes: ['numeric' or 'categorical'],
    defaultName: (param) => `${param}_newtransform`
  }
};
```

2. Implement in `data_processor.py`:
```python
def _apply_transformation(self, column, transformation):
    elif transformation == 'newTransform':
        # Implement transformation logic
        return transformed_values
```

### Adding New Visualizations

1. Add to VISUALIZATION_TYPES in `transformations.js`:
```javascript
export const VISUALIZATION_TYPES = {
  NUMERIC: [
    { id: 'new_viz', name: 'New Visualization' }
  ]
};
```

2. Implement in `data_processor.py`:
```python
def create_visualization(self, parameters, viz_type):
    elif viz_type == 'new_viz':
        # Implement visualization logic
```

## Error Messages

Common error messages and their solutions:

1. "Log transformation requires positive values"
   - Ensure data contains only positive values

2. "Square root transformation requires non-negative values"
   - Ensure data contains no negative values

3. "Invalid transformation"
   - Check if transformation is supported for data type

4. "No data loaded"
   - Upload a CSV file before attempting operations

5. "No columns specified"
   - Select at least one parameter for operation
