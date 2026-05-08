"""
╔══════════════════════════════════════════════════════════════╗
║   International Debt Analysis  — Streamlit Dashboard         ║
║   MySQL DB  : international_debt                             ║
║   Tables    : debt_records, countries, indicators,           ║
║               country_series, footnotes                      ║
╚══════════════════════════════════════════════════════════════╝

Run:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import mysql.connector
from mysql.connector import Error

# ── Page Config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="International Debt Analytics",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ═══════════════════════════════════════════════════════════════════════
# DB CONNECTION
# ═══════════════════════════════════════════════════════════════════════

def _secret(key: str, default: str) -> str:
    try:
        return st.secrets[key]
    except Exception:
        return default


@st.cache_resource
def get_connection():
    host     = _secret("db_host",     "localhost")
    user     = _secret("db_user",     "root")
    password = _secret("db_password", "")
    database = _secret("db_name",     "international_debt")
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            connection_timeout=10,
        )
        return conn
    except Error as e:
        st.error(f"❌ MySQL connection failed: {e}")
        return None


@st.cache_data(ttl=300)
def run_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        if not conn.is_connected():
            conn.reconnect()
        return pd.read_sql(sql, conn)
    except Error as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🌐 Debt Analytics")
    st.divider()

    page = st.radio(
        "NAVIGATE",
        [
            "📊 Overview Dashboard",
            "🟢 Basic Queries (Q1–Q10)",
            "🟡 Intermediate (Q11–Q20)",
            "🔴 Advanced (Q21–Q30)",
            "🗺️ Global Map",
            "📋 Raw Data Explorer",
        ],
    )

    st.divider()
    st.caption("**Database:** international_debt")
    st.caption("**Tables:** debt_records, countries, indicators, country_series, footnotes")
    st.caption("**Records:** ~1.56M debt_records")
    st.divider()

    with st.expander("⚙️ DB Settings"):
        st.text_input("Host",     value="localhost")
        st.text_input("User",     value="root")
        st.text_input("Password", type="password")
        st.text_input("Database", value="international_debt")


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════
def fmt_billion(val):
    if pd.isna(val):
        return "N/A"
    if abs(val) >= 1e12:
        return f"${val/1e12:.2f}T"
    if abs(val) >= 1e9:
        return f"${val/1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


def section(icon, title, q_num=None):
    if q_num:
        st.subheader(f"{icon} Q{q_num} · {title}")
    else:
        st.subheader(f"{icon} {title}")
    st.divider()


PLOTLY_TEMPLATE   = "plotly_white"
PRIMARY           = "#1e40af"
SECONDARY         = "#0ea5e9"
ACCENT            = "#f59e0b"
DANGER            = "#ef4444"
SUCCESS           = "#10b981"
SEQUENTIAL_BLUES  = px.colors.sequential.Blues


# ═══════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW DASHBOARD
# ═══════════════════════════════════════════════════════════════════════
if page == "📊 Overview Dashboard":

    st.title("🌐 International Debt Analytics")
    st.caption("World Bank · International Debt Analysis 💹 2000 - 2024")
    st.write(
        "End-to-end analysis of global borrowing patterns, country-wise exposure, "
        "and indicator-level debt distribution across 134 nations."
    )
    st.divider()

    # ─────────────────────────────────────────────────────────────────
    # Pre-load dropdown options (cached)
    # ─────────────────────────────────────────────────────────────────
    _all_countries = run_query("""
        SELECT DISTINCT Country_name FROM debt_records
        WHERE Country_name NOT LIKE '%income%'
        AND Country_name NOT LIKE '%IDA%'
        AND Country_name NOT LIKE '%IBRD%'
        AND Country_name NOT LIKE '%classification%'
        AND Country_name NOT LIKE '%total%'
        ORDER BY Country_name
    """)
    _country_list  = _all_countries["Country_name"].tolist() if not _all_countries.empty else []

    _all_indicators = run_query(
        "SELECT DISTINCT Series_name FROM debt_records ORDER BY Series_name"
    )
    _indicator_list = _all_indicators["Series_name"].tolist() if not _all_indicators.empty else []

    _years = list(range(2000, 2025))

    # ─────────────────────────────────────────────────────────────────
    # KPI METRICS — no filter (always shows full dataset)
    # ─────────────────────────────────────────────────────────────────
    st.subheader("📌 Global Snapshot")
    kpi1 = run_query("SELECT COUNT(DISTINCT Country_name) AS cnt FROM debt_records")
    kpi2 = run_query("SELECT COUNT(DISTINCT Series_name)  AS cnt FROM debt_records")
    kpi3 = run_query("SELECT SUM(Debt)/1e12 AS total FROM debt_records")
    kpi4 = run_query("SELECT COUNT(*) AS cnt FROM debt_records")

    v1 = int(kpi1["cnt"].iloc[0])                 if not kpi1.empty else 0
    v2 = int(kpi2["cnt"].iloc[0])                 if not kpi2.empty else 0
    v3 = fmt_billion(kpi3["total"].iloc[0]*1e12)   if not kpi3.empty else "—"
    v4 = f"{int(kpi4['cnt'].iloc[0]):,}"          if not kpi4.empty else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌍 Countries",        v1)
    c2.metric("📈 Indicators",        v2)
    c3.metric("💰 Total Global Debt", v3)
    c4.metric("🗄️ Total Records",    v4)

    st.divider()

    # ═════════════════════════════════════════════════════════════════
    # CHART 1 — Top N Countries by Total Debt
    # Filter: top_n slider  +  year range
    # ═════════════════════════════════════════════════════════════════
    st.subheader("🏆 Top Countries by Total Debt")
    with st.expander("⚙️ Filters — Top Countries Chart", expanded=False):
        f1c1, f1c2, f1c3 = st.columns(3)
        with f1c1:
            top_n = st.slider("Number of Countries to Show", 5, 30, 10, key="f1_topn")
        with f1c2:
            f1_yr = st.select_slider("Year Range", options=_years,
                                     value=(2000, 2024), key="f1_yr")
        with f1c3:
            f1_indicator = st.selectbox(
                "Filter by Indicator",
                ["All Indicators"] + _indicator_list,
                key="f1_ind",
            )

    f1_where = f"""
        Year BETWEEN {f1_yr[0]} AND {f1_yr[1]}
        AND Country_name NOT LIKE '%income%'
        AND Country_name NOT LIKE '%IDA%'
        AND Country_name NOT LIKE '%IBRD%'
        AND Country_name NOT LIKE '%classification%'
        AND Country_name NOT LIKE '%total%'
        {"AND Series_name = '" + f1_indicator + "'" if f1_indicator != "All Indicators" else ""}
    """
    q_c1 = run_query(f"""
        SELECT Country_name, SUM(Debt)/1e9 AS total_debt_bn
        FROM debt_records
        WHERE {f1_where}
        GROUP BY Country_name
        ORDER BY total_debt_bn DESC
        LIMIT {top_n}
    """)
    if not q_c1.empty:
        fig_c1 = px.bar(
            q_c1, x="total_debt_bn", y="Country_name",
            orientation="h",
            color="total_debt_bn",
            color_continuous_scale=SEQUENTIAL_BLUES,
            labels={"total_debt_bn": "Total Debt (Billion USD)", "Country_name": ""},
            template=PLOTLY_TEMPLATE,
        )
        fig_c1.update_layout(
            height=max(300, top_n * 36),
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        fig_c1.update_traces(marker_line_width=0)
        st.plotly_chart(fig_c1, use_container_width=True)

    st.divider()

    # ═════════════════════════════════════════════════════════════════
    # CHART 2 — Top Indicators by Debt Share (Donut)
    # Filter: top_n  +  specific country  +  year range
    # ═════════════════════════════════════════════════════════════════
    st.subheader("📊 Top Indicators by Debt Share")
    with st.expander("⚙️ Filters — Indicators Donut Chart", expanded=False):
        f2c1, f2c2, f2c3 = st.columns(3)
        with f2c1:
            f2_topn = st.slider("Number of Indicators", 3, 15, 5, key="f2_topn")
        with f2c2:
            f2_country = st.selectbox(
                "Filter by Country",
                ["All Countries"] + _country_list,
                key="f2_country",
            )
        with f2c3:
            f2_yr = st.select_slider("Year Range", options=_years,
                                     value=(2000, 2024), key="f2_yr")

    f2_where = f"""
        Year BETWEEN {f2_yr[0]} AND {f2_yr[1]}
        {"AND Country_name = '" + f2_country + "'" if f2_country != "All Countries" else ""}
    """
    q_c2 = run_query(f"""
        SELECT Series_name, SUM(Debt)/1e9 AS total_bn
        FROM debt_records
        WHERE {f2_where}
        GROUP BY Series_name
        ORDER BY total_bn DESC
        LIMIT {f2_topn}
    """)
    if not q_c2.empty:
        fig_c2 = px.pie(
            q_c2, values="total_bn", names="Series_name",
            color_discrete_sequence=px.colors.sequential.Blues_r,
            hole=0.45,
            template=PLOTLY_TEMPLATE,
        )
        fig_c2.update_traces(textposition="outside", textinfo="percent+label")
        fig_c2.update_layout(height=400, showlegend=True,
                             margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_c2, use_container_width=True)

    st.divider()

    # ═════════════════════════════════════════════════════════════════
    # CHART 3 — Global Debt Trend Over Time (Area)
    # Filter: specific countries (multi)  +  specific indicator
    # ═════════════════════════════════════════════════════════════════
    st.subheader("📅 Global Debt Trend Over Time")
    with st.expander("⚙️ Filters — Debt Trend Chart", expanded=False):
        f3c1, f3c2 = st.columns(2)
        with f3c1:
            f3_countries = st.multiselect(
                "Compare Specific Countries (leave empty = global total)",
                _country_list,
                default=[],
                key="f3_countries",
                placeholder="All countries (global total)",
            )
        with f3c2:
            f3_indicator = st.selectbox(
                "Filter by Indicator",
                ["All Indicators"] + _indicator_list,
                key="f3_ind",
            )

    f3_where_parts = [
        "Country_name NOT LIKE '%income%'",
        "Country_name NOT LIKE '%IDA%'",
        "Country_name NOT LIKE '%IBRD%'",
        "Country_name NOT LIKE '%classification%'",
        "Country_name NOT LIKE '%total%'",
        "Year BETWEEN 2000 AND 2024",
    ]
    if f3_countries:
        lst = "', '".join(f3_countries)
        f3_where_parts.append(f"Country_name IN ('{lst}')")
    if f3_indicator != "All Indicators":
        f3_where_parts.append(f"Series_name = '{f3_indicator}'")
    f3_where = " AND ".join(f3_where_parts)

    if f3_countries and len(f3_countries) > 1:
        # Multi-country line chart
        q_c3 = run_query(f"""
            SELECT Country_name, Year, SUM(Debt)/1e9 AS debt_bn
            FROM debt_records
            WHERE {f3_where}
            GROUP BY Country_name, Year
            ORDER BY Year
        """)
        if not q_c3.empty:
            fig_c3 = px.line(
                q_c3, x="Year", y="debt_bn",
                color="Country_name",
                labels={"debt_bn": "Debt (Billion USD)"},
                template=PLOTLY_TEMPLATE,
                markers=True,
            )
            fig_c3.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_c3, use_container_width=True)
    else:
        # Single country or global — area chart
        q_c3 = run_query(f"""
            SELECT Year, SUM(Debt)/1e12 AS total_trillion
            FROM debt_records
            WHERE {f3_where}
            GROUP BY Year
            ORDER BY Year
        """)
        if not q_c3.empty:
            fig_c3 = px.area(
                q_c3, x="Year", y="total_trillion",
                labels={"total_trillion": "Total Debt (Trillion USD)"},
                color_discrete_sequence=[PRIMARY],
                template=PLOTLY_TEMPLATE,
            )
            fig_c3.update_traces(line_color=PRIMARY,
                                 fillcolor="rgba(30,64,175,0.12)", line_width=2.5)
            fig_c3.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_c3, use_container_width=True)

    st.divider()

    # ═════════════════════════════════════════════════════════════════
    # CHART 4 — YoY Growth  +  Debt by Decade  (side by side)
    # Filter (YoY): specific country
    # Filter (Decade): specific country  +  specific indicator
    # ═════════════════════════════════════════════════════════════════
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📈 Year-over-Year Debt Growth Rate (%)")
        with st.expander("⚙️ Filters — YoY Growth", expanded=False):
            f4_country = st.selectbox(
                "Country (global if empty)",
                ["Global Total"] + _country_list,
                key="f4_country",
            )

        f4_where = "Year BETWEEN 2000 AND 2024"
        if f4_country != "Global Total":
            f4_where += f" AND Country_name = '{f4_country}'"
        else:
            f4_where += """ AND Country_name NOT LIKE '%income%'
                AND Country_name NOT LIKE '%IDA%'
                AND Country_name NOT LIKE '%IBRD%'
                AND Country_name NOT LIKE '%classification%'
                AND Country_name NOT LIKE '%total%'"""

        qt_yoy = run_query(f"""
            SELECT Year, SUM(Debt)/1e12 AS total_trillion
            FROM debt_records
            WHERE {f4_where}
            GROUP BY Year ORDER BY Year
        """)
        if not qt_yoy.empty and len(qt_yoy) > 1:
            qt_yoy["yoy_growth"] = qt_yoy["total_trillion"].pct_change() * 100
            qt_g = qt_yoy.dropna(subset=["yoy_growth"])
            fig_yoy = go.Figure()
            fig_yoy.add_trace(go.Bar(
                x=qt_g["Year"], y=qt_g["yoy_growth"],
                marker_color=[DANGER if v < 0 else SUCCESS for v in qt_g["yoy_growth"]],
            ))
            fig_yoy.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
            fig_yoy.update_layout(
                template=PLOTLY_TEMPLATE, height=300,
                yaxis_title="Growth (%)", xaxis_title="Year",
                margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
            )
            st.plotly_chart(fig_yoy, use_container_width=True)

    with col_b:
        st.subheader("🗓️ Debt by Decade")
        with st.expander("⚙️ Filters — Decade Chart", expanded=False):
            f5c1, f5c2 = st.columns(2)
            with f5c1:
                f5_country = st.selectbox(
                    "Country",
                    ["All Countries"] + _country_list,
                    key="f5_country",
                )
            with f5c2:
                f5_indicator = st.selectbox(
                    "Indicator",
                    ["All Indicators"] + _indicator_list,
                    key="f5_ind",
                )

        f5_where_parts = ["Year BETWEEN 2000 AND 2024"]
        if f5_country != "All Countries":
            f5_where_parts.append(f"Country_name = '{f5_country}'")
        if f5_indicator != "All Indicators":
            f5_where_parts.append(f"Series_name = '{f5_indicator}'")
        f5_where = " AND ".join(f5_where_parts)

        q_dec = run_query(f"""
            SELECT
                CASE
                    WHEN Year BETWEEN 2000 AND 2009 THEN '2000s'
                    WHEN Year BETWEEN 2010 AND 2019 THEN '2010s'
                    WHEN Year BETWEEN 2020 AND 2024 THEN '2020s'
                END AS decade,
                SUM(Debt)/1e12 AS total_trillion
            FROM debt_records
            WHERE {f5_where}
            GROUP BY decade ORDER BY decade
        """)
        if not q_dec.empty:
            fig_dec = px.bar(
                q_dec, x="decade", y="total_trillion",
                color="total_trillion",
                color_continuous_scale=SEQUENTIAL_BLUES,
                labels={"total_trillion": "Debt (Trillion $)", "decade": "Decade"},
                text="total_trillion", template=PLOTLY_TEMPLATE,
            )
            fig_dec.update_traces(texttemplate="%{text:.2f}T", textposition="outside")
            fig_dec.update_layout(height=300, coloraxis_showscale=False,
                                  margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_dec, use_container_width=True)

    st.divider()

    # ═════════════════════════════════════════════════════════════════
    # CHART 5 — Fastest Growing Countries
    # Filter: year from/to  +  specific indicator
    # ═════════════════════════════════════════════════════════════════
    st.subheader("🚀 Fastest Growing Debtor Countries")
    with st.expander("⚙️ Filters — Growth Chart", expanded=False):
        f6c1, f6c2, f6c3 = st.columns(3)
        with f6c1:
            f6_yr_start = st.selectbox("From Year", _years, index=0,  key="f6_start")
        with f6c2:
            f6_yr_end   = st.selectbox("To Year",   _years, index=len(_years)-1, key="f6_end")
        with f6c3:
            f6_indicator = st.selectbox(
                "Filter by Indicator",
                ["All Indicators"] + _indicator_list,
                key="f6_ind",
            )

    f6_base = """
        Country_name NOT LIKE '%income%'
        AND Country_name NOT LIKE '%IDA%'
        AND Country_name NOT LIKE '%IBRD%'
        AND Country_name NOT LIKE '%classification%'
        AND Country_name NOT LIKE '%total%'
    """
    if f6_indicator != "All Indicators":
        f6_base += f" AND Series_name = '{f6_indicator}'"

    q_growth = run_query(f"""
        SELECT
            f.Country_name,
            f.first_debt_bn,
            l.last_debt_bn,
            ROUND((l.last_debt_bn - f.first_debt_bn) / NULLIF(f.first_debt_bn,0) * 100, 1) AS growth_pct
        FROM (
            SELECT Country_name, SUM(Debt)/1e9 AS first_debt_bn
            FROM debt_records
            WHERE {f6_base} AND Year = {f6_yr_start}
            GROUP BY Country_name
        ) f
        JOIN (
            SELECT Country_name, SUM(Debt)/1e9 AS last_debt_bn
            FROM debt_records
            WHERE {f6_base} AND Year = {f6_yr_end}
            GROUP BY Country_name
        ) l ON f.Country_name = l.Country_name
        WHERE f.first_debt_bn > 0
        ORDER BY growth_pct DESC
        LIMIT 10
    """)
    if not q_growth.empty:
        fig_gr = px.bar(
            q_growth, x="Country_name", y="growth_pct",
            color="growth_pct",
            color_continuous_scale=px.colors.sequential.Oranges,
            text="growth_pct",
            labels={"growth_pct": "Debt Growth (%)", "Country_name": "Country"},
            template=PLOTLY_TEMPLATE,
        )
        fig_gr.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_gr.update_layout(height=340, coloraxis_showscale=False,
                             margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_gr, use_container_width=True)
    elif f6_yr_start >= f6_yr_end:
        st.warning("⚠️ 'From Year' must be less than 'To Year'.")
    else:
        st.info("No data found for the selected filters.")

# PAGE: BASIC QUERIES  (Q1 – Q10)
# ═══════════════════════════════════════════════════════════════════════
elif page == "🟢 Basic Queries (Q1–Q10)":
    st.title("🟢 Basic SQL Queries — Q1 to Q10")
    st.write("Direct table explorations and aggregate summaries.")
    st.divider()

    with st.expander("Q1 · All Distinct Country Names", expanded=False):
        section("🌍", "All Distinct Country Names", 1)
        q1 = run_query("SELECT DISTINCT Country_name FROM debt_records ORDER BY Country_name")
        st.write(f"**{len(q1)} countries found**")
        cols = st.columns(4)
        chunk = len(q1) // 4 + 1
        for i, col in enumerate(cols):
            with col:
                st.dataframe(
                    q1.iloc[i*chunk:(i+1)*chunk].reset_index(drop=True),
                    use_container_width=True, hide_index=True,
                )

    with st.expander("Q2 · Count of Countries", expanded=False):
        section("🔢", "Total Number of Countries", 2)
        q2 = run_query("SELECT COUNT(DISTINCT Country_name) AS total_countries FROM debt_records")
        if not q2.empty:
            st.metric("Total Countries", int(q2["total_countries"].iloc[0]))
        st.code("SELECT COUNT(DISTINCT Country_name) AS total_countries FROM debt_records;", language="sql")

    with st.expander("Q3 · Total Number of Indicators", expanded=False):
        section("📋", "Total Number of Indicators", 3)
        q3 = run_query("SELECT COUNT(DISTINCT Series_name) AS total_indicators FROM debt_records")
        if not q3.empty:
            st.metric("Total Indicators", int(q3["total_indicators"].iloc[0]))
        st.code("SELECT COUNT(DISTINCT Series_name) AS total_indicators FROM debt_records;", language="sql")

    with st.expander("Q4 · First 10 Records", expanded=False):
        section("📄", "First 10 Records of Dataset", 4)
        q4 = run_query("SELECT * FROM debt_records LIMIT 10")
        st.dataframe(q4, use_container_width=True, hide_index=True)
        st.code("SELECT * FROM debt_records LIMIT 10;", language="sql")

    with st.expander("Q5 · Total Global Debt", expanded=True):
        section("💰", "Total Global Debt (Sum)", 5)
        q5 = run_query("SELECT SUM(Debt) AS total_global_debt FROM debt_records")
        if not q5.empty:
            st.metric("Total Global Debt", fmt_billion(q5["total_global_debt"].iloc[0]))
        st.code("SELECT SUM(Debt) AS total_global_debt FROM debt_records;", language="sql")

    with st.expander("Q6 · All Unique Indicator Names", expanded=False):
        section("🏷️", "All Unique Indicator Names", 6)
        q6 = run_query("SELECT DISTINCT Series_name AS indicator FROM debt_records ORDER BY indicator")
        st.dataframe(q6, use_container_width=True, hide_index=True, height=250)
        st.code("SELECT DISTINCT Series_name AS indicator FROM debt_records ORDER BY indicator;", language="sql")

    with st.expander("Q7 · Number of Records per Country", expanded=False):
        # ✅ FIX: removed duplicate WHERE clause
        section("📊", "Records per Country", 7)
        q7 = run_query("""
            SELECT Country_name, COUNT(*) AS record_count
            FROM debt_records
            WHERE Country_name NOT LIKE '%income%'
            AND Country_name NOT LIKE '%IDA%'
            AND Country_name NOT LIKE '%IBRD%'
            AND Country_name NOT LIKE '%classification%'
            AND Country_name NOT LIKE '%total%'
            GROUP BY Country_name
            ORDER BY record_count DESC
        """)
        if not q7.empty:
            fig = px.bar(
                q7.head(20), x="Country_name", y="record_count",
                color="record_count",
                color_continuous_scale=SEQUENTIAL_BLUES,
                template=PLOTLY_TEMPLATE,
                labels={"record_count": "Records", "Country_name": "Country"},
                title="Top 20 Countries by Record Count",
            )
            fig.update_layout(height=350, coloraxis_showscale=False,
                              margin=dict(l=0, r=0, t=30, b=0))
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q7, use_container_width=True, hide_index=True)

    with st.expander("Q8 · Records Where Debt > 1 Billion USD", expanded=False):
        # ✅ FIX: removed stray 'x' from 1000000000x
        section("💵", "Debt > $1 Billion Records", 8)
        q8 = run_query("""
            SELECT Country_name, Series_name, Year, Debt
            FROM debt_records
            WHERE Debt > 1000000000
            ORDER BY Debt DESC
            LIMIT 100
        """)
        st.write("Showing top 100 of qualifying records.")
        st.dataframe(q8.style.format({"Debt": "${:,.0f}"}),
                     use_container_width=True, hide_index=True)
        st.code("SELECT * FROM debt_records WHERE Debt > 1000000000 ORDER BY Debt DESC;", language="sql")

    with st.expander("Q9 · Min, Max, Average Debt", expanded=True):
        section("📐", "Statistical Summary of Debt Values", 9)
        q9 = run_query("""
            SELECT MIN(Debt) AS min_debt,
                   MAX(Debt) AS max_debt,
                   AVG(Debt) AS avg_debt
            FROM debt_records
        """)
        if not q9.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Minimum Debt", fmt_billion(q9["min_debt"].iloc[0]))
            c2.metric("Maximum Debt", fmt_billion(q9["max_debt"].iloc[0]))
            c3.metric("Average Debt", fmt_billion(q9["avg_debt"].iloc[0]))
        st.code("SELECT MIN(Debt), MAX(Debt), AVG(Debt) FROM debt_records;", language="sql")

    with st.expander("Q10 · Total Record Count", expanded=False):
        section("🗄️", "Total Number of Records", 10)
        q10 = run_query("SELECT COUNT(*) AS total_records FROM debt_records")
        if not q10.empty:
            st.metric("Total Records", f"{int(q10['total_records'].iloc[0]):,}")
        st.code("SELECT COUNT(*) AS total_records FROM debt_records;", language="sql")


# ═══════════════════════════════════════════════════════════════════════
# PAGE: INTERMEDIATE  (Q11 – Q20)
# ═══════════════════════════════════════════════════════════════════════
elif page == "🟡 Intermediate (Q11–Q20)":
    st.title("🟡 Intermediate SQL Queries — Q11 to Q20")
    st.write("Aggregations, rankings, and comparative analysis.")
    st.divider()

    with st.expander("Q11 · Total Debt per Country", expanded=True):
        section("🌍", "Total Debt for Each Country", 11)
        q11 = run_query("""
            SELECT Country_name, SUM(Debt)/1e9 AS total_debt_bn
            FROM debt_records
            WHERE Country_name NOT LIKE '%income%'
            AND Country_name NOT LIKE '%IDA%'
            AND Country_name NOT LIKE '%IBRD%'
            AND Country_name NOT LIKE '%classification%'
            AND Country_name NOT LIKE '%total%'
            GROUP BY Country_name
            ORDER BY total_debt_bn DESC
        """)
        if not q11.empty:
            fig = px.bar(
                q11.head(30), x="Country_name", y="total_debt_bn",
                color="total_debt_bn",
                color_continuous_scale=SEQUENTIAL_BLUES,
                labels={"total_debt_bn": "Total Debt (Bn USD)", "Country_name": "Country"},
                template=PLOTLY_TEMPLATE,
                title="Total Debt per Country (Top 30)",
            )
            fig.update_layout(height=380, coloraxis_showscale=False,
                              margin=dict(l=0, r=0, t=30, b=0))
            fig.update_xaxes(tickangle=50)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q11.style.format({"total_debt_bn": "{:,.2f}"}),
                         use_container_width=True, hide_index=True)

    with st.expander("Q12 · Top 10 Countries — Highest Total Debt", expanded=False):
        section("🏆", "Top 10 Highest Debt Countries", 12)
        q12 = run_query("""
            SELECT Country_name, SUM(Debt)/1e9 AS total_debt_bn
            FROM debt_records
            WHERE Country_name NOT LIKE '%income%'
            AND Country_name NOT LIKE '%IDA%'
            AND Country_name NOT LIKE '%IBRD%'
            AND Country_name NOT LIKE '%classification%'
            AND Country_name NOT LIKE '%total%'
            GROUP BY Country_name
            ORDER BY total_debt_bn DESC
            LIMIT 10
        """)
        if not q12.empty:
            fig = px.bar(
                q12, x="total_debt_bn", y="Country_name",
                orientation="h",
                color="total_debt_bn",
                color_continuous_scale=px.colors.sequential.Reds,
                labels={"total_debt_bn": "Total Debt (Bn USD)", "Country_name": ""},
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(
                height=360, coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q12.style.format({"total_debt_bn": "{:,.2f}"}),
                         use_container_width=True, hide_index=True)
        st.code("""SELECT Country_name, SUM(Debt)/1e9 AS total_debt_bn
