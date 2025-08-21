import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.simulator import DABSimulator
from backend.diagnostics import add_health_scores

def show():
    st.title("🔬 DAB Simulator")
    st.write("Simulate DAB converter performance with different parameters.")
    
    # Initialize simulator
    simulator = DABSimulator()
    
    # Sidebar for parameter controls
    st.sidebar.header("Parameters")
    
    # Key parameter sliders
    phi = st.sidebar.slider(
        "φ (Phase Shift)", 
        min_value=0.0, 
        max_value=1.57, 
        value=0.3, 
        step=0.01
    )
    
    Pload = st.sidebar.slider(
        "Load Power (W)", 
        min_value=100.0, 
        max_value=5000.0, 
        value=1000.0, 
        step=100.0
    )
    
    delta1 = st.sidebar.slider(
        "δ₁ (Duty Cycle 1)", 
        min_value=0.1, 
        max_value=0.9, 
        value=0.5, 
        step=0.05
    )
    
    delta2 = st.sidebar.slider(
        "δ₂ (Duty Cycle 2)", 
        min_value=0.1, 
        max_value=0.9, 
        value=0.5, 
        step=0.05
    )
    
    # Run simulation with simplified parameters
    params = {
        'Vdc1': 400.0,
        'Vdc2': 48.0,
        'phi': phi,
        'delta1': delta1,
        'delta2': delta2,
        'Pload': Pload,
        'fsw': 100000,
        'L': 50e-6,
        'R_on': 0.1,
        'C_oss': 100e-12
    }
    
    # Run simulation
    results = simulator.run_simulation(params)
    
    # Display results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Efficiency", 
            f"{results['efficiency']:.1f}%"
        )
    
    with col2:
        st.metric(
            "Temperature", 
            f"{results['temperature']:.1f}°C"
        )
    
    with col3:
        zvs_status = results['zvs_status']
        st.metric(
            "ZVS Status", 
            "✅ ZVS" if zvs_status else "❌ No ZVS"
        )
    
    # Basic recommendations
    st.subheader("Recommendations")
    
    from backend.recommendations import DABRecommendations
    recommender = DABRecommendations()
    
    # Create mock dataframe for recommendations
    mock_data = pd.DataFrame([{
        'timestamp': pd.Timestamp.now(),
        'efficiency_percent': results['efficiency'],
        'temperature_C': results['temperature'],
        'health_score': 85.0,
        'ZVS_status': results['zvs_status']
    }])
    
    recommendations = recommender.generate_recommendations(mock_data)
    
    if recommendations:
        for rec in recommendations:
            st.write(f"• {rec}")
    else:
        st.success("✅ All parameters are within optimal ranges!")
    
    # Show current parameters
    st.subheader("Current Parameters")
    st.write(f"• Phase Shift: {phi:.3f} rad")
    st.write(f"• Load Power: {Pload:.0f} W")
    st.write(f"• Duty Cycles: δ₁={delta1:.2f}, δ₂={delta2:.2f}")
