import pandas as pd
import numpy as np
import os
import time

class CSVModelicaInterface:
    def __init__(self, model_path):
        self.model_path = model_path
        self.current_state = {
            'battery_soc': 50,
            'solar_power': 0,
            'load_power': 800,
            'grid_power': 0,
            'total_cost_inr': 0  # Changed to INR
        }
    
    def simulate_step(self, battery_setpoint, generator_setpoint, step_size=300):
        """
        Simulate one time step with given setpoints
        Simplified version that doesn't require full Modelica integration
        """
        # Update battery SOC
        battery_energy = self.current_state['battery_soc'] / 100 * 10  # kWh
        battery_energy += battery_setpoint * step_size / 3600 / 1000  # kWh
        
        # Apply constraints
        battery_energy = max(0, min(10000, battery_energy))
        new_soc = battery_energy / 10  # %
        
        # Simple solar pattern based on time of day
        from datetime import datetime
        hour = datetime.now().hour
        solar_power = 3000 * np.sin(np.pi * (hour + 6) / 15)
        solar_power = max(0, solar_power)
        
        # Simple load pattern
        load_power = 800 + 2000 * np.exp(-0.5 * ((hour - 19) / 3)**2)
        
        # Calculate grid power
        grid_power = load_power - solar_power - battery_setpoint - generator_setpoint
        
        # Calculate cost in INR - typical Indian electricity rates
        if 22 <= hour or hour < 6:  # Off-peak: 10 PM - 6 AM
            price = 4.0  # ₹/kWh
        elif 18 <= hour < 22:  # Peak: 6 PM - 10 PM
            price = 8.0  # ₹/kWh
        else:  # Normal: 6 AM - 6 PM
            price = 6.0  # ₹/kWh
            
        cost_increment = (max(0, grid_power) * price + 
                         generator_setpoint * 20.0 / 0.35) * step_size / 3600 / 1000  # Fuel cost 20 ₹/kWh
        
        # Update state
        self.current_state = {
            'battery_soc': new_soc,
            'solar_power': solar_power,
            'load_power': load_power,
            'grid_power': grid_power,
            'total_cost_inr': self.current_state['total_cost_inr'] + cost_increment
        }
        
        return self.current_state