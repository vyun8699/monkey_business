from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to Python path to import functions module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from functions import transform_column, clean_nan_values, calculate_histogram, analyze_nulls

import base64
import io
import json

app = Flask(__name__)
CORS(app)

# Global variable to store the current DataFrame
current_df = None

def truncate_text(text, max_length=100):
    """Truncate text to specified length and add ellipsis if needed"""
    if isinstance(text, str) and len(text) > max_length:
        return text[:max_length] + '...'
    return text

def get_unique_values_count(df, column):
    """Get count of unique values in a column"""
    return df[column].nunique()

def clean_and_truncate_data(df):
    """Clean NaN values and truncate long text in DataFrame"""
    df_dict = df.to_dict('records')
    cleaned_data = []
    for row in df_dict:
        cleaned_row = {}
        for k, v in row.items():
            if pd.isna(v) or (isinstance(v, float) and np.isnan(v)):
                cleaned_row[k] = None
            else:
                # Convert numpy types to Python native types
                if isinstance(v, (np.int64, np.int32, np.int16, np.int8)):
                    cleaned_row[k] = int(v)
                elif isinstance(v, (np.float64, np.float32)):
                    cleaned_row[k] = float(v)
                else:
                    cleaned_row[k] = truncate_text(v)
        cleaned_data.append(cleaned_row)
    return cleaned_data

def prepare_column_data(df, column):
    """Prepare column data for preview, ensuring numeric values are properly handled"""
    try:
        # For numeric columns, calculate histogram data
        if pd.api.types.is_numeric_dtype(df[column]):
            return calculate_histogram(df[column])
        
        # For categorical data, count occurrences
        value_counts = df[column].value_counts().head(15)
        total_count = len(df[column].dropna())
        
        data = [
            {
                "category": str(category),
                "count": int(count),
                "percentage": float(count / total_count * 100)
            }
            for category, count in value_counts.items()
        ]
        
        # Add "Others" category if there are more categories
        if len(df[column].unique()) > 15:
            others_count = total_count - sum(value_counts)
            if others_count > 0:
                data.append({
                    "category": "Others",
                    "count": int(others_count),
                    "percentage": float(others_count / total_count * 100)
                })
        
        return data
    except Exception as e:
        print(f"Error preparing column data: {str(e)}")
        return []

