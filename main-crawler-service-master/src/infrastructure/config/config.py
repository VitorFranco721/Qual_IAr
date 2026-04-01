import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]


def _load_env_file(env_path: Path, override: bool) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue

        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if override or key not in os.environ:
            os.environ[key] = value


# Ordem de prioridade:
# 1) .env (sobrescreve anteriores)
# 2) .env.dev
# 3) .env.docker
_load_env_file(BASE_DIR / '.env.docker', override=False)
_load_env_file(BASE_DIR / '.env.dev', override=False)
_load_env_file(BASE_DIR / '.env', override=True)


class Config:
    # Daily schedule time (HH:MM format)
    SCHEDULER_DAILY_TIME = os.getenv('SCHEDULER_DAILY_TIME', "07:00")

    # Definir se o navegador será aberto no modo visual ou não
    HEADLESS = os.getenv('HEADLESS', "False").lower() == "true"

    # Caminho opcional para o executável do Firefox
    FIREFOX_BINARY = os.getenv('FIREFOX_BINARY')
    # Caminho opcional para o executável do Chrome
    CHROME_BINARY = os.getenv('CHROME_BINARY')
    # Navegador do crawler: chrome, firefox ou auto
    BROWSER = os.getenv('BROWSER', 'firefox').lower()

    # Modo de apresentação dos logs: INFO, DEBUG, etc...
    LOG_MODE = os.getenv('LOG_MODE', 20)

    # Configurações de banco de dados
    DB_USER = os.getenv('DB_USER', 'admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'maindb')
    DB_HOST = os.getenv('DB_HOST', 'postgres')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'public')
    DB_NAME = os.getenv('DB_NAME', 'postgres')
    DB_CONNECT_MAX_RETRIES = int(os.getenv('DB_CONNECT_MAX_RETRIES', '30'))
    DB_CONNECT_RETRY_DELAY_SECONDS = float(os.getenv('DB_CONNECT_RETRY_DELAY_SECONDS', '1'))
    CSV_OUTPUT_DIR = os.getenv('CSV_OUTPUT_DIR', 'output')


# Instância da configuração para ser utilizada no restante do código
config = Config()
