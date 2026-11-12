from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ClientModel(Base):
    """Identidad del cliente autenticado (`userId` == `client_id`).

    Vive en `core/` porque, según la tabla de Data Ownership
    (`02_Interaction_and_Data_Design.md` §2.3), `CLIENT` no pertenece a ningún
    módulo de dominio: `survey` y `categorization` solo la referencian por FK.
    """

    __tablename__ = "client"

    client_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
