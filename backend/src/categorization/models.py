from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.categorization.enums import EvaluationStatus
from src.core.database import Base


class FinancialProfileModel(Base):
    """Categoría de inicio vigente del cliente (BR-01)."""

    __tablename__ = "financial_profile"

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