FROM debt_records
GROUP BY Country_name
ORDER BY total_debt_bn DESC LIMIT 10;""", language="sql")

    with st.expander("Q13 · Average Debt per Country", expanded=False):
        section("📊", "Average Debt per Country", 13)
        q13 = run_query("""
            SELECT Country_name, AVG(Debt)/1e9 AS avg_debt_bn
            FROM debt_records
            GROUP BY Country_name
            ORDER BY avg_debt_bn DESC
        """)
        if not q13.empty:
            fig = px.scatter(
                q13, x="Country_name", y="avg_debt_bn",
                color="avg_debt_bn",
                color_continuous_scale=SEQUENTIAL_BLUES,
                labels={"avg_debt_bn": "Avg Debt (Bn USD)", "Country_name": "Country"},
                template=PLOTLY_TEMPLATE,
                title="Average Debt per Country",
            )
            fig.update_layout(height=360, coloraxis_showscale=False,
                              xaxis_visible=False,
                              margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q13.style.format({"avg_debt_bn": "{:,.4f}"}),
                         use_container_width=True, hide_index=True)

    with st.expander("Q14 · Total Debt per Indicator", expanded=False):
        section("📋", "Total Debt for Each Indicator", 14)
        q14 = run_query("""
            SELECT Series_name AS indicator, SUM(Debt)/1e9 AS total_debt_bn
            FROM debt_records
            GROUP BY Series_name
            ORDER BY total_debt_bn DESC
        """)
        if not q14.empty:
            fig = px.bar(
                q14.head(15), x="total_debt_bn", y="indicator",
                orientation="h",
                color="total_debt_bn",
                color_continuous_scale=px.colors.sequential.Teal,
                labels={"total_debt_bn": "Total Debt (Bn USD)", "indicator": ""},
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(
                height=420, coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                margin=dict(l=0, r=10, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q14.style.format({"total_debt_bn": "{:,.2f}"}),
                         use_container_width=True, hide_index=True)

    with st.expander("Q15 · Indicator with Highest Total Debt", expanded=False):
        section("🎯", "Top Debt-Contributing Indicator", 15)
        q15 = run_query("""
            SELECT Series_name AS indicator, SUM(Debt)/1e9 AS total_debt_bn
            FROM debt_records
            GROUP BY Series_name
            ORDER BY total_debt_bn DESC
            LIMIT 1
        """)
        if not q15.empty:
            st.metric("Top Indicator", q15["indicator"].iloc[0],
                      f"${q15['total_debt_bn'].iloc[0]:,.2f} Billion")
        st.code("""SELECT Series_name, SUM(Debt)/1e9 AS total_debt_bn
