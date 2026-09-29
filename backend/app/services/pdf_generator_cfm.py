"""
Gerador de PDF de Documentos Médicos — Padrão CFM 2.314/2022.

Utiliza ReportLab para compor receitas médicas (simples, antimicrobianos em 2 vias,
controle especial) e atestados médicos oficiais, com layout institucional,
carimbo digital, hash criptográfico SHA-256 e QR Code vetorial de validação pública.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.barcode.qr import QrCodeWidget

from app.services.prescricao_digital_cfm import (
    DocumentoAtestadoCFM,
    DocumentoPrescricaoCFM,
    TipoPrescricao,
)


class GeradorPDFMedicoCFM:
    """Motor de renderização de PDFs clínicos em conformidade com o CFM e ICP-Brasil."""

    @classmethod
    def gerar_pdf_prescricao(
        cls,
        doc: DocumentoPrescricaoCFM,
        url_validacao: str,
    ) -> bytes:
        """Gera o PDF da prescrição médica.
        
        Se for antimicrobiano ou controle especial, gera documento em 2 vias:
        Via 1: Farmácia (Retenção)
        Via 2: Paciente (Orientação)
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4

        precisa_duas_vias = doc.tipo_prescricao in (
            TipoPrescricao.ANTIBIOTICO,
            TipoPrescricao.CONTROLE_ESPECIAL,
        )

        if precisa_duas_vias:
            # Página 1: 1ª Via — Retenção da Farmácia / Dispensação
            cls._desenhar_pagina_prescricao(
                c, doc, url_validacao, via_texto="1ª VIA — RETENÇÃO DA FARMÁCIA / DISPENSAÇÃO", largura=largura, altura=altura
            )
            c.showPage()
            # Página 2: 2ª Via — Paciente
            cls._desenhar_pagina_prescricao(
                c, doc, url_validacao, via_texto="2ª VIA — ORIENTAÇÃO DO PACIENTE", largura=largura, altura=altura
            )
            c.showPage()
        else:
            cls._desenhar_pagina_prescricao(
                c, doc, url_validacao, via_texto="VIA ÚNICA — PACIENTE E FARMÁCIA", largura=largura, altura=altura
            )
            c.showPage()

        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def _desenhar_pagina_prescricao(
        cls,
        c: canvas.Canvas,
        doc: DocumentoPrescricaoCFM,
        url_validacao: str,
        via_texto: str,
        largura: float,
        altura: float,
    ) -> None:
        margem = 1.8 * cm
        largura_util = largura - 2 * margem

        # ---------------------------------------------------------------------
        # CABEÇALHO INSTITUCIONAL & MÉDICO
        # ---------------------------------------------------------------------
        # Faixa superior azul escura
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(margem, altura - 2.8 * cm, largura_util, 2.0 * cm, fill=1, stroke=0)

        # Identificação da Clínica / Plataforma
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margem + 12, altura - 1.5 * cm, "MedIA Practice OS — Consultório Médico")

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(
            margem + 12,
            altura - 2.0 * cm,
            "Atenção Médica Especializada e Telemedicina • Resolução CFM nº 2.314/2022",
        )

        # Identificação do Médico no topo à direita
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(largura - margem - 12, altura - 1.5 * cm, doc.medico_nome)

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#38bdf8"))
        crm_texto = f"CRM-{doc.medico_uf} {doc.medico_crm}"
        if doc.medico_rqe:
            crm_texto += f"  |  RQE {doc.medico_rqe}"
        c.drawRightString(largura - margem - 12, altura - 2.0 * cm, crm_texto)

        # Faixa de Identificação da Via e Tipo de Receita
        y_atual = altura - 3.4 * cm
        if doc.tipo_prescricao == TipoPrescricao.ANTIBIOTICO:
            cor_faixa = colors.HexColor("#dc2626")  # Vermelho
            titulo_tipo = "RECEITUÁRIO DE ANTIMICROBIANO (RDC Nº 20/2011 - ANVISA)"
        elif doc.tipo_prescricao == TipoPrescricao.CONTROLE_ESPECIAL:
            cor_faixa = colors.HexColor("#ea580c")  # Laranja
            titulo_tipo = "RECEITUÁRIO DE CONTROLE ESPECIAL (PORTARIA SVS/MS Nº 344/1998)"
        else:
            cor_faixa = colors.HexColor("#2563eb")  # Azul
            titulo_tipo = "RECEITUÁRIO MÉDICO SIMPLES"

        c.setFillColor(cor_faixa)
        c.roundRect(margem, y_atual - 0.6 * cm, largura_util, 0.7 * cm, 4, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margem + 10, y_atual - 0.38 * cm, titulo_tipo)
        c.drawRightString(largura - margem - 10, y_atual - 0.38 * cm, via_texto)

        # ---------------------------------------------------------------------
        # DADOS DO PACIENTE
        # ---------------------------------------------------------------------
        y_atual -= 1.1 * cm
        c.setFillColor(colors.HexColor("#f8fafc"))
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.roundRect(margem, y_atual - 1.3 * cm, largura_util, 1.4 * cm, 4, fill=1, stroke=1)

        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margem + 10, y_atual - 0.35 * cm, "PACIENTE:")
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor("#0f172a"))
        c.drawString(margem + 65, y_atual - 0.35 * cm, doc.paciente_nome)

        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 8)
        cpf_mascarado = (
            f"***.{doc.paciente_cpf[3:6]}.{doc.paciente_cpf[6:9]}-**"
            if len(doc.paciente_cpf) == 11
            else doc.paciente_cpf
        )
        c.drawString(margem + 10, y_atual - 0.85 * cm, f"CPF: {cpf_mascarado}")

        # Data formatada
        try:
            dt_obj = datetime.fromisoformat(doc.data_emissao.replace("Z", "+00:00"))
            data_fmt = dt_obj.strftime("%d/%m/%Y às %H:%M")
        except Exception:
            data_fmt = doc.data_emissao

        c.drawRightString(largura - margem - 10, y_atual - 0.85 * cm, f"Data de Emissão: {data_fmt}")

        # ---------------------------------------------------------------------
        # CORPO DA PRESCRIÇÃO (MEDICAMENTOS E POSOLOGIA)
        # ---------------------------------------------------------------------
        y_atual -= 1.9 * cm

        c.setFillColor(colors.HexColor("#1e293b"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem, y_atual, "PRESCRIÇÃO TERAPÊUTICA")

        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.setLineWidth(0.8)
        c.line(margem, y_atual - 4, largura - margem, y_atual - 4)

        y_atual -= 18

        for idx, item in enumerate(doc.itens, start=1):
            # Título do Fármaco
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor("#0f172a"))
            linha_farmaco = f"{idx}. {item.farmaco}"
            if item.concentracao:
                linha_farmaco += f" {item.concentracao}"
            if item.forma_farmaceutica:
                linha_farmaco += f" ({item.forma_farmaceutica})"
            if item.quantidade_total:
                linha_farmaco += f" ------------------ {item.quantidade_total}"

            c.drawString(margem + 10, y_atual, linha_farmaco)
            y_atual -= 14

            # Posologia e Via
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor("#334155"))
            c.drawString(
                margem + 24,
                y_atual,
                f"Via de administração: {item.via_administracao}  •  Posologia: {item.posologia}",
            )
            y_atual -= 14

            # Instruções especiais (se houver)
            if item.instrucoes_especiais:
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColor(colors.HexColor("#64748b"))
                c.drawString(margem + 24, y_atual, f"Obs: {item.instrucoes_especiais}")
                y_atual -= 12

            y_atual -= 6

        # Instruções gerais adicionais
        if doc.instrucoes_gerais:
            y_atual -= 8
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.HexColor("#475569"))
            c.drawString(margem + 10, y_atual, "ORIENTAÇÕES ADICIONAIS:")
            y_atual -= 12
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#334155"))
            for linha in doc.instrucoes_gerais.split("\n"):
                c.drawString(margem + 10, y_atual, linha)
                y_atual -= 10

        # Campo de Identificação do Comprador / Farmácia (para Antibióticos e Controle Especial)
        if doc.tipo_prescricao in (TipoPrescricao.ANTIBIOTICO, TipoPrescricao.CONTROLE_ESPECIAL):
            y_comprador = 7.0 * cm
            c.setFillColor(colors.HexColor("#f1f5f9"))
            c.setStrokeColor(colors.HexColor("#cbd5e1"))
            c.roundRect(margem, y_comprador, largura_util, 2.2 * cm, 4, fill=1, stroke=1)

            c.setFillColor(colors.HexColor("#334155"))
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(margem + 8, y_comprador + 1.8 * cm, "IDENTIFICAÇÃO DO COMPRADOR / DISPENSAÇÃO FARMACÊUTICA:")

            c.setFont("Helvetica", 7)
            c.drawString(margem + 8, y_comprador + 1.3 * cm, "Nome do Comprador: _____________________________________________   RG/Órgão: __________________")
            c.drawString(margem + 8, y_comprador + 0.8 * cm, "Endereço: _____________________________________________________   Telefone: __________________")
            c.drawString(margem + 8, y_comprador + 0.3 * cm, "Farmacêutico Responsável / CRF: ________________________________   Data: _____/_____/2026")

        # ---------------------------------------------------------------------
        # RODAPÉ DE VALIDAÇÃO ELETRÔNICA, QR CODE & CONFORMIDADE CFM
        # ---------------------------------------------------------------------
        altura_rodape = 3.6 * cm
        y_rodape = margem

        # Caixa do rodapé
        c.setFillColor(colors.HexColor("#f8fafc"))
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.roundRect(margem, y_rodape, largura_util, altura_rodape, 4, fill=1, stroke=1)

        # Inserção do QR Code Oficial de Validação Pública
        qr_tamanho = 2.6 * cm
        qr = QrCodeWidget(url_validacao)
        qr.barWidth = qr_tamanho
        qr.barHeight = qr_tamanho
        qr.qrVersion = 3
        d = Drawing(qr_tamanho, qr_tamanho)
        d.add(qr)
        d.drawOn(c, margem + 8, y_rodape + 0.5 * cm)

        # Informações de Auditoria e Validação ao lado do QR Code
        x_info = margem + qr_tamanho + 20
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x_info, y_rodape + 3.0 * cm, "DOCUMENTO MÉDICO ASSINADO ELETRONICAMENTE (CFM 2.314/2022)")

        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawString(
            x_info,
            y_rodape + 2.5 * cm,
            f"Código de Validação: {doc.codigo_validacao}   •   Status: {doc.status}",
        )

        c.drawString(
            x_info,
            y_rodape + 2.0 * cm,
            f"Assinado por: {doc.medico_nome} (CRM-{doc.medico_uf} {doc.medico_crm})",
        )

        c.setFont("Courier", 6.5)
        c.setFillColor(colors.HexColor("#64748b"))
        hash_curto = doc.hash_integridade_sha256[:32] + "..." + doc.hash_integridade_sha256[-16:]
        c.drawString(x_info, y_rodape + 1.4 * cm, f"Hash SHA-256: {hash_curto}")

        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.HexColor("#2563eb"))
        c.drawString(x_info, y_rodape + 0.8 * cm, f"Verifique a autenticidade apontando a câmera ou acessando:")
        c.drawString(x_info, y_rodape + 0.4 * cm, url_validacao)

    @classmethod
    def gerar_pdf_atestado(
        cls,
        doc: DocumentoAtestadoCFM,
        url_validacao: str,
    ) -> bytes:
        """Gera o PDF oficial do atestado médico conforme normas do CFM."""
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4
        margem = 2.0 * cm
        largura_util = largura - 2 * margem

        # Cabeçalho Azul Escuro
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(margem, altura - 3.0 * cm, largura_util, 2.0 * cm, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margem + 14, altura - 1.7 * cm, "MedIA Practice OS — Consultório Médico")

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(
            margem + 14,
            altura - 2.2 * cm,
            "Atenção Médica Especializada • Resoluções CFM nº 2.314/2022 e 1.658/2002",
        )

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(largura - margem - 14, altura - 1.7 * cm, doc.medico_nome)

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.drawRightString(largura - margem - 14, altura - 2.2 * cm, f"CRM-{doc.medico_uf} {doc.medico_crm}")

        # Título Central
        y = altura - 5.0 * cm
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(largura / 2, y, "ATESTADO MÉDICO")

        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.setLineWidth(1)
        c.line(largura / 2 - 80, y - 6, largura / 2 + 80, y - 6)

        # Corpo do Atestado
        y -= 2.2 * cm
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#1e293b"))

        cpf_mascarado = (
            f"***.{doc.paciente_cpf[3:6]}.{doc.paciente_cpf[6:9]}-**"
            if len(doc.paciente_cpf) == 11
            else doc.paciente_cpf
        )

        paragrafo1 = (
            f"Atesto para os devidos fins que o(a) paciente Sr(a). {doc.paciente_nome}, "
            f"inscrito(a) no CPF sob o nº {cpf_mascarado}, esteve sob meus cuidados profissionais "
            f"nesta data e necessita de {doc.dias_afastamento} ({cls._numero_por_extenso(doc.dias_afastamento)}) "
            f"dia(s) de afastamento de suas atividades habituais e laborais, para fins de repouso e recuperação."
        )

        # Quebra simples de texto
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import Paragraph

        styles = getSampleStyleSheet()
        style_corpo = ParagraphStyle(
            name="AtestadoCorpo",
            fontName="Helvetica",
            fontSize=11,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            alignment=4,  # Justificado
        )

        p = Paragraph(paragrafo1, style_corpo)
        w, h = p.wrap(largura_util, 200)
        p.drawOn(c, margem, y - h)

        y = y - h - 1.5 * cm

        # Notificação de CID-10
        if doc.motivo_cid10:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margem, y, f"Diagnóstico Provável / CID-10: {doc.motivo_cid10}")
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.HexColor("#64748b"))
            c.drawString(
                margem,
                y - 12,
                "(Informação inserida sob autorização expressa do paciente, conforme Resolução CFM nº 1.658/2002)",
            )
            y -= 1.2 * cm

        # Local e Data
        y -= 1.0 * cm
        try:
            dt_obj = datetime.fromisoformat(doc.data_emissao.replace("Z", "+00:00"))
            data_fmt = dt_obj.strftime("%d de %B de %Y")
        except Exception:
            data_fmt = doc.data_emissao

        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawRightString(largura - margem, y, f"Emitido em {data_fmt}")

        # Assinatura Digital Centralizada
        y -= 3.0 * cm
        c.setStrokeColor(colors.HexColor("#94a3b8"))
        c.line(largura / 2 - 120, y, largura / 2 + 120, y)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor("#0f172a"))
        c.drawCentredString(largura / 2, y - 14, doc.medico_nome)

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748b"))
        c.drawCentredString(largura / 2, y - 26, f"Médico — CRM-{doc.medico_uf} {doc.medico_crm}")

        # Rodapé de Validação Eletrônica
        altura_rodape = 3.6 * cm
        y_rodape = margem
        c.setFillColor(colors.HexColor("#f8fafc"))
        c.setStrokeColor(colors.HexColor("#cbd5e1"))
        c.roundRect(margem, y_rodape, largura_util, altura_rodape, 4, fill=1, stroke=1)

        qr_tamanho = 2.6 * cm
        qr = QrCodeWidget(url_validacao)
        qr.barWidth = qr_tamanho
        qr.barHeight = qr_tamanho
        qr.qrVersion = 3
        d = Drawing(qr_tamanho, qr_tamanho)
        d.add(qr)
        d.drawOn(c, margem + 8, y_rodape + 0.5 * cm)

        x_info = margem + qr_tamanho + 20
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x_info, y_rodape + 3.0 * cm, "ATESTADO MÉDICO COM VALIDAÇÃO PÚBLICA ELETRÔNICA")

        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#334155"))
        c.drawString(x_info, y_rodape + 2.5 * cm, f"Código Validador: {doc.codigo_validacao}   •   Status: {doc.status}")
        c.drawString(x_info, y_rodape + 2.0 * cm, f"Emissor: {doc.medico_nome} (CRM-{doc.medico_uf} {doc.medico_crm})")

        c.setFont("Courier", 6.5)
        c.setFillColor(colors.HexColor("#64748b"))
        hash_curto = doc.hash_integridade_sha256[:32] + "..." + doc.hash_integridade_sha256[-16:]
        c.drawString(x_info, y_rodape + 1.4 * cm, f"Hash SHA-256: {hash_curto}")

        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.HexColor("#2563eb"))
        c.drawString(x_info, y_rodape + 0.8 * cm, "Para verificar a veracidade deste atestado, leia o QR Code ou acesse:")
        c.drawString(x_info, y_rodape + 0.4 * cm, url_validacao)

        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _numero_por_extenso(n: int) -> str:
        extenso = {
            1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco",
            6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
            14: "quatorze", 15: "quinze", 30: "trinta"
        }
        return extenso.get(n, str(n))
