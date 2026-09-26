"""
Rotas REST de Gestão Financeira, Pix e Livro Caixa para Médicos.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.pix_cobranca import MotorPixCobranca, DadosCobrancaPix
from app.services.livro_caixa import MotorLivroCaixaMedico, LancamentoReceita, LancamentoDespesa

router = APIRouter(prefix="/financeiro-medico", tags=["Financeiro & Pix Médico"])


class GerarPixRequest(BaseModel):
    chave_pix: str
    nome_beneficiario: str = "Dr. João Paulo Versiani"
    cidade_beneficiario: str = "Montes Claros"
    valor: float = 350.00
    identificador_transacao: Optional[str] = None
    descricao: Optional[str] = "Consulta Medica Telemedicina"


@router.post("/pix/gerar-cobranca")
def gerar_cobranca_pix(payload: GerarPixRequest):
    """Gera string oficial Pix Copia e Cola (padrão EMV Banco Central) com CRC16."""
    dados = DadosCobrancaPix(
        chave_pix=payload.chave_pix,
        nome_beneficiario=payload.nome_beneficiario,
        cidade_beneficiario=payload.cidade_beneficiario,
        valor=payload.valor,
        identificador_transacao=payload.identificador_transacao,
        descricao_consulta=payload.descricao,
    )
    return MotorPixCobranca.gerar_pix_copia_e_cola(dados)


@router.get("/livro-caixa/demonstrativo")
def obter_demonstrativo_livro_caixa(mes_ano: str = Query("09/2026")):
    """Retorna o balancete de livro caixa com apuração estimada de Carnê-Leão e DMED."""
    # Semente de dados representativa do mês para o consultório
    receitas = [
        LancamentoReceita("2026-09-02", "Mariana Souza Alencar", "12345678901", "TELEMEDICINA", 350.0, "REC-01"),
        LancamentoReceita("2026-09-04", "Roberto Carlos Fagundes", "98765432100", "PRESENCIAL", 400.0, "REC-02"),
        LancamentoReceita("2026-09-08", "Juliana Mendes Prado", "45678912344", "TELEMEDICINA", 350.0, "REC-03"),
        LancamentoReceita("2026-09-12", "Carlos Eduardo Pereira", "11122233344", "PRESENCIAL", 300.0, "REC-04"),
        LancamentoReceita("2026-09-18", "Camila Guimarães Ribeiro", "55566677788", "TELEMEDICINA", 380.0, "REC-05"),
    ]
    despesas = [
        LancamentoDespesa("2026-09-05", "Internet Fibra Home Office", "TELECOMUNICACOES", 180.0),
        LancamentoDespesa("2026-09-10", "Aluguel Consultório Montes Claros", "ALUGUEL_CONSULTORIO", 600.0),
        LancamentoDespesa("2026-09-15", "Conselho Regional de Medicina (Anuidade CRM-MG)", "ANUIDADE_CRM", 120.0),
    ]
    return MotorLivroCaixaMedico.gerar_demonstrativo_mensal(receitas, despesas, mes_ano)
