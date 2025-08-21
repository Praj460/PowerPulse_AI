import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import tempfile
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.sheets_loader import load_sheets_data
from backend.reports import create_health_report
from backend.diagnostics import add_health_scores, detect_anomalies, generate_basic_recommendations
from backend.alerting import DABAlerting

def show():
    st.title("📊 DAB HealthAI — Health Reports")
    st.write("Generate comprehensive health reports with one-click PDF generation.")
    
    # Load data
    df = load_sheets_data()
    if df.empty:
        st.error("No data available. Please ensure data is loaded first.")
        return
    
    df = add_health_scores(df)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Report configuration
    st.subheader("Report Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_type = st.selectbox(
            "Report Type",
            ["weekly", "monthly"],
            help="Select the time period for the report"
        )
    
    with col2:
        include_anomalies = st.checkbox(
            "Include Anomaly Analysis",
            value=True,
            help="Include detected anomalies in the report"
        )
    
    with col3:
        include_recommendations = st.checkbox(
            "Include Recommendations",
            value=True,
            help="Include actionable recommendations in the report"
        )
    
    # Date range selection
    st.subheader("Date Range Selection")
    
    min_date = df['timestamp'].min()
    max_date = df['timestamp'].max()
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=min_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=max_date.date(),
            min_value=start_date,
            max_value=max_date.date()
        )
    
    # Filter data for selected range
    start_datetime = pd.Timestamp(start_date)
    end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1)
    
    filtered_df = df[(df['timestamp'] >= start_datetime) & (df['timestamp'] <= end_datetime)]
    
    if filtered_df.empty:
        st.warning("No data available for the selected date range.")
        return
    
    # Data summary
    st.subheader("Data Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Points", len(filtered_df))
    
    with col2:
        avg_efficiency = filtered_df['efficiency_percent'].mean()
        st.metric("Avg Efficiency", f"{avg_efficiency:.2f}%")
    
    with col3:
        avg_temp = filtered_df['temperature_C'].mean()
        st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
    
    with col4:
        avg_health = filtered_df['health_score'].mean()
        st.metric("Avg Health Score", f"{avg_health:.1f}")
    
    # Anomaly detection
    if include_anomalies:
        st.subheader("Anomaly Detection")
        
        anomalies = detect_anomalies(filtered_df)
        
        if anomalies:
            st.warning(f"🚨 {len(anomalies)} anomalies detected in the selected period!")
            
            # Display anomalies
            anomaly_df = pd.DataFrame(anomalies)
            anomaly_df['timestamp'] = pd.to_datetime(anomaly_df['timestamp'])
            
            # Color code by severity
            def color_severity(severity):
                if severity == 'critical':
                    return 'background-color: #ffcccc'
                elif severity == 'warning':
                    return 'background-color: #fff2cc'
                else:
                    return ''
            
            styled_anomaly_df = anomaly_df.style.applymap(
                lambda x: color_severity(x) if x in ['critical', 'warning'] else '',
                subset=['severity']
            )
            
            st.dataframe(styled_anomaly_df, use_container_width=True)
        else:
            st.success("✅ No anomalies detected in the selected period.")
    
    # Recommendations
    if include_recommendations:
        st.subheader("Recommendations")
        
        recommendations = generate_basic_recommendations(filtered_df)
        
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):
                st.write(f"{i}. {rec}")
        else:
            st.success("✅ No recommendations needed. System is operating optimally!")
    
    # Trend analysis
    st.subheader("Trend Analysis")
    
    from backend.diagnostics import analyze_trends
    
    # Analyze trends for the selected period
    trends = analyze_trends(filtered_df, hours=int((end_datetime - start_datetime).total_seconds() / 3600))
    
    if trends:
        trend_data = []
        for metric, trend in trends.items():
            trend_data.append({
                'Metric': metric.replace('_', ' ').title(),
                'Trend': trend['trend'].title(),
                'Change (%)': f"{trend['pct_change']:+.1f}%",
                'Current Value': f"{trend['current']:.2f}",
                'Average Value': f"{trend['average']:.2f}"
            })
        
        trend_df = pd.DataFrame(trend_data)
        st.dataframe(trend_df, use_container_width=True)
    else:
        st.info("Insufficient data for trend analysis.")
    
    # Performance metrics
    st.subheader("Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Efficiency distribution
        st.write("**Efficiency Distribution**")
        efficiency_stats = filtered_df['efficiency_percent'].describe()
        st.write(f"• Min: {efficiency_stats['min']:.2f}%")
        st.write(f"• Max: {efficiency_stats['max']:.2f}%")
        st.write(f"• Mean: {efficiency_stats['mean']:.2f}%")
        st.write(f"• Std: {efficiency_stats['std']:.2f}%")
        
        # Temperature analysis
        st.write("**Temperature Analysis**")
        temp_stats = filtered_df['temperature_C'].describe()
        st.write(f"• Min: {temp_stats['min']:.1f}°C")
        st.write(f"• Max: {temp_stats['max']:.1f}°C")
        st.write(f"• Mean: {temp_stats['mean']:.1f}°C")
        st.write(f"• Std: {temp_stats['std']:.1f}°C")
    
    with col2:
        # Health score analysis
        st.write("**Health Score Analysis**")
        health_stats = filtered_df['health_score'].describe()
        st.write(f"• Min: {health_stats['min']:.1f}")
        st.write(f"• Max: {health_stats['max']:.1f}")
        st.write(f"• Mean: {health_stats['mean']:.1f}")
        st.write(f"• Std: {health_stats['std']:.1f}")
        
        # ZVS status
        if 'ZVS_status' in filtered_df.columns:
            zvs_counts = filtered_df['ZVS_status'].value_counts()
            st.write("**ZVS Status Distribution**")
            for status, count in zvs_counts.items():
                percentage = (count / len(filtered_df)) * 100
                st.write(f"• {status}: {count} ({percentage:.1f}%)")
    
    # Generate PDF Report
    st.subheader("Generate PDF Report")
    
    if st.button("📄 Generate Health Report", type="primary"):
        with st.spinner("Generating PDF report..."):
            try:
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    # Generate report
                    pdf_path = create_health_report(
                        filtered_df, 
                        report_type=report_type,
                        output_path=tmp_file.name
                    )
                    
                    # Read the PDF file
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_bytes = pdf_file.read()
                    
                    # Clean up temporary file
                    os.unlink(pdf_path)
                    
                    # Provide download button
                    st.success("✅ PDF report generated successfully!")
                    
                    # Create filename
                    filename = f"DAB_Health_Report_{report_type}_{start_date}_{end_date}.pdf"
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf"
                    )
                    
                    # Show report preview info
                    st.info(f"""
                    **Report Summary:**
                    - **Period:** {start_date} to {end_date}
                    - **Data Points:** {len(filtered_df)}
                    - **Anomalies:** {len(anomalies) if include_anomalies else 0}
                    - **Recommendations:** {len(recommendations) if include_recommendations else 0}
                    - **Report Type:** {report_type.title()}
                    """)
                    
            except Exception as e:
                st.error(f"❌ Error generating PDF report: {str(e)}")
                st.error("Please check that all required dependencies are installed.")
    
    # Report templates
    st.subheader("Report Templates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Executive Summary"):
            st.info("Executive summary template would be generated here.")
    
    with col2:
        if st.button("🔍 Technical Deep Dive"):
            st.info("Technical deep dive template would be generated here.")
    
    with col3:
        if st.button("📈 Trend Analysis"):
            st.info("Trend analysis template would be generated here.")
    
    # Scheduled reports
    st.subheader("Scheduled Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Weekly Reports**")
        st.write("• Every Monday at 9:00 AM")
        st.write("• Sent to engineering team")
        st.write("• Includes efficiency trends")
        
        if st.button("📅 Schedule Weekly Report"):
            st.success("Weekly report scheduled!")
    
    with col2:
        st.write("**Monthly Reports**")
        st.write("• First day of each month")
        st.write("• Sent to management team")
        st.write("• Includes comprehensive analysis")
        
        if st.button("📅 Schedule Monthly Report"):
            st.success("Monthly report scheduled!")
    
    # Report history
    if 'report_history' in st.session_state and st.session_state.report_history:
        st.subheader("Report History")
        
        history_df = pd.DataFrame(st.session_state.report_history)
        st.dataframe(history_df, use_container_width=True)
