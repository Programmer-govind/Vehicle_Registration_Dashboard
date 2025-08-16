import streamlit as st
import pandas as pd
import os
import re # For regex to extract year from filenames
import plotly.express as px # For interactive plots

# --- 1. Configuration and Data Paths ---
# Define the directory where CSVs are stored
DATA_DIR = "../vahan_data" # Assuming the scraped data is in this folder

# Ensure the data directory exists
if not os.path.exists(DATA_DIR):
    st.error(f"Error: The '{DATA_DIR}' directory was not found. Please ensure your scraped CSV files are placed in a folder named 'vahan_data' in the same directory as this script.")
    st.stop() # Stop the Streamlit app if data directory is missing

# --- 2. Data Loading and Preprocessing Functions ---
@st.cache_data # Cache data to avoid reloading on every rerun
def load_and_preprocess_data():
    """
    Loads all calendar year and month-wise CSVs from the DATA_DIR,
    combines them into two main DataFrames, and performs initial cleaning.
    """
    all_calendar_data = []
    all_monthly_data = []

    # --- Load Calendar Year Data (for YoY) ---
    # Files are expected to be named like Y_Maker_X_Calendar_Year_Year_YYYY.csv
    # or Y_Vehicle_Category_X_Calendar_Year_Year_YYYY.csv
    calendar_year_files = [f for f in os.listdir(DATA_DIR) if f.startswith("Y_") and "X_Calendar_Year_Year_" in f and f.endswith(".csv")]
    
    for file in calendar_year_files:
        filepath = os.path.join(DATA_DIR, file)
        try:
            df = pd.read_csv(filepath)
            
            # Determine if it's Maker or Vehicle Category data
            df_type = ""
            if "Y_Maker_" in file:
                df_type = "Manufacturer"
                df.rename(columns={col: col.replace('Maker_Maker', 'Name').replace('TOTAL_TOTAL', 'TotalRegistrations') for col in df.columns}, inplace=True)
            elif "Y_Vehicle_Category_" in file:
                df_type = "Vehicle Category"
                df.rename(columns={col: col.replace('Vehicle Category_Vehicle Category', 'Name').replace('TOTAL_TOTAL', 'TotalRegistrations') for col in df.columns}, inplace=True)
            else:
                continue # Skip files that don't match expected patterns

            df['DataType'] = df_type

            # Extract the year from the column name (e.g., 'Calendar Year_2024')
            year_col = next((col for col in df.columns if 'Calendar Year_' in col), None)
            if year_col:
                year = int(year_col.split('_')[-1])
                df['Year'] = year
                # Assign the specific year's registration count to a generic 'Registrations' column
                df['Registrations'] = pd.to_numeric(df[year_col], errors='coerce').fillna(0)
                
                # Select and reorder relevant columns
                df = df[['Name', 'DataType', 'Year', 'Registrations']]
                all_calendar_data.append(df)
            else:
                st.warning(f"Could not find a 'Calendar Year_' column in {file}. Skipping for YoY analysis.")
        except Exception as e:
            st.warning(f"Error loading or processing {file} for calendar data: {e}")

    calendar_data_combined = pd.concat(all_calendar_data, ignore_index=True) if all_calendar_data else pd.DataFrame()
    
    # --- Load Month Wise Data (for QoQ) ---
    # Files are expected to be named like Y_Maker_X_Month_Wise_Year_YYYY.csv
    # or Y_Vehicle_Category_X_Month_Wise_Year_YYYY.csv
    month_wise_files = [f for f in os.listdir(DATA_DIR) if f.startswith("Y_") and "X_Month_Wise_Year_" in f and f.endswith(".csv")]

    for file in month_wise_files:
        filepath = os.path.join(DATA_DIR, file)
        try:
            df = pd.read_csv(filepath)
            
            # Extract the year from the filename
            match = re.search(r'Year_(\d{4})\.csv', file)
            if not match:
                st.warning(f"Could not extract year from filename: {file}. Skipping for QoQ analysis.")
                continue
            year = int(match.group(1))

            df_type = ""
            if "Y_Maker_" in file:
                df_type = "Manufacturer"
                df.rename(columns={col: col.replace('Maker_Maker', 'Name') for col in df.columns}, inplace=True)
            elif "Y_Vehicle_Category_" in file:
                df_type = "Vehicle Category"
                df.rename(columns={col: col.replace('Vehicle Category_Vehicle Category', 'Name') for col in df.columns}, inplace=True)
            else:
                continue

            df['DataType'] = df_type
            df['Year'] = year

            # Melt the monthly columns into rows
            month_cols = [col for col in df.columns if 'Month Wise_' in col]
            if not month_cols:
                st.warning(f"No month-wise columns found in {file}. Skipping for QoQ analysis.")
                continue
            
            df_melted = df.melt(id_vars=['S No_S No', 'Name', 'DataType', 'Year'], 
                                value_vars=month_cols, 
                                var_name='Month', 
                                value_name='MonthlyRegistrations')
            
            df_melted['Month'] = df_melted['Month'].str.replace('Month Wise_', '') # Clean month name
            
            # Convert month name to number for datetime object
            month_to_num = {
                'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
            }
            df_melted['MonthNum'] = df_melted['Month'].map(month_to_num)
            
            # Create a proper date column (e.g., first day of the month) for sorting
            df_melted['Date'] = pd.to_datetime(df_melted['Year'].astype(str) + '-' + df_melted['MonthNum'].astype(str) + '-01', errors='coerce')
            df_melted.dropna(subset=['Date'], inplace=True) # Drop rows where date conversion failed

            df_melted['MonthlyRegistrations'] = pd.to_numeric(df_melted['MonthlyRegistrations'], errors='coerce').fillna(0)
            
            # Select and reorder relevant columns
            df_melted = df_melted[['Name', 'DataType', 'Year', 'Month', 'MonthNum', 'Date', 'MonthlyRegistrations']]
            all_monthly_data.append(df_melted)

        except Exception as e:
            st.warning(f"Error loading or processing {file} for monthly data: {e}")

    monthly_data_combined = pd.concat(all_monthly_data, ignore_index=True) if all_monthly_data else pd.DataFrame()

    return calendar_data_combined, monthly_data_combined

