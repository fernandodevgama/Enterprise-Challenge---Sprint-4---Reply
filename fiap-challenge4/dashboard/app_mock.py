#!/usr/bin/env python3
"""
Dashboard Moderno - Sistema IoT Industrial

Dashboard web moderno e responsivo para monitoramento de sensores IoT industriais.
Utiliza dados mockados para demonstração das funcionalidades.

Autor: Sistema IoT Industrial
Versão: 2.0
Data: 2024
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime, timezone, timedelta
import random

# Configuração da página
st.set_page_config(
    page_title="Sistema IoT Industrial - Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-good {
        color: #10b981;
    }
    
    .status-warning {
        color: #f59e0b;
    }
    
    .status-critical {
        color: #ef4444;
    }
    
    .alert-card {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 1px solid #fecaca;
        border-radius: 1rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .info-card {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #bfdbfe;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .sidebar .stSelectbox > div > div {
        background-color: #f8fafc;
        border-radius: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0px 24px;
        background-color: #f8fafc;
        border-radius: 8px;
        color: #64748b;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def generate_mock_data():
    """Gera dados mockados para os sensores"""
    
    # Configuração dos sensores
    sensors = {
        'temperature': {
            'name': 'Temperatura',
            'unit': '°C',
            'icon': '🌡️',
            'min_val': 18.0,
            'max_val': 35.0,
            'threshold_min': 20.0,
            'threshold_max': 30.0
        },
        'humidity': {
            'name': 'Umidade',
            'unit': '%',
            'icon': '💧',
            'min_val': 30.0,
            'max_val': 80.0,
            'threshold_min': 40.0,
            'threshold_max': 70.0
        },
        'vibration': {
            'name': 'Vibração',
            'unit': 'mg',
            'icon': '📳',
            'min_val': 0.0,
            'max_val': 2000.0,
            'threshold_min': 0.0,
            'threshold_max': 1500.0
        },
        'luminosity': {
            'name': 'Luminosidade',
            'unit': '%',
            'icon': '💡',
            'min_val': 0.0,
            'max_val': 100.0,
            'threshold_min': 20.0,
            'threshold_max': 80.0
        }
    }
    
    # Gera dados históricos (últimas 24 horas)
    now = datetime.now()
    timestamps = [now - timedelta(minutes=x*5) for x in range(288)]  # 5 em 5 minutos por 24h
    timestamps.reverse()
    
    historical_data = {}
    current_values = {}
    alerts = []
    
    for sensor_key, sensor_info in sensors.items():
        # Gera série temporal com tendência e ruído
        base_value = (sensor_info['min_val'] + sensor_info['max_val']) / 2
        trend = np.sin(np.linspace(0, 4*np.pi, len(timestamps))) * (sensor_info['max_val'] - sensor_info['min_val']) * 0.2
        noise = np.random.normal(0, (sensor_info['max_val'] - sensor_info['min_val']) * 0.05, len(timestamps))
        values = base_value + trend + noise
        
        # Garante que os valores estão dentro dos limites
        values = np.clip(values, sensor_info['min_val'], sensor_info['max_val'])
        
        historical_data[sensor_key] = {
            'timestamps': timestamps,
            'values': values.tolist(),
            'sensor_info': sensor_info
        }
        
        current_values[sensor_key] = values[-1]
        
        # Verifica alertas
        current_val = values[-1]
        if current_val < sensor_info['threshold_min'] or current_val > sensor_info['threshold_max']:
            severity = 'CRÍTICO' if (current_val < sensor_info['threshold_min'] * 0.9 or 
                                   current_val > sensor_info['threshold_max'] * 1.1) else 'ALERTA'
            alerts.append({
                'sensor': sensor_info['name'],
                'value': current_val,
                'unit': sensor_info['unit'],
                'severity': severity,
                'message': f"{sensor_info['name']} fora do limite: {current_val:.1f}{sensor_info['unit']}"
            })
    
    return historical_data, current_values, alerts

def create_modern_chart(data, title, color_scheme):
    """Cria gráfico moderno com Plotly"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['timestamps'],
        y=data['values'],
        mode='lines',
        name=title,
        line=dict(
            color=color_scheme,
            width=3,
            shape='spline'
        ),
        fill='tonexty',
        fillcolor=f'rgba({",".join(map(str, px.colors.hex_to_rgb(color_scheme)))}, 0.1)'
    ))
    
    fig.update_layout(
        title=dict(
            text=f"📊 {title} - Últimas 24h",
            font=dict(size=18, family="Inter", color="#1e293b")
        ),
        xaxis=dict(
            title="Tempo",
            showgrid=True,
            gridcolor='rgba(148, 163, 184, 0.3)',
            title_font=dict(family="Inter")
        ),
        yaxis=dict(
            title=f"{data['sensor_info']['name']} ({data['sensor_info']['unit']})",
            showgrid=True,
            gridcolor='rgba(148, 163, 184, 0.3)',
            title_font=dict(family="Inter")
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter"),
        hovermode='x unified',
        showlegend=False
    )
    
    return fig

def create_gauge_chart(value, title, unit, min_val, max_val, threshold_min, threshold_max):
    """Cria gráfico de gauge moderno"""
    
    # Define cor baseada no valor
    if threshold_min <= value <= threshold_max:
        color = "#10b981"  # Verde
    elif value < threshold_min * 0.9 or value > threshold_max * 1.1:
        color = "#ef4444"  # Vermelho
    else:
        color = "#f59e0b"  # Amarelo
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'family': 'Inter', 'size': 16}},
        delta = {'reference': (threshold_min + threshold_max) / 2},
        gauge = {
            'axis': {'range': [min_val, max_val], 'tickfont': {'family': 'Inter'}},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e2e8f0",
            'steps': [
                {'range': [min_val, threshold_min], 'color': "#fee2e2"},
                {'range': [threshold_min, threshold_max], 'color': "#dcfce7"},
                {'range': [threshold_max, max_val], 'color': "#fee2e2"}
            ],
            'threshold': {
                'line': {'color': "#64748b", 'width': 4},
                'thickness': 0.75,
                'value': (threshold_min + threshold_max) / 2
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        font={'family': 'Inter'},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def main():
    """Função principal do dashboard"""
    
    # Header
    st.markdown('<h1 class="main-header">🏭 Sistema IoT Industrial</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Dashboard de Monitoramento em Tempo Real</p>', unsafe_allow_html=True)
    
    # Gera dados mockados
    historical_data, current_values, alerts = generate_mock_data()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Configurações")
        
        # Seletor de período
        time_range = st.selectbox(
            "Período de visualização:",
            ["Últimas 24 horas", "Últimas 12 horas", "Últimas 6 horas", "Última hora"],
            index=0
        )
        
        # Seletor de sensores
        st.markdown("### 📊 Sensores Ativos")
        sensor_selection = {}
        for key, data in historical_data.items():
            sensor_selection[key] = st.checkbox(
                f"{data['sensor_info']['icon']} {data['sensor_info']['name']}", 
                value=True
            )
        
        # Informações do sistema
        st.markdown("### 📋 Status do Sistema")
        st.markdown("""
        <div class="info-card">
            <strong>🟢 Sistema Online</strong><br>
            <small>Última atualização: agora</small><br>
            <small>Sensores ativos: 4/4</small><br>
            <small>Dados mockados: ✅</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Alertas
    if alerts:
        st.markdown("### 🚨 Alertas Ativos")
        alert_cols = st.columns(len(alerts))
        for i, alert in enumerate(alerts):
            with alert_cols[i]:
                severity_class = "status-critical" if alert['severity'] == 'CRÍTICO' else "status-warning"
                st.markdown(f"""
                <div class="alert-card">
                    <div class="{severity_class}">
                        <strong>{alert['severity']}</strong>
                    </div>
                    <div>{alert['message']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # KPIs principais
    st.markdown("### 📈 Indicadores em Tempo Real")
    kpi_cols = st.columns(4)
    
    colors = ["#667eea", "#f093fb", "#4facfe", "#43e97b"]
    
    for i, (key, data) in enumerate(historical_data.items()):
        if sensor_selection[key]:
            with kpi_cols[i]:
                current_val = current_values[key]
                sensor_info = data['sensor_info']
                
                # Determina status
                if sensor_info['threshold_min'] <= current_val <= sensor_info['threshold_max']:
                    status_class = "status-good"
                    status_text = "Normal"
                elif current_val < sensor_info['threshold_min'] * 0.9 or current_val > sensor_info['threshold_max'] * 1.1:
                    status_class = "status-critical"
                    status_text = "Crítico"
                else:
                    status_class = "status-warning"
                    status_text = "Alerta"
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{sensor_info['icon']} {sensor_info['name']}</div>
                    <div class="metric-value" style="color: {colors[i]}">
                        {current_val:.1f}<small>{sensor_info['unit']}</small>
                    </div>
                    <div class="{status_class}">● {status_text}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Gráficos
    st.markdown("### 📊 Análise Temporal")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["📈 Séries Temporais", "🎯 Gauges", "📋 Estatísticas"])
    
    with tab1:
        chart_cols = st.columns(2)
        chart_index = 0
        
        for key, data in historical_data.items():
            if sensor_selection[key]:
                with chart_cols[chart_index % 2]:
                    fig = create_modern_chart(data, data['sensor_info']['name'], colors[chart_index])
                    st.plotly_chart(fig, use_container_width=True)
                chart_index += 1
    
    with tab2:
        gauge_cols = st.columns(2)
        gauge_index = 0
        
        for key, data in historical_data.items():
            if sensor_selection[key]:
                with gauge_cols[gauge_index % 2]:
                    sensor_info = data['sensor_info']
                    fig = create_gauge_chart(
                        current_values[key],
                        f"{sensor_info['icon']} {sensor_info['name']}",
                        sensor_info['unit'],
                        sensor_info['min_val'],
                        sensor_info['max_val'],
                        sensor_info['threshold_min'],
                        sensor_info['threshold_max']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                gauge_index += 1
    
    with tab3:
        st.markdown("### 📊 Estatísticas dos Sensores")
        
        stats_data = []
        for key, data in historical_data.items():
            if sensor_selection[key]:
                values = data['values']
                sensor_info = data['sensor_info']
                
                stats_data.append({
                    'Sensor': f"{sensor_info['icon']} {sensor_info['name']}",
                    'Atual': f"{current_values[key]:.2f} {sensor_info['unit']}",
                    'Média': f"{np.mean(values):.2f} {sensor_info['unit']}",
                    'Mínimo': f"{np.min(values):.2f} {sensor_info['unit']}",
                    'Máximo': f"{np.max(values):.2f} {sensor_info['unit']}",
                    'Desvio Padrão': f"{np.std(values):.2f} {sensor_info['unit']}"
                })
        
        if stats_data:
            df_stats = pd.DataFrame(stats_data)
            st.dataframe(df_stats, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.9rem;">
        🏭 Sistema IoT Industrial | Dashboard com Dados Mockados | 
        Atualizado em tempo real | Desenvolvido com Streamlit
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()