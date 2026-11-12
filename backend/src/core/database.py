from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings


class Base(DeclarativeBase):
    """Clase base declarativa para los modelos SQLAlchemy del sistema."""


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Provee una sesión transaccional de PostgreSQL por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
