"""
IQAir Data Collection Job - Business Layer
Scheduled job for collecting AQI data from IQAir
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.config.config import config
from src.infrastructure.config.database import SessionLocal
from src.business.services.iqair.iqair_controller import IQAirController
from src.persistence.repositories.iqair.iqair_repository import IQAirRepository
from src.persistence.repositories.iqair.iqair_repository_with_csv_fallback import IQAirRepositoryWithCSVFallback
from src.shared.utils.csv_utils import CSVManager

logger = logging.getLogger(__name__)


def collect_aqi_job():
    """
    Scheduled job to collect AQI data from IQAir
    
    This job:
    - Opens a database session
    - Creates IQAir repository and controller
    - Collects AQI data from IQAir website
    - Saves data to database
    - Handles errors and closes database session
    """
    logger.info("Iniciando job agendado de coleta de dados AQI")
    db: Session = SessionLocal()
    
    try:
        database_available = True
        try:
            db.execute(text("SELECT 1"))
        except SQLAlchemyError as db_error:
            database_available = False
            logger.warning(f"Banco indisponível no job IQAir. Ativando CSV fallback: {db_error}")

        if database_available:
            iqair_repository = IQAirRepository(db)
        else:
            csv_manager = CSVManager(output_dir=config.CSV_OUTPUT_DIR)
            iqair_repository = IQAirRepositoryWithCSVFallback(
                db=db,
                csv_manager=csv_manager,
                database_available=False,
            )

        iqair_controller = IQAirController(iqair_repository)
        
        # Collect AQI data for one sample per discovered sensor/unit in the same session
        data_items = iqair_controller.collect_aqi_data_for_session()
        logger.info(f"Dados AQI coletados com sucesso para {len(data_items)} unidade(s)")
        
    except Exception as e:
        logger.error(f"Erro no job agendado de coleta AQI: {str(e)}", exc_info=True)
    finally:
        db.close()

