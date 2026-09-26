"""
Motor Fiscal DMED (Receita Federal) — Projeto MedIA (Saúde 4.0)
Geração programática do leiaute magnético oficial da Declaração de Serviços Médicos e de Saúde.
Conformidade: Instrução Normativa RFB nº 1.987/2020 e layouts anuais da Receita Federal.
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional
import re


@dataclass
class LancamentoDespesaMedica:
    cpf_responsavel_pagamento: str
    nome_responsavel_pagamento: str
    cpf_beneficiario: Optional[str]
    data_nascimento_beneficiario: Optional[date]
    nome_beneficiario: str
    valor_pago: float
    data_servico: date
    descricao_servico: str = "Consulta médica / Atendimento clínico"


@dataclass
class DeclaracaoDMED:
    ano_calendario: int
    cnpj_prestador: str
    nome_empresarial: str
    numero_recibo_anterior: Optional[str] = None
    retificadora: bool = False
    lancamentos: List[LancamentoDespesaMedica] = None


class MotorFiscalDMED:
    """Motor de formatação e validação do arquivo texto magnético DMED."""

    @classmethod
    def validar_cpf(cls, cpf: str) -> bool:
        """Validação estrita de dígito verificador de CPF."""
        cpf_limpo = re.sub(r"\D", "", cpf or "")
        if len(cpf_limpo) != 11 or cpf_limpo == cpf_limpo[0] * 11:
            return False

        for i in range(9, 11):
            soma = sum(int(cpf_limpo[num]) * ((i + 1) - num) for num in range(0, i))
            digito = ((soma * 10) % 11) % 10
            if digito != int(cpf_limpo[i]):
                return False
        return True

    @classmethod
    def gerar_arquivo_magnetico(cls, declaracao: DeclaracaoDMED) -> str:
        """
        Gera o arquivo de texto magnético em conformidade com o leiaute da Receita Federal.
        Linhas com tamanho fixo e delimitador padrão.
        """
        linhas = []
        cnpj_limpo = re.sub(r"\D", "", declaracao.cnpj_prestador).zfill(14)

        # 1. Registro Header (Cabeçalho da Declaração)
        tipo_declaracao = "R" if declaracao.retificadora else "O"  # O=Original, R=Retificadora
        recibo = (declaracao.numero_recibo_anterior or "").zfill(12) if declaracao.retificadora else "0" * 12
        header = f"DMED|{declaracao.ano_calendario}|{cnpj_limpo}|{declaracao.nome_empresarial[:60].ljust(60)}|{tipo_declaracao}|{recibo}"
        linhas.append(header)

        # 2. Registros de Serviços Médicos Prestados (ROP - Responsável pelo Pagamento)
        total_valor = 0.0
        lancamentos = declaracao.lancamentos or []

        for item in lancamentos:
            cpf_resp = re.sub(r"\D", "", item.cpf_responsavel_pagamento).zfill(11)
            cpf_ben = re.sub(r"\D", "", item.cpf_beneficiario or "").zfill(11) if item.cpf_beneficiario else ""
            nasc_ben = item.data_nascimento_beneficiario.strftime("%d%m%Y") if item.data_nascimento_beneficiario else ""
            valor_centavos = int(round(item.valor_pago * 100))
            total_valor += item.valor_pago

            # Layout: ROP|CPF_RESP|NOME_RESP|CPF_BEN|NASC_BEN|NOME_BEN|VALOR_CENTAVOS
            linha_rop = (
                f"ROP|{cpf_resp}|{item.nome_responsavel_pagamento[:60].ljust(60)}|"
                f"{cpf_ben.ljust(11)}|{nasc_ben.ljust(8)}|{item.nome_beneficiario[:60].ljust(60)}|"
                f"{str(valor_centavos).zfill(12)}"
            )
            linhas.append(linha_rop)

        # 3. Registro Trailer (Encerramento do Arquivo com Totalizadores)
        total_centavos = int(round(total_valor * 100))
        total_registros = len(linhas) + 1  # Incluindo o próprio trailer
        trailer = f"T9|{str(total_registros).zfill(8)}|{str(total_centavos).zfill(15)}"
        linhas.append(trailer)

        return "\r\n".join(linhas) + "\r\n"
