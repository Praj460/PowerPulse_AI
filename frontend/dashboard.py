import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.sheets_loader import load_sheets_data
from backend.diagnostics import add_health_scores

def show():
    st.title("📈 DAB HealthAI — Analytics Dashboard")
    df = load_sheets_data()
    df = add_health_scores(df)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Date range filter
    min_date, max_date = df['timestamp'].min(), df['timestamp'].max()
    date_range = st.sidebar.date_input(
        "Select date range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    if isinstance(date_range, list) or isinstance(date_range, tuple):
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        df_view = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    else:
        df_view = df

    st.line_chart(df_view.set_index('timestamp')['efficiency_percent'])
    st.line_chart(df_view.set_index('timestamp')[['power_loss_W', 'switching_loss_W', 'conduction_loss_W']])
    st.line_chart(df_view.set_index('timestamp')['health_score'])

    if not df_view.empty:
        latest = df_view.iloc[-1]
        st.metric("Latest Efficiency (%)", f"{latest['efficiency_percent']:.2f}")
        st.metric("Latest Temperature (°C)", f"{latest['temperature_C']:.1f}")
        st.metric("Health Score", f"{latest['health_score']:.1f}")
    else:
        st.warning("No data for this range.")

    with st.expander("See raw data"):
        st.dataframe(df_view.tail(30))
