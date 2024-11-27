import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import streamlit as st

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

# Numeric Transformations
class NumericTransformation(Transformation):
    def __init__(self):
        self.fitted_params = {}

class StandardizationTransform(NumericTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        scaler = StandardScaler()
        transformed = scaler.fit_transform(data[column].values.reshape(-1, 1))
        self.fitted_params[column] = {
            'mean': scaler.mean_[0],
            'scale': scaler.scale_[0]
        }
        return pd.Series(transformed.flatten(), index=data.index)

    def get_name(self) -> str:
        return "Standardization"

    @property
    def requires_fit(self) -> bool:
        return True

class MinMaxScalingTransform(NumericTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        scaler = MinMaxScaler()
        transformed = scaler.fit_transform(data[column].values.reshape(-1, 1))
        self.fitted_params[column] = {
            'min': scaler.min_[0],
            'scale': scaler.scale_[0]
        }
        return pd.Series(transformed.flatten(), index=data.index)

    def get_name(self) -> str:
        return "Min-Max Scaling"

    @property
    def requires_fit(self) -> bool:
        return True

class LogTransform(NumericTransformation):
    def transform(self, data: pd.DataFrame, column: str) -> pd.Series:
        return np.log1p(data[column])

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
        self.fitted_params[column] = {
            'classes': encoder.classes_.tolist()
        }
        return pd.Series(transformed, index=data.index)

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
        return encoded

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

def log_change(key):
    if key == 'class_attr':
        st.session_state.change_log.append(f'Class attribute selected: {st.session_state.class_attr}')
    if key == 'transform':
        st.session_state.change_log.append(f'Transformation applied to {st.session_state.transform_column}: {st.session_state.transform_type}')
