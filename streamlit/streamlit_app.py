#adjusted from @wbjmattingly - https://www.youtube.com/watch?v=s86jz9qVeWA&t=158s

#imports
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler

pg = st.navigation([st.Page("page_1.py")])

st.set_page_config(layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .deselected {
        color: #cccccc !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #7f7f7f;
    }
    .stContainer {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 20px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

def transform_data(data, column, transform_type):
    """Apply data transformation to a column"""
    if transform_type == "Standardization":
        scaler = StandardScaler()
        transformed = scaler.fit_transform(data[column].values.reshape(-1, 1))
        return pd.Series(transformed.flatten(), index=data.index)
    elif transform_type == "Min-Max Scaling":
        scaler = MinMaxScaler()
        transformed = scaler.fit_transform(data[column].values.reshape(-1, 1))
        return pd.Series(transformed.flatten(), index=data.index)
    elif transform_type == "Log Transform":
        # Add small constant to handle zeros
        return np.log1p(data[column])
    return data[column]

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

def get_numeric_columns(data, columns):
    """Filter numeric columns from selected columns"""
    numeric_df = data[columns].select_dtypes(include=['int64', 'float64'])
    return list(numeric_df.columns)

def get_object_columns(data, columns):
    """Filter object/categorical columns from selected columns"""
    object_df = data[columns].select_dtypes(include=['object', 'category'])
    return list(object_df.columns)

# Initialize session state
if 'selected_numeric_attrs' not in st.session_state:
    st.session_state.selected_numeric_attrs = []
if 'selected_object_attrs' not in st.session_state:
    st.session_state.selected_object_attrs = []
if 'transform_popup' not in st.session_state:
    st.session_state.transform_popup = False
if 'kept_attributes' not in st.session_state:
    st.session_state.kept_attributes = []
if 'previous_class_attr' not in st.session_state:
    st.session_state.previous_class_attr = None
if 'transformed_data' not in st.session_state:
    st.session_state.transformed_data = None

# Top ribbon
st.markdown('<div class="top-ribbon">', unsafe_allow_html=True)
ribbon_cols = st.columns([1, 3])

# Upload section (1/5 of ribbon)
with ribbon_cols[0]:
    st.markdown("### Data Upload")
    uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

# Attributes section (4/5 of ribbon)
with ribbon_cols[1]:
    st.markdown("### Parameters")
    if uploaded_file is not None:
        # Load the uploaded CSV file
        elements = pd.read_csv(uploaded_file)
        if st.session_state.transformed_data is not None:
            elements = st.session_state.transformed_data
        
        # Get all attributes
        attributes = elements.columns
        
        # Class attribute selection in red box
        st.markdown('<div class="red-border">', unsafe_allow_html=True)
        class_atr = st.selectbox("Define your class attribute", [""] + list(attributes))
        st.markdown('</div>', unsafe_allow_html=True)
        
        if class_atr:
            # Check if class attribute has changed
            if class_atr != st.session_state.previous_class_attr:
                # Initialize or update available attributes when class changes
                other_attributes = [attr for attr in attributes if attr != class_atr]
                
                # Split attributes into numeric and object
                st.session_state.selected_numeric_attrs = get_numeric_columns(elements, other_attributes)
                st.session_state.selected_object_attrs = get_object_columns(elements, other_attributes)
                
                # Update previous class attribute
                st.session_state.previous_class_attr = class_atr
            
            col = st.columns([0.33, 0.33, 0.33])

            with col[0]:
                # Selected numeric attributes section
                selected_numeric = st.multiselect("Numeric attributes", 
                                                st.session_state.selected_numeric_attrs,
                                                default=st.session_state.selected_numeric_attrs)
            
            with col[1]:
                # Selected object attributes section
                selected_object = st.multiselect("Categorical attributes",
                                            st.session_state.selected_object_attrs,
                                            default=st.session_state.selected_object_attrs)
            
            # Calculate deselected attributes
            all_attrs = list(attributes)
            selected_attrs = [class_atr] + selected_numeric + selected_object
            deselected_attrs = [attr for attr in all_attrs if attr not in selected_attrs]
            
            with col[2]:
                # Deselected attributes section
                selected_deselected = st.multiselect("Deselected attributes",
                                                deselected_attrs,
                                                default=deselected_attrs)
                
            # Store all kept attributes
            st.session_state.kept_attributes = [class_atr] + selected_numeric + selected_object + selected_deselected
            
            # Transform button
            if st.button("Transform"):
                st.session_state.transform_popup = True
            
            # Transform popup
            if st.session_state.transform_popup:
                st.markdown("### Transform Attributes")
                transform_attrs = st.multiselect(
                    "Select attributes to transform",
                    selected_numeric + [class_atr]  # Only allow transforming numeric attributes
                )
                
                transformed_data = elements.copy()
                
                # For each selected attribute, show transformation options
                for attr in transform_attrs:
                    st.markdown(f"#### Transform {attr}")
                    transform_type = st.selectbox(
                        f"Transform type for {attr}",
                        ["Standardization", "Min-Max Scaling", "Log Transform"],
                        key=f"transform_{attr}"
                    )
                    
                    # Apply transformation
                    transformed_data[attr] = transform_data(elements, attr, transform_type)
                
                # Apply transformations button
                if st.button("Apply Transformations"):
                    st.session_state.transformed_data = transformed_data
                    st.success("Transformations applied successfully!")
                
                # Close popup button
                if st.button("Done"):
                    st.session_state.transform_popup = False

st.markdown('</div>', unsafe_allow_html=True)

# Main content area
if uploaded_file is None:
    st.warning("Please upload a CSV file to begin analysis.")
else:
    # Dataset Summary Container
    with st.container(border=1):
        st.markdown("#### Dataset Summary")
        st.markdown("[xxx] data points, with [xxx] numeric and [xxx] categorical attributes.")
        st.markdown("Target attribute is [xxx] with [xxx] actively selected by user. [xxx] were dropped.")
        st.markdown("Change log: [xxx]")

    col = st.columns([0.4, 0.6])
    # Numeric Attributes Container
    with col[0]:
        with st.container(border=1):
            st.markdown("##### Numeric Attributes Analysis")
            
            # Numerics
            if len(selected_numeric) > 0:
                # Display numeric statistics table
                stats_df = calculate_numeric_stats(elements, selected_numeric)
                st.dataframe(stats_df, use_container_width=True)
            else:
                st.info("No numeric attributes available for analysis.")

            st.markdown("##### Categorical Attributes Analysis")
            
            # Objects
            if len(selected_object) > 0:
                # Display object statistics table
                stats_df = calculate_object_stats(elements, selected_object)
                st.dataframe(stats_df, use_container_width=True)
            else:
                st.info("No categorical attributes available for analysis.")

    # Object Attributes Container
    with col[1]:
        with st.container(border=1):
            if len(st.session_state.kept_attributes) > 0:
                # Add selectbox for attributes
                selected_attr = st.selectbox("Select attribute to analyze:", st.session_state.kept_attributes)
                
                #note, this is a problem if class is categorical
                if selected_attr in (selected_numeric + [class_atr]):
                    # Display detailed statistics for selected attribute
                    st.markdown(f"#### Detailed Analysis of {selected_attr}")
                    
                    # Display histogram for selected attribute
                    fig = px.histogram(elements, x=selected_attr, 
                                     title=f'Distribution of {selected_attr}')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display box plot for selected attribute
                    fig = px.box(elements, y=selected_attr,
                               title=f'Box Plot of {selected_attr}')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display correlation with other numeric attributes
                    st.markdown(f"#### Correlations with {selected_attr}")
                    other_numeric = [col for col in selected_numeric if col != selected_attr]
                    if other_numeric:
                        corr_data = elements[[selected_attr] + other_numeric]
                        corr_matrix = corr_data.corr()[selected_attr].sort_values(ascending=False)
                        fig = px.bar(x=corr_matrix.index, y=corr_matrix.values,
                                   title=f'Correlation with other numeric attributes',
                                   labels={'x': 'Attributes', 'y': 'Correlation'})
                        st.plotly_chart(fig, use_container_width=True)
            
                elif selected_attr in selected_object:
                    # Display histogram
                    value_counts = elements[selected_attr].value_counts()
                    fig = px.bar(x=value_counts.index, 
                            y=value_counts.values,
                            title=f'Distribution of {selected_attr}',
                            labels={'x': selected_attr, 'y': 'Count'})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display top 10 values
                    st.markdown(f"#### Top 10 Values for {selected_attr}")
                    top_10 = value_counts.head(10).reset_index()
                    top_10.columns = [selected_attr, 'Count']
                    st.dataframe(top_10, use_container_width=True)

    col = st.columns([0.5, 0.5])

    with col[0]:
       st.markdown('abc')

    with col[1]:
        st.markdown('abc')
