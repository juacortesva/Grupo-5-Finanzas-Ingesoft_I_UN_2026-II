from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración transversal cargada desde variables de entorno."""

    database_url: str
    environment: str = "development"
    dev_user_1_id: str = "00000000-0000-0000-0000-000000000001"
    dev_user_2_id: str = "00000000-0000-0000-0000-000000000002"
    allow_dev_user_header: bool = True
    cors_origins: list[str] = [
        "http://localhost:3005",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
