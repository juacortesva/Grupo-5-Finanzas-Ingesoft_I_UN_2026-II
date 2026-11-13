"""Semilla idempotente de Fase 0 (Walking Skeleton).

NOTA IMPORTANTE: Los clientes de prueba (`dev-user-1`, `dev-user-2`) y el
catálogo de preguntas, opciones, pesos y puntajes incluidos en este script son
DATOS FICTICIOS / PROVISIONALES DE FASE 0, diseñados para validar el flujo
extremo a extremo (CONSERVATIVE <= 50.00, MODERATE <= 80.00, AGGRESSIVE > 80.00)
y pendientes de calibración definitiva por producto/finanzas.
"""

import sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from src.core.config import settings  # noqa: E402
from src.core.database import SessionLocal  # noqa: E402
from src.core.models import ClientModel  # noqa: E402
from src.survey.models import QuestionModel, QuestionOptionModel  # noqa: E402

# Catálogo ficticio/provisional de Fase 0 calibrado para umbrales 50.00 / 80.00:
# - Opción 1 + Opción 1 -> 15.00 + 15.00 = 30.00 (CONSERVATIVE)
# - Opción 1 + Opción 2 -> 15.00 + 35.00 = 50.00 (CONSERVATIVE, borde BR-05)
# - Opción 2 + Opción 2 -> 30.00 + 35.00 = 65.00 (MODERATE)
# - Opción 2 + Opción 3 -> 30.00 + 50.00 = 80.00 (MODERATE, borde BR-05)
# - Opción 3 + Opción 3 -> 45.00 + 50.00 = 95.00 (AGGRESSIVE)
PROVISIONAL_QUESTIONS_CATALOG: list[
    tuple[int, str, Decimal, int, bool, list[tuple[int, str, Decimal]]]
] = [
    (
        1,
        "¿Qué porcentaje de tus ingresos mensuales ahorras actualmente?",
        Decimal("1.00"),
        1,
        True,
        [
            (1, "Menos del 10%", Decimal("15.00")),
            (2, "Entre 10% y 25%", Decimal("30.00")),
            (3, "Más del 25%", Decimal("45.00")),
        ],
    ),
    (
        2,
        "¿Cómo reaccionarías ante una caída del 15% en tus inversiones?",
        Decimal("1.00"),
        2,
        True,
        [
            (1, "Vendería todo de inmediato", Decimal("15.00")),
            (2, "Esperaría a que se recupere", Decimal("35.00")),
            (3, "Invertiría más aprovechando el precio", Decimal("50.00")),
        ],
    ),
]


def seed_database(db: Session, *, commit: bool = True) -> None:
    """Siembra clientes dev y catálogo provisional de preguntas/opciones."""
    _seed_clients(db)
    _seed_questions(db)
    if commit:
        db.commit()
    else:
        db.flush()


def _seed_clients(db: Session) -> None:
    dev_clients = [
        (UUID(settings.dev_user_1_id), "dev-user-1@asesor.local"),
        (UUID(settings.dev_user_2_id), "dev-user-2@asesor.local"),
    ]
    for client_id, email in dev_clients:
        exists = db.execute(
            select(ClientModel).where(ClientModel.client_id == client_id)
        ).scalar_one_or_none()
        if exists is None:
            db.add(ClientModel(client_id=client_id, email=email))


def _seed_questions(db: Session) -> None:
    for (
        q_id,
        text_q,
        weight,
        order,
        required,
        options,
    ) in PROVISIONAL_QUESTIONS_CATALOG:
        question = db.execute(
            select(QuestionModel).where(QuestionModel.question_id == q_id)
        ).scalar_one_or_none()
        if question is None:
            question = QuestionModel(
                question_id=q_id,
                text=text_q,
                weight=weight,
                display_order=order,
                is_required=required,
                is_active=True,
            )
            for opt_num, opt_text, opt_val in options:
                question.options.append(
                    QuestionOptionModel(
                        option_number=opt_num,
                        text=opt_text,
                        value=opt_val,
                    )
                )
            db.add(question)
            continue

        question.text = text_q
        question.weight = weight
        question.display_order = order
        question.is_required = required
        question.is_active = True
        existing_opts = {opt.option_number: opt for opt in question.options}
        for opt_num, opt_text, opt_val in options:
            if opt_num in existing_opts:
                existing_opts[opt_num].text = opt_text
                existing_opts[opt_num].value = opt_val
            else:
                question.options.append(
                    QuestionOptionModel(
                        option_number=opt_num,
                        text=opt_text,
                        value=opt_val,
                    )
                )


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_database(session)
    print("Semilla provisional de Fase 0 ejecutada correctamente.")
