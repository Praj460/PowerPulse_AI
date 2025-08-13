import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import requests
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertType(Enum):
    THRESHOLD = "threshold"
    TREND = "trend"
    ANOMALY = "anomaly"
    HEALTH_DEGRADATION = "health_degradation"

@dataclass
class Alert:
    timestamp: datetime
    severity: AlertSeverity
    alert_type: AlertType
    message: str
    metric: str
    value: float
    threshold: Optional[float] = None
    trend_data: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

class DABAlerting:
    """DAB Converter Alerting System"""
    
    def __init__(self, config_file: str = None):
        self.alerts: List[Alert] = []
        self.config = self._load_config(config_file)
        self.alert_history: List[Alert] = []
        
        # Alert thresholds
        self.thresholds = {
            'efficiency_percent': {'warning': 95.0, 'critical': 90.0, 'emergency': 85.0},
            'temperature_C': {'warning': 60.0, 'critical': 70.0, 'emergency': 80.0},
            'health_score': {'warning': 80.0, 'critical': 60.0, 'emergency': 40.0},
            'power_loss_W': {'warning': 100.0, 'critical': 200.0, 'emergency': 300.0},
            'switching_loss_W': {'warning': 50.0, 'critical': 100.0, 'emergency': 150.0},
            'conduction_loss_W': {'warning': 30.0, 'critical': 60.0, 'emergency': 90.0}
        }
        
        # Trend thresholds
        self.trend_thresholds = {
            'efficiency_percent': {'warning': -5.0, 'critical': -10.0, 'emergency': -15.0},
            'temperature_C': {'warning': 5.0, 'critical': 10.0, 'emergency': 15.0},
            'health_score': {'warning': -5.0, 'critical': -10.0, 'emergency': -15.0}
        }
        
        # Cooldown periods (prevent spam)
        self.cooldown_periods = {
            AlertSeverity.INFO: timedelta(minutes=30),
            AlertSeverity.WARNING: timedelta(minutes=15),
            AlertSeverity.CRITICAL: timedelta(minutes=5),
            AlertSeverity.EMERGENCY: timedelta(minutes=1)
        }
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'recipients': []
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': '#alerts'
            },
            'alert_cooldown': True,
            'max_alerts_per_hour': 10
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    for key, value in user_config.items():
                        if key in default_config:
                            if isinstance(value, dict):
                                default_config[key].update(value)
                            else:
                                default_config[key] = value
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_config
    
    def check_threshold_alerts(self, df: pd.DataFrame) -> List[Alert]:
        """Check for threshold-based alerts"""
        new_alerts = []
        
        if df.empty:
            return new_alerts
        
        latest = df.iloc[-1]
        
        for metric, thresholds in self.thresholds.items():
            if metric in latest:
                value = latest[metric]
                
                # Determine severity
                severity = None
                threshold = None
                
                if metric == 'efficiency_percent':
                    # For efficiency, lower is worse
                    if value <= thresholds['emergency']:
                        severity = AlertSeverity.EMERGENCY
                        threshold = thresholds['emergency']
                    elif value <= thresholds['critical']:
                        severity = AlertSeverity.CRITICAL
                        threshold = thresholds['critical']
                    elif value <= thresholds['warning']:
                        severity = AlertSeverity.WARNING
                        threshold = thresholds['warning']
                else:
                    # For other metrics, higher is worse
                    if value >= thresholds['emergency']:
                        severity = AlertSeverity.EMERGENCY
                        threshold = thresholds['emergency']
                    elif value >= thresholds['critical']:
                        severity = AlertSeverity.CRITICAL
                        threshold = thresholds['critical']
                    elif value >= thresholds['warning']:
                        severity = AlertSeverity.WARNING
                        threshold = thresholds['warning']
                
                if severity:
                    # Check cooldown
                    if not self._is_in_cooldown(metric, severity):
                        alert = Alert(
                            timestamp=latest['timestamp'],
                            severity=severity,
                            alert_type=AlertType.THRESHOLD,
                            message=f"{metric.replace('_', ' ').title()} threshold exceeded: {value:.2f} (threshold: {threshold:.2f})",
                            metric=metric,
                            value=value,
                            threshold=threshold
                        )
                        
                        new_alerts.append(alert)
                        self._add_alert(alert)
        
        return new_alerts
    
    def check_trend_alerts(self, df: pd.DataFrame, hours: int = 24) -> List[Alert]:
        """Check for trend-based alerts"""
        new_alerts = []
        
        if df.empty or len(df) < 2:
            return new_alerts
        
        # Get recent data
        latest_time = df['timestamp'].max()
        start_time = latest_time - timedelta(hours=hours)
        recent_df = df[df['timestamp'] >= start_time]
        
        if len(recent_df) < 2:
            return new_alerts
        
        for metric, thresholds in self.trend_thresholds.items():
            if metric in recent_df.columns:
                values = recent_df[metric].dropna()
                if len(values) > 1:
                    # Calculate percentage change
                    if values.iloc[0] != 0:
                        pct_change = ((values.iloc[-1] - values.iloc[0]) / values.iloc[0]) * 100
                    else:
                        pct_change = 0
                    
                    # Determine severity based on trend
                    severity = None
                    threshold = None
                    
                    if metric == 'efficiency_percent' or metric == 'health_score':
                        # For these metrics, negative change is bad
                        if pct_change <= thresholds['emergency']:
                            severity = AlertSeverity.EMERGENCY
                            threshold = thresholds['emergency']
                        elif pct_change <= thresholds['critical']:
                            severity = AlertSeverity.CRITICAL
                            threshold = thresholds['critical']
                        elif pct_change <= thresholds['warning']:
                            severity = AlertSeverity.WARNING
                            threshold = thresholds['warning']
                    else:
                        # For other metrics, positive change is bad
                        if pct_change >= thresholds['emergency']:
                            severity = AlertSeverity.EMERGENCY
                            threshold = thresholds['emergency']
                        elif pct_change >= thresholds['critical']:
                            severity = AlertSeverity.CRITICAL
                            threshold = thresholds['critical']
                        elif pct_change >= thresholds['warning']:
                            severity = AlertSeverity.WARNING
                            threshold = thresholds['warning']
                    
                    if severity:
                        # Check cooldown
                        if not self._is_in_cooldown(f"{metric}_trend", severity):
                            trend_direction = "decreased" if pct_change < 0 else "increased"
                            alert = Alert(
                                timestamp=latest_time,
                                severity=severity,
                                alert_type=AlertType.TREND,
                                message=f"{metric.replace('_', ' ').title()} has {trend_direction} by {abs(pct_change):.1f}% in the last {hours}h (threshold: {threshold:.1f}%)",
                                metric=metric,
                                value=pct_change,
                                threshold=threshold,
                                trend_data={
                                    'pct_change': pct_change,
                                    'time_period': hours,
                                    'start_value': values.iloc[0],
                                    'end_value': values.iloc[-1]
                                }
                            )
                            
                            new_alerts.append(alert)
                            self._add_alert(alert)
        
        return new_alerts
    
    def check_health_degradation_alerts(self, df: pd.DataFrame, hours: int = 24) -> List[Alert]:
        """Check for health score degradation alerts"""
        new_alerts = []
        
        if df.empty or 'health_score' not in df.columns:
            return new_alerts
        
        # Get recent data
        latest_time = df['timestamp'].max()
        start_time = latest_time - timedelta(hours=hours)
        recent_df = df[df['timestamp'] >= start_time]
        
        if len(recent_df) < 2:
            return new_alerts
        
        health_scores = recent_df['health_score'].dropna()
        if len(health_scores) < 2:
            return new_alerts
        
        # Calculate health degradation
        initial_health = health_scores.iloc[0]
        current_health = health_scores.iloc[-1]
        
        if initial_health > 0:
            degradation = ((initial_health - current_health) / initial_health) * 100
            
            # Check for significant degradation
            if degradation >= 10:  # More than 10% degradation
                severity = AlertSeverity.CRITICAL if degradation >= 20 else AlertSeverity.WARNING
                
                if not self._is_in_cooldown("health_degradation", severity):
                    alert = Alert(
                        timestamp=latest_time,
                        severity=severity,
                        alert_type=AlertType.HEALTH_DEGRADATION,
                        message=f"Health score has degraded by {degradation:.1f}% in the last {hours}h (from {initial_health:.1f} to {current_health:.1f})",
                        metric='health_score',
                        value=degradation,
                        threshold=10.0,
                        trend_data={
                            'degradation_pct': degradation,
                            'time_period': hours,
                            'initial_health': initial_health,
                            'current_health': current_health
                        },
                        recommendations=[
                            "Check for component aging or degradation",
                            "Review operating conditions and optimize parameters",
                            "Consider preventive maintenance"
                        ]
                    )
                    
                    new_alerts.append(alert)
                    self._add_alert(alert)
        
        return new_alerts
    
    def _is_in_cooldown(self, metric: str, severity: AlertSeverity) -> bool:
        """Check if alert is in cooldown period"""
        if not self.config['alert_cooldown']:
            return False
        
        cooldown_period = self.cooldown_periods[severity]
        cutoff_time = datetime.now() - cooldown_period
        
        # Check recent alerts for this metric and severity
        recent_alerts = [a for a in self.alert_history 
                        if a.metric == metric and a.severity == severity 
                        and a.timestamp > cutoff_time]
        
        return len(recent_alerts) > 0
    
    def _add_alert(self, alert: Alert):
        """Add alert to history and send notifications"""
        self.alert_history.append(alert)
        
        # Limit history size
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Send notifications
        self._send_notifications(alert)
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications via email and Slack"""
        # Send email
        if self.config['email']['enabled']:
            self._send_email_alert(alert)
        
        # Send Slack
        if self.config['slack']['enabled']:
            self._send_slack_alert(alert)
    
    def _send_email_alert(self, alert: Alert):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['username']
            msg['To'] = ', '.join(self.config['email']['recipients'])
            msg['Subject'] = f"DAB Alert: {alert.severity.value.upper()} - {alert.alert_type.value}"
            
            body = f"""
