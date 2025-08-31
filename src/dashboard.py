import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Create Dash app
app = dash.Dash(__name__)
app.title = "MicroGrid Digital Twin Dashboard"

# Global variables to store data
historical_data = pd.DataFrame()
current_state = {}

def initialize_data():
    """Initialize sample data"""
    global historical_data, current_state
    
    hours = 24
    timestamps = [datetime.now() - timedelta(hours=h) for h in range(hours, 0, -1)]
    
    historical_data = pd.DataFrame({
        'timestamp': timestamps,
        'solar_power': [max(0, 3000 * np.sin(np.pi * (h + 6) / 15)) for h in range(hours)],
        'load_power': [800 + 2000 * np.exp(-0.5 * ((h - 19) / 3)**2) for h in range(hours)],
        'grid_power': [500 * np.sin(h/4) for h in range(hours)],
        'battery_soc': [50 + 20 * np.sin(h/6) for h in range(hours)],
        'total_cost_inr': [100 + h * 15 for h in range(hours)]
    })
    
    current_state = {
        'battery_soc': historical_data['battery_soc'].iloc[-1],
        'solar_power': historical_data['solar_power'].iloc[-1],
        'load_power': historical_data['load_power'].iloc[-1],
        'grid_power': historical_data['grid_power'].iloc[-1],
        'total_cost_inr': historical_data['total_cost_inr'].iloc[-1]
    }

# Initialize data
initialize_data()

