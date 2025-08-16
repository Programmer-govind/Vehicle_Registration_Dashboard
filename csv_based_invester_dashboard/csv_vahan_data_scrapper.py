import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
from datetime import datetime
import io

# --- Configuration ---
VAHAN_DASHBOARD_URL = "https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml"
OUTPUT_DIR = "vahan_data"
HTML_BACKUP_DIR = "html_backups"
BROWSER = "edge"
WAIT_TIMEOUT = 30
SLEEP_AFTER_ACTION = 3

# XPath Locators
LOCATORS = {
    "y_axis_dropdown_id": "yaxisVar",
    "x_axis_dropdown_id": "xaxisVar",
    "year_type_dropdown_id": "selectedYearType",
    "single_select_year_dropdown_id": "selectedYear",
    "multi_select_year_dropdown_id": "yearList",
    "refresh_button": (By.XPATH, "//button[contains(@class, 'ui-button') and .//span[contains(@class, 'ui-icon-refresh')]]"),
    "main_table_panel_id": "combTablePnl",
    "loading_overlay_blocker": (By.ID, "j_idt132_blocker"),
    "dropdown_options": (By.XPATH, ".//ul[contains(@class, 'ui-selectonemenu-list')]/li[contains(@class, 'ui-selectonemenu-item')]")
}

def setup_driver(browser_name):
    """
    Sets up and returns the webdriver.
    """
    options = webdriver.EdgeOptions() if browser_name == 'edge' else webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev_shm_usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36")

    try:
        if browser_name == 'edge':
            service = EdgeService("path/to/webdriver")
            driver = webdriver.Edge(service=service, options=options)
        elif browser_name == 'chrome':
            service = ChromeService("path/to/webdriver")
            driver = webdriver.Chrome(service=service, options=options)
        else:
            raise ValueError("Unsupported browser. Choose 'chrome' or 'edge'.")
        print(f"{browser_name.capitalize()} driver successfully set up.")
        return driver
    except Exception as e:
        print(f"Error setting up driver: {e}")
        return None

def save_html_backup(driver, filename):
    """
    Saves the current page's HTML to a file.
    """
    filepath = os.path.join(HTML_BACKUP_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"HTML backup saved: {filepath}")
    except Exception as e:
        print(f"Error saving HTML backup: {e}")

def get_dropdown_options(driver, dropdown_parent_id, dropdown_name):
    """
    Extracts options from a PrimeFaces dropdown.
    """
    try:
        dropdown_trigger_locator = (By.XPATH, f"//div[@id='{dropdown_parent_id}']/div[contains(@class, 'ui-selectonemenu-trigger')] | //div[@id='{dropdown_parent_id}']/div[contains(@class, 'ui-selectcheckboxmenu-trigger')]")
        
        dropdown_trigger_element = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(dropdown_trigger_locator),
            message=f"{dropdown_name} dropdown trigger (ID: {dropdown_parent_id}) is not clickable."
        )
        dropdown_trigger_element.click()
        time.sleep(SLEEP_AFTER_ACTION)

        specific_dropdown_panel_locator = (By.ID, f"{dropdown_parent_id}_panel")

        panel = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.visibility_of_element_located(specific_dropdown_panel_locator),
            message=f"{dropdown_name} dropdown panel (ID: {dropdown_parent_id}_panel) is not visible."
        )

        option_texts = []
        if dropdown_parent_id == LOCATORS["multi_select_year_dropdown_id"]:
            options_container = WebDriverWait(panel, WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, ".//div[contains(@class, 'ui-selectcheckboxmenu-items-wrapper')]")),
                message=f"No options container found for {dropdown_name} checkbox menu."
            )
            options = WebDriverWait(options_container, WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.XPATH, ".//li/label")),
                message=f"No options found for {dropdown_name} checkbox menu."
            )
            option_texts = [option.text.strip() for option in options if option.text.strip()]
        else:
            options = WebDriverWait(panel, WAIT_TIMEOUT).until(
                EC.presence_of_all_elements_located(LOCATORS["dropdown_options"]),
                message=f"No options found for {dropdown_name} dropdown."
            )
            option_texts = [option.text.strip() for option in options if option.text.strip()]
        
        print(f"Found {dropdown_name} options: {option_texts}")
        
        # Click the dropdown trigger again to close the panel, only if it's not a multi-select
        if dropdown_parent_id != LOCATORS["multi_select_year_dropdown_id"]:
            dropdown_trigger_element.click()
            try:
                WebDriverWait(driver, WAIT_TIMEOUT).until(
                    EC.invisibility_of_element_located(specific_dropdown_panel_locator),
                    message=f"{dropdown_name} dropdown panel did not become invisible after closing."
                )
                time.sleep(SLEEP_AFTER_ACTION)
            except Exception as e:
                print(f"Warning: Panel invisibility check failed for {dropdown_name}. Error: {e}")
                driver.find_element(By.TAG_NAME, "body").click()
                time.sleep(SLEEP_AFTER_ACTION)
        
        return option_texts
    except Exception as e:
        print(f"Error extracting {dropdown_name} options: {e}")
        return []

