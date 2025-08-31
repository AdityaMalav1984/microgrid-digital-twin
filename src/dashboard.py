import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time

# Create Dash app
app = dash.Dash(__name__)
app.title = "MicroGrid Digital Twin Dashboard"

# Generate sample data for demonstration
def generate_sample_data():
    """Generate sample data for the dashboard"""
    hours = 24
    timestamps = [datetime.now() - timedelta(hours=h) for h in range(hours, 0, -1)]
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'solar_power': [max(0, 3000 * np.sin(np.pi * (h + 6) / 15)) for h in range(hours)],
        'load_power': [800 + 2000 * np.exp(-0.5 * ((h - 19) / 3)**2) for h in range(hours)],
        'grid_power': [500 * np.sin(h/4) for h in range(hours)],
        'battery_soc': [50 + 20 * np.sin(h/6) for h in range(hours)],
        'total_cost_inr': [100 + h * 15 for h in range(hours)],
        'carbon_emissions': [0.5 + 0.1 * np.sin(h/3) for h in range(hours)]
    })

# Initialize sample data
sample_data = generate_sample_data()
current_state = {
    'battery_soc': 65,
    'solar_power': 2500,
    'load_power': 1800,
    'grid_power': -300,
    'total_cost_inr': 450,
    'carbon_emissions': 0.8,
    'reliability_status': 'Normal'
}

simulation_data = {
    'running': False,
    'historical_data': sample_data.to_dict('records'),
    'current_state': current_state
}

