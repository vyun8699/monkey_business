import streamlit as st
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
        padding-top: 1rem;
        padding-bottom: 2rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("## :red[Export Data]")

if st.session_state.raw_data is None:
    st.markdown('Data has not been selected yet')
else:
    st.markdown("### :blue[Current Data Overview]")
    
    # Display basic information about the transformed dataset
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Dataset Shape:**")
        st.write(f"Rows: {st.session_state.raw_data.shape[0]}")
        st.write(f"Columns: {st.session_state.raw_data.shape[1]}")
    
    with col2:
        st.markdown("**Column Types:**")
        st.write(f"Numeric: {len(st.session_state.raw_numeric_attrs)}")
        st.write(f"Categorical: {len(st.session_state.raw_object_attrs)}")

    # Export section
    st.markdown("### :blue[Export Options]")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export Transformed Data**")
        export_filename = st.text_input("Enter filename for transformed data", "transformed_data.csv")
        
        if st.button("Export Data"):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                data_path = f"data/{timestamp}_{export_filename}"
                st.session_state.raw_data.to_csv(data_path, index=False)
                st.success(f"Data successfully exported to {data_path}")
            except Exception as e:
                st.error(f"Error exporting data: {str(e)}")
    
    with col2:
        st.markdown("**Export Transformation Log**")
        log_filename = st.text_input("Enter filename for transformation log", "transformation_log.json")
        
        if st.button("Export Log"):
            try:
                if 'change_log' in st.session_state:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_path = f"data/{timestamp}_{log_filename}"
                    
                    # Add final export entry to log
                    st.session_state.change_log.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'action': 'Final Export',
                        'data_shape': st.session_state.raw_data.shape,
                        'columns': list(st.session_state.raw_data.columns)
                    })
                    
                    # Save log to file
                    with open(log_path, 'w') as f:
                        json.dump(st.session_state.change_log, f, indent=2)
                    st.success(f"Transformation log exported to {log_path}")
                else:
                    st.warning("No transformation log available")
            except Exception as e:
                st.error(f"Error exporting log: {str(e)}")

    # Log Preview
    if 'change_log' in st.session_state and st.session_state.change_log:
        with st.expander(":blue[See change log]"):
            st.json(st.session_state.change_log)  # Show last 5 log entries
