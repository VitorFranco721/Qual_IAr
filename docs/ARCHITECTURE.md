# Arquitetura

O projeto **Brasília Air Quality** foi organizado como um pipeline de dados
simples, porém extensível. O foco é manter separação de responsabilidades,
reprodutibilidade e facilidade de manutenção para quem está começando.

## Etapas do pipeline (arquitetura medalhão)

1. **Descoberta (RAG)** — O módulo `br/aqi/rag.py` identifica e classifica
   fontes oficiais de dados. O resultado é salvo em
   `artifacts/sources_index.json`.

2. **Extração (Bronze)** — O módulo `br/aqi/sources.py` contém conectores para
   baixar dados brutos. Cada conector implementa o método assíncrono
   `extract()`. Os arquivos de saída são gravados em `data/bronze`.

3. **Normalização (Silver)** — O módulo `br/aqi/normalize.py` padroniza nomes
   de colunas, poluentes, unidades e datas/horários. Os dados tratados são
   gravados em `data/silver`.

4. **Validação** — O módulo `br/aqi/validate.py` verifica qualidade dos dados:
   colunas obrigatórias, faixas plausíveis de valores, monotonicidade temporal
   e coordenadas válidas.

5. **Exportação** — O módulo `br/aqi/export.py` particiona os dados Silver por
   ano e mês em `data/export`, facilitando consumo incremental.

6. **Carga (Gold/Serving)** — O módulo `br/aqi/load.py` carrega os dados Silver
   para camadas de consumo: SQLite por padrão (`data/gold/air_quality.db`) e,
   opcionalmente, MongoDB via variável `AQI_MONGO_URI`.

## Ponte com o crawler

O conector `IQAirCrawlerOutputSource` em `br/aqi/sources.py` lê os CSVs gerados
em `main-crawler-service-master/output` e os converte para o contrato Bronze.
Assim, o crawler pode evoluir de forma independente sem quebrar o ETL.

## Observabilidade

O projeto usa `structlog` para logs estruturados. Cada etapa registra contexto
útil (origem, quantidade de linhas, caminhos de saída, erros), o que ajuda na
depuração e na operação diária.

## Agendamento e execução

O pipeline pode rodar de forma manual (CLI/Makefile) ou agendada (cron,
Docker Compose, Airflow). Em CI/CD, a recomendação é executar lint, testes e
validação de dados antes de publicar artefatos.

## Extensão do projeto

Para adicionar uma nova fonte:

1. Crie um novo conector em `br/aqi/sources.py` implementando `extract()`.
2. Registre o conector em `get_sources()`.
3. Garanta que as colunas necessárias existam para normalização e validação.
4. Execute `normalize`, `validate`, `export` e `load` para verificar o fluxo.