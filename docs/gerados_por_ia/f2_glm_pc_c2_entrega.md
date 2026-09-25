```python
"""
API de Dispensação Farmacêutica e Baixa de Receita (C2)

Este módulo implementa as rotas de consulta e confirmação de dispensação de
medicamentos para o projeto MedIA, atendendo aos requisitos de farmácia e
controle de receitas.

As rotas são:

- POST /dispensacao/consultar : Valida o QR Code/hash da receita e retorna
  informações sobre os medicamentos prescritos e saldos restantes.
- POST /dispensacao/confirmar : Registra a baixa (total ou fracionada) de
  medicamentos de uma receita, atualizando as quantidades dispensadas.

Toda a lógica é implementada com FastAPI, Pydantic v2 e SQLAlchemy 2.0,
seguindo o padrão do projeto MedIA.
"""

from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ...core.database import get_db
from ...models import (
    Receita,
    ItemReceita,
    Medicamento,
    Dispensacao,
    ItemDispensacao,
    Paciente,
    Medico,
)
from ...schemas import (
    # Caso existam schemas específicos, podem ser importados aqui.
    # Como não foram fornecidos, definimos schemas locais.
)

router = APIRouter(prefix="/dispensacao", tags=["Farmácia"])

# ----------------------------------------------------------------------
# Schemas Pydantic v2
# ----------------------------------------------------------------------

class ConsultaRequest(BaseModel):
    """Payload para consulta de receita por QR Code/hash."""
    codigo: str = Field(..., description="Hash ou código QR da receita")

class ItemConsultaResponse(BaseModel):
    """Representa um item da receita na resposta de consulta."""
    medicamento: str
    quantidade_prescrita: int
    quantidade_dispensada: int
    saldo_restante: int

class ConsultaResponse(BaseModel):
    """Resposta da consulta de receita."""
    receita_id: int
    paciente_nome: str
    medico_nome: str
    status: str
    itens: List[ItemConsultaResponse]

class ItemConfirmacao(BaseModel):
    """Item para confirmação de dispensação (uso em baixa fracionada)."""
    medicamento_id: int
    quantidade: int = Field(gt=0)

class ConfirmacaoRequest(BaseModel):
    """Payload para confirmação de dispensação."""
    codigo_receita: str
    tipo: Literal["total", "fracionada"] = Field(
        ..., description="Tipo de baixa: total ou fracionada"
    )
    itens: Optional[List[ItemConfirmacao]] = Field(
        None,
        description="Lista de itens para baixa fracionada (ignorado se tipo='total')",
    )

class ConfirmacaoResponse(BaseModel):
    """Resposta da confirmação de dispensação."""
    dispensacao_id: int
    status: str
    mensagem: str

# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------

@router.post(
    "/consultar",
    response_model=ConsultaResponse,
    status_code=status.HTTP_200_OK,
)
def consultar_receita(payload: ConsultaRequest, db: Session = Depends(get_db)):
    """
    Valida o QR Code/hash de uma receita e retorna seus dados.

    - Verifica se a receita existe e está ativa.
    - Retorna informações do paciente, médico e itens com saldos.
    """
    receita = db.query(Receita).filter(
        (Receita.hash == payload.codigo) | (Receita.qr_code == payload.codigo)
    ).first()

    if not receita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receita não encontrada",
        )

    if receita.status not in ("ativa", "parcial"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Receita com status '{receita.status}' não pode ser consultada",
        )

    # Verifica validade da receita (se houver campo)
    if receita.validade and receita.validade < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receita expirada",
        )

    # Carrega dados do paciente e médico
    paciente = db.query(Paciente).get(receita.paciente_id)
    medico = db.query(Medico).get(receita.medico_id)

    # Monta itens da resposta
    itens = []
    for item in receita.itens:  # assumindo relação 'itens'
        medicamento = db.query(Medicamento).get(item.medicamento_id)
        saldo = item.quantidade_prescrita - item.quantidade_dispensada
        itens.append(
            ItemConsultaResponse(
                medicamento=medicamento.nome,
                quantidade_prescrita=item.quantidade_prescrita,
                quantidade_dispensada=item.quantidade_dispensada,
                saldo_restante=saldo,
            )
        )

    return ConsultaResponse(
        receita_id=receita.id,
        paciente_nome=paciente.nome,
        medico_nome=medico.nome,
        status=receita.status,
        itens=itens,
    )


@router.post(
    "/confirmar",
    response_model=ConfirmacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirmar_dispensacao(payload: ConfirmacaoRequest, db: Session = Depends(get_db)):
    """
    Registra a dispensação de medicamentos de uma receita.

    - Para baixa total, dispensa todo o saldo restante de todos os itens.
    - Para baixa fracionada, dispensa as quantidades especificadas para os
      medicamentos informados.
    - Atualiza as quantidades dispensadas e o status da receita.
    """
    receita = db.query(Receita).filter(
        (Receita.hash == payload.codigo_receita) | (Receita.qr_code == payload.codigo_receita)
    ).first()

    if not receita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receita não encontrada",
        )

    if receita.status not in ("ativa", "parcial"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Receita com status '{receita.status}' não permite dispensação",
        )

    # Verifica validade
    if receita.validade and receita.validade < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Receita expirada",
        )

    # Prepara a dispensação principal
    dispensacao = Dispensacao(
        receita_id=receita.id,
        data=datetime.utcnow(),
        tipo=payload.tipo,
    )
    db.add(dispensacao)
    db.flush()  # para obter o ID da dispensação

    # Lista de itens a serem dispensados
    itens_a_dispensar = []

    if payload.tipo == "total":
        # Dispensa todos os itens restantes
        for item_receita in receita.itens:
            saldo = item_receita.quantidade_prescrita - item_receita.quantidade_dispensada
            if saldo > 0:
                itens_a_dispensar.append(
                    (item_receita, saldo)
                )
    else:  # fracionada
        if not payload.itens:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para baixa fracionada, informe os itens a dispensar",
            )
        # Valida cada item informado
        for item_confirm in payload.itens:
            item_receita = db.query(ItemReceita).filter(
                ItemReceita