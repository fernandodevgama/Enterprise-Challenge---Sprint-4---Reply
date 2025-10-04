#!/usr/bin/env python3
"""
Dashboard IoT Industrial - Versão com Banco PostgreSQL Real
Sistema de monitoramento com dados reais do banco de dados
Author: HermesReply Challenge - Grupo 5
Version: 1.0
Date: 2024-01-20
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import os
import sys

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import DatabaseConnection

# Configuração da página
st.set_page_config(
    page_title="IoT Industrial Dashboard - Real DB",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para design moderno
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .alert-low {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .status-online {
        color: #4caf50;
        font-weight: bold;
    }
    .status-offline {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)  # Cache por 30 segundos
def get_database_connection():
    """Conecta ao banco PostgreSQL"""
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'industrial_iot'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        return DatabaseConnection(db_config)
    except Exception as e:
        st.error(f"Erro ao conectar com o banco: {e}")
        return None

@st.cache_data(ttl=30)
def load_sensor_data(db_connection, hours_back=24):
    """Carrega dados dos sensores das últimas horas"""
    if not db_connection:
        return pd.DataFrame()
    
    try:
        # Query para buscar dados recentes
        query = """
        SELECT 
            s.name as sensor_name,
            s.type as sensor_type,
            s.unit,
            r.ts,
            r.value,
            a.name as asset_name
        FROM reading r
        JOIN sensor s ON r.sensor_id = s.id
        JOIN asset a ON s.asset_id = a.id
        WHERE r.ts >= NOW() - INTERVAL '%s hours'
        ORDER BY r.ts DESC
        LIMIT 10000
        """
        
        result = db_connection.execute_query(query, (hours_back,))
        if result:
            df = pd.DataFrame(result, columns=['sensor_name', 'sensor_type', 'unit', 'ts', 'value', 'asset_name'])
            df['ts'] = pd.to_datetime(df['ts'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_alerts(db_connection, limit=50):
    """Carrega alertas recentes"""
    if not db_connection:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            al.alert_type,
            al.message,
            al.severity,
            al.actual_value,
            al.threshold_value,
            al.created_at,
            s.name as sensor_name,
            a.name as asset_name
        FROM alert al
        JOIN sensor s ON al.sensor_id = s.id
        JOIN asset a ON s.asset_id = a.id
        ORDER BY al.created_at DESC
        LIMIT %s
        """
        
        result = db_connection.execute_query(query, (limit,))
        if result:
            df = pd.DataFrame(result, columns=[
                'alert_type', 'message', 'severity', 'actual_value', 
                'threshold_value', 'created_at', 'sensor_name', 'asset_name'
            ])
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar alertas: {e}")
        return pd.DataFrame()

