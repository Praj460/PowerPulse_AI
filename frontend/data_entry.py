import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.sheets_loader import append_row_to_sheet

def show():
    st.title("➕ Data Entry — Add New DAB Record (Auto-calculated fields)")

    # User-input parameters
    V_dc1 = st.number_input("Primary Voltage (V_dc1)", min_value=0.0, value=160.0)
    V_dc2 = st.number_input("Secondary Voltage (V_dc2)", min_value=0.0, value=100.0)
    I_dc1 = st.number_input("Primary Current (I_dc1)", min_value=0.0, value=10.0)
    I_dc2 = st.number_input("Secondary Current (I_dc2)", min_value=0.0, value=15.0)
    delta_1 = st.slider("Primary Duty Cycle (delta_1)", 0.0, 1.0, 0.5)
    delta_2 = st.slider("Secondary Duty Cycle (delta_2)", 0.0, 1.0, 0.4)
    phi = st.slider("Phase Shift (phi)", 0.0, 1.0, 0.3)
    ZVS_status = st.selectbox("ZVS Status", [True, False])

    # Calculated fields
    input_power = V_dc1 * I_dc1
    load_power = V_dc2 * I_dc2
    power_loss = input_power - load_power
    L_total = 10 - 2 * phi + np.random.normal(0, 0.05)
    R_total = 30 + 10 * (1 - delta_1) + np.random.normal(0, 0.2)
    efficiency = 98 - (R_total - 30)*0.05 - (10 - L_total)*0.3 + np.random.normal(0, 0.2)
    efficiency = np.clip(efficiency, 94, 98)
    temperature = 35 + (98 - efficiency) * 6 + np.random.normal(0, 1)
    temperature = np.clip(temperature, 35, 65)
    switching_loss = 0.03 * input_power + np.random.normal(0, 0.2)
    conduction_loss = 0.01 * input_power + 0.05 * R_total + np.random.normal(0, 0.1)

    st.markdown("---")
    st.subheader("Calculated Fields (auto-filled):")
    st.write(f"**L_total (μH):** {L_total:.3f}")
    st.write(f"**R_total (mΩ):** {R_total:.2f}")
    st.write(f"**Efficiency (%):** {efficiency:.2f}")
    st.write(f"**Temperature (°C):** {temperature:.1f}")
    st.write(f"**Power Loss (W):** {power_loss:.2f}")
    st.write(f"**Switching Loss (W):** {switching_loss:.2f}")
    st.write(f"**Conduction Loss (W):** {conduction_loss:.2f}")

    if st.button("Submit"):
        row = [
            str(pd.Timestamp.now()), V_dc1, V_dc2, I_dc1, I_dc2,
            delta_1, delta_2, phi, L_total, R_total, efficiency,
            temperature, ZVS_status, input_power, load_power, power_loss,
            switching_loss, conduction_loss
        ]
        append_row_to_sheet(row)
        st.success("Row added to Google Sheets!")