FROM debt_records GROUP BY Series_name ORDER BY total_debt_bn DESC LIMIT 1;""", language="sql")

    with st.expander("Q16 · Country with Lowest Total Debt", expanded=False):
        section("📉", "Country with Lowest Total Debt", 16)
        q16 = run_query("""
            SELECT Country_name, SUM(Debt)/1e6 AS total_debt_mn
            FROM debt_records
            GROUP BY Country_name
            ORDER BY total_debt_mn ASC
            LIMIT 10
        """)
        if not q16.empty:
            st.info(f"Lowest: {q16['Country_name'].iloc[0]} — ${q16['total_debt_mn'].iloc[0]:,.2f}M")
            fig = px.bar(
                q16, x="Country_name", y="total_debt_mn",
                color="total_debt_mn",
                color_continuous_scale=px.colors.sequential.Greens,
                labels={"total_debt_mn": "Total Debt (Mn USD)", "Country_name": "Country"},
                template=PLOTLY_TEMPLATE,
                title="10 Lowest-Debt Countries",
            )
            fig.update_layout(height=300, coloraxis_showscale=False,
                              margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Q17 · Debt per Country–Indicator Combination", expanded=False):
        section("🔀", "Country × Indicator Debt Heatmap", 17)
        q17 = run_query("""
            SELECT Country_name, Series_name AS indicator, SUM(Debt)/1e9 AS total_bn
            FROM debt_records
            GROUP BY Country_name, Series_name
            ORDER BY total_bn DESC
            LIMIT 500
        """)
        if not q17.empty:
            pivot = q17.head(200).pivot_table(
                index="Country_name", columns="indicator",
                values="total_bn", aggfunc="sum"
            ).fillna(0)
            top_c = q17.groupby("Country_name")["total_bn"].sum().nlargest(20).index
            top_i = q17.groupby("indicator")["total_bn"].sum().nlargest(10).index
            sub   = pivot.loc[pivot.index.isin(top_c), pivot.columns.isin(top_i)]
            fig   = px.imshow(
                sub,
                color_continuous_scale=SEQUENTIAL_BLUES,
                aspect="auto",
                labels=dict(color="Debt (Bn USD)"),
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Q18 · Number of Indicators per Country", expanded=False):
        # ✅ FIX: removed invalid y= parameter from histogram
        section("🔢", "How Many Indicators Does Each Country Have?", 18)
        q18 = run_query("""
            SELECT Country_name, COUNT(DISTINCT Series_name) AS indicator_count
            FROM debt_records
            WHERE Country_name NOT LIKE '%income%'
            AND Country_name NOT LIKE '%IDA%'
            AND Country_name NOT LIKE '%IBRD%'
            AND Country_name NOT LIKE '%classification%'
            AND Country_name NOT LIKE '%total%'
            GROUP BY Country_name
            ORDER BY indicator_count DESC
        """)
        if not q18.empty:
            fig = px.histogram(
                q18,
                x="indicator_count",
                nbins=30,
                color_discrete_sequence=[PRIMARY],
                labels={"indicator_count": "Indicators per Country"},
                template=PLOTLY_TEMPLATE,
                title="Distribution of Indicator Counts per Country",
            )
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q18, use_container_width=True, hide_index=True)

    with st.expander("Q19 · Countries with Debt Above Global Average", expanded=True):
        section("📈", "Above-Average Debt Countries", 19)
        q19 = run_query("""
            SELECT Country_name, SUM(Debt)/1e9 AS total_debt_bn
            FROM debt_records
            GROUP BY Country_name
            HAVING total_debt_bn > (
                SELECT AVG(country_total)
                FROM (
                    SELECT SUM(Debt)/1e9 AS country_total
                    FROM debt_records
                    GROUP BY Country_name
                ) sub
            )
            ORDER BY total_debt_bn DESC
        """)
        if not q19.empty:
            st.success(f"{len(q19)} countries are above the global average debt level.")
            fig = px.bar(
                q19, x="Country_name", y="total_debt_bn",
                color="total_debt_bn",
                color_continuous_scale=px.colors.sequential.Oranges,
                labels={"total_debt_bn": "Total Debt (Bn USD)", "Country_name": "Country"},
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(height=350, coloraxis_showscale=False,
                              margin=dict(l=0, r=0, t=10, b=0))
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q19.style.format({"total_debt_bn": "{:,.2f}"}),
                         use_container_width=True, hide_index=True)

    with st.expander("Q20 · Country Rankings by Total Debt", expanded=False):
        section("🥇", "Country Debt Rankings (High → Low)", 20)
        q20 = run_query("""
            SELECT RANK() OVER (ORDER BY SUM(Debt) DESC) AS debt_rank,
                   Country_name,
                   SUM(Debt)/1e9 AS total_debt_bn
            FROM debt_records
            WHERE Country_name NOT LIKE '%income%'
            AND Country_name NOT LIKE '%IDA%'
            AND Country_name NOT LIKE '%IBRD%'
            AND Country_name NOT LIKE '%classification%'
            AND Country_name NOT LIKE '%total%'
            GROUP BY Country_name
            ORDER BY debt_rank
        """)
        if not q20.empty:
            fig = px.bar(
                q20.head(30), x="Country_name", y="total_debt_bn",
                color="total_debt_bn",
                color_continuous_scale=SEQUENTIAL_BLUES,
                labels={"total_debt_bn": "Total Debt (Bn USD)", "Country_name": "Country"},
                template=PLOTLY_TEMPLATE,
                title="Top 30 Country Debt Rankings",
            )
            fig.update_layout(height=380, coloraxis_showscale=False,
                              margin=dict(l=0, r=0, t=30, b=0))
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(
                q20.style.format({"total_debt_bn": "{:,.2f}", "debt_rank": "{:.0f}"}),
                use_container_width=True, hide_index=True, height=400,
            )
        st.code("""SELECT RANK() OVER (ORDER BY SUM(Debt) DESC) AS debt_rank,
       Country_name, SUM(Debt)/1e9 AS total_debt_bn
