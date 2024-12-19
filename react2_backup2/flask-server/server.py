from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from data_processor import DataProcessor
import io

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5001"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize data processor
processor = DataProcessor()

@app.route("/test", methods=['GET'])
def test():
    """Test endpoint to verify server is running"""
    return jsonify({"status": "Server is running!"})

@app.route("/upload", methods=['POST'])
def upload_file():
    """Handle file upload and return dataset information"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
            
        if file and file.filename.endswith('.csv'):
            info = processor.load_data(file)
            return jsonify({'success': True, 'info': info})
            
        return jsonify({'success': False, 'error': 'Please upload a CSV file'}), 400
        
    except Exception as e:
        print(f"Error in upload_file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/summary", methods=['POST'])
def get_summary():
    """Generate summary statistics and visualizations"""
    try:
        data = request.get_json()
        columns = data.get('columns', [])
        
        if not columns:
            return jsonify({'success': False, 'error': 'No columns specified'}), 400
            
        summary_data = processor.get_summary(columns)
        return jsonify({'success': True, **summary_data})
        
    except Exception as e:
        print(f"Error in get_summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/transform", methods=['POST'])
def transform_data():
    """Handle data transformation requests"""
    try:
        data = request.get_json()
        column = data.get('column')
        
        if not column:
            return jsonify({'success': False, 'error': 'No column specified'}), 400
            
        # Just get distribution visualization
        if data.get('visualization_only'):
            visualization = processor.get_distribution(column)
            return jsonify({
                'success': True,
                'visualization': visualization
            })
            
        transformation = data.get('transformation')
        if not transformation:
            return jsonify({'success': False, 'error': 'No transformation specified'}), 400
            
        # Preview transformation
        if data.get('preview'):
            if transformation == 'one_hot_encoding':
                _, visualization, created_columns = processor.preview_transformation(column, transformation)
                return jsonify({
                    'success': True,
                    'visualization': visualization,
                    'created_columns': created_columns
                })
            else:
                _, visualization = processor.preview_transformation(column, transformation)
                return jsonify({
                    'success': True,
                    'visualization': visualization
                })
            
        # Apply transformation
        new_column_name = data.get('new_column_name', f"{column}_{transformation}")
        if transformation == 'one_hot_encoding':
            visualization, created_columns = processor.apply_transformation(column, transformation, new_column_name)
            return jsonify({
                'success': True,
                'visualization': visualization,
                'created_columns': created_columns
            })
        else:
            visualization, _ = processor.apply_transformation(column, transformation, new_column_name)
            return jsonify({
                'success': True,
                'visualization': visualization,
                'created_columns': [new_column_name]
            })
        
    except Exception as e:
        print(f"Error in transform_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/visualize", methods=['POST'])
def create_visualization():
    """Create custom visualization"""
    try:
        data = request.get_json()
        parameters = data.get('parameters', [])
        viz_type = data.get('type')
        
        if not parameters:
            return jsonify({'success': False, 'error': 'No parameters specified'}), 400
            
        if not viz_type:
            return jsonify({'success': False, 'error': 'No visualization type specified'}), 400
            
        visualization = processor.create_visualization(parameters, viz_type)
        return jsonify({
            'success': True,
            'visualization': visualization
        })
        
    except Exception as e:
        print(f"Error in create_visualization: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/head", methods=['GET'])
def get_head():
    """Get first 5 rows of the dataset"""
    try:
        if processor.current_df is None:
            return jsonify({'success': False, 'error': 'No data loaded'}), 400
            
        head_data = processor.current_df.head().to_dict('records')
        # Convert numpy types to native Python types
        for row in head_data:
            for key, value in row.items():
                if hasattr(value, 'item'):  # Check if value is a numpy type
                    row[key] = value.item()
                
        return jsonify({
            'success': True,
            'data': head_data
        })
        
    except Exception as e:
        print(f"Error in get_head: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/save", methods=['POST'])
def save_data():
    """Save selected columns to CSV"""
    try:
        data = request.get_json()
        columns = data.get('columns', [])
        
        if not columns:
            return jsonify({'success': False, 'error': 'No columns specified'}), 400
            
        output = processor.save_data(columns)
        
        mem = io.BytesIO()
        mem.write(output.getvalue().encode())
        mem.seek(0)
        
        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name='transformed_data.csv'
        )
        
    except Exception as e:
        print(f"Error in save_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, port=5001)
