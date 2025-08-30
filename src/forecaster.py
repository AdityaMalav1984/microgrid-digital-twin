import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

class AdvancedMicroGridForecaster:
    def __init__(self):
        self.solar_model = None
        self.load_model = None
        self.weather_model = None
        self.scaler = StandardScaler()
        self.models_dir = "models/ml_models"
        os.makedirs(self.models_dir, exist_ok=True)
        
    def create_features(self, timestamp):
        """Create time-based features for forecasting"""
        hour = timestamp.hour
        day_of_week = timestamp.dayofweek
        day_of_year = timestamp.dayofyear
        month = timestamp.month
        is_weekend = 1 if day_of_week >= 5 else 0
        
        return np.array([hour, day_of_week, day_of_year, month, is_weekend])
    
    def load_training_data(self):
        """Load or generate training data"""
        # In a real application, this would load historical data
        # For demo, we'll generate synthetic data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='H')
        data = []
        
        for date in dates:
            features = self.create_features(date)
            
            # Synthetic solar generation (sinusoidal with noise)
            solar = max(0, 3000 * np.sin(np.pi * (date.hour + 6) / 15) + 
                       np.random.normal(0, 200))
            
            # Synthetic load pattern with noise
            load = (800 + 2000 * np.exp(-0.5 * ((date.hour - 19) / 3)**2) + 
                   np.random.normal(0, 150))
            
            data.append([*features, solar, load])
        
        columns = ['hour', 'day_of_week', 'day_of_year', 'month', 'is_weekend', 'solar', 'load']
        return pd.DataFrame(data, columns=columns, index=dates)
    
    def train_models(self):
        """Train machine learning models for forecasting"""
        print("Training forecasting models...")
        data = self.load_training_data()
        
        # Prepare features and targets
        X = data[['hour', 'day_of_week', 'day_of_year', 'month', 'is_weekend']].values
        y_solar = data['solar'].values
        y_load = data['load'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_solar_train, y_solar_test, y_load_train, y_load_test = train_test_split(
            X_scaled, y_solar, y_load, test_size=0.2, random_state=42
        )
        
        # Train solar forecast model
        self.solar_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.solar_model.fit(X_train, y_solar_train)
        
        # Train load forecast model
        self.load_model = MLPRegressor(hidden_layer_sizes=(50, 25), max_iter=1000, random_state=42)
        self.load_model.fit(X_train, y_load_train)
        
        # Save models
        joblib.dump(self.solar_model, f"{self.models_dir}/solar_model.pkl")
        joblib.dump(self.load_model, f"{self.models_dir}/load_model.pkl")
        joblib.dump(self.scaler, f"{self.models_dir}/scaler.pkl")
        
        print("Models trained and saved successfully!")
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            self.solar_model = joblib.load(f"{self.models_dir}/solar_model.pkl")
            self.load_model = joblib.load(f"{self.models_dir}/load_model.pkl")
            self.scaler = joblib.load(f"{self.models_dir}/scaler.pkl")
            return True
        except:
            return False
    
    def forecast(self, hours=24):
        """Generate forecast for the next N hours"""
        if not self.load_models():
            self.train_models()
        
        now = pd.Timestamp.now()
        future_times = [now + pd.Timedelta(hours=i) for i in range(hours)]
        
        solar_forecast = []
        load_forecast = []
        
        for time in future_times:
            features = self.create_features(time)
            features_scaled = self.scaler.transform([features])
            
            solar_pred = max(0, self.solar_model.predict(features_scaled)[0])
            load_pred = self.load_model.predict(features_scaled)[0]
            
            solar_forecast.append(solar_pred)
            load_forecast.append(load_pred)
        
        return np.array(solar_forecast), np.array(load_forecast)
    
    def get_weather_forecast(self):
        """Simulate weather forecast data (would integrate with API in real application)"""
        # This would connect to a weather API like OpenWeatherMap
        return {
            'temperature': np.random.uniform(15, 30),
            'cloud_cover': np.random.uniform(0, 1),
            'precipitation': np.random.uniform(0, 5)
        }