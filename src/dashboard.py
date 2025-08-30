import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time

# Import our advanced modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import AdvancedMicroGridDigitalTwin as MicroGridDigitalTwin
from src.forecaster import AdvancedMicroGridForecaster
from src.optimizer import AdvancedMicroGridOptimizer

# Initialize the digital twin with advanced components
digital_twin = MicroGridDigitalTwin()
forecaster = AdvancedMicroGridForecaster()
optimizer = AdvancedMicroGridOptimizer()

# Create Dash app
app = dash.Dash(__name__)
app.title = "Advanced MicroGrid Digital Twin Dashboard"

# Layout with advanced controls
app.layout = html.Div([
    html.H1("Advanced MicroGrid Digital Twin", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # Control Panel
    html.Div([
        html.Div([
            html.H3("Control Panel", style={'marginBottom': '10px'}),
            
            html.Button('Start/Stop Simulation', id='start-button', n_clicks=0,
                       style={'backgroundColor': '#27ae60', 'color': 'white', 'margin': '5px'}),
            
            html.Button('Train Models', id='train-button', n_clicks=0,
                       style={'backgroundColor': '#3498db', 'color': 'white', 'margin': '5px'}),
            
            html.Button('Reset Simulation', id='reset-button', n_clicks=0,
                       style={'backgroundColor': '#e74c3c', 'color': 'white', 'margin': '5px'}),
            
            dcc.Interval(id='interval-component', interval=2000, n_intervals=0, disabled=True),
            
        ], style={'padding': '15px', 'backgroundColor': '#ecf0f1', 'borderRadius': '5px', 'marginBottom': '20px'}),
        
        # Configuration Panel
        html.Div([
            html.H3("Configuration", style={'marginBottom': '10px'}),
            
            html.Label("Carbon Cost ($/kgCO₂):"),
            dcc.Slider(id='carbon-slider', min=0, max=0.1, step=0.01, value=0.02,
                      marks={i/10: str(i/10) for i in range(0, 11, 2)}),
            
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
            
            html.Label("Grid Outage:"),
            dcc.RadioItems(
                id='grid-outage-radio',
                options=[
                    {'label': 'Grid Available', 'value': 'available'},
                    {'label': 'Grid Outage', 'value': 'outage'}
                ],
                value='available',
                labelStyle={'display': 'inline-block', 'marginRight': '10px'}
            ),
            
            html.Button('Apply Disturbance', id='disturbance-button', n_clicks=0,
                       style={'backgroundColor': '#f39c12', 'color': 'white', 'marginTop': '10px'}),
            
        ], style={'padding': '15px', 'backgroundColor': '#ecf0f1', 'borderRadius': '5px'}),
        
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '20px', 'marginBottom': '20px'}),
    
    # Key Metrics
    html.Div([
        html.Div([
            dcc.Graph(id='battery-gauge', style={'display': 'inline-block', 'width': '24%'}),
            dcc.Graph(id='cost-metric', style={'display': 'inline-block', 'width': '24%'}),
            dcc.Graph(id='carbon-metric', style={'display': 'inline-block', 'width': '24%'}),
            dcc.Graph(id='reliability-metric', style={'display': 'inline-block', 'width': '24%'}),
        ]),
    ], style={'marginBottom': '20px'}),
    
    # Main Visualization
    html.Div([
        dcc.Graph(id='power-graph', style={'height': '500px'}),
    ], style={'marginBottom': '20px'}),
    
    # Forecast Visualization
    html.Div([
        dcc.Graph(id='forecast-graph', style={'height': '400px'}),
    ]),
    
    # Data Table
    html.Div([
        html.H3("Historical Data"),
        html.Div(id='data-table'),
    ], style={'marginTop': '20px'}),
    
    # Hidden div for storing data
    dcc.Store(id='simulation-data', data={'running': False}),
])

# Advanced callbacks
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
        data['running'] = True
        return False, 'Stop Simulation', {'backgroundColor': '#e74c3c', 'color': 'white', 'margin': '5px'}
    else:
        # Stop simulation
        data['running'] = False
        return True, 'Start Simulation', {'backgroundColor': '#27ae60', 'color': 'white', 'margin': '5px'}

@app.callback(
    Output('simulation-data', 'data', allow_duplicate=True),
    [Input('train-button', 'n_clicks')],
    prevent_initial_call=True
)
def train_models(n_clicks):
    if n_clicks > 0:
        forecaster.train_models()
        return {'message': 'Models trained successfully!'}
    return dash.no_update

# Add more advanced callbacks for the enhanced features...

if __name__ == '__main__':
    app.run(debug=True, port=8050)