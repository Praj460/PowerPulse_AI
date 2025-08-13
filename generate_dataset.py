import numpy as np
import pandas as pd
from datetime import datetime, timedelta

num_samples = 365
start_date = datetime(2024, 1, 1)
timestamps = [start_date + timedelta(days=i) for i in range(num_samples)]
np.random.seed(42)

# Only simulate MEASURED values:
V_dc1 = np.random.normal(160, 3, num_samples)
I_dc1 = np.random.normal(10, 0.5, num_samples)

# Generate secondary as a realistic fraction of primary (e.g., 85–98%)
v_fraction = np.random.uniform(0.85, 0.98, num_samples)
i_fraction = np.random.uniform(0.85, 0.98, num_samples)

V_dc2 = V_dc1 * v_fraction
I_dc2 = I_dc1 * i_fraction

# Generate duty cycles and phase shift
delta_1 = np.random.uniform(0.4, 0.6, num_samples)
delta_2 = np.random.uniform(0.3, 0.5, num_samples)
phi = np.random.uniform(0.2, 0.4, num_samples)

input_power_W = V_dc1 * I_dc1
load_power_W = V_dc2 * I_dc2
power_loss_W = input_power_W - load_power_W

# L_total (μH) - from DAB formula
f = 100_000
n = 1
min_delta = np.minimum(delta_1, delta_2)
safe_phi = np.clip(phi, 0.05, None)
L_total = (n * V_dc1 * V_dc2) / (2 * np.pi * f * input_power_W * min_delta * np.sin(safe_phi))
L_total = np.abs(L_total) * 1e6 + np.random.normal(0, 0.05, num_samples)  # μH

# R_total (mΩ)
R_total = (np.abs(V_dc1 - V_dc2) / (I_dc1 + I_dc2)) * 1000 + np.random.normal(0, 1, num_samples)

# Efficiency (%)
efficiency = (load_power_W / input_power_W) * 100
efficiency += np.random.normal(0, 0.1, num_samples)  # minimal noise
efficiency = np.clip(efficiency, 94, 98)  # physically plausible range

# Temperature (°C) - rise proportional to power loss
temperature = 40 + power_loss_W * 0.025 + np.random.normal(0, 0.5, num_samples)
temperature = np.clip(temperature, 35, 65)

# ZVS_status (based on logical criteria)
ZVS_status = (temperature < 60) & (R_total < 45) & (L_total > 8.5)

# Advanced loss formulas (optional, or use proxies)
switching_loss_W = 0.03 * input_power_W + np.random.normal(0, 0.2, num_samples)
conduction_loss_W = 0.01 * input_power_W + 0.05 * R_total + np.random.normal(0, 0.1, num_samples)

# --- DataFrame ---
data = pd.DataFrame({
    'timestamp': timestamps,
    'V_dc1': np.round(V_dc1, 2),
    'V_dc2': np.round(V_dc2, 2),
    'I_dc1': np.round(I_dc1, 2),
    'I_dc2': np.round(I_dc2, 2),
    'delta_1': np.round(delta_1, 3),
    'delta_2': np.round(delta_2, 3),
    'phi': np.round(phi, 3),
    'L_total_uH': np.round(L_total, 3),
    'R_total_mOhm': np.round(R_total, 2),
    'efficiency_percent': np.round(efficiency, 2),
    'temperature_C': np.round(temperature, 1),
    'ZVS_status': ZVS_status,
    'input_power_W': np.round(input_power_W, 2),
    'load_power_W': np.round(load_power_W, 2),
    'power_loss_W': np.round(power_loss_W, 3),
    'switching_loss_W': np.round(switching_loss_W, 3),
    'conduction_loss_W': np.round(conduction_loss_W, 3)
})

data.to_csv('data/dab_converter_historical_dataset.csv', index=False)
print("Dataset saved to data/dab_converter_historical_dataset.csv")
print(data.head())
