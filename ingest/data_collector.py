#!/usr/bin/env python3
"""
Coletor de dados para integração com banco PostgreSQL
Conecta dados do ESP32 com o schema da Entrega 3
"""

import json
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid
from db.connection import DatabaseConnection

class DataCollector:
    """Coletor de dados que integra ESP32 com banco PostgreSQL"""
    
    def __init__(self, db_config: Dict):
        self.db = DatabaseConnection(db_config)
        self.asset_id = None
        self.sensor_ids = {}
        
    def setup_assets_and_sensors(self):
        """Configura assets e sensores no banco"""
        # Asset principal (equipamento industrial)
        asset_data = {
            'name': 'Linha de Produção Principal',
            'location': 'Setor A - Fábrica'
        }
        
        self.asset_id = self.db.create_asset(asset_data)
        print(f"Asset criado: {self.asset_id}")
        
        # Sensores baseados nos dados do ESP32
        sensors_config = [
            {
                'name': 'S_TEMP',
                'type': 'temperature',
                'unit': '°C',
                'min_value': -40.0,
                'max_value': 80.0
            },
            {
                'name': 'S_HUMIDITY',
                'type': 'humidity',
                'unit': '%',
                'min_value': 0.0,
                'max_value': 100.0
            },
            {
                'name': 'S_LIGHT',
                'type': 'luminosity',
                'unit': '%',
                'min_value': 0.0,
                'max_value': 100.0
            },
            {
                'name': 'S_VIBRATION',
                'type': 'vibration',
                'unit': 'mg',
                'min_value': 0.0,
                'max_value': 5000.0
            }
        ]
        
        for sensor_config in sensors_config:
            sensor_id = self.db.create_sensor(self.asset_id, sensor_config)
            self.sensor_ids[sensor_config['name']] = sensor_id
            print(f"Sensor {sensor_config['name']} criado: {sensor_id}")
    
    def process_esp32_data(self, esp32_data: List[Dict]) -> List[Dict]:
        """Processa dados do ESP32 para formato do banco"""
        processed_data = []
        
        for record in esp32_data:
            timestamp = datetime.fromisoformat(record['datetime'])
            
            # Temperatura
            processed_data.append({
                'sensor_id': self.sensor_ids['S_TEMP'],
                'ts': timestamp,
                'value': record['temperature']
            })
            
            # Umidade
            processed_data.append({
                'sensor_id': self.sensor_ids['S_HUMIDITY'],
                'ts': timestamp,
                'value': record['humidity']
            })
            
            # Luminosidade
            processed_data.append({
                'sensor_id': self.sensor_ids['S_LIGHT'],
                'ts': timestamp,
                'value': record['luminosity']
            })
            
            # Vibração (magnitude do vetor de aceleração)
            vibration = (record['accel_x']**2 + record['accel_y']**2 + record['accel_z']**2)**0.5
            processed_data.append({
                'sensor_id': self.sensor_ids['S_VIBRATION'],
                'ts': timestamp,
                'value': vibration
            })
        
        return processed_data
    
    def load_data_to_database(self, processed_data: List[Dict]):
        """Carrega dados processados no banco"""
        print(f"Carregando {len(processed_data)} registros no banco...")
        
        for record in processed_data:
            self.db.create_reading(
                sensor_id=record['sensor_id'],
                timestamp=record['ts'],
                value=record['value']
            )
        
        print("Dados carregados com sucesso!")
    
    def get_sensor_data(self, sensor_name: str, limit: int = 100) -> pd.DataFrame:
        """Recupera dados de um sensor específico"""
        sensor_id = self.sensor_ids.get(sensor_name)
        if not sensor_id:
            raise ValueError(f"Sensor {sensor_name} não encontrado")
        
        return self.db.get_sensor_readings(sensor_id, limit)
    
    def get_all_sensor_data(self, limit: int = 100) -> Dict[str, pd.DataFrame]:
        """Recupera dados de todos os sensores"""
        data = {}
        for sensor_name in self.sensor_ids.keys():
            data[sensor_name] = self.get_sensor_data(sensor_name, limit)
        return data
    
    def generate_summary_report(self) -> Dict:
        """Gera relatório resumo dos dados"""
        summary = {}
        
        for sensor_name, sensor_id in self.sensor_ids.items():
            df = self.get_sensor_data(sensor_name, 1000)
            if not df.empty:
                summary[sensor_name] = {
                    'count': len(df),
                    'mean': df['value'].mean(),
                    'std': df['value'].std(),
                    'min': df['value'].min(),
                    'max': df['value'].max(),
                    'last_reading': df['ts'].max()
                }
        
        return summary
    
    def detect_anomalies(self, threshold_config: Dict) -> List[Dict]:
        """Detecta anomalias baseadas em thresholds"""
        anomalies = []
        
        for sensor_name, sensor_id in self.sensor_ids.items():
            df = self.get_sensor_data(sensor_name, 100)
            if df.empty:
                continue
                
            threshold = threshold_config.get(sensor_name, {})
            min_threshold = threshold.get('min')
            max_threshold = threshold.get('max')
            
            for _, row in df.iterrows():
                value = row['value']
                timestamp = row['ts']
                
                if min_threshold is not None and value < min_threshold:
                    anomalies.append({
                        'sensor': sensor_name,
                        'timestamp': timestamp,
                        'value': value,
                        'type': 'below_minimum',
                        'threshold': min_threshold
                    })
                
                if max_threshold is not None and value > max_threshold:
                    anomalies.append({
                        'sensor': sensor_name,
                        'timestamp': timestamp,
                        'value': value,
                        'type': 'above_maximum',
                        'threshold': max_threshold
                    })
        
        return anomalies

if __name__ == "__main__":
    # Configuração do banco
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'industrial_iot',
        'user': 'postgres',
        'password': 'password'
    }
    
    # Exemplo de uso
    collector = DataCollector(db_config)
    
    # Configura assets e sensores
    collector.setup_assets_and_sensors()
    
    # Carrega dados de exemplo (simulados)
    with open('sensor_data.json', 'r') as f:
        esp32_data = json.load(f)
    
    # Processa e carrega dados
    processed_data = collector.process_esp32_data(esp32_data)
    collector.load_data_to_database(processed_data)
    
    # Gera relatório
    summary = collector.generate_summary_report()
    print("\n=== Relatório Resumo ===")
    print(json.dumps(summary, indent=2, default=str))
