#!/usr/bin/env python3
"""
Carregador de dados para demonstração
Gera dados sintéticos e carrega no banco
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import json
from db.connection import DatabaseConnection

class DataLoader:
    """Carregador de dados sintéticos para demonstração"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def generate_synthetic_data(self, days: int = 7, frequency_minutes: int = 5):
        """Gera dados sintéticos realísticos"""
        print(f"Gerando dados sintéticos para {days} dias...")
        
        # Configuração temporal
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        periods = int(days * 24 * 60 / frequency_minutes)
        
        # Dados sintéticos para cada sensor
        sensors_data = {}
        
        # Temperatura (S_TEMP) - Variação diária + tendência
        temp_base = 25
        temp_amplitude = 8
        temp_trend = np.linspace(0, 2, periods)
        temp_hourly = np.sin(2 * np.pi * np.arange(periods) * frequency_minutes / (24 * 60))
        temp_values = temp_base + temp_amplitude * temp_hourly + temp_trend + np.random.normal(0, 0.5, periods)
        
        sensors_data['S_TEMP'] = {
            'values': temp_values,
            'unit': '°C',
            'type': 'temperature'
        }
        
        # Umidade (S_HUMIDITY) - Correlação negativa com temperatura
        humidity_base = 60
        humidity_amplitude = 15
        humidity_values = humidity_base + humidity_amplitude * (-temp_hourly) + np.random.normal(0, 3, periods)
        humidity_values = np.clip(humidity_values, 0, 100)
        
        sensors_data['S_HUMIDITY'] = {
            'values': humidity_values,
            'unit': '%',
            'type': 'humidity'
        }
        
        # Luminosidade (S_LIGHT) - Padrão dia/noite
        light_values = []
        for i in range(periods):
            hour = (start_time + timedelta(minutes=i*frequency_minutes)).hour
            if 6 <= hour <= 18:  # Dia
                light = 70 + np.random.normal(0, 10)
            else:  # Noite
                light = 10 + np.random.normal(0, 5)
            light_values.append(max(0, min(100, light)))
        
        sensors_data['S_LIGHT'] = {
            'values': light_values,
            'unit': '%',
            'type': 'luminosity'
        }
        
        # Vibração (S_VIBRATION) - Picos ocasionais
        vibration_base = 1000
        vibration_values = []
        for i in range(periods):
            if np.random.random() < 0.05:  # 5% chance de pico
                vib = vibration_base + np.random.normal(0, 500) + 2000
            else:
                vib = vibration_base + np.random.normal(0, 100)
            vibration_values.append(max(0, vib))
        
        sensors_data['S_VIBRATION'] = {
            'values': vibration_values,
            'unit': 'mg',
            'type': 'vibration'
        }
        
        # Cria timestamps
        timestamps = [start_time + timedelta(minutes=i*frequency_minutes) for i in range(periods)]
        
        return sensors_data, timestamps
    
    def load_synthetic_data(self, days: int = 7):
        """Carrega dados sintéticos no banco"""
        print("Carregando dados sintéticos no banco...")
        
        # Gera dados
        sensors_data, timestamps = self.generate_synthetic_data(days)
        
        # Recupera IDs dos sensores
        sensor_ids = {}
        for sensor_name in sensors_data.keys():
            sensor_id = self.db.get_sensor_id_by_name(sensor_name)
            if sensor_id:
                sensor_ids[sensor_name] = sensor_id
            else:
                print(f"⚠️  Sensor {sensor_name} não encontrado no banco")
        
        # Carrega dados
        total_inserted = 0
        for sensor_name, data in sensors_data.items():
            if sensor_name not in sensor_ids:
                continue
                
            sensor_id = sensor_ids[sensor_name]
            values = data['values']
            
            print(f"Carregando {len(values)} registros para {sensor_name}...")
            
            for i, (timestamp, value) in enumerate(zip(timestamps, values)):
                try:
                    self.db.create_reading(sensor_id, timestamp, value)
                    total_inserted += 1
                except Exception as e:
                    print(f"Erro ao inserir registro {i} para {sensor_name}: {e}")
        
        print(f"✅ {total_inserted} registros carregados com sucesso")
        return total_inserted
    
    def create_sample_alerts(self):
        """Cria alertas de exemplo"""
        print("Criando alertas de exemplo...")
        
        # Recupera IDs dos sensores
        sensor_ids = {}
        for sensor_name in ['S_TEMP', 'S_HUMIDITY', 'S_VIBRATION', 'S_LIGHT']:
            sensor_id = self.db.get_sensor_id_by_name(sensor_name)
            if sensor_id:
                sensor_ids[sensor_name] = sensor_id
        
        # Cria alertas baseados em thresholds
        alerts_created = 0
        
        # Alerta de temperatura alta
        if 'S_TEMP' in sensor_ids:
            self.db.create_alert(
                sensor_ids['S_TEMP'],
                'threshold',
                35.0,
                38.5,
                'Temperatura crítica detectada - Verificar sistema de refrigeração',
                'high'
            )
            alerts_created += 1
        
        # Alerta de umidade alta
        if 'S_HUMIDITY' in sensor_ids:
            self.db.create_alert(
                sensor_ids['S_HUMIDITY'],
                'threshold',
                80.0,
                85.2,
                'Umidade elevada - Verificar ventilação',
                'medium'
            )
            alerts_created += 1
        
        # Alerta de vibração excessiva
        if 'S_VIBRATION' in sensor_ids:
            self.db.create_alert(
                sensor_ids['S_VIBRATION'],
                'threshold',
                2000.0,
                2500.0,
                'Vibração excessiva - Verificar alinhamento do equipamento',
                'high'
            )
            alerts_created += 1
        
        print(f"✅ {alerts_created} alertas criados")
        return alerts_created
    
    def create_sample_predictions(self):
        """Cria predições de exemplo"""
        print("Criando predições de exemplo...")
        
        # Recupera IDs dos sensores
        sensor_ids = {}
        for sensor_name in ['S_TEMP', 'S_HUMIDITY', 'S_VIBRATION']:
            sensor_id = self.db.get_sensor_id_by_name(sensor_name)
            if sensor_id:
                sensor_ids[sensor_name] = sensor_id
        
        # Cria predições
        predictions_created = 0
        
        for sensor_name, sensor_id in sensor_ids.items():
            # Gera predição baseada no último valor + ruído
            last_reading = self.db.get_sensor_readings_by_name(sensor_name, 1)
            if not last_reading.empty:
                base_value = last_reading['value'].iloc[0]
                predicted_value = base_value + np.random.normal(0, base_value * 0.05)
                confidence = np.random.uniform(0.7, 0.95)
                
                self.db.create_prediction(sensor_id, predicted_value, confidence, "v1.0")
                predictions_created += 1
        
        print(f"✅ {predictions_created} predições criadas")
        return predictions_created
    
    def generate_demo_report(self):
        """Gera relatório de demonstração"""
        print("Gerando relatório de demonstração...")
        
        # Estatísticas do banco
        stats = self.db.get_database_stats()
        
        # Dados dos sensores
        sensor_stats = {}
        for sensor_name in ['S_TEMP', 'S_HUMIDITY', 'S_LIGHT', 'S_VIBRATION']:
            try:
                data = self.db.get_sensor_readings_by_name(sensor_name, 100)
                if not data.empty:
                    sensor_stats[sensor_name] = {
                        'count': len(data),
                        'mean': data['value'].mean(),
                        'std': data['value'].std(),
                        'min': data['value'].min(),
                        'max': data['value'].max(),
                        'last_reading': data['ts'].max()
                    }
            except Exception as e:
                print(f"Erro ao obter estatísticas de {sensor_name}: {e}")
        
        # Alertas ativos
        active_alerts = self.db.get_active_alerts()
        
        # Predições recentes
        recent_predictions = self.db.get_recent_predictions(limit=10)
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database_stats': stats,
            'sensor_stats': sensor_stats,
            'active_alerts_count': len(active_alerts),
            'recent_predictions_count': len(recent_predictions),
            'summary': {
                'total_readings': stats.get('reading_count', 0),
                'total_sensors': stats.get('sensor_count', 0),
                'total_assets': stats.get('asset_count', 0),
                'active_alerts': len(active_alerts)
            }
        }
        
        # Salva relatório
        with open('demo_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print("✅ Relatório de demonstração salvo em demo_report.json")
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
    loader = DataLoader(db)
    
    try:
        # Carrega dados sintéticos
        loader.load_synthetic_data(days=7)
        
        # Cria alertas de exemplo
        loader.create_sample_alerts()
        
        # Cria predições de exemplo
        loader.create_sample_predictions()
        
        # Gera relatório
        report = loader.generate_demo_report()
        
        print("\n=== Relatório de Demonstração ===")
        print(f"Total de leituras: {report['summary']['total_readings']}")
        print(f"Total de sensores: {report['summary']['total_sensors']}")
        print(f"Alertas ativos: {report['summary']['active_alerts']}")
        
    finally:
        db.close()
