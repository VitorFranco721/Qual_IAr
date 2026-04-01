"""
Ponto de entrada da aplicação - Main
Configura e inicializa o FastAPI com a nova arquitetura em camadas
"""
import logging
import threading
import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, APIRouter

from src.infrastructure.config.cors import setup_cors
from src.infrastructure.config.config import config
from src.infrastructure.config.database import engine, Base, get_db
from src.infrastructure.config.logs_config import LogsConfig, request_id_var

# Presentation Layer - Controllers
from src.presentation.controllers.health_check import router as health_router
from src.presentation.controllers.iqair.iqair_router import router as iqair_router

# Exception Handlers
from src.shared.exceptions.exception_handlers import register_exception_handlers

# -----------------------------------------------------------------------------
# Lifespan - Startup and Shutdown
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI
    Handles startup and shutdown events
    """
    # Startup
    logging.info("Iniciando aplicação...")
    
    # Start scheduler in background thread
    from src.business.pipeline.schedules import run_scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("Agendador iniciado em thread em background")
    
    yield
    
    # Shutdown
    logging.info("Encerrando aplicação...")
    # Thread daemon will be terminated automatically on shutdown


# -----------------------------------------------------------------------------
# App FastAPI
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Main Crawler API",
    description="Sistema de crawlers e automação web.",
    version="0.1.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# Exception Handlers
# -----------------------------------------------------------------------------
register_exception_handlers(app)

# -----------------------------------------------------------------------------
# Logs + Middleware de Request ID
# -----------------------------------------------------------------------------
LogsConfig()


@app.middleware("http")
async def assign_request_id(request: Request, call_next):
    """
    Middleware para atribuir ID único a cada requisição
    """
    request_id = str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    logging.info(f"Iniciando processamento da requisição {request_id}")
    response = await call_next(request)
    logging.info(f"Finalizando processamento da requisição {request_id}")
    return response


# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
setup_cors(app)

# -----------------------------------------------------------------------------
# Routers (com prefixo raiz)
# -----------------------------------------------------------------------------
api_router = APIRouter(prefix="/api/v1")

# Rotas da API
api_router.include_router(iqair_router, prefix="/iqair", tags=["IQAir"])

# Health check (sem prefixo da API)
app.include_router(health_router, tags=["Health & Metrics"])

# Incluir router da API
app.include_router(api_router)

# -----------------------------------------------------------------------------
# Banco de dados (DDL inicial)
# Fallback para CSV se o banco de dados não estiver disponível
# -----------------------------------------------------------------------------
import time
from sqlalchemy.exc import OperationalError
from src.shared.utils.csv_utils import CSVManager

max_retries = config.DB_CONNECT_MAX_RETRIES
retry_delay_seconds = config.DB_CONNECT_RETRY_DELAY_SECONDS
retry_count = 0
database_available = False

while retry_count < max_retries:
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Tabelas criadas/verificadas com sucesso")
        database_available = True
        break
    except OperationalError as e:
        retry_count += 1
        if retry_count >= max_retries:
            logging.error(f"Falha ao conectar ao banco de dados após {max_retries} tentativas: {e}")
            logging.warning("Banco de dados não disponível. Alterando para modo CSV fallback...")
            
            # Inicializa o gerenciador de CSV como fallback
            csv_manager = CSVManager(output_dir=config.CSV_OUTPUT_DIR)
            logging.info("Modo CSV fallback ativado. Os dados serão armazenados em arquivos CSV em ./output/")
            database_available = False
            break
        logging.warning(
            f"Tentando conectar ao banco de dados ({retry_count}/{max_retries})... "
            f"Aguardando {retry_delay_seconds} segundo(s)"
        )
        time.sleep(retry_delay_seconds)

# Disponibiliza o gerenciador CSV na aplicação se necessário
app.state.database_available = database_available
if not database_available:
    app.state.csv_manager = CSVManager(output_dir=config.CSV_OUTPUT_DIR)

logging.info("Serviço em execução")

# -----------------------------------------------------------------------------
# Execução local
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
