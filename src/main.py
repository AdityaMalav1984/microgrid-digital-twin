import time
import pandas as pd
from forecaster import MicroGridForecaster
from optimizer import MicroGridOptimizer
from modelica_interface import CSVModelicaInterface  # Use CSVModelicaInterface for demo

class MicroGridDigitalTwin:
    def __init__(self):
        self.forecaster = MicroGridForecaster()
        self.optimizer = MicroGridOptimizer()
        self.simulator = CSVModelicaInterface("models/microgrid.mo")
        
        # Initialize data storage
        self.historical_data = pd.DataFrame(columns=[
            'timestamp', 'battery_soc', 'solar_power', 'load_power', 
            'grid_power', 'battery_setpoint', 'generator_setpoint', 'total_cost'
        ])
        
        self.current_state = {
            'battery_soc': 50,
            'solar_power': 0,
            'load_power': 800,
            'grid_power': 0,
            'total_cost': 0
        }
    
    def run_optimization_cycle(self):
        """Run one complete optimization cycle"""
        # Get current state from simulator
        current_state = self.simulator.current_state
        
        # Create forecasts
        solar_forecast = self.forecaster.forecast_solar(None)
        load_forecast = self.forecaster.forecast_load(None)
        
        # Generate electricity price forecast (simple time-of-day)
        hours = list(range(24))
        price_forecast = [0.12 if h < 8 or h >= 22 else 
                          0.15 if h < 18 else 
                          0.20 for h in hours]
        
        # Run optimization for the next 24 hours
        try:
            battery_schedule, generator_schedule = self.optimizer.optimize_schedule(
                solar_forecast, load_forecast, current_state['battery_soc'], 
                price_forecast
            )
            
            # Extract immediate setpoints
            battery_setpoint = battery_schedule[0] * 1000  # Convert kW to W
            generator_setpoint = generator_schedule[0] * 1000  # Convert kW to W
            
        except ValueError:
            # Fallback to rules-based control if optimization fails
            battery_setpoint, generator_setpoint = self.optimizer.get_immediate_setpoints(
                current_state, None
            )
        
        # Apply setpoints to simulator
        new_state = self.simulator.simulate_step(battery_setpoint, generator_setpoint)
        
        # Store results
        new_record = {
            'timestamp': pd.Timestamp.now(),
            'battery_soc': new_state['battery_soc'],
            'solar_power': new_state['solar_power'],
            'load_power': new_state['load_power'],
            'grid_power': new_state['grid_power'],
            'battery_setpoint': battery_setpoint,
            'generator_setpoint': generator_setpoint,
            'total_cost': new_state['total_cost']
        }
        
        new_df = pd.DataFrame([new_record])
        self.historical_data = pd.concat([self.historical_data, new_df], ignore_index=True)
        self.current_state = new_state
        
        return new_state, battery_setpoint, generator_setpoint
    
    def run_continuous(self, interval=300):
        """Run the digital twin in continuous mode"""
        print("Starting MicroGrid Digital Twin...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                start_time = time.time()
                
                state, battery_sp, gen_sp = self.run_optimization_cycle()
                
                print(f"Time: {pd.Timestamp.now()}")
                print(f"Solar: {state['solar_power']:.1f}W, Load: {state['load_power']:.1f}W")
                print(f"Battery: {state['battery_soc']:.1f}%, Setpoint: {battery_sp:.1f}W")
                print(f"Generator: {gen_sp:.1f}W, Grid: {state['grid_power']:.1f}W")
                print(f"Total Cost: ${state['total_cost']:.4f}")
                print("-" * 40)
                
                # Sleep until next cycle
                elapsed = time.time() - start_time
                time.sleep(max(0, interval - elapsed))
                
        except KeyboardInterrupt:
            print("Stopping MicroGrid Digital Twin")
            
    def inject_disturbance(self, solar_reduction=0, load_increase=0):
        """Inject a disturbance into the simulation"""
        print(f"Injecting disturbance: Solar -{solar_reduction}%, Load +{load_increase}%")
        
        # Modify the current state to simulate a disturbance
        self.simulator.current_state['solar_power'] *= (1 - solar_reduction / 100)
        self.simulator.current_state['load_power'] *= (1 + load_increase / 100)

if __name__ == "__main__":
    digital_twin = MicroGridDigitalTwin()
    digital_twin.run_continuous()