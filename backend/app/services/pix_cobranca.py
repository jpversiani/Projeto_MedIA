"""
Serviço Gerador de Cobrança Pix (Padrão BR Code / EMV QRCPS-MPM - Banco Central do Brasil).
Permite ao médico gerar QR Code dinâmico/estático e código 'Pix Copia e Cola' instantâneo
para consultas particulares presenciais ou de telemedicina em home office.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Dict, Optional
import uuid


def calcular_crc16(payload: str) -> str:
    """Calcula o checksum CRC16-CCITT (polinômio 0x1021, valor inicial 0xFFFF) do payload EMV."""
    crc = 0xFFFF
    for char in payload.encode("utf-8"):
        crc ^= (char << 8)
        for _ in range(8):
            if (crc & 0x8000) != 0:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def _formatar_campo_emv(id_campo: str, valor: str) -> str:
    """Formata um campo no formato TLV (Tag-Length-Value) do padrão EMV."""
    tamanho = f"{len(valor.encode('utf-8')):02d}"
    return f"{id_campo}{tamanho}{valor}"


@dataclass
class DadosCobrancaPix:
    chave_pix: str  # CPF, CNPJ, E-mail, Celular ou Chave Aleatória
    nome_beneficiario: str  # Nome do médico ou clínica (máx 25 carac)
    cidade_beneficiario: str  # Cidade do consultório (máx 15 carac)
    valor: float  # Valor da consulta em reais
    identificador_transacao: Optional[str] = None  # TxID (máx 25 carac alfanuméricos)
    descricao_consulta: Optional[str] = "Consulta Medica Particular"


class MotorPixCobranca:
    """Motor de geração de BR Code e conciliação de pagamentos Pix para consultórios."""

    PADRAO_PAIS = "BR"
    MOEDA_BRL = "986"

    @classmethod
    def gerar_pix_copia_e_cola(cls, dados: DadosCobrancaPix) -> Dict[str, str]:
        """
        Gera a string oficial Pix Copia e Cola conforme especificação do Banco Central.
        """
        nome_limpo = dados.nome_beneficiario[:25].upper()
        cidade_limpa = dados.cidade_beneficiario[:15].upper()
        txid = (dados.identificador_transacao or f"MED{uuid.uuid4().hex[:10].upper()}")[:25]
        valor_str = f"{dados.valor:.2f}"

        # 00: Payload Format Indicator
        pfi = _formatar_campo_emv("00", "01")

        # 26: Merchant Account Information (Pix)
        gui = _formatar_campo_emv("00", "br.gov.bcb.pix")
        chave = _formatar_campo_emv("01", dados.chave_pix)
        mai_conteudo = gui + chave
        if dados.descricao_consulta:
            desc = _formatar_campo_emv("02", dados.descricao_consulta[:25])
            mai_conteudo += desc
        mai = _formatar_campo_emv("26", mai_conteudo)

        # 52: Merchant Category Code (0000 = Geral / Saúde)
        mcc = _formatar_campo_emv("52", "0000")

        # 53: Transaction Currency (986 = Real Brasileiro BRL)
        moeda = _formatar_campo_emv("53", cls.MOEDA_BRL)

        # 54: Transaction Amount
        valor_campo = _formatar_campo_emv("54", valor_str)

        # 58: Country Code
        pais = _formatar_campo_emv("58", cls.PADRAO_PAIS)

        # 59: Merchant Name
        nome = _formatar_campo_emv("59", nome_limpo)

        # 60: Merchant City
        cidade = _formatar_campo_emv("60", cidade_limpa)

        # 62: Additional Data Field (TxID)
        txid_campo = _formatar_campo_emv("05", txid)
        add_data = _formatar_campo_emv("62", txid_campo)

        # 63: CRC16 prefixo
        payload_sem_crc = pfi + mai + mcc + moeda + valor_campo + pais + nome + cidade + add_data + "6304"
        crc = calcular_crc16(payload_sem_crc)
        pix_completo = payload_sem_crc + crc

        hash_id = hashlib.sha256(pix_completo.encode("utf-8")).hexdigest()

        return {
            "txid": txid,
            "chave_pix": dados.chave_pix,
            "beneficiario": nome_limpo,
            "cidade": cidade_limpa,
            "valor": valor_str,
            "pix_copia_e_cola": pix_completo,
            "crc16": crc,
            "hash_seguranca": hash_id,
            "data_geracao": datetime.now(timezone.utc).isoformat(),
        }


# Alias canônico para importação padronizada nos demais módulos
pix_service = MotorPixCobranca

