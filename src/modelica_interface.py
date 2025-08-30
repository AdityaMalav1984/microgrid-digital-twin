import subprocess
import pandas as pd
import numpy as np
import os
import time
from OMPython import OMCSession

class ModelicaSimulator:
    def __init__(self, model_path):
        self.model_path = model_path
        self.omc = OMCSession()
        self.omc.sendExpression("loadModel(Modelica)")
        self.load_model()
        
    def load_model(self):
        """Load the MicroGrid model"""
        result = self.omc.sendExpression(f'loadFile("{self.model_path}")')
        if not result:
            raise ValueError(f"Failed to load model from {self.model_path}")
        
        result = self.omc.sendExpression('getErrorString()')
        if result:
            print(f"Model loading warnings: {result}")
    
    def simulate_step(self, battery_setpoint, generator_setpoint, initial_state=None, 
                     step_size=300, stop_time=300):
        """
        Simulate one time step with given setpoints
        Returns the final state of the simulation
        """
        # Set initial conditions if provided
        if initial_state:
            initial_conditions = []
            for key, value in initial_state.items():
                initial_conditions.append(f"-override {key}={value}")
            initial_conditions_str = ",".join(initial_conditions)
        else:
            initial_conditions_str = ""
        
        # Set inputs
        input_overrides = f"battery_setpoint={battery_setpoint},generator_setpoint={generator_setpoint}"
        
        # Run simulation
        result = self.omc.sendExpression(
            f'simulate(MicroGrid, startTime=0, stopTime={stop_time}, '
            f'stepSize={step_size}, numberOfIntervals=0, '
            f'outputFormat="csv", '
            f'override={input_overrides}'
            f'{"," + initial_conditions_str if initial_conditions_str else ""})'
        )
        
        # Check for errors
        error = self.omc.sendExpression('getErrorString()')
        if error:
            print(f"Simulation error: {error}")
        
        # Read results
        result_file = "MicroGrid_res.csv"
        if os.path.exists(result_file):
            results = pd.read_csv(result_file)
            final_state = results.iloc[-1].to_dict()
            os.remove(result_file)  # Clean up
            return final_state
        else:
            raise FileNotFoundError("Simulation results file not found")
    
    def get_current_state(self):
        """Get the current state of the model (for continuous simulation)"""
        # This would be implemented for a proper co-simulation
        # For now, we'll use simulate_step with a very short duration
        pass

# Alternative approach using CSV file exchange
class CSVModelicaInterface:
    def __init__(self, model_path):
        self.model_path = model_path
        self.current_state = {
            'battery_soc': 50,
            'solar_power': 0,
            'load_power': 800,
            'grid_power': 0,
            'total_cost': 0
        }
    
    def simulate_step(self, battery_setpoint, generator_setpoint, step_size=300):
        """
        Simulate one time step with given setpoints
        Simplified version that doesn't require full Modelica integration
        """
        # Simple simulation logic for demonstration
        # In a real implementation, this would call the actual Modelica model
        
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
        
        # Calculate cost
        if 8 <= hour < 18:
            price = 0.15
        elif 18 <= hour < 22:
            price = 0.20
        else:
            price = 0.12
            
        cost_increment = (max(0, grid_power) * price + 
                         generator_setpoint * 0.25 / 0.35) * step_size / 3600 / 1000
        
        # Update state
        self.current_state = {
            'battery_soc': new_soc,
            'solar_power': solar_power,
            'load_power': load_power,
            'grid_power': grid_power,
            'total_cost': self.current_state['total_cost'] + cost_increment
        }
        
        return self.current_state