import streamlit as st
import pandas as pd
from utils.db import fetch_user_events, fetch_ratings
from utils.analytics import kpis

st.title("📊 Analytics Dashboard")

# check user permissions
user = st.session_state.get("user")
if not user or user["role"] not in ("Admin", "Analyst"):
    st.warning("Analyst/Admin only. Please login with sufficient permissions.")
    st.stop()

# --- Key Metrics ---
st.write("### Key Metrics")
metrics = kpis()
st.json(metrics)

# --- Recent Events ---
st.write("### Recent Events")
events = pd.DataFrame(fetch_user_events())
if events.empty:
    st.info("No events logged yet.")
else:
    st.dataframe(events)

# --- Ratings Overview ---
st.write("### Ratings Overview")
ratings = pd.DataFrame(fetch_ratings())
if ratings.empty:
    st.info("No ratings recorded yet.")
else:
    st.dataframe(ratings)
