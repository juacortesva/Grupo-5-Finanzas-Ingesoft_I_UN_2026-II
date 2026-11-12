from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.survey.router import router as survey_router

app = FastAPI(
    title="Asesor Financiero Personal API",
    version="0.1.0",
    description="API REST modular para perfilamiento financiero (REQ-01).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(survey_router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Verifica que el servidor FastAPI esté operativo."""
    return {"status": "ok"}
