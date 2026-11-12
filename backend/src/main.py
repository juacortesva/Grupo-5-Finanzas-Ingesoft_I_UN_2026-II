from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db, ping_database
from src.survey.router import router as survey_router

app = FastAPI(
    title="Asesor Financiero Personal API",
    version="0.1.0",
    description="API REST modular para perfilamiento financiero (REQ-01).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(survey_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["Health"])
def health_check(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Verifica que FastAPI esté operativo y que PostgreSQL responda."""
    try:
        ping_database(db)
    except SQLAlchemyError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está disponible.",
        ) from err
    return {"status": "ok", "database": "ok"}
