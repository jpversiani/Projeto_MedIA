"""add_convites_teleconsulta

Fase 2 (telemedicina plena): o paciente não tem conta no sistema, então o link
que ele recebe precisa ser a própria credencial. Antes o link era
``?sala=<codigo>`` puro — permanente, sem token e sem TTL — e com a autenticação
ligada o paciente não conseguia entrar (a página exigia um token de login).

Esta migração cria `convites_teleconsulta`, que persiste o ``jti`` de cada
convite assinado (JWT curto, papel PACIENTE, amarrado a uma sala) para permitir
revogação ao finalizar/cancelar a consulta e checagem de validade/expiração no
WebSocket. Sem a tabela, não há como revogar um convite vazado nem provar que
ele pertence àquela sala.

Revision ID: d5e8f2a91c47
Revises: c3d9e1f5a7b2
Create Date: 2026-11-13 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5e8f2a91c47"
down_revision: Union[str, Sequence[str], None] = "c3d9e1f5a7b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "convites_teleconsulta",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        # `unique=True` + `index=True` criam o índice único padrão junto com a
        # tabela (não criar op.create_index manual para não duplicar).
        sa.Column("jti", sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column(
            "teleconsulta_id",
            sa.Integer(),
            sa.ForeignKey("teleconsultas.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("codigo_sala", sa.String(length=64), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("convites_teleconsulta")