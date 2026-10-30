"""Integração Prescrição Digital → Farmácia (C10/C34).

Problema corrigido: ``MotorPrescricaoCFM`` gravava apenas em
``documentos_clinicos``. Nenhum código criava ``Receita``/``ReceitaItem``, então
``POST /api/v1/farmacia/dispensacao/consultar`` respondia **404 para toda
receita emitida** — a farmácia nunca conseguia dar baixa, mesmo com o QR Code
impresso na mão do paciente.

Este módulo faz a ponte no momento da emissão:

1. resolve a identificação SUS que a tabela ``receitas`` exige e que o payload
   clínico não carrega (CNS do paciente, CNS do prescritor e CNES da unidade);
2. calcula o ``codigo_hash`` (SHA-256 do conteúdo canônico da receita), que é o
   conteúdo lido do QR Code;
3. cria ``Receita`` + ``ReceitaItem`` na mesma transação do documento clínico.

Quando alguma identificação não pode ser resolvida, a prescrição **continua
sendo emitida** (o documento clínico não pode falhar por cadastro incompleto),
mas o retorno informa exatamente o que falta em ``pendencias``. Antes disso o
sistema falhava em silêncio: emitia o documento e a farmácia recebia 404 sem
que ninguém soubesse por quê.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional, Sequence

from sqlalchemy.orm import Session

from app.core.crypto import hash_busca
from app.models.cidadao import Cidadao
from app.models.estabelecimento import Estabelecimento
from app.models.farmacia import (
    STATUS_EMITIDA,
    Receita,
    ReceitaItem,
)
from app.models.profissional import Profissional

# Validade da prescrição por tipo (dias).
#   ANTIBIOTICO: RDC 471/2021 — receita válida por 10 dias.
#   Demais: prática usual de 30 dias para uso ambulatorial.
VALIDADE_POR_TIPO: dict[str, int] = {
    "ANTIBIOTICO": 10,
    "CONTROLE_ESPECIAL": 30,
    "SIMPLES": 30,
}
VALIDADE_PADRAO_DIAS = 30

# CNS tem 15 dígitos; CNES tem 7. A normalização não valida dígito
# verificador: o dado pode vir de cadastro legado (o seed, por exemplo, usa um
# CNS que o validador DATASUS recusaria) e recusar a receita por isso seria
# pior do que registrá-la.
_PADRAO_NAO_DIGITO = re.compile(r"\D")


@dataclass
class ResultadoIntegracao:
    """O que a ponte conseguiu (ou não) criar para a farmácia."""

    receita: Optional[Receita] = None
    qr_code_hash: Optional[str] = None
    pendencias: list[str] = field(default_factory=list)

    @property
    def integrada(self) -> bool:
        return self.receita is not None and self.qr_code_hash is not None


def _somente_digitos(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    digitos = _PADRAO_NAO_DIGITO.sub("", valor)
    return digitos or None


def _quantidade_de_texto(valor: Optional[str]) -> int:
    """Extrai a quantidade inteira de ``quantidade_total`` (texto livre).

    O contrato de emissão aceita ``"1 cartela"``, ``"30 comprimidos"`` ou
    ``"2 frascos"``. A farmácia trabalha com inteiro; sem dígito assume 1.
    """
    if not valor:
        return 1
    encontrado = re.search(r"\d+", valor)
    if not encontrado:
        return 1
    quantidade = int(encontrado.group())
    return quantidade if quantidade > 0 else 1


def _para_utc_naive(instante: datetime) -> datetime:
    """Normaliza para UTC sem ``tzinfo`` (colunas ``DateTime`` sem timezone)."""
    if instante.tzinfo is not None:
        return instante.astimezone(timezone.utc).replace(tzinfo=None)
    return instante


def _instante_canonico(instante: datetime) -> str:
    """Instante em UTC sem offset, para o hash ser estável após o round-trip.

    ``DateTime`` sem timezone (SQLite/Postgres) descarta o ``tzinfo`` na
    gravação. Se o hash usasse ``isoformat()`` de um datetime aware na emissão e
    de um naive na releitura, o mesmo conteúdo geraria hashes diferentes.
    """
    return _para_utc_naive(instante).isoformat()


def montar_conteudo_canonico(
    *,
    codigo_validacao: str,
    cns_paciente: str,
    cpf_paciente: Optional[str],
    prescritor_cns: str,
    prescritor_registro: str,
    unidade_cnes: str,
    data_emissao: datetime,
    itens: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Conteúdo estável a partir do qual o hash do QR Code é calculado.

    Qualquer adulteração em paciente, prescritor, unidade, data ou item muda o
    hash e a farmácia recusa a baixa.
    """
    return {
        "codigo_validacao": codigo_validacao,
        "cns_paciente": cns_paciente,
        "cpf_paciente": cpf_paciente,
        "prescritor_cns": prescritor_cns,
        "prescritor_registro": prescritor_registro,
        "unidade_cnes": unidade_cnes,
        "data_emissao": _instante_canonico(data_emissao),
        "itens": [
            {
                "medicamento": item["medicamento"],
                "dosagem": item["dosagem"],
                "posologia": item["posologia"],
                "quantidade_prescrita": item["quantidade_prescrita"],
            }
            for item in itens
        ],
    }


