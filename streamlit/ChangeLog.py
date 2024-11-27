import streamlit as st

st.write("Change Log:")

for i in st.session_state.change_log:
    st.write(i)