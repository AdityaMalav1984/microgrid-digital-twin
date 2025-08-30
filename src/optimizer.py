import numpy as np
from scipy.optimize import linprog

class MicroGridOptimizer:
    def __init__(self):
        self.battery_min_soc = 20  # %
        self.battery_max_soc = 95  # %
        self.battery_capacity = 10  # kWh
        self.generator_max_power = 5  # kW
        self.time_step = 1  # hours
        
    def optimize_schedule(self, solar_forecast, load_forecast, current_soc, 
                          electricity_prices, fuel_cost=0.25):
        """
        Optimize battery and generator operation for the next 24 hours
        Returns optimal power setpoints for each hour
        """
        n_periods = len(solar_forecast)
        
        # Decision variables: [battery_charge, battery_discharge, generator] for each period
        n_vars = 3 * n_periods
        
        # Objective function: minimize cost
        # Cost coefficients: [grid_import * price, generator * fuel_cost, 0 for battery]
        c = np.concatenate([
            electricity_prices,  # Cost for grid import
            np.full(n_periods, fuel_cost),  # Cost for generator
            np.zeros(n_periods)  # Battery operation has no direct cost
        ])
        
        # Constraints: power balance for each period
        A_eq = np.zeros((n_periods, n_vars))
        for i in range(n_periods):
            A_eq[i, i] = 1  # Battery discharge
            A_eq[i, i + n_periods] = -1  # Battery charge
            A_eq[i, i + 2*n_periods] = 1  # Generator
            
        # Power balance: solar + battery_discharge + generator + grid_import = load + battery_charge
        b_eq = load_forecast - solar_forecast
        
        # Battery state of charge constraints
        A_ineq = np.zeros((2*(n_periods-1), n_vars))
        b_ineq = np.zeros(2*(n_periods-1))
        
        # Build battery SOC constraints
        for i in range(1, n_periods):
            # SOC lower bound constraint
            A_ineq[i-1, :i] = -1  # Cumulative charging
            A_ineq[i-1, n_periods:n_periods+i] = 1  # Cumulative discharging
            b_ineq[i-1] = current_soc/100 * self.battery_capacity - self.battery_min_soc/100 * self.battery_capacity
            
            # SOC upper bound constraint
            A_ineq[i-1 + n_periods-1, :i] = 1  # Cumulative charging
            A_ineq[i-1 + n_periods-1, n_periods:n_periods+i] = -1  # Cumulative discharging
            b_ineq[i-1 + n_periods-1] = self.battery_max_soc/100 * self.battery_capacity - current_soc/100 * self.battery_capacity
        
        # Generator capacity constraints
        for i in range(n_periods):
            A_ineq = np.vstack([A_ineq, np.zeros(n_vars)])
            A_ineq[-1, i + 2*n_periods] = 1
            b_ineq = np.append(b_ineq, self.generator_max_power)
            
            A_ineq = np.vstack([A_ineq, np.zeros(n_vars)])
            A_ineq[-1, i + 2*n_periods] = -1
            b_ineq = np.append(b_ineq, 0)
        
        # Battery charge/discharge cannot happen simultaneously
        for i in range(n_periods):
            A_ineq = np.vstack([A_ineq, np.zeros(n_vars)])
            A_ineq[-1, i] = 1
            A_ineq[-1, i + n_periods] = 1
            b_ineq = np.append(b_ineq, self.battery_capacity/4)  # Max charge/discharge rate
        
        # Solve the linear programming problem
        bounds = [(0, None) for _ in range(n_vars)]
        result = linprog(c, A_ub=A_ineq, b_ub=b_ineq, A_eq=A_eq, b_eq=b_eq, bounds=bounds)
        
        if result.success:
            # Extract results
            battery_discharge = result.x[:n_periods]
            battery_charge = result.x[n_periods:2*n_periods]
            generator = result.x[2*n_periods:3*n_periods]
            
            # Net battery power (negative when charging, positive when discharging)
            battery_power = battery_discharge - battery_charge
            
            return battery_power, generator
        else:
            raise ValueError("Optimization failed: " + result.message)
    
    def get_immediate_setpoints(self, current_conditions, forecast):
        """
        Get setpoints for the immediate next time step
        Simplified version for real-time control
        """
        current_soc = current_conditions['battery_soc']
        current_solar = current_conditions['solar_power']
        current_load = current_conditions['load_power']
        
        # Calculate power imbalance
        imbalance = current_load - current_solar
        
        # Simple rules-based controller for demonstration
        if imbalance > 0:  # More load than generation
            # Use battery if available
            if current_soc > self.battery_min_soc + 5:  # Keep some reserve
                battery_power = min(imbalance, self.battery_capacity * 0.2)  # Max discharge rate
                imbalance -= battery_power
            else:
                battery_power = 0
                
            # Use generator for remaining imbalance
            generator_power = min(imbalance, self.generator_max_power)
        else:  # Excess generation
            # Charge battery if not full
            if current_soc < self.battery_max_soc - 5:  # Leave some headroom
                battery_power = -min(-imbalance, self.battery_capacity * 0.2)  # Max charge rate
            else:
                battery_power = 0
            generator_power = 0
        
        return battery_power, generator_power
    