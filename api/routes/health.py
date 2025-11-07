"""
Rota de healthcheck
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime
from api.database import get_session
from api.models import HealthResponse
from api.services.meilisearch_service import meili_service

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, tags=["Health"])
async def healthcheck(session: Session = Depends(get_session)):
    """
    Endpoint de health check.
    Verifica conectividade com banco de dados e Meilisearch.
    """
    # Verifica banco de dados
    try:
        # Tenta executar uma query simples
        session.exec(select(1)).first()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Verifica Meilisearch
    try:
        if meili_service.health_check():
            meili_status = "healthy"
        else:
            meili_status = "unhealthy"
    except Exception as e:
        meili_status = f"unhealthy: {str(e)}"

    # Status geral
    overall_status = "healthy" if (
        db_status == "healthy" and meili_status == "healthy"
    ) else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        meilisearch=meili_status,
        timestamp=datetime.utcnow()
    )
