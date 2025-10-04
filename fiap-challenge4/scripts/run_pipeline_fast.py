#!/usr/bin/env python3
"""
Script rápido para demonstração - 30 segundos
Versão otimizada para apresentação
"""

import sys
import os
import json
import time
from datetime import datetime, timezone

# Adiciona diretórios ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ingest.esp32_simulator import ESP32Simulator
from db.sqlite_connection import SQLiteConnection

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
    """Executa pipeline rápido para demonstração"""
    
    print_header("SISTEMA INTEGRADO - DEMONSTRAÇÃO RÁPIDA")
    print("Hermes Reply Challenge - Sprint 4")
    print("Versão rápida: 30 segundos para demonstração")
    
    try:
        # Passo 1: Simulação ESP32 rápida
        print_step(1, "Simulando coleta de dados do ESP32 (30 segundos)")
        
        simulator = ESP32Simulator()
        print("Iniciando simulação rápida por 30 segundos...")
        esp32_data = simulator.run_simulation(duration_minutes=0.5, interval_seconds=2)
        
        print(f"✅ Coletados {len(esp32_data)} registros do ESP32")
        simulator.save_data("sensor_data.json")
        
        # Passo 2: Configuração do banco SQLite
        print_step(2, "Configurando banco SQLite")
        
        db = SQLiteConnection("industrial_iot.db")
        print("✅ Conexão SQLite estabelecida")
        
        # Passo 3: Ingestão de dados
        print_step(3, "Ingerindo dados no banco SQLite")
        
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
            print(f"Sensor {sensor_config['name']} criado")
        
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
        
        # Passo 4: ML rápido
        print_step(4, "Treinando modelos ML (versão rápida)")
        
        # Treina apenas para temperatura
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import mean_absolute_error, r2_score
            import pandas as pd
            import numpy as np
            
            # Recupera dados de temperatura
            temp_data = db.get_sensor_readings_by_name('S_TEMP', 100)
            if not temp_data.empty:
                df = temp_data.sort_values('ts').reset_index(drop=True)
                df['lag1'] = df['value'].shift(1)
                df['lag2'] = df['value'].shift(2)
                df['roll3'] = df['value'].rolling(3).mean()
                df['hour'] = df['ts'].dt.hour
                df = df.dropna()
                
                if len(df) >= 10:
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
                    
                    print(f"✅ Modelo treinado: MAE={mae:.3f}, R²={r2:.3f}")
                    
                    # Salva modelo
                    import joblib
                    os.makedirs("models", exist_ok=True)
                    joblib.dump(model, "models/S_TEMP_linear_model.pkl")
                    
                    # Cria predição
                    sensor_id = db.get_sensor_id_by_name('S_TEMP')
                    if sensor_id:
                        prediction = model.predict(X.tail(1))[0]
                        db.create_prediction(sensor_id, prediction, 0.8, "v1.0")
                        print(f"✅ Predição criada: {prediction:.2f}°C")
                else:
                    print("⚠️  Dados insuficientes para ML")
            else:
                print("⚠️  Nenhum dado de temperatura encontrado")
                
        except Exception as e:
            print(f"⚠️  Erro no ML: {e}")
        
        # Passo 5: Alertas
        print_step(5, "Criando alertas de exemplo")
        
        # Cria alguns alertas baseados nos dados
        alerts_created = 0
        for sensor_name, sensor_id in sensor_ids.items():
            try:
                recent_data = db.get_sensor_readings_by_name(sensor_name, 1)
                if not recent_data.empty:
                    value = recent_data['value'].iloc[0]
                    
                    # Thresholds
                    thresholds = {
                        'S_TEMP': 35.0,
                        'S_HUMIDITY': 80.0,
                        'S_VIBRATION': 2000.0,
                        'S_LIGHT': 10.0
                    }
                    
                    threshold = thresholds.get(sensor_name)
                    if threshold and value > threshold:
                        db.create_alert(
                            sensor_id, 'threshold', threshold, value,
                            f'Valor {value:.2f} excede threshold {threshold}',
                            'high'
                        )
                        alerts_created += 1
                        print(f"⚠️  Alerta criado para {sensor_name}: {value:.2f}")
            except Exception as e:
                print(f"Erro ao criar alerta para {sensor_name}: {e}")
        
        print(f"✅ {alerts_created} alertas criados")
        
        # Passo 6: Relatório final
        print_step(6, "Relatório final")
        
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
            'database_stats': db_stats,
            'sensors': list(sensor_ids.keys()),
            'total_readings': processed_count
        }
        
        with open('prediction_report.json', 'w') as f:
            json.dump(prediction_report, f, indent=2, default=str)
        
        print("✅ Relatório salvo em prediction_report.json")
        
        # Instruções
        print_step(7, "Próximos passos")
        
        print("""
🚀 Para visualizar o dashboard:
    streamlit run dashboard/app_sqlite.py

📊 Para acessar o banco SQLite:
    sqlite3 industrial_iot.db

📁 Arquivos gerados:
    - industrial_iot.db (banco SQLite)
    - sensor_data.json (dados do ESP32)
    - prediction_report.json (relatório)
    - models/S_TEMP_linear_model.pkl (modelo ML)
        """)
        
        print_header("DEMONSTRAÇÃO RÁPIDA CONCLUÍDA!")
        print("Sistema pronto em 30 segundos!")
        print("Execute: streamlit run dashboard/app_sqlite.py")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
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
