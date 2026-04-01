-- Criar banco de dados postgres se não existir
CREATE DATABASE postgres;

-- Conectar ao banco postgres
\c postgres

-- Criar tabelas
CREATE TABLE IF NOT EXISTS iqair_data (
    id SERIAL PRIMARY KEY,
    aqi_score INTEGER NOT NULL,
    aqi_category VARCHAR,
    main_pollutant VARCHAR,
    pollutant_concentration VARCHAR,
    temperature VARCHAR,
    wind_speed VARCHAR,
    humidity VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for IQAir data
CREATE INDEX IF NOT EXISTS idx_iqair_data_id ON iqair_data(id);
CREATE INDEX IF NOT EXISTS idx_iqair_data_created_at ON iqair_data(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_iqair_data_aqi_score ON iqair_data(aqi_score);
