# sql_app.py

import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import plotly.express as px

# --- 1. Configuration ---
DB_FILE = "vahan_data.db" # Name of your SQLite database file

# --- 2. Data Loading from Database and Preprocessing ---
@st.cache_data # Cache data to avoid reloading on every rerun
def load_data_from_db():
    """
    Connects to the SQLite database and loads data from both tables.
    Ensures correct data types for calculations.
    """
    if not os.path.exists(DB_FILE):
        st.error(f"Error: The database file '{DB_FILE}' was not found. Please run 'sql_scraper.py' or 'migrate_csv_to_sql.py' first.")
        st.stop()

    conn = sqlite3.connect(DB_FILE)
    
    # Load annual data
    try:
        calendar_data_combined = pd.read_sql_query("SELECT * FROM annual_registrations", conn)
        # Ensure correct numeric types for annual data
        calendar_data_combined['Year'] = pd.to_numeric(calendar_data_combined['Year'], errors='coerce').fillna(0).astype(int)
        calendar_data_combined['Registrations'] = pd.to_numeric(calendar_data_combined['Registrations'], errors='coerce').fillna(0)
    except pd.io.sql.DatabaseError:
        st.warning(f"Table 'annual_registrations' not found in {DB_FILE}. Ensure scraper has completed successfully.")
        calendar_data_combined = pd.DataFrame()

    # Load monthly data
    try:
        monthly_data_combined = pd.read_sql_query("SELECT * FROM monthly_registrations", conn)
        # Ensure correct numeric types for monthly data
        monthly_data_combined['Year'] = pd.to_numeric(monthly_data_combined['Year'], errors='coerce').fillna(0).astype(int)
        monthly_data_combined['MonthlyRegistrations'] = pd.to_numeric(monthly_data_combined['MonthlyRegistrations'], errors='coerce').fillna(0)

        # Reconstruct 'Date' column for QoQ calculation
        month_to_num = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        if 'Month' in monthly_data_combined.columns and 'Year' in monthly_data_combined.columns:
            monthly_data_combined['MonthNum'] = monthly_data_combined['Month'].map(month_to_num)
            # Combine Year and MonthNum to create a valid date string, then convert to datetime
            monthly_data_combined['Date'] = pd.to_datetime(
                monthly_data_combined['Year'].astype(str) + '-' + 
                monthly_data_combined['MonthNum'].astype(str) + '-01', 
                errors='coerce'
            )
            monthly_data_combined.dropna(subset=['Date'], inplace=True)
            monthly_data_combined.drop(columns=['MonthNum'], inplace=True, errors='ignore') # Drop temporary MonthNum
    except pd.io.sql.DatabaseError:
        st.warning(f"Table 'monthly_registrations' not found in {DB_FILE}. Ensure scraper has completed successfully.")
        monthly_data_combined = pd.DataFrame()

    conn.close()
    
    # The map_vehicle_category function should now be applied here
    # to the loaded dataframes, not during migration.
    
    # We will first add a new column 'MappedName' to store the grouped category.
    # We'll use this new column for filtering and analysis when the user selects 'Vehicle Category'.
    
    # Apply category mapping for 'Vehicle Category' rows
    if not calendar_data_combined.empty and 'Name' in calendar_data_combined.columns:
        calendar_data_combined.loc[calendar_data_combined['DataType'] == 'Vehicle Category', 'MappedName'] = calendar_data_combined[calendar_data_combined['DataType'] == 'Vehicle Category']['Name'].apply(map_vehicle_category)
        # Correcting the FutureWarning by using re-assignment
        calendar_data_combined['MappedName'] = calendar_data_combined['MappedName'].fillna(calendar_data_combined['Name'])
    
    if not monthly_data_combined.empty and 'Name' in monthly_data_combined.columns:
        monthly_data_combined.loc[monthly_data_combined['DataType'] == 'Vehicle Category', 'MappedName'] = monthly_data_combined[monthly_data_combined['DataType'] == 'Vehicle Category']['Name'].apply(map_vehicle_category)
        # Correcting the FutureWarning by using re-assignment
        monthly_data_combined['MappedName'] = monthly_data_combined['MappedName'].fillna(monthly_data_combined['Name'])


    return calendar_data_combined, monthly_data_combined

