import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta

class DABRecommendations:
    """DAB Converter Recommendations Engine"""
    
    def __init__(self):
        # Thresholds for different metrics
        self.thresholds = {
            'efficiency': {'warning': 95.0, 'critical': 90.0},
            'temperature': {'warning': 60.0, 'critical': 70.0},
            'health_score': {'warning': 80.0, 'critical': 60.0},
            'power_loss': {'warning': 100.0, 'critical': 200.0}
        }
        
        # Recommendation templates
        self.templates = {
            'efficiency_low': [
                "Increase phase shift (φ) by {delta:.3f} to improve efficiency by ~{improvement:.1f}%",
                "Optimize duty cycles (δ₁, δ₂) to reduce conduction losses",
                "Check transformer inductance value and consider tuning for better power transfer"
            ],
            'temperature_high': [
                "Reduce load power by {reduction:.0f}W to lower temperature by ~{temp_drop:.1f}°C",
                "Increase cooling system efficiency or check thermal management",
                "Optimize switching frequency to reduce switching losses"
            ],
            'zvs_loss': [
                "Increase phase shift (φ) by {delta:.3f} to restore ZVS on leg-2 at {power:.1f} kW",
                "Adjust duty cycles to maintain sufficient transformer current for ZVS",
                "Consider reducing switching frequency to improve ZVS margin"
            ],
            'health_degradation': [
                "Perform preventive maintenance on power components",
                "Check for component aging or degradation",
                "Review operating conditions and optimize parameters"
            ]
        }
    
    def analyze_trends(self, df: pd.DataFrame, hours: int = 24) -> Dict[str, Any]:
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
    
    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in the data"""
        anomalies = []
        
        if df.empty:
            return anomalies
        
        # Get latest data point
        latest = df.iloc[-1]
        
        # Check each metric against thresholds
        for metric, thresholds in self.thresholds.items():
            if metric in latest:
                value = latest[metric]
                warning_thresh = thresholds['warning']
                critical_thresh = thresholds['critical']
                
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
    
    def generate_recommendations(self, df: pd.DataFrame, anomalies: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on data analysis"""
        recommendations = []
        
        if df.empty:
            return recommendations
        
        # Analyze trends
        trends = self.analyze_trends(df)
        
        # Get latest data
        latest = df.iloc[-1]
        
        # Efficiency recommendations
        if 'efficiency_percent' in latest:
            efficiency = latest['efficiency_percent']
            if efficiency < self.thresholds['efficiency']['warning']:
                # Calculate improvement potential
                target_efficiency = 98.0  # Target efficiency
                improvement = target_efficiency - efficiency
                
                # Estimate phase shift adjustment
                delta_phi = min(0.1, improvement / 100)  # Conservative estimate
                
                recommendations.append({
                    'action': f"Increase phase shift (φ) by {delta_phi:.3f} to improve efficiency by ~{improvement:.1f}%",
                    'impact': f"Expected efficiency improvement: {improvement:.1f}%",
                    'priority': 'high' if efficiency < self.thresholds['efficiency']['critical'] else 'medium',
                    'category': 'efficiency',
                    'estimated_effort': 'low',
                    'confidence': 0.8
                })
        
        # Temperature recommendations
        if 'temperature_C' in latest:
            temperature = latest['temperature_C']
            if temperature > self.thresholds['temperature']['warning']:
                # Calculate power reduction needed
                temp_excess = temperature - self.thresholds['temperature']['warning']
                power_reduction = temp_excess * 20  # Rough estimate: 20W per °C
                
                recommendations.append({
                    'action': f"Reduce load power by {power_reduction:.0f}W to lower temperature by ~{temp_excess:.1f}°C",
                    'impact': f"Expected temperature reduction: {temp_excess:.1f}°C",
                    'priority': 'high' if temperature > self.thresholds['temperature']['critical'] else 'medium',
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
            if health_score < self.thresholds['health_score']['warning']:
                # Check trend
                if 'health_score' in trends:
                    trend = trends['health_score']
                    if trend['pct_change'] < -10:  # More than 10% degradation
                        recommendations.append({
                            'action': "Perform preventive maintenance on power components",
                            'impact': "Prevent further degradation and potential failures",
                            'priority': 'high',
                            'category': 'maintenance',
                            'estimated_effort': 'high',
                            'confidence': 0.9
                        })
        
        # Trend-based recommendations
        for metric, trend in trends.items():
            if trend['pct_change'] < -5:  # More than 5% degradation
                if metric == 'efficiency_percent':
                    recommendations.append({
                        'action': "Investigate efficiency degradation trend",
                        'impact': "Identify root cause of performance decline",
                        'priority': 'medium',
                        'category': 'investigation',
                        'estimated_effort': 'medium',
                        'confidence': 0.7
                    })
                elif metric == 'temperature_C':
                    recommendations.append({
                        'action': "Monitor temperature trend and check cooling system",
                        'impact': "Prevent thermal runaway and component damage",
                        'priority': 'medium',
                        'category': 'thermal',
                        'estimated_effort': 'low',
                        'confidence': 0.6
                    })
        
        # Sort by priority and confidence
        priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        recommendations.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['confidence']), reverse=True)
        
        return recommendations
    
    def get_parameter_optimization(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get parameter optimization suggestions"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        suggestions = {}
        
        # Phase shift optimization
        if 'phi' in latest and 'efficiency_percent' in latest:
            phi = latest['phi']
            efficiency = latest['efficiency_percent']
            
            if efficiency < 95:
                # Suggest phase shift increase
                suggested_phi = min(np.pi/2, phi + 0.05)
                suggestions['phi'] = {
                    'current': phi,
                    'suggested': suggested_phi,
                    'reason': 'Improve efficiency and ZVS operation',
                    'expected_impact': 'efficiency_improvement'
                }
        
        # Duty cycle optimization
        if 'delta1' in latest and 'delta2' in latest:
            delta1, delta2 = latest['delta1'], latest['delta2']
            
            # Check for duty cycle imbalance
            if abs(delta1 - delta2) > 0.1:
                balanced_delta = (delta1 + delta2) / 2
                suggestions['duty_cycles'] = {
                    'current': {'delta1': delta1, 'delta2': delta2},
                    'suggested': {'delta1': balanced_delta, 'delta2': balanced_delta},
                    'reason': 'Balance duty cycles for optimal performance',
                    'expected_impact': 'reduced_conduction_losses'
                }
        
        return suggestions
    
    def calculate_impact_score(self, recommendation: Dict[str, Any]) -> float:
        """Calculate impact score for a recommendation (0-100)"""
        base_score = 0
        
        # Priority impact
        priority_scores = {'critical': 40, 'high': 30, 'medium': 20, 'low': 10}
        base_score += priority_scores.get(recommendation.get('priority', 'low'), 10)
        
        # Confidence impact
        base_score += recommendation.get('confidence', 0.5) * 30
        
        # Effort impact (lower effort = higher score)
        effort_scores = {'low': 20, 'medium': 15, 'high': 10}
        base_score += effort_scores.get(recommendation.get('estimated_effort', 'medium'), 15)
        
        return min(100, base_score)
