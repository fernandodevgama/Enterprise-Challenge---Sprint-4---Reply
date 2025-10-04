#!/usr/bin/env python3
"""
Simulador ESP32 para coleta de dados industriais
Baseado no código Arduino da Entrega 2, adaptado para Python
"""

import time
import random
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import numpy as np

class ESP32Simulator:
    """Simulador do ESP32 com sensores industriais"""
    
    def __init__(self):
        self.sensors = {
            'DHT22': {'temp': 25.0, 'humidity': 55.0},
            'MPU6050': {'ax': 0, 'ay': 0, 'az': 1000, 'gx': 0, 'gy': 0, 'gz': 0},
            'LDR': {'light': 50.0}
        }
        self.running = False
        self.data_buffer = []
        
    def initialize_sensors(self):
        """Inicializa os sensores simulados"""
        print("=== Sistema de Monitoramento Industrial ===")
        print("Inicializando sensores...")
        print("DHT22 inicializado")
        print("MPU6050 inicializado com sucesso")
        print("Sistema pronto para coleta de dados!")
        print("Timestamp,Temperatura(C),Umidade(%),Luminosidade,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z")
        
    def read_dht22(self) -> Tuple[float, float]:
        """Simula leitura do sensor DHT22 (temperatura e umidade)"""
        # Simula variação realística com sazonalidade
        hour = datetime.now().hour
        temp_base = 25 + 5 * np.sin(2 * np.pi * hour / 24)
        humidity_base = 55 - 10 * np.sin(2 * np.pi * hour / 24)
        
        # Adiciona ruído gaussiano
        temp = temp_base + random.gauss(0, 0.5)
        humidity = humidity_base + random.gauss(0, 2)
        
        # Verifica se as leituras são válidas
        if temp < -40 or temp > 80:
            temp = 25.0
        if humidity < 0 or humidity > 100:
            humidity = 55.0
            
        return temp, humidity
    
    def read_mpu6050(self) -> Dict[str, int]:
        """Simula leitura do sensor MPU6050 (acelerômetro e giroscópio)"""
        # Simula vibração normal com ocasionais picos
        if random.random() < 0.05:  # 5% chance de vibração excessiva
            ax = random.randint(-500, 500)
            ay = random.randint(-500, 500)
            az = random.randint(800, 1200)
        else:
            ax = random.randint(-50, 50)
            ay = random.randint(-50, 50)
            az = random.randint(950, 1050)
            
        gx = random.randint(-100, 100)
        gy = random.randint(-100, 100)
        gz = random.randint(-100, 100)
        
        return {'ax': ax, 'ay': ay, 'az': az, 'gx': gx, 'gy': gy, 'gz': gz}
    
    def read_ldr(self) -> float:
        """Simula leitura do fotoresistor (luminosidade)"""
        # Simula variação dia/noite
        hour = datetime.now().hour
        if 6 <= hour <= 18:  # Dia
            light = 70 + random.gauss(0, 10)
        else:  # Noite
            light = 10 + random.gauss(0, 5)
            
        return max(0, min(100, light))
    
    def collect_data(self) -> Dict:
        """Coleta dados de todos os sensores"""
        timestamp = int(time.time())
        
        # Leitura DHT22
        temp, humidity = self.read_dht22()
        
        # Leitura MPU6050
        mpu_data = self.read_mpu6050()
        
        # Leitura LDR
        light = self.read_ldr()
        
        # Monta dados formatados
        data = {
            'timestamp': timestamp,
            'temperature': round(temp, 2),
            'humidity': round(humidity, 2),
            'luminosity': round(light, 2),
            'accel_x': mpu_data['ax'],
            'accel_y': mpu_data['ay'],
            'accel_z': mpu_data['az'],
            'gyro_x': mpu_data['gx'],
            'gyro_y': mpu_data['gy'],
            'gyro_z': mpu_data['gz'],
            'datetime': datetime.now(timezone.utc).isoformat()
        }
        
        return data
    
    def analyze_data(self, data: Dict) -> List[str]:
        """Analisa dados para detecção de anomalias"""
        alerts = []
        
        if data['temperature'] > 35.0:
            alerts.append("⚠️  ALERTA: Temperatura elevada!")
            
        if data['humidity'] > 80.0:
            alerts.append("⚠️  ALERTA: Umidade muito alta!")
            
        if data['luminosity'] < 10.0:
            alerts.append("⚠️  ALERTA: Luminosidade muito baixa!")
            
        # Detecção de vibração excessiva
        vibration = np.sqrt(data['accel_x']**2 + data['accel_y']**2 + data['accel_z']**2)
        if vibration > 2000:
            alerts.append("⚠️  ALERTA: Vibração excessiva detectada!")
            
        return alerts
    
    def display_data(self, data: Dict, alerts: List[str]):
        """Exibe dados formatados no console"""
        print(f"{data['timestamp']},{data['temperature']},{data['humidity']},{data['luminosity']},{data['accel_x']},{data['accel_y']},{data['accel_z']},{data['gyro_x']},{data['gyro_y']},{data['gyro_z']}")
        
        print("--- Leitura dos Sensores ---")
        print("Ambiente:")
        print(f"  Temperatura: {data['temperature']:.2f}°C")
        print(f"  Umidade: {data['humidity']:.2f}%")
        print(f"  Luminosidade: {data['luminosity']:.2f}%")
        
        print("Vibração/Movimento (MPU6050):")
        print(f"  Aceleração (mg): X={data['accel_x']}, Y={data['accel_y']}, Z={data['accel_z']}")
        print(f"  Giroscópio (mdps): X={data['gyro_x']}, Y={data['gyro_y']}, Z={data['gyro_z']}")
        
        for alert in alerts:
            print(alert)
        print("================================")
    
    def run_simulation(self, duration_minutes: int = 10, interval_seconds: int = 2):
        """Executa simulação por tempo determinado"""
        self.initialize_sensors()
        self.running = True
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        print(f"Iniciando simulação por {duration_minutes} minutos...")
        
        while self.running and time.time() < end_time:
            # Coleta dados
            data = self.collect_data()
            alerts = self.analyze_data(data)
            
            # Armazena no buffer
            self.data_buffer.append(data)
            
            # Exibe dados
            self.display_data(data, alerts)
            
            # Aguarda próximo ciclo
            time.sleep(interval_seconds)
        
        print(f"Simulação finalizada. {len(self.data_buffer)} registros coletados.")
        return self.data_buffer
    
    def save_data(self, filename: str = "sensor_data.json"):
        """Salva dados coletados em arquivo JSON"""
        with open(filename, 'w') as f:
            json.dump(self.data_buffer, f, indent=2)
        print(f"Dados salvos em {filename}")
    
    def get_data_summary(self) -> Dict:
        """Retorna resumo dos dados coletados"""
        if not self.data_buffer:
            return {}
            
        df_data = []
        for record in self.data_buffer:
            df_data.append({
                'timestamp': record['timestamp'],
                'temperature': record['temperature'],
                'humidity': record['humidity'],
                'luminosity': record['luminosity'],
                'vibration': np.sqrt(record['accel_x']**2 + record['accel_y']**2 + record['accel_z']**2)
            })
        
        import pandas as pd
        df = pd.DataFrame(df_data)
        
        summary = {
            'total_records': len(df),
            'temperature': {
                'mean': df['temperature'].mean(),
                'std': df['temperature'].std(),
                'min': df['temperature'].min(),
                'max': df['temperature'].max()
            },
            'humidity': {
                'mean': df['humidity'].mean(),
                'std': df['humidity'].std(),
                'min': df['humidity'].min(),
                'max': df['humidity'].max()
            },
            'luminosity': {
                'mean': df['luminosity'].mean(),
                'std': df['luminosity'].std(),
                'min': df['luminosity'].min(),
                'max': df['luminosity'].max()
            },
            'vibration': {
                'mean': df['vibration'].mean(),
                'std': df['vibration'].std(),
                'min': df['vibration'].min(),
                'max': df['vibration'].max()
            }
        }
        
        return summary

if __name__ == "__main__":
    # Exemplo de uso
    simulator = ESP32Simulator()
    
    # Executa simulação por 5 minutos
    data = simulator.run_simulation(duration_minutes=5, interval_seconds=2)
    
    # Salva dados
    simulator.save_data("sensor_data.json")
    
    # Exibe resumo
    summary = simulator.get_data_summary()
    print("\n=== Resumo dos Dados ===")
    print(json.dumps(summary, indent=2))
