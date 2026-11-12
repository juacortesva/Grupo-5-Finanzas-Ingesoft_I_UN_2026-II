from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.categorization.enums import EvaluationStatus
from src.core.database import Base


class FinancialProfileModel(Base):
    """Categoría de inicio vigente del cliente (BR-01)."""

    __tablename__ = "financial_profile"
    __table_args__ = (
        CheckConstraint(
            "assigned_category IN "
            "('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE', 'UNDER_EVALUATION')",
            name="ck_financial_profile_category_valid",
        ),
        CheckConstraint(
            "evaluation_status IN ('COMPLETED', 'ERROR')",
            name="ck_financial_profile_status_valid",
        ),
        # REQ-01 Escenario 3: ERROR => UNDER_EVALUATION y total_score nulo.
        CheckConstraint(
            "evaluation_status <> 'ERROR' OR "
            "(assigned_category = 'UNDER_EVALUATION' AND total_score IS NULL)",
            name="ck_financial_profile_error_is_provisional",
        ),
    )

    profile_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("client.client_id"), unique=True, nullable=False
    )
    survey_id: Mapped[UUID] = mapped_column(
        ForeignKey("survey.survey_id"), nullable=False
    )
    assigned_category: Mapped[str] = mapped_column(String(30), nullable=False)
    evaluation_status: Mapped[str] = mapped_column(
        String(20), default=EvaluationStatus.COMPLETED.value, nullable=False
    )
    total_score: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4, asdecimal=True), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
