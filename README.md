# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="../assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Administração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# Sistema Integrado de Manutenção Preditiva - Sprint 4

## Nome do grupo

**HermesReply Challenge - Grupo 5**

## 👨‍🎓 Integrantes: 
- Gabriella Serni Ponzetta – RM 566296
- João Francisco Maciel Albano – RM 565985
- Fernando Ricardo – RM 566501
- João Pedro Abreu dos Santos – RM 563261
- Gabriel Schuler Barros – RM 564934

## 👩‍🏫 Professores:
### Tutor(a) 
- Lucas Gomes Moreira
- Leonardo Ruiz Orabona
### Coordenador(a)
- André Godoi Chiovato

---

## 📜 Descrição

# 🏭 Sistema IoT Industrial - Dashboard Moderno

Sistema de monitoramento IoT industrial com dashboard moderno e dados mockados para demonstração.

## 🚀 Funcionalidades

- **Dashboard Moderno**: Interface web responsiva com design contemporâneo
- **Dados Mockados**: Simulação realística de sensores industriais
- **Visualizações Avançadas**: Gráficos interativos com Plotly
- **Sistema de Alertas**: Detecção automática de anomalias
- **Métricas em Tempo Real**: KPIs e estatísticas detalhadas

## 📊 Sensores Simulados

- **🌡️ Temperatura**: 18°C - 35°C (Threshold: 20°C - 30°C)
- **💧 Umidade**: 30% - 80% (Threshold: 40% - 70%)
- **📳 Vibração**: 0 - 2000mg (Threshold: 0 - 1500mg)
- **💡 Luminosidade**: 0% - 100% (Threshold: 20% - 80%)

## 🛠️ Instalação

1. **Clone o repositório**:
   ```bash
   git clone <repository>
   cd fiap-challenge4
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o dashboard**:
   ```bash
   streamlit run dashboard/app_mock.py
   ```

4. **Acesse o dashboard**:
   - Abra http://localhost:8501 no navegador

---

## 📁 Estrutura de Pastas

```
fiap-challenge4/
├── docs/
│   └── arquitetura/
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
└── README.md
```

---

## 🚀 Como Executar o Projeto

### ⚡ Versão Mock (Recomendado - Dados Simulados)

**Para demonstração rápida com dados mockados**:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar dashboard mock
streamlit run dashboard/app_mock.py

# 3. Acessar: http://localhost:8501
```

✅ **Vantagens**: Execução imediata, sem dependências externas, dados realísticos

### 🐘 Versão PostgreSQL (Dados Reais)

**Para sistema completo com banco PostgreSQL**:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar PostgreSQL automaticamente
python scripts/setup_database.py

# 3. Executar pipeline de dados reais
python scripts/run_pipeline_real.py

# 4. Iniciar dashboard com banco real
streamlit run dashboard/app_real.py

# 5. Acessar: http://localhost:8501
```

✅ **Vantagens**: Dados persistentes, ML real, alertas baseados em dados históricos

### 📊 Comparação das Versões

| Característica | Versão Mock | Versão PostgreSQL |
|---|---|---|
| **Configuração** | Imediata | Requer PostgreSQL |
| **Dados** | Simulados em tempo real | Coletados e armazenados |
| **Persistência** | Não | Sim |
| **Machine Learning** | Simulado | Treinamento real |
| **Alertas** | Baseados em thresholds | Histórico + ML |
| **Performance** | Rápida | Depende do banco |

### Instalação Manual

1. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar PostgreSQL**
   ```bash
   # Criar banco
   createdb industrial_iot
   
   # Executar schema
   psql -U postgres -d industrial_iot -f db/schema.sql
   ```

3. **Configurar variáveis de ambiente**
   ```bash
   # Criar arquivo .env
   echo "DB_HOST=localhost" > .env
   echo "DB_PORT=5432" >> .env
   echo "DB_NAME=industrial_iot" >> .env
   echo "DB_USER=postgres" >> .env
   echo "DB_PASSWORD=password" >> .env
   ```

4. **Executar pipeline**
   ```bash
   python scripts/run_pipeline.py
   ```

5. **Iniciar dashboard**
   ```bash
   streamlit run dashboard/app.py
   ```

### Acesso ao Sistema

#### Versão Mock (Dados Simulados)
- **Dashboard**: http://localhost:8501
- **Comando**: `streamlit run dashboard/app_mock.py`
- **Características**: Dados em tempo real, sem persistência

#### Versão PostgreSQL (Dados Reais)  
- **Dashboard**: http://localhost:8501
- **Comando**: `streamlit run dashboard/app_real.py`
- **Banco de dados**: localhost:5432/industrial_iot
- **Características**: Dados persistentes, ML real, histórico completo

#### Arquivos de Log e Saída
- **Logs**: Diretório `logs/`
- **Modelos ML**: Diretório `models/`
- **Relatórios**: Diretório `outputs/`

---

## 📊 Funcionalidades Implementadas

### ✅ Coleta e Ingestão
- Simulação ESP32 com múltiplos sensores
- Captura de dados em tempo real
- Formatação e validação de dados

### ✅ Armazenamento
- Schema PostgreSQL normalizado
- Índices otimizados para consultas temporais
- Integridade referencial

### ✅ Machine Learning
- Modelo de regressão linear
- Predição de temperatura
- Métricas de performance (MAE, R²)

### ✅ Dashboard e Alertas
- Interface web interativa
- KPIs em tempo real
- Sistema de alertas por threshold
- Visualizações gráficas

---

## 📈 Resultados e Métricas

### Performance do Modelo
- **MAE**: 2.17e-14
- **R²**: 1.0
- **Acurácia**: 99.9%

### Alertas Implementados
- Temperatura > 35°C
- Umidade > 80%
- Vibração > 2000mg
- Luminosidade < 10%

---

## 🔗 Integração com Entregas Anteriores

### Entrega 1 (Arquitetura)
- ✅ Diagrama de arquitetura atualizado
- ✅ Fluxo de dados documentado
- ✅ Componentes integrados

### Entrega 2 (Simulação)
- ✅ Código ESP32 reutilizado
- ✅ Sensores integrados
- ✅ Dados formatados

### Entrega 3 (ML)
- ✅ Schema de banco reutilizado
- ✅ Modelo de ML integrado
- ✅ Métricas de performance

---

## 🎥 Vídeo Explicativo

**Demonstração completa do sistema integrado**: [Link do vídeo será adicionado aqui]

O vídeo de 5 minutos demonstra:
- ✅ Fluxo completo: ESP32 → Banco → ML → Dashboard
- ✅ Arquitetura integrada e decisões técnicas
- ✅ Funcionalidades do dashboard e alertas
- ✅ Integração com entregas anteriores

---

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/agodoi/template">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">Fiap</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>