@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        global current_df
        content = request.json.get("file")
        
        # Extract the base64 content
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        
        # Read the CSV file
        current_df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Get column information
        numeric_columns = current_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = current_df.select_dtypes(exclude=[np.number]).columns.tolist()
        
        # Get unique value counts for categorical columns
        categorical_info = {
            col: get_unique_values_count(current_df, col)
            for col in categorical_columns
        }

        # Get null value analysis
        null_info = analyze_nulls(current_df)
        
        return jsonify({
            "success": True,
            "info": {
                "rows": len(current_df),
                "columns": current_df.columns.tolist(),
                "numeric_columns": numeric_columns,
                "categorical_columns": categorical_columns,
                "categorical_info": categorical_info,
                "null_info": null_info
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/preview", methods=["GET"])
def get_preview():
    try:
        if current_df is None:
            return jsonify({"error": "No data uploaded"})
        
        preview_data = clean_and_truncate_data(current_df.head())
        return jsonify({
            "data": preview_data,
            "columns": current_df.columns.tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/transformations", methods=["GET"])
def get_transformations():
    return jsonify({
        "numeric": {
            "standardization": "Standardization (z-score)",
            "minmax": "Min-Max Scaling",
            "log": "Log Transform",
            "remove_nulls": "Remove Null Values"
        },
        "categorical": {
            "label": "Label Encoding",
            "onehot": "One-Hot Encoding (max 10 categories)",
            "remove_nulls": "Remove Null Values"
        }
    })

@app.route("/api/preview_column", methods=["POST"])
def preview_column():
    try:
        data = request.json
        column = data.get("column")
        
        if current_df is None:
            return jsonify({"error": "No data uploaded"})
        
        # Create copies of the data
        preview_df = current_df.head().copy()
        full_df = current_df.copy()
        
        # Get the data for the selected column
        original_preview = clean_and_truncate_data(preview_df[[column]])
        original_full = prepare_column_data(full_df, column)
        
        return jsonify({
            "success": True,
            "preview": {
                "original": {
                    "preview": original_preview,
                    "full": original_full
                },
                "transformed": {
                    "preview": original_preview,  # Same as original since no transformation
                    "full": original_full  # Same as original since no transformation
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/preview_transform", methods=["POST"])
def preview_transform():
    try:
        data = request.json
        column = data.get("column")
        transformation = data.get("transformation")
        
        if current_df is None:
            return jsonify({"error": "No data uploaded"})
        
        # If no transformation is specified, delegate to preview_column
        if not transformation:
            return preview_column()
        
        # Check for one-hot encoding limitations
        if transformation == "onehot":
            unique_count = get_unique_values_count(current_df, column)
            if unique_count > 10:
                return jsonify({
                    "success": False,
                    "error": f"One-hot encoding is limited to columns with 10 or fewer unique values. This column has {unique_count} unique values."
                })
        
        # Create a copy of the full dataset for visualization
        full_df = current_df.copy()
        # Create a copy of the preview for the table view
        preview_df = current_df.head().copy()
        transformed_preview = preview_df.copy()
        transformed_full = full_df.copy()
        
        # Map frontend transformation names to backend names
        transform_map = {
            "standardization": "standardized",
            "minmax": "minmax",
            "log": "log",
            "label": "label",
            "onehot": "onehot",
            "remove_nulls": "remove_nulls"
        }
        
        # Transform both preview and full datasets
        transformed_preview, error = transform_column(transformed_preview, column, transform_map[transformation])
        if error:
            return jsonify({"success": False, "error": error})
            
        transformed_full, _ = transform_column(transformed_full, column, transform_map[transformation])
        
        # For the preview table, we only want to show the original column and its transformed version
        original_preview = clean_and_truncate_data(preview_df[[column]])
        original_full = prepare_column_data(full_df, column)
        
        # Get the transformed column name based on transformation type
        if transformation == "onehot":
            # For onehot, we need all the new columns that start with the original column name
            transformed_cols = [col for col in transformed_preview.columns if col.startswith(f"{column}_")]
            transformed_preview_data = clean_and_truncate_data(transformed_preview[transformed_cols])
            transformed_full_data = clean_and_truncate_data(transformed_full[transformed_cols])
        else:
            transformed_col = f"{column}_{transform_map[transformation]}"
            transformed_preview_data = clean_and_truncate_data(transformed_preview[[transformed_col]])
            transformed_full_data = prepare_column_data(transformed_full, transformed_col)
        
        return jsonify({
            "success": True,
            "preview": {
                "original": {
                    "preview": original_preview,
                    "full": original_full
                },
                "transformed": {
                    "preview": transformed_preview_data,
                    "full": transformed_full_data
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/transform", methods=["POST"])
def transform():
    try:
        global current_df
        data = request.json
        column = data.get("column")
        transformation = data.get("transformation")
        
        if current_df is None:
            return jsonify({"error": "No data uploaded"})
        
        # Check for one-hot encoding limitations
        if transformation == "onehot":
            unique_count = get_unique_values_count(current_df, column)
            if unique_count > 10:
                return jsonify({
                    "success": False,
                    "error": f"One-hot encoding is limited to columns with 10 or fewer unique values. This column has {unique_count} unique values."
                })
        
        # Map frontend transformation names to backend names
        transform_map = {
            "standardization": "standardized",
            "minmax": "minmax",
            "log": "log",
            "label": "label",
            "onehot": "onehot",
            "remove_nulls": "remove_nulls"
        }
        
        current_df, error = transform_column(current_df, column, transform_map[transformation])
        if error:
            return jsonify({"success": False, "error": error})
        
        # Get updated column information
        numeric_columns = current_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = current_df.select_dtypes(exclude=[np.number]).columns.tolist()
        categorical_info = {
            col: get_unique_values_count(current_df, col)
            for col in categorical_columns
        }

        # Get updated null analysis
        null_info = analyze_nulls(current_df)
        
        preview_data = clean_and_truncate_data(current_df.head())
        return jsonify({
            "success": True,
            "preview": {
                "data": preview_data,
                "columns": current_df.columns.tolist()
            },
            "info": {
                "rows": len(current_df),
                "columns": current_df.columns.tolist(),
                "numeric_columns": numeric_columns,
                "categorical_columns": categorical_columns,
                "categorical_info": categorical_info,
                "null_info": null_info
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/save", methods=["POST"])
def save_csv():
    try:
        data = request.json
        columns = data.get("columns", [])
        
        if current_df is None:
            return jsonify({"error": "No data uploaded"})
        
        if not columns:
            return jsonify({"error": "No columns selected"})
        
        # Create a new DataFrame with only selected columns
        selected_df = current_df[columns]
        
        # Save to a buffer
        buffer = io.BytesIO()
        selected_df.to_csv(buffer, index=False)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name='transformed_data.csv'
        )
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(port=5001, debug=True)
