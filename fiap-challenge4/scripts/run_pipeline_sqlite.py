#!/usr/bin/env python3
"""
Pipeline Principal - Sistema IoT Industrial

Script principal para execução do pipeline completo com SQLite.
Executa coleta de dados, treinamento ML e geração de relatórios.

Autor: Sistema IoT Industrial
Versão: 2.0
Data: 2024
"""

import sys
import os
import json
import time
from datetime import datetime, timezone

# Adiciona diretórios ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ingest.esp32_simulator import ESP32Simulator
from ingest.data_collector import DataCollector
from db.sqlite_connection import SQLiteConnection
from ml.model_trainer import MLModelTrainer
from ml.predictor import MLPredictor

def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step, description):
    """Imprime passo do pipeline"""
    print(f"\n[{step}] {description}")
    print("-" * 40)

def main():
    """Executa pipeline completo com SQLite"""
    
    print_header("SISTEMA INTEGRADO DE MANUTENÇÃO PREDITIVA")
    print("Hermes Reply Challenge - Sprint 4")
    print("Versão SQLite - Funciona sem PostgreSQL")
    print("Integração completa: ESP32 → SQLite → ML → Dashboard")
    
    try:
        # Passo 1: Simulação ESP32
        print_step(1, "Simulando coleta de dados do ESP32")
        
        simulator = ESP32Simulator()
        print("Iniciando simulação por 2 minutos...")
        esp32_data = simulator.run_simulation(duration_minutes=2, interval_seconds=5)
        
        print(f"✅ Coletados {len(esp32_data)} registros do ESP32")
        simulator.save_data("sensor_data.json")
        
        # Passo 2: Configuração do banco SQLite
        print_step(2, "Configurando banco SQLite")
        
        db = SQLiteConnection("industrial_iot.db")
        print("✅ Conexão SQLite estabelecida")
        
        # Passo 3: Ingestão de dados
        print_step(3, "Ingerindo dados no banco SQLite")
        
        # Configuração para SQLite
        db_config = {'type': 'sqlite', 'path': 'industrial_iot.db'}
        
        # Cria assets e sensores se não existirem
        asset_id = db.create_asset({
            'name': 'Linha de Produção Principal',
            'location': 'Setor A - Fábrica'
        })
        
        # Cria sensores
        sensor_ids = {}
        sensors_config = [
            {'name': 'S_TEMP', 'type': 'temperature', 'unit': '°C', 'min_value': -40.0, 'max_value': 80.0},
            {'name': 'S_HUMIDITY', 'type': 'humidity', 'unit': '%', 'min_value': 0.0, 'max_value': 100.0},
            {'name': 'S_LIGHT', 'type': 'luminosity', 'unit': '%', 'min_value': 0.0, 'max_value': 100.0},
            {'name': 'S_VIBRATION', 'type': 'vibration', 'unit': 'mg', 'min_value': 0.0, 'max_value': 5000.0}
        ]
        
        for sensor_config in sensors_config:
            sensor_id = db.create_sensor(asset_id, sensor_config)
            sensor_ids[sensor_config['name']] = sensor_id
            print(f"Sensor {sensor_config['name']} criado: {sensor_id}")
        
        # Processa e carrega dados
        processed_count = 0
        for record in esp32_data:
            timestamp = datetime.fromisoformat(record['datetime'])
            
            # Temperatura
            db.create_reading(sensor_ids['S_TEMP'], timestamp, record['temperature'])
            processed_count += 1
            
            # Umidade
            db.create_reading(sensor_ids['S_HUMIDITY'], timestamp, record['humidity'])
            processed_count += 1
            
            # Luminosidade
            db.create_reading(sensor_ids['S_LIGHT'], timestamp, record['luminosity'])
            processed_count += 1
            
            # Vibração
            vibration = (record['accel_x']**2 + record['accel_y']**2 + record['accel_z']**2)**0.5
            db.create_reading(sensor_ids['S_VIBRATION'], timestamp, vibration)
            processed_count += 1
        
        print(f"✅ {processed_count} registros carregados no SQLite")
        
        # Passo 4: Treinamento de modelos ML
        print_step(4, "Treinando modelos de Machine Learning")
        
        # Adapta ML para SQLite
        class SQLiteMLTrainer(MLModelTrainer):
            def __init__(self, db_connection):
                self.db = db_connection
                self.models = {}
                self.feature_columns = ['lag1', 'lag2', 'roll3', 'hour']
        
        trainer = SQLiteMLTrainer(db)
        sensors = ['S_TEMP', 'S_HUMIDITY', 'S_LIGHT', 'S_VIBRATION']
        
        print("Treinando modelos para sensores...")
        training_results = {}
        
        for sensor in sensors:
            try:
                # Recupera dados do sensor
                sensor_data = db.get_sensor_readings_by_name(sensor, 1000)
                if sensor_data.empty:
                    print(f"⚠️  Nenhum dado para {sensor}")
                    continue
                
                # Prepara dados para ML
                df = sensor_data.sort_values('ts').reset_index(drop=True)
                df['lag1'] = df['value'].shift(1)
                df['lag2'] = df['value'].shift(2)
                df['roll3'] = df['value'].rolling(3).mean()
                df['hour'] = df['ts'].dt.hour
                df = df.dropna()
                
                if len(df) < 10:
                    print(f"⚠️  Dados insuficientes para {sensor}")
                    continue
                
                # Split e treino
                from sklearn.linear_model import LinearRegression
                from sklearn.metrics import mean_absolute_error, r2_score
                
                X = df[['lag1', 'lag2', 'roll3', 'hour']]
                y = df['value']
                
                split_idx = int(len(X) * 0.8)
                X_train, X_test = X[:split_idx], X[split_idx:]
                y_train, y_test = y[:split_idx], y[split_idx:]
                
                model = LinearRegression()
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                training_results[f"{sensor}_linear"] = {
                    'model_type': 'linear',
                    'sensor_name': sensor,
                    'mae': float(mae),
                    'r2': float(r2),
                    'train_samples': len(X_train),
                    'test_samples': len(X_test)
                }
                
                trainer.models[f"{sensor}_linear"] = model
                print(f"✅ {sensor}: MAE={mae:.3f}, R²={r2:.3f}")
                
            except Exception as e:
                print(f"❌ Erro ao treinar {sensor}: {e}")
        
        # Salva resultados
        with open("training_results.json", 'w') as f:
            json.dump(training_results, f, indent=2, default=str)
        
        print("✅ Modelos treinados e salvos")
        
        # Passo 5: Predições em tempo real
        print_step(5, "Executando predições ML")
        
        # Adapta predictor para SQLite
        class SQLiteMLPredictor(MLPredictor):
            def __init__(self, db_connection):
                self.db = db_connection
                self.models = trainer.models
                self.feature_columns = ['lag1', 'lag2', 'roll3', 'hour']
        
        predictor = SQLiteMLPredictor(db)
        
        print("Gerando predições para sensores...")
        predictions = {}
        
        for sensor in sensors:
            try:
                # Recupera dados recentes
                recent_data = db.get_sensor_readings_by_name(sensor, 5)
                if recent_data.empty:
                    continue
                
                # Prepara features
                df = recent_data.sort_values('ts').reset_index(drop=True)
                df['lag1'] = df['value'].shift(1)
                df['lag2'] = df['value'].shift(2)
                df['roll3'] = df['value'].rolling(3).mean()
                df['hour'] = df['ts'].dt.hour
                df = df.dropna()
                
                if len(df) == 0:
                    continue
                
                # Predição
                model_key = f"{sensor}_linear"
                if model_key in predictor.models:
                    model = predictor.models[model_key]
                    features = df[['lag1', 'lag2', 'roll3', 'hour']].tail(1)
                    prediction = model.predict(features)[0]
                    
                    # Salva predição
                    sensor_id = db.get_sensor_id_by_name(sensor)
                    if sensor_id:
                        db.create_prediction(sensor_id, prediction, 0.8, "v1.0")
                    
                    predictions[sensor] = {
                        'predicted_value': float(prediction),
                        'confidence': 0.8,
                        'model_used': model_key
                    }
                    
                    print(f"✅ {sensor}: {prediction:.2f}")
                
            except Exception as e:
                print(f"❌ Erro na predição de {sensor}: {e}")
        
        # Passo 6: Detecção de anomalias
        print_step(6, "Detectando anomalias")
        
        all_anomalies = []
        for sensor in sensors:
            try:
                recent_data = db.get_sensor_readings_by_name(sensor, 10)
                if recent_data.empty:
                    continue
                
                # Simula detecção de anomalias baseada em thresholds
                last_value = recent_data['value'].iloc[0]
                
                thresholds = {
                    'S_TEMP': 35.0,
                    'S_HUMIDITY': 80.0,
                    'S_VIBRATION': 2000.0,
                    'S_LIGHT': 10.0
                }
                
                threshold = thresholds.get(sensor)
                if threshold and last_value > threshold:
                    anomaly = {
                        'sensor_name': sensor,
                        'actual_value': last_value,
                        'threshold': threshold,
                        'severity': 'high' if last_value > threshold * 1.5 else 'medium'
                    }
                    all_anomalies.append(anomaly)
                    
                    # Cria alerta no banco
                    sensor_id = db.get_sensor_id_by_name(sensor)
                    if sensor_id:
                        db.create_alert(
                            sensor_id, 'threshold', threshold, last_value,
                            f'Valor {last_value:.2f} excede threshold {threshold}',
                            anomaly['severity']
                        )
            
            except Exception as e:
                print(f"❌ Erro na detecção de anomalias para {sensor}: {e}")
        
        if all_anomalies:
            print(f"⚠️  {len(all_anomalies)} anomalias detectadas:")
            for anomaly in all_anomalies:
                print(f"  - {anomaly['sensor_name']}: {anomaly['actual_value']:.2f} > {anomaly['threshold']}")
        else:
            print("✅ Nenhuma anomalia detectada")
        
        # Passo 7: Relatório final
        print_step(7, "Gerando relatório final")
        
        # Estatísticas do banco
        db_stats = db.get_database_stats()
        print(f"Total de assets: {db_stats.get('asset_count', 0)}")
        print(f"Total de sensores: {db_stats.get('sensor_count', 0)}")
        print(f"Total de leituras: {db_stats.get('reading_count', 0)}")
        print(f"Total de alertas: {db_stats.get('alert_count', 0)}")
        print(f"Total de predições: {db_stats.get('prediction_count', 0)}")
        
        # Relatório de predições
        prediction_report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'predictions': predictions,
            'anomalies': all_anomalies,
            'database_stats': db_stats
        }
        
        with open('prediction_report.json', 'w') as f:
            json.dump(prediction_report, f, indent=2, default=str)
        
        print("✅ Relatório de predições salvo em prediction_report.json")
        
        # Passo 8: Instruções para dashboard
        print_step(8, "Próximos passos")
        
        print("""
🚀 Para visualizar o dashboard:
    streamlit run dashboard/app_sqlite.py

📊 Para acessar o banco SQLite:
    sqlite3 industrial_iot.db

📁 Arquivos gerados:
    - industrial_iot.db (banco SQLite)
    - sensor_data.json (dados do ESP32)
    - training_results.json (resultados do ML)
    - prediction_report.json (relatório de predições)
        """)
        
        print_header("PIPELINE EXECUTADO COM SUCESSO!")
        print("Sistema integrado funcionando com SQLite")
        print("Todos os componentes conectados: ESP32 → SQLite → ML → Dashboard")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("Verifique se as dependências estão instaladas")
        return 1
    
    finally:
        try:
            db.close()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
