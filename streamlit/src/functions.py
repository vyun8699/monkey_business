import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import streamlit as st
from datetime import datetime

#output functions

def get_numeric_columns(data):
    """Filter numeric columns from selected columns"""
    columns = data.columns
    numeric_df = data[columns].select_dtypes(include=['int64', 'float64'])
    return list(numeric_df.columns)

def get_object_columns(data):
    """Filter object/categorical columns from selected columns"""
    columns = data.columns
    object_df = data[columns].select_dtypes(include=['object', 'category'])
    return list(object_df.columns)

def calculate_numeric_stats(data, attributes):
    """Calculate statistics for numeric attributes"""
    stats_list = []
    for attribute in attributes:
        if pd.api.types.is_numeric_dtype(data[attribute]):
            stats = {
                'Attribute': attribute,
                'Data Type': str(data[attribute].dtype),
                'Total Count': len(data[attribute]),
                'NaN Count': data[attribute].isna().sum(),
                'Mean': f"{data[attribute].mean():.2f}",
                'Median': f"{data[attribute].median():.2f}"
            }
            stats_list.append(stats)
    return pd.DataFrame(stats_list)

def calculate_object_stats(data, attributes):
    """Calculate statistics for object attributes"""
    stats_list = []
    for attribute in attributes:
        if pd.api.types.is_object_dtype(data[attribute]):
            stats = {
                'Attribute': attribute,
                'Data Type': str(data[attribute].dtype),
                'Total Count': len(data[attribute]),
                'NaN Count': data[attribute].isna().sum(),
            }
            stats_list.append(stats)
    return pd.DataFrame(stats_list)

