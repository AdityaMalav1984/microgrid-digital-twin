import sys
import os
import time
import pandas as pd

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import AdvancedMicroGridDigitalTwin

def run_demo():
    print("=== Advanced MicroGrid Digital Twin Demo ===")
    print("This demo shows advanced features of the digital twin with INR currency")
    print()
    
    digital_twin = AdvancedMicroGridDigitalTwin()
    
    # Phase 1: Normal operation with forecasting
    print("Phase 1: Normal operation with ML forecasting")
    for i in range(5):
        state, battery_sp, gen_sp = digital_twin.run_optimization_cycle()
        health = digital_twin.get_system_health()
        print(f"Cycle {i+1}: SOC={state['battery_soc']:.1f}%, Cost=₹{state['total_cost_inr']:.2f}, "
              f"CO₂={state['carbon_emissions']:.3f}kg, Status: {state['reliability_status']}, "
              f"Health: {health}")
        time.sleep(1)
    
    # Phase 2: Cloud cover disturbance
    print("\nPhase 2: Cloud cover (70% solar reduction)")
    digital_twin.inject_disturbance(solar_reduction=70, load_increase=0)
    
    for i in range(5):
        state, battery_sp, gen_sp = digital_twin.run_optimization_cycle()
        health = digital_twin.get_system_health()
        print(f"Cycle {i+1}: Solar={state['solar_power']:.1f}W, Battery={battery_sp:.1f}W, "
              f"Generator={gen_sp:.1f}W, Cost=₹{state['total_cost_inr']:.2f}, "
              f"Status: {state['reliability_status']}")
        time.sleep(1)
    
    # Phase 3: Grid outage
    print("\nPhase 3: Grid outage with high load")
    digital_twin.inject_disturbance(solar_reduction=0, load_increase=40, grid_outage=True)
    
    for i in range(5):
        state, battery_sp, gen_sp = digital_twin.run_optimization_cycle()
        health = digital_twin.get_system_health()
        print(f"Cycle {i+1}: Load={state['load_power']:.1f}W, Grid={state['grid_power']:.1f}W, "
              f"Cost=₹{state['total_cost_inr']:.2f}, Status: {state['reliability_status']}, "
              f"Health: {health}")
        time.sleep(1)
    
    # Phase 4: Carbon-aware mode
    print("\nPhase 4: Carbon-aware operation (high carbon cost)")
    digital_twin.update_config(carbon_cost=5.0)  # High carbon cost in ₹/kgCO₂
    
    for i in range(3):
        state, battery_sp, gen_sp = digital_twin.run_optimization_cycle()
        health = digital_twin.get_system_health()
        print(f"Cycle {i+1}: CO₂={state['carbon_emissions']:.3f}kg, Cost=₹{state['total_cost_inr']:.2f}, "
              f"Status: {state['reliability_status']}")
        time.sleep(1)
    
    print("\nDemo completed!")
    print("Final system health:", digital_twin.get_system_health())
    
    # Show summary statistics in INR
    if not digital_twin.historical_data.empty:
        print("\n=== Summary Statistics ===")
        print(f"Total cost: ₹{digital_twin.historical_data['total_cost_inr'].sum():.2f}")
        print(f"Total carbon emissions: {digital_twin.historical_data['carbon_emissions'].sum():.3f} kgCO₂")
        print("Reliability events:")
        print(digital_twin.historical_data['reliability_status'].value_counts())

if __name__ == "__main__":
    run_demo()