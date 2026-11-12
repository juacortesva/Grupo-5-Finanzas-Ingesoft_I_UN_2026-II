from collections.abc import Generator

from sqlalchemy import create_engine, text
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


def ping_database(db: Session) -> None:
    """Ejecuta `SELECT 1` para comprobar la conexión con PostgreSQL.

    Args:
        db: Sesión activa de SQLAlchemy.

    Raises:
        SQLAlchemyError: Si la base de datos no responde.
    """
    db.execute(text("SELECT 1"))