# Layout
app.layout = html.Div([
    html.H1("MicroGrid Digital Twin Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # Control Panel
    html.Div([
        html.Button('Start Simulation', id='start-button', n_clicks=0,
                   style={'backgroundColor': '#27ae60', 'color': 'white', 'margin': '5px'}),
        html.Button('Reset Simulation', id='reset-button', n_clicks=0,
                   style={'backgroundColor': '#e74c3c', 'color': 'white', 'margin': '5px'}),
        html.Button('Inject Cloud Cover', id='cloud-button', n_clicks=0,
                   style={'backgroundColor': '#3498db', 'color': 'white', 'margin': '5px'}),
        html.Button('Inject Load Spike', id='load-button', n_clicks=0,
                   style={'backgroundColor': '#f39c12', 'color': 'white', 'margin': '5px'}),
        dcc.Interval(id='interval-component', interval=2000, n_intervals=0, disabled=True),
    ], style={'padding': '10px', 'textAlign': 'center', 'backgroundColor': '#ecf0f1', 'marginBottom': '20px'}),
    
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
    
    # Status Display
    html.Div([
        html.H4("System Status:", style={'marginBottom': '10px'}),
        html.Div(id='status-display')
    ], style={'marginTop': '20px', 'padding': '10px', 'backgroundColor': '#f8f9fa'})
])

# Callbacks
@app.callback(
    [Output('interval-component', 'disabled'),
     Output('start-button', 'children'),
     Output('start-button', 'style')],
    [Input('start-button', 'n_clicks')]
)
def toggle_simulation(n_clicks):
    if n_clicks % 2 == 1:
        return False, 'Stop Simulation', {'backgroundColor': '#e74c3c', 'color': 'white', 'margin': '5px'}
    else:
        return True, 'Start Simulation', {'backgroundColor': '#27ae60', 'color': 'white', 'margin': '5px'}

@app.callback(
    Output('status-display', 'children'),
    [Input('reset-button', 'n_clicks'),
     Input('cloud-button', 'n_clicks'),
     Input('load-button', 'n_clicks')]
)
def handle_buttons(reset_clicks, cloud_clicks, load_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "System ready. Click 'Start Simulation' to begin."
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'reset-button' and reset_clicks:
        initialize_data()
        return "System reset to initial state."
    elif button_id == 'cloud-button' and cloud_clicks:
        # Reduce solar power by 60%
        current_state['solar_power'] *= 0.4
        return "Cloud cover injected! Solar power reduced by 60%."
    elif button_id == 'load-button' and load_clicks:
        # Increase load by 50%
        current_state['load_power'] *= 1.5
        return "Load spike injected! Load increased by 50%."
    
    return "System ready. Click 'Start Simulation' to begin."

@app.callback(
    [Output('power-graph', 'figure'),
     Output('cost-graph', 'figure'),
     Output('battery-gauge', 'figure'),
     Output('cost-metric', 'figure'),
     Output('solar-metric', 'figure'),
     Output('load-metric', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n_intervals):
    global historical_data, current_state
    
    # Create power flow graph
    power_fig = make_subplots(rows=2, cols=1, 
                             subplot_titles=('Power Flow (W)', 'Battery State of Charge (%)'),
                             vertical_spacing=0.15)
    
    power_fig.add_trace(go.Scatter(
        x=historical_data['timestamp'], y=historical_data['solar_power'],
        name='Solar', line=dict(color='orange', width=2), fill='tozeroy'
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=historical_data['timestamp'], y=historical_data['load_power'],
        name='Load', line=dict(color='red', width=2), fill='tozeroy'
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=historical_data['timestamp'], y=historical_data['grid_power'],
        name='Grid', line=dict(color='blue', width=2)
    ), row=1, col=1)
    
    power_fig.add_trace(go.Scatter(
        x=historical_data['timestamp'], y=historical_data['battery_soc'],
        name='Battery SOC', line=dict(color='green', width=2)
    ), row=2, col=1)
    
    power_fig.update_layout(
        height=500, 
        showlegend=True,
        title_text="Real-time Power Monitoring",
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    power_fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    power_fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    power_fig.update_yaxes(title_text="Power (W)", row=1, col=1)
    power_fig.update_yaxes(title_text="SOC (%)", row=2, col=1)
    
    # Cost Graph
    cost_fig = go.Figure()
    cost_fig.add_trace(go.Scatter(
        x=historical_data['timestamp'], y=historical_data['total_cost_inr'],
        name='Total Cost', line=dict(color='purple', width=3)
    ))
    cost_fig.update_layout(
        height=400,
        title="Cumulative Energy Cost (INR)",
        yaxis_title="Cost (₹)",
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    cost_fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    cost_fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    # Battery Gauge
    battery_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_state['battery_soc'],
        title={'text': "Battery SOC (%)", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "green", 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 20], 'color': 'red'},
                {'range': [20, 95], 'color': 'lightgreen'},
                {'range': [95, 100], 'color': 'orange'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    battery_gauge.update_layout(height=250, paper_bgcolor='white')
    
    # Cost Metric
    cost_metric = go.Figure(go.Indicator(
        mode="number",
        value=current_state['total_cost_inr'],
        title={'text': "Total Cost", 'font': {'size': 16}},
        number={'prefix': "₹", 'valueformat': ".2f", 'font': {'size': 24}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    cost_metric.update_layout(height=250, paper_bgcolor='white')
    
    # Solar Metric
    solar_metric = go.Figure(go.Indicator(
        mode="number",
        value=current_state['solar_power'],
        title={'text': "Solar Power", 'font': {'size': 16}},
        number={'suffix': " W", 'font': {'size': 24}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    solar_metric.update_layout(height=250, paper_bgcolor='white')
    
    # Load Metric
    load_metric = go.Figure(go.Indicator(
        mode="number",
        value=current_state['load_power'],
        title={'text': "Load Power", 'font': {'size': 16}},
        number={'suffix': " W", 'font': {'size': 24}},
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    load_metric.update_layout(height=250, paper_bgcolor='white')
    
    return power_fig, cost_fig, battery_gauge, cost_metric, solar_metric, load_metric

@app.callback(
    Output('interval-component', 'n_intervals'),
    [Input('interval-component', 'n_intervals')],
    [State('interval-component', 'disabled')]
)
def update_simulation(n_intervals, disabled):
    global historical_data, current_state
    
    if disabled:
        return n_intervals
    
    # Simulate new data point
    new_timestamp = datetime.now()
    
    # Add some realistic fluctuations
    new_solar = max(0, current_state['solar_power'] * np.random.uniform(0.95, 1.05))
    new_load = current_state['load_power'] * np.random.uniform(0.97, 1.03)
    new_soc = max(20, min(95, current_state['battery_soc'] + np.random.uniform(-2, 2)))
    
    # Calculate grid power based on balance
    grid_power = new_load - new_solar
    
    # Update cost (simple model - 6 INR/kWh)
    cost_increment = max(0, grid_power) * 6.0 / 1000
    new_cost = current_state['total_cost_inr'] + cost_increment
    
    # Create new record
    new_record = {
        'timestamp': new_timestamp,
        'solar_power': new_solar,
        'load_power': new_load,
        'grid_power': grid_power,
        'battery_soc': new_soc,
        'total_cost_inr': new_cost
    }
    
    # Update historical data (keep last 48 records)
    if len(historical_data) >= 48:
        historical_data = historical_data.iloc[1:]
    
    historical_data = pd.concat([historical_data, pd.DataFrame([new_record])], ignore_index=True)
    
    # Update current state
    current_state.update({
        'battery_soc': new_soc,
        'solar_power': new_solar,
        'load_power': new_load,
        'grid_power': grid_power,
        'total_cost_inr': new_cost
    })
    
    return n_intervals

if __name__ == '__main__':
    print("Starting MicroGrid Digital Twin Dashboard...")
    print("Open http://127.0.0.1:8050 in your browser")
    app.run(debug=True, port=8050)