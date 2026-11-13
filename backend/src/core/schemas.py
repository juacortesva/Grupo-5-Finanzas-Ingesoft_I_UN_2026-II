from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelCaseSchema(BaseModel):
    """Clase base para todos los DTOs expuestos en la API REST."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ErrorResponse(CamelCaseSchema):
    """Formato estándar del cuerpo de error HTTP según FastAPI."""

    detail: str
