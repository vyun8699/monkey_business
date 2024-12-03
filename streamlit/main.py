#adjusted from @wbjmattingly - https://www.youtube.com/watch?v=s86jz9qVeWA&t=158s

#imports
import streamlit as st

Input = st.Page('Input.py', title='0. Input')
Dashboard = st.Page('Dashboard.py', title='1. Dashboard')
Balance = st.Page('null.py', title = '2. Nulls & Duplicates')
Visualization = st.Page('Transformation.py', title = '3. Transformations')
Output = st.Page('output.py', title = '4. Output & Logs')

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

pg = st.navigation([Input, Dashboard, Balance, Visualization, Output])

st.set_page_config(page_title='No-code EDA', page_icon=':blue:')
pg.run()