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

class DataProcessor:
    def __init__(self):
        self.current_df = None
        self.original_df = None
        plt.style.use('dark_background')

    def load_data(self, file):
        """Load data from CSV file and determine column types"""
        self.current_df = pd.read_csv(file)
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
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('#282c34')
        ax.set_facecolor('#282c34')
        
        try:
            if pd.api.types.is_numeric_dtype(self.current_df[column]):
                ax.hist(self.current_df[column].dropna(), bins=30, color='#61dafb', alpha=0.7)
            else:
                counts = self.current_df[column].value_counts()
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
            fig, ax = plt.subplots(figsize=(10, 8))
            fig.patch.set_facecolor('#282c34')
            ax.set_facecolor('#282c34')
            
            sns.heatmap(df_selected[numeric_cols].corr(), 
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
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(df_selected[numeric_cols])
            
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(scaled_data)
            
            fig, ax = plt.subplots(figsize=(10, 8))
            fig.patch.set_facecolor('#282c34')
            ax.set_facecolor('#282c34')
            
            scatter = ax.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.5, c='#61dafb')
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
            if transformation == 'log':
                if (data <= 0).any():
                    raise ValueError('Log transformation requires positive values')
                return np.log(data)
                
            elif transformation == 'sqrt':
                if (data < 0).any():
                    raise ValueError('Square root transformation requires non-negative values')
                return np.sqrt(data)
                
            elif transformation == 'standard':
                scaler = StandardScaler()
                return pd.Series(scaler.fit_transform(data.values.reshape(-1, 1)).flatten(), index=data.index)
                
            elif transformation == 'minmax':
                scaler = MinMaxScaler()
                return pd.Series(scaler.fit_transform(data.values.reshape(-1, 1)).flatten(), index=data.index)
                
            elif transformation == 'dropna':
                return data.dropna()
                
            elif transformation == 'fillna_mean':
                return data.fillna(data.mean())
                
            elif transformation == 'fillna_median':
                return data.fillna(data.median())
                
            elif transformation == 'label_encoding':
                le = LabelEncoder()
                return pd.Series(le.fit_transform(data.astype(str)), index=data.index)
                
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
            
            else:
                raise ValueError('Invalid transformation')
                
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
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor('#282c34')
        ax.set_facecolor('#282c34')
        
        try:
            if viz_type == 'histogram':
                ax.hist(self.current_df[parameters[0]].dropna(), bins=30, color='#61dafb', alpha=0.7)
                
            elif viz_type == 'box':
                ax.boxplot(self.current_df[parameters[0]].dropna(), patch_artist=True,
                          boxprops=dict(facecolor='#61dafb', alpha=0.7))
                
            elif viz_type == 'violin':
                ax.violinplot(self.current_df[parameters[0]].dropna(), patch_artist=True)
                
            elif viz_type == 'bar':
                counts = self.current_df[parameters[0]].value_counts()
                ax.bar(counts.index.astype(str), counts.values, color='#61dafb', alpha=0.7)
                plt.xticks(rotation=45)
                
            elif viz_type == 'pie':
                counts = self.current_df[parameters[0]].value_counts()
                ax.pie(counts.values, labels=counts.index, autopct='%1.1f%%', colors=['#61dafb'])
                
            elif viz_type == 'scatter':
                if len(parameters) != 2:
                    raise ValueError('Scatter plot requires exactly 2 parameters')
                ax.scatter(self.current_df[parameters[0]], self.current_df[parameters[1]], 
                         alpha=0.5, c='#61dafb')
                ax.set_xlabel(parameters[0])
                ax.set_ylabel(parameters[1])
                
            elif viz_type == 'line':
                if len(parameters) != 2:
                    raise ValueError('Line plot requires exactly 2 parameters')
                ax.plot(self.current_df[parameters[0]], self.current_df[parameters[1]], 
                       color='#61dafb', alpha=0.7)
                ax.set_xlabel(parameters[0])
                ax.set_ylabel(parameters[1])
            
            ax.set_title(f'{viz_type.title()} Plot', color='white', pad=20)
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
            
            return self._fig_to_base64(fig)
            
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
