from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.infrastructure.config.config import config

SQLALCHEMY_DATABASE_URL = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_SCHEMA}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,  # Define o número máximo de conexões no pool
    max_overflow=10,  # Conexões extras além do pool_size
    pool_pre_ping=True,  # Verifica se a conexão está ativa antes de reutilizá-la
    pool_recycle=1800,  # Fecha conexões inativas após 30 minutos
    echo=False  # Desabilita logs de SQL (pode ativar para debug)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
