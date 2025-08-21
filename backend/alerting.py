import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertType(Enum):
    THRESHOLD = "threshold"
    TREND = "trend"
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

class DABAlerting:
    """Simplified DAB Converter Alerting System"""
    
    def __init__(self):
        # Active, unacknowledged alerts
        self.alerts: List[Alert] = []
        # Historical record (acknowledged + resolved alerts)
        self.alert_history: List[Alert] = []
        
        # Thresholds used by threshold checks
        self.thresholds = {
            'efficiency_percent': {'warning': 95.0, 'critical': 90.0},
            'temperature_C': {'warning': 60.0, 'critical': 70.0},
            'health_score': {'warning': 80.0, 'critical': 60.0}
        }
        
        # Trend thresholds (percent change over window)
        self.trend_thresholds = {
            'efficiency_percent': -5.0,   # drop more than 5%
            'temperature_C': 5.0,         # rise more than 5%
            'health_score': -5.0          # drop more than 5%
        }
        
        # Notification config stubs
        self.config: Dict[str, Any] = {
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'recipients': []
            },
            'slack': {
                'enabled': False,
                'webhook_url': '',
                'channel': ''
            }
        }
    
    
    def check_alerts(self, df: pd.DataFrame) -> List[Alert]:
        """Backward-compatible wrapper for threshold alerts."""
        return self.check_threshold_alerts(df)

    def check_threshold_alerts(self, df: pd.DataFrame) -> List[Alert]:
        """Check for basic threshold alerts and store them as active alerts."""
        new_alerts: List[Alert] = []
        if df.empty:
            return new_alerts
        latest = df.iloc[-1]
        for metric, thresholds in self.thresholds.items():
            if metric in latest:
                value = float(latest[metric])
                severity = None
                thr = None
                if metric == 'efficiency_percent':
                    if value <= thresholds['critical']:
                        severity = AlertSeverity.CRITICAL
                        thr = thresholds['critical']
                    elif value <= thresholds['warning']:
                        severity = AlertSeverity.WARNING
                        thr = thresholds['warning']
                else:
                    if value >= thresholds['critical']:
                        severity = AlertSeverity.CRITICAL
                        thr = thresholds['critical']
                    elif value >= thresholds['warning']:
                        severity = AlertSeverity.WARNING
                        thr = thresholds['warning']
                if severity:
                    alert = Alert(
                        timestamp=latest.get('timestamp', datetime.now()),
                        severity=severity,
                        alert_type=AlertType.THRESHOLD,
                        message=f"{metric.replace('_', ' ').title()}: {value:.2f} (threshold: {thr:.2f})",
                        metric=metric,
                        value=value,
                        threshold=float(thr)
                    )
                    self.alerts.append(alert)
                    self.alert_history.append(alert)
                    new_alerts.append(alert)
        return new_alerts

    def check_trend_alerts(self, df: pd.DataFrame, hours: int = 24) -> List[Alert]:
        """Raise alerts based on percent change trends over a time window."""
        new_alerts: List[Alert] = []
        if df.empty or 'timestamp' not in df.columns:
            return new_alerts
        sdf = df.copy()
        sdf['timestamp'] = pd.to_datetime(sdf['timestamp'], errors='coerce')
        sdf = sdf.dropna(subset=['timestamp']).sort_values('timestamp')
        if len(sdf) < 2:
            return new_alerts
        cutoff = sdf['timestamp'].max() - pd.Timedelta(hours=hours)
        wdf = sdf[sdf['timestamp'] >= cutoff]
        if len(wdf) < 2:
            return new_alerts
        for metric, threshold in self.trend_thresholds.items():
            if metric in wdf.columns and wdf[metric].notna().sum() >= 2:
                start = float(wdf[metric].iloc[0])
                end = float(wdf[metric].iloc[-1])
                if start != 0:
                    pct = ((end - start) / abs(start)) * 100.0
                    trigger = (pct <= threshold) if threshold < 0 else (pct >= threshold)
                    if trigger:
                        severity = AlertSeverity.WARNING if abs(pct) < abs(threshold) * 2 else AlertSeverity.CRITICAL
                        alert = Alert(
                            timestamp=wdf['timestamp'].iloc[-1],
                            severity=severity,
                            alert_type=AlertType.TREND,
                            message=f"{metric.replace('_',' ').title()} trend {pct:+.1f}% over {hours}h",
                            metric=metric,
                            value=end,
                            trend_data={'start': start, 'end': end, 'pct_change': pct}
                        )
                        self.alerts.append(alert)
                        self.alert_history.append(alert)
                        new_alerts.append(alert)
        return new_alerts

    def check_health_degradation_alerts(self, df: pd.DataFrame, hours: int = 24) -> List[Alert]:
        """Specific alerts for health_score degradation over time."""
        if 'health_score' not in df.columns:
            return []
        return [a for a in self.check_trend_alerts(df, hours) if a.metric == 'health_score']

    def get_active_alerts(self) -> List[Alert]:
        """Return current, unacknowledged alerts."""
        return [a for a in self.alerts if not a.acknowledged]

    def acknowledge_alert(self, index: int, user: str = "") -> None:
        """Acknowledge and remove an active alert by index."""
        if 0 <= index < len(self.alerts):
            self.alerts[index].acknowledged = True
            # Remove from active list while keeping in history
            self.alerts.pop(index)

    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Summarize alerts in the last window."""
        cutoff = datetime.now() - pd.Timedelta(hours=hours)
        recent = [a for a in self.alert_history if a.timestamp > cutoff]
        summary: Dict[str, Any] = {
            'total_alerts': len(recent),
            'unacknowledged': len([a for a in self.alerts if not a.acknowledged]),
            'by_severity': {},
            'by_type': {}
        }
        for a in recent:
            summary['by_severity'][a.severity.value] = summary['by_severity'].get(a.severity.value, 0) + 1
            summary['by_type'][a.alert_type.value] = summary['by_type'].get(a.alert_type.value, 0) + 1
        return summary

    # Notification stubs
    def _send_email_alert(self, alert: Alert) -> None:
        """Stub: integrate with SMTP as needed."""
        return None

    def _send_slack_alert(self, alert: Alert) -> None:
        """Stub: integrate with Slack webhook as needed."""
        return None
    
    
    
    
    def get_alerts(self) -> List[Alert]:
        """Get current alerts (alias for get_active_alerts)."""
        return self.get_active_alerts()
