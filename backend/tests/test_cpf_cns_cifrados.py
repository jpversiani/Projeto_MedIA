"""P0-7 — CPF e CNS cifrados em repouso (AES-256-GCM) com índice cego.

Antes, ``cidadaos.cpf``/``cidadaos.cns`` e ``profissionais.cpf``/``cns`` eram
``VARCHAR`` em texto claro: um dump do banco expunha a identificação de todos os
pacientes (LGPD art. 46).

O que estes testes garantem:

1. o **banco** guarda ciphertext (prefixo ``enc:v1:``), nunca o documento;
2. o **ORM** devolve texto claro (contrato da API intacto);
3. busca/unicidade continuam funcionando, via índice cego (HMAC);
4. valores legados em texto claro seguem legíveis durante a transição;
5. chave diferente falha alto (não devolve dado errado em silêncio).
"""

from __future__ import annotations

import hashlib

import pytest
from sqlalchemy import text

from app.core import crypto
from app.core.crypto import (
    PREFIXO,
    ErroCriptografia,
    cifrar,
    decifrar,
    hash_busca,
    somente_digitos,
)
from app.models.cidadao import Cidadao
from app.models.profissional import Profissional


def _cpf_valido(nove_digitos: str) -> str:
    """CPF com dígitos verificadores válidos (módulo 11)."""
    def dv(sequencia: str, peso_inicial: int) -> int:
        soma = sum(int(d) * p for d, p in zip(sequencia, range(peso_inicial, 1, -1)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    primeiro = dv(nove_digitos, 10)
    return f"{nove_digitos}{primeiro}{dv(nove_digitos + str(primeiro), 11)}"


CPF_A = _cpf_valido("390533447")
CPF_B = _cpf_valido("111444777")
CPF_C = _cpf_valido("987654321")
CNS_A = "898000123456780"


# ---------------------------------------------------------------------------
# Primitivas
# ---------------------------------------------------------------------------


def test_cifra_nao_guarda_o_documento_e_volta_ao_original():
    cifrado = cifrar(CPF_A)

    assert cifrado.startswith(PREFIXO)
    assert CPF_A not in cifrado
    assert decifrar(cifrado) == CPF_A


def test_cifra_e_nao_deterministica():
    """Nonce aleatório: o mesmo CPF gera textos diferentes (sem vazamento por igualdade)."""
    primeiro = cifrar(CPF_A)
    segundo = cifrar(CPF_A)

    assert primeiro != segundo
    assert decifrar(primeiro) == decifrar(segundo) == CPF_A


def test_cifrar_de_novo_nao_duplica_a_camada():
    uma_vez = cifrar(CPF_A)
    duas_vezes = cifrar(uma_vez)

    assert duas_vezes == uma_vez
    assert decifrar(duas_vezes) == CPF_A


def test_indice_cego_e_estavel_e_normaliza_formatacao():
    assert hash_busca("123.456.789-00") == hash_busca("12345678900")
    assert hash_busca(CPF_A) != hash_busca(CPF_B)
    assert len(hash_busca(CPF_A)) == 64
    assert CPF_A not in hash_busca(CPF_A)


def test_indice_cego_nao_e_sha256_do_documento():
    """HMAC com chave — não pode ser quebrado por dicionário de CPFs."""
    assert hash_busca(CPF_A) != hashlib.sha256(CPF_A.encode()).hexdigest()


def test_valores_nulos_e_vazios_atravessam():
    assert cifrar(None) is None
    assert decifrar(None) is None
    assert cifrar("") == ""
    assert hash_busca(None) is None
    assert hash_busca("") is None


def test_texto_claro_legado_continua_legivel():
    """Durante a transição, linhas não migradas não podem quebrar a leitura."""
    assert decifrar("12345678900") == "12345678900"


def test_somente_digitos():
    assert somente_digitos("123.456.789-00") == "12345678900"
    assert somente_digitos("abc") is None


def test_chave_diferente_falha_alto(monkeypatch):
    cifrado = cifrar(CPF_A)

    chave_errada = b"\x01" * 32
    monkeypatch.setattr(crypto, "_chaves", lambda: (chave_errada, chave_errada))

    with pytest.raises(ErroCriptografia):
        decifrar(cifrado)


# ---------------------------------------------------------------------------
# Persistência (banco real da suíte)
# ---------------------------------------------------------------------------


def _criar_cidadao(client, cpf: str, cns: str | None = None, nome="Paciente Cifrado"):
    resposta = client.post(
        "/api/v1/cidadaos/",
        json={
            "nome_completo": nome,
            "data_nascimento": "1991-05-12",
            "sexo": "F",
            "cpf": cpf,
            **({"cns": cns} if cns else {}),
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _valor_bruto(db_session, coluna: str, hash_alvo: str) -> str:
    """Lê a coluna direto do banco, sem passar pelo TypeDecorator."""
    return db_session.execute(
        text(f"SELECT {coluna} FROM cidadaos WHERE cpf_hash = :h"), {"h": hash_alvo}
    ).scalar_one()


def test_banco_guarda_cpf_e_cns_cifrados_e_api_devolve_texto_claro(client, db_session):
    criado = _criar_cidadao(client, CPF_A, CNS_A)
    assert criado["cpf"] == CPF_A
    assert criado["cns"] == CNS_A

    bruto_cpf = _valor_bruto(db_session, "cpf", hash_busca(CPF_A))
    bruto_cns = _valor_bruto(db_session, "cns", hash_busca(CPF_A))

    assert bruto_cpf.startswith(PREFIXO) and CPF_A not in bruto_cpf
    assert bruto_cns.startswith(PREFIXO) and CNS_A not in bruto_cns

    cidadao = db_session.query(Cidadao).filter(Cidadao.cpf == CPF_A).one()
    assert cidadao.cpf == CPF_A
    assert cidadao.cns == CNS_A
    assert cidadao.cpf_hash == hash_busca(CPF_A)
    assert cidadao.cns_hash == hash_busca(CNS_A)


def test_comparacao_por_atributo_usa_o_indice_cego(client, db_session):
    _criar_cidadao(client, CPF_B)

    # Formatação diferente do armazenado.
    encontrado = db_session.query(Cidadao).filter(Cidadao.cpf == "111.444.777-35").first()
    assert encontrado is not None
    assert encontrado.cpf == CPF_B

    # `IN` também é traduzido para o índice cego.
    lista = (
        db_session.query(Cidadao)
        .filter(Cidadao.cpf.in_([CPF_B, "00000000000"]))
        .all()
    )
    assert [c.cpf for c in lista] == [CPF_B]


def test_cpf_duplicado_e_recusado_pelo_indice_cego(client):
    _criar_cidadao(client, CPF_C, nome="Primeiro")

    repetido = client.post(
        "/api/v1/cidadaos/",
        json={
            "nome_completo": "Segundo",
            "data_nascimento": "1990-01-01",
            "sexo": "M",
            "cpf": CPF_C,
        },
    )
    assert repetido.status_code == 400
    assert "CPF" in repetido.json()["detail"]


def test_busca_por_cpf_e_cns_encontra_mesmo_cifrado(client):
    # CNS distinto do usado nos outros testes (o banco é compartilhado).
    cns_busca = "110433218196000"
    cpf_busca = _cpf_valido("123321123")
    criado = _criar_cidadao(client, cpf_busca, cns_busca, "Paciente Busca")

    cpf_formatado = f"{cpf_busca[:3]}.{cpf_busca[3:6]}.{cpf_busca[6:9]}-{cpf_busca[9:]}"
    por_cpf = client.get("/api/v1/cidadaos/", params={"busca": cpf_formatado})
    assert por_cpf.status_code == 200
    assert criado["id"] in [c["id"] for c in por_cpf.json()]

    por_cns = client.get("/api/v1/cidadaos/", params={"busca": cns_busca})
    assert criado["id"] in [c["id"] for c in por_cns.json()]

    # Busca por nome continua funcionando (não usa o campo cifrado).
    por_nome = client.get("/api/v1/cidadaos/", params={"busca": "Paciente Busca"})
    assert criado["id"] in [c["id"] for c in por_nome.json()]


def test_profissionais_tambem_ficam_cifrados(db_session):
    profissional = db_session.query(Profissional).first()
    assert profissional is not None

    bruto = db_session.execute(
        text("SELECT cpf, cns FROM profissionais WHERE id = :id"),
        {"id": profissional.id},
    ).one()
    assert bruto.cpf.startswith(PREFIXO)
    assert bruto.cns.startswith(PREFIXO)

    # A busca por CNS (usada pelo repositório de consultas APS) continua achando.
    recuperado = (
        db_session.query(Profissional)
        .filter(Profissional.cns == profissional.cns)
        .first()
    )
    assert recuperado is not None
    assert recuperado.id == profissional.id
