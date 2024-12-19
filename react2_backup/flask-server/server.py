from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
import io
import base64

app = Flask(__name__)
# Enable CORS for all routes with specific origins
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5001"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Global variables to store the dataframe and original data
current_df = None
original_df = None

@app.route("/test", methods=['GET'])
def test():
    return jsonify({"status": "Server is running!"})

@app.route("/upload", methods=['POST'])
def upload_file():
    global current_df, original_df
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
            
        if file and file.filename.endswith('.csv'):
            # Read the CSV file
            current_df = pd.read_csv(file)
            original_df = current_df.copy()  # Keep original data
            
            # Basic dataset info
            info = {
                'num_rows': len(current_df),
                'num_columns': len(current_df.columns),
                'columns': current_df.columns.tolist()
            }
            return jsonify({'success': True, 'info': info})
        return jsonify({'success': False, 'error': 'Please upload a CSV file'}), 400
    except Exception as e:
        print(f"Error in upload_file: {str(e)}")  # Server-side logging
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/summary", methods=['POST'])
def get_summary():
    if current_df is None:
        return jsonify({'success': False, 'error': 'No dataset uploaded'}), 400
    
    try:
        # Get selected columns from request
        data = request.get_json()
        columns = data.get('columns', current_df.columns.tolist())
        
        # Filter DataFrame for selected columns
        df_selected = current_df[columns]
        
        # Basic summary statistics for numeric columns only
        numeric_cols = df_selected.select_dtypes(include=[np.number]).columns
        summary = df_selected[numeric_cols].describe().to_dict()
        
        # Generate correlation matrix visualization if there are numeric columns
        corr_img_str = None
        if len(numeric_cols) > 1:
            plt.figure(figsize=(10, 8))
            sns.heatmap(df_selected[numeric_cols].corr(), annot=True, cmap='coolwarm', center=0)
            plt.title('Correlation Matrix')
            
            # Save correlation plot to bytes buffer
            corr_buf = io.BytesIO()
            plt.savefig(corr_buf, format='png', bbox_inches='tight')
            plt.close()
            corr_buf.seek(0)
            corr_img_str = base64.b64encode(corr_buf.getvalue()).decode()

        # Generate PCA plot if there are enough numeric columns
        pca_data = None
        if len(numeric_cols) > 1:
            # Standardize the features
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df_selected[numeric_cols])
            
            # Apply PCA
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(scaled_data)
            
            # Create the plot
            plt.figure(figsize=(10, 8))
            plt.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.5)
            plt.xlabel('First Principal Component')
            plt.ylabel('Second Principal Component')
            plt.title('PCA Plot of Numerical Features')
            
            # Save PCA plot to bytes buffer
            pca_buf = io.BytesIO()
            plt.savefig(pca_buf, format='png', bbox_inches='tight')
            plt.close()
            pca_buf.seek(0)
            
            pca_data = {
                'image': base64.b64encode(pca_buf.getvalue()).decode(),
                'explained_variance_ratio': pca.explained_variance_ratio_.tolist()
            }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'correlation': corr_img_str,
            'pca': pca_data
        })
    except Exception as e:
        print(f"Error in get_summary: {str(e)}")  # Server-side logging
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/transform", methods=['POST'])
def transform_data():
    global current_df
    if current_df is None:
        return jsonify({'success': False, 'error': 'No dataset uploaded'}), 400
    
    try:
        data = request.get_json()
        column = data.get('column')
        transformation = data.get('transformation')
        visualization_only = data.get('visualization_only', False)
        preview = data.get('preview', False)
        new_column_name = data.get('new_column_name')
        
        if column not in current_df.columns:
            return jsonify({'success': False, 'error': 'Column not found'}), 400
        
        # For visualization_only, just show the original distribution
        if visualization_only:
            plt.figure(figsize=(8, 6))
            if np.issubdtype(current_df[column].dtype, np.number):
                plt.hist(current_df[column].dropna(), bins=30)
                plt.title(f'Distribution: {column}')
            else:
                counts = current_df[column].value_counts()
                plt.bar(counts.index, counts.values)
                plt.title(f'Distribution: {column}')
                plt.xticks(rotation=45)
            
            # Save plot to bytes buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close()
            buf.seek(0)
            
            return jsonify({
                'success': True,
                'visualization': base64.b64encode(buf.getvalue()).decode()
            })
        
        # For preview or actual transformation
        if transformation not in ['log', 'sqrt', 'standard', 'minmax']:
            return jsonify({'success': False, 'error': 'Invalid transformation'}), 400
        
        # Calculate transformed values
        if transformation == 'log':
            if (current_df[column] <= 0).any():
                return jsonify({'success': False, 'error': 'Log transformation requires positive values'}), 400
            transformed_values = np.log(current_df[column])
        elif transformation == 'sqrt':
            if (current_df[column] < 0).any():
                return jsonify({'success': False, 'error': 'Square root transformation requires non-negative values'}), 400
            transformed_values = np.sqrt(current_df[column])
        elif transformation == 'standard':
            scaler = StandardScaler()
            transformed_values = scaler.fit_transform(current_df[[column]]).flatten()
        elif transformation == 'minmax':
            scaler = MinMaxScaler()
            transformed_values = scaler.fit_transform(current_df[[column]]).flatten()
        
        # Create visualization
        plt.figure(figsize=(8, 6))
        plt.hist(transformed_values.dropna(), bins=30)
        plt.title(f'Preview of {transformation} transformation')
        
        # Save plot to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        # If this is just a preview, don't modify the dataframe
        if preview:
            return jsonify({
                'success': True,
                'visualization': base64.b64encode(buf.getvalue()).decode()
            })
        
        # Otherwise, apply the transformation
        if new_column_name:
            current_df[new_column_name] = transformed_values
        else:
            current_df[f"{column}_{transformation}"] = transformed_values
        
        return jsonify({
            'success': True,
            'visualization': base64.b64encode(buf.getvalue()).decode()
        })
        
    except Exception as e:
        print(f"Error in transform_data: {str(e)}")  # Server-side logging
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/save", methods=['POST'])
def save_data():
    if current_df is None:
        return jsonify({'success': False, 'error': 'No dataset uploaded'}), 400
    
    try:
        data = request.get_json()
        columns = data.get('columns', current_df.columns.tolist())
        
        # Filter DataFrame for selected columns
        df_selected = current_df[columns]
        
        # Save to a temporary file
        output = io.StringIO()
        df_selected.to_csv(output, index=False)
        
        # Convert to bytes for download
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
        print(f"Error in save_data: {str(e)}")  # Server-side logging
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask server...")  # Server startup logging
    app.run(debug=True, port=5001)
