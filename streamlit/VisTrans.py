import streamlit as st 
import plotly.express as px
from src.functions import TransformationRegistry
import pandas as pd

if st.session_state.raw_data is None: 
    st.markdown('Data has not been selected yet')

else:
    st.markdown(('### Data Overview'))

    # Initialize transformed data in session state if not exists
    if 'transformed_data' not in st.session_state:
        st.session_state.transformed_data = st.session_state.raw_data.copy()

    for param in st.session_state.raw_data.columns:
        with st.container(border=True):
            st.markdown(f"#### :blue[{param}]")
            if param in st.session_state.raw_numeric_attrs:
                # Display transformation buttons for numeric attributes
                st.markdown("**Available Transformations:**")
                col0,col1, col2,col3 = st.columns(4, gap ='small', vertical_alignment = 'center')
                
                with col0:
                    if st.button('Standardize', key=f'std_{param}'):
                        transform = st.session_state.transformation_registry.get_numeric_transformation('Standardization')
                        st.session_state.transformed_data[param] = transform.transform(st.session_state.raw_data, param)
                
                with col1:
                    if st.button('Min-Max Scale', key=f'minmax_{param}'):
                        transform = st.session_state.transformation_registry.get_numeric_transformation('Min-Max Scaling')
                        st.session_state.transformed_data[param] = transform.transform(st.session_state.raw_data, param)
                
                with col2:
                    if st.button('Log Transform', key=f'log_{param}'):
                        transform = st.session_state.transformation_registry.get_numeric_transformation('Log Transform')
                        st.session_state.transformed_data[param] = transform.transform(st.session_state.raw_data, param)
                
                with col3:
                    if st.button(f':red[Reset]', key=f'reset_{param}'):
                        st.session_state.transformed_data[param] = st.session_state.raw_data[param]
                
                # Display histograms
                col0, col1 = st.columns([1,1])

                with col0:
                    fig = px.histogram(st.session_state.raw_data, x=param, 
                                    title=f'Raw distribution of {param}')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col1:
                    fig = px.histogram(st.session_state.transformed_data, x=param,
                                    title=f'Transformed distribution of {param}')
                    st.plotly_chart(fig, use_container_width=True)

                # Display box plots
                col = st.columns([0.5,0.5])
                with col[0]:
                    fig = px.box(st.session_state.raw_data, y=param,
                                title=f'Raw box Plot of {param}')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col[1]:
                    fig = px.box(st.session_state.transformed_data, y=param,
                                title=f'Transformed box Plot of {param}')
                    st.plotly_chart(fig, use_container_width=True)
            
            elif param in st.session_state.raw_object_attrs:
                # Display transformation buttons for categorical attributes
                st.markdown("**Available Transformations:**")
                col_buttons = st.columns([0.33, 0.33, 0.33])
                
                with col_buttons[0]:
                    if st.button('Label Encode', key=f'label_{param}'):
                        transform = st.session_state.transformation_registry.get_categorical_transformation('Label Encoding')
                        st.session_state.transformed_data[param] = transform.transform(st.session_state.raw_data, param)
                
                with col_buttons[1]:
                    if st.button('One-Hot Encode', key=f'onehot_{param}'):
                        transform = st.session_state.transformation_registry.get_categorical_transformation('One-Hot Encoding')
                        encoded_data = transform.transform(st.session_state.raw_data, param)
                        # Add the encoded columns to transformed_data
                        for col in encoded_data.columns:
                            st.session_state.transformed_data[col] = encoded_data[col]
                        # Remove the original column
                        st.session_state.transformed_data = st.session_state.transformed_data.drop(columns=[param])
                
                # Reset button
                with col_buttons[2]:
                    if st.button(':red[Reset]', key=f'reset_{param}'):
                        # Remove any one-hot encoded columns
                        one_hot_cols = [col for col in st.session_state.transformed_data.columns if col.startswith(f"{param}_")]
                        st.session_state.transformed_data = st.session_state.transformed_data.drop(columns=one_hot_cols)
                        # Restore original column
                        st.session_state.transformed_data[param] = st.session_state.raw_data[param]
                
                # Display original distribution

                col = st.columns([0.5,0.5])

                with col[0]:
                    value_counts = st.session_state.raw_data[param].value_counts()
                    fig = px.bar(x=value_counts.index, 
                            y=value_counts.values,
                            title=f'Distribution of {param}',
                            labels={'x': param, 'y': 'Count'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col[1]:
                    value_counts = st.session_state.transformed_data[param].value_counts()
                    fig = px.bar(x=value_counts.index, 
                            y=value_counts.values,
                            title=f'Transformed Distribution of {param}',
                            labels={'x': param, 'y': 'Count'})
                    st.plotly_chart(fig, use_container_width=True)

                # Display top 10 values

                col = st.columns([0.5,0.5])

                with col[0]:
                    st.markdown(f"#### Top 10 Values for {param}")
                    top_10 = value_counts.head(10).reset_index()
                    top_10.columns = [param, 'Count']
                    st.dataframe(top_10, use_container_width=True)

                with col[1]:
                    st.write('TBD')
