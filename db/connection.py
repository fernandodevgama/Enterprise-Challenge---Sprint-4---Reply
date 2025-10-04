#!/usr/bin/env python3
"""
Conexão com banco PostgreSQL para sistema de sensores IoT
Baseado no schema da Entrega 3
"""

import psycopg2
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import uuid

class DatabaseConnection:
    """Conexão e operações com banco PostgreSQL"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.connection = None
        self.connect()
    
    def connect(self):
        """Estabelece conexão com o banco"""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            print("Conexão com banco estabelecida com sucesso!")
        except Exception as e:
            print(f"Erro ao conectar com banco: {e}")
            raise
    
    def close(self):
        """Fecha conexão com o banco"""
        if self.connection:
            self.connection.close()
            print("Conexão com banco fechada.")
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Executa query SQL e retorna resultados"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return cursor.fetchall()
                self.connection.commit()
                return []
        except Exception as e:
            print(f"Erro ao executar query: {e}")
            self.connection.rollback()
            raise
    
    def create_asset(self, asset_data: Dict) -> str:
        """Cria novo asset no banco"""
        query = """
        INSERT INTO asset (name, location)
        VALUES (%s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (asset_data['name'], asset_data['location']))
        return str(result[0][0])
    
    def create_sensor(self, asset_id: str, sensor_data: Dict) -> str:
        """Cria novo sensor no banco"""
        query = """
        INSERT INTO sensor (asset_id, name, type, unit, min_value, max_value)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (
            asset_id,
            sensor_data['name'],
            sensor_data['type'],
            sensor_data['unit'],
            sensor_data['min_value'],
            sensor_data['max_value']
        ))
        return str(result[0][0])
    
    def create_reading(self, sensor_id: str, timestamp: datetime, value: float) -> str:
        """Cria nova leitura no banco"""
        query = """
        INSERT INTO reading (sensor_id, ts, value)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        result = self.execute_query(query, (sensor_id, timestamp, value))
        return str(result[0][0])
    
    def get_sensor_readings(self, sensor_id: str, limit: int = 100) -> pd.DataFrame:
        """Recupera leituras de um sensor específico"""
        query = """
        SELECT ts, value
        FROM reading
        WHERE sensor_id = %s
        ORDER BY ts DESC
        LIMIT %s
        """
        results = self.execute_query(query, (sensor_id, limit))
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['ts', 'value'])
        df['ts'] = pd.to_datetime(df['ts'])
        return df
    
    def get_all_readings(self, limit: int = 1000) -> pd.DataFrame:
        """Recupera todas as leituras com informações dos sensores"""
        query = """
        SELECT r.ts, r.value, s.name as sensor_name, s.type, s.unit, a.name as asset_name
        FROM reading r
        JOIN sensor s ON r.sensor_id = s.id
        JOIN asset a ON s.asset_id = a.id
        ORDER BY r.ts DESC
        LIMIT %s
        """
        results = self.execute_query(query, (limit,))
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['ts', 'value', 'sensor_name', 'type', 'unit', 'asset_name'])
        df['ts'] = pd.to_datetime(df['ts'])
        return df
    
    def get_sensor_summary(self, sensor_id: str) -> Dict:
        """Retorna resumo estatístico de um sensor"""
        query = """
        SELECT 
            COUNT(*) as count,
            AVG(value) as mean,
            STDDEV(value) as std,
            MIN(value) as min,
            MAX(value) as max,
            MIN(ts) as first_reading,
            MAX(ts) as last_reading
        FROM reading
        WHERE sensor_id = %s
        """
        results = self.execute_query(query, (sensor_id,))
        
        if not results or results[0][0] == 0:
            return {}
        
        row = results[0]
        return {
            'count': row[0],
            'mean': float(row[1]) if row[1] else 0,
            'std': float(row[2]) if row[2] else 0,
            'min': float(row[3]) if row[3] else 0,
            'max': float(row[4]) if row[4] else 0,
            'first_reading': row[5],
            'last_reading': row[6]
        }
    
    def get_anomalies(self, sensor_id: str, threshold_min: float = None, threshold_max: float = None) -> pd.DataFrame:
        """Identifica anomalias baseadas em thresholds"""
        conditions = ["sensor_id = %s"]
        params = [sensor_id]
        
        if threshold_min is not None:
            conditions.append("value < %s")
            params.append(threshold_min)
        
        if threshold_max is not None:
            conditions.append("value > %s")
            params.append(threshold_max)
        
        query = f"""
        SELECT ts, value
        FROM reading
        WHERE {' AND '.join(conditions)}
        ORDER BY ts DESC
        """
        
        results = self.execute_query(query, tuple(params))
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results, columns=['ts', 'value'])
        df['ts'] = pd.to_datetime(df['ts'])
        return df
    
    def get_latest_readings(self) -> pd.DataFrame:
        """Recupera as últimas leituras de cada sensor"""
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
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove dados antigos para manter performance"""
        query = """
        DELETE FROM reading
        WHERE ts < NOW() - INTERVAL '%s days'
        """
        
        result = self.execute_query(query, (days_to_keep,))
        print(f"Dados antigos removidos (mais de {days_to_keep} dias)")
    
    def get_database_stats(self) -> Dict:
        """Retorna estatísticas gerais do banco"""
        stats = {}
        
        # Contagem de registros por tabela
        tables = ['asset', 'sensor', 'reading']
        for table in tables:
            query = f"SELECT COUNT(*) FROM {table}"
            result = self.execute_query(query)
            stats[f'{table}_count'] = result[0][0] if result else 0
        
        # Última leitura
        query = "SELECT MAX(ts) FROM reading"
        result = self.execute_query(query)
        stats['last_reading'] = result[0][0] if result and result[0][0] else None
        
        # Primeira leitura
        query = "SELECT MIN(ts) FROM reading"
        result = self.execute_query(query)
        stats['first_reading'] = result[0][0] if result and result[0][0] else None
        
        return stats

if __name__ == "__main__":
    # Exemplo de uso
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'industrial_iot',
        'user': 'postgres',
        'password': 'password'
    }
    
    db = DatabaseConnection(config)
    
    try:
        # Estatísticas do banco
        stats = db.get_database_stats()
        print("=== Estatísticas do Banco ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
    finally:
        db.close()
