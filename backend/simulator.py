import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
import streamlit as st

class DABSimulator:
    """DAB Converter What-If Simulator"""
    
    def __init__(self):
        # Default parameters based on typical DAB converter
        self.default_params = {
            'Vdc1': 400.0,      # Primary DC voltage (V)
            'Vdc2': 48.0,       # Secondary DC voltage (V)
            'phi': 0.3,          # Phase shift (rad)
            'delta1': 0.5,      # Duty cycle 1
            'delta2': 0.5,      # Duty cycle 2
            'Pload': 1000.0,    # Load power (W)
            'fsw': 100000,      # Switching frequency (Hz)
            'L': 50e-6,         # Transformer inductance (H)
            'R_on': 0.1,        # On-resistance (Ω)
            'C_oss': 100e-12,   # Output capacitance (F)
        }
        
        # Operating limits
        self.limits = {
            'Vdc1': (200, 800),
            'Vdc2': (12, 100),
            'phi': (0, np.pi/2),
            'delta1': (0.1, 0.9),
            'delta2': (0.1, 0.9),
            'Pload': (100, 5000)
        }
    
    def simulate_efficiency(self, params: Dict[str, float]) -> float:
        """Calculate efficiency based on parameters"""
        Vdc1, Vdc2 = params['Vdc1'], params['Vdc2']
        phi, delta1, delta2 = params['phi'], params['delta1'], params['delta2']
        Pload = params['Pload']
        fsw, L, R_on, C_oss = params['fsw'], params['L'], params['R_on'], params['C_oss']
        
        # Calculate transformer current
        I_transformer = Pload / (Vdc1 * delta1)
        
        # Conduction losses
        P_conduction = I_transformer**2 * R_on * (delta1 + delta2)
        
        # Switching losses
        P_switching = 0.5 * C_oss * Vdc1**2 * fsw * (delta1 + delta2)
        
        # Transformer losses (simplified)
        P_transformer = 0.02 * Pload  # 2% of power
        
        # Total losses
        P_total_loss = P_conduction + P_switching + P_transformer
        
        # Efficiency
        efficiency = (Pload / (Pload + P_total_loss)) * 100
        
        return max(0, min(100, efficiency))
    
    def simulate_temperature(self, params: Dict[str, float], ambient_temp: float = 25.0) -> float:
        """Calculate junction temperature based on parameters"""
        efficiency = self.simulate_efficiency(params)
        Pload = params['Pload']
        
        # Power dissipation
        P_dissipated = Pload * (1 - efficiency/100)
        
        # Thermal resistance (simplified model)
        R_th = 0.5  # °C/W
        
        # Temperature rise
        delta_T = P_dissipated * R_th
        
        return ambient_temp + delta_T
    
    def check_zvs_region(self, params: Dict[str, float]) -> Dict[str, bool]:
        """Check if ZVS (Zero Voltage Switching) is possible"""
        Vdc1, Vdc2 = params['Vdc1'], params['Vdc2']
        phi, delta1, delta2 = params['phi'], params['delta1'], params['delta2']
        Pload = params['Pload']
        L = params['L']
        fsw = params['fsw']
        
        # Calculate transformer current
        I_transformer = Pload / (Vdc1 * delta1)
        
        # ZVS conditions (simplified)
        # Leg 1 ZVS: sufficient current to discharge Coss
        zvs_leg1 = I_transformer > 0.5  # Simplified threshold
        
        # Leg 2 ZVS: phase shift and current conditions
        zvs_leg2 = (phi > 0.1) and (I_transformer > 0.3)
        
        return {
            'leg1_zvs': zvs_leg1,
            'leg2_zvs': zvs_leg2,
            'overall_zvs': zvs_leg1 and zvs_leg2
        }
    
    def calculate_losses(self, params: Dict[str, float]) -> Dict[str, float]:
        """Calculate detailed power losses"""
        Vdc1, Vdc2 = params['Vdc1'], params['Vdc2']
        phi, delta1, delta2 = params['phi'], params['delta1'], params['delta2']
        Pload = params['Pload']
        fsw, L, R_on, C_oss = params['fsw'], params['L'], params['R_on'], params['C_oss']
        
        # Transformer current
        I_transformer = Pload / (Vdc1 * delta1)
        
        # Conduction losses
        P_conduction = I_transformer**2 * R_on * (delta1 + delta2)
        
        # Switching losses
        P_switching = 0.5 * C_oss * Vdc1**2 * fsw * (delta1 + delta2)
        
        # Transformer losses
        P_transformer = 0.02 * Pload
        
        # Total losses
        P_total_loss = P_conduction + P_switching + P_transformer
        
        return {
            'conduction_loss': P_conduction,
            'switching_loss': P_switching,
            'transformer_loss': P_transformer,
            'total_loss': P_total_loss
        }
    
    def run_simulation(self, params: Dict[str, float]) -> Dict[str, any]:
        """Run complete simulation with given parameters"""
        # Validate parameters
        for param, value in params.items():
            if param in self.limits:
                min_val, max_val = self.limits[param]
                if value < min_val or value > max_val:
                    st.warning(f"{param} value {value} is outside safe range [{min_val}, {max_val}]")
        
        # Run simulations
        efficiency = self.simulate_efficiency(params)
        temperature = self.simulate_temperature(params)
        zvs_status = self.check_zvs_region(params)
        losses = self.calculate_losses(params)
        
        return {
            'efficiency': efficiency,
            'temperature': temperature,
            'zvs_status': zvs_status,
            'losses': losses,
            'parameters': params
        }
    
    def generate_zvs_heatmap(self, param1: str, param2: str, 
                            param1_range: Tuple[float, float, int] = None,
                            param2_range: Tuple[float, float, int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate ZVS heatmap for two parameters"""
        if param1_range is None:
            param1_range = self.limits[param1]
        if param2_range is None:
            param2_range = self.limits[param2]
        
        param1_vals = np.linspace(param1_range[0], param1_range[1], param1_range[2])
        param2_vals = np.linspace(param2_range[0], param2_range[1], param2_range[2])
        
        # Use default parameters
        base_params = self.default_params.copy()
        
        # Create meshgrid
        X, Y = np.meshgrid(param1_vals, param2_vals)
        Z = np.zeros_like(X)
        
        # Calculate ZVS status for each combination
        for i in range(len(param2_vals)):
            for j in range(len(param1_vals)):
                test_params = base_params.copy()
                test_params[param1] = param1_vals[j]
                test_params[param2] = param2_vals[i]
                
                zvs_status = self.check_zvs_region(test_params)
                Z[i, j] = 1 if zvs_status['overall_zvs'] else 0
        
        return X, Y, Z
    
    def get_parameter_impact(self, base_params: Dict[str, float], 
                           param_name: str, variation: float = 0.1) -> Dict[str, Dict[str, float]]:
        """Calculate impact of parameter variation on key metrics"""
        base_sim = self.run_simulation(base_params)
        
        # Vary the parameter
        varied_params = base_params.copy()
        varied_params[param_name] *= (1 + variation)
        
        varied_sim = self.run_simulation(varied_params)
        
        # Calculate deltas
        delta_efficiency = varied_sim['efficiency'] - base_sim['efficiency']
        delta_temperature = varied_sim['temperature'] - base_sim['temperature']
        
        return {
            'base': {
                'efficiency': base_sim['efficiency'],
                'temperature': base_sim['temperature']
            },
            'varied': {
                'efficiency': varied_sim['efficiency'],
                'temperature': varied_sim['temperature']
            },
            'delta': {
                'efficiency': delta_efficiency,
                'temperature': delta_temperature
            }
        }
