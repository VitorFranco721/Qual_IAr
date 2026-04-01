# Projeto Brasília Air Quality

Este repositório implementa um pipeline reprodutível para descobrir, extrair,
tratar, validar e disponibilizar dados de qualidade do ar do Distrito Federal
(Brasília/DF).

## Objetivo

Centralizar dados de fontes oficiais em um fluxo único, com arquitetura
medalhão:

- **Bronze:** dados brutos
- **Silver:** dados padronizados
- **Gold/Serving:** dados prontos para consumo em banco

## Principais funcionalidades

* **Descoberta de fontes (RAG)** para organizar e ranquear fontes oficiais.
* **Conectores de extração** para ArcGIS, MonitorAr e ponte com crawler IQAir.
* **Normalização** de colunas, unidades e timestamps.
* **Validação de qualidade** com regras de consistência.
* **Exportação particionada** por ano/mês.
* **Carga em banco** para SQLite e MongoDB (opcional).

## Fontes de dados

As fontes atuais estão detalhadas em [SOURCES.md](SOURCES.md), incluindo URLs,
agências responsáveis e limitações conhecidas.

## Estrutura do repositório

```text
brasilia-air-quality/
├─ br/aqi/               # Código principal do ETL
├─ data/bronze/          # Camada Bronze (dados brutos)
├─ data/silver/          # Camada Silver (dados normalizados)
├─ data/gold/            # Camada Gold/Serving (banco SQLite)
├─ data/export/          # Exportações particionadas
├─ artifacts/            # Cache e artefatos auxiliares
├─ docs/                 # Documentação do projeto
├─ tests/                # Testes automatizados
└─ main-crawler-service-master/  # Serviço crawler integrado
```

## Começando

Consulte [QUICKSTART.md](QUICKSTART.md) para o passo a passo completo.

Comandos essenciais:

    python -m br.aqi.cli discover
    python -m br.aqi.cli extract --since 2020-01-01 --until today
    python -m br.aqi.cli normalize
    python -m br.aqi.cli validate
    python -m br.aqi.cli export
    python -m br.aqi.cli load
