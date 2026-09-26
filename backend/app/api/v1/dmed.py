from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from app.services.dmed_generator import (
    MotorFiscalDMED,
    DeclaracaoDMED,
    LancamentoDespesaMedica
)

router = APIRouter(prefix="/dmed", tags=["Motor Fiscal DMED (Receita Federal)"])


class ItemDespesaMedicaSchema(BaseModel):
    cpf_responsavel_pagamento: str = Field(..., example="12345678909")
    nome_responsavel_pagamento: str = Field(..., example="João da Silva")
    cpf_beneficiario: Optional[str] = Field(None, example="12345678909")
    data_nascimento_beneficiario: Optional[date] = Field(None, example="1985-04-12")
    nome_beneficiario: str = Field(..., example="João da Silva")
    valor_pago: float = Field(..., example=350.00)
    data_servico: date = Field(default_factory=date.today)
    descricao_servico: str = Field("Consulta Médica Especializada")


class DeclaracaoDMEDRequest(BaseModel):
    ano_calendario: int = Field(2025, example=2025)
    cnpj_prestador: str = Field(..., example="12345678000199")
    nome_empresarial: str = Field(..., example="CLINICA MEDICA VERSINI LTDA")
    numero_recibo_anterior: Optional[str] = None
    retificadora: bool = False
    lancamentos: List[ItemDespesaMedicaSchema]


@router.post("/exportar-arquivo-magnetico")
def exportar_arquivo_magnetico(dados: DeclaracaoDMEDRequest):
    """
    Gera e exporta o arquivo texto magnético DMED no padrão oficial da Receita Federal.
    """
    itens = [LancamentoDespesaMedica(**item.model_dump()) for item in dados.lancamentos]
    declaracao = DeclaracaoDMED(
        ano_calendario=dados.ano_calendario,
        cnpj_prestador=dados.cnpj_prestador,
        nome_empresarial=dados.nome_empresarial,
        numero_recibo_anterior=dados.numero_recibo_anterior,
        retificadora=dados.retificadora,
        lancamentos=itens
    )
    conteudo_txt = MotorFiscalDMED.gerar_arquivo_magnetico(declaracao)
    
    return Response(
        content=conteudo_txt,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=DMED_{dados.ano_calendario}_{dados.cnpj_prestador}.txt"
        }
    )
