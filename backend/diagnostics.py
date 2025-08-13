import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta

def compute_health_score(row):
    # Simple example: combine normalized efficiency and temp
    score = 0.5 * (row['efficiency_percent'] / 98) \
          + 0.3 * (1 - (row['temperature_C'] - 35) / (65 - 35)) \
          + 0.2 * (row['ZVS_status'])
    return round(score * 100, 1)

def add_health_scores(df):
    df['health_score'] = df.apply(compute_health_score, axis=1)
    return df

def detect_anomalies(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect anomalies in the data using statistical methods"""
    anomalies = []
    
    if df.empty:
        return anomalies
    
    # Get latest data point
    latest = df.iloc[-1]
    
    # Define thresholds for different metrics
    thresholds = {
        'efficiency_percent': {'warning': 95.0, 'critical': 90.0},
        'temperature_C': {'warning': 60.0, 'critical': 70.0},
        'health_score': {'warning': 80.0, 'critical': 60.0},
        'power_loss_W': {'warning': 100.0, 'critical': 200.0}
    }
    
    # Check each metric against thresholds
    for metric, threshold_values in thresholds.items():
        if metric in latest:
            value = latest[metric]
            warning_thresh = threshold_values['warning']
            critical_thresh = threshold_values['critical']
            
            if metric == 'efficiency_percent':
                # For efficiency, lower is worse
                if value < critical_thresh:
                    severity = 'critical'
                    threshold = critical_thresh
                elif value < warning_thresh:
                    severity = 'warning'
                    threshold = warning_thresh
                else:
                    continue
            elif metric == 'temperature_C':
                # For temperature, higher is worse
                if value > critical_thresh:
                    severity = 'critical'
                    threshold = critical_thresh
                elif value > warning_thresh:
                    severity = 'warning'
                    threshold = warning_thresh
                else:
                    continue
            elif metric == 'health_score':
                # For health score, lower is worse
                if value < critical_thresh:
                    severity = 'critical'
                    threshold = critical_thresh
                elif value < warning_thresh:
                    severity = 'warning'
                    threshold = warning_thresh
                else:
                    continue
            elif metric == 'power_loss_W':
                # For power loss, higher is worse
                if value > critical_thresh:
                    severity = 'critical'
                    threshold = critical_thresh
                elif value > warning_thresh:
                    severity = 'warning'
                    threshold = warning_thresh
                else:
                    continue
            
            anomalies.append({
                'timestamp': latest['timestamp'],
                'metric': metric,
                'value': value,
                'threshold': threshold,
                'severity': severity,
                'message': f"{metric.replace('_', ' ').title()} is {severity}: {value:.2f} (threshold: {threshold:.2f})"
            })
    
    return anomalies

def generate_recommendations(df: pd.DataFrame, anomalies: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on data analysis"""
    recommendations = []
    
    if df.empty:
        return recommendations
    
    # Get latest data
    latest = df.iloc[-1]
    
    # Efficiency recommendations
    if 'efficiency_percent' in latest:
        efficiency = latest['efficiency_percent']
        if efficiency < 95.0:
            # Calculate improvement potential
            target_efficiency = 98.0  # Target efficiency
            improvement = target_efficiency - efficiency
            
            # Estimate phase shift adjustment
            delta_phi = min(0.1, improvement / 100)  # Conservative estimate
            
            recommendations.append({
                'action': f"Increase phase shift (φ) by {delta_phi:.3f} to improve efficiency by ~{improvement:.1f}%",
                'impact': f"Expected efficiency improvement: {improvement:.1f}%",
                'priority': 'high' if efficiency < 90.0 else 'medium',
                'category': 'efficiency',
                'estimated_effort': 'low',
                'confidence': 0.8
            })
    
    # Temperature recommendations
    if 'temperature_C' in latest:
        temperature = latest['temperature_C']
        if temperature > 60.0:
            # Calculate power reduction needed
            temp_excess = temperature - 60.0
            power_reduction = temp_excess * 20  # Rough estimate: 20W per °C
            
            recommendations.append({
                'action': f"Reduce load power by {power_reduction:.0f}W to lower temperature by ~{temp_excess:.1f}°C",
                'impact': f"Expected temperature reduction: {temp_excess:.1f}°C",
                'priority': 'high' if temperature > 70.0 else 'medium',
                'category': 'thermal',
                'estimated_effort': 'medium',
                'confidence': 0.7
            })
    
    # ZVS recommendations
    if 'ZVS_status' in latest:
        zvs_status = latest['ZVS_status']
        if not zvs_status:
            # Check if we can estimate phase shift adjustment
            if 'phi' in latest:
                current_phi = latest['phi']
                target_phi = min(np.pi/2, current_phi + 0.05)
                delta_phi = target_phi - current_phi
                
                recommendations.append({
                    'action': f"Increase phase shift (φ) by {delta_phi:.3f} to restore ZVS operation",
                    'impact': "Expected ZVS restoration and reduced switching losses",
                    'priority': 'medium',
                    'category': 'zvs',
                    'estimated_effort': 'low',
                    'confidence': 0.6
                })
    
    # Health score recommendations
    if 'health_score' in latest:
        health_score = latest['health_score']
        if health_score < 80.0:
            recommendations.append({
                'action': "Perform preventive maintenance on power components",
                'impact': "Prevent further degradation and potential failures",
                'priority': 'high',
                'category': 'maintenance',
                'estimated_effort': 'high',
                'confidence': 0.9
            })
    
    # Sort by priority and confidence
    priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
    recommendations.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['confidence']), reverse=True)
    
    return recommendations

def analyze_trends(df: pd.DataFrame, hours: int = 24) -> Dict[str, Any]:
    """Analyze trends in the data over specified time period"""
    if df.empty:
        return {}
    
    # Get recent data
    latest_time = df['timestamp'].max()
    start_time = latest_time - timedelta(hours=hours)
    recent_df = df[df['timestamp'] >= start_time]
    
    if recent_df.empty:
        return {}
    
    # Calculate trends
    trends = {}
    metrics = ['efficiency_percent', 'temperature_C', 'health_score', 'power_loss_W']
    
    for metric in metrics:
        if metric in recent_df.columns:
            values = recent_df[metric].dropna()
            if len(values) > 1:
                # Linear regression for trend
                x = np.arange(len(values))
                slope = np.polyfit(x, values, 1)[0]
                
                # Calculate percentage change
                if values.iloc[0] != 0:
                    pct_change = ((values.iloc[-1] - values.iloc[0]) / values.iloc[0]) * 100
                else:
                    pct_change = 0
                
                trends[metric] = {
                    'slope': slope,
                    'pct_change': pct_change,
                    'trend': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                    'current': values.iloc[-1],
                    'average': values.mean()
                }
    
    return trends
