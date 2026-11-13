from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import register_exception_handlers
from src.survey.router import router as survey_router

app = FastAPI(
    title="Asesor Financiero Personal — API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(survey_router)


@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:  # noqa: B008
    """Verifica conectividad con la base de datos PostgreSQL."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