FROM debt_records GROUP BY Country_name ORDER BY debt_rank;""", language="sql")


# ═══════════════════════════════════════════════════════════════════════
# PAGE: ADVANCED  (Q21 – Q30)
# ═══════════════════════════════════════════════════════════════════════
elif page == "🔴 Advanced (Q21–Q30)":
    st.title("🔴 Advanced SQL Queries — Q21 to Q30")
    st.write("Window functions, CTEs, views, and complex aggregations.")
    st.divider()

    with st.expander("Q21 · Top 5 Indicators — Global Debt Contribution", expanded=True):
        section("🎯", "Top 5 Indicators by Global Debt", 21)
        q21 = run_query("""
            SELECT Series_name AS indicator,
                   SUM(Debt)/1e9 AS total_debt_bn,
                   ROUND(SUM(Debt)*100.0/(SELECT SUM(Debt) FROM debt_records), 2) AS pct
            FROM debt_records
            GROUP BY Series_name
            ORDER BY total_debt_bn DESC
            LIMIT 5
        """)
        if not q21.empty:
            fig = px.funnel(
                q21, x="total_debt_bn", y="indicator",
                color_discrete_sequence=[PRIMARY],
                labels={"total_debt_bn": "Total Debt (Bn USD)", "indicator": "Indicator"},
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(height=350, margin=dict(l=10, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q21.style.format({"total_debt_bn": "{:,.2f}", "pct": "{:.2f}%"}),
                         use_container_width=True, hide_index=True)

    # ✅ FIX: All code properly indented inside the expander
    # ✅ FIX: Removed stray comment from inside the SQL string
    with st.expander("Q22 · Country % Contribution to Global Debt", expanded=False):
        section("🌍", "Each Country's Share of Global Debt", 22)
        q22 = run_query("""
            SELECT Country_name,
                   SUM(Debt)/1e9 AS total_debt_bn,
                   ROUND(SUM(Debt)*100.0/(SELECT SUM(Debt) FROM debt_records), 4) AS pct_contribution
            FROM debt_records
            WHERE Country_name NOT LIKE '%income%'
            AND Country_name NOT LIKE '%IDA%'
            AND Country_name NOT LIKE '%IBRD%'
            AND Country_name NOT LIKE '%classification%'
            AND Country_name NOT LIKE '%total%'
            GROUP BY Country_name
            ORDER BY pct_contribution DESC
        """)
        if not q22.empty:
            top15 = q22.head(15)

            fig = px.line_polar(
                top15,
                r="pct_contribution",
                theta="Country_name",
                line_close=True,
                color_discrete_sequence=[PRIMARY],
                template=PLOTLY_TEMPLATE,
            )
            fig.update_traces(fill='toself', line_width=3)
            fig.update_layout(
                title="🌐 Top Countries by Global Debt Contribution",
                title_x=0.25,
                height=600,
                margin=dict(l=20, r=20, t=60, b=20),
                polar=dict(radialaxis=dict(visible=True, ticksuffix="%")),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                q22.style.format({
                    "total_debt_bn": "{:,.2f}",
                    "pct_contribution": "{:.4f}%",
                }),
                use_container_width=True,
                hide_index=True,
            )

    # ✅ FIX: All visualizations properly indented inside the expander
    with st.expander("Q23 · Top 3 Countries per Indicator", expanded=False):
        section("🏅", "Top 3 Countries for Each Indicator", 23)
        q23 = run_query("""
            SELECT indicator, Country_name, total_debt_bn, rnk
            FROM (
                SELECT Series_name AS indicator,
                       Country_name,
                       SUM(Debt)/1e9 AS total_debt_bn,
                       ROW_NUMBER() OVER (PARTITION BY Series_name ORDER BY SUM(Debt) DESC) AS rnk
                FROM debt_records
                GROUP BY Series_name, Country_name
            ) ranked
            WHERE rnk <= 3
            ORDER BY indicator, rnk
        """)
        if not q23.empty:
            # Medal labels
            medal_map = {1: "🥇 1st", 2: "🥈 2nd", 3: "🥉 3rd"}
            q23["rank_label"] = q23["rnk"].map(medal_map)

            # ── Filter ────────────────────────────────────────────────
            indicator_filter = st.selectbox(
                "Filter by Indicator",
                ["All"] + sorted(q23["indicator"].unique().tolist()),
            )
            df_show = q23 if indicator_filter == "All" else q23[q23["indicator"] == indicator_filter]

            # ── Raw table ─────────────────────────────────────────────
            st.dataframe(
                df_show[["indicator", "Country_name", "total_debt_bn", "rank_label"]]
                .rename(columns={"rank_label": "rank"})
                .style.format({"total_debt_bn": "{:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            # ── VIZ 1: Grouped bar — only when a single indicator selected ─
            if indicator_filter != "All":
                st.markdown("#### 🏆 Debt Comparison – Top 3 Countries")
                color_map = {"🥇 1st": "#FFD700", "🥈 2nd": "#C0C0C0", "🥉 3rd": "#CD7F32"}
                fig_bar = px.bar(
                    df_show.sort_values("rnk"),
                    x="Country_name",
                    y="total_debt_bn",
                    color="rank_label",
                    color_discrete_map=color_map,
                    text="total_debt_bn",
                    labels={
                        "total_debt_bn": "Total Debt (Billion $)",
                        "Country_name": "Country",
                        "rank_label": "Rank",
                    },
                    title=f"Top 3 Countries · {indicator_filter}",
                    template=PLOTLY_TEMPLATE,
                )
                fig_bar.update_traces(texttemplate="%{text:,.2f}B", textposition="outside")
                fig_bar.update_layout(
                    height=380,
                    showlegend=True,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
                    margin=dict(l=0, r=0, t=40, b=0),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # ── VIZ 2: Countries that dominate (rank #1 most often) ───
            st.markdown("#### 🌍 Which Countries Dominate? (Rank #1 Winners)")
            df_top1 = q23[q23["rnk"] == 1]
            win_counts = (
                df_top1.groupby("Country_name")
                .size()
                .reset_index(name="indicators_led")
                .sort_values("indicators_led", ascending=False)
                .head(15)
            )
            fig_wins = px.bar(
                win_counts,
                x="indicators_led",
                y="Country_name",
                orientation="h",
                color="indicators_led",
                color_continuous_scale="Oranges",
                labels={"indicators_led": "# Indicators Led", "Country_name": "Country"},
                title="Countries with Most #1 Rankings Across Indicators",
                template=PLOTLY_TEMPLATE,
            )
            fig_wins.update_layout(
                height=420,
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                margin=dict(l=0, r=0, t=40, b=0),
            )
            st.plotly_chart(fig_wins, use_container_width=True)

            # ── VIZ 4: Podium summary cards ───────────────────────────
            st.markdown("#### 🎖️ Overall Podium — Total Debt Across All Indicators")
            podium = (
                q23.groupby("Country_name")["total_debt_bn"]
                .sum()
                .reset_index()
                .sort_values("total_debt_bn", ascending=False)
                .head(3)
            )
            cols = st.columns(3)
            medals = ["🥇", "🥈", "🥉"]
            for i, (col, (_, row)) in enumerate(zip(cols, podium.iterrows())):
                col.metric(
                    label=f"{medals[i]} #{i+1} Country",
                    value=row["Country_name"],
                    delta=f"${row['total_debt_bn']:,.2f}B total debt",
                )

    with st.expander("Q24 · Max – Min Debt Range per Country", expanded=False):
        section("📐", "Debt Range (Max − Min) per Country", 24)
        q24 = run_query("""
            SELECT Country_name,
                   MAX(Debt)/1e9  AS max_debt_bn,
                   MIN(Debt)/1e9  AS min_debt_bn,
                   (MAX(Debt)-MIN(Debt))/1e9 AS debt_range_bn
            FROM debt_records
            GROUP BY Country_name
            ORDER BY debt_range_bn DESC
            LIMIT 20
        """)
        if not q24.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Max Debt",
                x=q24["Country_name"], y=q24["max_debt_bn"],
                marker_color=DANGER,
            ))
            fig.add_trace(go.Bar(
                name="Min Debt",
                x=q24["Country_name"], y=q24["min_debt_bn"],
                marker_color=SUCCESS,
            ))
            fig.update_layout(
                barmode="group", template=PLOTLY_TEMPLATE,
                height=380, xaxis_tickangle=45,
                legend=dict(orientation="h", y=1.1),
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q24.style.format({
                "max_debt_bn":   "{:,.2f}",
                "min_debt_bn":   "{:,.4f}",
                "debt_range_bn": "{:,.2f}",
            }), use_container_width=True, hide_index=True)

    with st.expander("Q25 · VIEW — Top 10 Countries with Highest Debt", expanded=False):
        section("👁️", "View: vw_top10_countries_debt", 25)
        st.code("""