# Layout with advanced controls
app.layout = html.Div([
    html.H1("MicroGrid Digital Twin Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # Control Panel
    html.Div([
        html.Div([
            html.H3("Control Panel", style={'marginBottom': '10px'}),
            
            html.Button('Start/Stop Simulation', id='start-button', n_clicks=0,
                       style={'backgroundColor': '#27ae60', 'color': 'white', 'margin': '5px'}),
            
            html.Button('Reset Simulation', id='reset-button', n_clicks=0,
                       style={'backgroundColor': '#e74c3c', 'color': 'white', 'margin': '5px'}),
            
            dcc.Interval(id='interval-component', interval=2000, n_intervals=0, disabled=True),
            
        ], style={'padding': '15px', 'backgroundColor': '#ecf0f1', 'borderRadius': '5px', 'marginBottom': '20px'}),
        
        # Configuration Panel
        html.Div([
            html.H3("Configuration", style={'marginBottom': '10px'}),
            
            html.Label("Battery Min SOC (%):"),
            dcc.Slider(id='soc-min-slider', min=10, max=40, step=5, value=20,
                      marks={i: str(i) for i in range(10, 41, 10)}),
            
            html.Label("Battery Max SOC (%):"),
            dcc.Slider(id='soc-max-slider', min=80, max=100, step=5, value=95,
                      marks={i: str(i) for i in range(80, 101, 10)}),
            
        ], style={'padding': '15px', 'backgroundColor': '#ecf0f1', 'borderRadius': '5px', 'marginBottom': '20px'}),
        
        # Disturbance Panel
        html.Div([
            html.H3("Inject Disturbance", style={'marginBottom': '10px'}),
            
            html.Label("Solar Reduction (%):"),
            dcc.Slider(id='solar-slider', min=0, max=100, step=5, value=0,
                      marks={i: f'{i}%' for i in range(0, 101, 20)}),
            
            html.Label("Load Increase (%):"),
            dcc.Slider(id='load-slider', min=0, max=100, step=5, value=0,
                      marks={i: f'{i}%' for i in range(0, 101, 20)}),
            
            html.Button('Apply Disturbance', id='disturbance-button', n_clicks=0,
                       style={'backgroundColor': '#f39c12', 'color': 'white', 'marginTop': '10px'}),
            
        ], style={'padding': '15px', 'backgroundColor': '#ecf0f1', 'borderRadius': '5px'}),
        
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '20px', 'marginBottom': '20px'}),
    
    # Key Metrics
    html.Div([
        html.Div([
            dcc.Graph(id='battery-gauge', style={'display': 'inline-block', 'width': '24%'}),
            dcc.Graph(id='cost-metric', style={'display': 'inline-block', 'width': '24%'}),
            dcc.Graph(id='solar-metric', style={'display': 'inline-block', 'width': '24%'}),
            dcc.Graph(id='load-metric', style={'display': 'inline-block', 'width': '24%'}),
        ]),
    ], style={'marginBottom': '20px'}),
    
    # Main Visualization
    html.Div([
        dcc.Graph(id='power-graph', style={'height': '500px'}),
    ], style={'marginBottom': '20px'}),
    
    # Cost Visualization
    html.Div([
        dcc.Graph(id='cost-graph', style={'height': '400px'}),
    ]),
    
    # Hidden div for storing data
    dcc.Store(id='simulation-data', data=simulation_data),
])

# Callbacks
@app.callback(
    [Output('interval-component', 'disabled'),
     Output('start-button', 'children'),
     Output('start-button', 'style')],
    [Input('start-button', 'n_clicks')],
    [State('simulation-data', 'data')]
)
def toggle_simulation(n_clicks, data):
    if n_clicks % 2 == 1:
        # Start simulation
        return False, 'Stop Simulation', {'backgroundColor': '#e74c3c', 'color': 'white', 'margin': '5px'}
    else:
        # Stop simulation
        return True, 'Start Simulation', {'backgroundColor': '#27ae60', 'color': 'white', 'margin': '5px'}

@app.callback(
    Output('simulation-data', 'data', allow_duplicate=True),
    [Input('disturbance-button', 'n_clicks')],
    [State('solar-slider', 'value'),
     State('load-slider', 'value'),
     State('simulation-data', 'data')],
    prevent_initial_call=True
)
def inject_disturbance(n_clicks, solar_reduction, load_increase, data):
    if n_clicks > 0:
        # Update current state with disturbance
        current_state = data['current_state']
        current_state['solar_power'] *= (1 - solar_reduction / 100)
        current_state['load_power'] *= (1 + load_increase / 100)
        data['current_state'] = current_state
    return data

@app.callback(
    Output('simulation-data', 'data'),
    [Input('interval-component', 'n_intervals')],
    [State('simulation-data', 'data')]
)
def update_simulation(n_intervals, data):
    if not data['running']:
        return data
    
    # Simulate new data point
    current_state = data['current_state']
    historical_data = pd.DataFrame(data['historical_data'])
    
    # Create new data point with some randomness
    new_timestamp = datetime.now()
    new_solar = max(0, current_state['solar_power'] * np.random.uniform(0.95, 1.05))
    new_load = current_state['load_power'] * np.random.uniform(0.97, 1.03)
    new_soc = max(20, min(95, current_state['battery_soc'] + np.random.uniform(-2, 2)))
    
    # Calculate grid power based on balance
    grid_power = new_load - new_solar
    
    # Update cost (simple model)
    cost_increment = max(0, grid_power) * 6.0 / 1000  # 6 INR/kWh assumption
    new_cost = current_state['total_cost_inr'] + cost_increment
    
    # Create new record
    new_record = {
        'timestamp': new_timestamp,
        'solar_power': new_solar,
        'load_power': new_load,
        'grid_power': grid_power,
        'battery_soc': new_soc,
        'total_cost_inr': new_cost,
        'carbon_emissions': np.random.uniform(0.5, 1.0)
    }
    
    # Update historical data (keep last 48 records)
    if len(historical_data) >= 48:
        historical_data = historical_data.tail(47)
    
    historical_data = pd.concat([historical_data, pd.DataFrame([new_record])], ignore_index=True)
    
    # Update current state
    new_state = {
        'battery_soc': new_soc,
        'solar_power': new_solar,
        'load_power': new_load,
        'grid_power': grid_power,
        'total_cost_inr': new_cost,
        'carbon_emissions': new_record['carbon_emissions'],
        'reliability_status': 'Normal'
    }
    
    data['historical_data'] = historical_data.to_dict('records')
    data['current_state'] = new_state
    
    return data

@app.callback(
    [Output('power-graph', 'figure'),
     Output('cost-graph', 'figure'),
     Output('battery-gauge', 'figure'),
     Output('cost-metric', 'figure'),
     Output('solar-metric', 'figure'),
     Output('load-metric', 'figure')],
    [Input('simulation-data', 'data')]
)
def update_dashboard(data):
    historical_df = pd.DataFrame(data['historical_data'])
    current_state = data['current_state']
    
    # Power Flow Graph
    power_fig = make_subplots(rows=2, cols=1, subplot_titles=('Power Flow (W)', 'Battery State of Charge (%)'))
    
    power_fig.add_trace(go.Scatter(
        x=historical_df['timestamp'], y=historical_df['solar_power'],
        name='Solar', line=dict(color='orange'), fill='tozeroy'
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=historical_df['timestamp'], y=historical_df['load_power'],
        name='Load', line=dict(color='red'), fill='tozeroy'
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=historical_df['timestamp'], y=historical_df['grid_power'],
        name='Grid', line=dict(color='blue')
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=historical_df['timestamp'], y=historical_df['battery_soc'],
        name='Battery SOC', line=dict(color='green')
    ), row=2, col=1)
    
    power_fig.update_layout(height=500, showlegend=True)
    power_fig.update_yaxes(title_text="Power (W)", row=1, col=1)
    power_fig.update_yaxes(title_text="SOC (%)", row=2, col=1)
    
    # Cost Graph
    cost_fig = go.Figure()
    cost_fig.add_trace(go.Scatter(
        x=historical_df['timestamp'], y=historical_df['total_cost_inr'],
        name='Total Cost', line=dict(color='purple')
    ))
    cost_fig.update_layout(
        height=400,
        title="Cumulative Energy Cost",
        yaxis_title="Cost (₹)",
        showlegend=True
    )
    
    # Battery Gauge
    battery_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_state['battery_soc'],
        title={'text': "Battery SOC (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 20], 'color': "lightgray"},
                {'range': [95, 100], 'color': "lightgray"}
            ],
        }
    ))
    battery_gauge.update_layout(height=250)
    
    # Cost Metric
    cost_metric = go.Figure(go.Indicator(
        mode="number",
        value=current_state['total_cost_inr'],
        title={'text': "Total Cost"},
        number={'prefix': "₹", 'valueformat': ".2f"}
    ))
    cost_metric.update_layout(height=250)
    
    # Solar Metric
    solar_metric = go.Figure(go.Indicator(
        mode="number",
        value=current_state['solar_power'],
        title={'text': "Solar Power"},
        number={'suffix': " W"}
    ))
    solar_metric.update_layout(height=250)
    
    # Load Metric
    load_metric = go.Figure(go.Indicator(
        mode="number",
        value=current_state['load_power'],
        title={'text': "Load Power"},
        number={'suffix': " W"}
    ))
    load_metric.update_layout(height=250)
    
    return power_fig, cost_fig, battery_gauge, cost_metric, solar_metric, load_metric

if __name__ == '__main__':
    app.run(debug=True, port=8050)