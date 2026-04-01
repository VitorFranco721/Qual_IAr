# Docker Compose Setup

## Pré-requisitos

- Docker
- Docker Compose

## Configuração

1. Copie o arquivo de exemplo de variáveis de ambiente:
   ```bash
   cp .env.docker.example .env.docker
   ```

2. Edite o arquivo `.env.docker` com suas configurações:
   ```env
   DB_USER=admin
   DB_PASSWORD=maindb
   DB_HOST=postgres
   DB_PORT=5432
   DB_NAME=postgres
   DB_SCHEMA=public
   HEADLESS=True
   LOG_LEVEL=INFO
   SCHEDULER_DAILY_TIME=07:00
   ```

## Uso

### Iniciar os serviços
```bash
docker-compose up -d
```

### Ver logs
```bash
docker-compose logs -f crawler_service
```

### Parar os serviços
```bash
docker-compose down
```

### Parar e remover volumes (limpar dados)
```bash
docker-compose down -v
```

### Rebuild da imagem
```bash
docker-compose build --no-cache
```

### Acessar a API
- API: http://localhost:8080
- Docs: http://localhost:8080/api/v1/docs
- Health: http://localhost:8080/health

## Estrutura

- **crawler_service**: Aplicação FastAPI
- **postgres**: Banco de dados PostgreSQL

## Volumes

- `./logs`: Logs da aplicação
- `postgres_data`: Dados persistentes do PostgreSQL

## Health Checks

O endpoint `/health` está disponível para serviços externos de monitoramento (Kubernetes, Prometheus, etc.) fazerem verificações periódicas. O Docker não realiza healthchecks automáticos.

