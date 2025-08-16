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
git clone https://github.com/your-username/Vehicle_Registration_Dashboard.git
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
- Data is sourced from the official [Vahan Dashboard](https://vahan.parivahan.gov.in/vahan4dashboard/).
- CSVs are expected to follow the naming conventions as in the `vahan_data/` folder.
- Vehicle categories are mapped to 2W (Two Wheeler), 3W (Three Wheeler), and 4W (Four Wheeler/Other) for analysis.
- Data cleaning and transformation steps are handled in the migration and app scripts.

---

## 📈 Screenshots

> _Add screenshots of your dashboard UI, graphs, and filters here._

- ![Dashboard Home](screenshots/dashboard_home.png)
- ![Filters Example](screenshots/filters.png)
- ![Growth Trends](screenshots/growth_trends.png)

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
_The video should cover:_
- What you built
- How to use the dashboard
- Key investor insights

---

## 💡 Investment Insights (Bonus)
> _Share any valuable investment insight or surprising trend you noticed while working on the data._

### Key Investment Insights from Vahan Vehicle Registration Data

1. **Consistent Growth in 2W Segment:**
  - Two-wheelers (2W) consistently show the highest registration volumes, especially in semi-urban and rural regions. This trend suggests strong demand for affordable personal mobility, making 2W manufacturers attractive for long-term investment.

2. **Emerging Electric Vehicle (EV) Uptake:**
  - Recent years show a noticeable uptick in registrations for electric 2W and 3W vehicles, outpacing growth rates in traditional fuel segments. This signals a shift in consumer preference and policy support, highlighting opportunities in the EV supply chain and related infrastructure.

3. **Quarterly Volatility Linked to Policy and Festive Seasons:**
  - QoQ data reveals spikes in registrations during festive quarters (Q3/Q4), and occasional dips following regulatory changes (e.g., BS6 emission norms, subsidy revisions). Investors should monitor policy cycles and seasonality for optimal entry/exit points.

4. **Market Share Shifts Among Manufacturers:**
  - While a few manufacturers dominate the 2W and 4W segments, new entrants and aggressive pricing strategies have led to periodic market share gains for challengers. Tracking these shifts can help identify emerging leaders early.

5. **4W Segment Recovery Post-Pandemic:**
  - The 4W (four-wheeler) segment, after a pandemic-induced slump, is showing signs of recovery, especially in the SUV and compact car categories. This rebound may present value opportunities in select OEMs.

6. **Commercial Vehicle (3W/4W) Cyclicality:**
  - 3W and 4W commercial vehicle registrations are more sensitive to economic cycles and infrastructure spending. Surges often coincide with government incentives or logistics sector growth.

> _These insights are based on observed patterns in the Vahan registration data and general industry trends. For investment decisions, always combine data-driven analysis with broader market research._

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
- [Vahan Dashboard](https://vahan.parivahan.gov.in/vahan4dashboard/)
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [SQLite](https://www.sqlite.org/index.html)

---

> _For any queries, contact [your-email@example.com]._
