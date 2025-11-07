"""
Configuração do banco de dados SQLModel + SQLAlchemy
"""
from sqlmodel import SQLModel, Session, create_engine
from typing import Generator
from api.config import settings

# Engine do SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    echo=(settings.LOG_LEVEL == "debug"),
    pool_pre_ping=True,  # Verifica conexões antes de usar
    pool_size=5,
    max_overflow=10
)


def create_db_and_tables():
    """Cria todas as tabelas no banco (apenas para dev/testes)"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco de dados
    Uso: session: Session = Depends(get_session)
    """
    with Session(engine) as session:
        yield session
