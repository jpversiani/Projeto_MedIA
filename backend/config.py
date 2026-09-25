# Arquivo: backend/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuração do projeto MedIA com padrões SUS/APS."""

    # Aplicação
    APP_NAME: str = "MedIA - Sistema de Gestão de Saúde"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///media.db"
    SECRET_KEY: str = "media-secret-key-change-in-production"

    # API
    API_PREFIX: str = "/api"
    API_VERSION: str = "v1"

    # Dashboard
    DASHBOARD_KPI_REFRESH_SECONDS: int = 30
    DASHBOARD_HEATMAP_DAYS: int = 30
    DASHBOARD_LINE_CHART_DAYS: int = 30

    # Identificação SUS/APS
    IDENTIFICATION_METHODS: list[str] = ["CNS", "CPF", "CNPJ"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
