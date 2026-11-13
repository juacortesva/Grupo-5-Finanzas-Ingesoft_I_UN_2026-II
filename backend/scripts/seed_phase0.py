from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import SessionLocal
from src.survey.models import ClientModel, QuestionModel, QuestionOptionModel


def seed_database(db: Session) -> None:
    """Siembra clientes dev y catálogo mínimo de preguntas/opciones (idempotente)."""
    _seed_clients(db)
    _seed_questions(db)
    db.commit()


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
    catalog = [
        (
            1,
            "¿Qué porcentaje de tus ingresos mensuales ahorras actualmente?",
            Decimal("1.00"),
            1,
            True,
            [
                (1, "Menos del 10%", Decimal("20.00")),
                (2, "Entre 10% y 25%", Decimal("55.00")),
                (3, "Más del 25%", Decimal("90.00")),
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
                (2, "Esperaría a que se recupere", Decimal("60.00")),
                (3, "Invertiría más aprovechando el precio", Decimal("95.00")),
            ],
        ),
    ]
    for q_id, text_q, weight, order, required, options in catalog:
        exists = db.execute(
            select(QuestionModel).where(QuestionModel.question_id == q_id)
        ).scalar_one_or_none()
        if exists is not None:
            continue
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


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_database(session)
    print("Semilla de Fase 0 ejecutada correctamente.")
