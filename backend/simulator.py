import numpy as np
import pandas as pd
from typing import Dict

class DABSimulator:
    """Simplified DAB Converter Simulator"""
    
    def __init__(self):
        # Default parameters
        self.default_params = {
            'Vdc1': 400.0,      # Primary DC voltage (V)
            'Vdc2': 48.0,       # Secondary DC voltage (V)
            'phi': 0.3,         # Phase shift (rad)
            'delta1': 0.5,      # Duty cycle 1
            'delta2': 0.5,      # Duty cycle 2
            'Pload': 1000.0,    # Load power (W)
            'fsw': 100000,      # Switching frequency (Hz)
            'L': 50e-6,         # Transformer inductance (H)
            'R_on': 0.1,        # On-resistance (Ω)
            'C_oss': 100e-12,   # Output capacitance (F)
        }
    
    def simulate_efficiency(self, params: Dict[str, float]) -> float:
        """Calculate efficiency based on parameters"""
        Pload = params['Pload']
        delta1, delta2 = params['delta1'], params['delta2']
        Vdc1 = params['Vdc1']
        R_on = params['R_on']
        
        # Simplified loss calculation
        I_transformer = Pload / (Vdc1 * delta1)
        P_conduction = I_transformer**2 * R_on * (delta1 + delta2)
        P_total_loss = P_conduction + 0.02 * Pload  # Add 2% for other losses
        
        efficiency = (Pload / (Pload + P_total_loss)) * 100
        return max(0, min(100, efficiency))
    
    def simulate_temperature(self, params: Dict[str, float]) -> float:
        """Calculate temperature based on power dissipation"""
        efficiency = self.simulate_efficiency(params)
        Pload = params['Pload']
        
        # Simple temperature calculation
        P_dissipated = Pload * (1 - efficiency/100)
        return 25.0 + P_dissipated * 0.5  # 25°C ambient + 0.5°C/W thermal resistance
    
    def check_zvs_status(self, params: Dict[str, float]) -> bool:
        """Check if ZVS operation is achieved"""
        phi = params['phi']
        Pload = params['Pload']
        Vdc1 = params['Vdc1']
        delta1 = params['delta1']
        
        # Simplified ZVS check
        I_transformer = Pload / (Vdc1 * delta1)
        return (phi > 0.1) and (I_transformer > 0.3)
    
    
    def run_simulation(self, params: Dict[str, float]) -> Dict[str, float]:
        """Run basic simulation with given parameters"""
        efficiency = self.simulate_efficiency(params)
        temperature = self.simulate_temperature(params)
        zvs_status = self.check_zvs_status(params)
        
        return {
            'efficiency': efficiency,
            'temperature': temperature,
            'zvs_status': zvs_status
        }
    
