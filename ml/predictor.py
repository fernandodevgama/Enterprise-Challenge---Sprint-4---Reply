#!/usr/bin/env python3
"""
Sistema de predição em tempo real para sensores IoT
Integra modelos ML com dados do banco PostgreSQL
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import os
from db.connection import DatabaseConnection

class MLPredictor:
    """Sistema de predição ML para sensores IoT"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.models = {}
        self.feature_columns = ['lag1', 'lag2', 'roll3', 'hour']
        self.load_models()
    
    def load_models(self):
        """Carrega modelos treinados"""
        models_dir = "models"
        if not os.path.exists(models_dir):
            print("Diretório de modelos não encontrado")
            return
        
        for filename in os.listdir(models_dir):
            if filename.endswith('.pkl'):
                model_path = os.path.join(models_dir, filename)
                model_name = filename.replace('.pkl', '')
                try:
                    self.models[model_name] = joblib.load(model_path)
                    print(f"Modelo carregado: {model_name}")
                except Exception as e:
                    print(f"Erro ao carregar modelo {model_name}: {e}")
    
    def prepare_features(self, sensor_name: str, lookback: int = 5) -> pd.DataFrame:
        """Prepara features para predição"""
        # Recupera dados recentes do sensor
        recent_data = self.db.get_sensor_readings_by_name(sensor_name, lookback)
        
        if recent_data.empty:
            raise ValueError(f"Nenhum dado encontrado para {sensor_name}")
        
        # Ordena por timestamp
        df = recent_data.sort_values('ts').reset_index(drop=True)
        
        # Cria features
        df['lag1'] = df['value'].shift(1)
        df['lag2'] = df['value'].shift(2)
        df['roll3'] = df['value'].rolling(3).mean()
        df['hour'] = df['ts'].dt.hour
        
        # Remove NaN
        df = df.dropna()
        
        if len(df) == 0:
            raise ValueError(f"Features insuficientes para {sensor_name}")
        
        return df[self.feature_columns]
    
    def predict_single_value(self, sensor_name: str, model_name: str = None) -> Dict:
        """Prediz próximo valor para um sensor"""
        if model_name is None:
            # Tenta encontrar melhor modelo
            model_name = self.find_best_model(sensor_name)
        
        if model_name not in self.models:
            raise ValueError(f"Modelo {model_name} não encontrado")
        
        # Prepara features
        features = self.prepare_features(sensor_name)
        
        # Predição
        model = self.models[model_name]
        prediction = model.predict(features.tail(1))[0]
        
        # Calcula confiança baseada na variância dos dados recentes
        recent_values = self.db.get_sensor_readings_by_name(sensor_name, 10)['value']
        confidence = max(0.1, min(0.95, 1.0 - (recent_values.std() / recent_values.mean())))
        
        # Salva predição no banco
        sensor_id = self.db.get_sensor_id_by_name(sensor_name)
        self.db.create_prediction(sensor_id, prediction, confidence, "v1.0")
        
        return {
            'sensor_name': sensor_name,
            'predicted_value': float(prediction),
            'confidence': float(confidence),
            'model_used': model_name,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def predict_multiple_sensors(self, sensor_names: List[str]) -> Dict:
        """Prediz valores para múltiplos sensores"""
        predictions = {}
        
        for sensor_name in sensor_names:
            try:
                pred = self.predict_single_value(sensor_name)
                predictions[sensor_name] = pred
            except Exception as e:
                predictions[sensor_name] = {'error': str(e)}
        
        return predictions
    
    def predict_sequence(self, sensor_name: str, steps: int = 5) -> List[Dict]:
        """Prediz sequência de valores futuros"""
        predictions = []
        current_features = self.prepare_features(sensor_name)
        
        model_name = self.find_best_model(sensor_name)
        if model_name not in self.models:
            raise ValueError(f"Modelo não encontrado para {sensor_name}")
        
        model = self.models[model_name]
        
        for step in range(steps):
            # Prediz próximo valor
            pred = model.predict(current_features.tail(1))[0]
            
            # Atualiza features para próxima predição
            new_row = current_features.iloc[-1].copy()
            new_row['lag1'] = pred
            new_row['lag2'] = current_features.iloc[-1]['lag1']
            new_row['roll3'] = (pred + current_features.iloc[-1]['lag1'] + current_features.iloc[-1]['lag2']) / 3
            new_row['hour'] = (datetime.now() + timedelta(minutes=step*5)).hour
            
            # Adiciona nova linha
            current_features = pd.concat([current_features, new_row.to_frame().T], ignore_index=True)
            
            predictions.append({
                'step': step + 1,
                'predicted_value': float(pred),
                'timestamp': (datetime.now() + timedelta(minutes=step*5)).isoformat()
            })
        
        return predictions
    
    def find_best_model(self, sensor_name: str) -> str:
        """Encontra melhor modelo para um sensor"""
        # Procura modelos que contenham o nome do sensor
        available_models = [name for name in self.models.keys() if sensor_name in name]
        
        if not available_models:
            raise ValueError(f"Nenhum modelo encontrado para {sensor_name}")
        
        # Prioriza Random Forest sobre Linear
        rf_models = [name for name in available_models if 'rf' in name]
        if rf_models:
            return rf_models[0]
        
        return available_models[0]
    
    def detect_anomalies(self, sensor_name: str, threshold: float = 2.0) -> List[Dict]:
        """Detecta anomalias baseadas em predições"""
        try:
            # Prediz valor atual
            prediction = self.predict_single_value(sensor_name)
            predicted_value = prediction['predicted_value']
            
            # Recupera valor atual
            current_data = self.db.get_sensor_readings_by_name(sensor_name, 1)
            if current_data.empty:
                return []
            
            actual_value = current_data['value'].iloc[0]
            
            # Calcula diferença normalizada
            error = abs(actual_value - predicted_value)
            recent_std = self.db.get_sensor_readings_by_name(sensor_name, 20)['value'].std()
            
            if recent_std > 0:
                normalized_error = error / recent_std
                
                if normalized_error > threshold:
                    return [{
                        'sensor_name': sensor_name,
                        'actual_value': actual_value,
                        'predicted_value': predicted_value,
                        'error': error,
                        'normalized_error': normalized_error,
                        'severity': 'high' if normalized_error > threshold * 2 else 'medium',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }]
        
        except Exception as e:
            print(f"Erro na detecção de anomalias para {sensor_name}: {e}")
        
        return []
    
    def get_prediction_accuracy(self, sensor_name: str, hours_back: int = 24) -> Dict:
        """Calcula acurácia das predições recentes"""
        # Recupera predições das últimas 24 horas
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        # Recupera predições e valores reais
        predictions = self.db.get_predictions_by_sensor(sensor_name, cutoff_time)
        actual_values = self.db.get_sensor_readings_by_name(sensor_name, 1000)
        
        if predictions.empty or actual_values.empty:
            return {}
        
        # Alinha predições com valores reais
        accuracy_data = []
        for _, pred in predictions.iterrows():
            pred_time = pred['created_at']
            # Encontra valor real mais próximo
            time_diff = abs(actual_values['ts'] - pred_time)
            closest_idx = time_diff.idxmin()
            
            if time_diff.iloc[closest_idx] < timedelta(minutes=30):  # Tolerância de 30 min
                actual_value = actual_values.iloc[closest_idx]['value']
                error = abs(pred['predicted_value'] - actual_value)
                accuracy_data.append({
                    'predicted': pred['predicted_value'],
                    'actual': actual_value,
                    'error': error,
                    'timestamp': pred_time
                })
        
        if not accuracy_data:
            return {}
        
        df_accuracy = pd.DataFrame(accuracy_data)
        
        return {
            'total_predictions': len(accuracy_data),
            'mean_error': df_accuracy['error'].mean(),
            'std_error': df_accuracy['error'].std(),
            'max_error': df_accuracy['error'].max(),
            'accuracy_rate': (df_accuracy['error'] < df_accuracy['error'].mean()).mean()
        }
    
    def generate_prediction_report(self, sensor_names: List[str]) -> Dict:
        """Gera relatório de predições para múltiplos sensores"""
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sensors': {}
        }
        
        for sensor_name in sensor_names:
            try:
                # Predição atual
                current_pred = self.predict_single_value(sensor_name)
                
                # Sequência de predições
                sequence_pred = self.predict_sequence(sensor_name, 5)
                
                # Detecção de anomalias
                anomalies = self.detect_anomalies(sensor_name)
                
                # Acurácia
                accuracy = self.get_prediction_accuracy(sensor_name)
                
                report['sensors'][sensor_name] = {
                    'current_prediction': current_pred,
                    'sequence_predictions': sequence_pred,
                    'anomalies': anomalies,
                    'accuracy': accuracy
                }
                
            except Exception as e:
                report['sensors'][sensor_name] = {'error': str(e)}
        
        return report

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
    predictor = MLPredictor(db)
    
    try:
        # Predições para sensores principais
        sensors = ['S_TEMP', 'S_HUMIDITY', 'S_LIGHT', 'S_VIBRATION']
        
        # Predições individuais
        for sensor in sensors:
            try:
                pred = predictor.predict_single_value(sensor)
                print(f"{sensor}: {pred['predicted_value']:.2f} (confiança: {pred['confidence']:.2f})")
            except Exception as e:
                print(f"Erro para {sensor}: {e}")
        
        # Relatório completo
        report = predictor.generate_prediction_report(sensors)
        with open('prediction_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print("Relatório de predições salvo em prediction_report.json")
        
    finally:
        db.close()
