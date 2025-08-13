import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.sheets_loader import load_sheets_data
from backend.alerting import DABAlerting, AlertSeverity, AlertType
from backend.diagnostics import add_health_scores

def show():
    st.title("🚨 DAB HealthAI — Alerting System")
    st.write("Monitor system health with real-time alerts and notifications.")
    
    # Initialize alerting system
    if 'alerting_system' not in st.session_state:
        st.session_state.alerting_system = DABAlerting()
    
    alerting = st.session_state.alerting_system
    
    # Load data
    df = load_sheets_data()
    if not df.empty:
        df = add_health_scores(df)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Sidebar for configuration
    st.sidebar.header("Alert Configuration")
    
    # Alert thresholds configuration
    st.sidebar.subheader("Threshold Settings")
    
    # Efficiency threshold
    eff_warning = st.sidebar.number_input(
        "Efficiency Warning (%)",
        min_value=80.0,
        max_value=99.0,
        value=95.0,
        step=0.5
    )
    
    eff_critical = st.sidebar.number_input(
        "Efficiency Critical (%)",
        min_value=70.0,
        max_value=95.0,
        value=90.0,
        step=0.5
    )
    
    # Temperature threshold
    temp_warning = st.sidebar.number_input(
        "Temperature Warning (°C)",
        min_value=40.0,
        max_value=80.0,
        value=60.0,
        step=1.0
    )
    
    temp_critical = st.sidebar.number_input(
        "Temperature Critical (°C)",
        min_value=50.0,
        max_value=90.0,
        value=70.0,
        step=1.0
    )
    
    # Health score threshold
    health_warning = st.sidebar.number_input(
        "Health Score Warning",
        min_value=50.0,
        max_value=90.0,
        value=80.0,
        step=1.0
    )
    
    health_critical = st.sidebar.number_input(
        "Health Score Critical",
        min_value=30.0,
        max_value=80.0,
        value=60.0,
        step=1.0
    )
    
    # Update thresholds
    if st.sidebar.button("Update Thresholds"):
        alerting.thresholds['efficiency_percent'] = {
            'warning': eff_warning,
            'critical': eff_critical,
            'emergency': eff_critical - 5
        }
        alerting.thresholds['temperature_C'] = {
            'warning': temp_warning,
            'critical': temp_critical,
            'emergency': temp_critical + 10
        }
        alerting.thresholds['health_score'] = {
            'warning': health_warning,
            'critical': health_critical,
            'emergency': health_critical - 20
        }
        st.sidebar.success("Thresholds updated!")
    
    # Email configuration
    st.sidebar.subheader("Email Configuration")
    
    email_enabled = st.sidebar.checkbox("Enable Email Alerts")
    
    if email_enabled:
        smtp_server = st.sidebar.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.sidebar.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
        email_username = st.sidebar.text_input("Email Username")
        email_password = st.sidebar.text_input("Email Password", type="password")
        email_recipients = st.sidebar.text_area("Recipient Emails (one per line)")
        
        if st.sidebar.button("Save Email Config"):
            recipients_list = [email.strip() for email in email_recipients.split('\n') if email.strip()]
            alerting.config['email'].update({
                'enabled': True,
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'username': email_username,
                'password': email_password,
                'recipients': recipients_list
            })
            st.sidebar.success("Email configuration saved!")
    
    # Slack configuration
    st.sidebar.subheader("Slack Configuration")
    
    slack_enabled = st.sidebar.checkbox("Enable Slack Alerts")
    
    if slack_enabled:
        webhook_url = st.sidebar.text_input("Webhook URL")
        channel = st.sidebar.text_input("Channel", value="#alerts")
        
        if st.sidebar.button("Save Slack Config"):
            alerting.config['slack'].update({
                'enabled': True,
                'webhook_url': webhook_url,
                'channel': channel
            })
            st.sidebar.success("Slack configuration saved!")
    
    # Main content
    # Check for new alerts
    if not df.empty:
        st.subheader("Alert Detection")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Check Threshold Alerts"):
                with st.spinner("Checking for threshold alerts..."):
                    new_alerts = alerting.check_threshold_alerts(df)
                    if new_alerts:
                        st.success(f"✅ {len(new_alerts)} new threshold alerts detected!")
                    else:
                        st.info("ℹ️ No new threshold alerts detected.")
        
        with col2:
            if st.button("📈 Check Trend Alerts"):
                with st.spinner("Checking for trend alerts..."):
                    new_alerts = alerting.check_trend_alerts(df, hours=24)
                    if new_alerts:
                        st.success(f"✅ {len(new_alerts)} new trend alerts detected!")
                    else:
                        st.info("ℹ️ No new trend alerts detected.")
        
        with col3:
            if st.button("💔 Check Health Degradation"):
                with st.spinner("Checking for health degradation..."):
                    new_alerts = alerting.check_health_degradation_alerts(df, hours=24)
                    if new_alerts:
                        st.success(f"✅ {len(new_alerts)} new health degradation alerts detected!")
                    else:
                        st.info("ℹ️ No new health degradation alerts detected.")
    
    # Active alerts
    st.subheader("Active Alerts")
    
    active_alerts = alerting.get_active_alerts()
    
    if active_alerts:
        # Filter by severity
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All"] + [sev.value for sev in AlertSeverity],
            index=0
        )
        
        if severity_filter == "All":
            filtered_alerts = active_alerts
        else:
            filtered_alerts = [a for a in active_alerts if a.severity.value == severity_filter]
        
        # Display alerts
        for i, alert in enumerate(filtered_alerts):
            # Color code by severity
            severity_colors = {
                AlertSeverity.INFO: "🟢",
                AlertSeverity.WARNING: "🟡",
                AlertSeverity.CRITICAL: "🟠",
                AlertSeverity.EMERGENCY: "🔴"
            }
            
            with st.expander(f"{severity_colors[alert.severity]} {alert.severity.value.upper()}: {alert.message}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Timestamp:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Metric:** {alert.metric}")
                    st.write(f"**Value:** {alert.value:.2f}")
                    if alert.threshold:
                        st.write(f"**Threshold:** {alert.threshold:.2f}")
                    st.write(f"**Type:** {alert.alert_type.value}")
                
                with col2:
                    if alert.trend_data:
                        st.write("**Trend Data:**")
                        for key, value in alert.trend_data.items():
                            if isinstance(value, float):
                                st.write(f"• {key}: {value:.2f}")
                            else:
                                st.write(f"• {key}: {value}")
                    
                    if alert.recommendations:
                        st.write("**Recommendations:**")
                        for rec in alert.recommendations:
                            st.write(f"• {rec}")
                
                # Acknowledge button
                if st.button(f"Acknowledge Alert {i}", key=f"ack_{i}"):
                    alerting.acknowledge_alert(i, "User")
                    st.success("Alert acknowledged!")
                    st.rerun()
    
    else:
        st.success("✅ No active alerts!")
    
    # Alert summary
    st.subheader("Alert Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get summary for different time periods
    summary_24h = alerting.get_alert_summary(hours=24)
    summary_7d = alerting.get_alert_summary(hours=24*7)
    summary_30d = alerting.get_alert_summary(hours=24*30)
    
    with col1:
        st.metric("Last 24h", summary_24h['total_alerts'])
        st.write(f"Active: {summary_24h['unacknowledged']}")
    
    with col2:
        st.metric("Last 7 Days", summary_7d['total_alerts'])
        st.write(f"Active: {summary_7d['unacknowledged']}")
    
    with col3:
        st.metric("Last 30 Days", summary_30d['total_alerts'])
        st.write(f"Active: {summary_30d['unacknowledged']}")
    
    with col4:
        # Most common alert type
        if summary_24h['by_type']:
            most_common = max(summary_24h['by_type'].items(), key=lambda x: x[1])
            st.metric("Most Common", most_common[0].title())
            st.write(f"Count: {most_common[1]}")
    
    # Alert statistics
    st.subheader("Alert Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Alerts by Severity (24h)**")
        severity_data = summary_24h['by_severity']
        if severity_data:
            for severity, count in severity_data.items():
                if count > 0:
                    st.write(f"• {severity.title()}: {count}")
    
    with col2:
        st.write("**Alerts by Type (24h)**")
        type_data = summary_24h['by_type']
        if type_data:
            for alert_type, count in type_data.items():
                if count > 0:
                    st.write(f"• {alert_type.title()}: {count}")
    
    # Alert history
    st.subheader("Alert History")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        history_hours = st.selectbox(
            "Time Period",
            [24, 48, 168, 720],  # 1 day, 2 days, 1 week, 1 month
            format_func=lambda x: f"{x//24} days" if x >= 24 else f"{x} hours"
        )
    
    with col2:
        history_severity = st.selectbox(
            "Severity Filter",
            ["All"] + [sev.value for sev in AlertSeverity],
            index=0
        )
    
    with col3:
        history_type = st.selectbox(
            "Type Filter",
            ["All"] + [at.value for at in AlertType],
            index=0
        )
    
    # Get filtered history
    cutoff_time = datetime.now() - timedelta(hours=history_hours)
    filtered_history = [a for a in alerting.alert_history if a.timestamp > cutoff_time]
    
    if history_severity != "All":
        filtered_history = [a for a in filtered_history if a.severity.value == history_severity]
    
    if history_type != "All":
        filtered_history = [a for a in filtered_history if a.alert_type.value == history_type]
    
    if filtered_history:
        # Convert to DataFrame for display
        history_data = []
        for alert in filtered_history:
            history_data.append({
                'Timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Severity': alert.severity.value.upper(),
                'Type': alert.alert_type.value,
                'Metric': alert.metric,
                'Value': f"{alert.value:.2f}",
                'Message': alert.message[:50] + "..." if len(alert.message) > 50 else alert.message,
                'Acknowledged': "✅" if alert.acknowledged else "❌"
            })
        
        history_df = pd.DataFrame(history_data)
        st.dataframe(history_df, use_container_width=True)
        
        # Export option
        if st.button("📊 Export Alert History"):
            csv = history_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"alert_history_{history_hours}h.csv",
                mime="text/csv"
            )
    else:
        st.info("No alerts found for the selected filters.")
    
    # Test alerts
    st.subheader("Test Alerts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧪 Test Email Alert"):
            if alerting.config['email']['enabled']:
                # Create a test alert
                test_alert = type('TestAlert', (), {
                    'severity': AlertSeverity.INFO,
                    'alert_type': AlertType.THRESHOLD,
                    'message': 'This is a test alert',
                    'metric': 'test',
                    'value': 0.0,
                    'timestamp': datetime.now()
                })()
                
                try:
                    alerting._send_email_alert(test_alert)
                    st.success("✅ Test email sent successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to send test email: {str(e)}")
            else:
                st.warning("⚠️ Email alerts are not enabled.")
    
    with col2:
        if st.button("🧪 Test Slack Alert"):
            if alerting.config['slack']['enabled']:
                # Create a test alert
                test_alert = type('TestAlert', (), {
                    'severity': AlertSeverity.INFO,
                    'alert_type': AlertType.THRESHOLD,
                    'message': 'This is a test alert',
                    'metric': 'test',
                    'value': 0.0,
                    'timestamp': datetime.now()
                })()
                
                try:
                    alerting._send_slack_alert(test_alert)
                    st.success("✅ Test Slack message sent successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to send test Slack message: {str(e)}")
            else:
                st.warning("⚠️ Slack alerts are not enabled.")
    
    # Configuration export/import
    st.subheader("Configuration Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Config"):
            config_data = {
                'thresholds': alerting.thresholds,
                'trend_thresholds': alerting.trend_thresholds,
                'config': alerting.config
            }
            config_json = json.dumps(config_data, indent=2, default=str)
            st.download_button(
                label="📥 Download Config",
                data=config_json,
                file_name="alerting_config.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("Import Config", type=['json'])
        if uploaded_file is not None:
            try:
                config_data = json.load(uploaded_file)
                # Update configuration
                if 'thresholds' in config_data:
                    alerting.thresholds.update(config_data['thresholds'])
                if 'trend_thresholds' in config_data:
                    alerting.trend_thresholds.update(config_data['trend_thresholds'])
                if 'config' in config_data:
                    alerting.config.update(config_data['config'])
                st.success("✅ Configuration imported successfully!")
            except Exception as e:
                st.error(f"❌ Failed to import configuration: {str(e)}")
