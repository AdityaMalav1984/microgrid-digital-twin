import numpy as np
from scipy.optimize import minimize, Bounds, LinearConstraint
import pandas as pd

class AdvancedMicroGridOptimizer:
    def __init__(self):
        self.battery_min_soc = 20  # %
        self.battery_max_soc = 95  # %
        self.battery_capacity = 10  # kWh
        self.battery_max_power = 5  # kW charge/discharge rate
        self.generator_max_power = 8  # kW
        self.generator_min_power = 1  # kW (minimum stable generation)
        self.generator_efficiency = 0.35
        self.fuel_cost = 0.25  # $/kWh
        self.grid_export_price = 0.08  # $/kWh (feed-in tariff)
        self.carbon_intensity_grid = 0.5  # kgCO2/kWh
        self.carbon_intensity_generator = 0.7  # kgCO2/kWh
        
    def multi_objective_optimization(self, solar_forecast, load_forecast, current_soc, 
                                   electricity_prices, carbon_cost=0.02):
        """
        Multi-objective optimization: minimize cost AND carbon emissions
        """
        n_periods = len(solar_forecast)
        
        # Decision variables: [battery_power, generator_power] for each period
        # battery_power > 0: discharging, < 0: charging
        n_vars = 2 * n_periods
        
        # Objective function: weighted sum of cost and emissions
        def objective(x):
            cost = 0
            emissions = 0
            
            for i in range(n_periods):
                battery_power = x[i]
                generator_power = x[i + n_periods]
                
                # Grid power balance
                grid_power = load_forecast[i] - solar_forecast[i] - battery_power - generator_power
                
                # Cost calculation
                if grid_power > 0:  # Importing from grid
                    cost += grid_power * electricity_prices[i] / 1000  # Convert to $
                else:  # Exporting to grid
                    cost += grid_power * self.grid_export_price / 1000  # Negative cost
                
                # Generator fuel cost
                cost += (generator_power * self.fuel_cost / self.generator_efficiency) / 1000
                
                # Carbon emissions
                emissions += max(0, grid_power) * self.carbon_intensity_grid / 1000
                emissions += generator_power * self.carbon_intensity_generator / 1000
            
            # Weighted objective (cost + carbon_cost * emissions)
            return cost + carbon_cost * emissions
        
        # Constraints
        constraints = []
        
        # Power balance constraint (handled in objective)
        
        # Battery SOC constraints
        soc_trajectory = [current_soc / 100 * self.battery_capacity]  # Start with current SOC in kWh
        
        for i in range(n_periods):
            next_soc = soc_trajectory[-1] - x[i] / 4  # 15-minute time step assumption
            soc_trajectory.append(next_soc)
        
        # Bounds
        bounds = Bounds(
            [-self.battery_max_power] * n_periods + [0] * n_periods,  # Lower bounds
            [self.battery_max_power] * n_periods + [self.generator_max_power] * n_periods  # Upper bounds
        )
        
        # SOC constraints (20%-95%)
        def soc_constraint(x):
            soc = current_soc / 100 * self.battery_capacity
            constraints = []
            
            for i in range(n_periods):
                soc -= x[i] / 4  # 15-minute time step
                constraints.append(soc - self.battery_min_soc/100 * self.battery_capacity)  # Min SOC
                constraints.append(self.battery_max_soc/100 * self.battery_capacity - soc)  # Max SOC
            
            return np.array(constraints)
        
        # Generator minimum power constraint
        def generator_constraint(x):
            return x[n_periods:] - self.generator_min_power  # Generator power >= min_power
        
        constraints = [
            {'type': 'ineq', 'fun': soc_constraint},
            {'type': 'ineq', 'fun': generator_constraint}
        ]
        
        # Initial guess
        x0 = np.zeros(n_vars)
        
        # Solve optimization
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, 
                         constraints=constraints, options={'maxiter': 1000})
        
        if result.success:
            battery_power = result.x[:n_periods]
            generator_power = result.x[n_periods:]
            return battery_power, generator_power
        else:
            # Fallback to simple optimization
            return self.simple_optimization(solar_forecast, load_forecast, current_soc, electricity_prices)
    
    def simple_optimization(self, solar_forecast, load_forecast, current_soc, electricity_prices):
        """Fallback optimization method"""
        # Simplified optimization logic (similar to previous version)
        n_periods = len(solar_forecast)
        battery_power = np.zeros(n_periods)
        generator_power = np.zeros(n_periods)
        
        for i in range(n_periods):
            imbalance = load_forecast[i] - solar_forecast[i]
            
            if imbalance > 0:  # More load than generation
                # Use battery first
                available_battery = min(self.battery_max_power, 
                                      (current_soc/100 * self.battery_capacity - 
                                       self.battery_min_soc/100 * self.battery_capacity) * 4)
                battery_discharge = min(imbalance, available_battery)
                battery_power[i] = battery_discharge
                imbalance -= battery_discharge
                
                # Use generator for remaining imbalance
                if imbalance > 0:
                    generator_power[i] = min(imbalance, self.generator_max_power)
            
            else:  # Excess generation
                # Charge battery
                available_charging = min(self.battery_max_power,
                                       (self.battery_max_soc/100 * self.battery_capacity - 
                                        current_soc/100 * self.battery_capacity) * 4)
                battery_charge = min(-imbalance, available_charging)
                battery_power[i] = -battery_charge
            
            # Update SOC for next time step
            current_soc -= battery_power[i] / self.battery_capacity * 100 / 4
        
        return battery_power, generator_power
    
    def real_time_control(self, current_state, forecast):
        """Real-time model predictive control"""
        # Extract current conditions
        current_soc = current_state['battery_soc']
        current_solar = current_state['solar_power']
        current_load = current_state['load_power']
        
        # Get short-term forecast (next 4 hours)
        short_solar = forecast['solar'][:4]
        short_load = forecast['load'][:4]
        short_prices = forecast['prices'][:4]
        
        # Run optimization for short horizon
        battery_power, generator_power = self.multi_objective_optimization(
            short_solar, short_load, current_soc, short_prices
        )
        
        # Return first step actions
        return battery_power[0], generator_power[0]