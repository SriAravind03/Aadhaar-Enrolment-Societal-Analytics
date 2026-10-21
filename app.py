import os

import streamlit as st
import plotly.express as px

from preprocess import load_and_clean
from analysis import time_trends, district_pressure, migration_clusters
from anomaly import detect_anomalies
from forecast import forecast_demand

st.set_page_config(layout="wide")
st.title("Aadhaar Enrolment Societal Analytics Dashboard")

# ---------- LOAD DATA ----------

# Use your real dataset if present, otherwise the bundled synthetic sample.
DATA_PATH = "data/aadhaar.csv" if os.path.exists("data/aadhaar.csv") else "data/sample_aadhaar.csv"
df = load_and_clean(DATA_PATH)

# ---------- FILTERS ------------

state = st.selectbox("Select State", ["All"] + sorted(df['state'].unique().tolist()))
district = st.selectbox("Select District", ["All"] + sorted(df['district'].unique().tolist()))

if state != "All":
    df = df[df['state'] == state]
if district != "All":
    df = df[df['district'] == district]

# ---------- TRENDS -------------

st.subheader("📈 Enrolment Trends Over Time")
trend = time_trends(df)
fig1 = px.line(trend, x="date", y="total")
st.plotly_chart(fig1, use_container_width=True)

# ---------- DISTRICT LOAD -------

st.subheader("🏙 District Enrollment Pressure")
pressure = district_pressure(df)
fig2 = px.bar(pressure.head(10), x="district", y="total")
st.plotly_chart(fig2, use_container_width=True)

# ---------- MIGRATION CLUSTERS ---

st.subheader("🧭 Pincode Migration / Growth Clusters")
clusters = migration_clusters(df)
fig3 = px.scatter(clusters, x="pincode", y="total", color="cluster")
st.plotly_chart(fig3, use_container_width=True)

# ---------- ANOMALIES ------------

st.subheader("🚨 Abnormal Enrolment Surges")
anoms = detect_anomalies(df)
st.dataframe(anoms[['date','district','pincode','total']].head(50))

# ---------- FORECAST -------------

st.subheader("🔮 Future Demand Forecast")
forecast = forecast_demand(df)
fig4 = px.line(forecast, x="ds", y="yhat")
st.plotly_chart(fig4, use_container_width=True)

# ---------- POLICY INSIGHTS ------

st.subheader("🧠 AI Policy Insights")

if len(anoms) > 10:
    st.warning("Sudden regional surges detected → Possible migration or event-based demand")

if pressure['total'].max() > pressure['total'].mean() * 2:
    st.info("High load districts → Recommend new enrollment centers")

st.success("System operating within expected patterns")
