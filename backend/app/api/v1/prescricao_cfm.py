"""
Rotas REST de Prescrição Digital, Atestados Médicos e Validação Pública CFM 2.314/2022.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.services.pdf_generator_cfm import GeradorPDFMedicoCFM
from app.services.prescricao_digital_cfm import (
    DocumentoAtestadoCFM,
    DocumentoPrescricaoCFM,
    MotorPrescricaoCFM,
    TipoPrescricao,
)

router = APIRouter(prefix="/prescricao", tags=["Prescrição Digital CFM"])


class EmitirPrescricaoRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    medico_nome: str = "Dr. João Paulo Versiani"
    medico_crm: str = "78421"
    medico_uf: str = "MG"
    medico_rqe: Optional[str] = "39412"
    tipo: TipoPrescricao = TipoPrescricao.SIMPLES
    itens: List[Dict[str, str]]
    instrucoes_gerais: Optional[str] = None


class EmitirAtestadoRequest(BaseModel):
    paciente_nome: str
    paciente_cpf: str
    medico_nome: str = "Dr. João Paulo Versiani"
    medico_crm: str = "78421"
    medico_uf: str = "MG"
    dias_afastamento: int = 3
    cid10: Optional[str] = None


@router.post("/emitir", status_code=status.HTTP_201_CREATED)
def emitir_prescricao_digital(payload: EmitirPrescricaoRequest, request: Request):
    """Emite prescrição eletrônica com código de validação pública e hash de integridade."""
    doc = MotorPrescricaoCFM.emitir_prescricao(
        paciente_nome=payload.paciente_nome,
        paciente_cpf=payload.paciente_cpf,
        medico_nome=payload.medico_nome,
        medico_crm=payload.medico_crm,
        medico_uf=payload.medico_uf,
        medico_rqe=payload.medico_rqe,
        itens=payload.itens,
        tipo=payload.tipo,
        instrucoes_gerais=payload.instrucoes_gerais,
    )
    base_url = str(request.base_url).rstrip("/")
    url_validador_local = f"{base_url}/api/v1/prescricao/validar-html/{doc.codigo_validacao}"
    url_pdf = f"{base_url}/api/v1/prescricao/{doc.codigo_validacao}/pdf"

    return {
        "codigo_validacao": doc.codigo_validacao,
        "tipo": doc.tipo_prescricao.value,
        "data_emissao": doc.data_emissao,
        "hash_integridade": doc.hash_integridade_sha256,
        "status": doc.status,
        "url_validacao_publica": f"https://validador.media-saude.com.br/verificar?codigo={doc.codigo_validacao}",
        "url_validacao_local": url_validador_local,
        "url_pdf": url_pdf,
    }


@router.post("/atestado/emitir", status_code=status.HTTP_201_CREATED)
def emitir_atestado_digital(payload: EmitirAtestadoRequest, request: Request):
    """Emite atestado médico digital em conformidade com as normas do CFM."""
    doc = MotorPrescricaoCFM.emitir_atestado(
        paciente_nome=payload.paciente_nome,
        paciente_cpf=payload.paciente_cpf,
        medico_nome=payload.medico_nome,
        medico_crm=payload.medico_crm,
        medico_uf=payload.medico_uf,
        dias_afastamento=payload.dias_afastamento,
        cid10=payload.cid10,
    )
    base_url = str(request.base_url).rstrip("/")
    url_validador = f"{base_url}/api/v1/prescricao/validar-html/{doc.codigo_validacao}"
    url_pdf = f"{base_url}/api/v1/prescricao/atestado/{doc.codigo_validacao}/pdf"

    return {
        "codigo_validacao": doc.codigo_validacao,
        "dias_afastamento": doc.dias_afastamento,
        "data_emissao": doc.data_emissao,
        "hash_integridade": doc.hash_integridade_sha256,
        "status": doc.status,
        "url_validacao_publica": url_validador,
        "url_pdf": url_pdf,
    }


@router.get("/{codigo}/pdf")
def download_pdf_prescricao(codigo: str, request: Request):
    """Gera e retorna o PDF oficial da prescrição médica com QR Code para impressão ou download."""
    registro = MotorPrescricaoCFM.obter_documento(codigo)
    if not registro or not isinstance(registro["documento"], DocumentoPrescricaoCFM):
        raise HTTPException(status_code=404, detail="Prescrição médica não encontrada ou expirada.")

    doc: DocumentoPrescricaoCFM = registro["documento"]
    base_url = str(request.base_url).rstrip("/")
    url_validacao = f"{base_url}/api/v1/prescricao/validar-html/{doc.codigo_validacao}"

    pdf_bytes = GeradorPDFMedicoCFM.gerar_pdf_prescricao(doc, url_validacao)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=prescricao_{codigo}.pdf",
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.get("/atestado/{codigo}/pdf")
def download_pdf_atestado(codigo: str, request: Request):
    """Gera e retorna o PDF oficial do atestado médico com QR Code para impressão ou download."""
    registro = MotorPrescricaoCFM.obter_documento(codigo)
    if not registro or not isinstance(registro["documento"], DocumentoAtestadoCFM):
        raise HTTPException(status_code=404, detail="Atestado médico não encontrado ou expirado.")

    doc: DocumentoAtestadoCFM = registro["documento"]
    base_url = str(request.base_url).rstrip("/")
    url_validacao = f"{base_url}/api/v1/prescricao/validar-html/{doc.codigo_validacao}"

    pdf_bytes = GeradorPDFMedicoCFM.gerar_pdf_atestado(doc, url_validacao)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=atestado_{codigo}.pdf",
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.get("/validar/{codigo}")
def consultar_documento_publico(codigo: str):
    """Endpoint JSON público para farmácias e pacientes validarem a autenticidade do documento."""
    dados = MotorPrescricaoCFM.validar_documento_publico(codigo)
    if not dados:
        raise HTTPException(status_code=404, detail="Documento médico não encontrado ou expirado no validador público.")
    return dados


@router.get("/validar-html/{codigo}", response_class=HTMLResponse)
def tela_validacao_publica_html(codigo: str, request: Request):
    """Página visual responsiva para conferência de autenticidade acessada via QR Code por farmácias e pacientes."""
    registro = MotorPrescricaoCFM.obter_documento(codigo)
    if not registro:
        return HTMLResponse(
            status_code=404,
            content=f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Documento Não Encontrado — Validador MedIA</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-slate-50 flex items-center justify-center min-h-screen p-4 font-sans">
                <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center border border-rose-100">
                    <div class="w-16 h-16 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold">✕</div>
                    <h1 class="text-xl font-bold text-slate-800 mb-2">Documento Não Localizado</h1>
                    <p class="text-xs text-slate-500 mb-4">O código informado <code class="bg-slate-100 px-2 py-1 rounded text-rose-600 font-mono">{codigo}</code> não foi encontrado ou foi revogado.</p>
                </div>
            </body>
            </html>
            """,
        )

    tipo_doc = registro["tipo_documento"]
    doc = registro["documento"]
    dados_publicos = registro["dados_consulta_farmacia"]
    base_url = str(request.base_url).rstrip("/")
    url_pdf = (
        f"{base_url}/api/v1/prescricao/atestado/{codigo}/pdf"
        if tipo_doc == "ATESTADO_MEDICO"
        else f"{base_url}/api/v1/prescricao/{codigo}/pdf"
    )

    titulo_doc = "Atestado Médico Digital" if tipo_doc == "ATESTADO_MEDICO" else "Prescrição Médica Eletrônica"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validação Oficial — {titulo_doc}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-slate-100 text-slate-800 min-h-screen flex flex-col justify-between antialiased">
    <header class="bg-[#0b1220] text-white py-4 px-6 shadow-md border-b border-slate-800">
        <div class="max-w-3xl mx-auto flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white text-sm">M</div>
                <div>
                    <h1 class="text-sm font-bold tracking-tight">MedIA Validador Oficial</h1>
                    <p class="text-[10px] text-slate-400">Resolução CFM nº 2.314/2022 • ICP-Brasil</p>
                </div>
            </div>
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <i class="fa-solid fa-circle-check text-[10px]"></i> Documento Autêntico
            </span>
        </div>
    </header>

    <main class="max-w-3xl mx-auto w-full p-4 sm:p-6 my-auto">
        <div class="bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden">
            <!-- Banner de Status -->
            <div class="bg-emerald-600 p-6 text-white text-center">
                <div class="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-3 backdrop-blur-sm border border-white/20">
                    <i class="fa-solid fa-certificate text-2xl text-white"></i>
                </div>
                <h2 class="text-xl font-extrabold tracking-tight">DOCUMENTO MÉDICO VÁLIDO E REGISTRADO</h2>
                <p class="text-xs text-emerald-100 mt-1">Assinatura eletrônica em conformidade com as exigências sanitárias e éticas.</p>
                <div class="mt-3 inline-block bg-black/20 px-3 py-1 rounded-lg font-mono text-xs font-semibold tracking-wider">
                    {codigo}
                </div>
            </div>

            <!-- Dados do Documento -->
            <div class="p-6 sm:p-8 space-y-6 text-xs sm:text-sm">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-6 border-b border-slate-100">
                    <div>
                        <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Médico Emissor</div>
                        <div class="font-bold text-slate-900 text-sm">{doc.medico_nome}</div>
                        <div class="text-slate-600">CRM-{doc.medico_uf} {doc.medico_crm}</div>
                    </div>
                    <div>
                        <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Paciente Beneficiário</div>
                        <div class="font-bold text-slate-900 text-sm">{doc.paciente_nome}</div>
                        <div class="text-slate-600 font-mono">CPF: {dados_publicos.get('paciente_cpf_mascarado', doc.paciente_cpf)}</div>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-6 border-b border-slate-100">
                    <div>
                        <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Tipo de Documento</div>
                        <div class="font-semibold text-slate-800">{titulo_doc}</div>
                    </div>
                    <div>
                        <div class="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">Data e Hora de Registro</div>
                        <div class="font-mono text-slate-700">{doc.data_emissao}</div>
                    </div>
                </div>

                <!-- Hash Criptográfico -->
                <div class="bg-slate-50 p-4 rounded-2xl border border-slate-200">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">Hash SHA-256 de Integridade</div>
                    <div class="font-mono text-[11px] text-slate-700 break-all">{doc.hash_integridade_sha256}</div>
                </div>

                <!-- Botões de Ação -->
                <div class="flex flex-col sm:flex-row items-center gap-3 pt-2">
                    <a href="{url_pdf}" target="_blank" class="w-full sm:w-auto flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl text-center shadow-lg shadow-blue-500/20 transition flex items-center justify-center gap-2">
                        <i class="fa-solid fa-file-pdf"></i>
                        <span>Visualizar / Baixar PDF Oficial</span>
                    </a>
                    <button onclick="window.print()" class="w-full sm:w-auto px-5 py-3 border border-slate-300 hover:bg-slate-50 font-semibold text-slate-700 rounded-xl transition flex items-center justify-center gap-2">
                        <i class="fa-solid fa-print"></i>
                        <span>Imprimir Comprovante</span>
                    </button>
                </div>
            </div>
        </div>
    </main>

    <footer class="bg-white border-t border-slate-200 text-center py-4 text-xs text-slate-400">
        MedIA Practice OS • Validador de Documentos Médicos CFM nº 2.314/2022 • LGPD Art. 11
    </footer>
</body>
</html>
"""
    return HTMLResponse(content=html)
