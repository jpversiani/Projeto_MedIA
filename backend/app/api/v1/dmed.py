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
    cpf_responsavel_pagamento: str = Field(..., json_schema_extra={"example": "12345678909"})
    nome_responsavel_pagamento: str = Field(..., json_schema_extra={"example": "João da Silva"})
    cpf_beneficiario: Optional[str] = Field(None, json_schema_extra={"example": "12345678909"})
    data_nascimento_beneficiario: Optional[date] = Field(None, json_schema_extra={"example": "1985-04-12"})
    nome_beneficiario: str = Field(..., json_schema_extra={"example": "João da Silva"})
    valor_pago: float = Field(..., json_schema_extra={"example": 350.00})
    data_servico: date = Field(default_factory=date.today)
    descricao_servico: str = Field("Consulta Médica Especializada")


class DeclaracaoDMEDRequest(BaseModel):
    ano_calendario: int = Field(2025, json_schema_extra={"example": 2025})
    cnpj_prestador: str = Field(..., json_schema_extra={"example": "12345678000199"})
    nome_empresarial: str = Field(..., json_schema_extra={"example": "CLINICA MEDICA VERSINI LTDA"})
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


@router.get("/exportar-exemplo")
def exportar_exemplo_dmed():
    """Gera e retorna o arquivo magnético DMED oficial pronto para o lote da clínica."""
    lancamentos_exemplo = [
        LancamentoDespesaMedica(
            cpf_responsavel_pagamento="12345678901",
            nome_responsavel_pagamento="Mariana Souza Alencar",
            cpf_beneficiario="12345678901",
            data_nascimento_beneficiario=date(1992, 5, 14),
            nome_beneficiario="Mariana Souza Alencar",
            valor_pago=350.00,
            data_servico=date.today(),
            descricao_servico="Consulta Psiquiatria / Telemedicina",
        ),
        LancamentoDespesaMedica(
            cpf_responsavel_pagamento="98765432100",
            nome_responsavel_pagamento="Roberto Carlos Fagundes",
            cpf_beneficiario="98765432100",
            data_nascimento_beneficiario=date(1978, 11, 22),
            nome_beneficiario="Roberto Carlos Fagundes",
            valor_pago=400.00,
            data_servico=date.today(),
            descricao_servico="Consulta Cardiologia / Presencial",
        ),
        LancamentoDespesaMedica(
            cpf_responsavel_pagamento="45678912344",
            nome_responsavel_pagamento="Juliana Mendes Prado",
            cpf_beneficiario="45678912344",
            data_nascimento_beneficiario=date(1985, 3, 9),
            nome_beneficiario="Juliana Mendes Prado",
            valor_pago=350.00,
            data_servico=date.today(),
            descricao_servico="Consulta Telemedicina",
        ),
    ]
    declaracao = DeclaracaoDMED(
        ano_calendario=date.today().year,
        cnpj_prestador="12345678000199",
        nome_empresarial="CLINICA MEDICA VERSINI LTDA",
        numero_recibo_anterior=None,
        retificadora=False,
        lancamentos=lancamentos_exemplo,
    )
    conteudo_txt = MotorFiscalDMED.gerar_arquivo_magnetico(declaracao)
    return Response(
        content=conteudo_txt,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=DMED_{declaracao.ano_calendario}_{declaracao.cnpj_prestador}.txt"
        },
    )
