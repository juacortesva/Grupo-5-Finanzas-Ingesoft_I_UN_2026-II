"""Fixtures compartidas: cada prueba corre en una transacción que se revierte.

Así las pruebas no dependen de datos precargados ni dejan basura en la BD,
aunque se ejecuten contra la base de datos de la VM.
"""

import os
from collections.abc import Generator
from decimal import Decimal
from uuid import UUID, uuid4

# Debe ir antes de importar src: Settings lee DATABASE_URL al importarse.
if test_url := os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = test_url

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import update  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from src.categorization import models as _categorization  # noqa: E402, F401
from src.core.database import engine, get_db  # noqa: E402
from src.core.models import ClientModel  # noqa: E402
from src.main import app  # noqa: E402
from src.survey.models import QuestionModel  # noqa: E402


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Sesión ligada a una transacción externa que siempre se revierte."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def api_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP cuya dependencia get_db usa la sesión transaccional."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_client(db_session: Session) -> UUID:
    """Inserta un cliente nuevo y retorna su client_id."""
    client_id = uuid4()
    db_session.add(ClientModel(client_id=client_id, email=f"{client_id}@test.local"))
    db_session.flush()
    return client_id


@pytest.fixture
def isolated_catalog(db_session: Session) -> list[QuestionModel]:
    """Desactiva el catálogo existente e inserta 3 preguntas conocidas."""
    db_session.execute(update(QuestionModel).values(is_active=False))
    questions = [
        QuestionModel(text="Pregunta 1", weight=Decimal("0.4000"), display_order=1),
        QuestionModel(text="Pregunta 2", weight=Decimal("0.3000"), display_order=2),
        QuestionModel(text="Pregunta 3", weight=Decimal("0.3000"), display_order=3),
    ]
    db_session.add_all(questions)
    db_session.flush()
    return questions
