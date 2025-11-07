"""
Aplicação principal FastAPI - Gerador de Comandos
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api.config import settings
from api.database import create_db_and_tables
from api.routes import health, commands

# Configurar logging
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle da aplicação.
    Executado no startup e shutdown.
    """
    # Startup
    logger.info("Iniciando aplicação...")
    # Cria tabelas (apenas para dev - em prod use Alembic)
    # create_db_and_tables()
    logger.info("Aplicação iniciada com sucesso")

    yield

    # Shutdown
    logger.info("Encerrando aplicação...")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    API para gerenciar comandos reutilizáveis com:
    - CRUD completo
    - Busca fuzzy via Meilisearch
    - Renderização de templates com variáveis
    - Validação de variáveis obrigatórias
    """,
    lifespan=lifespan
)

# CORS (ajuste origins conforme necessário)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rotas
app.include_router(health.router)
app.include_router(commands.router)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/healthz"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL
    )
