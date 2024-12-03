import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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


st.markdown("## :red[Feature details]")

if st.session_state.raw_data is None: 
    st.markdown('Data has not been selected yet')

else:
    # Initialize transformed data in session state if not exists
    if 'transformed_data' not in st.session_state:
        st.session_state.transformed_data = st.session_state.raw_data.copy()
    
    # Initialize change tracking variables in session state
    if 'last_operation_stats' not in st.session_state:
        st.session_state.last_operation_stats = {
            'rows_removed': 0,
            'cols_removed': 0,
            'new_rows': 0,
            'new_cols': 0
        }
    
    # Null handling section
    st.markdown("### :blue[Null Value Handling]")
    
    # Display current data size
    current_rows, current_cols = st.session_state.raw_data.shape
    st.markdown(f"**Current Data Size:** :orange[{current_rows} rows × {current_cols} columns]")
    
    # Display null value summary
    data = st.session_state.raw_data
    null_counts = data.isnull().sum()
    columns_with_nulls = null_counts[null_counts > 0]
    
    # Check for null values immediately and return success message if none found
    if len(columns_with_nulls) == 0:
        st.success("No null values found in the dataset!")
    else:
        st.markdown("**Columns with null values:**")
        null_summary = pd.DataFrame({
            'Column': columns_with_nulls.index,
            'Null Count': columns_with_nulls.values,
            'Null Percentage': (columns_with_nulls.values / len(st.session_state.raw_data) * 100).round(2)
        })
        st.dataframe(null_summary)
        
        # Create color map of null values
        fig = px.imshow(data.isnull(), height = 350, aspect='auto', origin='lower', title = 'Null Values Heatmap')
        st.plotly_chart(fig, use_container_width=True)
    
        # Interactive Null Analysis Section
        st.markdown("### :blue[Interactive Null Analysis]")
        
        # Get columns that have null values
        columns_with_nulls = [col for col in st.session_state.available_columns 
                            if st.session_state.raw_data[col].isnull().sum() > 0]
        
        if not columns_with_nulls:
            st.success("No columns contain null values in the dataset!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                null_param = st.selectbox(
                    "Select parameter to analyze nulls",
                    columns_with_nulls,
                    key="null_param"
                )
            with col2:
                x_axis_param = st.selectbox(
                    "Select parameter for X-axis",
                    [col for col in st.session_state.available_columns if col != null_param],
                    key="x_axis_param"
                )
            
            # Calculate null counts grouped by x-axis parameter
            null_counts = st.session_state.raw_data.groupby(x_axis_param)[null_param].apply(
                lambda x: x.isnull().sum()
            ).reset_index()
            null_counts.columns = [x_axis_param, 'Null Count']
            
            # Create interactive bar chart
            fig = px.bar(
                null_counts,
                x=x_axis_param,
                y='Null Count',
                title=f'Null Values in {null_param} by {x_axis_param}',
                labels={'Null Count': f'Number of Nulls in {null_param}'}
            )
            fig.update_layout(
                xaxis_title=x_axis_param,
                yaxis_title=f'Number of Nulls in {null_param}',
                bargap=0.2
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display summary statistics
            total_nulls = null_counts['Null Count'].sum()
            max_nulls = null_counts['Null Count'].max()
            max_category = null_counts.loc[null_counts['Null Count'].idxmax(), x_axis_param]
            
            st.markdown(f"""
            **Summary Statistics:**
            - Total null values in {null_param}: {total_nulls}
            - Maximum null values: {max_nulls} (in {x_axis_param} = {max_category})
            - Average null values per category: {(total_nulls / len(null_counts)):.2f}
            """)
        
        st.markdown("---")
        
        with st.container(border=True):
            st.markdown("**Null Removal Options**")
            
            removal_type = st.radio(
                "Choose removal method:",
                ["Remove Rows with Nulls", "Remove Columns with Nulls"],
                key="null_removal_type"
            )
            
            if removal_type == "Remove Rows with Nulls":
                threshold = st.slider(
                    "Remove rows with null values in at least X% of columns:",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=5,
                    key="null_row_threshold"
                )
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("Remove Null Rows"):
                        # Calculate threshold in terms of number of columns
                        min_non_null = int(np.ceil(st.session_state.raw_data.shape[1] * (1 - threshold/100)))
                        # Remove rows with more nulls than threshold
                        st.session_state.transformed_data = st.session_state.raw_data.dropna(
                            thresh=min_non_null
                        )
                        
                        # Calculate and store changes in session state
                        new_rows, new_cols = st.session_state.transformed_data.shape
                        st.session_state.last_operation_stats = {
                            'rows_removed': current_rows - new_rows,
                            'cols_removed': 0,
                            'new_rows': new_rows,
                            'new_cols': new_cols
                        }
                        
                        # Display changes
                        st.markdown(f"""
                        **Changes to be made:**
                        - Rows removed: {st.session_state.last_operation_stats['rows_removed']}
                        - New data size: {new_rows} rows × {new_cols} columns
                        - Percentage reduction: {(st.session_state.last_operation_stats['rows_removed']/current_rows * 100):.2f}% of rows
                        """)
                
                with col2:
                    if st.button(":green[Save]", key="save_null_rows"):
                        # Log the changes
                        if 'change_log' not in st.session_state:
                            st.session_state.change_log = []
                        
                        st.session_state.change_log.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'action': 'Remove Null Rows',
                            'threshold': f"{threshold}%",
                            'rows_removed': st.session_state.last_operation_stats['rows_removed'],
                            'new_size': f"{st.session_state.last_operation_stats['new_rows']} rows × {st.session_state.last_operation_stats['new_cols']} columns"
                        })
                        
                        # Update raw data
                        st.session_state.raw_data = st.session_state.transformed_data.copy()
                        st.success("Changes have been saved and logged.")
            
            else:  # Remove Columns with Nulls
                threshold = st.slider(
                    "Remove columns with null values in at least X% of rows:",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=5,
                    key="null_col_threshold"
                )
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("Remove Null Columns"):
                        # Calculate null percentages for each column
                        null_percentages = (st.session_state.raw_data.isnull().sum() / len(st.session_state.raw_data) * 100)
                        # Get columns to drop
                        cols_to_drop = null_percentages[null_percentages >= threshold].index
                        # Remove columns
                        st.session_state.transformed_data = st.session_state.raw_data.drop(columns=cols_to_drop)
                        
                        # Calculate and store changes in session state
                        new_rows, new_cols = st.session_state.transformed_data.shape
                        st.session_state.last_operation_stats = {
                            'rows_removed': 0,
                            'cols_removed': current_cols - new_cols,
                            'new_rows': new_rows,
                            'new_cols': new_cols
                        }
                        
                        # Display changes
                        st.markdown(f"""
                        **Changes to be made:**
                        - Columns removed: {st.session_state.last_operation_stats['cols_removed']}
                        - New data size: {new_rows} rows × {new_cols} columns
                        - Percentage reduction: {(st.session_state.last_operation_stats['cols_removed']/current_cols * 100):.2f}% of columns
                        """)
                
                with col2:
                    if st.button(":green[Save]", key="save_null_cols"):
                        # Log the changes
                        if 'change_log' not in st.session_state:
                            st.session_state.change_log = []
                        
                        st.session_state.change_log.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'action': 'Remove Null Columns',
                            'threshold': f"{threshold}%",
                            'columns_removed': st.session_state.last_operation_stats['cols_removed'],
                            'new_size': f"{st.session_state.last_operation_stats['new_rows']} rows × {st.session_state.last_operation_stats['new_cols']} columns"
                        })
                        
                        # Update raw data
                        st.session_state.raw_data = st.session_state.transformed_data.copy()
                        # Update available columns
                        st.session_state.available_columns = list(st.session_state.raw_data.columns)
                        st.session_state.raw_numeric_attrs = list(st.session_state.raw_data.select_dtypes(include=['int64', 'float64']).columns)
                        st.session_state.raw_object_attrs = list(st.session_state.raw_data.select_dtypes(include=['object', 'category']).columns)
                        st.success("Changes have been saved and logged.")
    
    # Duplicate handling section
    st.markdown("### :blue[Duplicate Handling]")
    
    # Get duplicate information
    duplicate_count = data.duplicated().sum()
    duplicate_percentage = (duplicate_count / len(data)) * 100
    
    st.markdown(f"**Total duplicate rows:** :orange[{duplicate_count} ({duplicate_percentage:.2f}%)]")
    
    # Check for duplicates immediately and return success message if none found
    if duplicate_count == 0:
        st.success("No duplicate rows found in the dataset!")
    else:
        # Get duplicate rows
        duplicates = data[data.duplicated(keep=False)]
        # Sort duplicates to group them together
        duplicates_sorted = duplicates.sort_values(by=list(data.columns))
        # Add a group identifier for each set of duplicates
        duplicates_sorted['Duplicate_Group'] = (
            (duplicates_sorted != duplicates_sorted.shift())
            .any(axis=1)
            .cumsum()
        )
        
        # Show duplicate groups summary
        duplicate_groups = duplicates_sorted.groupby('Duplicate_Group').size().value_counts()
        st.markdown("**Summary of duplicate groups:**")
        for count, groups in duplicate_groups.items():
            st.markdown(f"- Found :orange[{groups} groups] with :orange[{count} identical rows] each")
        
        # Display duplicates with styling
        st.markdown("**Duplicate rows with their original entries:**")
        styled_duplicates = duplicates_sorted.style.apply(
            lambda x: ['background: #ffcdd2' if i % 2 == 0 else 'background: #ef9a9a' 
                     for i in range(len(x))], 
            axis=0
        )
        st.dataframe(styled_duplicates)
        
        # Interactive Duplicate Analysis
        st.markdown("### :blue[Interactive Duplicate Analysis]")
        
        # Let user select columns to consider for duplicates
        st.markdown("**Select columns to consider for duplicate analysis:**")
        selected_columns = st.multiselect(
            "Choose columns",
            st.session_state.available_columns,
            default=st.session_state.available_columns,
            key="duplicate_columns"
        )
        
        if selected_columns:
            subset_duplicates = data.duplicated(subset=selected_columns, keep=False)
            subset_duplicate_count = subset_duplicates.sum()
            subset_duplicate_percentage = (subset_duplicate_count / len(data)) * 100
            
            st.markdown(f"""
            **Duplicate analysis for selected columns:**
            - Duplicate rows: :orange[{subset_duplicate_count}]
            - Percentage: :orange[{subset_duplicate_percentage:.2f}%]
            """)
            
            if subset_duplicate_count > 0:
                subset_duplicates_df = data[subset_duplicates].sort_values(by=selected_columns)
                st.dataframe(subset_duplicates_df)
        
        st.markdown("---")
        
        # Duplicate Removal Options
        with st.container(border=True):
            st.markdown("**Duplicate Removal Options**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                keep_option = st.radio(
                    "Which duplicate to keep:",
                    ["First", "Last", "None"],
                    key="duplicate_keep_option"
                )
            
            with col2:
                subset_cols = st.multiselect(
                    "Consider only these columns for duplicates:",
                    st.session_state.available_columns,
                    default=None,
                    key="duplicate_subset_cols"
                )
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("Remove Duplicates"):
                    # Remove duplicates based on selected options
                    st.session_state.transformed_data = st.session_state.raw_data.drop_duplicates(
                        subset=subset_cols if subset_cols else None,
                        keep=keep_option.lower() if keep_option != "None" else False
                    )
                    
                    # Calculate and store changes in session state
                    new_rows, new_cols = st.session_state.transformed_data.shape
                    st.session_state.last_operation_stats = {
                        'rows_removed': current_rows - new_rows,
                        'cols_removed': 0,
                        'new_rows': new_rows,
                        'new_cols': new_cols
                    }
                    
                    # Display changes
                    st.markdown(f"""
                    **Changes to be made:**
                    - Rows removed: {st.session_state.last_operation_stats['rows_removed']}
                    - New data size: {new_rows} rows × {new_cols} columns
                    - Percentage reduction: {(st.session_state.last_operation_stats['rows_removed']/current_rows * 100):.2f}% of rows
                    """)
            
            with col2:
                if st.button(":green[Save]", key="save_duplicates"):
                    # Log the changes
                    if 'change_log' not in st.session_state:
                        st.session_state.change_log = []
                    
                    st.session_state.change_log.append({
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'action': 'Remove Duplicates',
                        'keep_option': keep_option,
                        'subset_columns': subset_cols if subset_cols else 'All columns',
                        'rows_removed': st.session_state.last_operation_stats['rows_removed'],
                        'new_size': f"{st.session_state.last_operation_stats['new_rows']} rows × {st.session_state.last_operation_stats['new_cols']} columns"
                    })
                    
                    # Update raw data
                    st.session_state.raw_data = st.session_state.transformed_data.copy()
                    st.success("Changes have been saved and logged.")
