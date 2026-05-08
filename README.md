# 🌐 International Debt Analytics Dashboard

> An end-to-end data analysis project built on **World Bank International Debt Statistics (IDS)** — covering 134 countries, 574 debt indicators, and ~1.56 million records from 2000 to 2024.

---

## 📌 Project Overview

This project transforms raw World Bank debt CSVs into a fully interactive **Streamlit dashboard** powered by a **MySQL relational database**. It covers the complete data pipeline — from raw CSV ingestion and cleaning in Python, to relational schema design in MySQL, to 30 SQL queries visualised in a multi-page Streamlit app.

---

## 🗂️ Dataset

| File | Description | Rows |
|------|-------------|------|
| `IDS_ALLCountries_Data.csv` | Core debt records (country × indicator × year × value) | ~1.56M |
| `IDS_CountryMetaData.csv` | Country metadata (region, income group, currency, etc.) | 134 |
| `IDS_SeriesMetaData.csv` | Indicator metadata (definitions, topics, periodicity) | 574 |
| `Country-Series - Metadata.csv` | Country–indicator relationship metadata | 375 |
| `IDS_FootNoteMetaData.csv` | Footnotes and data-quality notes | 2,673 |

**Source:** [World Bank — International Debt Statistics](https://www.worldbank.org/en/programs/debt-statistics/ids)  
**Coverage:** 2000 – 2024 (future projections 2025–2032 excluded)

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| Data Cleaning | Python · Pandas · NumPy |
| Database | MySQL 8 · `mysql-connector-python` |
| Dashboard | Streamlit |
| Visualisation | Plotly Express · Plotly Graph Objects |
| Environment | Jupyter Notebook (ETL) + Streamlit (app) |

---

## 🗄️ Database Schema

The data is stored in **5 relational tables** with enforced primary and foreign keys:

```
countries   (PK: Country_code)  ←──┐
                                    ├── debt_records    (FK → both)
indicators  (PK: Series_code)   ←──┤── country_series  (FK → both)
                                    └── footnotes       (FK → both)
```

| Table | PK | Rows | Description |
|-------|----|------|-------------|
| `countries` | `Country_code` (natural) | 134 | World Bank country metadata |
| `indicators` | `Series_code` (natural) | 574 | Debt indicator definitions |
| `debt_records` | `record_id` (surrogate) | ~1.56M | Core fact table — country × indicator × year × debt value |
| `country_series` | `id` (surrogate) | 375 | Country–indicator relationship notes |
| `footnotes` | `footnote_id` (surrogate) | 2,673 | Data-quality footnotes |

---

## 🧹 Data Pipeline (ETL)

All cleaning and loading is done in **`Debt_Analysis_Final.ipynb`**:

1. **Load** — 5 CSVs read with `latin-1` encoding
2. **Clean** — drop useless columns (`Counterpart-Area`), strip future year projections (2025–2032), remove null footer rows
3. **Reshape** — melt wide year columns into a long format (`Year`, `Debt`) using `pd.melt`
4. **Impute** — forward-fill and back-fill missing debt values grouped by indicator
5. **Normalise** — rename columns consistently across all DataFrames
6. **Load to MySQL** — create schema → validate FK integrity → `executemany` bulk inserts

---

## 📊 Dashboard Pages

### 📊 Overview Dashboard
Interactive KPI metrics and 5 filterable charts:
- **KPI Cards** — total countries, indicators, global debt, record count
- **Top N Countries by Debt** — filter by year range and indicator
- **Top Indicators Donut** — filter by country and year range
- **Debt Trend Over Time** — area chart (global) or multi-line (per country)
- **YoY Growth Rate** — green/red bar chart per country or global
- **Fastest Growing Countries** — configurable from/to year comparison

### 🟢 Basic Queries (Q1–Q10)
Foundational SQL — distinct values, counts, simple aggregations, min/max/avg.

### 🟡 Intermediate Queries (Q11–Q20)
Group-by aggregations, rankings, HAVING clauses, heatmaps, above-average filters.

### 🔴 Advanced Queries (Q21–Q30)
Window functions (`RANK`, `ROW_NUMBER`, cumulative SUM), CTEs, VIEWs, CASE categorisation, subqueries.

### 🗺️ Global Map
Year-slider choropleth map — visualises debt intensity across all countries for any year from 2000 to 2024.

### 📋 Raw Data Explorer
Multi-filter table browser with CSV download and country trend line chart.

---

## 🔑 Key SQL Techniques Used

- `RANK()` and `ROW_NUMBER()` window functions with `PARTITION BY`
- Cumulative sums using `SUM() OVER (ORDER BY Year)`
- Correlated subqueries and `HAVING` with aggregates
- `CASE WHEN` debt categorisation (High / Medium / Low)
- Self-joins for year-over-year growth calculation
- `CREATE OR REPLACE VIEW` for reusable query logic
- FK-safe bulk inserts with pre-validation against parent tables

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/your-username/international-debt-analytics.git
cd international-debt-analytics
```

### 2. Install dependencies
```bash
pip install streamlit pandas plotly mysql-connector-python numpy
```

### 3. Set up MySQL
Run the Jupyter notebook `Debt_Analysis_Final.ipynb` end-to-end — it creates the database, all 5 tables, and loads the data automatically.

### 4. Configure secrets
Create `.streamlit/secrets.toml`:
```toml
db_host     = "localhost"
db_user     = "root"
db_password = "your_password"
db_name     = "international_debt"
```

### 5. Launch the dashboard
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
international-debt-analytics/
│
├── Debt_Analysis_Final.ipynb   # ETL pipeline — clean, transform, load to MySQL
├── app.py                      # Streamlit dashboard (6 pages, 30 queries)
├── .streamlit/
│   └── secrets.toml            # DB credentials (not committed)
├── data/                       # Raw CSVs from World Bank (not committed)
│   ├── IDS_ALLCountries_Data.csv
│   ├── IDS_CountryMetaData.csv
│   ├── IDS_SeriesMetaData.csv
│   ├── Country-Series - Metadata.csv
│   └── IDS_FootNoteMetaData.csv
└── README.md
```

---

## 📈 Sample Insights

- **China and India** consistently dominate total external debt across most indicators
- Global debt grew by over **3× between 2000 and 2024**, with the sharpest spike post-2020
- The indicator **"External debt stocks, total (DOD, current US$)"** alone accounts for the largest single share of recorded debt
- The **2010s decade** saw the highest cumulative debt accumulation globally
- Several small economies show **>1000% debt growth** when comparing 2000 vs 2024 baselines

---

## 🙋 Author

**Shyam**  
Data Analyst · Python · SQL · Streamlit  
[GitHub](https://github.com/shyammuthuvel47-star) · [LinkedIn](linkedin.com/in/shyam-m-25b949216)

---

## 📄 License

This project is for educational and portfolio purposes.  
Data sourced from the [World Bank Open Data](https://data.worldbank.org/) under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.
