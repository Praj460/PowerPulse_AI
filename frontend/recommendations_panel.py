import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.sheets_loader import load_sheets_data
from backend.recommendations import DABRecommendations
from backend.diagnostics import add_health_scores, analyze_trends
from backend.simulator import DABSimulator

def show():
    st.title("💡 DAB HealthAI — Recommendations Panel")
    st.write("Get actionable recommendations to optimize DAB converter performance and restore ZVS operation.")
    
    # Load data
    df = load_sheets_data()
    if df.empty:
        st.error("No data available. Please ensure data is loaded first.")
        return
    
    df = add_health_scores(df)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Initialize components
    recommender = DABRecommendations()
    simulator = DABSimulator()
    
    # Get latest data
    latest = df.iloc[-1] if not df.empty else None
    
    if latest is None:
        st.error("No data available for analysis.")
        return
    
    # Current status overview
    st.subheader("Current System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        efficiency = latest.get('efficiency_percent', 0)
        st.metric(
            "Efficiency", 
            f"{efficiency:.2f}%",
            delta=f"{efficiency - 95:.2f}%" if efficiency < 95 else None
        )
    
    with col2:
        temperature = latest.get('temperature_C', 0)
        st.metric(
            "Temperature", 
            f"{temperature:.1f}°C",
            delta=f"{temperature - 60:.1f}°C" if temperature > 60 else None
        )
    
    with col3:
        health_score = latest.get('health_score', 0)
        st.metric(
            "Health Score", 
            f"{health_score:.1f}/100",
            delta=f"{health_score - 80:.1f}" if health_score < 80 else None
        )
    
    with col4:
        zvs_status = latest.get('ZVS_status', False)
        st.metric(
            "ZVS Status", 
            "✅ ZVS" if zvs_status else "❌ No ZVS",
            delta="ZVS Active" if zvs_status else "ZVS Lost"
        )
    
    # Generate recommendations
    st.subheader("Actionable Recommendations")
    
    # Get anomalies and recommendations
    anomalies = recommender.detect_anomalies(df)
    recommendations = recommender.generate_recommendations(df, anomalies)
    
    if recommendations:
        # Sort by priority and impact
        priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        recommendations.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['confidence']), reverse=True)
        
        # Display top recommendations
        for i, rec in enumerate(recommendations[:5], 1):
            with st.expander(f"🎯 {rec['action']}", expanded=i <= 2):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Impact:** {rec['impact']}")
                    st.write(f"**Priority:** {rec['priority'].title()}")
                    st.write(f"**Effort:** {rec['estimated_effort'].title()}")
                    st.write(f"**Confidence:** {rec['confidence']:.1%}")
                    
                    # Calculate impact score
                    impact_score = recommender.calculate_impact_score(rec)
                    st.write(f"**Impact Score:** {impact_score:.0f}/100")
                
                with col2:
                    # Show parameter optimization if applicable
                    if 'phi' in rec['action'] and 'phase shift' in rec['action'].lower():
                        st.write("**Parameter Optimization:**")
                        
                        # Extract current phi value
                        current_phi = latest.get('phi', 0.3)
                        if current_phi > 0:
                            # Estimate improvement
                            suggested_phi = min(np.pi/2, current_phi + 0.05)
                            st.write(f"• Current φ: {current_phi:.3f}")
                            st.write(f"• Suggested φ: {suggested_phi:.3f}")
                            st.write(f"• Change: +{(suggested_phi - current_phi):.3f}")
                    
                    elif 'duty cycle' in rec['action'].lower():
                        st.write("**Parameter Optimization:**")
                        delta1 = latest.get('delta1', 0.5)
                        delta2 = latest.get('delta2', 0.5)
                        balanced_delta = (delta1 + delta2) / 2
                        st.write(f"• Current δ₁: {delta1:.2f}")
                        st.write(f"• Current δ₂: {delta2:.2f}")
                        st.write(f"• Suggested: {balanced_delta:.2f}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"✅ Implement {i}", key=f"implement_{i}"):
                        st.success(f"Recommendation {i} marked as implemented!")
                
                with col2:
                    if st.button(f"📊 Analyze Impact {i}", key=f"analyze_{i}"):
                        # Show impact analysis
                        st.info("Impact analysis would be performed here.")
                
                with col3:
                    if st.button(f"⏰ Schedule {i}", key=f"schedule_{i}"):
                        st.info("Recommendation scheduled for later implementation.")
    
    else:
        st.success("✅ All systems are operating optimally! No recommendations needed at this time.")
    
    # Parameter optimization suggestions
    st.subheader("Parameter Optimization Suggestions")
    
    # Get optimization suggestions
    optimization_suggestions = recommender.get_parameter_optimization(df)
    
    if optimization_suggestions:
        for param, suggestion in optimization_suggestions.items():
            with st.expander(f"🔧 {param.upper()} Optimization"):
                if param == 'phi':
                    st.write(f"**Current Value:** {suggestion['current']:.3f}")
                    st.write(f"**Suggested Value:** {suggestion['suggested']:.3f}")
                    st.write(f"**Reason:** {suggestion['reason']}")
                    st.write(f"**Expected Impact:** {suggestion['expected_impact']}")
                    
                    # Show impact simulation
                    if st.button(f"Simulate {param} Change"):
                        # Run simulation with current and suggested values
                        current_params = {
                            'Vdc1': latest.get('Vdc1', 400.0),
                            'Vdc2': latest.get('Vdc2', 48.0),
                            'phi': suggestion['current'],
                            'delta1': latest.get('delta1', 0.5),
                            'delta2': latest.get('delta2', 0.5),
                            'Pload': latest.get('Pload', 1000.0),
                            'fsw': latest.get('fsw', 100000),
                            'L': 50e-6,
                            'R_on': 0.1,
                            'C_oss': 100e-12
                        }
                        
                        suggested_params = current_params.copy()
                        suggested_params['phi'] = suggestion['suggested']
                        
                        # Run simulations
                        current_sim = simulator.run_simulation(current_params)
                        suggested_sim = simulator.run_simulation(suggested_params)
                        
                        # Display comparison
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Current Parameters:**")
                            st.write(f"• Efficiency: {current_sim['efficiency']:.2f}%")
                            st.write(f"• Temperature: {current_sim['temperature']:.1f}°C")
                            st.write(f"• ZVS: {'✅' if current_sim['zvs_status']['overall_zvs'] else '❌'}")
                        
                        with col2:
                            st.write("**Suggested Parameters:**")
                            st.write(f"• Efficiency: {suggested_sim['efficiency']:.2f}%")
                            st.write(f"• Temperature: {suggested_sim['temperature']:.1f}°C")
                            st.write(f"• ZVS: {'✅' if suggested_sim['zvs_status']['overall_zvs'] else '❌'}")
                        
                        # Calculate improvements
                        eff_improvement = suggested_sim['efficiency'] - current_sim['efficiency']
                        temp_improvement = current_sim['temperature'] - suggested_sim['temperature']
                        zvs_improvement = suggested_sim['zvs_status']['overall_zvs'] - current_sim['zvs_status']['overall_zvs']
                        
                        st.success(f"""
                        **Expected Improvements:**
                        • Efficiency: {eff_improvement:+.2f}%
                        • Temperature: {temp_improvement:+.1f}°C
                        • ZVS Status: {'Restored' if zvs_improvement > 0 else 'No change'}
                        """)
                
                elif param == 'duty_cycles':
                    st.write(f"**Current Values:**")
                    st.write(f"• δ₁: {suggestion['current']['delta1']:.2f}")
                    st.write(f"• δ₂: {suggestion['current']['delta2']:.2f}")
                    st.write(f"**Suggested Values:**")
                    st.write(f"• δ₁: {suggestion['suggested']['delta1']:.2f}")
                    st.write(f"• δ₂: {suggestion['suggested']['delta2']:.2f}")
                    st.write(f"**Reason:** {suggestion['reason']}")
                    st.write(f"**Expected Impact:** {suggestion['expected_impact']}")
    
    else:
        st.info("No parameter optimization suggestions at this time.")
    
    # Trend analysis and recommendations
    st.subheader("Trend-Based Recommendations")
    
    # Analyze trends
    trends = analyze_trends(df, hours=24)
    
    if trends:
        trend_recommendations = []
        
        for metric, trend in trends.items():
            if trend['pct_change'] < -5:  # More than 5% degradation
                if metric == 'efficiency_percent':
                    trend_recommendations.append({
                        'metric': metric,
                        'trend': trend,
                        'action': 'Investigate efficiency degradation trend',
                        'priority': 'medium',
                        'impact': 'Identify root cause of performance decline'
                    })
                elif metric == 'temperature_C':
                    trend_recommendations.append({
                        'metric': metric,
                        'trend': trend,
                        'action': 'Monitor temperature trend and check cooling system',
                        'priority': 'medium',
                        'impact': 'Prevent thermal runaway and component damage'
                    })
                elif metric == 'health_score':
                    trend_recommendations.append({
                        'metric': metric,
                        'trend': trend,
                        'action': 'Perform preventive maintenance on power components',
                        'priority': 'high',
                        'impact': 'Prevent further degradation and potential failures'
                    })
        
        if trend_recommendations:
            for rec in trend_recommendations:
                with st.expander(f"📈 {rec['action']}"):
                    st.write(f"**Metric:** {rec['metric'].replace('_', ' ').title()}")
                    st.write(f"**Trend:** {rec['trend']['trend']}")
                    st.write(f"**Change:** {rec['trend']['pct_change']:+.1f}%")
                    st.write(f"**Priority:** {rec['priority'].title()}")
                    st.write(f"**Impact:** {rec['impact']}")
        else:
            st.success("✅ No concerning trends detected.")
    else:
        st.info("Insufficient data for trend analysis.")
    
    # ZVS restoration recommendations
    st.subheader("ZVS Restoration Recommendations")
    
    if not latest.get('ZVS_status', True):
        st.warning("🚨 ZVS operation has been lost! Here are specific recommendations to restore it:")
        
        # ZVS restoration strategies
        zvs_strategies = [
            {
                'strategy': 'Increase Phase Shift (φ)',
                'description': 'Gradually increase phase shift to restore ZVS conditions',
                'current_value': latest.get('phi', 0.3),
                'suggested_value': min(np.pi/2, latest.get('phi', 0.3) + 0.05),
                'impact': 'Restore ZVS operation, reduce switching losses',
                'effort': 'Low',
                'risk': 'Low'
            },
            {
                'strategy': 'Optimize Duty Cycles',
                'description': 'Balance duty cycles for optimal transformer current',
                'current_value': f"δ₁: {latest.get('delta1', 0.5):.2f}, δ₂: {latest.get('delta2', 0.5):.2f}",
                'suggested_value': f"δ₁: 0.50, δ₂: 0.50",
                'impact': 'Improve current balance, enhance ZVS margin',
                'effort': 'Low',
                'risk': 'Low'
            },
            {
                'strategy': 'Reduce Switching Frequency',
                'description': 'Lower switching frequency to improve ZVS margin',
                'current_value': f"{latest.get('fsw', 100000)/1000:.0f} kHz",
                'suggested_value': f"{latest.get('fsw', 100000)*0.9/1000:.0f} kHz",
                'impact': 'Increase ZVS margin, reduce switching losses',
                'effort': 'Medium',
                'risk': 'Medium'
            }
        ]
        
        for i, strategy in enumerate(zvs_strategies):
            with st.expander(f"🔄 {strategy['strategy']}"):
                st.write(f"**Description:** {strategy['description']}")
                st.write(f"**Current Value:** {strategy['current_value']}")
                st.write(f"**Suggested Value:** {strategy['suggested_value']}")
                st.write(f"**Expected Impact:** {strategy['impact']}")
                st.write(f"**Implementation Effort:** {strategy['effort']}")
                st.write(f"**Risk Level:** {strategy['risk']}")
                
                if st.button(f"Implement {strategy['strategy']}", key=f"zvs_{i}"):
                    st.success(f"{strategy['strategy']} implementation started!")
    
    # Implementation tracking
    st.subheader("Recommendation Implementation Tracking")
    
    # Mock implementation data (in real app, this would come from database)
    if 'implemented_recommendations' not in st.session_state:
        st.session_state.implemented_recommendations = []
    
    if st.session_state.implemented_recommendations:
        implementation_df = pd.DataFrame(st.session_state.implemented_recommendations)
        st.dataframe(implementation_df, use_container_width=True)
    else:
        st.info("No recommendations have been implemented yet.")
    
    # Add new implementation
    with st.expander("➕ Add Implementation Record"):
        col1, col2 = st.columns(2)
        
        with col1:
            rec_action = st.text_input("Recommendation Action")
            implementation_date = st.date_input("Implementation Date")
        
        with col2:
            status = st.selectbox("Status", ["Completed", "In Progress", "On Hold"])
            notes = st.text_area("Implementation Notes")
        
        if st.button("Add Implementation"):
            if rec_action:
                new_implementation = {
                    'Action': rec_action,
                    'Date': implementation_date,
                    'Status': status,
                    'Notes': notes
                }
                st.session_state.implemented_recommendations.append(new_implementation)
                st.success("Implementation record added!")
                st.rerun()
    
    # Export recommendations
    st.subheader("Export & Share")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Recommendations"):
            # Create recommendations summary
            if recommendations:
                rec_data = []
                for rec in recommendations:
                    rec_data.append({
                        'Action': rec['action'],
                        'Impact': rec['impact'],
                        'Priority': rec['priority'],
                        'Effort': rec['estimated_effort'],
                        'Confidence': f"{rec['confidence']:.1%}"
                    })
                
                rec_df = pd.DataFrame(rec_data)
                csv = rec_df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name="dab_recommendations.csv",
                    mime="text/csv"
                )
            else:
                st.info("No recommendations to export.")
    
    with col2:
        if st.button("📧 Email Summary"):
            st.info("Email summary feature would be implemented here.")
    
    # Performance monitoring
    st.subheader("Performance Monitoring")
    
    # Show recent performance trends
    if len(df) > 1:
        # Create performance trend chart
        recent_df = df.tail(50)  # Last 50 data points
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Efficiency Trend', 'Temperature Trend', 'Health Score Trend', 'ZVS Status')
        )
        
        # Efficiency trend
        fig.add_trace(
            go.Scatter(x=recent_df['timestamp'], y=recent_df['efficiency_percent'], 
                      mode='lines+markers', name='Efficiency'),
            row=1, col=1
        )
        
        # Temperature trend
        fig.add_trace(
            go.Scatter(x=recent_df['timestamp'], y=recent_df['temperature_C'], 
                      mode='lines+markers', name='Temperature'),
            row=1, col=2
        )
        
        # Health score trend
        fig.add_trace(
            go.Scatter(x=recent_df['timestamp'], y=recent_df['health_score'], 
                      mode='lines+markers', name='Health Score'),
            row=2, col=1
        )
        
        # ZVS status
        if 'ZVS_status' in recent_df.columns:
            zvs_values = recent_df['ZVS_status'].astype(int)
            fig.add_trace(
                go.Scatter(x=recent_df['timestamp'], y=zvs_values, 
                          mode='lines+markers', name='ZVS Status'),
                row=2, col=2
            )
        
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
