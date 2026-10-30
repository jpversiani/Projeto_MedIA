"""add_jornadas_atendimento

Persiste a jornada do fluxo de atendimento (antes só em memória). Sem isso,
reiniciar o servidor apagava a consulta em andamento, cada worker via uma
lista diferente e a finalização não tinha tenant nem vínculo com a agenda.

Revision ID: e7b2c9d41f38
Revises: d4a1f7c62e90
Create Date: 2026-10-29 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7b2c9d41f38"
down_revision: Union[str, Sequence[str], None] = "d4a1f7c62e90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a tabela de jornadas do fluxo de atendimento."""
    op.create_table(
        "jornadas_atendimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consulta_id", sa.String(length=40), nullable=False),
        sa.Column("cidadao_id", sa.Integer(), nullable=True),
        sa.Column("profissional_id", sa.Integer(), nullable=True),
        sa.Column("estabelecimento_id", sa.Integer(), nullable=True),
        sa.Column("agendamento_id", sa.Integer(), nullable=True),
        sa.Column("paciente_nome", sa.String(length=200), nullable=False),
        sa.Column("paciente_cpf", sa.String(length=11), nullable=True),
        sa.Column("medico_nome", sa.String(length=200), nullable=False),
        sa.Column("medico_crm", sa.String(length=20), nullable=True),
        sa.Column("modalidade", sa.String(length=20), nullable=False),
        sa.Column("etapa", sa.String(length=20), nullable=False, server_default="AGENDADA"),
        sa.Column("valor_honorarios", sa.Float(), nullable=True),
        sa.Column("dados_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agendamento_id"], ["agendamentos.id"]),
        sa.ForeignKeyConstraint(["cidadao_id"], ["cidadaos.id"]),
        sa.ForeignKeyConstraint(["estabelecimento_id"], ["estabelecimentos.id"]),
        sa.ForeignKeyConstraint(["profissional_id"], ["profissionais.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_jornadas_atendimento_id"), "jornadas_atendimento", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_jornadas_atendimento_consulta_id"),
        "jornadas_atendimento",
        ["consulta_id"],
        unique=True,
    )
    for coluna in (
        "cidadao_id",
        "profissional_id",
        "estabelecimento_id",
        "agendamento_id",
        "etapa",
        "paciente_nome",
    ):
        op.create_index(
            op.f(f"ix_jornadas_atendimento_{coluna}"),
            "jornadas_atendimento",
            [coluna],
            unique=False,
        )


def downgrade() -> None:
    """Remove a tabela de jornadas."""
    for coluna in (
        "paciente_nome",
        "etapa",
        "agendamento_id",
        "estabelecimento_id",
        "profissional_id",
        "cidadao_id",
        "consulta_id",
        "id",
    ):
        op.drop_index(
            op.f(f"ix_jornadas_atendimento_{coluna}"),
            table_name="jornadas_atendimento",
        )
    op.drop_table("jornadas_atendimento")
