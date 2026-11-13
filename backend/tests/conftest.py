"""Configuración de fixtures para pruebas unitarias y de integración.

Soporta ejecución contra PostgreSQL real cuando se define `TEST_DATABASE_URL`
(ej. el contenedor `local-db` en el puerto 5433 o una BD de pruebas dedicada).
En entornos aislados sin servidor PostgreSQL disponible, aplica un fallback
explícito a SQLite en memoria con `PRAGMA foreign_keys=ON`, el cual valida el
índice único parcial `sqlite_where=text("status = 'DRAFT'")`, `UniqueConstraint`,
`CheckConstraint` y tipos `Numeric(asdecimal=True)`.
"""

import os
from collections.abc import Generator
from typing import Any

# Garantiza que Settings() disponga de DATABASE_URL al importar src.main en
# entornos de prueba aislados, manteniendo database_url obligatorio en prod.
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:"),
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from scripts.seed_phase0 import seed_database  # noqa: E402
from src.core.database import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402


def _build_test_engine() -> Engine:
    """Construye el motor SQLAlchemy usando TEST_DATABASE_URL o fallback SQLite."""
    test_db_url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if test_db_url:
        return create_engine(test_db_url, pool_pre_ping=True)

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provee una sesión transaccional limpia con el esquema y semilla REQ-01."""
    engine = _build_test_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, class_=Session
    )
    with testing_session() as session:
        seed_database(session)
        yield session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP de pruebas conectado a la sesión de base de datos activa."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
