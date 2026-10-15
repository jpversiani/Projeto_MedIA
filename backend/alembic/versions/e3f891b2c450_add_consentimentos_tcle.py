"""add_consentimentos_tcle

Revision ID: e3f891b2c450
Revises: db700d6edb6d
Create Date: 2026-10-15 12:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f891b2c450'
down_revision: Union[str, Sequence[str], None] = 'db700d6edb6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'consentimentos_tcle',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo_tcle', sa.String(length=32), nullable=False),
        sa.Column('teleconsulta_id', sa.Integer(), nullable=True),
        sa.Column('cidadao_id', sa.Integer(), nullable=True),
        sa.Column('paciente_cpf', sa.String(length=11), nullable=False),
        sa.Column('paciente_nome', sa.String(length=255), nullable=True),
        sa.Column('versao_termo', sa.String(length=32), server_default='CFM_2314_2022_V1', nullable=False),
        sa.Column('texto_integral', sa.Text(), nullable=False),
        sa.Column('hash_sha256', sa.String(length=64), nullable=False),
        sa.Column('ip_origem', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('metodo_aceite', sa.String(length=64), server_default='ELETRONICO_WEB', nullable=False),
        sa.Column('aceito_em', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cidadao_id'], ['cidadaos.id'], ),
        sa.ForeignKeyConstraint(['teleconsulta_id'], ['teleconsultas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consentimentos_tcle_id'), 'consentimentos_tcle', ['id'], unique=False)
    op.create_index(op.f('ix_consentimentos_tcle_codigo_tcle'), 'consentimentos_tcle', ['codigo_tcle'], unique=True)
    op.create_index(op.f('ix_consentimentos_tcle_paciente_cpf'), 'consentimentos_tcle', ['paciente_cpf'], unique=False)
    op.create_index(op.f('ix_consentimentos_tcle_hash_sha256'), 'consentimentos_tcle', ['hash_sha256'], unique=False)
    op.create_index(op.f('ix_consentimentos_tcle_teleconsulta_id'), 'consentimentos_tcle', ['teleconsulta_id'], unique=False)
    op.create_index(op.f('ix_consentimentos_tcle_cidadao_id'), 'consentimentos_tcle', ['cidadao_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_consentimentos_tcle_cidadao_id'), table_name='consentimentos_tcle')
    op.drop_index(op.f('ix_consentimentos_tcle_teleconsulta_id'), table_name='consentimentos_tcle')
    op.drop_index(op.f('ix_consentimentos_tcle_hash_sha256'), table_name='consentimentos_tcle')
    op.drop_index(op.f('ix_consentimentos_tcle_paciente_cpf'), table_name='consentimentos_tcle')
    op.drop_index(op.f('ix_consentimentos_tcle_id'), table_name='consentimentos_tcle')
    op.drop_table('consentimentos_tcle')
