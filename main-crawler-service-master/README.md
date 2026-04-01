# Main Crawler API

Sistema de crawlers e automação web para coleta de dados AQI do IQAir. Implementa Layered Architecture para garantir escalabilidade e manutenibilidade.

## Índice

- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [API Endpoints](#api-endpoints)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Docker](#docker)
- [Desenvolvimento](#desenvolvimento)

## Tecnologias

- **Linguagem**: Python 3.11+
- **Framework**: FastAPI
- **Banco de Dados**: PostgreSQL (SQLAlchemy ORM)
- **Automação**: Selenium + Firefox (BrowserUtils)
- **Agendamento**: schedule (tarefas periódicas)
- **Integrações**: IQAir

## Arquitetura

O projeto segue uma **Layered Architecture** (Arquitetura em Camadas) para garantir separação de responsabilidades e facilitar manutenção:

```
src/
├── presentation/          # Camada de Apresentação
│   ├── controllers/      # Routers FastAPI (fino, sem lógica)
│   └── schemas/          # DTOs/Pydantic (validação entrada/saída)
│
├── business/             # Camada de Negócio
│   ├── services/        # Lógica de negócio e orquestração
│   ├── pipeline/        # Pipeline de processamento e schedules
│   └── mappers/         # Conversão entre entidades e DTOs
│
├── persistence/          # Camada de Persistência
│   ├── entities/        # Modelos de domínio (SQLAlchemy)
│   ├── repositories/    # Acesso a dados
│   └── enums/           # Enumerações
│
├── infrastructure/       # Camada de Infraestrutura
│   ├── config/          # Configurações da aplicação
│   └── external/        # Integrações com serviços externos
│
└── shared/              # Código Compartilhado
    ├── exceptions/      # Exceções customizadas
    ├── utils/           # Utilitários (BrowserUtils, DataUtils)
    ├── constants/       # Constantes da aplicação
    └── dependency_injection.py  # Injeção de dependências
```

### Princípios da Arquitetura

- **Presentation Layer**: Controllers finos, apenas roteamento e validação
- **Business Layer**: Toda lógica de negócio e orquestração
- **Persistence Layer**: Acesso a dados isolado em repositories
- **Infrastructure Layer**: Configurações e integrações externas
- **Shared Layer**: Código compartilhado entre camadas

## Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL 15 ou superior
- Git
- Docker e Docker Compose (opcional, para execução via containers)

## Instalação

### 1. Clone o repositório

```bash
git clone <repository-url>
cd main-crawler
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=admin
DB_PASSWORD=maindb
DB_SCHEMA=public
DB_CONNECT_MAX_RETRIES=30
DB_CONNECT_RETRY_DELAY_SECONDS=1

# Application
HEADLESS=True
BROWSER=chrome
CHROME_BINARY=C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
FIREFOX_BINARY=C:\\Program Files\\Mozilla Firefox\\firefox.exe
LOG_LEVEL=INFO
SCHEDULER_DAILY_TIME=07:00

```

### Banco de Dados

O banco de dados será criado automaticamente na primeira execução. Os scripts de inicialização estão em `src/infrastructure/docker/init_db/`.

## Execução

### Execução Local

```bash
# Ative o ambiente virtual
.venv\Scripts\activate  # Windows
# ou
source .venv/bin/activate  # Linux/Mac

# Execute a aplicação
c:/Users/vitor/Desktop/brasilia-air-quality/.venv-1/Scripts/python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload --app-dir main-crawler-service-master
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

####
Se estiver no Windows e o Firefox não for encontrado automaticamente, defina `FIREFOX_BINARY` no `.env` com o caminho completo do `firefox.exe`.

c:/Users/vitor/Desktop/brasilia-air-quality/.venv-1/Scripts/python.exe -c "from src.infrastructure.config.config import config; print(config.BROWSER)"

Para usar Chrome no crawler, defina `BROWSER=chrome` e, se necessário, `CHROME_BINARY` com o caminho completo do `chrome.exe`.

Para fazer apenas 1 tentativa de conexão ao banco, defina `DB_CONNECT_MAX_RETRIES=1` no `.env`.
#### 

A aplicação estará disponível em: `http://localhost:8080`

### Execução com Docker

Consulte o arquivo [docker-compose.README.md](./docker-compose.README.md) para instruções detalhadas.

```bash
docker-compose up -d
```

## API Endpoints

### Health Check

- **GET** `/health` - Health check simples
- **GET** `/health/detailed` - Health check detalhado

### IQAir

- **GET** `/api/v1/iqair/coletar-aqi` - Coletar dados AQI do IQAir
- **GET** `/api/v1/iqair/historico` - Obter histórico de dados AQI
  - Query params: `limit` (padrão: 100), `offset` (padrão: 0)

### Documentação Interativa

- **Swagger UI**: `http://localhost:8080/api/v1/docs`
- **ReDoc**: `http://localhost:8080/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8080/api/v1/openapi.json`

## Estrutura do Projeto

```
main-crawler/
├── src/
│   ├── main.py                          # Ponto de entrada FastAPI
│   │
│   ├── presentation/                    # Camada de Apresentação
│   │   ├── controllers/                 # Routers FastAPI
│   │   │   ├── health_check.py
│   │   │   └── iqair/
│   │   └── schemas/                      # DTOs/Pydantic
│   │       └── iqair/
│   │
│   ├── business/                         # Camada de Negócio
│   │   ├── services/                    # Services
│   │   │   ├── health/
│   │   │   └── iqair/
│   │   ├── pipeline/                     # Schedules e Jobs
│   │   │   ├── jobs/
│   │   │   └── schedules.py
│   │   └── mappers/                      # Mappers
│   │
│   ├── persistence/                      # Camada de Persistência
│   │   ├── entities/                     # Entidades SQLAlchemy
│   │   ├── repositories/                 # Repositories
│   │   └── enums/                        # Enumerações
│   │
│   ├── infrastructure/                   # Camada de Infraestrutura
│   │   ├── config/                        # Configurações
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── logs_config.py
│   │   │   └── cors.py
│   │   ├── external/                     # Clientes externos
│   │   └── docker/
│   │       └── init_db/                   # Scripts SQL
│   │
│   └── shared/                           # Código Compartilhado
│       ├── exceptions/                   # Exceções customizadas
│       ├── utils/                        # Utilitários
│       │   ├── browser_utils.py
│       │   └── data_utils.py
│       ├── constants/                    # Constantes
│       │   └── screen_elements/
│       └── dependency_injection.py       # DI
│
├── logs/                                 # Logs da aplicação
│
├── docker-compose.yml                    # Docker Compose
├── Dockerfile                            # Dockerfile
├── requirements.txt                      # Dependências Python
└── README.md                             # Este arquivo
```

## Docker

O projeto inclui configuração Docker completa. Consulte [docker-compose.README.md](./docker-compose.README.md) para mais detalhes.

### Comandos Rápidos

```bash
# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f crawler_service

# Parar serviços
docker-compose down

# Rebuild
docker-compose build --no-cache
```

## Desenvolvimento

### Padrões de Código

- **Classes/Enums**: PascalCase (`FooService`, `BarEnum`)
- **Funções/Variáveis**: snake_case (`buscar_pecas`, `processar_dados`)
- **Constantes**: UPPER_SNAKE_CASE (`DB_HOST`, `LOG_LEVEL`)
- **Arquivos**: snake_case (`iqair_controller.py`)

### Fluxo de Desenvolvimento

1. **Controller** (Presentation) → apenas roteamento
2. **Service** (Business) → lógica de negócio
3. **Repository** (Persistence) → acesso a dados
4. **Entity** (Persistence) → modelo de domínio

### Adicionar Novo Módulo

Siga a estrutura de camadas:

1. Entity → `persistence/entities/{module}/`
2. Repository → `persistence/repositories/{module}/`
3. Service → `business/services/{module}/`
4. Mapper → `business/mappers/{module}_mapper.py`
5. Schema → `presentation/schemas/{module}/`
6. Router → `presentation/controllers/{module}/`
7. Dependency Injection → `shared/dependency_injection.py`

### Logs

Os logs são configurados automaticamente:
- **Console**: Com cores e request ID
- **Arquivo**: Rotativo em `logs/app.log` (10MB, 5 backups)
- **Nível**: Configurável via `LOG_LEVEL` (padrão: INFO)

### Agendamento

Jobs agendados são configurados em `src/business/pipeline/schedules.py` e executados automaticamente quando a aplicação inicia.

## Licença

[Adicione informações de licença aqui]

## Contribuidores

[Adicione informações de contribuidores aqui]
