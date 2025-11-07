"""
Rotas CRUD de comandos + render + search
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from api.database import get_session
from api.models import (
    Command,
    CommandCreate,
    CommandRead,
    CommandUpdate,
    RenderRequest,
    RenderResponse,
    SearchRequest
)
from api.services.meilisearch_service import meili_service
from api.services.render_service import RenderService

router = APIRouter(prefix="/commands", tags=["Commands"])


@router.post("/", response_model=CommandRead, status_code=status.HTTP_201_CREATED)
async def create_command(
    command: CommandCreate,
    session: Session = Depends(get_session)
):
    """
    Cria um novo comando.
    Sincroniza automaticamente com Meilisearch.
    """
    db_command = Command.model_validate(command)
    session.add(db_command)
    session.commit()
    session.refresh(db_command)

    # Sincroniza com Meilisearch
    meili_service.add_command(db_command)

    return db_command


@router.get("/", response_model=List[CommandRead])
async def list_commands(
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    session: Session = Depends(get_session)
):
    """
    Lista comandos com paginação e filtro por categoria.
    """
    query = select(Command)

    if category:
        query = query.where(Command.category == category)

    query = query.offset(skip).limit(limit)
    commands = session.exec(query).all()
    return commands


@router.get("/{command_id}", response_model=CommandRead)
async def get_command(
    command_id: int,
    session: Session = Depends(get_session)
):
    """
    Busca comando por ID.
    """
    command = session.get(Command, command_id)
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comando {command_id} não encontrado"
        )
    return command


@router.patch("/{command_id}", response_model=CommandRead)
async def update_command(
    command_id: int,
    command_update: CommandUpdate,
    session: Session = Depends(get_session)
):
    """
    Atualiza comando parcialmente.
    Sincroniza automaticamente com Meilisearch.
    """
    db_command = session.get(Command, command_id)
    if not db_command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comando {command_id} não encontrado"
        )

    # Atualiza apenas campos fornecidos
    update_data = command_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_command, key, value)

    session.add(db_command)
    session.commit()
    session.refresh(db_command)

    # Sincroniza com Meilisearch
    meili_service.update_command(db_command)

    return db_command


@router.delete("/{command_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_command(
    command_id: int,
    session: Session = Depends(get_session)
):
    """
    Remove comando.
    Remove também do Meilisearch.
    """
    db_command = session.get(Command, command_id)
    if not db_command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comando {command_id} não encontrado"
        )

    session.delete(db_command)
    session.commit()

    # Remove do Meilisearch
    meili_service.delete_command(command_id)

    return None


@router.post("/render", response_model=RenderResponse)
async def render_command(
    request: RenderRequest,
    session: Session = Depends(get_session)
):
    """
    Renderiza comando substituindo variáveis.

    Exemplo:
        POST /commands/render
        {
            "command_id": 1,
            "variables": {
                "SERVICE": "postgres_postgres",
                "SHELL": "bash"
            }
        }
    """
    # Busca comando
    command = session.get(Command, request.command_id)
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comando {request.command_id} não encontrado"
        )

    # Aplica valores padrão
    variables_with_defaults = RenderService.apply_defaults(
        command.variables,
        request.variables
    )

    # Valida variáveis obrigatórias
    missing_vars = RenderService.validate_required_variables(
        command.variables,
        variables_with_defaults
    )

    # Renderiza template
    rendered, _ = RenderService.render(
        command.command_template,
        variables_with_defaults
    )

    return RenderResponse(
        command_id=command.id,
        name=command.name,
        rendered_command=rendered,
        missing_variables=missing_vars
    )


@router.post("/search")
async def search_commands(request: SearchRequest):
    """
    Busca comandos via Meilisearch.

    Suporta:
    - Busca por texto (fuzzy, typo-tolerant)
    - Filtro por categoria
    - Paginação

    Exemplo:
        POST /commands/search
        {
            "q": "docker exec",
            "limit": 10,
            "offset": 0,
            "category": "docker"
        }
    """
    results = meili_service.search(
        query=request.q,
        limit=request.limit,
        offset=request.offset,
        category=request.category
    )

    return {
        "hits": results.get("hits", []),
        "total": results.get("estimatedTotalHits", 0),
        "offset": request.offset,
        "limit": request.limit
    }


@router.post("/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_meilisearch(session: Session = Depends(get_session)):
    """
    Reindexar todos os comandos no Meilisearch.
    Útil após importação em massa ou correção de dados.
    """
    # Busca todos os comandos do banco
    commands = session.exec(select(Command)).all()

    # Reindexar
    success = meili_service.reindex_all(commands)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao reindexar comandos"
        )

    return {
        "message": f"{len(commands)} comandos reindexados com sucesso",
        "count": len(commands)
    }