# --- 3. Vehicle Category Mapping ---
def map_vehicle_category(category_name):
    """
    Maps detailed vehicle category names to broader 2W, 3W, or 4W groups.
    """
    category_name = str(category_name).strip().upper()
    
    # Check for two-wheelers
    if 'TWO WHEELER' in category_name:
        return '2W'
    
    # Check for three-wheelers
    if 'THREE WHEELER' in category_name:
        return '3W'
    
    # Check for four-wheelers and other heavy vehicles
    if any(keyword in category_name for keyword in [
        'FOUR WHEELER', 'LIGHT MOTOR VEHICLE', 'MEDIUM MOTOR VEHICLE',
        'HEAVY MOTOR VEHICLE', 'GOODS VEHICLE', 'PASSENGER VEHICLE',
        'BUS', 'TRAC', 'EARTH MOVING', 'DUMPER', 'CRANE'
    ]):
        return '4W'
        
    return 'Other'

# --- 4. Growth Analysis Functions ---
def calculate_yoy_growth(df_annual):
    """
    Calculates Year-over-Year (YoY) growth for registrations.
    Expects a DataFrame with 'Name' or 'MappedName', 'Year', and 'Registrations' columns.
    """
    # Use 'MappedName' for grouping if it exists, otherwise use 'Name'
    group_col = 'MappedName' if 'MappedName' in df_annual.columns else 'Name'
    if df_annual.empty or 'Year' not in df_annual.columns or 'Registrations' not in df_annual.columns or group_col not in df_annual.columns:
        return pd.DataFrame()

    # Aggregate registrations by the grouping column and year
    df_annual_grouped = df_annual.groupby([group_col, 'Year'])['Registrations'].sum().reset_index()

    # Ensure registrations are numeric and sort
    df_annual_grouped['Registrations'] = pd.to_numeric(df_annual_grouped['Registrations'], errors='coerce').fillna(0)
    df_annual_sorted = df_annual_grouped.sort_values(by=[group_col, 'Year']).copy()
    
    # Calculate previous year's registrations using shift
    df_annual_sorted['PrevYearRegistrations'] = df_annual_sorted.groupby([group_col])['Registrations'].shift(1)
    
    # Calculate YoY Growth and ensure the resulting column is a nullable float type
    yoy_series = ((df_annual_sorted['Registrations'] - df_annual_sorted['PrevYearRegistrations']) / df_annual_sorted['PrevYearRegistrations']) * 100
    df_annual_sorted['YoYGrowth'] = pd.to_numeric(yoy_series, errors='coerce').replace([float('inf'), -float('inf')], pd.NA).round(2)
    
    return df_annual_sorted

def calculate_qoq_growth(df_monthly):
    """
    Calculates Quarter-over-Quarter (QoQ) growth for registrations.
    Expects a DataFrame with 'Name' or 'MappedName', 'Date', and 'MonthlyRegistrations' columns.
    """
    # Use 'MappedName' for grouping if it exists, otherwise use 'Name'
    group_col = 'MappedName' if 'MappedName' in df_monthly.columns else 'Name'
    if df_monthly.empty or 'Date' not in df_monthly.columns or 'MonthlyRegistrations' not in df_monthly.columns or group_col not in df_monthly.columns:
        return pd.DataFrame()

    # Ensure monthly registrations are numeric
    df_monthly['MonthlyRegistrations'] = pd.to_numeric(df_monthly['MonthlyRegistrations'], errors='coerce').fillna(0)

    # Add Quarter and QuarterYear columns
    df_monthly['Quarter'] = df_monthly['Date'].dt.quarter
    df_monthly['QuarterYear'] = df_monthly['Year'].astype(str) + '-Q' + df_monthly['Quarter'].astype(str)
    
    # Aggregate monthly registrations to quarterly by the grouping column
    df_quarterly = df_monthly.groupby([group_col, 'Year', 'Quarter', 'QuarterYear'])['MonthlyRegistrations'].sum().reset_index()
    df_quarterly.rename(columns={'MonthlyRegistrations': 'QuarterlyRegistrations'}, inplace=True)
    
    # Sort for correct shift calculation
    df_quarterly_sorted = df_quarterly.sort_values(by=[group_col, 'Year', 'Quarter']).copy()
    
    # Calculate previous quarter's registrations using shift
    df_quarterly_sorted['PrevQuarterRegistrations'] = df_quarterly_sorted.groupby([group_col])['QuarterlyRegistrations'].shift(1)
    
    # Calculate QoQ Growth and ensure the resulting column is a nullable float type
    qoq_series = ((df_quarterly_sorted['QuarterlyRegistrations'] - df_quarterly_sorted['PrevQuarterRegistrations']) / df_quarterly_sorted['PrevQuarterRegistrations']) * 100
    df_quarterly_sorted['QoQGrowth'] = pd.to_numeric(qoq_series, errors='coerce').replace([float('inf'), -float('inf')], pd.NA).round(2)
    
    return df_quarterly_sorted