# Base Transformation class
class Transformation(ABC):
    @abstractmethod
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        """Transform the data"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get transformation name"""
        pass

    @property
    @abstractmethod
    def requires_fit(self) -> bool:
        """Whether this transformation needs to be fit before transform"""
        pass

    def get_data_stats(self, data: pd.Series) -> dict:
        """Get basic statistics of data"""
        if pd.api.types.is_numeric_dtype(data):
            return {
                'mean': f"{data.mean():.2f}",
                'std': f"{data.std():.2f}",
                'min': f"{data.min():.2f}",
                'max': f"{data.max():.2f}"
            }
        else:
            return {
                'unique_values': data.nunique(),
                'most_common': data.value_counts().head(3).to_dict()
            }

    def prepare_transformation_log(self, column: str, original_data: pd.Series = None, transformed_data: pd.Series = None) -> dict:
        """Prepare transformation log entry without saving it"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'transformation': self.get_name(),
            'column': column,
            'parameters': self.fitted_params.get(column, {})
        }

        # Add data statistics if provided
        if original_data is not None and transformed_data is not None:
            log_entry['original_stats'] = self.get_data_stats(original_data)
            log_entry['transformed_stats'] = self.get_data_stats(transformed_data)

        return log_entry

# Numeric Transformations
class NumericTransformation(Transformation):
    def __init__(self):
        self.fitted_params = {}

class StandardizationTransform(NumericTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        scaler = StandardScaler()
        transformed = scaler.fit_transform(data[column].values.reshape(-1, 1))
        transformed_series = pd.Series(transformed.flatten(), index=data.index)
        self.fitted_params[column] = {
            'mean': float(scaler.mean_[0]),
            'scale': float(scaler.scale_[0])
        }
        return transformed_series, self.prepare_transformation_log(column, data[column], transformed_series)

    def get_name(self) -> str:
        return "Standardization"

    @property
    def requires_fit(self) -> bool:
        return True

class MinMaxScalingTransform(NumericTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        scaler = MinMaxScaler()
        transformed = scaler.fit_transform(data[column].values.reshape(-1, 1))
        transformed_series = pd.Series(transformed.flatten(), index=data.index)
        self.fitted_params[column] = {
            'min': float(scaler.min_[0]),
            'scale': float(scaler.scale_[0])
        }
        return transformed_series, self.prepare_transformation_log(column, data[column], transformed_series)

    def get_name(self) -> str:
        return "Min-Max Scaling"

    @property
    def requires_fit(self) -> bool:
        return True

class LogTransform(NumericTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        transformed_series = np.log1p(data[column])
        return transformed_series, self.prepare_transformation_log(column, data[column], transformed_series)

    def get_name(self) -> str:
        return "Log Transform"

    @property
    def requires_fit(self) -> bool:
        return False

# Categorical Transformations
class CategoricalTransformation(Transformation):
    def __init__(self):
        self.fitted_params = {}

class LabelEncodingTransform(CategoricalTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        encoder = LabelEncoder()
        transformed = encoder.fit_transform(data[column])
        transformed_series = pd.Series(transformed, index=data.index)
        self.fitted_params[column] = {
            'classes': encoder.classes_.tolist()
        }
        return transformed_series, self.prepare_transformation_log(column, data[column], transformed_series)

    def get_name(self) -> str:
        return "Label Encoding"

    @property
    def requires_fit(self) -> bool:
        return True

class OneHotEncodingTransform(CategoricalTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.DataFrame:
        encoded = pd.get_dummies(data[column], prefix=column)
        self.fitted_params[column] = {
            'categories': encoded.columns.tolist()
        }
        return encoded, self.prepare_transformation_log(column, data[column], encoded)

    def get_name(self) -> str:
        return "One-Hot Encoding"

    @property
    def requires_fit(self) -> bool:
        return True

# Transformation Registry
class TransformationRegistry:
    def __init__(self):
        self._numeric_transformations: Dict[str, NumericTransformation] = {}
        self._categorical_transformations: Dict[str, CategoricalTransformation] = {}
        self._pending_log = None

    def register_numeric(self, transformation: NumericTransformation) -> None:
        """Register a numeric transformation"""
        self._numeric_transformations[transformation.get_name()] = transformation

    def register_categorical(self, transformation: CategoricalTransformation) -> None:
        """Register a categorical transformation"""
        self._categorical_transformations[transformation.get_name()] = transformation

    def get_numeric_transformation(self, name: str) -> NumericTransformation:
        """Get a numeric transformation by name"""
        return self._numeric_transformations.get(name)

    def get_categorical_transformation(self, name: str) -> CategoricalTransformation:
        """Get a categorical transformation by name"""
        return self._categorical_transformations.get(name)

    def get_numeric_names(self) -> List[str]:
        """Get list of available numeric transformation names"""
        return list(self._numeric_transformations.keys())

    def get_categorical_names(self) -> List[str]:
        """Get list of available categorical transformation names"""
        return list(self._categorical_transformations.keys())

    def set_pending_log(self, log_entry: dict) -> None:
        """Store a transformation log entry to be saved later"""
        self._pending_log = log_entry

    def save_pending_log(self) -> None:
        """Save the pending log entry to the change log"""
        if self._pending_log is not None:
            if 'change_log' not in st.session_state:
                st.session_state.change_log = []
            st.session_state.change_log.append(self._pending_log)
            self._pending_log = None

    def clear_pending_log(self) -> None:
        """Clear the pending log entry without saving"""
        self._pending_log = None

# Initialize global registry
if 'transformation_registry' not in st.session_state:
    registry = TransformationRegistry()
    
    # Register numeric transformations
    registry.register_numeric(StandardizationTransform())
    registry.register_numeric(MinMaxScalingTransform())
    registry.register_numeric(LogTransform())
    
    # Register categorical transformations
    registry.register_categorical(LabelEncodingTransform())
    registry.register_categorical(OneHotEncodingTransform())
    
    st.session_state.transformation_registry = registry

def save_transformed_data(data: pd.DataFrame, filename: str) -> None:
    """Save transformed data to CSV file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"data/transformed_{timestamp}_{filename}"
    data.to_csv(save_path, index=False)
    if 'change_log' in st.session_state:
        st.session_state.change_log.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': 'Save',
            'filename': save_path
        })
    return save_path

def log_change(key):
    if 'change_log' not in st.session_state:
        st.session_state.change_log = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if key == 'class_attr':
        st.session_state.change_log.append({
            'timestamp': timestamp,
            'action': 'Class Selection',
            'attribute': st.session_state.class_attr
        })
    elif key == 'reset':
        st.session_state.change_log.append({
            'timestamp': timestamp,
            'action': 'Reset',
            'column': st.session_state.get('transform_column', 'Unknown')
        })
