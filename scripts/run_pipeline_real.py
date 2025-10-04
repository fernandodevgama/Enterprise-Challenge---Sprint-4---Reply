#!/usr/bin/env python3
"""
Pipeline de dados para PostgreSQL - Sistema IoT Industrial
Coleta dados do ESP32 simulator e armazena no banco PostgreSQL
Author: HermesReply Challenge - Grupo 5
Version: 1.0
Date: 2024-01-20
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
import pandas as pd

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.esp32_simulator import ESP32Simulator
from db.connection import DatabaseConnection
from ml.model_trainer import MLModelTrainer

def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_step(step, text):
    """Imprime passo formatado"""
    print(f"\n[{step}] {text}")

def collect_sensor_data(duration_minutes=5, interval_seconds=10):
    """Coleta dados dos sensores por um período"""
    print(f"Coletando dados por {duration_minutes} minutos (intervalo: {interval_seconds}s)...")
    
    # Inicializar simulador
    simulator = ESP32Simulator()
    collected_data = []
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    sample_count = 0
    while time.time() < end_time:
        # Coletar dados de todos os sensores
        timestamp = datetime.now()
        
        sensors_data = {
            'S_TEMP': simulator.read_dht22_temperature(),
            'S_HUMIDITY': simulator.read_dht22_humidity(),
            'S_VIBRATION': simulator.read_vibration(),
            'S_LIGHT': simulator.read_light_sensor()
        }
        
        for sensor_name, value in sensors_data.items():
            collected_data.append({
                'sensor_name': sensor_name,
                'timestamp': timestamp,
                'value': value
            })
        
        sample_count += 1
        print(f"  Amostra {sample_count}: {len(sensors_data)} sensores coletados")
        
        time.sleep(interval_seconds)
    
    print(f"✅ Coleta concluída! {len(collected_data)} leituras coletadas")
    return collected_data

def store_data_in_database(data, db_connection):
    """Armazena dados no banco PostgreSQL"""
    print("Armazenando dados no banco PostgreSQL...")
    
    try:
        # Buscar IDs dos sensores
        sensor_ids = {}
        for sensor_name in ['S_TEMP', 'S_HUMIDITY', 'S_VIBRATION', 'S_LIGHT']:
            result = db_connection.execute_query(
                "SELECT id FROM sensor WHERE name = %s", 
                (sensor_name,)
            )
            if result:
                sensor_ids[sensor_name] = result[0][0]
            else:
                print(f"❌ Sensor {sensor_name} não encontrado no banco!")
                return False
        
        # Inserir leituras
        inserted_count = 0
        for reading in data:
            sensor_id = sensor_ids.get(reading['sensor_name'])
            if sensor_id:
                db_connection.execute_query(
                    "INSERT INTO reading (sensor_id, ts, value) VALUES (%s, %s, %s)",
                    (sensor_id, reading['timestamp'], reading['value'])
                )
                inserted_count += 1
        
        print(f"✅ {inserted_count} leituras inseridas no banco!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao armazenar dados: {e}")
        return False

def generate_alerts(db_connection):
    """Gera alertas baseados nos dados recentes"""
    print("Gerando alertas baseados em thresholds...")
    
    try:
        # Definir thresholds
        thresholds = {
            'S_TEMP': {'min': 20, 'max': 30, 'unit': '°C'},
            'S_HUMIDITY': {'min': 40, 'max': 70, 'unit': '%'},
            'S_VIBRATION': {'min': 0, 'max': 1500, 'unit': 'mg'},
            'S_LIGHT': {'min': 20, 'max': 80, 'unit': '%'}
        }
        
        alerts_generated = 0
        
        for sensor_name, threshold in thresholds.items():
            # Buscar leituras recentes
            query = """
            SELECT r.id, r.value, s.id as sensor_id
            FROM reading r
            JOIN sensor s ON r.sensor_id = s.id
            WHERE s.name = %s 
            AND r.ts >= NOW() - INTERVAL '1 hour'
            ORDER BY r.ts DESC
            LIMIT 10
            """
            
            result = db_connection.execute_query(query, (sensor_name,))
            
            if result:
                for reading_id, value, sensor_id in result:
                    alert_type = None
                    severity = 'low'
                    
                    if value < threshold['min']:
                        alert_type = 'LOW_VALUE'
                        severity = 'medium' if value < threshold['min'] * 0.8 else 'low'
                    elif value > threshold['max']:
                        alert_type = 'HIGH_VALUE'
                        severity = 'high' if value > threshold['max'] * 1.2 else 'medium'
                    
                    if alert_type:
                        message = f"{sensor_name}: {value:.1f}{threshold['unit']} (Limite: {threshold['min']}-{threshold['max']})"
                        
                        db_connection.execute_query("""
                            INSERT INTO alert (sensor_id, alert_type, threshold_value, actual_value, message, severity)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (sensor_id, alert_type, threshold['max'] if 'HIGH' in alert_type else threshold['min'], 
                              value, message, severity))
                        
                        alerts_generated += 1
        
        print(f"✅ {alerts_generated} alertas gerados!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar alertas: {e}")
        return False

