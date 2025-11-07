"""
Configuração da aplicação - carrega variáveis de ambiente
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://cmdgen:cmdgen@localhost:5432/cmdgen"

    # Meilisearch
    MEILI_URL: str = "http://localhost:7700"
    MEILI_MASTER_KEY: Optional[str] = None
    MEILI_INDEX_NAME: str = "commands"

    # API
    API_TITLE: str = "Gerador de Comandos API"
    API_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "info"

    # Timeouts (em segundos)
    DRY_RUN_DOCKER_TIMEOUT: int = 5
    DRY_RUN_PSQL_TIMEOUT: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
