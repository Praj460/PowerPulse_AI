import streamlit as st

st.set_page_config(page_title="DAB HealthAI Home", layout="centered")  # First Streamlit command!

st.title("🔌 DAB HealthAI — Home")
st.write("Welcome! Choose your tool:")

col1, col2, col3, col4 = st.columns(4)
if 'page' not in st.session_state:
    st.session_state['page'] = None

with col1:
    if st.button("📈 Analytics Dashboard"):
        st.session_state['page'] = 'dashboard'
with col2:
    if st.button("🤖 Gemini Chatbot"):
        st.session_state['page'] = 'chatbot'
with col3:
    if st.button("➕ Data Entry"):
        st.session_state['page'] = 'data_entry'
with col4:
    if st.button("🔬 What-If Simulator"):
        st.session_state['page'] = 'simulator'

# Second row of buttons
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 Health Reports"):
        st.session_state['page'] = 'reports'
with col2:
    if st.button("🚨 Alerting System"):
        st.session_state['page'] = 'alerts'
with col3:
    if st.button("💡 Recommendations"):
        st.session_state['page'] = 'recommendations'
with col4:
    if st.button("🏠 Home"):
        st.session_state['page'] = None

page = st.session_state['page']
if page == 'dashboard':
    from frontend import dashboard
    dashboard.show()
elif page == 'chatbot':
    from frontend import chatbot
    chatbot.show()
elif page == 'data_entry':
    from frontend import data_entry
    data_entry.show()
elif page == 'simulator':
    from frontend import simulator
    simulator.show()
elif page == 'reports':
    from frontend import reports
    reports.show()
elif page == 'alerts':
    from frontend import alerts
    alerts.show()
elif page == 'recommendations':
    from frontend import recommendations_panel
    recommendations_panel.show()
else:
    st.write("⬅️ Select a tool to get started!")
    
    # Show feature overview
    st.markdown("---")
    st.subheader("🚀 New Advanced Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🔬 What-If Simulator**
        - Interactive sliders for Vdc1, Vdc2, φ, δ₁, δ₂, Pload
        - Predict efficiency, temperature, and ZVS regions
        - Real-time parameter impact analysis
        - ZVS heatmap visualization
        
        **📊 One-Click Health Reports**
        - Generate PDF reports (weekly/monthly)
        - Include plots, anomalies, and recommendations
        - Customizable date ranges
        - Professional report templates
        """)
    
    with col2:
        st.markdown("""
        **🚨 Smart Alerting System**
        - Threshold and trend-based alerts
        - Email and Slack integration
        - Configurable alert levels
        - Alert history and management
        
        **💡 AI-Powered Recommendations**
        - Actionable optimization suggestions
        - ZVS restoration strategies
        - Parameter impact analysis
        - Implementation tracking
        """)
    
    st.markdown("---")
    st.markdown("**Select any tool above to explore these advanced features!**")
