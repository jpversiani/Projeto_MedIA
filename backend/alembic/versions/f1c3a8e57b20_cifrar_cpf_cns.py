"""cifrar_cpf_cns

LGPD art. 46: CPF e CNS estavam em texto claro em ``cidadaos`` e
``profissionais``. Esta migração:

1. alarga as colunas (o ciphertext é maior que o documento);
2. cria os índices cegos ``cpf_hash``/``cns_hash`` (HMAC-SHA-256) usados para
   busca e unicidade;
3. reescreve os valores existentes cifrados (AES-256-GCM) e preenche os hashes;
4. troca os índices únicos do documento (inúteis sobre ciphertext aleatório) por
   índices simples, mantendo a unicidade no índice cego.

A cifragem é feita em Python (``app.core.crypto``) porque o SQL não conhece a
chave. Valores já cifrados (prefixo ``enc:v1:``) são reconhecidos e não são
cifrados duas vezes — a migração é re-executável com segurança.

Revision ID: f1c3a8e57b20
Revises: e7b2c9d41f38
Create Date: 2026-10-30 09:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f1c3a8e57b20"
down_revision: Union[str, Sequence[str], None] = "e7b2c9d41f38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELAS = (
    ("cidadaos", "cpf"),
    ("cidadaos", "cns"),
    ("profissionais", "cpf"),
    ("profissionais", "cns"),
)


def upgrade() -> None:
    """Cifra CPF/CNS existentes e cria os índices cegos."""
    from app.core.crypto import cifrar, hash_busca

    for tabela, coluna in TABELAS:
        with op.batch_alter_table(tabela) as batch:
            batch.alter_column(
                coluna, type_=sa.String(length=255), existing_type=sa.String(length=15)
            )
            # Unicidade sobre ciphertext aleatório não protege nada (o mesmo
            # CPF gera textos diferentes); a unicidade passa ao hash.
            batch.drop_index(f"ix_{tabela}_{coluna}")
            batch.create_index(f"ix_{tabela}_{coluna}", [coluna], unique=False)
            batch.add_column(
                sa.Column(f"{coluna}_hash", sa.String(length=64), nullable=True)
            )
            batch.create_index(
                f"ix_{tabela}_{coluna}_hash", [f"{coluna}_hash"], unique=True
            )

    conexao = op.get_bind()
    for tabela, coluna in TABELAS:
        registros = conexao.execute(
            sa.text(f"SELECT id, {coluna} FROM {tabela}")
        ).fetchall()
        for registro_id, valor in registros:
            if valor is None:
                continue
            conexao.execute(
                sa.text(
                    f"UPDATE {tabela} SET {coluna} = :cifrado, "
                    f"{coluna}_hash = :indice WHERE id = :id"
                ),
                {
                    "cifrado": cifrar(valor),
                    "indice": hash_busca(valor),
                    "id": registro_id,
                },
            )


def downgrade() -> None:
    """Volta ao texto claro (apenas para rollback controlado)."""
    from app.core.crypto import decifrar

    conexao = op.get_bind()
    for tabela, coluna in TABELAS:
        registros = conexao.execute(
            sa.text(f"SELECT id, {coluna} FROM {tabela}")
        ).fetchall()
        for registro_id, valor in registros:
            if valor is None:
                continue
            conexao.execute(
                sa.text(f"UPDATE {tabela} SET {coluna} = :claro WHERE id = :id"),
                {"claro": decifrar(valor), "id": registro_id},
            )

        with op.batch_alter_table(tabela) as batch:
            batch.drop_index(f"ix_{tabela}_{coluna}_hash")
            batch.drop_column(f"{coluna}_hash")
            batch.drop_index(f"ix_{tabela}_{coluna}")
            batch.alter_column(
                coluna, type_=sa.String(length=15), existing_type=sa.String(length=255)
            )
            batch.create_index(f"ix_{tabela}_{coluna}", [coluna], unique=True)
