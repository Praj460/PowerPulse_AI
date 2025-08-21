import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

def compute_health_score(row):
    """Calculate health score based on efficiency, temperature, and ZVS status"""
    score = 0.5 * (row['efficiency_percent'] / 98) \
          + 0.3 * (1 - (row['temperature_C'] - 35) / (65 - 35)) \
          + 0.2 * (row['ZVS_status'])
    return round(score * 100, 1)

def add_health_scores(df):
    """Add health scores to dataframe"""
    df['health_score'] = df.apply(compute_health_score, axis=1)
    return df

def detect_anomalies(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect basic anomalies in the data and include fields used by reports."""
    anomalies: List[Dict[str, Any]] = []
    
    if df.empty:
        return anomalies
    
    latest = df.iloc[-1]
    ts = latest['timestamp'] if 'timestamp' in latest else datetime.now()
    
    # Threshold rules
    thresholds = {
        'efficiency_percent': {'warning': 95.0, 'critical': 90.0, 'direction': 'low'},
        'temperature_C': {'warning': 60.0, 'critical': 70.0, 'direction': 'high'},
        'health_score': {'warning': 80.0, 'critical': 60.0, 'direction': 'low'},
    }
    
    for metric, cfg in thresholds.items():
        if metric in latest:
            val = latest[metric]
            severity = None
            thr = None
            if cfg['direction'] == 'low':
                if val <= cfg['critical']:
                    severity = 'critical'
                    thr = cfg['critical']
                elif val <= cfg['warning']:
                    severity = 'warning'
                    thr = cfg['warning']
            else:  # high means higher is worse
                if val >= cfg['critical']:
                    severity = 'critical'
                    thr = cfg['critical']
                elif val >= cfg['warning']:
                    severity = 'warning'
                    thr = cfg['warning']
            
            if severity:
                anomalies.append({
                    'timestamp': pd.to_datetime(ts),
                    'metric': metric,
                    'value': float(val),
                    'threshold': float(thr),
                    'severity': severity,
                    'message': f"{metric.replace('_',' ').title()} {'low' if cfg['direction']=='low' else 'high'}: {val} (thr: {thr})"
                })
    
    return anomalies

def generate_basic_recommendations(df: pd.DataFrame) -> List[str]:
    """Generate simple recommendations based on current data"""
    recommendations = []
    
    if df.empty:
        return recommendations
    
    latest = df.iloc[-1]
    
    # Simple efficiency check
    if 'efficiency_percent' in latest and latest['efficiency_percent'] < 95.0:
        recommendations.append("Consider increasing phase shift to improve efficiency")
    
    # Simple temperature check
    if 'temperature_C' in latest and latest['temperature_C'] > 60.0:
        recommendations.append("Reduce load power or improve cooling to lower temperature")
    
    # Simple ZVS check
    if 'ZVS_status' in latest and not latest['ZVS_status']:
        recommendations.append("Adjust phase shift to restore ZVS operation")
    
    return recommendations

def analyze_trends(df: pd.DataFrame, hours: int = 24) -> Dict[str, Any]:
    """Analyze simple trends over a period and return percent changes per metric."""
    trends: Dict[str, Any] = {}
    if df.empty or 'timestamp' not in df.columns:
        return trends
    
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp']).sort_values('timestamp')
    if df.empty:
        return trends
    
    cutoff = df['timestamp'].max() - pd.Timedelta(hours=hours)
    window_df = df[df['timestamp'] >= cutoff]
    if len(window_df) < 2:
        return trends
    
    metrics = ['efficiency_percent', 'temperature_C', 'health_score']
    for metric in metrics:
        if metric in window_df.columns and window_df[metric].notna().sum() >= 2:
            start_val = window_df[metric].iloc[0]
            end_val = window_df[metric].iloc[-1]
            if pd.notna(start_val) and start_val != 0 and pd.notna(end_val):
                pct_change = ((end_val - start_val) / abs(start_val)) * 100.0
                avg_val = window_df[metric].mean()
                trends[metric] = {
                    'start': float(start_val),
                    'end': float(end_val),
                    'current': float(end_val),
                    'average': float(avg_val) if pd.notna(avg_val) else float('nan'),
                    'pct_change': float(pct_change),
                    'trend': 'increasing' if pct_change > 0 else 'decreasing' if pct_change < 0 else 'stable'
                }
    return trends

