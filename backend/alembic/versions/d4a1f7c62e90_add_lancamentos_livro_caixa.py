"""add_lancamentos_livro_caixa

Livro caixa real para Carnê-Leão/DMED. A rota de demonstrativo devolvia dados
hardcoded (pacientes e valores fictícios); a partir desta tabela os lançamentos
são persistidos, escopados por estabelecimento/profissional e idempotentes por
``chave_idempotencia`` (reenvio da finalização da consulta não duplica receita).

Revision ID: d4a1f7c62e90
Revises: c8d42e1f7b33
Create Date: 2026-10-29 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4a1f7c62e90"
down_revision: Union[str, Sequence[str], None] = "c8d42e1f7b33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a tabela do livro caixa do médico."""
    op.create_table(
        "lancamentos_livro_caixa",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("estabelecimento_id", sa.Integer(), nullable=True),
        sa.Column("profissional_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=10), nullable=False),
        sa.Column("data_competencia", sa.Date(), nullable=False),
        sa.Column("descricao", sa.String(length=300), nullable=False),
        sa.Column("valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("paciente_nome", sa.String(length=200), nullable=True),
        sa.Column("paciente_cpf", sa.String(length=11), nullable=True),
        sa.Column("modalidade", sa.String(length=15), nullable=True),
        sa.Column("numero_recibo", sa.String(length=50), nullable=True),
        sa.Column("metodo_pagamento", sa.String(length=30), nullable=True),
        sa.Column("categoria", sa.String(length=40), nullable=True),
        sa.Column("dedutivel", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "origem", sa.String(length=30), nullable=False, server_default="MANUAL"
        ),
        sa.Column("chave_idempotencia", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["estabelecimento_id"], ["estabelecimentos.id"]),
        sa.ForeignKeyConstraint(["profissional_id"], ["profissionais.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chave_idempotencia", name="uq_livro_caixa_idempotencia"
        ),
    )
    op.create_index(
        op.f("ix_lancamentos_livro_caixa_id"),
        "lancamentos_livro_caixa",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lancamentos_livro_caixa_estabelecimento_id"),
        "lancamentos_livro_caixa",
        ["estabelecimento_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lancamentos_livro_caixa_profissional_id"),
        "lancamentos_livro_caixa",
        ["profissional_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lancamentos_livro_caixa_tipo"),
        "lancamentos_livro_caixa",
        ["tipo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lancamentos_livro_caixa_data_competencia"),
        "lancamentos_livro_caixa",
        ["data_competencia"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lancamentos_livro_caixa_chave_idempotencia"),
        "lancamentos_livro_caixa",
        ["chave_idempotencia"],
        unique=False,
    )


def downgrade() -> None:
    """Remove a tabela do livro caixa."""
    op.drop_index(
        op.f("ix_lancamentos_livro_caixa_chave_idempotencia"),
        table_name="lancamentos_livro_caixa",
    )
    op.drop_index(
        op.f("ix_lancamentos_livro_caixa_data_competencia"),
        table_name="lancamentos_livro_caixa",
    )
    op.drop_index(
        op.f("ix_lancamentos_livro_caixa_tipo"),
        table_name="lancamentos_livro_caixa",
    )
    op.drop_index(
        op.f("ix_lancamentos_livro_caixa_profissional_id"),
        table_name="lancamentos_livro_caixa",
    )
    op.drop_index(
        op.f("ix_lancamentos_livro_caixa_estabelecimento_id"),
        table_name="lancamentos_livro_caixa",
    )
    op.drop_index(
        op.f("ix_lancamentos_livro_caixa_id"),
        table_name="lancamentos_livro_caixa",
    )
    op.drop_table("lancamentos_livro_caixa")
