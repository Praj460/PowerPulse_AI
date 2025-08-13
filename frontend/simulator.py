import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.simulator import DABSimulator
from backend.diagnostics import add_health_scores

def show():
    st.title("🔬 DAB HealthAI — What-If Simulator")
    st.write("Simulate DAB converter performance with different parameters and predict efficiency, temperature, and ZVS regions.")
    
    # Initialize simulator
    simulator = DABSimulator()
    
    # Sidebar for parameter controls
    st.sidebar.header("Parameter Controls")
    
    # Parameter sliders
    st.sidebar.subheader("DC Voltages")
    Vdc1 = st.sidebar.slider(
        "Vdc1 (Primary DC Voltage)", 
        min_value=200.0, 
        max_value=800.0, 
        value=400.0, 
        step=10.0,
        help="Primary DC voltage in Volts"
    )
    
    Vdc2 = st.sidebar.slider(
        "Vdc2 (Secondary DC Voltage)", 
        min_value=12.0, 
        max_value=100.0, 
        value=48.0, 
        step=1.0,
        help="Secondary DC voltage in Volts"
    )
    
    st.sidebar.subheader("Control Parameters")
    phi = st.sidebar.slider(
        "φ (Phase Shift)", 
        min_value=0.0, 
        max_value=np.pi/2, 
        value=0.3, 
        step=0.01,
        help="Phase shift in radians"
    )
    
    delta1 = st.sidebar.slider(
        "δ₁ (Duty Cycle 1)", 
        min_value=0.1, 
        max_value=0.9, 
        value=0.5, 
        step=0.05,
        help="Primary duty cycle"
    )
    
    delta2 = st.sidebar.slider(
        "δ₂ (Duty Cycle 2)", 
        min_value=0.1, 
        max_value=0.9, 
        value=0.5, 
        step=0.05,
        help="Secondary duty cycle"
    )
    
    st.sidebar.subheader("Load & System")
    Pload = st.sidebar.slider(
        "Pload (Load Power)", 
        min_value=100.0, 
        max_value=5000.0, 
        value=1000.0, 
        step=100.0,
        help="Load power in Watts"
    )
    
    fsw = st.sidebar.slider(
        "fsw (Switching Frequency)", 
        min_value=50000, 
        max_value=200000, 
        value=100000, 
        step=5000,
        help="Switching frequency in Hz"
    )
    
    # Run simulation
    params = {
        'Vdc1': Vdc1,
        'Vdc2': Vdc2,
        'phi': phi,
        'delta1': delta1,
        'delta2': delta2,
        'Pload': Pload,
        'fsw': fsw,
        'L': 50e-6,
        'R_on': 0.1,
        'C_oss': 100e-12
    }
    
    # Run simulation
    results = simulator.run_simulation(params)
    
    # Display results
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Efficiency", 
            f"{results['efficiency']:.2f}%",
            delta=f"{results['efficiency'] - 95:.2f}%" if results['efficiency'] < 95 else None
        )
    
    with col2:
        st.metric(
            "Temperature", 
            f"{results['temperature']:.1f}°C",
            delta=f"{results['temperature'] - 60:.1f}°C" if results['temperature'] > 60 else None
        )
    
    with col3:
        zvs_status = results['zvs_status']['overall_zvs']
        st.metric(
            "ZVS Status", 
            "✅ ZVS" if zvs_status else "❌ No ZVS",
            delta="ZVS Active" if zvs_status else "ZVS Lost"
        )
    
    with col4:
        total_loss = results['losses']['total_loss']
        st.metric(
            "Total Loss", 
            f"{total_loss:.1f}W",
            delta=f"{total_loss - 100:.1f}W" if total_loss > 100 else None
        )
    
    # Detailed results
    st.subheader("Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**ZVS Status Details:**")
        zvs_details = results['zvs_status']
        st.write(f"• Leg 1 ZVS: {'✅' if zvs_details['leg1_zvs'] else '❌'}")
        st.write(f"• Leg 2 ZVS: {'✅' if zvs_details['leg2_zvs'] else '❌'}")
        st.write(f"• Overall ZVS: {'✅' if zvs_details['overall_zvs'] else '❌'}")
        
        st.write("**Power Losses:**")
        losses = results['losses']
        st.write(f"• Conduction Loss: {losses['conduction_loss']:.2f}W")
        st.write(f"• Switching Loss: {losses['switching_loss']:.2f}W")
        st.write(f"• Transformer Loss: {losses['transformer_loss']:.2f}W")
        st.write(f"• Total Loss: {losses['total_loss']:.2f}W")
    
    with col2:
        st.write("**Parameter Impact Analysis:**")
        
        # Analyze impact of parameter changes
        impact_analysis = {}
        for param_name in ['phi', 'delta1', 'delta2', 'Pload']:
            impact = simulator.get_parameter_impact(params, param_name, 0.1)
            impact_analysis[param_name] = impact
        
        for param_name, impact in impact_analysis.items():
            delta_eff = impact['delta']['efficiency']
            delta_temp = impact['delta']['temperature']
            
            st.write(f"**{param_name} (+10%):**")
            st.write(f"  • Efficiency: {delta_eff:+.2f}%")
            st.write(f"  • Temperature: {delta_temp:+.1f}°C")
    
    # ZVS Heatmap
    st.subheader("ZVS Region Heatmap")
    
    # Parameter selection for heatmap
    col1, col2 = st.columns(2)
    
    with col1:
        heatmap_param1 = st.selectbox(
            "X-axis parameter",
            ['phi', 'Pload', 'Vdc1', 'delta1'],
            index=0
        )
    
    with col2:
        heatmap_param2 = st.selectbox(
            "Y-axis parameter",
            ['Pload', 'phi', 'Vdc2', 'delta2'],
            index=0
        )
    
    # Generate heatmap
    if st.button("Generate ZVS Heatmap"):
        with st.spinner("Generating ZVS heatmap..."):
            # Define ranges for heatmap
            ranges = {
                'phi': (0, np.pi/2, 50),
                'Pload': (100, 5000, 50),
                'Vdc1': (200, 800, 50),
                'Vdc2': (12, 100, 50),
                'delta1': (0.1, 0.9, 50),
                'delta2': (0.1, 0.9, 50)
            }
            
            param1_range = ranges[heatmap_param1]
            param2_range = ranges[heatmap_param2]
            
            X, Y, Z = simulator.generate_zvs_heatmap(
                heatmap_param1, heatmap_param2, 
                param1_range, param2_range
            )
            
            # Create heatmap using plotly
            fig = go.Figure(data=go.Heatmap(
                z=Z,
                x=X[0, :],
                y=Y[:, 0],
                colorscale='RdYlGn',
                zmin=0,
                zmax=1,
                hovertemplate='<b>%{xaxis.title.text}</b>: %{x}<br>' +
                            '<b>%{yaxis.title.text}</b>: %{y}<br>' +
                            '<b>ZVS Status</b>: %{z}<br>' +
                            '<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"ZVS Region Heatmap: {heatmap_param1} vs {heatmap_param2}",
                xaxis_title=heatmap_param1,
                yaxis_title=heatmap_param2,
                width=800,
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ZVS statistics
            zvs_percentage = (Z == 1).sum() / Z.size * 100
            st.write(f"**ZVS Coverage:** {zvs_percentage:.1f}% of the parameter space")
    
    # Parameter optimization suggestions
    st.subheader("Parameter Optimization Suggestions")
    
    # Get optimization suggestions
    from backend.recommendations import DABRecommendations
    recommender = DABRecommendations()
    
    # Create a mock dataframe for recommendations
    mock_data = pd.DataFrame([{
        'timestamp': pd.Timestamp.now(),
        'efficiency_percent': results['efficiency'],
        'temperature_C': results['temperature'],
        'health_score': 85.0,  # Mock value
        'ZVS_status': results['zvs_status']['overall_zvs'],
        'phi': phi,
        'delta1': delta1,
        'delta2': delta2,
        'power_loss_W': results['losses']['total_loss']
    }])
    
    recommendations = recommender.generate_recommendations(mock_data)
    
    if recommendations:
        for i, rec in enumerate(recommendations[:3], 1):
            with st.expander(f"Recommendation {i}: {rec['action']}"):
                st.write(f"**Impact:** {rec['impact']}")
                st.write(f"**Priority:** {rec['priority'].title()}")
                st.write(f"**Effort:** {rec['estimated_effort'].title()}")
                st.write(f"**Confidence:** {rec['confidence']:.1%}")
    else:
        st.success("✅ All parameters are within optimal ranges!")
    
    # Performance comparison
    st.subheader("Performance Comparison")
    
    # Compare with default parameters
    default_results = simulator.run_simulation(simulator.default_params)
    
    comparison_data = {
        'Metric': ['Efficiency (%)', 'Temperature (°C)', 'ZVS Status', 'Total Loss (W)'],
        'Current': [
            results['efficiency'],
            results['temperature'],
            'ZVS' if results['zvs_status']['overall_zvs'] else 'No ZVS',
            results['losses']['total_loss']
        ],
        'Default': [
            default_results['efficiency'],
            default_results['temperature'],
            'ZVS' if default_results['zvs_status']['overall_zvs'] else 'No ZVS',
            default_results['losses']['total_loss']
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Save simulation results
    if st.button("Save Simulation Results"):
        # Create results summary
        results_summary = {
            'timestamp': pd.Timestamp.now(),
            'parameters': params,
            'results': results
        }
        
        # Save to session state for now (in real app, save to database)
        if 'simulation_history' not in st.session_state:
            st.session_state.simulation_history = []
        
        st.session_state.simulation_history.append(results_summary)
        st.success("Simulation results saved!")
    
    # Show simulation history
    if 'simulation_history' in st.session_state and st.session_state.simulation_history:
        st.subheader("Simulation History")
        
        history_df = pd.DataFrame([
            {
                'Timestamp': h['timestamp'],
                'Efficiency (%)': h['results']['efficiency'],
                'Temperature (°C)': h['results']['temperature'],
                'ZVS Status': 'ZVS' if h['results']['zvs_status']['overall_zvs'] else 'No ZVS',
                'Total Loss (W)': h['results']['losses']['total_loss']
            }
            for h in st.session_state.simulation_history[-5:]  # Show last 5
        ])
        
        st.dataframe(history_df, use_container_width=True)