# --- 3. Vehicle Category Mapping ---
def map_vehicle_category(category_name):
    """
    Maps detailed vehicle category names to broader 2W, 3W, or 4W groups.
    """
    category_name = str(category_name).strip().upper()
    if 'TWO WHEELER' in category_name:
        return '2W'
    elif 'THREE WHEELER' in category_name:
        return '3W'
    # Classify everything else that seems like a vehicle under 4W, as per general understanding
    elif any(keyword in category_name for keyword in ['FOUR WHEELER', 'GOODS VEHICLE', 'PASSENGER VEHICLE', 'MOTOR VEHICLE', 'TRAC', 'EARTH MOVING']):
        return '4W'
    return 'Other' # Fallback for unclassified categories

# --- 4. Growth Analysis Functions ---
def calculate_yoy_growth(df_annual):
    """
    Calculates Year-over-Year (YoY) growth for registrations.
    Expects a DataFrame with 'Name', 'Year', and 'Registrations' columns.
    First, it aggregates the data to ensure one row per Name and Year.
    """
    if df_annual.empty or 'Year' not in df_annual.columns or 'Registrations' not in df_annual.columns or 'Name' not in df_annual.columns:
        return pd.DataFrame()

    # Step 1: Aggregate data to ensure there's only one entry per name and year.
    # This prevents the multiple, incorrect rows seen in the dashboard.
    df_annual_grouped = df_annual.groupby(['Name', 'Year'])['Registrations'].sum().reset_index()

    # Step 2: Ensure registrations are numeric and sort for correct shift calculation.
    df_annual_grouped['Registrations'] = pd.to_numeric(df_annual_grouped['Registrations'], errors='coerce').fillna(0)
    df_annual_sorted = df_annual_grouped.sort_values(by=['Name', 'Year']).copy()
    
    # Step 3: Calculate previous year's registrations using shift on the aggregated data.
    df_annual_sorted['PrevYearRegistrations'] = df_annual_sorted.groupby(['Name'])['Registrations'].shift(1)
    
    # Step 4: Calculate YoY Growth.
    # Handle the case where the previous year's registrations are zero to avoid division by zero errors.
    # The YoY growth is set to NA for the first year as it has no prior data for comparison.
    df_annual_sorted['YoYGrowth'] = ((df_annual_sorted['Registrations'] - df_annual_sorted['PrevYearRegistrations']) / df_annual_sorted['PrevYearRegistrations']) * 100
    
    # Handle infinite values (from division by zero) and round the result.
    df_annual_sorted['YoYGrowth'] = df_annual_sorted['YoYGrowth'].replace([float('inf'), -float('inf')], pd.NA).round(2)
    
    # Return the final DataFrame with the correct calculations.
    return df_annual_sorted

