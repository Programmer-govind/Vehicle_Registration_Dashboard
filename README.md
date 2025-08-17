# Vehicle Registration Dashboard

## 🚗 Assignment for Backend Developer Internship

### Objective
Build an interactive, investor-focused dashboard to analyze vehicle registration data from the Vahan Dashboard, providing actionable insights for investors.

---

## 📊 Features
- **Year-over-Year (YoY) & Quarter-over-Quarter (QoQ) Growth:**
  - Total vehicles by category (2W/3W/4W)
  - Manufacturer-wise registration data
- **Clean, Investor-Friendly UI:**
  - Built with [Streamlit](https://streamlit.io/) (or Dash)
  - Date range selection
  - Filters by vehicle category and manufacturer
  - Graphs showing trends and % change
- **Data Processing:**
  - Python for ETL and dashboard logic
  - SQL (SQLite) for efficient data manipulation
- **Modular, Readable, and Version-Controlled Code**

---

## 📁 Project Structure
```
├── csv_based_invester_dashboard/
│   ├── csv_app.py
│   └── csv_vahan_data_scrapper.py
├── sql_based_investor_dashboard/
│   ├── sql_app.py
│   └── sql_vahan_data_scrapper.py
├── vahan_data/
│   └── [Raw CSV files]
├── migrate_csv_to_sql.py
└── README.md
```

---

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Programmer-govind/Vehicle_Registration_Dashboard.git
cd Vehicle_Registration_Dashboard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*If `requirements.txt` is missing, install manually:*
```bash
pip install pandas streamlit sqlite3
```

### 3. Prepare Data
- Place all Vahan Dashboard CSV files in the `vahan_data/` directory.
- If you need to scrape data, use the provided scrapers:
  - `csv_based_invester_dashboard/csv_vahan_data_scrapper.py`
  - `sql_based_investor_dashboard/sql_vahan_data_scrapper.py`

#### Selenium WebDriver Setup (Important for Scraping)
The scrapers use Selenium for automated data collection. Selenium requires a browser driver (e.g. EdgeDriver for Microsoft Edge, ChromeDriver for Chrome, GeckoDriver for Firefox):

- By default, the script tries to use the internal ChromiumManager to download the driver automatically.
- If this fails or causes issues, **download the correct driver manually** for your browser version:
-  - [ChromeDriver](https://sites.google.com/chromium.org/driver/)
-  - [GeckoDriver for Firefox](https://github.com/mozilla/geckodriver/releases)
-  - [Edge WebDriver (msedgedriver)](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)
- After downloading, update the path to the driver in the scrapper script (see the comments in `*_vahan_data_scrapper.py`).
- Ensure the driver executable is accessible (either in your PATH or by providing the full path in the script).

**Note:** The Vahan portal is highly dynamic, built using JSF and custom PrimeFaces components. This can cause scraping issues or breakages if the portal structure changes. If you encounter persistent scraping problems, please contact me for support.

### 4. Migrate Data to SQLite (Optional, for SQL-based dashboard)
```bash
python migrate_csv_to_sql.py
```

### 5. Run the Dashboard
- **CSV-based Dashboard:**
  ```bash
  streamlit run csv_based_invester_dashboard/csv_app.py
  ```
- **SQL-based Dashboard:**
  ```bash
  streamlit run sql_based_investor_dashboard/sql_app.py
  ```

---

## 📝 Data Assumptions
- Data is sourced from the official [Vahan Dashboard](https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml).
- CSVs are expected to follow the naming conventions as in the `vahan_data/` folder.
- Vehicle categories are mapped to 2W (Two Wheeler), 3W (Three Wheeler), and 4W (Four Wheeler/Other) for analysis.
- Data cleaning and transformation steps are handled in the migration and app scripts.

---

## 📈 Screenshots

<img width="1907" height="984" alt="image" src="https://github.com/user-attachments/assets/1eeab58a-b41b-4fa9-8c0c-579f163edf7e" />
<img width="1908" height="955" alt="image" src="https://github.com/user-attachments/assets/5fae6c53-6a20-47e6-b5cf-df0cd62c6f10" />
<img width="1915" height="913" alt="image" src="https://github.com/user-attachments/assets/debcae5a-3862-4f1d-b8c3-54d52c1099a4" />
<img width="1917" height="988" alt="image" src="https://github.com/user-attachments/assets/47910a35-099c-442c-9411-022a33c1d223" />

---

## 🗺️ Feature Roadmap
- [ ] Add user authentication for personalized dashboards
- [ ] Enable export of filtered data and graphs
- [ ] Integrate real-time data updates
- [ ] Add AI-powered investment recommendations
- [ ] Mobile-friendly UI improvements

---

## 🎥 Video Walkthrough
> _[Insert your YouTube/Drive video link here]_

---

## 🛠️ Technical Details
- **Python** for all data processing and dashboard logic
- **Streamlit** for rapid UI development
- **SQLite** for efficient, file-based data storage (SQL-based version)
- **Pandas** for data wrangling
- **Modular codebase** for easy maintenance and extension

---

## 📚 Documentation
- All scraping/data collection steps are documented in the respective `*_vahan_data_scrapper.py` scripts.
- Database schema and migration logic are in `migrate_csv_to_sql.py`.
- Dashboard logic and UI are in `csv_app.py` and `sql_app.py`.

---

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License
[MIT](LICENSE)

---

## 🙏 Acknowledgements
- [Vahan Dashboard](https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml)
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [SQLite](https://www.sqlite.org/index.html)

---

> _For any queries, contact [gautamgovind448@gmail.com]._