def select_dropdown_option(driver, dropdown_parent_id, option_text, dropdown_name):
    """
    Selects a specific option(s) in a PrimeFaces dropdown.
    """
    try:
        print(f"Selecting '{option_text}' in {dropdown_name} (ID: {dropdown_parent_id})...")
        dropdown_trigger_locator = (By.XPATH, f"//div[@id='{dropdown_parent_id}']/div[contains(@class, 'ui-selectonemenu-trigger')] | //div[@id='{dropdown_parent_id}']/div[contains(@class, 'ui-selectcheckboxmenu-trigger')]")

        dropdown_trigger_element = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(dropdown_trigger_locator),
            message=f"{dropdown_name} dropdown trigger is not clickable."
        )
        dropdown_trigger_element.click()
        time.sleep(SLEEP_AFTER_ACTION)

        specific_dropdown_panel_locator = (By.ID, f"{dropdown_parent_id}_panel")
        panel = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.visibility_of_element_located(specific_dropdown_panel_locator),
            message=f"{dropdown_name} dropdown panel is not visible."
        )

        options_to_select = [option_text] if not isinstance(option_text, list) else option_text

        for opt_val in options_to_select:
            current_panel = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.visibility_of_element_located(specific_dropdown_panel_locator),
                message=f"Panel for '{dropdown_name}' became stale while selecting '{opt_val}'."
            )
            
            if dropdown_parent_id == LOCATORS["multi_select_year_dropdown_id"]:
                option_xpath = f".//li/label[text()='{opt_val}']"
            else:
                option_xpath = LOCATORS["dropdown_options"][1] + f"[text()='{opt_val}']"

            option_to_click = WebDriverWait(current_panel, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, option_xpath)),
                message=f"Option '{opt_val}' in {dropdown_name} is not clickable."
            )
            
            driver.execute_script("arguments[0].scrollIntoView(true);", option_to_click)
            option_to_click.click()
            time.sleep(1)

        if dropdown_parent_id == LOCATORS["multi_select_year_dropdown_id"]:
            try:
                filter_button_locator = (By.XPATH, f"//div[@id='{dropdown_parent_id}_panel']//button[contains(span, 'Filter')]")
                filter_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(filter_button_locator)
                )
                filter_button.click()
                print("Filter button clicked.")
            except:
                print("No Filter button found, clicking trigger to close panel.")
                dropdown_trigger_element.click()
        
        try:
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.invisibility_of_element_located(specific_dropdown_panel_locator),
                message=f"{dropdown_name} dropdown panel did not become invisible after closing."
            )
            time.sleep(SLEEP_AFTER_ACTION)
        except Exception as e:
            print(f"Warning: Panel invisibility check failed for {dropdown_name}. Error: {e}")
            driver.find_element(By.TAG_NAME, "body").click()
            time.sleep(SLEEP_AFTER_ACTION)
        print(f"Successfully selected '{option_text}' in {dropdown_name}.")
        return True
    except Exception as e:
        print(f"Error while selecting '{option_text}' in {dropdown_name}: {e}")
        return False

