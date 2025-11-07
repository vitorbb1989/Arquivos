"""
Modelos de dados usando SQLModel (SQLAlchemy + Pydantic)
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON
from pydantic import validator


class CommandBase(SQLModel):
    """Modelo base de comando"""
    name: str = Field(index=True, description="Nome curto do comando")
    description: str = Field(description="Descrição do que o comando faz")
    command_template: str = Field(description="Template do comando com placeholders ${VAR}")
    category: str = Field(index=True, description="Categoria (docker, postgres, git, k8s, etc)")
    tags: list[str] = Field(default=[], sa_column=Column(JSON), description="Tags para busca")
    variables: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON),
        description="Variáveis necessárias: {VAR: {type, default, required, description}}"
    )
    notes: Optional[str] = Field(default=None, description="Observações adicionais")


class Command(CommandBase, table=True):
    """Modelo de comando no banco de dados"""
    __tablename__ = "commands"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v):
        """Atualiza timestamp automaticamente"""
        return datetime.utcnow()


class CommandCreate(CommandBase):
    """Modelo para criação de comando (sem id/timestamps)"""
    pass


class CommandUpdate(SQLModel):
    """Modelo para atualização parcial de comando"""
    name: Optional[str] = None
    description: Optional[str] = None
    command_template: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    variables: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CommandRead(CommandBase):
    """Modelo para leitura de comando (com id/timestamps)"""
    id: int
    created_at: datetime
    updated_at: datetime


class RenderRequest(SQLModel):
    """Request para renderizar um comando"""
    command_id: int
    variables: Dict[str, str] = Field(
        default={},
        description="Valores para substituir no template"
    )


class RenderResponse(SQLModel):
    """Response do render"""
    command_id: int
    name: str
    rendered_command: str
    missing_variables: list[str] = Field(
        default=[],
        description="Variáveis obrigatórias que não foram fornecidas"
    )


class SearchRequest(SQLModel):
    """Request para busca via Meilisearch"""
    q: str = Field(description="Query de busca")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    category: Optional[str] = None


class HealthResponse(SQLModel):
    """Response do healthcheck"""
    status: str
    database: str
    meilisearch: str
    timestamp: datetime
