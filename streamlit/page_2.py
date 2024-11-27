import streamlit as st 

if st.session_state.raw_data is None: 
    st.markdown('Data has not been selected yet asshole')

else:
    st.markdown('Data has been selected asshole')