#!/usr/bin/env python3
"""
Script de configuração inicial do sistema
Instala dependências e configura banco de dados
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql

def run_command(command, description):
    """Executa comando e exibe resultado"""
    print(f"Executando: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erro: {e}")
        return False

def check_python_version():
    """Verifica versão do Python"""
    print("Verificando versão do Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ é necessário")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Instala dependências Python"""
    print("\nInstalando dependências Python...")
    
    if not run_command("pip install -r requirements.txt", "Instalação de dependências"):
        return False
    
    return True

def check_postgresql():
    """Verifica se PostgreSQL está disponível"""
    print("\nVerificando PostgreSQL...")
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='password'
        )
        conn.close()
        print("✅ PostgreSQL conectado")
        return True
    except Exception as e:
        print(f"❌ Erro ao conectar PostgreSQL: {e}")
        print("Verifique se o PostgreSQL está rodando e as credenciais estão corretas")
        return False

def create_database():
    """Cria banco de dados se não existir"""
    print("\nCriando banco de dados...")
    
    try:
        # Conecta ao banco padrão
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='password'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verifica se banco existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'industrial_iot'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE industrial_iot")
            print("✅ Banco 'industrial_iot' criado")
        else:
            print("✅ Banco 'industrial_iot' já existe")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        return False

def setup_database_schema():
    """Configura schema do banco"""
    print("\nConfigurando schema do banco...")
    
    try:
        # Conecta ao banco industrial_iot
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='industrial_iot',
            user='postgres',
            password='password'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Executa schema SQL
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        print("✅ Schema configurado com sucesso")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar schema: {e}")
        return False

def create_directories():
    """Cria diretórios necessários"""
    print("\nCriando diretórios...")
    
    directories = [
        'models',
        'data',
        'logs',
        'outputs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Diretório '{directory}' criado")
    
    return True

def create_config_files():
    """Cria arquivos de configuração"""
    print("\nCriando arquivos de configuração...")
    
    # Streamlit secrets
    secrets_content = """
[db]
host = "localhost"
port = 5432
database = "industrial_iot"
user = "postgres"
password = "password"
"""
    
    with open('.streamlit/secrets.toml', 'w') as f:
        os.makedirs('.streamlit', exist_ok=True)
        f.write(secrets_content)
    
    print("✅ Arquivo de configuração do Streamlit criado")
    
    # Configuração de ambiente
    env_content = """
# Configurações do Sistema de Sensores IoT
DB_HOST=localhost
DB_PORT=5432
DB_NAME=industrial_iot
DB_USER=postgres
DB_PASSWORD=password
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Arquivo .env criado")
    
    return True

def run_tests():
    """Executa testes básicos"""
    print("\nExecutando testes básicos...")
    
    try:
        # Testa importação dos módulos
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from db.connection import DatabaseConnection
        from ingest.esp32_simulator import ESP32Simulator
        from ml.model_trainer import MLModelTrainer
        
        print("✅ Módulos importados com sucesso")
        
        # Testa conexão com banco
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'industrial_iot',
            'user': 'postgres',
            'password': 'password'
        }
        
        db = DatabaseConnection(db_config)
        stats = db.get_database_stats()
        print(f"✅ Conexão com banco testada - {stats.get('reading_count', 0)} leituras")
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return False

def main():
    """Função principal de setup"""
    print("="*60)
    print(" CONFIGURAÇÃO DO SISTEMA DE SENSORES IoT")
    print(" Hermes Reply Challenge - Sprint 4")
    print("="*60)
    
    steps = [
        ("Verificação do Python", check_python_version),
        ("Instalação de dependências", install_dependencies),
        ("Verificação do PostgreSQL", check_postgresql),
        ("Criação do banco de dados", create_database),
        ("Configuração do schema", setup_database_schema),
        ("Criação de diretórios", create_directories),
        ("Criação de arquivos de configuração", create_config_files),
        ("Testes básicos", run_tests)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"\n--- {step_name} ---")
        if step_function():
            success_count += 1
        else:
            print(f"❌ Falha em: {step_name}")
    
    print("\n" + "="*60)
    print(f" CONFIGURAÇÃO CONCLUÍDA: {success_count}/{len(steps)} passos")
    print("="*60)
    
    if success_count == len(steps):
        print("""
🎉 SISTEMA CONFIGURADO COM SUCESSO!

Próximos passos:
1. Execute o pipeline: python scripts/run_pipeline.py
2. Inicie o dashboard: streamlit run dashboard/app.py
3. Acesse http://localhost:8501 no navegador

Arquivos importantes:
- requirements.txt: Dependências Python
- db/schema.sql: Schema do banco
- scripts/run_pipeline.py: Pipeline completo
- dashboard/app.py: Interface web
        """)
        return 0
    else:
        print("""
❌ CONFIGURAÇÃO INCOMPLETA

Verifique os erros acima e execute novamente.
Certifique-se de que:
- Python 3.8+ está instalado
- PostgreSQL está rodando
- Credenciais do banco estão corretas
        """)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
