-- Schema para Sistema de Sensores IoT - Hermes Reply Fase 4
-- PostgreSQL 15+ com extensão UUID
-- Baseado na Entrega 3, adaptado para integração completa

create extension if not exists "uuid-ossp";

-- Tabela de Assets (Equipamentos/Linhas de Produção)
create table if not exists asset (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  location text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Tabela de Sensores
create table if not exists sensor (
  id uuid primary key default uuid_generate_v4(),
  asset_id uuid not null references asset(id) on delete cascade,
  name text not null,
  type text not null,
  unit text not null,
  min_value double precision,
  max_value double precision,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Tabela de Leituras dos Sensores
create table if not exists reading (
  id uuid primary key default uuid_generate_v4(),
  sensor_id uuid not null references sensor(id) on delete cascade,
  ts timestamptz not null,
  value double precision not null,
  created_at timestamptz default now()
);

-- Tabela de Alertas
create table if not exists alert (
  id uuid primary key default uuid_generate_v4(),
  sensor_id uuid not null references sensor(id) on delete cascade,
  alert_type text not null,
  threshold_value double precision,
  actual_value double precision,
  message text,
  severity text check (severity in ('low', 'medium', 'high', 'critical')),
  acknowledged boolean default false,
  created_at timestamptz default now()
);

-- Tabela de Predições ML
create table if not exists prediction (
  id uuid primary key default uuid_generate_v4(),
  sensor_id uuid not null references sensor(id) on delete cascade,
  predicted_value double precision not null,
  confidence double precision,
  model_version text,
  created_at timestamptz default now()
);

-- Índices para otimização de consultas
create index if not exists idx_reading_sensor_ts on reading(sensor_id, ts);
create index if not exists idx_reading_ts on reading(ts);
create index if not exists idx_reading_value on reading(value);
create index if not exists idx_alert_sensor_created on alert(sensor_id, created_at);
create index if not exists idx_prediction_sensor_created on prediction(sensor_id, created_at);

-- Comentários para documentação
comment on table asset is 'Cadastro de equipamentos e linhas de produção';
comment on table sensor is 'Metadados dos sensores vinculados aos assets';
comment on table reading is 'Leituras temporais dos sensores com timestamp UTC';
comment on table alert is 'Alertas gerados por anomalias ou thresholds';
comment on table prediction is 'Predições geradas por modelos de ML';

comment on column asset.id is 'Identificador único do asset';
comment on column asset.name is 'Nome do equipamento/linha';
comment on column asset.location is 'Localização física do asset';

comment on column sensor.id is 'Identificador único do sensor';
comment on column sensor.asset_id is 'Referência ao asset proprietário';
comment on column sensor.name is 'Nome identificador do sensor';
comment on column sensor.type is 'Tipo de medição (temperature, humidity, vibration, luminosity)';
comment on column sensor.unit is 'Unidade de medida (°C, %, mg, %)';
comment on column sensor.min_value is 'Valor mínimo esperado';
comment on column sensor.max_value is 'Valor máximo esperado';

comment on column reading.id is 'Identificador único da leitura';
comment on column reading.sensor_id is 'Referência ao sensor';
comment on column reading.ts is 'Timestamp da leitura em UTC';
comment on column reading.value is 'Valor numérico da medição';

comment on column alert.id is 'Identificador único do alerta';
comment on column alert.sensor_id is 'Referência ao sensor que gerou o alerta';
comment on column alert.alert_type is 'Tipo do alerta (threshold, anomaly, prediction)';
comment on column alert.threshold_value is 'Valor do threshold que foi violado';
comment on column alert.actual_value is 'Valor real que causou o alerta';
comment on column alert.message is 'Mensagem descritiva do alerta';
comment on column alert.severity is 'Severidade do alerta (low, medium, high, critical)';
comment on column alert.acknowledged is 'Se o alerta foi reconhecido';

comment on column prediction.id is 'Identificador único da predição';
comment on column prediction.sensor_id is 'Referência ao sensor predito';
comment on column prediction.predicted_value is 'Valor predito pelo modelo';
comment on column prediction.confidence is 'Nível de confiança da predição (0-1)';
comment on column prediction.model_version is 'Versão do modelo utilizado';

-- Função para atualizar timestamp de atualização
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Triggers para atualização automática de timestamps
create trigger update_asset_updated_at before update on asset
    for each row execute function update_updated_at_column();

create trigger update_sensor_updated_at before update on sensor
    for each row execute function update_updated_at_column();

-- View para dashboard - últimas leituras com informações dos sensores
create or replace view latest_readings as
select 
    r.ts,
    r.value,
    s.name as sensor_name,
    s.type as sensor_type,
    s.unit,
    a.name as asset_name,
    a.location
from reading r
join sensor s on r.sensor_id = s.id
join asset a on s.asset_id = a.id
where r.ts = (
    select max(ts) 
    from reading r2 
    where r2.sensor_id = r.sensor_id
);

-- View para alertas ativos
create or replace view active_alerts as
select 
    a.id,
    a.alert_type,
    a.threshold_value,
    a.actual_value,
    a.message,
    a.severity,
    a.created_at,
    s.name as sensor_name,
    s.type as sensor_type,
    ast.name as asset_name
from alert a
join sensor s on a.sensor_id = s.id
join asset ast on s.asset_id = ast.id
where a.acknowledged = false
order by a.created_at desc;

-- View para estatísticas dos sensores
create or replace view sensor_stats as
select 
    s.id,
    s.name,
    s.type,
    s.unit,
    count(r.id) as reading_count,
    min(r.ts) as first_reading,
    max(r.ts) as last_reading,
    avg(r.value) as avg_value,
    stddev(r.value) as std_value,
    min(r.value) as min_value,
    max(r.value) as max_value
from sensor s
left join reading r on s.id = r.sensor_id
group by s.id, s.name, s.type, s.unit;

-- Inserir dados iniciais para demonstração
insert into asset (name, location) values 
('Linha de Produção Principal', 'Setor A - Fábrica'),
('Equipamento de Teste', 'Laboratório');

-- Inserir sensores iniciais
insert into sensor (asset_id, name, type, unit, min_value, max_value)
select 
    a.id,
    'S_TEMP',
    'temperature',
    '°C',
    -40.0,
    80.0
from asset a where a.name = 'Linha de Produção Principal';

insert into sensor (asset_id, name, type, unit, min_value, max_value)
select 
    a.id,
    'S_HUMIDITY',
    'humidity',
    '%',
    0.0,
    100.0
from asset a where a.name = 'Linha de Produção Principal';

insert into sensor (asset_id, name, type, unit, min_value, max_value)
select 
    a.id,
    'S_LIGHT',
    'luminosity',
    '%',
    0.0,
    100.0
from asset a where a.name = 'Linha de Produção Principal';

insert into sensor (asset_id, name, type, unit, min_value, max_value)
select 
    a.id,
    'S_VIBRATION',
    'vibration',
    'mg',
    0.0,
    5000.0
from asset a where a.name = 'Linha de Produção Principal';
