"""Configuração central do Projeto MedIA/PEC (componentes C29 e C30)."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Configurações tipadas da aplicação (Pydantic v2, imutável por padrão de leitura)."""

    model_config = {"frozen": True}

    PROJECT_NAME: str = "MedIA - Prontuário Eletrônico do Cidadão (PEC)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # SQLite para desenvolvimento local imediato; PostgreSQL em produção.
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./esus.db")
    )

    # Contingência offline (C29)
    MAX_ITENS_LOTE_SYNC: int = 500


settings = Settings()
