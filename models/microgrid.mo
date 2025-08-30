model MicroGrid
  // Inputs from Python controller
  input Real battery_setpoint "Battery power setpoint (W)";
  input Real generator_setpoint "Generator power setpoint (W)";
  
  // Outputs to Python controller
  output Real battery_soc "Battery state of charge (%)";
  output Real solar_power "Solar power generation (W)";
  output Real load_power "Household demand (W)";
  output Real grid_power "Grid power (W) - positive=import";
  output Real total_cost "Operating cost ($)";
  
  // Internal components
  Modelica.Blocks.Sources.CombiTimeTable solar_data(
    table=[0,0; 6,0; 7,500; 12,4000; 18,1000; 20,0; 24,0],
    timeScale=3600) "Solar generation profile";
  
  Modelica.Blocks.Sources.CombiTimeTable load_data(
    table=[0,800; 6,600; 8,400; 12,800; 17,3500; 22,1200; 24,800],
    timeScale=3600) "Load profile";
  
  // Battery model (simplified)
  parameter Real battery_capacity = 10000 "Wh";
  Real battery_energy(start=5000) "Wh";
  
  // Grid price signal
  Modelica.Blocks.Sources.CombiTimeTable price_data(
    table=[0,0.12; 8,0.15; 18,0.20; 22,0.15; 24,0.12],
    timeScale=3600) "Electricity price $/kWh";
  
  // Generator model
  parameter Real generator_efficiency = 0.35;
  parameter Real fuel_cost = 0.25 "$/kWh";
  
equation
  // Battery dynamics
  der(battery_energy) = battery_setpoint;
  battery_soc = (battery_energy / battery_capacity) * 100;
  
  // Power balance equation
  grid_power = load_power - solar_power - battery_setpoint - generator_setpoint;
  
  // Cost calculation
  total_cost = (grid_power * (if grid_power > 0 then price_data.y[1]/1000 else 0.05)) / 1000 + 
               (generator_setpoint * fuel_cost / generator_efficiency) / 1000;
  
  // Connect data sources
  solar_power = solar_data.y[1];
  load_power = load_data.y[1];
  
  // Constraints
  assert(battery_energy >= 0 and battery_energy <= battery_capacity, "Battery limits violated");
  assert(generator_setpoint >= 0, "Generator cannot absorb power");

end MicroGrid;