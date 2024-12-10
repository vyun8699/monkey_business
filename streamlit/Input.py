import streamlit as st
import pandas as pd
import plotly.express as px
from src.functions import get_numeric_columns, get_object_columns


st.markdown("## :red[File Upload]")

#Prompt user to upload data and choose class attribute
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

#assign variables to session_states
if uploaded_file is not None:
    st.session_state.upload_toggle = uploaded_file.name
    st.session_state.raw_data = pd.read_csv(uploaded_file)
    st.session_state.available_columns = list(st.session_state.raw_data.columns)
    st.session_state.raw_numeric_attrs = get_numeric_columns(st.session_state.raw_data)
    st.session_state.raw_object_attrs = get_object_columns(st.session_state.raw_data)

if st.session_state.upload_toggle:

    # Uploaded data
    st.markdown(f'Uploaded file: :orange[{st.session_state.upload_toggle}]')

    # Show data
    st.write(st.session_state.raw_data)