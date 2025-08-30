import pandas as pd
import numpy as np
import time
import os
from datetime import datetime

# Import advanced modules
from forecaster import AdvancedMicroGridForecaster
from optimizer import AdvancedMicroGridOptimizer
from modelica_interface import CSVModelicaInterface

class AdvancedMicroGridDigitalTwin:
    def __init__(self):
        self.forecaster = AdvancedMicroGridForecaster()
        self.optimizer = AdvancedMicroGridOptimizer()
        
        # Initialize simulation
        models_dir = "models"
        model_path = os.path.join(models_dir, "microgrid.mo")
        os.makedirs(models_dir, exist_ok=True)
        
        self.simulator = CSVModelicaInterface(model_path)
        
        # Initialize data storage
        self.historical_data = pd.DataFrame(columns=[
            'timestamp', 'battery_soc', 'solar_power', 'load_power', 
            'grid_power', 'battery_setpoint', 'generator_setpoint', 
            'total_cost', 'carbon_emissions', 'reliability_status'
        ])
        
        self.current_state = {
            'battery_soc': 50,
            'solar_power': 0,
            'load_power': 800,
            'grid_power': 0,
            'total_cost': 0,
            'carbon_emissions': 0,
            'reliability_status': 'Normal'
        }
        
        self.config = {
            'carbon_cost': 0.02,
            'battery_min_soc': 20,
            'battery_max_soc': 95,
            'grid_available': True
        }
    
    def update_config(self, **kwargs):
        """Update configuration parameters"""
        self.config.update(kwargs)
        self.optimizer.carbon_cost = self.config['carbon_cost']
        self.optimizer.battery_min_soc = self.config['battery_min_soc']
        self.optimizer.battery_max_soc = self.config['battery_max_soc']
    
    def run_optimization_cycle(self):
        """Run one complete optimization cycle with advanced features"""
        # Get forecasts
        solar_forecast, load_forecast = self.forecaster.forecast()
        
        # Generate price forecast (time-of-use pricing)
        hours = list(range(24))
        price_forecast = [0.12 if h < 8 or h >= 22 else 
                          0.15 if h < 18 else 
                          0.20 for h in hours]
        
        # Run advanced optimization
        try:
            battery_schedule, generator_schedule = self.optimizer.multi_objective_optimization(
                solar_forecast, load_forecast, 
                self.current_state['battery_soc'], 
                price_forecast,
                carbon_cost=self.config['carbon_cost']
            )
            
            # Extract immediate setpoints
            battery_setpoint = battery_schedule[0] * 1000  # Convert kW to W
            generator_setpoint = generator_schedule[0] * 1000  # Convert kW to W
            
        except Exception as e:
            print(f"Optimization failed: {e}")
            # Fallback to real-time control
            forecast_data = {
                'solar': solar_forecast,
                'load': load_forecast,
                'prices': price_forecast
            }
            battery_setpoint, generator_setpoint = self.optimizer.real_time_control(
                self.current_state, forecast_data
            )
            battery_setpoint *= 1000
            generator_setpoint *= 1000
        
        # Apply grid outage if configured
        if not self.config['grid_available']:
            # Force island mode - no grid connection
            pass
        
        # Apply setpoints to simulator
        new_state = self.simulator.simulate_step(battery_setpoint, generator_setpoint)
        
        # Calculate carbon emissions
        carbon_emissions = self.calculate_emissions(new_state)
        
        # Check system reliability
        reliability_status = self.check_reliability(new_state)
        
        # Update state with additional metrics
        new_state.update({
            'carbon_emissions': carbon_emissions,
            'reliability_status': reliability_status
        })
        
        # Store results
        new_record = {
            'timestamp': pd.Timestamp.now(),
            'battery_soc': new_state['battery_soc'],
            'solar_power': new_state['solar_power'],
            'load_power': new_state['load_power'],
            'grid_power': new_state['grid_power'],
            'battery_setpoint': battery_setpoint,
            'generator_setpoint': generator_setpoint,
            'total_cost': new_state['total_cost'],
            'carbon_emissions': carbon_emissions,
            'reliability_status': reliability_status
        }
        
        new_df = pd.DataFrame([new_record])
        self.historical_data = pd.concat([self.historical_data, new_df], ignore_index=True)
        self.current_state = new_state
        
        return new_state, battery_setpoint, generator_setpoint
    
    def calculate_emissions(self, state):
        """Calculate carbon emissions for the current state"""
        grid_emissions = max(0, state['grid_power']) * self.optimizer.carbon_intensity_grid / 1000
        generator_emissions = state['generator_setpoint'] * self.optimizer.carbon_intensity_generator / 1000
        return grid_emissions + generator_emissions
    
    def check_reliability(self, state):
        """Check system reliability status"""
        if state['grid_power'] > 5000:  # High grid dependency
            return 'Grid Dependent'
        elif state['battery_soc'] < self.config['battery_min_soc'] + 5:  # Low battery
            return 'Low Reserve'
        elif state['generator_setpoint'] > 0:  # Using generator
            return 'Generator Active'
        else:
            return 'Normal'
    
    def inject_disturbance(self, solar_reduction=0, load_increase=0, grid_outage=False):
        """Inject various types of disturbances"""
        print(f"Injecting disturbance: Solar -{solar_reduction}%, Load +{load_increase}%, Grid Outage: {grid_outage}")
        
        # Modify current state to simulate disturbances
        self.simulator.current_state['solar_power'] *= (1 - solar_reduction / 100)
        self.simulator.current_state['load_power'] *= (1 + load_increase / 100)
        self.config['grid_available'] = not grid_outage
        
        if grid_outage:
            self.current_state['reliability_status'] = 'Island Mode'
    
    def get_system_health(self):
        """Get overall system health assessment"""
        recent_data = self.historical_data.tail(10)
        
        if recent_data.empty:
            return "No data available"
        
        avg_cost = recent_data['total_cost'].mean()
        avg_emissions = recent_data['carbon_emissions'].mean()
        reliability = recent_data['reliability_status'].value_counts().idxmax()
        
        if avg_cost > 1.0 or avg_emissions > 2.0 or reliability != 'Normal':
            return "Needs Attention"
        else:
            return "Healthy"