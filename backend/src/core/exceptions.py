from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Excepción base de dominio para traducirse en la frontera HTTP."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UnauthorizedError(DomainError):
    """Credencial ausente, inválida o de cliente inexistente (CT-02)."""

    status_code = status.HTTP_401_UNAUTHORIZED


class NotFoundError(DomainError):
    """Recurso inexistente o perteneciente a otro usuario (CT-07)."""

    status_code = status.HTTP_404_NOT_FOUND


class InvalidStateError(DomainError):
    """Operación incompatible con el estado COMPLETED de la encuesta (BR-03)."""

    status_code = status.HTTP_409_CONFLICT


class ValidationError(DomainError):
    """Violación de regla de validación de entrada o catálogo (422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


class InvalidInputError(DomainError):
    """Entrada inválida en capa interna de dominio."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


class EvaluationPersistenceError(DomainError):
    """Fallo doble al persistir la categoría provisional UNDER_EVALUATION (BR-06)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


def register_exception_handlers(app: FastAPI) -> None:
    """Registra traductores globales de excepciones de dominio a JSON estándar."""

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