def calcular_hash_receita(conteudo: dict[str, Any]) -> str:
    """SHA-256 (hex minúsculo) do conteúdo canônico — o que vai no QR Code."""
    serializado = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def _resolver_cns_paciente(
    db: Session, cns_informado: Optional[str], cpf: Optional[str], cidadao_id: Optional[int]
) -> Optional[str]:
    cns = _somente_digitos(cns_informado)
    if cns:
        return cns
    if cidadao_id is not None:
        cidadao = db.query(Cidadao).filter(Cidadao.id == cidadao_id).first()
        if cidadao is not None:
            return _somente_digitos(cidadao.cns)
    cpf_limpo = _somente_digitos(cpf)
    if cpf_limpo:
        # CPF é cifrado em repouso; a busca usa o índice cego (HMAC).
        cidadao = (
            db.query(Cidadao)
            .filter(Cidadao.cpf_hash == hash_busca(cpf_limpo))
            .first()
        )
        if cidadao is not None:
            return _somente_digitos(cidadao.cns)
    return None


def _resolver_cns_prescritor(
    db: Session, cns_informado: Optional[str], profissional_id: Optional[int]
) -> Optional[str]:
    cns = _somente_digitos(cns_informado)
    if cns:
        return cns
    if profissional_id is not None:
        profissional = (
            db.query(Profissional).filter(Profissional.id == profissional_id).first()
        )
        if profissional is not None:
            return _somente_digitos(profissional.cns)
    return None


def _resolver_cnes(
    db: Session, cnes_informado: Optional[str], estabelecimento_id: Optional[int]
) -> Optional[str]:
    cnes = _somente_digitos(cnes_informado)
    if cnes:
        return cnes
    if estabelecimento_id is not None:
        estabelecimento = (
            db.query(Estabelecimento)
            .filter(Estabelecimento.id == estabelecimento_id)
            .first()
        )
        if estabelecimento is not None:
            return _somente_digitos(estabelecimento.cnes)
    return None


def preparar_receita_farmacia(
    db: Session,
    *,
    codigo_validacao: str,
    tipo_prescricao: str,
    paciente_cpf: str,
    paciente_cns: Optional[str],
    medico_nome: str,
    medico_crm: str,
    medico_uf: str,
    medico_cns: Optional[str],
    unidade_cnes: Optional[str],
    data_emissao: datetime,
    itens: Sequence[dict[str, Any]],
    cidadao_id: Optional[int] = None,
    profissional_id: Optional[int] = None,
    estabelecimento_id: Optional[int] = None,
    cid10: Optional[str] = None,
    ciap2: Optional[str] = None,
    observacoes: Optional[str] = None,
) -> ResultadoIntegracao:
    """Cria (sem commit) a ``Receita`` que a farmácia vai consultar.

    Devolve ``pendencias`` legíveis quando falta identificação SUS, em vez de
    silenciosamente deixar a farmácia sem a receita.
    """
    pendencias: list[str] = []

    cns_paciente = _resolver_cns_paciente(
        db, paciente_cns, paciente_cpf, cidadao_id
    )
    if not cns_paciente:
        pendencias.append(
            "CNS do paciente ausente: informe paciente_cns ou cadastre o "
            "cidadão com CPF antes de prescrever."
        )

    prescritor_cns = _resolver_cns_prescritor(db, medico_cns, profissional_id)
    if not prescritor_cns:
        pendencias.append(
            "CNS do prescritor ausente: informe medico_cns ou vincule um "
            "profissional ao usuário autenticado."
        )

    cnes = _resolver_cnes(db, unidade_cnes, estabelecimento_id)
    if not cnes:
        pendencias.append(
            "CNES da unidade ausente: informe unidade_cnes ou use um token "
            "com estabelecimento ativo."
        )

    if pendencias:
        return ResultadoIntegracao(pendencias=pendencias)

    prescritor_registro = f"{medico_crm}-{medico_uf}"
    instante_emissao = _para_utc_naive(data_emissao)
    itens_normalizados = [
        {
            "medicamento": item["farmaco"],
            "dosagem": (
                " ".join(
                    parte
                    for parte in (item.get("concentracao"), item.get("forma_farmaceutica"))
                    if parte
                )
                or "Não informada"
            ),
            "posologia": item["posologia"],
            "quantidade_prescrita": _quantidade_de_texto(item.get("quantidade_total")),
        }
        for item in itens
    ]

    conteudo = montar_conteudo_canonico(
        codigo_validacao=codigo_validacao,
        cns_paciente=cns_paciente,
        cpf_paciente=_somente_digitos(paciente_cpf),
        prescritor_cns=prescritor_cns,
        prescritor_registro=prescritor_registro,
        unidade_cnes=cnes,
        data_emissao=instante_emissao,
        itens=itens_normalizados,
    )
    qr_code_hash = calcular_hash_receita(conteudo)

    receita = Receita(
        codigo_hash=qr_code_hash,
        cns_paciente=cns_paciente,
        cpf_paciente=_somente_digitos(paciente_cpf),
        cid10=cid10,
        ciap2=ciap2,
        prescritor_nome=medico_nome,
        prescritor_cns=prescritor_cns,
        prescritor_registro=prescritor_registro,
        unidade_cnes=cnes,
        data_emissao=instante_emissao,
        # Validade contada a partir da emissão (não de `date.today()`): o
        # fuso local pode estar à frente de UTC e encurtar a validade em um dia.
        data_validade=instante_emissao.date()
        + timedelta(days=VALIDADE_POR_TIPO.get(tipo_prescricao, VALIDADE_PADRAO_DIAS)),
        status=STATUS_EMITIDA,
        observacoes=observacoes,
        itens=[
            ReceitaItem(
                medicamento=item["medicamento"],
                dosagem=item["dosagem"],
                posologia=item["posologia"],
                quantidade_prescrita=item["quantidade_prescrita"],
                quantidade_dispensada=0,
            )
            for item in itens_normalizados
        ],
    )
    db.add(receita)
    # ``flush`` (não commit) atribui o id e deixa documento + receita na mesma
    # transação: ou os dois existem, ou nenhum.
    db.flush()

    return ResultadoIntegracao(receita=receita, qr_code_hash=qr_code_hash)