def calculate_qoq_growth(df_monthly):
    """
    Calculates Quarter-over-Quarter (QoQ) growth for registrations.
    Expects a DataFrame with 'Name', 'Date', and 'MonthlyRegistrations' columns.
    """
    if df_monthly.empty or 'Date' not in df_monthly.columns or 'MonthlyRegistrations' not in df_monthly.columns or 'Name' not in df_monthly.columns:
        return pd.DataFrame()

    # Ensure monthly registrations are numeric
    df_monthly['MonthlyRegistrations'] = pd.to_numeric(df_monthly['MonthlyRegistrations'], errors='coerce').fillna(0)

    # Add Quarter and QuarterYear columns
    df_monthly['Quarter'] = df_monthly['Date'].dt.quarter
    df_monthly['QuarterYear'] = df_monthly['Date'].dt.year.astype(str) + '-Q' + df_monthly['Quarter'].astype(str)
    
    # Aggregate monthly registrations to quarterly
    df_quarterly = df_monthly.groupby(['Name', 'DataType', 'Year', 'Quarter', 'QuarterYear'])['MonthlyRegistrations'].sum().reset_index()
    df_quarterly.rename(columns={'MonthlyRegistrations': 'QuarterlyRegistrations'}, inplace=True)
    
    # Sort for correct shift calculation
    df_quarterly_sorted = df_quarterly.sort_values(by=['Name', 'Year', 'Quarter']).copy()
    
    # Calculate previous quarter's registrations using shift
    df_quarterly_sorted['PrevQuarterRegistrations'] = df_quarterly_sorted.groupby(['Name'])['QuarterlyRegistrations'].shift(1)
    
    # Calculate QoQ Growth
    df_quarterly_sorted['QoQGrowth'] = ((df_quarterly_sorted['QuarterlyRegistrations'] - df_quarterly_sorted['PrevQuarterRegistrations']) / df_quarterly_sorted['PrevQuarterRegistrations']) * 100
    
    # *** FIX: Explicitly convert to numeric before rounding to avoid TypeError ***
    df_quarterly_sorted['QoQGrowth'] = pd.to_numeric(df_quarterly_sorted['QoQGrowth'], errors='coerce')

    df_quarterly_sorted['QoQGrowth'] = df_quarterly_sorted['QoQGrowth'].replace([float('inf'), -float('inf')], pd.NA).round(2) # Handle inf values
    
    return df_quarterly_sorted

