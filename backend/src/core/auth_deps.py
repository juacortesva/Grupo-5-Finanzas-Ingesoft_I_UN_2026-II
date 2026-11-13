from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import Uuid, column, select, table
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import UnauthorizedError

_CLIENT_TABLE = table("client", column("client_id", Uuid(as_uuid=True)))


def _resolve_dev_token(token: str) -> UUID | None:
    """Resuelve tokens provisionales de Fase 0 a un UUID de cliente."""
    token_map = {
        "dev-user-1": settings.dev_user_1_id,
        "dev-user-2": settings.dev_user_2_id,
    }
    raw_id = token_map.get(token, token)
    try:
        return UUID(raw_id)
    except ValueError:
        return None


def _extract_user_id(
    authorization: str | None,
    x_user_id: str | None,
) -> UUID:
    """Extrae y parsea el UUID desde Authorization Bearer o X-User-Id en dev."""
    if settings.environment != "development":
        raise UnauthorizedError("No autenticado")

    if authorization is not None:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise UnauthorizedError("No autenticado")
        parsed = _resolve_dev_token(token.strip())
        if parsed is None:
            raise UnauthorizedError("No autenticado")
        return parsed

    if settings.allow_dev_user_header and x_user_id is not None:
        parsed = _resolve_dev_token(x_user_id.strip())
        if parsed is not None:
            return parsed

    raise UnauthorizedError("No autenticado")


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),  # noqa: B008
) -> UUID:
    """Dependencia CT-02: obtiene y valida el user_id del cliente autenticado."""
    user_id = _extract_user_id(authorization=authorization, x_user_id=x_user_id)
    row = db.execute(
        select(_CLIENT_TABLE.c.client_id).where(
            _CLIENT_TABLE.c.client_id == user_id
        )
    ).first()
    if row is None:
        raise UnauthorizedError("No autenticado")
    return user_id