def train_ml_models(db_connection):
    """Treina modelos de ML com os dados coletados"""
    print("Treinando modelos de Machine Learning...")
    
    try:
        trainer = MLModelTrainer(db_connection)
        
        # Treinar modelos para sensores com dados suficientes
        sensors_to_train = ['S_TEMP', 'S_HUMIDITY', 'S_VIBRATION', 'S_LIGHT']
        results = {}
        
        for sensor in sensors_to_train:
            try:
                # Verificar se há dados suficientes
                query = """
                SELECT COUNT(*) FROM reading r
                JOIN sensor s ON r.sensor_id = s.id
                WHERE s.name = %s
                """
                result = db_connection.execute_query(query, (sensor,))
                count = result[0][0] if result else 0
                
                if count >= 20:  # Mínimo de dados para treino
                    print(f"  Treinando modelo para {sensor} ({count} amostras)...")
                    result = trainer.train_linear_model(sensor)
                    results[sensor] = result
                    print(f"    MAE: {result.get('mae', 'N/A'):.4f}, R²: {result.get('r2', 'N/A'):.4f}")
                else:
                    print(f"  {sensor}: Dados insuficientes ({count} amostras)")
                    
            except Exception as e:
                print(f"  ❌ Erro ao treinar {sensor}: {e}")
        
        # Salvar resultados
        if results:
            results_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'training_results.json')
            os.makedirs(os.path.dirname(results_path), exist_ok=True)
            
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"✅ Resultados salvos em: {results_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no treinamento ML: {e}")
        return False

def generate_summary_report(db_connection):
    """Gera relatório resumo do pipeline"""
    print("Gerando relatório resumo...")
    
    try:
        # Estatísticas gerais
        stats = {}
        
        # Contagem de leituras por sensor
        query = """
        SELECT s.name, COUNT(r.id) as reading_count,
               AVG(r.value) as avg_value,
               MIN(r.value) as min_value,
               MAX(r.value) as max_value
        FROM sensor s
        LEFT JOIN reading r ON s.id = r.sensor_id
        WHERE r.ts >= NOW() - INTERVAL '1 day'
        GROUP BY s.name
        """
        
        result = db_connection.execute_query(query)
        if result:
            for name, count, avg, min_val, max_val in result:
                stats[name] = {
                    'readings': count,
                    'average': float(avg) if avg else 0,
                    'minimum': float(min_val) if min_val else 0,
                    'maximum': float(max_val) if max_val else 0
                }
        
        # Contagem de alertas
        alert_query = "SELECT severity, COUNT(*) FROM alert GROUP BY severity"
        alert_result = db_connection.execute_query(alert_query)
        alert_stats = dict(alert_result) if alert_result else {}
        
        # Criar relatório
        report = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_status': 'completed',
            'sensor_statistics': stats,
            'alert_summary': alert_stats,
            'total_sensors': len(stats),
            'total_alerts': sum(alert_stats.values())
        }
        
        # Salvar relatório
        report_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'pipeline_report.json')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Relatório salvo em: {report_path}")
        
        # Exibir resumo
        print("\n📊 RESUMO DO PIPELINE:")
        print(f"  • Sensores processados: {len(stats)}")
        print(f"  • Total de leituras: {sum(s['readings'] for s in stats.values())}")
        print(f"  • Total de alertas: {sum(alert_stats.values())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")
        return False

def main():
    """Função principal do pipeline"""
    print_header("🏭 PIPELINE DE DADOS POSTGRESQL")
    print("Sistema IoT Industrial - HermesReply Challenge")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Conectar ao banco
    print_step("1/6", "Conectando ao banco PostgreSQL...")
    
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'industrial_iot'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        db = DatabaseConnection(db_config)
        print("✅ Conectado ao PostgreSQL!")
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        print("\nExecute primeiro: python scripts/setup_database.py")
        return False
    
    try:
        # Passo 2: Coletar dados
        print_step("2/6", "Coletando dados dos sensores...")
        sensor_data = collect_sensor_data(duration_minutes=2, interval_seconds=5)
        
        # Passo 3: Armazenar no banco
        print_step("3/6", "Armazenando dados no banco...")
        if not store_data_in_database(sensor_data, db):
            return False
        
        # Passo 4: Gerar alertas
        print_step("4/6", "Gerando alertas...")
        if not generate_alerts(db):
            return False
        
        # Passo 5: Treinar modelos ML
        print_step("5/6", "Treinando modelos de ML...")
        if not train_ml_models(db):
            return False
        
        # Passo 6: Gerar relatório
        print_step("6/6", "Gerando relatório final...")
        if not generate_summary_report(db):
            return False
        
        # Sucesso
        print_header("✅ PIPELINE CONCLUÍDO COM SUCESSO!")
        print("\n🎉 Dados coletados e processados!")
        print("\n📋 Próximos passos:")
        print("1. Inicie o dashboard: streamlit run dashboard/app_real.py")
        print("2. Acesse: http://localhost:8501")
        print("3. Visualize os dados em tempo real!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no pipeline: {e}")
        return False
        
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)