-- Create view (run once in MySQL)
CREATE OR REPLACE VIEW vw_top10_countries_debt AS
    SELECT Country_name, SUM(Debt)/1e9 AS total_debt_bn
    FROM debt_records
    GROUP BY Country_name
    ORDER BY total_debt_bn DESC
    LIMIT 10;

-- Query the view
SELECT * FROM vw_top10_countries_debt;
        """, language="sql")
        q25 = run_query("""
            SELECT Country_name, SUM(Debt)/1e9 AS total_debt_bn
            FROM debt_records
            GROUP BY Country_name
            ORDER BY total_debt_bn DESC
            LIMIT 10
        """)
        if not q25.empty:
            fig = px.bar(
                q25, x="Country_name", y="total_debt_bn",
                color="total_debt_bn",
                color_continuous_scale=SEQUENTIAL_BLUES,
                labels={"total_debt_bn": "Total Debt (Bn USD)", "Country_name": "Country"},
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(height=320, coloraxis_showscale=False,
                              margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Q26 · Debt Category: High / Medium / Low", expanded=True):
        section("🏷️", "Categorize Countries — High / Medium / Low Debt", 26)
        q26 = run_query("""
            SELECT Country_name,
                   SUM(Debt)/1e9 AS total_debt_bn,
                   CASE
                       WHEN SUM(Debt)/1e9 >= 500 THEN 'High Debt'
                       WHEN SUM(Debt)/1e9 >= 50  THEN 'Medium Debt'
                       ELSE 'Low Debt'
                   END AS debt_category
            FROM debt_records
            GROUP BY Country_name
            ORDER BY total_debt_bn DESC
        """)
        if not q26.empty:
            cat_counts = q26["debt_category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]

            col1, col2 = st.columns([1, 2])
            with col1:
                fig_pie = px.pie(
                    cat_counts, values="Count", names="Category",
                    color="Category",
                    color_discrete_map={
                        "High Debt":   DANGER,
                        "Medium Debt": ACCENT,
                        "Low Debt":    SUCCESS,
                    },
                    hole=0.45, template=PLOTLY_TEMPLATE,
                )
                fig_pie.update_layout(height=300, showlegend=True,
                                      margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                fig_bar = px.bar(
                    q26, x="Country_name", y="total_debt_bn",
                    color="debt_category",
                    color_discrete_map={
                        "High Debt":   DANGER,
                        "Medium Debt": ACCENT,
                        "Low Debt":    SUCCESS,
                    },
                    labels={"total_debt_bn": "Total Debt (Bn USD)", "Country_name": "Country"},
                    template=PLOTLY_TEMPLATE,
                )
                fig_bar.update_layout(
                    height=300, xaxis_visible=False,
                    legend=dict(orientation="h", y=1.1),
                    margin=dict(l=0, r=0, t=10, b=0),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            st.dataframe(q26.style.format({"total_debt_bn": "{:,.2f}"}),
                         use_container_width=True, hide_index=True)

    with st.expander("Q27 · Cumulative Debt per Country (Window Function)", expanded=False):
        section("📈", "Cumulative Debt Over Time using Window Functions", 27)
        country_list = run_query(
            "SELECT DISTINCT Country_name FROM debt_records ORDER BY Country_name"
        )
        if not country_list.empty:
            sel_country = st.selectbox(
                "Select Country",
                country_list["Country_name"].tolist(),
                index=0,
            )
            q27 = run_query(f"""
                SELECT Year, Debt/1e9 AS debt_bn,
                       SUM(Debt/1e9) OVER (ORDER BY Year) AS cumulative_debt_bn
                FROM debt_records
                WHERE Country_name = '{sel_country}'
                ORDER BY Year
            """)
            if not q27.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=q27["Year"], y=q27["debt_bn"],
                    name="Annual Debt", marker_color=SECONDARY, opacity=0.6,
                ))
                fig.add_trace(go.Scatter(
                    x=q27["Year"], y=q27["cumulative_debt_bn"],
                    name="Cumulative Debt",
                    line=dict(color=PRIMARY, width=2.5),
                    yaxis="y2",
                ))
                fig.update_layout(
                    yaxis=dict(title="Annual Debt (Bn USD)"),
                    yaxis2=dict(title="Cumulative (Bn USD)", overlaying="y", side="right"),
                    legend=dict(orientation="h", y=1.1),
                    template=PLOTLY_TEMPLATE,
                    height=360,
                    margin=dict(l=0, r=0, t=10, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)

    with st.expander("Q28 · Indicators with Avg Debt > Overall Average", expanded=False):
        section("📊", "Above-Average Indicators", 28)
        q28 = run_query("""
            SELECT Series_name AS indicator, AVG(Debt)/1e9 AS avg_debt_bn
            FROM debt_records
            GROUP BY Series_name
            HAVING avg_debt_bn > (SELECT AVG(Debt)/1e9 FROM debt_records)
            ORDER BY avg_debt_bn DESC
        """)
        if not q28.empty:
            st.success(f"{len(q28)} indicators have above-average debt.")
            fig = px.bar(
                q28, x="avg_debt_bn", y="indicator",
                orientation="h",
                color="avg_debt_bn",
                color_continuous_scale=px.colors.sequential.Purples,
                labels={"avg_debt_bn": "Avg Debt (Bn USD)", "indicator": ""},
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(
                height=max(300, len(q28)*28),
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

    with st.expander("Q29 · Countries Contributing > 5% of Global Debt", expanded=True):
        section("🌐", "Countries with 5%+ Share of Global Debt", 29)
        q29 = run_query("""
            SELECT Country_name,
                   SUM(Debt)/1e9 AS total_debt_bn,
                   ROUND(SUM(Debt)*100.0/(SELECT SUM(Debt) FROM debt_records), 2) AS pct
            FROM debt_records
            GROUP BY Country_name
            HAVING pct > 5
            ORDER BY pct DESC
        """)
        if not q29.empty:
            fig = px.treemap(
                q29,
                path=["Country_name"],
                values="pct",
                color="pct",
                color_continuous_scale=SEQUENTIAL_BLUES,
                labels={"pct": "% of Global Debt"},
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q29.style.format({"total_debt_bn": "{:,.2f}", "pct": "{:.2f}%"}),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No country contributes more than 5% of global debt.")

    with st.expander("Q30 · Most Dominant Indicator per Country", expanded=False):
        section("👑", "Top Indicator (Highest Contribution) for Each Country", 30)
        q30 = run_query("""
            SELECT Country_name, indicator, max_debt_bn
            FROM (
                SELECT Country_name,
                       Series_name AS indicator,
                       SUM(Debt)/1e9 AS max_debt_bn,
                       RANK() OVER (
                           PARTITION BY Country_name
                           ORDER BY SUM(Debt) DESC
                       ) AS rnk
                FROM debt_records
                GROUP BY Country_name, Series_name
            ) ranked
            WHERE rnk = 1
            ORDER BY max_debt_bn DESC
        """)
        if not q30.empty:
            top_inds = q30["indicator"].value_counts().head(10).reset_index()
            top_inds.columns = ["Indicator", "Count"]
            fig = px.bar(
                top_inds, x="Count", y="Indicator",
                orientation="h",
                color="Count",
                color_continuous_scale=SEQUENTIAL_BLUES,
                labels={"Count": "# Countries", "Indicator": ""},
                template=PLOTLY_TEMPLATE,
                title="Most Common Dominant Indicators Across Countries",
            )
            fig.update_layout(
                height=360, coloraxis_showscale=False,
                yaxis=dict(autorange="reversed"),
                margin=dict(l=0, r=0, t=30, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(q30.style.format({"max_debt_bn": "{:,.2f}"}),
                         use_container_width=True, hide_index=True)
        st.code("""
