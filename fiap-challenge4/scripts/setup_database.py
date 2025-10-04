#!/usr/bin/env python3
"""
Script de configuração automática do banco PostgreSQL
Cria banco, tabelas e dados iniciais para o sistema IoT
Author: HermesReply Challenge - Grupo 5
Version: 1.0
Date: 2024-01-20
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_step(step, text):
    """Imprime passo formatado"""
    print(f"\n[{step}] {text}")

def check_postgresql_connection():
    """Verifica se o PostgreSQL está rodando"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='password'
        )
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar com PostgreSQL: {e}")
        return False

def create_database():
    """Cria o banco de dados se não existir"""
    try:
        # Conectar ao PostgreSQL como superuser
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='password'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar se banco existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='industrial_iot'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Criando banco de dados 'industrial_iot'...")
            cursor.execute("CREATE DATABASE industrial_iot")
            print("✅ Banco criado com sucesso!")
        else:
            print("✅ Banco 'industrial_iot' já existe")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        return False

def create_tables():
    """Cria as tabelas do schema"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='industrial_iot',
            user='postgres',
            password='password'
        )
        cursor = conn.cursor()
        
        # Ler schema SQL
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Executar schema
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Tabelas criadas com sucesso!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def insert_initial_data():
    """Insere dados iniciais (assets e sensores)"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='industrial_iot',
            user='postgres',
            password='password'
        )
        cursor = conn.cursor()
        
        # Inserir asset
        cursor.execute("""
            INSERT INTO asset (name, location) 
            VALUES ('Linha de Produção 1', 'Fábrica Principal')
            ON CONFLICT DO NOTHING
            RETURNING id
        """)
        
        result = cursor.fetchone()
        if result:
            asset_id = result[0]
        else:
            # Se já existe, buscar o ID
            cursor.execute("SELECT id FROM asset WHERE name = 'Linha de Produção 1'")
            asset_id = cursor.fetchone()[0]
        
        # Inserir sensores
        sensors = [
            ('S_TEMP', 'temperature', '°C', 0, 50),
            ('S_HUMIDITY', 'humidity', '%', 0, 100),
            ('S_VIBRATION', 'vibration', 'mg', 0, 2000),
            ('S_LIGHT', 'light', '%', 0, 100)
        ]
        
        for name, sensor_type, unit, min_val, max_val in sensors:
            cursor.execute("""
                INSERT INTO sensor (asset_id, name, type, unit, min_value, max_value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (asset_id, name, sensor_type, unit, min_val, max_val))
        
        conn.commit()
        print("✅ Dados iniciais inseridos com sucesso!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados iniciais: {e}")
        return False

def create_env_file():
    """Cria arquivo .env com configurações do banco"""
    env_content = """# Configurações do Banco PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=industrial_iot
DB_USER=postgres
DB_PASSWORD=password

# Configurações do Sistema
ENVIRONMENT=development
DEBUG=true
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ Arquivo .env criado com sucesso!")
    else:
        print("✅ Arquivo .env já existe")

def test_connection():
    """Testa a conexão com o banco configurado"""
    try:
        from db.connection import DatabaseConnection
        
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'industrial_iot',
            'user': 'postgres',
            'password': 'password'
        }
        
        db = DatabaseConnection(db_config)
        
        # Testar query simples
        result = db.execute_query("SELECT COUNT(*) FROM sensor")
        sensor_count = result[0][0] if result else 0
        
        print(f"✅ Conexão testada! Sensores cadastrados: {sensor_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False

def main():
    """Função principal"""
    print_header("🏭 CONFIGURAÇÃO DO BANCO POSTGRESQL")
    print("Sistema IoT Industrial - HermesReply Challenge")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Passo 1: Verificar PostgreSQL
    print_step("1/6", "Verificando conexão com PostgreSQL...")
    if not check_postgresql_connection():
        print("\n❌ ERRO: PostgreSQL não está rodando ou credenciais incorretas")
        print("\nVerifique se:")
        print("- PostgreSQL está instalado e rodando")
        print("- Usuário 'postgres' existe com senha 'password'")
        print("- Porta 5432 está disponível")
        return False
    
    print("✅ PostgreSQL está rodando!")
    
    # Passo 2: Criar banco
    print_step("2/6", "Criando banco de dados...")
    if not create_database():
        return False
    
    # Passo 3: Criar tabelas
    print_step("3/6", "Criando tabelas...")
    if not create_tables():
        return False
    
    # Passo 4: Inserir dados iniciais
    print_step("4/6", "Inserindo dados iniciais...")
    if not insert_initial_data():
        return False
    
    # Passo 5: Criar arquivo .env
    print_step("5/6", "Criando arquivo de configuração...")
    create_env_file()
    
    # Passo 6: Testar conexão
    print_step("6/6", "Testando conexão final...")
    if not test_connection():
        return False
    
    # Sucesso
    print_header("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("\n🎉 O banco PostgreSQL está pronto para uso!")
    print("\n📋 Próximos passos:")
    print("1. Execute o pipeline: python scripts/run_pipeline_sqlite.py")
    print("2. Inicie o dashboard: streamlit run dashboard/app_real.py")
    print("3. Acesse: http://localhost:8501")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)