# --- 5. Streamlit Dashboard Main Function ---
def main_dashboard():
    st.set_page_config(layout="wide", page_title="Vehicle Registration Dashboard 🚗")
    st.title("🚗📈 Vehicle Registration Growth Analysis")
    st.markdown("---")
    st.markdown("""
        Welcome to the Vehicle Registration Growth Dashboard!
        This dashboard provides insights into Year-over-Year (YoY) and Quarter-over-Quarter (QoQ) growth
        for vehicle registrations by **Vehicle Category (2W, 3W, 4W)** and **Manufacturer**.
        Use the filters on the sidebar to explore trends.
    """)
    st.markdown("---")

    # Load and preprocess data using the SQL function
    calendar_data, monthly_data = load_data_from_db()

    if calendar_data.empty and monthly_data.empty:
        st.error("No data loaded. Please ensure the database is populated correctly.")
        st.stop()

    # --- Sidebar Filters ---
    st.sidebar.header("⚙️ Dashboard Controls")

    data_type_filter = st.sidebar.radio(
        "Select Data Type:",
        ["Vehicle Category", "Manufacturer"],
        help="Choose to analyze by broad vehicle categories (2W, 3W, 4W) or individual manufacturers."
    )
    st.sidebar.markdown("---")

    growth_type_filter = st.sidebar.radio(
        "Select Growth Metric:",
        ["YoY Growth", "QoQ Growth"],
        help="YoY (Year-over-Year) shows annual growth. QoQ (Quarter-over-Quarter) shows quarterly growth."
    )
    st.sidebar.markdown("---")

    # Dynamic filter for Name (Vehicle Category Group or Manufacturer Name)
    unique_names = []
    if data_type_filter == "Vehicle Category":
        # Use 'MappedName' for the selectbox options
        if not calendar_data.empty:
            unique_names.extend(calendar_data[calendar_data['DataType'] == 'Vehicle Category']['MappedName'].unique())
        if not monthly_data.empty:
            unique_names.extend(monthly_data[monthly_data['DataType'] == 'Vehicle Category']['MappedName'].unique())
    else: # Manufacturer
        if not calendar_data.empty:
            unique_names.extend(calendar_data[calendar_data['DataType'] == 'Manufacturer']['Name'].unique())
        if not monthly_data.empty:
            unique_names.extend(monthly_data[monthly_data['DataType'] == 'Manufacturer']['Name'].unique())
    
    unique_names = sorted(list(set(unique_names)))
    
    if not unique_names:
        st.warning("No names (categories/manufacturers) found in the loaded data for filtering.")
        return

    selected_name = st.sidebar.selectbox(
        f"Select {data_type_filter}:",
        unique_names,
        help=f"Select a specific {data_type_filter.lower()} to view its growth trends."
    )
    st.sidebar.markdown("---")

    # Date Range Selection
    min_year_data = pd.Timestamp.now().year
    max_year_data = pd.Timestamp.now().year
    
    if not calendar_data.empty and 'Year' in calendar_data.columns:
        min_year_data = min(min_year_data, calendar_data['Year'].min())
        max_year_data = max(max_year_data, calendar_data['Year'].max())
    if not monthly_data.empty and 'Year' in monthly_data.columns:
        min_year_data = min(min_year_data, monthly_data['Year'].min())
        max_year_data = max(max_year_data, monthly_data['Year'].max())

    year_range = st.sidebar.slider(
        "Select Year Range:",
        min_value=int(min_year_data),
        max_value=int(max_year_data),
        value=(int(min_year_data), int(max_year_data)),
        help="Adjust the year range to focus on specific periods."
    )
    st.sidebar.markdown("---")

    # --- Display Growth Analysis ---
    st.header(f"📈 {growth_type_filter} for {selected_name}")

    insight_message = ""
    if growth_type_filter == "YoY Growth":
        # Use 'MappedName' for filtering if applicable
        filter_col = 'MappedName' if data_type_filter == "Vehicle Category" else 'Name'
        filtered_annual_data = calendar_data[
            (calendar_data['DataType'] == data_type_filter) &
            (calendar_data[filter_col] == selected_name)
        ].copy()

        yoy_df = calculate_yoy_growth(filtered_annual_data)
        
        if not yoy_df.empty:
            display_yoy_df = yoy_df[
                (yoy_df['Year'] >= year_range[0]) & 
                (yoy_df['Year'] <= year_range[1])
            ]
            
            if not display_yoy_df.empty:
                st.subheader("Year-over-Year Growth Table")
                st.dataframe(display_yoy_df[['Year', 'Registrations', 'PrevYearRegistrations', 'YoYGrowth']].set_index('Year').style.format({"Registrations": "{:,.0f}", "PrevYearRegistrations": "{:,.0f}", "YoYGrowth": "{:.2f}%"}))

                st.subheader("Year-over-Year Growth Trend")
                fig_yoy = px.line(display_yoy_df, 
                                x='Year', 
                                y='YoYGrowth', 
                                title=f"YoY Growth for {selected_name}",
                                labels={'YoYGrowth': 'YoY Growth (%)', 'Year': 'Year'},
                                markers=True)
                fig_yoy.update_traces(mode='lines+markers')
                st.plotly_chart(fig_yoy, use_container_width=True)

                st.info(f"YoY Growth is calculated as ((Current Year Registrations - Previous Year Registrations) / Previous Year Registrations) * 100.")
                
                latest_yoy_growth = display_yoy_df['YoYGrowth'].iloc[-1] if not display_yoy_df.empty else None
                if latest_yoy_growth is not None:
                    trend = "positive" if latest_yoy_growth > 0 else "negative" if latest_yoy_growth < 0 else "stable"
                    insight_message = f"The **{selected_name}** shows a **{trend} YoY growth of {latest_yoy_growth:.2f}%** in the latest available year within the selected range."
                    if trend == "positive":
                        insight_message += " This indicates a strong expansion compared to the previous year."
                    elif trend == "negative":
                        insight_message += " This suggests a contraction in registrations compared to the previous year."
                    else:
                        insight_message += " This indicates a relatively stable registration count compared to the previous year."
                
                if not display_yoy_df.empty and display_yoy_df['YoYGrowth'].max() > 0: # Ensure not empty before max
                    best_year = display_yoy_df.loc[display_yoy_df['YoYGrowth'].idxmax()]
                    insight_message += f"\n\nIts highest YoY growth was **{best_year['YoYGrowth']:.2f}%** in **{int(best_year['Year'])}**."

            else:
                st.info(f"No sufficient data for YoY growth for **{selected_name}** in the selected year range ({year_range[0]}-{year_range[1]}). "
                        f"Ensure at least two consecutive years of data are available for this entity.")
        else:
            st.warning("YoY growth data could not be computed. Please check the raw data and filters.")
    
    elif growth_type_filter == "QoQ Growth":
        # Use 'MappedName' for filtering if applicable
        filter_col = 'MappedName' if data_type_filter == "Vehicle Category" else 'Name'
        filtered_monthly_data = monthly_data[
            (monthly_data['DataType'] == data_type_filter) &
            (monthly_data[filter_col] == selected_name)
        ].copy()

        qoq_df = calculate_qoq_growth(filtered_monthly_data)
        
        if not qoq_df.empty:
            display_qoq_df = qoq_df[
                (qoq_df['Year'] >= year_range[0]) & 
                (qoq_df['Year'] <= year_range[1])
            ].dropna(subset=['QoQGrowth'])
            
            if not display_qoq_df.empty:
                st.subheader("Quarter-over-Quarter Growth Table")
                st.dataframe(display_qoq_df[['QuarterYear', 'QuarterlyRegistrations', 'PrevQuarterRegistrations', 'QoQGrowth']].set_index('QuarterYear').style.format({"QuarterlyRegistrations": "{:,.0f}", "PrevQuarterRegistrations": "{:,.0f}", "QoQGrowth": "{:.2f}%"}))

                st.subheader("Quarter-over-Quarter Growth Trend")
                fig_qoq = px.line(display_qoq_df.sort_values('QuarterYear'), 
                                x='QuarterYear', 
                                y='QoQGrowth', 
                                title=f"QoQ Growth for {selected_name}",
                                labels={'QoQGrowth': 'QoQ Growth (%)', 'QuarterYear': 'Quarter'},
                                markers=True)
                fig_qoq.update_traces(mode='lines+markers')
                st.plotly_chart(fig_qoq, use_container_width=True)

                st.info(f"QoQ Growth is calculated as ((Current Quarter Registrations - Previous Quarter Registrations) / Previous Quarter Registrations) * 100.")

                latest_qoq_growth = display_qoq_df['QoQGrowth'].iloc[-1] if not display_qoq_df.empty else None
                if latest_qoq_growth is not None:
                    trend = "positive" if latest_qoq_growth > 0 else "negative" if latest_qoq_growth < 0 else "stable"
                    insight_message = f"The **{selected_name}** shows a **{trend} QoQ growth of {latest_qoq_growth:.2f}%** in the latest available quarter within the selected range."
                    if trend == "positive":
                        insight_message += " This indicates healthy sequential growth."
                    elif trend == "negative":
                        insight_message += " This suggests a slowdown in registrations compared to the previous quarter."
                    else:
                        insight_message += " This indicates a relatively stable registration count compared to the previous quarter."
                
                if not display_qoq_df.empty and display_qoq_df['QoQGrowth'].max() > 0: # Ensure not empty before max
                    best_quarter = display_qoq_df.loc[display_qoq_df['QoQGrowth'].idxmax()]
                    insight_message += f"\n\nIts highest QoQ growth was **{best_quarter['QoQGrowth']:.2f}%** in **{best_quarter['QuarterYear']}**."

            else:
                st.info(f"No sufficient data for QoQ growth for **{selected_name}** in the selected year range ({year_range[0]}-{year_range[1]}). "
                        f"Ensure at least two consecutive quarters of data are available for this entity.")
        else:
            st.warning("QoQ growth data could not be computed. Please check the raw data and filters.")

    st.markdown("---")
    st.subheader("💡 Key Insights")
    if insight_message:
        st.write(insight_message)
    else:
        st.write("Select a data type, entity, and growth metric to generate insights. Ensure sufficient data is available for the selected period.")

    st.markdown("---")
    st.subheader("Dataset Previews")
    col1, col2 = st.columns(2)
    with col1:
        st.write("#### Annual Data (for YoY)")
        # Display only head for preview, if calendar_data is not empty
        if not calendar_data.empty:
            st.dataframe(calendar_data.head())
        else:
            st.info("No annual data available.")
    with col2:
        st.write("#### Monthly Data (for QoQ)")
        # Display only head for preview, if monthly_data is not empty
        if not monthly_data.empty:
            st.dataframe(monthly_data.head())
        else:
            st.info("No monthly data available.")

if __name__ == "__main__":
    main_dashboard()