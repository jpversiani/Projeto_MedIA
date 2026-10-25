"""add_refresh_tokens

Sessões revogáveis: o access token de 24 h sem revogação vira 15 min + refresh
token de 7 dias registrado no banco (rotação a cada uso, logout revoga).

Revision ID: c8d42e1f7b33
Revises: b7c31d9e4a02
Create Date: 2026-10-13 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d42e1f7b33'
down_revision: Union[str, Sequence[str], None] = 'b7c31d9e4a02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a tabela de refresh tokens."""
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('estabelecimento_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=300), nullable=True),
        sa.Column('substituido_por', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['estabelecimento_id'], ['estabelecimentos.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_jti'), 'refresh_tokens', ['jti'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_usuario_id'), 'refresh_tokens', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_estabelecimento_id'), 'refresh_tokens', ['estabelecimento_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_created_at'), 'refresh_tokens', ['created_at'], unique=False)


def downgrade() -> None:
    """Remove a tabela de refresh tokens."""
    op.drop_index(op.f('ix_refresh_tokens_created_at'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_estabelecimento_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_usuario_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_jti'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