def create_gauge_chart(value, title, min_val=0, max_val=100, threshold_low=20, threshold_high=80):
    """Cria gráfico de gauge"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': (threshold_low + threshold_high) / 2},
        gauge = {
            'axis': {'range': [None, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_val, threshold_low], 'color': "lightgray"},
                {'range': [threshold_low, threshold_high], 'color': "lightgreen"},
                {'range': [threshold_high, max_val], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': threshold_high
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def main():
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🏭 Sistema IoT Industrial - Dashboard Real</h1>
        <p>Monitoramento em tempo real com dados do PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Conectar ao banco
    db = get_database_connection()
    
    if not db:
        st.error("❌ Não foi possível conectar ao banco de dados PostgreSQL")
        st.info("Verifique se o PostgreSQL está rodando e as credenciais estão corretas no arquivo .env")
        return
    
    # Sidebar para controles
    st.sidebar.header("⚙️ Controles")
    
    # Seletor de período
    hours_back = st.sidebar.selectbox(
        "Período de dados:",
        [1, 6, 12, 24, 48, 72],
        index=3,
        format_func=lambda x: f"Últimas {x} horas"
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=True)
    
    if auto_refresh:
        time.sleep(1)
        st.rerun()
    
    # Carregar dados
    with st.spinner("Carregando dados do banco..."):
        df = load_sensor_data(db, hours_back)
        alerts_df = load_alerts(db)
    
    if df.empty:
        st.warning("⚠️ Nenhum dado encontrado no banco de dados")
        st.info("Execute o pipeline de dados para popular o banco: `python scripts/run_pipeline_sqlite.py`")
        return
    
    # Status da conexão
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("### 📊 Status do Sistema")
    with col2:
        st.markdown('<p class="status-online">🟢 Banco Online</p>', unsafe_allow_html=True)
    with col3:
        st.markdown(f"**Última atualização:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Métricas principais
    st.markdown("### 📈 KPIs Principais")
    
    # Calcular métricas por sensor
    latest_data = df.groupby('sensor_name').last().reset_index()
    
    cols = st.columns(4)
    sensor_configs = {
        'S_TEMP': {'name': '🌡️ Temperatura', 'unit': '°C', 'min': 0, 'max': 50, 'low': 20, 'high': 30},
        'S_HUMIDITY': {'name': '💧 Umidade', 'unit': '%', 'min': 0, 'max': 100, 'low': 40, 'high': 70},
        'S_VIBRATION': {'name': '📳 Vibração', 'unit': 'mg', 'min': 0, 'max': 2000, 'low': 0, 'high': 1500},
        'S_LIGHT': {'name': '💡 Luminosidade', 'unit': '%', 'min': 0, 'max': 100, 'low': 20, 'high': 80}
    }
    
    for i, (sensor_id, config) in enumerate(sensor_configs.items()):
        with cols[i]:
            sensor_data = latest_data[latest_data['sensor_name'] == sensor_id]
            if not sensor_data.empty:
                value = sensor_data.iloc[0]['value']
                st.metric(
                    label=config['name'],
                    value=f"{value:.1f} {config['unit']}",
                    delta=f"{np.random.uniform(-2, 2):.1f}"  # Delta simulado
                )
            else:
                st.metric(label=config['name'], value="N/A")
    
    # Gráficos de gauge
    st.markdown("### 🎯 Indicadores Visuais")
    gauge_cols = st.columns(4)
    
    for i, (sensor_id, config) in enumerate(sensor_configs.items()):
        with gauge_cols[i]:
            sensor_data = latest_data[latest_data['sensor_name'] == sensor_id]
            if not sensor_data.empty:
                value = sensor_data.iloc[0]['value']
                fig = create_gauge_chart(
                    value, config['name'], 
                    config['min'], config['max'], 
                    config['low'], config['high']
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Gráficos de séries temporais
    st.markdown("### 📊 Séries Temporais")
    
    if len(df) > 0:
        # Gráfico principal com todos os sensores
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['🌡️ Temperatura', '💧 Umidade', '📳 Vibração', '💡 Luminosidade'],
            vertical_spacing=0.08
        )
        
        sensors = ['S_TEMP', 'S_HUMIDITY', 'S_VIBRATION', 'S_LIGHT']
        positions = [(1,1), (1,2), (2,1), (2,2)]
        
        for sensor, (row, col) in zip(sensors, positions):
            sensor_df = df[df['sensor_name'] == sensor].sort_values('ts')
            if not sensor_df.empty:
                fig.add_trace(
                    go.Scatter(
                        x=sensor_df['ts'],
                        y=sensor_df['value'],
                        mode='lines+markers',
                        name=sensor,
                        line=dict(width=2)
                    ),
                    row=row, col=col
                )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Sistema de alertas
    st.markdown("### 🚨 Sistema de Alertas")
    
    if not alerts_df.empty:
        # Contadores de alertas
        alert_counts = alerts_df['severity'].value_counts()
        
        alert_cols = st.columns(4)
        with alert_cols[0]:
            st.metric("🔴 Críticos", alert_counts.get('critical', 0))
        with alert_cols[1]:
            st.metric("🟠 Altos", alert_counts.get('high', 0))
        with alert_cols[2]:
            st.metric("🟡 Médios", alert_counts.get('medium', 0))
        with alert_cols[3]:
            st.metric("🟣 Baixos", alert_counts.get('low', 0))
        
        # Lista de alertas recentes
        st.markdown("#### Alertas Recentes")
        for _, alert in alerts_df.head(10).iterrows():
            severity_class = f"alert-{alert['severity']}" if alert['severity'] in ['high', 'medium', 'low'] else "alert-high"
            st.markdown(f"""
            <div class="{severity_class}">
                <strong>{alert['sensor_name']}</strong> - {alert['alert_type']}<br>
                <small>{alert['message']} | {alert['created_at'].strftime('%d/%m/%Y %H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Nenhum alerta ativo no momento")
    
    # Estatísticas detalhadas
    with st.expander("📊 Estatísticas Detalhadas"):
        if not df.empty:
            stats_df = df.groupby('sensor_name')['value'].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
            st.dataframe(stats_df, use_container_width=True)
        
        st.markdown("#### Dados Brutos (Últimos 100 registros)")
        st.dataframe(df.head(100), use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🏭 Sistema IoT Industrial - Versão PostgreSQL | HermesReply Challenge - Grupo 5</p>
        <p>Dados em tempo real do banco PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()