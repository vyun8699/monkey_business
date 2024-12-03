import streamlit as st 
import plotly.express as px
from src.functions import TransformationRegistry, save_transformed_data
import pandas as pd
import json
from datetime import datetime

st.markdown("""
    <style>
    .stApp {
        max-height: 900vh;
        height: 100%;
        overflow: auto;
    }
    .main .block-container {
        max-height: 100%;
        padding-top: 1rem;     # Increased top padding
        padding-bottom: 2rem;  # Increased bottom padding
        margin-top: 1rem;      # Added top margin
        margin-bottom: 1rem;   # Added bottom margin
    }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.raw_data is None: 
    st.markdown('Data has not been selected yet')

else:
    selected_feature = st.selectbox(
        "Choose feature to explore", 
        st.session_state.available_columns
    )

    # Initialize transformed data in session state if not exists
    if 'transformed_data' not in st.session_state:
        st.session_state.transformed_data = st.session_state.raw_data.copy()

    # Overview of raw parameter
    st.markdown('### :blue[Feature Overview]')

    data = st.session_state.raw_data

    if selected_feature in st.session_state.raw_numeric_attrs:
        desc = data[selected_feature].describe()
    
        col0,col1 = st.columns(2)

        formatted_desc0 = f"""
        - **Count:** {desc['count']:.0f}
        - **Missing Values:** {data[selected_feature].isnull().sum()}
        - **Mean:** {desc['mean']:.2f}
        - **Standard Deviation:** {desc['std']:.2f}
        """

        formatted_desc1 = f"""
        - **Min:** {desc['min']:.2f}
        - **25%:** {desc['25%']:.2f}
        - **Median:** {desc['50%']:.2f}
        - **75%:** {desc['75%']:.2f}
        - **Max:** {desc['max']:.2f}
        """

        with col0:    
            st.markdown(formatted_desc0)
        
        with col1:    
            st.markdown(formatted_desc1)

        with st.container(border=True):
            # Display transformation buttons for numeric attributes
            st.markdown("**Available Transformations:**")

            col0,col1, col2,col3, col4 = st.columns(5, gap ='small')
            
            with col0:
                if st.button('Standardize', key=f'std_{selected_feature}'):
                    transform = st.session_state.transformation_registry.get_numeric_transformation('Standardization')
                    transformed_data, log_entry = transform.transform(st.session_state.raw_data, selected_feature)
                    st.session_state.transformed_data[selected_feature] = transformed_data
                    st.session_state.transformation_registry.set_pending_log(log_entry)
            
            with col1:
                if st.button('Min-Max Scale', key=f'minmax_{selected_feature}'):
                    transform = st.session_state.transformation_registry.get_numeric_transformation('Min-Max Scaling')
                    transformed_data, log_entry = transform.transform(st.session_state.raw_data, selected_feature)
                    st.session_state.transformed_data[selected_feature] = transformed_data
                    st.session_state.transformation_registry.set_pending_log(log_entry)
            
            with col2:
                if st.button('Log Transform', key=f'log_{selected_feature}'):
                    transform = st.session_state.transformation_registry.get_numeric_transformation('Log Transform')
                    transformed_data, log_entry = transform.transform(st.session_state.raw_data, selected_feature)
                    st.session_state.transformed_data[selected_feature] = transformed_data
                    st.session_state.transformation_registry.set_pending_log(log_entry)
            
            with col3:
                if st.button(f':red[Reset]', key=f'reset_{selected_feature}'):
                    st.session_state.transformed_data[selected_feature] = st.session_state.raw_data[selected_feature]
                    st.session_state['transform_column'] = selected_feature
                    st.session_state.transformation_registry.clear_pending_log()
            
            with col4:
                if st.button(':green[Save Transformation]'):
                    # Save the pending transformation log
                    st.session_state.transformation_registry.save_pending_log()
                    # Update raw_data with the transformed data
                    st.session_state.raw_data = st.session_state.transformed_data.copy()
                    st.success(f'Transformation for {selected_feature} has been saved to session state.')

            # Display histograms
            col0, col1 = st.columns([1,1])

            with col0:
                fig = px.histogram(st.session_state.raw_data, x=selected_feature, 
                                title=f'Raw distribution of {selected_feature}', marginal='box')
                st.plotly_chart(fig, use_container_width=True)
            
            with col1:
                fig = px.histogram(st.session_state.transformed_data, x=selected_feature,
                                title=f'Transformed distribution of {selected_feature}', marginal='box')
                st.plotly_chart(fig, use_container_width=True)

            # Display box plots
            col = st.columns([0.5,0.5])
            with col[0]:
                fig = px.box(st.session_state.raw_data, x=selected_feature,
                            title=f'Raw box Plot of {selected_feature}', points='all')
                st.plotly_chart(fig, use_container_width=True)
                
            with col[1]:
                fig = px.box(st.session_state.transformed_data, x=selected_feature,
                            title=f'Transformed box Plot of {selected_feature}', points='all')
                st.plotly_chart(fig, use_container_width=True)

    elif selected_feature in st.session_state.raw_object_attrs:
        desc = data[selected_feature].describe()
        
        col0, col1 = st.columns(2)
        
        formatted_desc0 = f"""
        - **Total Count:** {desc['count']}
        - **Missing Values:** {data[selected_feature].isnull().sum()}
        - **Unique Values:** {desc['unique']}
        """

        formatted_desc1 = f"""
        - **Most Common:** {desc['top']}
        - **Frequency of Most Common:** {desc['freq']}
        - **% of Most Common:** {(desc['freq'] / desc['count'] * 100):.2f}%
        """

        with col0:    
            st.markdown(formatted_desc0)
        
        with col1:    
            st.markdown(formatted_desc1)

        with st.container(border=True):
            st.markdown("**Available Transformations:**")
            
            col0, col1, col2, col3 = st.columns(4, gap='small')
                
            with col0:
                if st.button('Label Encode', key=f'label_{selected_feature}'):
                    transform = st.session_state.transformation_registry.get_categorical_transformation('Label Encoding')
                    transformed_data, log_entry = transform.transform(st.session_state.raw_data, selected_feature)
                    st.session_state.transformed_data[selected_feature] = transformed_data
                    st.session_state.transformation_registry.set_pending_log(log_entry)
            
            with col1:
                if st.button('One-Hot Encode', key=f'onehot_{selected_feature}'):
                    transform = st.session_state.transformation_registry.get_categorical_transformation('One-Hot Encoding')
                    encoded_data, log_entry = transform.transform(st.session_state.raw_data, selected_feature)
                    # Add the encoded columns to transformed_data
                    for col in encoded_data.columns:
                        st.session_state.transformed_data[col] = encoded_data[col]
                    # Remove the original column
                    st.session_state.transformed_data = st.session_state.transformed_data.drop(columns=[selected_feature])
                    st.session_state.transformation_registry.set_pending_log(log_entry)
                    # Update available columns
                    st.session_state.available_columns = list(st.session_state.transformed_data.columns)
                    st.session_state.raw_numeric_attrs = list(st.session_state.transformed_data.select_dtypes(include=['int64', 'float64']).columns)
                    st.session_state.raw_object_attrs = list(st.session_state.transformed_data.select_dtypes(include=['object', 'category']).columns)
                    st.experimental_rerun()
            
            with col2:
                if st.button(':red[Reset]', key=f'reset_{selected_feature}'):
                    # Remove any one-hot encoded columns
                    one_hot_cols = [col for col in st.session_state.transformed_data.columns if col.startswith(f"{selected_feature}_")]
                    st.session_state.transformed_data = st.session_state.transformed_data.drop(columns=one_hot_cols)
                    # Restore original column
                    st.session_state.transformed_data[selected_feature] = st.session_state.raw_data[selected_feature]
                    st.session_state['transform_column'] = selected_feature
                    st.session_state.transformation_registry.clear_pending_log()
                    # Update available columns
                    st.session_state.available_columns = list(st.session_state.transformed_data.columns)
                    st.session_state.raw_numeric_attrs = list(st.session_state.transformed_data.select_dtypes(include=['int64', 'float64']).columns)
                    st.session_state.raw_object_attrs = list(st.session_state.transformed_data.select_dtypes(include=['object', 'category']).columns)
                    st.experimental_rerun()
            
            with col3:
                if st.button(':green[Save Transformation]'):
                    # Save the pending transformation log
                    st.session_state.transformation_registry.save_pending_log()
                    # Update raw_data with the transformed data
                    st.session_state.raw_data = st.session_state.transformed_data.copy()
                    # Update available columns
                    st.session_state.available_columns = list(st.session_state.raw_data.columns)
                    st.session_state.raw_numeric_attrs = list(st.session_state.raw_data.select_dtypes(include=['int64', 'float64']).columns)
                    st.session_state.raw_object_attrs = list(st.session_state.raw_data.select_dtypes(include=['object', 'category']).columns)
                    st.success(f'Transformation for {selected_feature} has been saved to session state.')

            # Display value counts before and after transformation
            col0, col1 = st.columns([1,1])

            with col0:
                raw_value_counts = st.session_state.raw_data[selected_feature].value_counts()
                fig = px.bar(x=raw_value_counts.index, y=raw_value_counts.values,
                            title=f'Raw distribution of {selected_feature}',
                            labels={'x': selected_feature, 'y': 'Count'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col1:
                if selected_feature in st.session_state.transformed_data.columns:
                    # For label encoding
                    trans_value_counts = st.session_state.transformed_data[selected_feature].value_counts()
                    fig = px.bar(x=trans_value_counts.index, y=trans_value_counts.values,
                                title=f'Transformed distribution of {selected_feature}',
                                labels={'x': selected_feature, 'y': 'Count'})
                else:
                    # For one-hot encoding
                    one_hot_cols = [col for col in st.session_state.transformed_data.columns if col.startswith(f"{selected_feature}_")]
                    if one_hot_cols:
                        fig = px.bar(x=one_hot_cols, y=st.session_state.transformed_data[one_hot_cols].sum(),
                                    title=f'One-Hot Encoded distribution of {selected_feature}',
                                    labels={'x': 'Categories', 'y': 'Count'})
                st.plotly_chart(fig, use_container_width=True)