SELECT Country_name, indicator, max_debt_bn
FROM (
    SELECT Country_name,
           Series_name AS indicator,
           SUM(Debt)/1e9 AS max_debt_bn,
           RANK() OVER (PARTITION BY Country_name ORDER BY SUM(Debt) DESC) AS rnk
    FROM debt_records
    GROUP BY Country_name, Series_name
) ranked
WHERE rnk = 1
ORDER BY max_debt_bn DESC;
        """, language="sql")


# ═══════════════════════════════════════════════════════════════════════
# PAGE: GLOBAL MAP
# ═══════════════════════════════════════════════════════════════════════
elif page == "🗺️ Global Map":
    st.title("🗺️ Global Debt Map")
    st.write("Choropleth view of debt distribution across all countries.")
    st.divider()

    year_options = list(range(2000, 2025))
    sel_year     = st.select_slider("Select Year for Map", options=year_options, value=2022)

    q_year_map = run_query(f"""
        SELECT Country_code AS iso3,
               Country_name,
               SUM(Debt)/1e9 AS total_debt_bn
        FROM debt_records
        WHERE Year = {sel_year}
        GROUP BY Country_code, Country_name
        ORDER BY total_debt_bn DESC
    """)

    if not q_year_map.empty:
        fig_map = px.choropleth(
            q_year_map,
            locations="iso3",
            locationmode="ISO-3",
            color="total_debt_bn",
            hover_name="Country_name",
            hover_data={"total_debt_bn": ":.2f"},
            color_continuous_scale=SEQUENTIAL_BLUES,
            labels={"total_debt_bn": "Debt (Bn USD)"},
            title=f"International Debt Distribution — {sel_year}",
            template=PLOTLY_TEMPLATE,
        )
        fig_map.update_layout(
            height=550,
            geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_map, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"🔝 Top 10 Countries — {sel_year}")
            st.dataframe(
                q_year_map.head(10).style.format({"total_debt_bn": "{:,.2f}"}),
                use_container_width=True, hide_index=True,
            )
        with col2:
            st.subheader(f"📉 Bottom 10 Countries — {sel_year}")
            bottom = q_year_map.sort_values("total_debt_bn").head(10)
            st.dataframe(
                bottom.style.format({"total_debt_bn": "{:,.4f}"}),
                use_container_width=True, hide_index=True,
            )
    else:
        st.warning(f"No data found for year {sel_year}.")


# ═══════════════════════════════════════════════════════════════════════
# PAGE: RAW DATA EXPLORER
# ═══════════════════════════════════════════════════════════════════════
elif page == "📋 Raw Data Explorer":
    st.title("📋 Raw Data Explorer")
    st.write("Browse and filter the debt_records table directly.")
    st.divider()

    col1, col2, col3 = st.columns(3)

    countries_list  = run_query("SELECT DISTINCT Country_name FROM debt_records ORDER BY Country_name")
    indicators_list = run_query("SELECT DISTINCT Series_name  FROM debt_records ORDER BY Series_name")

    with col1:
        sel_countries = st.multiselect(
            "Filter Countries",
            countries_list["Country_name"].tolist() if not countries_list.empty else [],
            default=[],
        )
    with col2:
        sel_indicators = st.multiselect(
            "Filter Indicators",
            indicators_list["Series_name"].tolist() if not indicators_list.empty else [],
            default=[],
        )
    with col3:
        year_range = st.slider("Year Range", 2000, 2024, (2010, 2022))

    where_parts = [f"Year BETWEEN {year_range[0]} AND {year_range[1]}"]
    if sel_countries:
        esc = "', '".join(sel_countries)
        where_parts.append(f"Country_name IN ('{esc}')")
    if sel_indicators:
        esc2 = "', '".join(sel_indicators)
        where_parts.append(f"Series_name IN ('{esc2}')")

    where_sql = " AND ".join(where_parts)
    q_raw = run_query(f"""
        SELECT Country_name, Country_code, Series_name AS indicator, Year, Debt
        FROM debt_records
        WHERE {where_sql}
        ORDER BY Debt DESC
        LIMIT 2000
    """)

    st.write(f"**{len(q_raw):,} records** (max 2,000 shown)")
    if not q_raw.empty:
        st.dataframe(
            q_raw.style.format({"Debt": "${:,.0f}"}),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        csv = q_raw.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Filtered Data (CSV)",
            data=csv,
            file_name="filtered_debt_data.csv",
            mime="text/csv",
        )

        if sel_countries and len(sel_countries) <= 10:
            st.subheader("📈 Debt Trend for Selected Countries")
            trend            = q_raw.groupby(["Country_name", "Year"])["Debt"].sum().reset_index()
            trend["Debt_bn"] = trend["Debt"] / 1e9
            fig = px.line(
                trend, x="Year", y="Debt_bn",
                color="Country_name",
                labels={"Debt_bn": "Total Debt (Bn USD)"},
                template=PLOTLY_TEMPLATE,
                markers=True,
            )
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)