def scrape_table_data(driver, combination_name):
    """
    Scrapes the data table from the page and saves it to a CSV file.
    """
    try:
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.invisibility_of_element_located(LOCATORS["loading_overlay_blocker"]),
            message="Loading overlay did not disappear."
        )
        print("Loading overlay disappeared.")
        time.sleep(1)

        main_table_container_id = ""
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "groupingTable")))
            main_table_container_id = "groupingTable"
        except:
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "vchgroupTable")))
                main_table_container_id = "vchgroupTable"
            except Exception as e:
                print(f"Error: Neither 'groupingTable' nor 'vchgroupTable' found. {e}")
                return pd.DataFrame()

        if not main_table_container_id:
            print(f"Error: No main table container found for '{combination_name}'.")
            return pd.DataFrame()

        main_table_container = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.visibility_of_element_located((By.ID, main_table_container_id)), 
            message=f"Table container '{main_table_container_id}' not found or visible."
        )
        
        table_html_to_parse = main_table_container.get_attribute('outerHTML')
        tables = pd.read_html(io.StringIO(table_html_to_parse))

        if tables:
            data_df = pd.DataFrame()
            best_df = None
            for df in tables:
                s_no_found = any('S No' in str(col) or 'S. No' in str(col) for col in df.columns)
                if s_no_found and df.shape[0] > 1:
                    best_df = df
                    break
                if df.shape[0] > 1 and df.shape[1] > 2 and (best_df is None or df.size > best_df.size):
                    best_df = df
            
            if best_df is not None:
                data_df = best_df
                if isinstance(data_df.columns, pd.MultiIndex):
                    data_df.columns = ['_'.join(col).strip() for col in data_df.columns.values]
                else:
                    data_df.columns = [col.strip() for col in data_df.columns.values]

                for col in data_df.columns:
                    if data_df[col].dtype == 'object':
                        data_df[col] = data_df[col].astype(str).str.replace(',', '', regex=False).str.strip()
                        data_df[col] = pd.to_numeric(data_df[col], errors='ignore')

                safe_combination_name = "".join([c if c.isalnum() else "_" for c in combination_name])
                output_filename = os.path.join(OUTPUT_DIR, f"{safe_combination_name}.csv")
                data_df.to_csv(output_filename, index=False, encoding='utf-8')
                print(f"Data saved: {output_filename}")
                return data_df
            else:
                print(f"No usable data table found for '{combination_name}'.")
                return pd.DataFrame()
        else:
            print(f"No tables found at all within '{main_table_container_id}'s HTML for '{combination_name}'.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error scraping data table for '{combination_name}': {e}")
        return pd.DataFrame()

