from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException, status

DEFAULT_DEMO_USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def get_current_user(
    x_user_id: Annotated[str | None, Header()] = None,
) -> UUID:
    """Obtiene el userId autenticado desde el contexto de sesión/cabecera.

    Para el Walking Skeleton (Fase 0), usa el usuario semilla de demostración
    si no se envía la cabecera X-User-Id.
    """
    if x_user_id is None:
        return DEFAULT_DEMO_USER_ID
    try:
        return UUID(x_user_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuario inválido.",
        ) from err
