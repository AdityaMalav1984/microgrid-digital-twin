import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

class MicroGridForecaster:
    def __init__(self):
        self.solar_model = self._create_solar_model()
        self.load_model = self._create_load_model()
        
    def _create_solar_model(self):
        # Simple model based on time of day
        return Pipeline([
            ('poly', PolynomialFeatures(degree=3)),
            ('linear', LinearRegression())
        ])
    
    def _create_load_model(self):
        # Simple model based on time of day and day of week
        return Pipeline([
            ('poly', PolynomialFeatures(degree=3)),
            ('linear', LinearRegression())
        ])
    
    def fit_models(self, historical_data):
        """Train models on historical data"""
        # This would be implemented with real historical data
        pass
    
    def forecast_solar(self, current_time, weather_data=None):
        """Forecast solar production for the next 24 hours"""
        hours = np.array([[i] for i in range(24)])
        
        # Simple sinusoidal pattern for demonstration
        # Peak at noon, zero at night
        forecast = 3000 * np.sin(np.pi * (hours + 6) / 15)
        forecast[forecast < 0] = 0
        
        return forecast
    
    def forecast_load(self, current_time, day_of_week=None):
        """Forecast load for the next 24 hours"""
        hours = np.array([[i] for i in range(24)])
        
        # Simple pattern with peaks in morning and evening
        morning_peak = 2500 * np.exp(-0.5 * ((hours - 8) / 2)**2)
        evening_peak = 3500 * np.exp(-0.5 * ((hours - 19) / 2)**2)
        base_load = 800 * np.ones_like(hours)
        
        forecast = base_load + morning_peak + evening_peak
        return forecast.flatten()