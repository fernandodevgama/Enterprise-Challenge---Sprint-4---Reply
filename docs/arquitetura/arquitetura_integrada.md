# Arquitetura Integrada - Sistema de Sensores IoT

## Visão Geral

Este documento descreve a arquitetura integrada do sistema de manutenção preditiva desenvolvido para o Hermes Reply Challenge - Sprint 4. O sistema integra todas as entregas anteriores em um pipeline fim-a-fim funcional.

## Componentes Principais

### 1. Coleta de Dados (ESP32)
- **Fonte**: Simulação ESP32 com sensores industriais
- **Sensores**: DHT22 (temperatura/umidade), MPU6050 (vibração), LDR (luminosidade)
- **Frequência**: Coleta a cada 2-5 segundos
- **Formato**: JSON com timestamp UTC

### 2. Ingestão e Processamento
- **Coletor**: `data_collector.py` - Processa dados do ESP32
- **Validação**: Verificação de integridade e ranges
- **Transformação**: Conversão para formato do banco

### 3. Armazenamento (PostgreSQL)
- **Schema**: Baseado na Entrega 3, expandido
- **Tabelas**: asset, sensor, reading, alert, prediction
- **Índices**: Otimizados para consultas temporais
- **Views**: latest_readings, active_alerts, sensor_stats

### 4. Machine Learning
- **Treinamento**: Modelos Linear e Random Forest
- **Predição**: Valores futuros e detecção de anomalias
- **Features**: lag1, lag2, roll3, hour
- **Métricas**: MAE, R², RMSE

### 5. Dashboard e Visualização
- **Interface**: Streamlit web app
- **KPIs**: Métricas em tempo real
- **Gráficos**: Plotly interativo
- **Alertas**: Sistema de notificações

## Fluxo de Dados

```
[Sensores ESP32] 
    ↓ (JSON via serial/simulação)
[Data Collector] 
    ↓ (validação e transformação)
[PostgreSQL Database] 
    ↓ (consultas SQL)
[ML Pipeline] 
    ↓ (predições e anomalias)
[Dashboard Streamlit] 
    ↓ (visualização)
[Usuário Final]
```

## Integração com Entregas Anteriores

### Entrega 1 - Arquitetura
- ✅ Diagrama de arquitetura atualizado
- ✅ Fluxo de dados documentado
- ✅ Componentes integrados

### Entrega 2 - Simulação
- ✅ Código ESP32 reutilizado
- ✅ Sensores integrados (DHT22, MPU6050, LDR)
- ✅ Dados formatados para ingestão

### Entrega 3 - ML e Banco
- ✅ Schema PostgreSQL reutilizado
- ✅ Modelo de ML integrado
- ✅ Métricas de performance

## Tecnologias Utilizadas

### Backend
- **Python 3.11+**: Linguagem principal
- **PostgreSQL 15+**: Banco de dados
- **Psycopg2**: Conector Python-PostgreSQL
- **SQLAlchemy**: ORM (opcional)

### Machine Learning
- **Scikit-learn**: Modelos ML
- **Pandas/NumPy**: Manipulação de dados
- **Joblib**: Persistência de modelos

### Frontend
- **Streamlit**: Dashboard web
- **Plotly**: Gráficos interativos
- **HTML/CSS**: Estilização customizada

### Simulação
- **Wokwi**: Simulador ESP32
- **Arduino IDE**: Desenvolvimento
- **Python**: Simulador alternativo

## Configuração do Sistema

### Pré-requisitos
- Python 3.11+
- PostgreSQL 15+
- ESP32 (simulado)

### Instalação
```bash
# 1. Clonar repositório
git clone <repository>
cd fiap-challenge4

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar banco
python scripts/setup.py

# 4. Executar pipeline
python scripts/run_pipeline.py

# 5. Iniciar dashboard
streamlit run dashboard/app.py
```

## Estrutura de Arquivos

```
fiap-challenge4/
├── docs/
│   └── arquitetura/
│       ├── arquitetura_integrada.md
│       └── arquitetura_integrada.drawio
├── ingest/
│   ├── esp32_simulator.py
│   ├── data_collector.py
│   └── serial_monitor.py
├── db/
│   ├── schema.sql
│   ├── data_loader.py
│   └── connection.py
├── ml/
│   ├── model_trainer.py
│   ├── predictor.py
│   └── metrics.py
├── dashboard/
│   ├── app.py
│   ├── components/
│   └── utils/
├── scripts/
│   ├── setup.py
│   └── run_pipeline.py
├── models/          # Modelos ML salvos
├── data/            # Dados processados
├── outputs/         # Resultados e métricas
└── logs/            # Logs do sistema
```

## Monitoramento e Alertas

### Thresholds Configurados
- **Temperatura**: > 35°C (crítico)
- **Umidade**: > 80% (médio)
- **Vibração**: > 2000mg (crítico)
- **Luminosidade**: < 10% (baixo)

### Tipos de Alertas
- **Crítico**: Vermelho - Ação imediata necessária
- **Médio**: Laranja - Monitoramento aumentado
- **Baixo**: Verde - Informativo

## Métricas e KPIs

### Operacionais
- **Disponibilidade**: % de tempo operacional
- **Eficiência**: Performance dos sensores
- **Confiabilidade**: Precisão das medições

### ML
- **MAE**: Erro absoluto médio
- **R²**: Coeficiente de determinação
- **Acurácia**: % de predições corretas

### Alertas
- **Total**: Número de alertas gerados
- **Resolvidos**: Alertas tratados
- **Tempo médio**: Resolução de alertas

## Escalabilidade

### Horizontal
- Múltiplos sensores ESP32
- Distribuição de carga
- Redundância de dados

### Vertical
- Otimização de consultas
- Índices de banco
- Cache de predições

## Segurança

### Dados
- Criptografia em trânsito
- Backup automático
- Auditoria de acessos

### Sistema
- Autenticação de usuários
- Controle de acesso
- Logs de segurança

## Próximos Passos

### Melhorias Técnicas
- [ ] Implementar comunicação WiFi real
- [ ] Adicionar mais tipos de sensores
- [ ] Otimizar modelos ML
- [ ] Implementar cache Redis

### Funcionalidades
- [ ] Alertas por email/SMS
- [ ] Relatórios automáticos
- [ ] API REST
- [ ] Mobile app

### Integração
- [ ] Sistemas ERP/MES
- [ ] Cloud platforms
- [ ] Edge computing
- [ ] 5G connectivity

## Conclusão

O sistema integrado demonstra com sucesso a conexão entre todas as entregas anteriores, criando um pipeline funcional de manutenção preditiva. A arquitetura é escalável, modular e pronta para expansão em ambientes industriais reais.

---

**Desenvolvido por**: Grupo 5 - Hermes Reply Challenge  
**Data**: Janeiro 2025  
**Versão**: 1.0
