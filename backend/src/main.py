from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.core.database import engine

# La documentación interactiva queda bajo /api para que sea alcanzable a través
# de nginx en la VM: http://<vm>:<puerto>/api/docs
app = FastAPI(
    title="Asesor Financiero Personal API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/api/health", tags=["Health"])
def health_check() -> JSONResponse:
    """Endpoint técnico: comprueba que el backend responde y llega a PostgreSQL."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "error", "database": "unreachable"}
        )
    return JSONResponse(content={"status": "ok", "database": "ok"})


# Los routers de los módulos de dominio se registran aquí, por ejemplo:
# app.include_router(survey_router, prefix="/api")
