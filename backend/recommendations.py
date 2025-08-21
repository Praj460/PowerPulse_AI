import pandas as pd
import numpy as np
from typing import List, Dict, Any

class DABRecommendations:
    """Simplified DAB Converter Recommendations"""
    
    def __init__(self):
        # Basic thresholds
        self.thresholds = {
            'efficiency_percent': {'warning': 95.0, 'critical': 90.0},
            'temperature_C': {'warning': 60.0, 'critical': 70.0},
            'health_score': {'warning': 80.0, 'critical': 60.0}
        }
    
    
    
    def generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate simple recommendations based on current data"""
        recommendations = []
        
        if df.empty:
            return recommendations
        
        latest = df.iloc[-1]
        
        # Efficiency recommendations
        if 'efficiency_percent' in latest:
            efficiency = latest['efficiency_percent']
            if efficiency < self.thresholds['efficiency_percent']['critical']:
                recommendations.append("Critical: Increase phase shift to improve efficiency")
            elif efficiency < self.thresholds['efficiency_percent']['warning']:
                recommendations.append("Warning: Consider optimizing phase shift for better efficiency")
        
        # Temperature recommendations
        if 'temperature_C' in latest:
            temperature = latest['temperature_C']
            if temperature > self.thresholds['temperature_C']['critical']:
                recommendations.append("Critical: Reduce load power to lower temperature")
            elif temperature > self.thresholds['temperature_C']['warning']:
                recommendations.append("Warning: Monitor temperature and consider cooling improvements")
        
        # Health score recommendations
        if 'health_score' in latest:
            health_score = latest['health_score']
            if health_score < self.thresholds['health_score']['critical']:
                recommendations.append("Critical: Perform maintenance on power components")
            elif health_score < self.thresholds['health_score']['warning']:
                recommendations.append("Warning: Schedule preventive maintenance")
        
        return recommendations
    
    def get_parameter_optimization(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return simple parameter optimization suggestions for phi and duty cycles.
        Structure matches what the UI expects in recommendations_panel.py.
        """
        suggestions: Dict[str, Any] = {}
        if df.empty:
            return suggestions
        latest = df.iloc[-1]
        # Phase shift (phi)
        current_phi = float(latest.get('phi', 0.3))
        suggested_phi = float(min(np.pi/2, current_phi + 0.05))
        suggestions['phi'] = {
            'current': current_phi,
            'suggested': suggested_phi,
            'reason': 'Increase φ to improve ZVS margin and efficiency if below target.',
            'expected_impact': 'Potentially increases efficiency and restores ZVS.'
        }
        # Duty cycles balancing
        delta1 = float(latest.get('delta1', 0.5))
        delta2 = float(latest.get('delta2', 0.5))
        balanced = (delta1 + delta2) / 2.0
        suggestions['duty_cycles'] = {
            'current': {'delta1': delta1, 'delta2': delta2},
            'suggested': {'delta1': balanced, 'delta2': balanced},
            'reason': 'Balance duty cycles to reduce circulating current.',
            'expected_impact': 'Improves current balance and ZVS margin.'
        }
        return suggestions

