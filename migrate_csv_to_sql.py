# migrate_csv_to_sql.py

import os
import pandas as pd
import sqlite3
import re
from datetime import datetime

# --- Configuration ---
DATA_DIR = "vahan_data" # Directory where your existing CSVs are located
DB_FILE = "vahan_data.db" # Name for your SQLite database file

# --- Database Interaction Functions ---
def initialize_db(conn):
    """Initializes the SQLite database with necessary tables if they don't exist."""
    cursor = conn.cursor()

    # Drop tables if they exist to ensure a clean slate for migration
    # This is helpful for re-running migration without unique constraint errors
    cursor.execute('DROP TABLE IF EXISTS annual_registrations;')
    cursor.execute('DROP TABLE IF EXISTS monthly_registrations;')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annual_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            DataType TEXT NOT NULL,
            Year INTEGER NOT NULL,
            Registrations INTEGER NOT NULL,
            UNIQUE(Name, DataType, Year)
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            DataType TEXT NOT NULL,
            Year INTEGER NOT NULL,
            Month TEXT NOT NULL,
            MonthlyRegistrations INTEGER NOT NULL,
            UNIQUE(Name, DataType, Year, Month)
        );
    ''')
    conn.commit()
    print(f"Database schema initialized in '{DB_FILE}'.")

def map_vehicle_category(category_name):
    """
    Maps detailed vehicle category names to broader 2W, 3W, or 4W groups.
    (Copied from app.py for consistency during migration)
    """
    category_name = str(category_name).strip().upper()
    if 'TWO WHEELER' in category_name:
        return '2W'
    elif 'THREE WHEELER' in category_name:
        return '3W'
    elif any(keyword in category_name for keyword in ['FOUR WHEELER', 'GOODS VEHICLE', 'PASSENGER VEHICLE', 'MOTOR VEHICLE', 'TRAC', 'EARTH MOVING']):
        return '4W'
    return 'Other'

def migrate_csvs():
    """Reads all CSVs from DATA_DIR and migrates them to the SQLite database."""
    if not os.path.exists(DATA_DIR):
        print(f"Error: CSV data directory '{DATA_DIR}' not found. Cannot migrate.")
        return

    conn = sqlite3.connect(DB_FILE)
    initialize_db(conn) # Ensure tables exist and are clean

    print(f"Starting migration from CSVs in '{DATA_DIR}' to '{DB_FILE}'...")

    # --- Migrate Calendar Year Data (for YoY) ---
    calendar_year_files = [f for f in os.listdir(DATA_DIR) if f.startswith("Y_") and "X_Calendar_Year_Year_" in f and f.endswith(".csv")]
    
    for file in calendar_year_files:
        filepath = os.path.join(DATA_DIR, file)
        try:
            df = pd.read_csv(filepath)
            
            df_type = "Manufacturer"
            if "Y_Vehicle_Category_" in file:
                df_type = "Vehicle Category"

            # Rename the primary 'Name' column first
            if df_type == "Manufacturer":
                df.rename(columns={col: 'Name' for col in df.columns if 'Maker_Maker' in col}, inplace=True)
            elif df_type == "Vehicle Category":
                df.rename(columns={col: 'Name' for col in df.columns if 'Vehicle Category_Vehicle Category' in col}, inplace=True)

            # Identify year columns (e.g., 'Calendar Year_2024', 'Calendar Year_2025')
            year_cols = [col for col in df.columns if re.match(r'Calendar Year_\d{4}', col)]
            
            # Identify other ID columns to keep during melt (like S No, Name)
            id_vars = [col for col in df.columns if col not in year_cols and col not in ['TOTAL_TOTAL']]
            
            if 'Name' not in df.columns:
                print(f"Warning: 'Name' column not found in {file}. Skipping annual data migration.")
                continue

            if year_cols:
                # Melt the year columns into rows
                df_melted_annual = df.melt(
                    id_vars=id_vars,
                    value_vars=year_cols,
                    var_name='Year_Column',
                    value_name='Registrations'
                )
                
                # Extract the actual year number
                df_melted_annual['Year'] = df_melted_annual['Year_Column'].str.extract(r'(\d{4})').astype(int)
                
                # Prepare DataFrame for database insertion
                df_to_insert = pd.DataFrame({
                    'Name': df_melted_annual['Name'],
                    'DataType': df_type,
                    'Year': df_melted_annual['Year'],
                    'Registrations': pd.to_numeric(df_melted_annual['Registrations'], errors='coerce').fillna(0)
                })
                
                # We will no longer apply the category mapping here.
                # The data will be stored with its original, detailed category names.

                # Filter out rows with NaN in Name or 0 registrations
                df_to_insert.dropna(subset=['Name', 'Registrations'], inplace=True)
                df_to_insert = df_to_insert[df_to_insert['Registrations'] > 0]

                if not df_to_insert.empty:
                    # Use 'replace' to handle unique constraints if re-running
                    df_to_insert.to_sql('annual_registrations', conn, if_exists='append', index=False, method='multi')
                    print(f"Migrated annual data from {file} to 'annual_registrations'.")
                else:
                    print(f"No valid annual data to migrate from {file}.")
            else:
                print(f"Warning: No valid year columns found in {file}. Skipping annual migration.")
        except Exception as e:
            print(f"Error migrating annual data from {file}: {e}")

    # --- Migrate Month Wise Data (for QoQ) ---
    month_wise_files = [f for f in os.listdir(DATA_DIR) if f.startswith("Y_") and "X_Month_Wise_Year_" in f and f.endswith(".csv")]

    for file in month_wise_files:
        filepath = os.path.join(DATA_DIR, file)
        try:
            df = pd.read_csv(filepath)
            
            df_type = "Manufacturer"
            if "Y_Vehicle_Category_" in file:
                df_type = "Vehicle Category"

            year_match = re.search(r'Year_(\d{4})\.csv', file)
            year = int(year_match.group(1)) if year_match else None

            if year is None:
                print(f"Warning: Could not determine year from filename for {file}. Skipping monthly data migration.")
                continue

            # Rename the primary 'Name' column first
            if df_type == "Manufacturer":
                df.rename(columns={col: 'Name' for col in df.columns if 'Maker_Maker' in col}, inplace=True)
            elif df_type == "Vehicle Category":
                df.rename(columns={col: 'Name' for col in df.columns if 'Vehicle Category_Vehicle Category' in col}, inplace=True)

            month_cols = [col for col in df.columns if 'Month Wise_' in col]
            
            if 'Name' in df.columns and month_cols:
                # Identify other ID columns to keep during melt
                id_vars_monthly = [col for col in df.columns if col not in month_cols and col not in ['TOTAL_TOTAL']]

                df_melted_monthly = df.melt(id_vars=id_vars_monthly,
                                    value_vars=month_cols, 
                                    var_name='Month', 
                                    value_name='MonthlyRegistrations')
                
                df_melted_monthly['Month'] = df_melted_monthly['Month'].str.replace('Month Wise_', '')
                
                df_to_insert = pd.DataFrame({
                    'Name': df_melted_monthly['Name'],
                    'DataType': df_type,
                    'Year': year,
                    'Month': df_melted_monthly['Month'],
                    'MonthlyRegistrations': pd.to_numeric(df_melted_monthly['MonthlyRegistrations'], errors='coerce').fillna(0)
                })

                # We will no longer apply the category mapping here.
                # The data will be stored with its original, detailed category names.

                # Filter out rows with NaN in Name or 0 registrations
                df_to_insert.dropna(subset=['Name', 'MonthlyRegistrations'], inplace=True)
                df_to_insert = df_to_insert[df_to_insert['MonthlyRegistrations'] > 0]

                if not df_to_insert.empty:
                    df_to_insert.to_sql('monthly_registrations', conn, if_exists='append', index=False, method='multi')
                    print(f"Migrated monthly data from {file} to 'monthly_registrations'.")
                else:
                    print(f"No valid monthly data to migrate from {file}.")
            else:
                print(f"Warning: Missing 'Name' or month columns in {file}. Skipping monthly migration.")
        except Exception as e:
            print(f"Error migrating monthly data from {file}: {e}")

    conn.close()
    print("All CSV migration complete!")

if __name__ == "__main__":
    # Ensure the DATA_DIR exists for the migration script to find CSVs
    if not os.path.exists(DATA_DIR):
        print(f"Creating data directory: {DATA_DIR}")
        os.makedirs(DATA_DIR)
        print("Please place your scraped CSV files into this directory.")
    migrate_csvs()