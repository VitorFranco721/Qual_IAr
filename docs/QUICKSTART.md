# Guia rápido

Este guia mostra o passo a passo para configurar o ambiente, descobrir fontes,
executar o ETL e carregar os dados em banco. O foco é facilitar o uso para
quem ainda está começando.

## Pré-requisitos

* **Python 3.11+**
* **Docker** (opcional)

## Configuração inicial

Clone o repositório e crie um ambiente virtual:

    git clone https://github.com/your-username/brasilia-air-quality.git
    cd brasilia-air-quality
    python -m venv .venv

No Windows:

    .venv\Scripts\activate

No Linux/macOS:

    source .venv/bin/activate

Instale dependências:

    pip install -r requirements.unique.txt

## 1) Descobrir fontes

    python -m br.aqi.cli discover

Gera o índice em `artifacts/sources_index.json`.

## 2) Extrair dados brutos (Bronze)

    python -m br.aqi.cli extract --since 2020-01-01 --until today

Saída em `data/bronze`.

Se o crawler IQAir estiver no mesmo repositório, os CSVs em
`main-crawler-service-master/output/*.csv` também serão incorporados.

## 3) Normalizar (Silver)

    python -m br.aqi.cli normalize

Saída em `data/silver`.

## 4) Validar

    python -m br.aqi.cli validate

Se houver inconsistências, o comando termina com erro e lista os problemas.

## 5) Exportar

    python -m br.aqi.cli export

Gera arquivos particionados em `data/export/year=YYYY/month=MM/`.

## 6) Carregar em banco (Gold/Serving)

    python -m br.aqi.cli load

Por padrão carrega em SQLite (`data/gold/air_quality.db`).

Para também carregar em MongoDB:

    # PowerShell (sessão atual)
    $env:AQI_MONGO_URI="mongodb+srv://vitorfranco_db_user:RSH47ZCrQ3obI8Iq@clusterrespirar.mcuc0vt.mongodb.net/"

    # Persistir no Windows (novos terminais)
    setx AQI_MONGO_URI "mongodb+srv://vitorfranco_db_user:RSH47ZCrQ3obI8Iq@clusterrespirar.mcuc0vt.mongodb.net/"

    python -m br.aqi.cli load --mongo-database air_quality --mongo-collection measurements

## Comandos Makefile

    make setup
    make discover
    make extract
    make normalize
    make validate
    make export
    make load
    make all