from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración transversal de la aplicación cargada desde variables de entorno."""

    database_url: str
    # Orígenes permitidos por CORS, separados por coma en el .env.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    # Walking Skeleton: si no llega X-User-Id se usa el cliente demo.
    # Debe quedar en false cuando exista autenticación real.
    demo_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        """Convierte 'a,b' en ['a', 'b'] para leerlo desde el .env."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