# --- 5. Streamlit Dashboard ---
def main_dashboard():
    st.set_page_config(layout="wide", page_title="Vehicle Registration Dashboard 🚗📈")
    st.title("🚗📈 Vehicle Registration Growth Analysis")
    st.markdown("---")
    st.markdown("""
        Welcome to the Vehicle Registration Growth Dashboard!
        This dashboard provides insights into Year-over-Year (YoY) and Quarter-over-Quarter (QoQ) growth
        for vehicle registrations by **Vehicle Category (2W, 3W, 4W)** and **Manufacturer**.
        Use the filters on the sidebar to explore trends.
    """)
    st.markdown("---")

    # Load and preprocess data
    calendar_data, monthly_data = load_and_preprocess_data()

    if calendar_data.empty and monthly_data.empty:
        st.error("No data loaded. Please ensure CSV files are in the 'vahan_data' directory and follow the expected naming conventions.")
        st.stop() # Stop execution if no data is found

    # Apply vehicle category mapping to the original dataframes for filtering
    if not calendar_data.empty and 'Name' in calendar_data.columns and 'Vehicle Category' in calendar_data['DataType'].unique():
        calendar_data.loc[calendar_data['DataType'] == 'Vehicle Category', 'Name'] = calendar_data[calendar_data['DataType'] == 'Vehicle Category']['Name'].apply(map_vehicle_category)
    
    if not monthly_data.empty and 'Name' in monthly_data.columns and 'Vehicle Category' in monthly_data['DataType'].unique():
        monthly_data.loc[monthly_data['DataType'] == 'Vehicle Category', 'Name'] = monthly_data[monthly_data['DataType'] == 'Vehicle Category']['Name'].apply(map_vehicle_category)

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
        if not calendar_data.empty:
            unique_names.extend(calendar_data[calendar_data['DataType'] == 'Vehicle Category']['Name'].unique())
        if not monthly_data.empty:
            unique_names.extend(monthly_data[monthly_data['DataType'] == 'Vehicle Category']['Name'].unique())
        # Ensure 2W, 3W, 4W are always present if data exists
        if '2W' not in unique_names and '3W' not in unique_names and '4W' not in unique_names:
             unique_names.extend(['2W', '3W', '4W']) # Add them if no data for these specific categories
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
    min_year_data = pd.Timestamp.now().year # Default min to current year
    max_year_data = pd.Timestamp.now().year # Default max to current year
    
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
        # Filter annual data for the selected type and name
        filtered_annual_data = calendar_data[
            (calendar_data['DataType'] == data_type_filter) &
            (calendar_data['Name'] == selected_name)
        ].copy()

        yoy_df = calculate_yoy_growth(filtered_annual_data)
        
        if not yoy_df.empty:
            display_yoy_df = yoy_df[
                (yoy_df['Year'] >= year_range[0]) & 
                (yoy_df['Year'] <= year_range[1])
            ].dropna(subset=['YoYGrowth'])
            
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
                
                # Dynamic YoY Insight
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
                
                if display_yoy_df['YoYGrowth'].max() > 0:
                    best_year = display_yoy_df.loc[display_yoy_df['YoYGrowth'].idxmax()]
                    insight_message += f"\n\nIts highest YoY growth was **{best_year['YoYGrowth']:.2f}%** in **{int(best_year['Year'])}**."

            else:
                st.info(f"No sufficient data for YoY growth for **{selected_name}** in the selected year range ({year_range[0]}-{year_range[1]}). "
                        f"Ensure at least two consecutive years of data are available for this entity.")
        else:
            st.warning("YoY growth data could not be computed. Please check the raw data and filters.")
    
    elif growth_type_filter == "QoQ Growth":
        # Filter monthly data for the selected type and name
        filtered_monthly_data = monthly_data[
            (monthly_data['DataType'] == data_type_filter) &
            (monthly_data['Name'] == selected_name)
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
                # Ensure QuarterYear is sortable for plotting
                fig_qoq = px.line(display_qoq_df.sort_values('QuarterYear'), 
                                x='QuarterYear', 
                                y='QoQGrowth', 
                                title=f"QoQ Growth for {selected_name}",
                                labels={'QoQGrowth': 'QoQ Growth (%)', 'QuarterYear': 'Quarter'},
                                markers=True)
                fig_qoq.update_traces(mode='lines+markers')
                st.plotly_chart(fig_qoq, use_container_width=True)

                st.info(f"QoQ Growth is calculated as ((Current Quarter Registrations - Previous Quarter Registrations) / Previous Quarter Registrations) * 100.")

                # Dynamic QoQ Insight
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
                
                if display_qoq_df['QoQGrowth'].max() > 0:
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
        st.dataframe(calendar_data.head())
    with col2:
        st.write("#### Monthly Data (for QoQ)")
        st.dataframe(monthly_data.head())

if __name__ == "__main__":
    main_dashboard()
