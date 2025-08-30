import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time

from main import MicroGridDigitalTwin

# Initialize the digital twin
digital_twin = MicroGridDigitalTwin()

# Create Dash app
app = dash.Dash(__name__)
app.title = "MicroGrid Digital Twin"

# Layout
app.layout = html.Div([
    html.H1("MicroGrid Digital Twin Dashboard", style={'textAlign': 'center'}),
    
    # Controls
    html.Div([
        html.Button('Start Simulation', id='start-button', n_clicks=0),
        html.Button('Inject Disturbance', id='disturbance-button', n_clicks=0),
        dcc.Interval(id='interval-component', interval=3000, n_intervals=0, disabled=True),
        dcc.Store(id='simulation-data', data={'running': False}),
    ], style={'padding': '10px', 'textAlign': 'center'}),
    
    # Gauges and metrics
    html.Div([
        html.Div([
            dcc.Graph(id='battery-gauge', style={'display': 'inline-block', 'width': '30%'}),
            dcc.Graph(id='cost-metric', style={'display': 'inline-block', 'width': '30%'}),
            dcc.Graph(id='power-metrics', style={'display': 'inline-block', 'width': '30%'}),
        ]),
    ]),
    
    # Main power flow graph
    dcc.Graph(id='power-graph'),
    
    # Disturbance controls
    html.Div([
        html.Label("Solar Reduction (%)"),
        dcc.Slider(id='solar-slider', min=0, max=100, step=5, value=0,
                   marks={i: f'{i}%' for i in range(0, 101, 20)}),
        
        html.Label("Load Increase (%)"),
        dcc.Slider(id='load-slider', min=0, max=100, step=5, value=0,
                   marks={i: f'{i}%' for i in range(0, 101, 20)}),
    ], style={'padding': '20px', 'width': '80%', 'margin': 'auto'}),
])

# Simulation thread
simulation_thread = None
stop_simulation = False

def run_simulation():
    global stop_simulation
    stop_simulation = False
    
    while not stop_simulation:
        digital_twin.run_optimization_cycle()
        time.sleep(3)  # Update every 3 seconds

# Callbacks
@app.callback(
    [Output('interval-component', 'disabled'),
     Output('start-button', 'children'),
     Output('simulation-data', 'data')],
    [Input('start-button', 'n_clicks')],
    [State('simulation-data', 'data')]
)
def toggle_simulation(n_clicks, data):
    global simulation_thread, stop_simulation
    
    if n_clicks > 0:
        if not data['running']:
            # Start simulation
            data['running'] = True
            simulation_thread = threading.Thread(target=run_simulation)
            simulation_thread.start()
            return False, 'Stop Simulation', data
        else:
            # Stop simulation
            data['running'] = False
            stop_simulation = True
            if simulation_thread:
                simulation_thread.join()
            return True, 'Start Simulation', data
    
    return True, 'Start Simulation', data

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
        digital_twin.inject_disturbance(solar_reduction, load_increase)
        data['disturbance'] = True
        data['solar_reduction'] = solar_reduction
        data['load_increase'] = load_increase
    return data

@app.callback(
    [Output('power-graph', 'figure'),
     Output('battery-gauge', 'figure'),
     Output('cost-metric', 'figure'),
     Output('power-metrics', 'figure')],
    [Input('interval-component', 'n_intervals')],
    [State('simulation-data', 'data')]
)
def update_dashboard(n_intervals, data):
    # Get the latest data
    if not digital_twin.historical_data.empty:
        df = digital_twin.historical_data
        current = digital_twin.current_state
    else:
        # Default empty data
        df = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(minutes=i) for i in range(30, 0, -1)],
            'solar_power': [0] * 30,
            'load_power': [800] * 30,
            'grid_power': [0] * 30,
            'battery_setpoint': [0] * 30,
            'generator_setpoint': [0] * 30,
        })
        current = {
            'battery_soc': 50,
            'total_cost': 0,
            'solar_power': 0,
            'load_power': 800,
            'grid_power': 0
        }
    
    # Create power flow graph
    power_fig = make_subplots(rows=2, cols=1, subplot_titles=('Power Flow', 'Cost Accumulation'))
    
    # Power flow traces
    power_fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['solar_power'],
        name='Solar', line=dict(color='yellow')
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['load_power'],
        name='Load', line=dict(color='red')
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['grid_power'],
        name='Grid', line=dict(color='blue')
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['battery_setpoint'],
        name='Battery', line=dict(color='green')
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['generator_setpoint'],
        name='Generator', line=dict(color='orange')
    ), row=1, col=1)
    
    # Cost trace
    if 'total_cost' in df.columns:
        power_fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df['total_cost'],
            name='Total Cost', line=dict(color='purple')
        ), row=2, col=1)
    
    power_fig.update_layout(height=600, showlegend=True)
    
    # Battery gauge
    battery_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current['battery_soc'],
        title = {'text': "Battery SOC (%)"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 20], 'color': "lightgray"},
                {'range': [95, 100], 'color': "lightgray"}
            ],
        }
    ))
    battery_gauge.update_layout(height=250)
    
    # Cost metric
    cost_metric = go.Figure(go.Indicator(
        mode = "number",
        value = current['total_cost'],
        title = {'text': "Total Cost ($)"},
        number = {'prefix': "$", 'valueformat': ".4f"}
    ))
    cost_metric.update_layout(height=250)
    
    # Power metrics
    power_metrics = go.Figure()
    power_metrics.add_trace(go.Indicator(
        mode = "number",
        value = current['solar_power'],
        title = {'text': "Solar (W)"},
        domain = {'row': 0, 'column': 0}
    ))
    power_metrics.add_trace(go.Indicator(
        mode = "number",
        value = current['load_power'],
        title = {'text': "Load (W)"},
        domain = {'row': 0, 'column': 1}
    ))
    power_metrics.add_trace(go.Indicator(
        mode = "number",
        value = current['grid_power'],
        title = {'text': "Grid (W)"},
        domain = {'row': 1, 'column': 0}
    ))
    power_metrics.update_layout(
        grid = {'rows': 2, 'columns': 2, 'pattern': "independent"},
        height=250
    )
    
    return power_fig, battery_gauge, cost_metric, power_metrics

if __name__ == '__main__':
    app.run(debug=True, port=8050)