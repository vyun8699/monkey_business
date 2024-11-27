import streamlit as st
import pandas as pd
from src.functions import log_change, get_numeric_columns, get_object_columns, calculate_numeric_stats, calculate_object_stats

#title
st.title(":red[Data Preprocessing Dashboard]")
st.markdown(':blue[Please upload your data and choose target class attribute]')


#initialize session states to be used across pages
if 'upload_toggle' not in st.session_state:
    st.session_state.upload_toggle = None
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = None
if 'raw_numeric_attrs' not in st.session_state:
    st.session_state.raw_numeric_attrs = None
if 'raw_object_attrs' not in st.session_state:
    st.session_state.raw_object_attrs = None
if 'class_attr' not in st.session_state:
    st.session_state.class_attr = None
if 'change_log' not in st.session_state:
    st.session_state.change_log = []
if 'available_columns' not in st.session_state:
    st.session_state.available_columns = []

#Prompt user to upload data and choose class attribute
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

#assign variables to session_states
if uploaded_file is not None:
    st.session_state.upload_toggle = uploaded_file.name
    st.session_state.raw_data = pd.read_csv(uploaded_file)
    st.session_state.available_columns = list(st.session_state.raw_data.columns)

# Show selectbox if we have columns available (either from current upload or previous session)
if st.session_state.available_columns:
    # Get current value from session state or default to first column
    current_value = st.session_state.class_attr if st.session_state.class_attr in st.session_state.available_columns else st.session_state.available_columns[0]
    
    selected_class = st.selectbox(
        "Define your class attribute", 
        st.session_state.available_columns,
        index=st.session_state.available_columns.index(current_value)
    )
    
    # Update session state if selection changes
    if selected_class != st.session_state.class_attr:
        st.session_state.class_attr = selected_class
        log_change('class_attr')

st.markdown('---')

#load data as df if file is uploaded
if st.session_state.upload_toggle:
    # Identify numeric and object attributes
    st.session_state.raw_numeric_attrs = get_numeric_columns(st.session_state.raw_data)
    st.session_state.raw_object_attrs = get_object_columns(st.session_state.raw_data)

    # Uploaded data
    st.markdown(f'#### Uploaded file: {st.session_state.upload_toggle}')
    
    # chosen class
    st.markdown(f'Class attribute: {st.session_state.class_attr}')
    
    #numerics
    st.write("Numeric attributes are shown below:")
    if len(st.session_state.raw_numeric_attrs) > 0:
        # Display numeric statistics table
        stats_df = calculate_numeric_stats(st.session_state.raw_data, st.session_state.raw_numeric_attrs)
        st.dataframe(stats_df, use_container_width=True)
    else:
        st.info("No numeric attributes available for analysis.")
    
    #objects
    st.write("Object attributes are shown below:")

    if len(st.session_state.raw_object_attrs) > 0:
        # Display object statistics table
        stats_df = calculate_object_stats(st.session_state.raw_data, st.session_state.raw_object_attrs)
        st.dataframe(stats_df, use_container_width=True)
    else:
        st.info("No categorical attributes available for analysis.")

    st.write("Top 10 rows of the uploaded data:")
    st.write(st.session_state.raw_data.head(10))
