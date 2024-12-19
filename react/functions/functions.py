import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
import math

def calculate_histogram(series: pd.Series, max_bins: int = 50, sample_size: int = 10000) -> dict:
    """Calculate histogram bins and counts for a numeric series, with sampling for large datasets"""
    # Handle NaN values
    series = series.dropna()
    
    # Sample data if it's too large
    if len(series) > sample_size:
        series = series.sample(n=sample_size, random_state=42)
    
    # Calculate optimal number of bins (Sturges' rule)
    n_bins = min(max_bins, int(np.ceil(np.log2(len(series)) + 1)))
    
    # Calculate histogram
    counts, bin_edges = np.histogram(series, bins=n_bins)
    
    # Create bin labels
    bin_labels = [f"{bin_edges[i]:.2f} - {bin_edges[i+1]:.2f}" for i in range(len(bin_edges)-1)]
    
    return {
        "bins": bin_labels,
        "counts": counts.tolist(),
        "total_count": len(series),
        "sampled": len(series) < len(series.dropna())
    }

def analyze_nulls(df: pd.DataFrame) -> dict:
    """Analyze null values in the DataFrame"""
    total_rows = len(df)
    null_info = {}
    
    for column in df.columns:
        null_count = df[column].isna().sum()
        null_percentage = (null_count / total_rows) * 100
        
        null_info[column] = {
            "null_count": int(null_count),
            "null_percentage": round(null_percentage, 2),
            "total_rows": total_rows
        }
    
    return null_info

def clean_nan_values(df_dict):
    """Replace NaN values with None in a dictionary and ensure JSON serializable types"""
    cleaned = {}
    for key, value in df_dict.items():
        if isinstance(value, float) and math.isnan(value):
            cleaned[key] = None
        elif isinstance(value, (int, float)):  # Handle numeric values including 0 and 1
            # Convert to regular Python int/float for JSON serialization
            if float(value).is_integer():
                cleaned[key] = int(value)
            else:
                cleaned[key] = float(value)
        elif isinstance(value, np.integer):  # Handle numpy integers
            cleaned[key] = int(value)
        elif isinstance(value, np.floating):  # Handle numpy floats
            cleaned[key] = float(value)
        else:
            cleaned[key] = value
    return cleaned

def apply_standardization(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Apply standardization to a column"""
    scaler = StandardScaler()
    df[f"{column}_standardized"] = df[column].copy().astype('float64')
    mask = ~df[f"{column}_standardized"].isna()
    df.loc[mask, f"{column}_standardized"] = scaler.fit_transform(df.loc[mask, [column]])
    return df

def apply_minmax(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Apply min-max scaling to a column"""
    scaler = MinMaxScaler()
    df[f"{column}_minmax"] = df[column].copy().astype('float64')
    mask = ~df[f"{column}_minmax"].isna()
    df.loc[mask, f"{column}_minmax"] = scaler.fit_transform(df.loc[mask, [column]])
    return df

def apply_log(df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, str | None]:
    """Apply log transformation to a column"""
    # Ensure column is float64 type for log transformation
    df[column] = df[column].astype('float64')
    
    # Create new column for transformed values
    df[f"{column}_log"] = df[column].copy()
    
    # Create mask for non-null values
    mask = ~df[f"{column}_log"].isna()
    
    # Check for positive values only on non-null data
    if (df.loc[mask, column] <= 0).any():
        return df, 'Log transformation requires positive values'
    
    # Apply log transformation only to non-null positive values
    df.loc[mask, f"{column}_log"] = np.log1p(df.loc[mask, column].astype('float64'))
    return df, None

def apply_label_encoding(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Apply label encoding to a column"""
    le = LabelEncoder()
    df[f"{column}_label"] = df[column].copy()
    mask = ~df[f"{column}_label"].isna()
    df.loc[mask, f"{column}_label"] = le.fit_transform(df.loc[mask, [column]])
    return df

def apply_onehot_encoding(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Apply one-hot encoding to a column"""
    # Ensure the column is treated as categorical
    df[column] = df[column].astype('category')
    one_hot = pd.get_dummies(df[column], prefix=column, dtype=int)  # Use Python int instead of np.int64
    return pd.concat([df, one_hot], axis=1)

def remove_nulls(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Remove rows with null values in the specified column"""
    return df.dropna(subset=[column])

def transform_column(df: pd.DataFrame, column: str, transform_type: str) -> tuple[pd.DataFrame, str | None]:
    """Transform a column based on the specified transformation type"""
    is_numeric = np.issubdtype(df[column].dtype, np.number)
    
    if transform_type == 'remove_nulls':
        return remove_nulls(df, column), None
    
    if is_numeric:
        if transform_type == 'standardized':
            return apply_standardization(df, column), None
        elif transform_type == 'minmax':
            return apply_minmax(df, column), None
        elif transform_type == 'log':
            return apply_log(df, column)
    else:
        if transform_type == 'label':
            return apply_label_encoding(df, column), None
        elif transform_type == 'onehot':
            return apply_onehot_encoding(df, column), None
    
    return df, f'Invalid transformation {transform_type} for column type'
