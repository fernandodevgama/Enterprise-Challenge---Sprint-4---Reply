#!/usr/bin/env python3
"""
Conexão SQLite para demonstração sem PostgreSQL
Alternativa para sistemas sem PostgreSQL instalado
"""

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import pandas as pd

class SQLiteConnection:
    """Conexão SQLite para demonstração"""
    
    def __init__(self, db_path: str = "industrial_iot.db"):
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Estabelece conexão com SQLite"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Para acessar colunas por nome
            print(f"Conexão SQLite estabelecida: {self.db_path}")
        except Exception as e:
            print(f"Erro ao conectar SQLite: {e}")
            raise
    
    def close(self):
        """Fecha conexão"""
        if self.connection:
            self.connection.close()
            print("Conexão SQLite fechada.")
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Executa query SQL"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return []
        except Exception as e:
            print(f"Erro ao executar query: {e}")
            self.connection.rollback()
            raise
    
    def create_tables(self):
        """Cria tabelas do sistema"""
        print("Criando tabelas SQLite...")
        
        # Tabela de Assets
        self.execute_query("""
        CREATE TABLE IF NOT EXISTS asset (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de Sensores
        self.execute_query("""
        CREATE TABLE IF NOT EXISTS sensor (
            id TEXT PRIMARY KEY,
            asset_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            unit TEXT NOT NULL,
            min_value REAL,
            max_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES asset (id)
        )
        """)
        
        # Tabela de Leituras
        self.execute_query("""
        CREATE TABLE IF NOT EXISTS reading (
            id TEXT PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            ts TIMESTAMP NOT NULL,
            value REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES sensor (id)
        )
        """)
        
        # Tabela de Alertas
        self.execute_query("""
        CREATE TABLE IF NOT EXISTS alert (
            id TEXT PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            threshold_value REAL,
            actual_value REAL,
            message TEXT,
            severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            acknowledged BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES sensor (id)
        )
        """)
        
        # Tabela de Predições
        self.execute_query("""
        CREATE TABLE IF NOT EXISTS prediction (
            id TEXT PRIMARY KEY,
            sensor_id TEXT NOT NULL,
            predicted_value REAL NOT NULL,
            confidence REAL,
            model_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sensor_id) REFERENCES sensor (id)
        )
        """)
        
        # Índices
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_reading_sensor_ts ON reading(sensor_id, ts)")
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_reading_ts ON reading(ts)")
        
        # Dados iniciais
        self._insert_initial_data()
        
        print("✅ Tabelas SQLite criadas com sucesso")
    
    def _insert_initial_data(self):
        """Insere dados iniciais"""
        # Verifica se já existem dados
        result = self.execute_query("SELECT COUNT(*) FROM asset")
        if result[0][0] > 0:
            return
        
        # Asset principal
        asset_id = str(uuid.uuid4())
        self.execute_query(
            "INSERT INTO asset (id, name, location) VALUES (?, ?, ?)",
            (asset_id, 'Linha de Produção Principal', 'Setor A - Fábrica')
        )
        
        # Sensores
        sensors = [
            ('S_TEMP', 'temperature', '°C', -40.0, 80.0),
            ('S_HUMIDITY', 'humidity', '%', 0.0, 100.0),
            ('S_LIGHT', 'luminosity', '%', 0.0, 100.0),
            ('S_VIBRATION', 'vibration', 'mg', 0.0, 5000.0)
        ]
        
        for name, sensor_type, unit, min_val, max_val in sensors:
            sensor_id = str(uuid.uuid4())
            self.execute_query(
                """INSERT INTO sensor (id, asset_id, name, type, unit, min_value, max_value) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sensor_id, asset_id, name, sensor_type, unit, min_val, max_val)
            )
    
    def create_asset(self, asset_data: Dict) -> str:
        """Cria novo asset"""
        asset_id = str(uuid.uuid4())
        query = "INSERT INTO asset (id, name, location) VALUES (?, ?, ?)"
        self.execute_query(query, (asset_id, asset_data['name'], asset_data['location']))
        return asset_id
    
    def create_sensor(self, asset_id: str, sensor_data: Dict) -> str:
        """Cria novo sensor"""
        sensor_id = str(uuid.uuid4())
        query = """INSERT INTO sensor (id, asset_id, name, type, unit, min_value, max_value) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)"""
        self.execute_query(query, (
            sensor_id, asset_id, sensor_data['name'], sensor_data['type'], 
            sensor_data['unit'], sensor_data['min_value'], sensor_data['max_value']
        ))
        return sensor_id
    
    def create_reading(self, sensor_id: str, timestamp: datetime, value: float) -> str:
        """Cria nova leitura"""
        reading_id = str(uuid.uuid4())
        query = "INSERT INTO reading (id, sensor_id, ts, value) VALUES (?, ?, ?, ?)"
        self.execute_query(query, (reading_id, sensor_id, timestamp, value))
        return reading_id
    
    def create_alert(self, sensor_id: str, alert_type: str, threshold_value: float, 
                    actual_value: float, message: str, severity: str) -> str:
        """Cria novo alerta"""
        alert_id = str(uuid.uuid4())
        query = """INSERT INTO alert (id, sensor_id, alert_type, threshold_value, 
                   actual_value, message, severity) VALUES (?, ?, ?, ?, ?, ?, ?)"""
        self.execute_query(query, (alert_id, sensor_id, alert_type, threshold_value, 
                                  actual_value, message, severity))
        return alert_id
    
    def create_prediction(self, sensor_id: str, predicted_value: float, 
                         confidence: float, model_version: str) -> str:
        """Cria nova predição"""
        prediction_id = str(uuid.uuid4())
        query = """INSERT INTO prediction (id, sensor_id, predicted_value, 
                   confidence, model_version) VALUES (?, ?, ?, ?, ?)"""
        self.execute_query(query, (prediction_id, sensor_id, predicted_value, 
                                  confidence, model_version))
        return prediction_id
    
    def get_sensor_readings(self, sensor_id: str, limit: int = 100) -> pd.DataFrame:
        """Recupera leituras de um sensor"""
        query = """
        SELECT ts, value
        FROM reading
        WHERE sensor_id = ?
        ORDER BY ts DESC
        LIMIT ?
        """
        results = self.execute_query(query, (sensor_id, limit))
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['ts', 'value'])
        df['ts'] = pd.to_datetime(df['ts'])
        return df
    
    def get_sensor_readings_by_name(self, sensor_name: str, limit: int = 100) -> pd.DataFrame:
        """Recupera leituras por nome do sensor"""
        query = """
        SELECT r.ts, r.value
        FROM reading r
        JOIN sensor s ON r.sensor_id = s.id
        WHERE s.name = ?
        ORDER BY r.ts DESC
        LIMIT ?
        """
        results = self.execute_query(query, (sensor_name, limit))
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['ts', 'value'])
        df['ts'] = pd.to_datetime(df['ts'])
        return df
    
    def get_latest_readings(self) -> pd.DataFrame:
        """Recupera últimas leituras de cada sensor"""
        query = """
        WITH latest_readings AS (
            SELECT sensor_id, MAX(ts) as latest_ts
            FROM reading
            GROUP BY sensor_id
        )
        SELECT r.ts, r.value, s.name as sensor_name, s.type, s.unit
        FROM reading r
        JOIN latest_readings lr ON r.sensor_id = lr.sensor_id AND r.ts = lr.latest_ts
        JOIN sensor s ON r.sensor_id = s.id
        ORDER BY s.name
        """
        
        results = self.execute_query(query)
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['ts', 'value', 'sensor_name', 'type', 'unit'])
        df['ts'] = pd.to_datetime(df['ts'])
        return df
    
    def get_sensor_id_by_name(self, sensor_name: str) -> Optional[str]:
        """Recupera ID do sensor por nome"""
        query = "SELECT id FROM sensor WHERE name = ?"
        results = self.execute_query(query, (sensor_name,))
        return results[0][0] if results else None
    
    def get_database_stats(self) -> Dict:
        """Retorna estatísticas do banco"""
        stats = {}
        
        # Contagem de registros
        tables = ['asset', 'sensor', 'reading', 'alert', 'prediction']
        for table in tables:
            query = f"SELECT COUNT(*) FROM {table}"
            result = self.execute_query(query)
            stats[f'{table}_count'] = result[0][0] if result else 0
        
        # Última leitura
        query = "SELECT MAX(ts) FROM reading"
        result = self.execute_query(query)
        stats['last_reading'] = result[0][0] if result and result[0][0] else None
        
        return stats
    
    def get_active_alerts(self) -> pd.DataFrame:
        """Recupera alertas ativos"""
        query = """
        SELECT a.*, s.name as sensor_name, s.type as sensor_type
        FROM alert a
        JOIN sensor s ON a.sensor_id = s.id
        WHERE a.acknowledged = 0
        ORDER BY a.created_at DESC
        """
        
        results = self.execute_query(query)
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        return df
    
    def get_recent_predictions(self, limit: int = 10) -> pd.DataFrame:
        """Recupera predições recentes"""
        query = """
        SELECT p.*, s.name as sensor_name
        FROM prediction p
        JOIN sensor s ON p.sensor_id = s.id
        ORDER BY p.created_at DESC
        LIMIT ?
        """
        
        results = self.execute_query(query, (limit,))
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        return df

if __name__ == "__main__":
    # Teste da conexão SQLite
    db = SQLiteConnection()
    
    try:
        # Estatísticas
        stats = db.get_database_stats()
        print("=== Estatísticas SQLite ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Últimas leituras
        latest = db.get_latest_readings()
        if not latest.empty:
            print("\n=== Últimas Leituras ===")
            for _, row in latest.iterrows():
                print(f"{row['sensor_name']}: {row['value']:.2f} {row['unit']}")
        
    finally:
        db.close()
