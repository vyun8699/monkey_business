import streamlit as st
import pandas as pd
from src.functions import log_change, get_numeric_columns, get_object_columns, calculate_numeric_stats, calculate_object_stats
import plotly.express as px

#title
st.markdown("## :red[Data Dashboard]")

#summary
st.markdown('### :blue[Key summary]')
    
if st.session_state.upload_toggle:
    data = st.session_state.raw_data
    

    # Check nulls
    null_cols = data.columns[data.isnull().any()].tolist()
    if null_cols:
        st.write(f"⚠️ Found null values in columns: :orange['{', '.join(null_cols)}']")
    
    # Check duplicates
    duplicate_count = data.duplicated().sum()
    if duplicate_count > 0:
        st.write(f"⚠️ Found duplicate rows: :orange[{duplicate_count} duplicates ({(duplicate_count/len(data)*100):.1f}%)]")
    
    # Check for high cardinality
    for col in data.select_dtypes(include=['object']).columns:
        unique_pct = (data[col].nunique() / len(data)) * 100
        if unique_pct > 50:
            st.write(f"⚠️ Found high cardinality: :orange['{col}'({unique_pct:.1f}%)]")
    
    # Check for high percentage of zeros in numeric columns
    for col in data.select_dtypes(include=['int64', 'float64']).columns:
        zero_pct = (data[col] == 0).mean() * 100
        if zero_pct > 50:
            st.write(f"⚠️ Found high proportion of zeroes: :orange['{col}' ({zero_pct:.1f}%)]")
    
    # Check for outliers
    for col in data.select_dtypes(include=['int64', 'float64']).columns:
        Q1 = data[col].quantile(0.25)
        Q3 = data[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = data[(data[col] < Q1 - 1.5 * IQR) | (data[col] > Q3 + 1.5 * IQR)][col]
        if len(outliers) > 0:
            outlier_pct = (len(outliers) / len(data)) * 100
            if outlier_pct > 10:
                st.write(f"⚠️ High number of outliers in :orange['{col}' ({outlier_pct:.1f}%)]")
            else:
                st.write(f"⚠️ Small number of outliers in :orange['{col}' ({outlier_pct:.1f}%)]")

    with st.expander("See details"):
        # Identify numeric and object attributes
        st.session_state.raw_numeric_attrs = get_numeric_columns(st.session_state.raw_data)
        st.session_state.raw_object_attrs = get_object_columns(st.session_state.raw_data)

        st.markdown('### :blue[Attributes]')
        
        #numerics
        st.write("Numeric attributes:")
        if len(st.session_state.raw_numeric_attrs) > 0:
            # Display numeric statistics table
            stats_df = calculate_numeric_stats(st.session_state.raw_data, st.session_state.raw_numeric_attrs)
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("No numeric attributes available for analysis.")
        
        #objects
        st.write("Categorical attributes:")
        if len(st.session_state.raw_object_attrs) > 0:
            # Display object statistics table
            stats_df = calculate_object_stats(st.session_state.raw_data, st.session_state.raw_object_attrs)
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("No categorical attributes available for analysis.")


        data = st.session_state.raw_data

        st.markdown('### :blue[Count of Nulls]')

        st.markdown('Null table')
        # Create table of feature name, null count, and percentage of nulls
        null_counts = data.isnull().sum()
        null_percentages = (null_counts / len(data)) * 100
        null_df = pd.DataFrame({
            'Feature': null_counts.index,
            'Null Count': null_counts.values,
            'Null Percentage': null_percentages.values.round(2)
        })
        st.dataframe(null_df)
            
        st.markdown('### :blue[Count of Duplicates]')
        # Check for duplicate values
        duplicate_count = data.duplicated().sum()
        duplicate_percentage = (duplicate_count / len(data)) * 100
        

        if duplicate_count > 0:
            
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
            
            
            # Show summary of duplicate groups
            duplicate_groups = duplicates_sorted.groupby('Duplicate_Group').size().value_counts()
            st.write(f"{duplicate_count} duplicated groups ({duplicate_percentage:.2f}% of the dataset).")
            for count, groups in duplicate_groups.items():
                st.write(f"- Found {groups} entries of {count} identical rows each.")

            # Display duplicates with their group numbers
            st.dataframe(
                duplicates_sorted.style.apply(
                    lambda x: ['background: #ffcdd2' if i % 2 == 0 else 'background: #ef9a9a' 
                            for i in range(len(x))], 
                    axis=0
                )
            )


        st.markdown('### :blue[Count of Unique Values]')


        st.markdown('Unique value table')
        # Create table of feature name, unique count, and percentage of unique values
        unique_counts = data.nunique()
        unique_percentages = (unique_counts / len(data)) * 100
        unique_df = pd.DataFrame({
            'Feature': unique_counts.index,
            'Unique Count': unique_counts.values,
            'Unique Percentage': unique_percentages.values.round(2)
        })
        st.dataframe(unique_df)

        st.markdown('### :blue[Count of Outliers]')
        # Check for outliers using IQR method, only for numeric values
        numeric_cols = data.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            outlier_stats = []
            for col in numeric_cols:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)][col]
                outlier_percentage = (len(outliers) / len(data)) * 100
                
                outlier_stats.append({
                    'Feature': col,
                    'Outlier Count': len(outliers),
                    'Outlier Percentage': round(outlier_percentage, 2)
                })
            
            outlier_df = pd.DataFrame(outlier_stats)
            st.dataframe(outlier_df)

        st.markdown('### :blue[Count of Zeros]')
        # Check for zeros, only for numeric values
        if len(numeric_cols) > 0:
            zero_stats = []
            for col in numeric_cols:
                zero_count = (data[col] == 0).sum()
                zero_percentage = (zero_count / len(data)) * 100
                
                zero_stats.append({
                    'Feature': col,
                    'Zero Count': zero_count,
                    'Zero Percentage': round(zero_percentage, 2)
                })
            
            zero_df = pd.DataFrame(zero_stats)
            st.dataframe(zero_df)

st.markdown('---')

# Feature exploration section
selected_feature = st.selectbox(
    "Choose feature to explore", 
    st.session_state.available_columns
)

data = st.session_state.raw_data

if selected_feature in st.session_state.raw_numeric_attrs:

    st.markdown('### :blue[Feature Overview and Distribution]')
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

    fig = px.histogram(data, x=selected_feature, marginal ='box', hover_data = data.columns)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('---')

if selected_feature in st.session_state.raw_object_attrs:
    st.markdown('### :blue[Feature Overview]')
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
        
    st.markdown('---')
        
    st.markdown('### :blue[Feature Distribution]')
    value_counts = st.session_state.raw_data[selected_feature].value_counts()
    fig = px.bar(x=value_counts.index, 
            y=value_counts.values,
            title=f'Distribution of {selected_feature}',
            labels={'x': selected_feature, 'y': 'Count'})
    st.plotly_chart(fig, use_container_width=True)



