from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.core.models import ClientModel

DEFAULT_DEMO_USER_ID = UUID("11111111-1111-1111-1111-111111111111")

_UNAUTHORIZED_DETAIL = "No fue posible identificar al usuario."


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail=_UNAUTHORIZED_DETAIL
    )


def _parse_user_id(x_user_id: str | None) -> UUID:
    """Traduce la cabecera X-User-Id a UUID aplicando el modo demo."""
    if x_user_id is None:
        if not settings.demo_mode:
            raise _unauthorized()
        return DEFAULT_DEMO_USER_ID
    try:
        return UUID(x_user_id)
    except ValueError as err:
        raise _unauthorized() from err


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    x_user_id: Annotated[str | None, Header()] = None,
) -> UUID:
    """Obtiene el userId autenticado desde el contexto de sesión/cabecera.

    Walking Skeleton (Fase 0): sustituye a un módulo de autenticación real
    (fuera del alcance de REQ-01). El userId nunca se lee del body (REQ-01).

    Args:
        db: Sesión de base de datos de la petición.
        x_user_id: Valor de la cabecera `X-User-Id`, si se envió.

    Returns:
        El `client_id` del cliente autenticado.

    Raises:
        HTTPException: 401 si la cabecera es inválida, falta sin `DEMO_MODE`
            o el cliente no existe (contrato `startSurvey`, diseño 02 §3).
    """
    user_id = _parse_user_id(x_user_id)
    if db.get(ClientModel, user_id) is None:
        raise _unauthorized()
    return user_id
