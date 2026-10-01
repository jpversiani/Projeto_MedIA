"""Bootstrap idempotente dos dados iniciais da aplicação.

Sem isto, uma instalação nova sobe com o schema criado mas completamente vazio:
nenhuma unidade de saúde, nenhum profissional e nenhum usuário. O login de
demonstração então devolvia `clinica_ativa = null` e o Workspace Switcher do
Cockpit ficava inutilizável — a aplicação não servia para nenhum teste real.

Todas as rotinas de seed consultam antes de inserir, então este bootstrap é
idempotente e seguro para rodar a cada boot.
"""

from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.estabelecimento import Estabelecimento

logger = logging.getLogger("media.bootstrap")


def is_empty(db: Session) -> bool:
    """True quando ainda não existe nenhuma unidade de saúde cadastrada."""
    return db.query(Estabelecimento.id).first() is None


def run_migrations() -> None:
    """Aplica as migrações do Alembic até `head`.

    Substitui o antigo `Base.metadata.create_all()` no startup. `create_all`
    só executa `CREATE TABLE IF NOT EXISTS`: nunca altera colunas, nunca
    migra dados e não versiona o schema — uma coluna nova em um modelo era
    silenciosamente ignorada em bancos existentes enquanto `/health` seguia
    respondendo 200. Com o Alembic, o schema é reproduzível e versionado.
    """
    import alembic.command
    from alembic.config import Config

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    repo_dir = os.path.dirname(backend_dir)

    ini_path = os.path.join(repo_dir, "alembic.ini")
    if not os.path.isfile(ini_path):
        # Layout empacotado (imagem Docker): o ini fica ao lado do backend/.
        ini_path = os.path.join(backend_dir, "alembic.ini")
    if not os.path.isfile(ini_path):
        logger.warning("alembic.ini não encontrado — schema não migrado.")
        return

    cfg = Config(ini_path)
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    alembic.command.upgrade(cfg, "head")
    logger.info("Migrações Alembic aplicadas até head.")


def bootstrap_demo_data() -> bool:
    """Popula os dados de demonstração no primeiro boot.

    Retorna ``True`` se o seed foi executado. Em produção o processo é ignorado:
    dados fictícios em base de prontuário real seriam um problema de LGPD.
    """
    if not settings.AUTO_SEED_DEMO_DATA:
        return False

    if settings.is_production:
        logger.warning(
            "AUTO_SEED_DEMO_DATA está ligado em produção; seed ignorado por segurança."
        )
        return False

    from app.seeds.init_data import seed_database
    from app.seeds.seed_multiclinica_auth import seed_multiclinica

    db = SessionLocal()
    try:
        if not is_empty(db):
            logger.info("Bootstrap ignorado: banco já possui unidades de saúde.")
            return False
        logger.info("Banco vazio — populando dados iniciais de demonstração...")
        seed_database(db)
    finally:
        db.close()

    seed_multiclinica()
    logger.info("Dados iniciais de demonstração populados com sucesso.")
    return True