def select_and_unselect_year(driver, year_to_scrape, y_axis_option, x_axis_option, active_year_dropdown_id):
    """
    Selects a single year from a multi-select dropdown, scrapes the data, and then unselects it.
    """
    try:
        # Select the specific year
        if not select_dropdown_option(driver, active_year_dropdown_id, year_to_scrape, "Year"):
            return

        combination_name = f"Y_{y_axis_option}_X_{x_axis_option}_Year_{year_to_scrape}"
        print(f"\nProcessing combination: {combination_name}")

        try:
            refresh_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable(LOCATORS["refresh_button"]),
                message="Refresh button is not clickable."
            )
            refresh_button.click()
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.invisibility_of_element_located(LOCATORS["loading_overlay_blocker"]),
                message="Loading overlay did not disappear after refresh."
            )
            time.sleep(SLEEP_AFTER_ACTION)
            print("Refresh button clicked and page reloaded.")
        except Exception as e:
            print(f"Error clicking Refresh button or waiting for page reload: {e}. Skipping to next year.")
            return

        save_html_backup(driver, f"{combination_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        scrape_table_data(driver, combination_name)
    except Exception as e:
        print(f"An error occurred while processing year {year_to_scrape}: {e}")
    finally:
        # Unselect the year after scraping is complete
        try:
            print(f"Unselecting year {year_to_scrape}...")
            dropdown_trigger_locator = (By.XPATH, f"//div[@id='{active_year_dropdown_id}']/div[contains(@class, 'ui-selectcheckboxmenu-trigger')]")
            dropdown_trigger_element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable(dropdown_trigger_locator)
            )
            dropdown_trigger_element.click()
            time.sleep(SLEEP_AFTER_ACTION)
            
            year_label_locator = (By.XPATH, f"//div[@id='{active_year_dropdown_id}_panel']//li/label[text()='{year_to_scrape}']")
            year_label_element = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable(year_label_locator)
            )
            year_label_element.click()
            time.sleep(SLEEP_AFTER_ACTION)

            dropdown_trigger_element.click()
            print(f"Successfully unselected year {year_to_scrape}.")
        except Exception as e:
            print(f"Error unselecting year {year_to_scrape}: {e}")

