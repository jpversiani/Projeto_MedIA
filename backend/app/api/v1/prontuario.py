"""Endpoints REST do Prontuário do Cidadão (PEC e-SUS APS).

Agrega, por CNS do cidadão, o resumo clínico da APS (Lista de Problemas
ativos, alergias e medicamentos em uso), as evoluções clínicas no método
SOAP com paginação por offset e o registro de alergias e de problemas
codificados por CIAP-2 ou CID-10.

Códigos HTTP: 200 (leitura), 201 (criação), 404 (cidadão não encontrado),
422 (payload inválido, CNS malformado ou duplicidade clínica).

Projeto MedIA — SUS/APS (Python 3.12, Pydantic v2, SQLAlchemy 2.0).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Final

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.atendimento import AtendimentoProblema, AtendimentoSOAP
from app.models.cidadao import Cidadao
from app.models.prontuario import ProntuarioProblema
from app.schemas.atendimento import AtendimentoSOAPOut
from app.schemas.prontuario import (
    AlergiaCriadaOut,
    AlergiaCreate,
    MedicamentoEmUsoOut,
    OrigemProblema,
    PaginaEvolucoesOut,
    ProblemaAtivoOut,
    ProblemaProntuarioCreate,
    ProblemaProntuarioOut,
    ProntuarioResumoOut,
)

router = APIRouter(prefix="/prontuario", tags=["Prontuário do Cidadão (PEC)"])

# CNS aceito no caminho: exatamente 15 dígitos numéricos (formato SUS)
CNSPath = Annotated[
    str,
    Path(
        min_length=15,
        max_length=15,
        pattern=r"^\d{15}$",
        description="Cartão Nacional de Saúde (CNS) do cidadão com 15 dígitos",
    ),
]

# Separadores tolerados na leitura do campo textual de alergias do cadastro
_REGEX_SEPARADOR_ALERGIA: Final[re.Pattern[str]] = re.compile(r"[;\n,]")
# Formato das prescrições registradas no plano SOAP: "Medicamento - detalhe" por linha


def _obter_cidadao_por_cns(db: Session, cns: str) -> Cidadao:
    """Localiza o cidadão pelo CNS ou levanta 404 quando inexistente."""
    cidadao = db.query(Cidadao).filter(Cidadao.cns == cns).first()
    if cidadao is None:
        raise HTTPException(
            status_code=404,
            detail="Cidadão não encontrado para o CNS informado.",
        )
    return cidadao


def _listar_alergias(texto_alergias: str | None) -> list[str]:
    """Converte o campo textual de alergias do cadastro em lista normalizada."""
    if not texto_alergias:
        return []
    return [
        item.strip()
        for item in _REGEX_SEPARADOR_ALERGIA.split(texto_alergias)
        if item.strip()
    ]


def _extrair_medicamentos_em_uso(
    atendimentos: Sequence[AtendimentoSOAP],
) -> list[MedicamentoEmUsoOut]:
    """Deriva a lista de medicamentos em uso das prescrições do plano SOAP.

    Percorre os atendimentos do mais recente para o mais antigo e mantém a
    primeira ocorrência de cada medicamento (comparação sem acentuar caixa),
    evitando repetições de tratamento contínuo entre evoluções.
    """
    medicamentos: list[MedicamentoEmUsoOut] = []
    ja_registrados: set[str] = set()

    for atendimento in atendimentos:
        for linha in (atendimento.plano_prescricoes or "").splitlines():
            linha = linha.strip()
            if not linha:
                continue

            nome, separador, detalhe = linha.partition(" - ")
            chave = nome.strip().casefold()
            if not chave or chave in ja_registrados:
                continue

            ja_registrados.add(chave)
            medicamentos.append(
                MedicamentoEmUsoOut(
                    nome=nome.strip(),
                    detalhe=detalhe.strip() if separador and detalhe.strip() else None,
                )
            )
    return medicamentos


def _registrar_problema_ativo(
    problemas: list[ProblemaAtivoOut],
    vistos: set[tuple[str, str]],
    *,
    tipo_codigo: str,
    codigo: str,
    descricao: str,
    situacao: str,
    data_registro: datetime | None,
    origem: OrigemProblema,
) -> None:
    """Adiciona um problema ativo ao resumo, ignorando duplicidades por código."""
    chave = (tipo_codigo.casefold(), codigo.casefold())
    if chave in vistos:
        return
    vistos.add(chave)
    problemas.append(
        ProblemaAtivoOut(
            tipo_codigo=tipo_codigo,
            codigo=codigo,
            descricao=descricao,
            situacao=situacao,
            data_registro=data_registro,
            origem=origem,
        )
    )


@router.get(
    "/{cns}",
    response_model=ProntuarioResumoOut,
    summary="Resumo do prontuário do cidadão",
)
def obter_resumo_prontuario(cns: CNSPath, db: Session = Depends(get_db)) -> ProntuarioResumoOut:
    """Retorna o resumo do prontuário: problemas ativos, alergias e medicamentos em uso.

    - **Problemas ativos**: Lista de Problemas do prontuário + episódios
      diagnósticos dos atendimentos SOAP (CIAP-2/CID-10), excluídos os RESOLVIDOS.
    - **Alergias**: condições autorreferidas registradas no cadastro do cidadão.
    - **Medicamentos em uso**: prescrições (plano SOAP) dos atendimentos, sem
      duplicidades, priorizando as mais recentes.
    """
    cidadao = _obter_cidadao_por_cns(db, cns)

    atendimentos = (
        db.query(AtendimentoSOAP)
        .filter(AtendimentoSOAP.cidadao_id == cidadao.id)
        .order_by(AtendimentoSOAP.data_hora_inicio.desc())
        .all()
    )

    problemas_ativos: list[ProblemaAtivoOut] = []
    codigos_vistos: set[tuple[str, str]] = set()

    # Lista de Problemas continuada do prontuário (fonte prioritária)
    problemas_prontuario = (
        db.query(ProntuarioProblema)
        .filter(
            ProntuarioProblema.cidadao_id == cidadao.id,
            ProntuarioProblema.situacao != "RESOLVIDO",
        )
        .order_by(ProntuarioProblema.data_registro.desc())
        .all()
    )
    for problema in problemas_prontuario:
        _registrar_problema_ativo(
            problemas_ativos,
            codigos_vistos,
            tipo_codigo=problema.tipo_codigo,
            codigo=problema.codigo,
            descricao=problema.descricao,
            situacao=problema.situacao,
            data_registro=problema.data_registro,
            origem="PRONTUARIO",
        )

    # Episódios diagnósticos dos atendimentos SOAP ainda não resolvidos
    problemas_atendimento = (
        db.query(AtendimentoProblema)
        .join(AtendimentoSOAP, AtendimentoProblema.atendimento_id == AtendimentoSOAP.id)
        .filter(
            AtendimentoSOAP.cidadao_id == cidadao.id,
            AtendimentoProblema.situacao != "RESOLVIDO",
        )
        .order_by(AtendimentoSOAP.data_hora_inicio.desc())
        .all()
    )
    for episodio in problemas_atendimento:
        _registrar_problema_ativo(
            problemas_ativos,
            codigos_vistos,
            tipo_codigo=episodio.tipo_codigo,
            codigo=episodio.codigo,
            descricao=episodio.descricao,
            situacao=episodio.situacao,
            data_registro=(
                episodio.atendimento.data_hora_inicio
                if episodio.atendimento is not None
                else None
            ),
            origem="ATENDIMENTO",
        )

    total_atendimentos = (
        db.query(func.count(AtendimentoSOAP.id))
        .filter(AtendimentoSOAP.cidadao_id == cidadao.id)
        .scalar()
        or 0
    )

    return ProntuarioResumoOut(
        cidadao=cidadao,
        problemas_ativos=problemas_ativos,
        alergias=_listar_alergias(cidadao.alergias),
        medicamentos_em_uso=_extrair_medicamentos_em_uso(atendimentos),
        total_atendimentos=total_atendimentos,
        data_ultimo_atendimento=(
            atendimentos[0].data_hora_inicio if atendimentos else None
        ),
    )


@router.get(
    "/{cns}/evolucoes",
    response_model=PaginaEvolucoesOut,
    summary="Lista paginada das evoluções clínicas (SOAP)",
)
def listar_evolucoes_prontuario(
    cns: CNSPath,
    skip: Annotated[int, Query(ge=0, description="Registros a ignorar (offset)")] = 0,
    limit: Annotated[
        int, Query(gt=0, le=100, description="Tamanho da página (máximo 100)")
    ] = 20,
    db: Session = Depends(get_db),
) -> PaginaEvolucoesOut:
    """Retorna as evoluções (atendimentos SOAP) do cidadão, paginadas por offset.

    Ordenadas da mais recente para a mais antiga, com metadados de paginação
    (total, skip e limit) para consumo incremental pelo frontend.
    """
    cidadao = _obter_cidadao_por_cns(db, cns)

    consulta_base = db.query(AtendimentoSOAP).filter(
        AtendimentoSOAP.cidadao_id == cidadao.id
    )
    total = consulta_base.count()

    itens = (
        consulta_base.order_by(
            AtendimentoSOAP.data_hora_inicio.desc(), AtendimentoSOAP.id.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return PaginaEvolucoesOut(total=total, skip=skip, limit=limit, itens=itens)


@router.post(
    "/{cns}/alergia",
    response_model=AlergiaCriadaOut,
    status_code=201,
    summary="Registra alergia no prontuário do cidadão",
)
def registrar_alergia_prontuario(
    cns: CNSPath, payload: AlergiaCreate, db: Session = Depends(get_db)
) -> AlergiaCriadaOut:
    """Registra uma nova alergia (condição autorreferida) no prontuário.

    Retorna 201 com o item criado e a lista atualizada. Alergias já existentes
    (comparação sem diferenciar caixa) retornam 422.
    """
    cidadao = _obter_cidadao_por_cns(db, cns)

    alergias_atuais = _listar_alergias(cidadao.alergias)
    if any(
        existente.casefold() == payload.descricao.casefold()
        for existente in alergias_atuais
    ):
        raise HTTPException(
            status_code=422,
            detail="Alergia já registrada no prontuário do cidadão.",
        )

    alergias_atualizadas = [*alergias_atuais, payload.descricao]
    cidadao.alergias = "; ".join(alergias_atualizadas)

    db.commit()
    db.refresh(cidadao)

    return AlergiaCriadaOut(
        cidadao_id=cidadao.id,
        descricao=payload.descricao,
        alergias=_listar_alergias(cidadao.alergias),
    )


@router.post(
    "/{cns}/problema",
    response_model=ProblemaProntuarioOut,
    status_code=201,
    summary="Registra problema/condição na Lista de Problemas",
)
def registrar_problema_prontuario(
    cns: CNSPath, payload: ProblemaProntuarioCreate, db: Session = Depends(get_db)
) -> ProblemaProntuarioOut:
    """Registra um problema/condição (CIAP-2 ou CID-10) na Lista de Problemas.

    O código deve seguir o padrão oficial da terminologia informada. Já existe
    registro com o mesmo código e situação não resolvida? Retorna 422.
    """
    cidadao = _obter_cidadao_por_cns(db, cns)

    problema_duplicado = (
        db.query(ProntuarioProblema)
        .filter(
            ProntuarioProblema.cidadao_id == cidadao.id,
            ProntuarioProblema.tipo_codigo == payload.tipo_codigo,
            func.upper(ProntuarioProblema.codigo) == payload.codigo.upper(),
            ProntuarioProblema.situacao != "RESOLVIDO",
        )
        .first()
    )
    if problema_duplicado is not None:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Problema {payload.tipo_codigo} {payload.codigo} já registrado "
                "e não resolvido no prontuário do cidadão."
            ),
        )

    problema = ProntuarioProblema(cidadao_id=cidadao.id, **payload.model_dump())
    db.add(problema)
    db.commit()
    db.refresh(problema)

    return problema