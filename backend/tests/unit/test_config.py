"""Pruebas unitarias sin base de datos de la configuración transversal."""

from src.core.config import Settings


def test_settings_when_cors_origins_is_csv_then_returns_list() -> None:
    # Arrange
    raw = "http://10.0.0.5:5173, http://localhost:5173"

    # Act
    settings = Settings(database_url="postgresql+psycopg://x", cors_origins=raw)

    # Assert
    assert settings.cors_origins == ["http://10.0.0.5:5173", "http://localhost:5173"]
