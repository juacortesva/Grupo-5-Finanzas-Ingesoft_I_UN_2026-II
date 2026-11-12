"""Carga datos de demostración para el Walking Skeleton (Fase 0, ADR-0002).

Inserta el cliente demo y un catálogo provisional de 3 preguntas. Es idempotente:
puede ejecutarse varias veces sin duplicar filas. El catálogo real de preguntas
y pesos sigue abierto (`02_Interaction_and_Data_Design.md` §5), por lo que estos
valores son solo de demostración.

Uso (desde backend/):
    python -m scripts.seed_demo
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.categorization import models as _categorization_models  # noqa: F401
from src.core.auth_deps import DEFAULT_DEMO_USER_ID
from src.core.database import SessionLocal
from src.core.models import ClientModel
from src.survey.models import QuestionModel

DEMO_EMAIL = "demo@asesor-financiero.local"


@dataclass(frozen=True)
class DemoQuestion:
    """Pregunta de demostración del catálogo provisional."""

    text: str
    weight: Decimal
    display_order: int


DEMO_QUESTIONS: tuple[DemoQuestion, ...] = (
    DemoQuestion("¿Cuál es tu horizonte de inversión?", Decimal("0.4000"), 1),
    DemoQuestion("¿Cómo reaccionas ante una pérdida del 10%?", Decimal("0.3000"), 2),
    DemoQuestion("¿Qué porcentaje de tus ingresos ahorras?", Decimal("0.3000"), 3),
)


def seed_client(db: Session) -> bool:
    """Crea el cliente demo si no existe. Retorna True si lo insertó."""
    if db.get(ClientModel, DEFAULT_DEMO_USER_ID) is not None:
        return False
    db.add(ClientModel(client_id=DEFAULT_DEMO_USER_ID, email=DEMO_EMAIL))
    return True


def seed_questions(db: Session) -> int:
    """Inserta las preguntas demo cuyo display_order activo aún no existe."""
    used_orders = set(
        db.scalars(
            select(QuestionModel.display_order).where(QuestionModel.is_active)
        ).all()
    )
    inserted = 0
    for question in DEMO_QUESTIONS:
        if question.display_order in used_orders:
            continue
        db.add(
            QuestionModel(
                text=question.text,
                weight=question.weight,
                display_order=question.display_order,
            )
        )
        inserted += 1
    return inserted


def main() -> None:
    """Ejecuta la carga de datos demo en una sola transacción."""
    with SessionLocal() as db, db.begin():
        client_created = seed_client(db)
        questions_created = seed_questions(db)
    print(  # Salida de CLI: solo contadores, sin PII.
        f"seed_demo: cliente_creado={client_created} "
        f"preguntas_creadas={questions_created}"
    )


if __name__ == "__main__":
    main()
