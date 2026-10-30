"""add_consentimentos_teleconsulta

P0-TM: a Resolução CFM nº 2.314/2022 (Art. 4º, § 2º) exige consentimento
livre e esclarecido do paciente **antes** da teleconsulta. O registro do
aceite existia apenas como dataclass em memória (`RegistroTCLE`) e morria na
resposta HTTP — não havia prova persistida, e `/iniciar-chamada` iniciava a
chamada mesmo sem consentimento.

Esta migração cria a tabela `consentimentos_teleconsulta`, que grava o texto
integral do termo, o hash SHA-256 de integridade, o método de aceite e o IP de
origem, permitindo (a) auditoria do consentimento e (b) o bloqueio real do
início da chamada sem termo vigente.

O CPF do paciente é cifrado com o mesmo `CampoProtegido` usado no resto do
módulo de telemedicina (P0-7). Os índices (inclusive o único de `codigo`)
são criados pelas próprias colunas (`unique=True`/`index=True`), com o nome
padrão do SQLAlchemy — criar `op.create_index` manual duplicaria o índice.

Revision ID: c3d9e1f5a7b2
Revises: b6e8f24a91d7
Create Date: 2026-10-30 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d9e1f5a7b2"
down_revision: Union[str, Sequence[str], None] = "b6e8f24a91d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "consentimentos_teleconsulta",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        # `unique=True` + `index=True` criam o índice único padrão
        # `ix_consentimentos_teleconsulta_codigo` junto com a tabela.
        sa.Column(
            "codigo",
            sa.String(length=40),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column(
            "teleconsulta_id",
            sa.Integer(),
            sa.ForeignKey("teleconsultas.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("paciente_nome", sa.String(length=200), nullable=False),
        # CPF cifrado (CampoProtegido no modelo; o repouso é VARCHAR com o
        # prefixo `enc:v1:` — ver `app/core/crypto.py`).
        sa.Column(
            "paciente_cpf",
            sa.String(length=255),
            nullable=True,
            index=True,
        ),
        sa.Column("texto_integral", sa.Text(), nullable=False),
        sa.Column("hash_integridade_sha256", sa.String(length=64), nullable=False),
        sa.Column("metodo_aceite", sa.String(length=40), nullable=False),
        sa.Column("ip_origem", sa.String(length=45), nullable=True),
        sa.Column("data_aceite", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    # `drop_table` remove também os índices criados junto com a tabela.
    op.drop_table("consentimentos_teleconsulta")
