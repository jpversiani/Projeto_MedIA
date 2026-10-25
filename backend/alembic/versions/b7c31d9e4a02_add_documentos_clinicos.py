"""add_documentos_clinicos

Persiste receitas e atestados emitidos, que antes viviam apenas em memória
(``_REPOSITORIO_DOCUMENTOS_CFM``) e desapareciam a cada restart — fazendo o
QR Code de validação responder 404.

Revision ID: b7c31d9e4a02
Revises: 09250669ac4f
Create Date: 2026-10-13 09:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c31d9e4a02'
down_revision: Union[str, Sequence[str], None] = '09250669ac4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a tabela de documentos clínicos emitidos."""
    op.create_table(
        'documentos_clinicos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo_validacao', sa.String(length=32), nullable=False),
        sa.Column('tipo_documento', sa.String(length=30), nullable=False),
        sa.Column('cidadao_id', sa.Integer(), nullable=True),
        sa.Column('profissional_id', sa.Integer(), nullable=True),
        sa.Column('estabelecimento_id', sa.Integer(), nullable=True),
        sa.Column('paciente_nome', sa.String(length=200), nullable=False),
        sa.Column('paciente_cpf', sa.String(length=11), nullable=False),
        sa.Column('medico_nome', sa.String(length=200), nullable=False),
        sa.Column('medico_crm', sa.String(length=20), nullable=False),
        sa.Column('medico_uf', sa.String(length=2), nullable=False),
        sa.Column('medico_rqe', sa.String(length=30), nullable=True),
        sa.Column('data_emissao', sa.DateTime(), nullable=False),
        sa.Column('hash_integridade_sha256', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('dados_consulta_publica', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cidadao_id'], ['cidadaos.id'], ),
        sa.ForeignKeyConstraint(['estabelecimento_id'], ['estabelecimentos.id'], ),
        sa.ForeignKeyConstraint(['profissional_id'], ['profissionais.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documentos_clinicos_id'), 'documentos_clinicos', ['id'], unique=False)
    op.create_index(op.f('ix_documentos_clinicos_codigo_validacao'), 'documentos_clinicos', ['codigo_validacao'], unique=True)
    op.create_index(op.f('ix_documentos_clinicos_tipo_documento'), 'documentos_clinicos', ['tipo_documento'], unique=False)
    op.create_index(op.f('ix_documentos_clinicos_cidadao_id'), 'documentos_clinicos', ['cidadao_id'], unique=False)
    op.create_index(op.f('ix_documentos_clinicos_estabelecimento_id'), 'documentos_clinicos', ['estabelecimento_id'], unique=False)
    op.create_index(op.f('ix_documentos_clinicos_paciente_cpf'), 'documentos_clinicos', ['paciente_cpf'], unique=False)
    op.create_index(op.f('ix_documentos_clinicos_data_emissao'), 'documentos_clinicos', ['data_emissao'], unique=False)
    op.create_index(op.f('ix_documentos_clinicos_status'), 'documentos_clinicos', ['status'], unique=False)


def downgrade() -> None:
    """Remove a tabela de documentos clínicos emitidos."""
    op.drop_index(op.f('ix_documentos_clinicos_status'), table_name='documentos_clinicos')
    op.drop_index(op.f('ix_documentos_clinicos_data_emissao'), table_name='documentos_clinicos')
    op.drop_index(op.f('ix_documentos_clinicos_paciente_cpf'), table_name='documentos_clinicos')
    op.drop_index(op.f('ix_documentos_clinicos_estabelecimento_id'), table_name='documentos_clinicos')
    op.drop_index(op.f('ix_documentos_clinicos_cidadao_id'), table_name='documentos_clinicos')
    op.drop_index(op.f('ix_documentos_clinicos_tipo_documento'), table_name='documentos_clinicos')
    op.drop_index(op.f('ix_documentos_clinicos_codigo_validacao'), table_name='documentos_clinicos')
    op.drop_index(op.f('ix_documentos_clinicos_id'), table_name='documentos_clinicos')
    op.drop_table('documentos_clinicos')
