"""Configuração central do Projeto MedIA/PEC.

Fonte única de verdade, carregada de variáveis de ambiente e do arquivo `.env`
(raiz do repositório ou `backend/`). Antes esta configuração lia `os.getenv`
diretamente, o que fazia o `.env` ser IGNORADO: o `.env.example` documentava
`SECRET_KEY` enquanto o código lia `JWT_SECRET_KEY`, de modo que a chave
definida pelo operador nunca era aplicada.
"""

from __future__ import annotations

import os
import warnings
from typing import List, Literal, Optional

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Chave usada APENAS em desenvolvimento/testes. Nunca é aceitável em produção:
# qualquer pessoa que a conheça consegue forjar um JWT de administrador.
DEV_FALLBACK_SECRET = "media_secret_jwt_sovereign_clinical_2026_key"


def _sqlite_padrao() -> str:
    """SQLite padrão ancorado em `backend/`, e não no diretório de trabalho.

    Com `sqlite:///./esus.db` o arquivo nascia no diretório de onde o processo
    foi iniciado: `start.sh` faz `cd backend`, o README manda rodar a partir de
    `backend/`, mas o pytest roda da raiz do repositório. O resultado eram DUAS
    bases diferentes conforme o comando usado, e um banco "vazio" surpreendente
    depois de popular um dos dois.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    caminho = os.path.join(backend_dir, "esus.db").replace("\\", "/")
    return f"sqlite:///{caminho}"


def _env_files() -> tuple[str, ...]:
    """Localiza o `.env` na raiz do repositório e/ou em `backend/`."""
    here = os.path.dirname(os.path.abspath(__file__))  # backend/app/core
    backend_dir = os.path.abspath(os.path.join(here, "..", ".."))
    repo_dir = os.path.abspath(os.path.join(backend_dir, ".."))
    candidatos = [os.path.join(repo_dir, ".env"), os.path.join(backend_dir, ".env")]
    return tuple(p for p in candidatos if os.path.isfile(p))


class Settings(BaseSettings):
    """Configurações tipadas da aplicação (Pydantic v2 + pydantic-settings)."""

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    PROJECT_NAME: str = "MedIA - Prontuário Eletrônico do Cidadão (PEC)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    @field_validator(
        "JWT_SECRET_KEY",
        "GEMINI_API_KEY",
        "TURN_SECRET",
        "GOOGLE_CLIENT_ID",
        "MICROSOFT_CLIENT_ID",
        mode="before",
    )
    @classmethod
    def _opcional_em_branco_vira_none(cls, valor):
        """`CHAVE=` vazia no `.env` significa "não definido", não string vazia."""
        if isinstance(valor, str):
            return valor.strip() or None
        return valor

    @field_validator("DATABASE_URL", "CORS_ORIGINS", "LOG_LEVEL", "ENVIRONMENT", mode="before")
    @classmethod
    def _branco_usa_padrao(cls, valor, info):
        """Para campos com padrão, o valor em branco cai no padrão.

        O `.env.example` é distribuído com placeholders vazios; sem isto,
        copiar o arquivo e preencher só o necessário deixaria
        `DATABASE_URL=""` (quebrando `create_engine`) e `CORS_ORIGINS=""`
        (desligando todo o CORS silenciosamente).
        """
        if isinstance(valor, str) and not valor.strip():
            padroes = {
                "DATABASE_URL": _sqlite_padrao(),
                "CORS_ORIGINS": "http://localhost:8000,http://127.0.0.1:8000",
                "LOG_LEVEL": "info",
                "ENVIRONMENT": "development",
            }
            return padroes[info.field_name]
        return valor

    # -- Ambiente ----------------------------------------------------------
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    LOG_LEVEL: str = "info"

    # -- Segurança ---------------------------------------------------------
    # `SECRET_KEY` é aceito como alias legado do `.env.example` existente.
    JWT_SECRET_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )

    # -- Banco de dados ---------------------------------------------------
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL") or _sqlite_padrao()
    )

    # -- HTTP / CORS -------------------------------------------------------
    # Lista separada por vírgula (formato simples, sem JSON obrigatório).
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    # -- Funcionalidades ---------------------------------------------------
    # Exige `Authorization: Bearer <token>` em TODAS as rotas clínicas.
    # Hoje apenas 3 rotas (/auth/me, /auth/switch-clinic, /auth/audit-trail)
    # validam o token; as demais ~88 aceitavam requisição anônima, o que
    # expunha prontuário, prescrição e faturamento a qualquer chamada HTTP.
    # Ligado por padrão fora de desenvolvimento.
    REQUIRE_AUTH: bool = False
    # Aplica `alembic upgrade head` no startup. Em produção, prefira rodar
    # `alembic upgrade head` como passo explícito de deploy (job/container).
    AUTO_MIGRATE_ON_STARTUP: bool = True
    # Popula clinics/profissionais/usuários de demonstração no primeiro boot.
    # Nunca deve ser ligado em produção.
    AUTO_SEED_DEMO_DATA: bool = True
    # Login instantâneo via `demo_role` (sem senha). Desligar fora de dev.
    DEMO_LOGIN_ENABLED: bool = True
    # Callbacks SSO Google/Microsoft. O mock de interface fica ligado em
    # desenvolvimento, mas NUNCA em produção (ver `_exigir_sso_habilitado`).
    SSO_ENABLED: bool = True

    # -- Integrações -------------------------------------------------------
    GEMINI_API_KEY: Optional[str] = None
    TURN_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None

    # Contingência offline (C29)
    MAX_ITENS_LOTE_SYNC: int = 500

    # -- Derivados ---------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT in ("development", "test")

    @property
    def require_auth(self) -> bool:
        """Autenticação obrigatória: ligada por padrão fora de desenvolvimento.

        Em desenvolvimento e nos testes permanece desligada para que a suíte e
        o uso local funcionem sem token. Em staging/produção é OBRIGATÓRIA.
        """
        if self.ENVIRONMENT in ("production", "staging"):
            return True
        return self.REQUIRE_AUTH

    def validar_ambiente(self) -> None:
        """Falha rápida em configurações que exponham dados de saúde."""
        problemas: List[str] = []

        if self.is_production:
            if not self.JWT_SECRET_KEY:
                problemas.append(
                    "JWT_SECRET_KEY/SECRET_KEY ausente (a chave padrão de "
                    "desenvolvimento é pública e permitiria forjar tokens)."
                )
            if not self.require_auth:  # pragma: no cover - inalcançável hoje
                problemas.append("REQUIRE_AUTH desligado em produção.")
            if self.AUTO_SEED_DEMO_DATA:
                problemas.append(
                    "AUTO_SEED_DEMO_DATA ligado em produção popularia "
                    "prontuários fictícios na base real (viola a LGPD)."
                )
            if self.DEMO_LOGIN_ENABLED:
                problemas.append("DEMO_LOGIN_ENABLED ligado em produção.")
            if self.SSO_ENABLED:
                problemas.append(
                    "SSO_ENABLED ligado em produção, mas o mock de SSO não "
                    "valida o id_token. Implemente a verificação JWKS antes."
                )

        if problemas:
            raise RuntimeError(
                "Configuração insegura para o ambiente "
                f"{self.ENVIRONMENT!r}:\n  - " + "\n  - ".join(problemas)
            )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def effective_secret_key(self) -> str:
        """Resolve a chave de assinatura do JWT, falhando alto em produção."""
        if self.JWT_SECRET_KEY:
            return self.JWT_SECRET_KEY

        if self.is_production:
            raise RuntimeError(
                "JWT_SECRET_KEY (ou SECRET_KEY) é obrigatório em produção. "
                "Gere uma chave com `openssl rand -hex 32` e defina-a no ambiente. "
                "A aplicação NÃO sobe com a chave de desenvolvimento padrão."
            )

        if not self.is_development:
            warnings.warn(
                "Usando a chave JWT padrão de desenvolvimento fora de "
                f"desenvolvimento (ENVIRONMENT={self.ENVIRONMENT!r}). "
                "Defina JWT_SECRET_KEY antes de expor esta instância.",
                stacklevel=2,
            )

        return DEV_FALLBACK_SECRET


settings = Settings()
