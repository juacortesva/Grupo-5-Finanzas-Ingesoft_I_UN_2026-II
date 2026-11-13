from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class FinancialProfileModel(Base):
    """Modelo SQLAlchemy de la tabla financial_profile (BR-04, BR-06)."""

    __tablename__ = "financial_profile"
    __table_args__ = (
        CheckConstraint(
            "(evaluation_status = 'ERROR' "
            "AND assigned_category = 'UNDER_EVALUATION' "
            "AND total_score IS NULL) "
            "OR "
            "(evaluation_status = 'COMPLETED' "
            "AND assigned_category IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE') "
            "AND total_score IS NOT NULL)",
            name="ck_financial_profile_br06_coherence",
        ),
    )

    profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    client_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("client.client_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    survey_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("survey.survey_id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_category: Mapped[str] = mapped_column(String(32), nullable=False)
    evaluation_status: Mapped[str] = mapped_column(String(16), nullable=False)
    total_score: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
