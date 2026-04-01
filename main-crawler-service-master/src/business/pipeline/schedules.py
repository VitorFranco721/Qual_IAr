"""
Scheduled Tasks Pipeline - Business Layer
Registers and runs all scheduled jobs
"""
import logging
import time

import schedule

from src.infrastructure.config.config import config
from src.business.pipeline.jobs.iqair_job import collect_aqi_job

logger = logging.getLogger(__name__)


def run_jobs_on_startup():
    """
    Executa os jobs imediatamente quando o serviço inicia
    
    Esta função executa os jobs uma vez na inicialização do serviço,
    antes de iniciar o agendamento periódico.
    """
    logger.info("Executando jobs na inicialização do serviço...")
    
    try:
        # Executar job de coleta IQAir imediatamente
        collect_aqi_job()
        logger.info("Job de coleta IQAir executado na inicialização")
    except Exception as e:
        logger.error(f"Erro ao executar job na inicialização: {str(e)}", exc_info=True)


def register_jobs():
    """
    Register all scheduled jobs
    
    This function registers all jobs that should run on a schedule.
    Add new jobs here as they are created.
    """
    # Register IQAir AQI data collection job
    schedule.every(1).minutes.do(collect_aqi_job)
    logger.info("Job de coleta IQAir registrado - executa a cada 1 minuto")
    
    # Add more jobs here as needed
    # Example:
    # schedule.every().hour.do(some_other_job)
    # schedule.every().day.at("07:00").do(another_job)
    # schedule.every().day.at(config.SCHEDULER_DAILY_TIME).do(another_job)


def run_scheduler():
    """
    Run the scheduler loop
    
    This function runs continuously, checking for pending jobs
    and executing them at their scheduled times.
    """
    logger.info("Iniciando agendador...")
    
    # Executar jobs imediatamente na inicialização
    run_jobs_on_startup()
    
    # Registrar jobs agendados
    register_jobs()
    
    # Loop principal do agendador
    while True:
        schedule.run_pending()
        time.sleep(1)


# Run scheduler if executed directly
if __name__ == "__main__":
    run_scheduler()