def handle_year_selection_month_wise(driver, x_axis_option, y_axis_option):
    """
    Handles single-select year iteration for the 'Month Wise' X-axis.
    """
    active_year_dropdown_id = LOCATORS["single_select_year_dropdown_id"]
    print(f"Detected single-select Year dropdown: {active_year_dropdown_id}")

    fetched_year_options = get_dropdown_options(driver, active_year_dropdown_id, "Year")
    if not fetched_year_options:
        print("No year options available. Skipping year iteration.")
        return

    # Define the years you want to scrape
    target_years = ["2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016"]
    relevant_year_options = [opt for opt in fetched_year_options if opt in target_years]

    if not relevant_year_options:
        print("No relevant years found to scrape. Skipping.")
        return

    # Iterate through each year, select it, and scrape the data
    for year_to_scrape in relevant_year_options:
        # Select the specific year from the single-select dropdown
        if not select_dropdown_option(driver, active_year_dropdown_id, year_to_scrape, "Year"):
            continue

        combination_name = f"Y_{y_axis_option}_X_{x_axis_option}_Year_{year_to_scrape}"
        print(f"\nProcessing combination: {combination_name}")

        try:
            refresh_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable(LOCATORS["refresh_button"]),
                message="Refresh button is not clickable."
            )
            refresh_button.click()
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                EC.invisibility_of_element_located(LOCATORS["loading_overlay_blocker"]),
                message="Loading overlay did not disappear after refresh."
            )
            time.sleep(SLEEP_AFTER_ACTION)
            print("Refresh button clicked and page reloaded.")
        except Exception as e:
            print(f"Error clicking Refresh button or waiting for page reload: {e}. Skipping to next year.")
            continue

        save_html_backup(driver, f"{combination_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        scrape_table_data(driver, combination_name)
        # No need to unselect for a single-select dropdown, as the next selection will overwrite it.

def handle_year_selection_calendar(driver, x_axis_option, y_axis_option):
    """
    Handles multi-select year iteration for the 'Calendar Year' X-axis.
    """
    active_year_dropdown_id = LOCATORS["multi_select_year_dropdown_id"]
    print(f"Detected multi-select Year dropdown: {active_year_dropdown_id}")

    fetched_year_options = get_dropdown_options(driver, active_year_dropdown_id, "Year")
    if not fetched_year_options:
        print("No year options available. Skipping year iteration.")
        return

    target_years = ["2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016"]
    relevant_year_options = [opt for opt in fetched_year_options if opt in target_years]

    if not relevant_year_options:
        print("No relevant years found to scrape. Skipping.")
        return

    # Iterate through each year and select it one-by-one for scraping
    for year_to_scrape in relevant_year_options:
        select_and_unselect_year(driver, year_to_scrape, y_axis_option, x_axis_option, active_year_dropdown_id)
        
        # After a year is scraped and unselected, we need to ensure the dropdown is closed
        try:
            dropdown_trigger_locator = (By.XPATH, f"//div[@id='{active_year_dropdown_id}']/div[contains(@class, 'ui-selectcheckboxmenu-trigger')]")
            panel_locator = (By.ID, f"{active_year_dropdown_id}_panel")
            WebDriverWait(driver, 5).until(EC.invisibility_of_element_located(panel_locator))
        except:
            pass # Panel is already closed, or we can move on

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(HTML_BACKUP_DIR, exist_ok=True)
    driver = setup_driver(BROWSER)
    if not driver:
        return

    try:
        driver.get(VAHAN_DASHBOARD_URL)
        print(f"Navigated to: {VAHAN_DASHBOARD_URL}")
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.invisibility_of_element_located(LOCATORS["loading_overlay_blocker"]),
            message="Initial loading overlay did not disappear."
        )
        time.sleep(SLEEP_AFTER_ACTION)
        save_html_backup(driver, f"initial_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

        target_y_axis_options = ["Maker"]
        target_x_axis_options = ["Calendar Year"]
        
        y_axis_options_available = get_dropdown_options(driver, LOCATORS["y_axis_dropdown_id"], "Y-Axis")
        if not y_axis_options_available:
            print("Failed to retrieve Y-Axis options. Script exiting.")
            return

        for y_axis_option in target_y_axis_options:
            if y_axis_option not in y_axis_options_available:
                print(f"Y-Axis option '{y_axis_option}' not available. Skipping.")
                continue

            if not select_dropdown_option(driver, LOCATORS["y_axis_dropdown_id"], y_axis_option, "Y-Axis"):
                continue

            fetched_x_axis_options = get_dropdown_options(driver, LOCATORS["x_axis_dropdown_id"], "X-Axis")
            relevant_x_axis_options = [opt for opt in fetched_x_axis_options if opt in target_x_axis_options]

            if not relevant_x_axis_options:
                print(f"No relevant X-Axis options found for '{y_axis_option}'. Skipping.")
                continue

            for x_axis_option in relevant_x_axis_options:
                if not select_dropdown_option(driver, LOCATORS["x_axis_dropdown_id"], x_axis_option, "X-Axis"):
                    continue

                if x_axis_option == "Calendar Year":
                    # For Calendar Year, use the multi-select handler
                    handle_year_selection_calendar(driver, x_axis_option, y_axis_option)
                elif x_axis_option == "Month Wise":
                    # For Month Wise, use the single-select handler
                    handle_year_selection_month_wise(driver, x_axis_option, y_axis_option)
                else:
                    # Generic case for other X-axis options
                    combination_name = f"Y_{y_axis_option}_X_{x_axis_option}"
                    print(f"\nProcessing combination: {combination_name}")

                    try:
                        refresh_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
                            EC.element_to_be_clickable(LOCATORS["refresh_button"]),
                            message="Refresh button is not clickable."
                        )
                        refresh_button.click()
                        WebDriverWait(driver, WAIT_TIMEOUT).until(
                            EC.invisibility_of_element_located(LOCATORS["loading_overlay_blocker"]),
                            message="Loading overlay did not disappear after refresh."
                        )
                        time.sleep(SLEEP_AFTER_ACTION)
                        print("Refresh button clicked and page reloaded.")
                    except Exception as e:
                        print(f"Error clicking Refresh button or waiting for page reload: {e}. Skipping.")
                        continue

                    save_html_backup(driver, f"{combination_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                    scrape_table_data(driver, combination_name)

    except Exception as e:
        print(f"An unexpected error occurred during the scraping process: {e}")
    finally:
        if driver:
            driver.quit()
            print("Driver closed.")

if __name__ == "__main__":
    main()
