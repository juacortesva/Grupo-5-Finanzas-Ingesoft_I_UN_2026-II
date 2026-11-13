from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from scripts.seed_phase0 import seed_database
from src.core.database import Base, get_db
from src.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provee una sesión SQLite aislada en memoria con el esquema REQ-01."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, class_=Session
    )
    with testing_session() as session:
        seed_database(session)
        yield session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP de pruebas conectado a la sesión en memoria."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
