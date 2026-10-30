"""cifrar_copias_cpf_cns

P0-7b: o cadastro mestre passou a cifrar CPF/CNS em ``f1c3a8e57b20``, mas as
**cópias** desses documentos espalhadas em tabelas operacionais continuaram em
texto claro — um dump de ``receitas``, ``guias_tiss``, ``dispensacoes`` ou
``atendimentos_offline`` ainda expunha a identificação do paciente (LGPD
art. 46 + art. 5º II).

Esta migração:

1. **alarga as colunas de texto** (ciphertext é maior que o documento) — só
   onde ``ALTER COLUMN TYPE`` é nativo (Postgres). No SQLite ``VARCHAR(n)``
   não é imposto e a única rota seria ``batch_alter_table``, que **recria a
   tabela por reflection e perde constraints UNIQUE/FK** (sondado neste
   repositório) — então lá a estrutura permanece e só os dados mudam;
2. cifra ``guias_tiss.xml_tiss`` por inteiro (XML com CPF, CNS e CID);
3. cifra os campos ``paciente_cpf``/``paciente_cns`` embutidos em
   ``documentos_clinicos.payload_json`` e ``jornadas_atendimento.dados_json``,
   preservando legíveis o restante do payload (itens, checklist e o hash de
   integridade, que precisa ser recalculável);
4. reescreve as 20 colunas de texto existentes.

A cifragem é idempotente (valores ``enc:v1:`` não são cifrados de novo), então
a migração pode ser reexecutada. **Nenhuma coluna de índice cego (``_hash``)
é criada**: nenhuma consulta do sistema filtra por essas cópias, e o
``ComparadorProtegido`` falha alto se alguém tentar comparar texto claro com
ciphertext — em vez de devolver resultado vazio.

No downgrade os dados voltam a texto claro, mas o alargamento da coluna é
mantido: é compatível com o texto claro e estreitar de volta arriscaria perda
de dado caso algum valor não decifre.

Revision ID: b6e8f24a91d7
Revises: f1c3a8e57b20
Create Date: 2026-10-30 12:00:00.000000

"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional, Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6e8f24a91d7"
down_revision: Union[str, Sequence[str], None] = "f1c3a8e57b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TAMANHO_ALVO = 255

# (tabela, coluna, largura original declarada no modelo)
COLUNAS_TEXTO: Sequence[tuple[str, str, int]] = (
    ("documentos_clinicos", "paciente_cpf", 11),
    ("receitas", "cns_paciente", 15),
    ("receitas", "cpf_paciente", 11),
    ("receitas", "prescritor_cns", 15),
    ("dispensacoes", "farmaceutico_cns", 15),
    ("dispensacoes", "farmaceutico_cpf", 11),
    ("guias_tiss", "paciente_cns", 15),
    ("guias_tiss", "paciente_cpf", 14),
    ("lancamentos_financeiros", "paciente_cpf", 14),
    ("lancamentos_financeiros", "cpf_cnpj_pagador", 14),
    ("lancamentos_livro_caixa", "paciente_cpf", 11),
    ("jornadas_atendimento", "paciente_cpf", 11),
    ("atendimentos_offline", "cns_cidadao", 15),
    ("atendimentos_offline", "cpf_cidadao", 11),
    ("atendimentos_offline", "profissional_cns", 15),
    ("mensagens_preventivas", "cns", 15),
    ("mensagens_preventivas", "cpf", 11),
    ("alertas_busca_ativa", "cns", 15),
    ("alertas_busca_ativa", "cpf", 11),
    ("teleconsultas", "paciente_cpf", 11),
)

# Colunas de texto longo já tipadas TEXT nos dois dialetos — cifradas por
# inteiro, sem alteração de DDL.
COLUNAS_LONGAS: Sequence[tuple[str, str]] = (
    ("guias_tiss", "xml_tiss"),
)

# Campos pessoais embutidos em JSON (o resto do payload permanece legível).
COLUNAS_JSON: Sequence[tuple[str, str, Sequence[str]]] = (
    ("documentos_clinicos", "payload_json", ("paciente_cpf", "paciente_cns")),
    ("jornadas_atendimento", "dados_json", ("paciente_cpf", "paciente_cns")),
)


def _reescrever_coluna(
    conexao, tabela: str, coluna: str, operacao: Callable[[str], str]
) -> None:
    """Aplica ``operacao`` (cifrar/decifrar) a cada valor da coluna."""
    registros = conexao.execute(
        sa.text(f"SELECT id, {coluna} FROM {tabela}")
    ).fetchall()
    for registro_id, valor in registros:
        if valor is None:
            continue
        novo = operacao(valor)
        if novo == valor:
            continue  # já cifrado (ida) ou já texto claro (volta)
        conexao.execute(
            sa.text(f"UPDATE {tabela} SET {coluna} = :valor WHERE id = :id"),
            {"valor": novo, "id": registro_id},
        )


def _percorrer_texto(operacao: Callable[[str], str]) -> None:
    conexao = op.get_bind()
    for tabela, coluna, _tamanho in COLUNAS_TEXTO:
        _reescrever_coluna(conexao, tabela, coluna, operacao)
    for tabela, coluna in COLUNAS_LONGAS:
        _reescrever_coluna(conexao, tabela, coluna, operacao)


def _tabela_json(nome: str, coluna: str) -> sa.TableClause:
    """Tabela Core com ``id`` + a coluna JSON real, tipada (por dialeto)."""
    return sa.table(
        nome,
        sa.column("id", sa.Integer()),
        sa.column(coluna, sa.JSON()),
    )


def _como_dict(valor: Any) -> Optional[dict]:
    """Normaliza o valor lido de uma coluna JSON (str no SQLite, dict no PG)."""
    if isinstance(valor, dict):
        return valor
    if isinstance(valor, str):
        try:
            carregado = json.loads(valor)
        except ValueError:
            return None
        return carregado if isinstance(carregado, dict) else None
    return None


def _percorrer_json(operacao: Callable[[str], str], *, somente_legado: bool) -> None:
    """Cifra/descifra os campos pessoais de cada payload JSON.

    ``somente_legado`` limita a operação a valores **ainda** em texto claro na
    ida e a ciphertext na volta — assim um reexecutar não refaz trabalho já
    feito e o downgrade não tenta decifrar texto que é legado.
    """
    from app.core.crypto import PREFIXO

    conexao = op.get_bind()
    for tabela, coluna, campos in COLUNAS_JSON:
        tabela_core = _tabela_json(tabela, coluna)
        linhas = conexao.execute(
            sa.select(tabela_core.c.id, tabela_core.c[coluna])
        ).fetchall()
        for registro_id, bruto in linhas:
            payload = _como_dict(bruto)
            if payload is None:
                continue
            novo = dict(payload)
            alterado = False
            for campo in campos:
                valor = novo.get(campo)
                if not isinstance(valor, str) or not valor:
                    continue
                ja_cifrado = valor.startswith(PREFIXO)
                if somente_legado and ja_cifrado:
                    continue
                if not somente_legado and not ja_cifrado:
                    continue
                novo[campo] = operacao(valor)
                alterado = True
            if alterado:
                conexao.execute(
                    tabela_core.update()
                    .where(tabela_core.c.id == registro_id)
                    .values({coluna: novo})
                )


def upgrade() -> None:
    """Cifra as cópias de CPF/CNS espalhadas em tabelas operacionais."""
    from app.core.crypto import cifrar

    if op.get_bind().dialect.name != "sqlite":
        # Postgres: ALTER COLUMN TYPE nativo preserva UNIQUE/FK/índices (e o
        # Enum vira tipo nativo, sem risco de rebuild). O SQLite não suporta
        # ALTER de tipo e o batch_alter_table por reflection perde constraints,
        # então lá só os dados mudam (VARCHAR(n) não é imposto de qualquer forma).
        for tabela, coluna, tamanho in COLUNAS_TEXTO:
            op.alter_column(
                tabela,
                coluna,
                type_=sa.String(length=TAMANHO_ALVO),
                existing_type=sa.String(length=tamanho),
            )

    _percorrer_texto(cifrar)
    _percorrer_json(cifrar, somente_legado=True)


def downgrade() -> None:
    """Volta as cópias a texto claro (rollback controlado).

    O alargamento das colunas é mantido de propósito: é compatível com texto
    claro e estreitar arriscaria perda de dado se algum valor não decifrar.
    """
    from app.core.crypto import decifrar

    _percorrer_json(decifrar, somente_legado=False)
    _percorrer_texto(decifrar)
