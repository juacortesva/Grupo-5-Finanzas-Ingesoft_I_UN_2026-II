from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings


class Base(DeclarativeBase):
    """Clase base de los modelos SQLAlchemy."""


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesión de base de datos por petición y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
