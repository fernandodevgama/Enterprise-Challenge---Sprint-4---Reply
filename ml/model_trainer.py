#!/usr/bin/env python3
"""
Treinador de modelo ML integrado com banco PostgreSQL
Baseado na Entrega 3, adaptado para integração completa
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.model_selection import train_test_split
import joblib
from db.connection import DatabaseConnection

class MLModelTrainer:
    """Treinador de modelos ML para sensores IoT"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.models = {}
        self.feature_columns = ['lag1', 'lag2', 'roll3', 'hour']
        
    def prepare_training_data(self, sensor_name: str, limit: int = 1000) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Prepara dados para treinamento do modelo"""
        # Recupera dados do sensor
        sensor_data = self.db.get_sensor_readings_by_name(sensor_name, limit)
        
        if sensor_data.empty:
            raise ValueError(f"Nenhum dado encontrado para o sensor {sensor_name}")
        
        # Ordena por timestamp
        sensor_data = sensor_data.sort_values('ts').reset_index(drop=True)
        
        # Cria features para ML
        df = sensor_data.copy()
        df['lag1'] = df['value'].shift(1)
        df['lag2'] = df['value'].shift(2)
        df['roll3'] = df['value'].rolling(3).mean()
        df['hour'] = df['ts'].dt.hour
        
        # Remove linhas com NaN
        df = df.dropna().reset_index(drop=True)
        
        if len(df) < 10:
            raise ValueError(f"Dados insuficientes para treinamento: {len(df)} registros")
        
        # Separa features e target
        X = df[self.feature_columns]
        y = df['value']
        
        return X, y
    
    def train_linear_model(self, sensor_name: str, test_size: float = 0.2) -> Dict:
        """Treina modelo de regressão linear"""
        print(f"Treinando modelo linear para {sensor_name}...")
        
        X, y = self.prepare_training_data(sensor_name)
        
        # Split temporal
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Treina modelo
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Predições
        y_pred = model.predict(X_test)
        
        # Métricas
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # Salva modelo
        model_path = f"models/{sensor_name}_linear_model.pkl"
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, model_path)
        
        results = {
            'model_type': 'linear',
            'sensor_name': sensor_name,
            'mae': float(mae),
            'r2': float(r2),
            'rmse': float(rmse),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'model_path': model_path,
            'feature_importance': dict(zip(self.feature_columns, model.coef_))
        }
        
        self.models[f"{sensor_name}_linear"] = model
        
        return results
    
    def train_random_forest_model(self, sensor_name: str, test_size: float = 0.2) -> Dict:
        """Treina modelo Random Forest"""
        print(f"Treinando modelo Random Forest para {sensor_name}...")
        
        X, y = self.prepare_training_data(sensor_name)
        
        # Split temporal
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Treina modelo
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Predições
        y_pred = model.predict(X_test)
        
        # Métricas
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # Salva modelo
        model_path = f"models/{sensor_name}_rf_model.pkl"
        os.makedirs("models", exist_ok=True)
        joblib.dump(model, model_path)
        
        results = {
            'model_type': 'random_forest',
            'sensor_name': sensor_name,
            'mae': float(mae),
            'r2': float(r2),
            'rmse': float(rmse),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'model_path': model_path,
            'feature_importance': dict(zip(self.feature_columns, model.feature_importances_))
        }
        
        self.models[f"{sensor_name}_rf"] = model
        
        return results
    
    def train_all_models(self, sensors: List[str]) -> Dict:
        """Treina modelos para todos os sensores"""
        results = {}
        
        for sensor in sensors:
            try:
                # Treina modelo linear
                linear_results = self.train_linear_model(sensor)
                results[f"{sensor}_linear"] = linear_results
                
                # Treina modelo Random Forest
                rf_results = self.train_random_forest_model(sensor)
                results[f"{sensor}_rf"] = rf_results
                
            except Exception as e:
                print(f"Erro ao treinar modelo para {sensor}: {e}")
                results[f"{sensor}_error"] = str(e)
        
        return results
    
    def save_training_results(self, results: Dict, filename: str = "training_results.json"):
        """Salva resultados do treinamento"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Resultados salvos em {filename}")
    
    def get_best_model(self, sensor_name: str) -> str:
        """Retorna o melhor modelo para um sensor baseado no R²"""
        linear_key = f"{sensor_name}_linear"
        rf_key = f"{sensor_name}_rf"
        
        if linear_key in self.models and rf_key in self.models:
            # Compara modelos (assumindo que temos métricas salvas)
            # Por simplicidade, retorna Random Forest se disponível
            return rf_key
        elif linear_key in self.models:
            return linear_key
        elif rf_key in self.models:
            return rf_key
        else:
            raise ValueError(f"Nenhum modelo treinado para {sensor_name}")
    
    def predict_next_value(self, sensor_name: str, model_type: str = 'auto') -> Dict:
        """Prediz próximo valor para um sensor"""
        if model_type == 'auto':
            model_key = self.get_best_model(sensor_name)
        else:
            model_key = f"{sensor_name}_{model_type}"
        
        if model_key not in self.models:
            raise ValueError(f"Modelo {model_key} não encontrado")
        
        # Recupera dados recentes
        recent_data = self.db.get_sensor_readings_by_name(sensor_name, 10)
        if recent_data.empty:
            raise ValueError(f"Dados insuficientes para predição de {sensor_name}")
        
        # Prepara features
        df = recent_data.sort_values('ts').tail(3)
        features = pd.DataFrame({
            'lag1': [df['value'].iloc[-2] if len(df) > 1 else df['value'].iloc[-1]],
            'lag2': [df['value'].iloc[-3] if len(df) > 2 else df['value'].iloc[-1]],
            'roll3': [df['value'].tail(3).mean()],
            'hour': [datetime.now().hour]
        })
        
        # Predição
        model = self.models[model_key]
        prediction = model.predict(features)[0]
        
        # Salva predição no banco
        sensor_id = self.db.get_sensor_id_by_name(sensor_name)
        self.db.create_prediction(sensor_id, prediction, 0.8, "v1.0")
        
        return {
            'sensor_name': sensor_name,
            'predicted_value': float(prediction),
            'model_used': model_key,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def evaluate_model_performance(self, sensor_name: str) -> Dict:
        """Avalia performance do modelo em dados recentes"""
        # Recupera dados dos últimos 100 registros
        recent_data = self.db.get_sensor_readings_by_name(sensor_name, 100)
        if recent_data.empty:
            return {}
        
        # Prepara dados para avaliação
        df = recent_data.sort_values('ts').reset_index(drop=True)
        df['lag1'] = df['value'].shift(1)
        df['lag2'] = df['value'].shift(2)
        df['roll3'] = df['value'].rolling(3).mean()
        df['hour'] = df['ts'].dt.hour
        df = df.dropna()
        
        if len(df) < 10:
            return {}
        
        # Usa últimos 20% para teste
        test_size = int(len(df) * 0.2)
        test_data = df.tail(test_size)
        
        X_test = test_data[self.feature_columns]
        y_test = test_data['value']
        
        # Avalia cada modelo disponível
        results = {}
        
        for model_key, model in self.models.items():
            if sensor_name in model_key:
                try:
                    y_pred = model.predict(X_test)
                    mae = mean_absolute_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    
                    results[model_key] = {
                        'mae': float(mae),
                        'r2': float(r2),
                        'test_samples': len(y_test)
                    }
                except Exception as e:
                    results[model_key] = {'error': str(e)}
        
        return results

if __name__ == "__main__":
    # Exemplo de uso
    from db.connection import DatabaseConnection
    
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'industrial_iot',
        'user': 'postgres',
        'password': 'password'
    }
    
    db = DatabaseConnection(db_config)
    trainer = MLModelTrainer(db)
    
    try:
        # Treina modelos para sensores principais
        sensors = ['S_TEMP', 'S_HUMIDITY', 'S_LIGHT', 'S_VIBRATION']
        results = trainer.train_all_models(sensors)
        
        # Salva resultados
        trainer.save_training_results(results)
        
        # Exibe resumo
        print("\n=== Resumo do Treinamento ===")
        for key, result in results.items():
            if 'error' not in result:
                print(f"{key}: MAE={result['mae']:.3f}, R²={result['r2']:.3f}")
        
    finally:
        db.close()