DAB Converter Alert

Severity: {alert.severity.value.upper()}
Type: {alert.alert_type.value}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Metric: {alert.metric}
Value: {alert.value:.2f}
Message: {alert.message}

"""
            
            if alert.recommendations:
                body += "Recommendations:\n"
                for rec in alert.recommendations:
                    body += f"- {rec}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['username'], self.config['email']['password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _send_slack_alert(self, alert: Alert):
        """Send Slack alert"""
        try:
            # Color coding based on severity
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ffcc00",
                AlertSeverity.CRITICAL: "#ff6600",
                AlertSeverity.EMERGENCY: "#cc0000"
            }
            
            payload = {
                "channel": self.config['slack']['channel'],
                "attachments": [{
                    "color": color_map.get(alert.severity, "#cccccc"),
                    "title": f"DAB Converter Alert: {alert.severity.value.upper()}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Metric",
                            "value": alert.metric,
                            "short": True
                        },
                        {
                            "title": "Value",
                            "value": f"{alert.value:.2f}",
                            "short": True
                        },
                        {
                            "title": "Type",
                            "value": alert.alert_type.value,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime('%H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "DAB HealthAI System"
                }]
            }
            
            if alert.recommendations:
                payload['attachments'][0]['fields'].append({
                    "title": "Recommendations",
                    "value": "\n".join([f"• {rec}" for rec in alert.recommendations]),
                    "short": False
                })
            
            response = requests.post(self.config['slack']['webhook_url'], json=payload)
            response.raise_for_status()
            
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active (unacknowledged) alerts"""
        if severity:
            return [a for a in self.alert_history if not a.acknowledged and a.severity == severity]
        return [a for a in self.alert_history if not a.acknowledged]
    
    def acknowledge_alert(self, alert_index: int, user: str):
        """Acknowledge an alert"""
        if 0 <= alert_index < len(self.alert_history):
            alert = self.alert_history[alert_index]
            alert.acknowledged = True
            alert.acknowledged_by = user
            alert.acknowledged_at = datetime.now()
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of alerts in the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a.timestamp > cutoff_time]
        
        summary = {
            'total_alerts': len(recent_alerts),
            'by_severity': {},
            'by_type': {},
            'acknowledged': len([a for a in recent_alerts if a.acknowledged]),
            'unacknowledged': len([a for a in recent_alerts if not a.acknowledged])
        }
        
        # Count by severity
        for severity in AlertSeverity:
            summary['by_severity'][severity.value] = len([a for a in recent_alerts if a.severity == severity])
        
        # Count by type
        for alert_type in AlertType:
            summary['by_type'][alert_type.value] = len([a for a in recent_alerts if a.alert_type == alert_type])
        
        return summary
