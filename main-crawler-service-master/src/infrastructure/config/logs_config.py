import logging
import os
import sys
import contextvars
from logging.handlers import RotatingFileHandler

# Variável de contexto para armazenar o ID da requisição
request_id_var = contextvars.ContextVar("request_id", default="global")


class RequestIdFilter(logging.Filter):
    """Filtro para adicionar o ID da requisição aos logs"""

    def filter(self, record):
        record.request_id = request_id_var.get()  # Obtém o ID da requisição atual
        return True


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para console"""

    # Códigos de cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record):
        # Adicionar cor baseada no nível
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        # Formato com cores
        colored_format = f"{color}%(levelname)s{reset}: %(asctime)s - Thread #%(request_id)s - %(message)s"
        formatter = logging.Formatter(colored_format)
        return formatter.format(record)


class LogsConfig:
    def __init__(self):
        # Usar caminho absoluto para garantir que os logs sejam criados na pasta raiz do projeto
        if hasattr(sys, '_MEIPASS'):
            # Se estiver executando como executável (PyInstaller)
            log_dir = os.path.join(os.path.dirname(sys.executable), "logs")
        else:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
            log_dir = os.path.abspath(log_dir)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Limpar handlers existentes para evitar duplicação
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Configurar nível de log baseado em variável de ambiente
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Formato dos logs para arquivo (sem cores)
        file_format = logging.Formatter(
            "%(levelname)s: %(asctime)s - Thread #%(request_id)s - %(name)s - %(message)s"
        )

        # Formato dos logs para console (com cores)
        console_format = ColoredFormatter()

        # Criar filtro de Request ID
        request_id_filter = RequestIdFilter()

        # Configurar RotatingFileHandler (rotação automática)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(file_format)
        file_handler.addFilter(request_id_filter)
        file_handler.setLevel(logging.DEBUG)  # Arquivo sempre DEBUG
        root_logger.addHandler(file_handler)

        # Configurar StreamHandler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_format)
        console_handler.addFilter(request_id_filter)
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        root_logger.addHandler(console_handler)

        # Configurar logger específico para SQLAlchemy (menos verboso)
        sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
        sqlalchemy_logger.setLevel(logging.WARNING)

        # Configurar logger para uvicorn (menos verboso)
        uvicorn_logger = logging.getLogger('uvicorn')
        uvicorn_logger.setLevel(logging.INFO)
        uvicorn_access_logger = logging.getLogger('uvicorn.access')
        uvicorn_access_logger.setLevel(logging.WARNING)

        logging.info("Logs configurados com sucesso")
        logging.info(f"Nível de log configurado: {log_level}")
        logging.info(f"Diretório de logs: {os.path.abspath(log_dir)}")


# Configurar encoding do stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

