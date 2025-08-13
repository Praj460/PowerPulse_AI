# 🔌 PowerPulse_AI - DAB Converter Health Monitoring System

A comprehensive AI-powered health monitoring and optimization system for Dual Active Bridge (DAB) converters with advanced simulation, reporting, and alerting capabilities.

## 🚀 New Advanced Features

### 1. 🔬 What-If Simulator
**Interactive parameter simulation with real-time analysis**

- **Parameter Controls**: Interactive sliders for Vdc1, Vdc2, φ (phase shift), δ₁, δ₂ (duty cycles), Pload, and switching frequency
- **Real-time Simulation**: Instant prediction of efficiency, temperature, and ZVS status
- **ZVS Heatmap**: 2D visualization showing ZVS/no-ZVS regions across parameter space
- **Parameter Impact Analysis**: Quantify the effect of parameter changes on performance
- **Performance Comparison**: Compare current settings with optimal defaults

**Key Benefits:**
- Optimize converter performance before implementation
- Identify optimal operating regions
- Understand parameter interdependencies
- Prevent ZVS loss through proactive tuning

### 2. 📊 One-Click Health Reports
**Professional PDF reports with comprehensive analysis**

- **Report Types**: Weekly and monthly health reports
- **Content**: Performance metrics, anomaly detection, trend analysis, and recommendations
- **Customization**: Configurable date ranges and content inclusion
- **Professional Format**: PDF output with executive summary, charts, and tables
- **Scheduling**: Automated report generation and distribution

**Report Sections:**
- Executive Summary with key metrics
- Performance trends and analysis
- Detected anomalies and severity levels
- Actionable recommendations
- Professional charts and visualizations

### 3. 🚨 Smart Alerting System
**Intelligent threshold and trend-based alerts**

- **Alert Types**: Threshold, trend, anomaly, and health degradation alerts
- **Severity Levels**: Info, Warning, Critical, and Emergency
- **Notification Channels**: Email and Slack integration
- **Smart Cooldown**: Prevents alert spam with configurable cooldown periods
- **Alert Management**: Acknowledge, track, and manage active alerts

**Alert Categories:**
- Efficiency threshold violations
- Temperature excursions
- Health score degradation
- Trend-based performance decline
- ZVS operation loss

### 4. 💡 AI-Powered Recommendations
**Actionable optimization suggestions with impact analysis**

- **Recommendation Engine**: AI-generated suggestions based on data analysis
- **Priority Scoring**: Impact-based prioritization with confidence levels
- **Parameter Optimization**: Specific suggestions for φ, δ₁, δ₂ adjustments
- **ZVS Restoration**: Targeted strategies to restore ZVS operation
- **Implementation Tracking**: Monitor recommendation implementation status

**Recommendation Types:**
- Phase shift optimization for efficiency
- Duty cycle balancing for ZVS
- Temperature management strategies
- Preventive maintenance scheduling
- Performance trend investigation

## 🏗️ System Architecture

### Backend Modules
- **`simulator.py`**: DAB converter simulation engine
- **`reports.py`**: PDF report generation system
- **`alerting.py`**: Alert detection and notification system
- **`recommendations.py`**: AI recommendation engine
- **`diagnostics.py`**: Health scoring and anomaly detection

### Frontend Modules
- **`simulator.py`**: Interactive simulation interface
- **`reports.py`**: Report generation and management
- **`alerts.py`**: Alert configuration and monitoring
- **`recommendations_panel.py`**: Recommendations display and management

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Streamlit
- Required dependencies (see requirements.txt)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd PowerPulse_AI

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Configuration
1. **Email Alerts**: Configure SMTP settings in the Alerting System
2. **Slack Integration**: Add webhook URL for Slack notifications
3. **Alert Thresholds**: Customize warning and critical thresholds
4. **Report Settings**: Configure report types and scheduling

## 📊 Key Metrics Monitored

- **Efficiency**: Power conversion efficiency percentage
- **Temperature**: Junction and ambient temperatures
- **Health Score**: Composite health indicator (0-100)
- **ZVS Status**: Zero Voltage Switching operation status
- **Power Losses**: Conduction, switching, and total losses
- **Performance Trends**: Historical performance analysis

## 🔧 Technical Features

### Simulation Engine
- Physics-based DAB converter modeling
- Real-time parameter optimization
- ZVS region boundary calculation
- Loss estimation and efficiency prediction

### Alert System
- Configurable threshold management
- Trend analysis with statistical methods
- Multi-channel notification system
- Alert history and analytics

### Report Generation
- Professional PDF formatting
- Interactive chart generation
- Customizable content templates
- Automated scheduling capabilities

## 📈 Use Cases

### Engineering Teams
- **Performance Optimization**: Use simulator to find optimal parameters
- **Troubleshooting**: Identify root causes of performance issues
- **Design Validation**: Verify converter performance before implementation

### Operations Teams
- **Real-time Monitoring**: Track system health and performance
- **Predictive Maintenance**: Identify maintenance needs before failures
- **Performance Reporting**: Generate reports for stakeholders

### Management Teams
- **Executive Dashboards**: High-level performance overview
- **Trend Analysis**: Long-term performance tracking
- **ROI Analysis**: Quantify optimization benefits

## 🔮 Future Enhancements

- **Machine Learning**: Advanced anomaly detection and prediction
- **Cloud Integration**: Multi-site monitoring and analytics
- **Mobile App**: Real-time alerts and monitoring on mobile devices
- **API Integration**: Connect with existing SCADA and control systems
- **Advanced Analytics**: Predictive maintenance and failure prediction

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code style and standards
- Testing requirements
- Documentation updates
- Feature requests and bug reports

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation and examples

---

**PowerPulse_AI** - Empowering DAB converter optimization through intelligent monitoring and AI-driven insights.
