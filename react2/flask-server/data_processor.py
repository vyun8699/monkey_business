import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
import seaborn as sns
from sklearn.decomposition import PCA
import io
import base64
import json
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import psutil
import os
import logging
import warnings

# Ignore matplotlib font warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for server deployment
MAX_MEMORY_PERCENT = 80  # Maximum memory usage percentage
MAX_FILE_SIZE_MB = 100   # Maximum file size in MB
CHUNK_SIZE = 10000       # Number of rows to process at once
# Adjust worker count based on available server resources
N_WORKERS = min(4, max(1, multiprocessing.cpu_count() - 1))  # Cap at 4 workers, leave 1 CPU free

class DataProcessor:
    def __init__(self):
        self.current_df = None
        self.original_df = None
        plt.style.use('dark_background')

    def _check_memory_usage(self):
        """Check if memory usage is within limits"""
        memory_percent = psutil.Process(os.getpid()).memory_percent()
        if memory_percent > MAX_MEMORY_PERCENT:
            raise MemoryError(f"Memory usage ({memory_percent:.1f}%) exceeds limit ({MAX_MEMORY_PERCENT}%)")

    def _check_file_size(self, file):
        """Check if file size is within limits"""
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"File size ({size_mb:.1f}MB) exceeds limit ({MAX_FILE_SIZE_MB}MB)")

    def load_data(self, file):
        """Load data from CSV file and determine column types"""
        try:
            # Check file size
            self._check_file_size(file)
            
            # Read CSV in chunks if it's large
            chunks = []
            for chunk in pd.read_csv(file, chunksize=CHUNK_SIZE):
                self._check_memory_usage()  # Check memory usage during loading
                chunks.append(chunk)
            self.current_df = pd.concat(chunks, ignore_index=True)
            
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            raise ValueError(f"Invalid CSV file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading file: {str(e)}")
            
        self.original_df = self.current_df.copy()
        
        # Determine column types
        column_types = {}
        for col in self.current_df.columns:
            if pd.api.types.is_numeric_dtype(self.current_df[col]):
                column_types[col] = 'numeric'
            else:
                column_types[col] = 'categorical'
        
        return {
            'num_rows': int(len(self.current_df)),
            'num_columns': int(len(self.current_df.columns)),
            'columns': self.current_df.columns.tolist(),
            'column_types': column_types
        }

    def get_distribution(self, column):
        """Generate distribution plot for a column"""
        self._check_memory_usage()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#282c34')
        ax.set_facecolor('#282c34')
        
        try:
            if pd.api.types.is_numeric_dtype(self.current_df[column]):
                ax.hist(self.current_df[column].dropna(), bins=30, color='#61dafb', alpha=0.7)
            else:
                # For categorical data, limit to top 50 categories for visualization
                counts = self.current_df[column].value_counts().head(50)
                ax.bar(counts.index.astype(str), counts.values, color='#61dafb', alpha=0.7)
                plt.xticks(rotation=45)
            
            ax.set_title(f'Distribution: {column}', color='white', pad=20)
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
            
            return self._fig_to_base64(fig)
        finally:
            plt.close(fig)

    def get_summary(self, columns):
        """Generate summary statistics including null counts"""
        self._check_memory_usage()
        
        df_selected = self.current_df[columns]
        
        # Get numeric columns
        numeric_cols = df_selected.select_dtypes(include=[np.number]).columns
        
        # Basic summary statistics with null counts
        summary = {}
        for col in df_selected.columns:
            if col in numeric_cols:
                # Convert numpy types to Python native types
                stats = df_selected[col].describe().to_dict()
                stats = {k: float(v) if isinstance(v, np.floating) else int(v) 
                        for k, v in stats.items()}
                stats['null_count'] = int(df_selected[col].isna().sum())
                summary[col] = stats
            else:
                # For categorical columns, include count and null count
                stats = {
                    'count': int(len(df_selected[col])),
                    'null_count': int(df_selected[col].isna().sum()),
                    'unique_count': int(df_selected[col].nunique())
                }
                summary[col] = stats
        
        # Generate correlation matrix visualization
        corr_img_str = None
        if len(numeric_cols) > 1:
            # Fill NaN values with mean for correlation matrix
            df_corr = df_selected[numeric_cols].fillna(df_selected[numeric_cols].mean())
            
            fig, ax = plt.subplots(figsize=(8, 6))
            fig.patch.set_facecolor('#282c34')
            ax.set_facecolor('#282c34')
            
            sns.heatmap(df_corr.corr(), 
                       annot=True, 
                       cmap='coolwarm', 
                       center=0,
                       ax=ax,
                       cbar_kws={'label': 'Correlation'})
            
            plt.title('Correlation Matrix', color='white', pad=20)
            ax.tick_params(colors='white')
            
            corr_img_str = self._fig_to_base64(fig)
            plt.close(fig)

        # Generate PCA plot
        pca_data = None
        if len(numeric_cols) > 1:
            # Fill NaN values with mean before scaling and PCA
            df_pca = df_selected[numeric_cols].fillna(df_selected[numeric_cols].mean())
            
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df_pca)
            
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(scaled_data)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            fig.patch.set_facecolor('#282c34')
            ax.set_facecolor('#282c34')
            
            # Limit points for visualization if dataset is large
            max_points = 5000
            if len(pca_result) > max_points:
                indices = np.random.choice(len(pca_result), max_points, replace=False)
                scatter_data = pca_result[indices]
            else:
                scatter_data = pca_result
            
            scatter = ax.scatter(scatter_data[:, 0], scatter_data[:, 1], alpha=0.5, c='#61dafb')
            ax.set_xlabel('First Principal Component', color='white')
            ax.set_ylabel('Second Principal Component', color='white')
            ax.set_title('PCA Plot of Numerical Features', color='white', pad=20)
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            
            pca_data = {
                'image': self._fig_to_base64(fig),
                'explained_variance_ratio': [float(x) for x in pca.explained_variance_ratio_]
            }
            plt.close(fig)
        
        return {
            'summary': summary,
            'correlation': corr_img_str,
            'pca': pca_data
        }

    def _process_chunk(self, chunk, column, transformation):
        """Process a chunk of data for transformations"""
        if transformation == 'log':
            if (chunk <= 0).any():
                raise ValueError('Log transformation requires positive values')
            return np.log(chunk)
            
        elif transformation == 'sqrt':
            if (chunk < 0).any():
                raise ValueError('Square root transformation requires non-negative values')
            return np.sqrt(chunk)
            
        elif transformation == 'standard':
            scaler = StandardScaler()
            return pd.Series(scaler.fit_transform(chunk.values.reshape(-1, 1)).flatten(), index=chunk.index)
            
        elif transformation == 'minmax':
            scaler = MinMaxScaler()
            return pd.Series(scaler.fit_transform(chunk.values.reshape(-1, 1)).flatten(), index=chunk.index)
            
        elif transformation == 'label_encoding':
            le = LabelEncoder()
            return pd.Series(le.fit_transform(chunk.astype(str)), index=chunk.index)
            
        return chunk

    def _apply_transformation(self, column, transformation):
        """Apply specified transformation to column"""
        # Ensure we're working with a pandas Series
        if isinstance(column, str):
            data = self.current_df[column]
        elif isinstance(column, np.ndarray):
            data = pd.Series(column)
        else:
            data = column

        try:
            if transformation == 'dropna':
                # Get indices of non-null values in the column
                valid_indices = data[~data.isna()].index
                # Update the entire DataFrame to keep only rows with non-null values in this column
                self.current_df = self.current_df.loc[valid_indices]
                # Return the cleaned column
                return self.current_df[column] if isinstance(column, str) else data[valid_indices]
                
            elif transformation == 'fillna_mean':
                return data.fillna(data.mean())
                
            elif transformation == 'fillna_median':
                return data.fillna(data.median())
                
            elif transformation == 'one_hot_encoding':
                # Get unique categories (excluding NA/null values)
                categories = data.dropna().unique()
                
                # Create DataFrame with columns for each category
                result = pd.DataFrame(index=data.index)
                created_columns = []  # Track created column names
                for category in categories:
                    col_name = f"{column}_{category}" if isinstance(column, str) else f"col_{category}"
                    result[col_name] = (data == category).astype(int)
                    created_columns.append(col_name)
                
                # Add created column names as metadata
                result.attrs['created_columns'] = created_columns
                return result
            
            # For other transformations, process in chunks if data is large
            if len(data) > CHUNK_SIZE:
                chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
                with ThreadPoolExecutor(max_workers=N_WORKERS) as executor:
                    transformed_chunks = list(executor.map(
                        lambda chunk: self._process_chunk(chunk, column, transformation),
                        chunks
                    ))
                return pd.concat(transformed_chunks)
            else:
                return self._process_chunk(data, column, transformation)
                
        except Exception as e:
            raise Exception(f"Error in transformation '{transformation}': {str(e)}")

    def preview_transformation(self, column, transformation):
        """Preview transformation result without applying it"""
        transformed_values = self._apply_transformation(column, transformation)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#282c34')
        ax.set_facecolor('#282c34')
        
        if isinstance(transformed_values, pd.DataFrame):  # For one-hot encoding
            bar_width = 0.8 / len(transformed_values.columns)
            for i, col in enumerate(transformed_values.columns):
                x = np.arange(2) + i * bar_width
                counts = transformed_values[col].value_counts()
                ax.bar(x, [counts.get(0, 0), counts.get(1, 0)], 
                      width=bar_width, alpha=0.7, label=col.split('_')[-1])
            ax.set_xticks(np.arange(2) + (bar_width * (len(transformed_values.columns) - 1) / 2))
            ax.set_xticklabels(['0', '1'])
            ax.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            if pd.api.types.is_numeric_dtype(transformed_values):
                ax.hist(transformed_values.dropna(), bins=30, color='#61dafb', alpha=0.7)
            else:
                counts = transformed_values.value_counts()
                ax.bar(counts.index.astype(str), counts.values, color='#61dafb', alpha=0.7)
                plt.xticks(rotation=45)
        
        ax.set_title(f'Preview of {transformation} transformation', color='white', pad=20)
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        
        img_str = self._fig_to_base64(fig)
        plt.close(fig)
        
        # For one-hot encoding, include created column names in the response
        if isinstance(transformed_values, pd.DataFrame) and hasattr(transformed_values, 'attrs'):
            return transformed_values, img_str, transformed_values.attrs.get('created_columns', [])
        return transformed_values, img_str

    def apply_transformation(self, column, transformation, new_column_name):
        """Apply transformation and add as new column"""
        transformed_values = self._apply_transformation(column, transformation)
        created_columns = []
        
        if isinstance(transformed_values, pd.DataFrame):  # For one-hot encoding
            for col in transformed_values.columns:
                self.current_df[col] = transformed_values[col]
                created_columns.append(col)
        else:
            self.current_df[new_column_name] = transformed_values
            created_columns.append(new_column_name)
        
        # Create visualization
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#282c34')
        ax.set_facecolor('#282c34')
        
        if isinstance(transformed_values, pd.DataFrame):  # For one-hot encoding
            bar_width = 0.8 / len(transformed_values.columns)
            for i, col in enumerate(transformed_values.columns):
                x = np.arange(2) + i * bar_width
                counts = transformed_values[col].value_counts()
                ax.bar(x, [counts.get(0, 0), counts.get(1, 0)], 
                      width=bar_width, alpha=0.7, label=col.split('_')[-1])
            ax.set_xticks(np.arange(2) + (bar_width * (len(transformed_values.columns) - 1) / 2))
            ax.set_xticklabels(['0', '1'])
            ax.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            if pd.api.types.is_numeric_dtype(transformed_values):
                ax.hist(transformed_values.dropna(), bins=30, color='#61dafb', alpha=0.7)
            else:
                counts = transformed_values.value_counts()
                ax.bar(counts.index.astype(str), counts.values, color='#61dafb', alpha=0.7)
                plt.xticks(rotation=45)
        
        ax.set_title(f'New Distribution: {new_column_name}', color='white', pad=20)
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        
        img_str = self._fig_to_base64(fig)
        plt.close(fig)
        
        # Return both the visualization and created column names
        return img_str, created_columns

    def create_visualization(self, parameters, viz_type):
        """Create custom visualization"""
        if not parameters or not viz_type:
            raise ValueError("Parameters and visualization type are required")

        # Handle null values by removing rows where any of the parameters has null values
        df_viz = self.current_df[parameters].dropna()
        
        if len(df_viz) == 0:
            raise ValueError("No data available after removing null values")

        # Create figure with adjusted size for better label visibility
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('#282c34')
        ax.set_facecolor('#282c34')
        
        try:
            # Convert categorical x-axis values to strings
            x_data = df_viz[parameters[0]]
            
            if not pd.api.types.is_numeric_dtype(x_data):
                x_data = x_data.astype(str)
            
            if viz_type == 'histogram':
                if not pd.api.types.is_numeric_dtype(x_data):
                    raise ValueError("Histogram requires numeric data")
                ax.hist(x_data, bins=30, color='#61dafb', alpha=0.7)
                ax.grid(True, alpha=0.3)
                
            elif viz_type == 'box':
                if not pd.api.types.is_numeric_dtype(x_data):
                    raise ValueError("Box plot requires numeric data")
                ax.boxplot(x_data, patch_artist=True,
                          boxprops=dict(facecolor='#61dafb', alpha=0.7))
                ax.grid(True, alpha=0.3)
                
            elif viz_type == 'violin':
                if not pd.api.types.is_numeric_dtype(x_data):
                    raise ValueError("Violin plot requires numeric data")
                # Use seaborn's violinplot instead of matplotlib's
                sns.violinplot(data=x_data, ax=ax, color='#61dafb', alpha=0.7)
                ax.grid(True, alpha=0.3)
                
            elif viz_type == 'bar':
                counts = x_data.value_counts()
                # Limit to top 30 categories if there are too many
                if len(counts) > 30:
                    counts = counts.head(30)
                ax.bar(counts.index, counts.values, color='#61dafb', alpha=0.7)
                plt.xticks(rotation=45, ha='right')
                ax.grid(True, alpha=0.3)
                
            elif viz_type == 'pie':
                counts = x_data.value_counts()
                # Limit to top 10 categories for pie chart
                if len(counts) > 10:
                    counts = counts.head(10)
                ax.pie(counts.values, labels=counts.index, autopct='%1.1f%%', colors=['#61dafb'])
                
            elif viz_type == 'scatter':
                if len(parameters) != 2:
                    raise ValueError('Scatter plot requires exactly 2 parameters')
                y_data = df_viz[parameters[1]]
                if not pd.api.types.is_numeric_dtype(y_data):
                    raise ValueError("Y-axis must be numeric for scatter plot")
                ax.scatter(x_data, y_data, alpha=0.5, c='#61dafb')
                ax.set_xlabel(parameters[0])
                ax.set_ylabel(parameters[1])
                ax.grid(True, alpha=0.3)
                
            elif viz_type == 'line':
                if len(parameters) != 2:
                    raise ValueError('Line plot requires exactly 2 parameters')
                y_data = df_viz[parameters[1]]
                if not pd.api.types.is_numeric_dtype(y_data):
                    raise ValueError("Y-axis must be numeric for line plot")
                
                # For categorical x-axis, calculate mean y-value for each category
                if not pd.api.types.is_numeric_dtype(x_data):
                    # Calculate means and sort by value
                    means = df_viz.groupby(parameters[0])[parameters[1]].agg(['mean', 'count']).sort_values('mean')
                    
                    # Filter to show only categories with significant counts
                    min_count = max(means['count'].max() * 0.01, 5)  # At least 1% of max count or 5 samples
                    means = means[means['count'] >= min_count]
                    
                    # Limit to top 30 categories if there are too many
                    if len(means) > 30:
                        means = means.tail(30)  # Take top 30 by mean value
                    
                    # Plot with both lines and points
                    ax.plot(means.index, means['mean'], color='#61dafb', alpha=0.7, 
                           marker='o', markersize=6, linewidth=2)
                    
                    # Add value labels
                    for i, (idx, row) in enumerate(means.iterrows()):
                        ax.annotate(f'{row["mean"]:.1f}', 
                                  (idx, row['mean']),
                                  textcoords="offset points",
                                  xytext=(0,10),
                                  ha='center',
                                  color='white',
                                  alpha=0.7)
                else:
                    # For numeric x-axis, sort by x values
                    df_sorted = df_viz.sort_values(parameters[0])
                    ax.plot(df_sorted[parameters[0]], df_sorted[parameters[1]], 
                           color='#61dafb', alpha=0.7)
                
                ax.set_xlabel(parameters[0])
                ax.set_ylabel(parameters[1])
                plt.xticks(rotation=45, ha='right')
                ax.grid(True, alpha=0.3)
            else:
                raise ValueError(f"Unsupported visualization type: {viz_type}")
            
            ax.set_title(f'{viz_type.title()} Plot', color='white', pad=20)
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            img_str = self._fig_to_base64(fig)
            return img_str
            
        except Exception as e:
            raise
        finally:
            plt.close(fig)

    def save_data(self, columns):
        """Save selected columns to CSV"""
        output = io.StringIO()
        self.current_df[columns].to_csv(output, index=False)
        return output

    def _fig_to_base64(self, fig):
        """Convert matplotlib figure to base64 string"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode()
