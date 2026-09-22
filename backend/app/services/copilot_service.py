import os
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.cidadao import Cidadao
from app.schemas.copilot import CopilotSOAPRequest, CopilotSOAPResponse
from app.schemas.atendimento import ProblemaCreate

def processar_copilot_soap(req: CopilotSOAPRequest, db: Optional[Session] = None) -> CopilotSOAPResponse:
    """
    Processa a transcrição ou anotação livre da consulta e gera a estrutura SOAP
    com sugestão de CIAP-2 / CID-10 e validação de segurança médica.
    """
    texto = req.relato_clinico.lower()
    cidadao = None
    alertas: List[str] = []
    problemas: List[ProblemaCreate] = []

    if db and req.cidadao_id:
        cidadao = db.query(Cidadao).filter(Cidadao.id == req.cidadao_id).first()
        if cidadao and cidadao.alergias:
            alertas.append(f"Atenção: Paciente possui alergia documentada a: {cidadao.alergias}.")

    # 1. Análise de Queixa e Diagnósticos Prováveis
    motivo = "Consulta de rotina / avaliação clínica"
    notas_subjetivo = req.relato_clinico
    achados_exame = "Paciente em bom estado geral, orientado, vigil, corado e hidratado."
    avaliacao = "Quadro clínico a esclarecer."
    conduta = "Orientações gerais, hidratação e retorno conforme evolução."
    prescricao = ""
    exames = ""

    # Padrão: Hipertensão / Crise Hipertensiva
    if any(k in texto for k in ["hipertens", "pressao", "has", "cefal", "nuca", "dor de cabeca"]):
        motivo = "Cefaleia / Acompanhamento de Pressão Arterial"
        achados_exame += f" ACV: Bulhas rítmicas e normofonéticas em 2 tempos, sem sopros. PA aferida: {req.pressao_aferida or 'Verificada em acolhimento'}."
        avaliacao = "Hipertensão arterial sistêmica descompensada / Sintomas cefalálgicos associados."
        conduta = "Retorno em 15 dias para reavaliação dos níveis pressóricos. Orientado a manter dieta hipossódica e atividade física moderada."
        prescricao = "1. Losartana Potássica 50mg - 1 comprimido VO pela manhã (Uso contínuo)\n2. Dipirona 500mg - 1 comprimido VO de 6/6h se dor intensa (se não houver contraindicação)"
        exames = "Eletrocardiograma (ECG), Glicemia de jejum, Perfil lipídico, Creatinina, EAS"
        
        problemas.append(ProblemaCreate(tipo_codigo="CIAP2", codigo="K86", descricao="Hipertensão arterial sem complicações", situacao="ATIVO"))
        problemas.append(ProblemaCreate(tipo_codigo="CID10", codigo="I10", descricao="Hipertensão essencial (primária)", situacao="ATIVO"))

    # Padrão: Infecção Respiratória / Tosse / Garganta
    elif any(k in texto for k in ["tosse", "garganta", "febre", "coriza", "resfriado", "gripe"]):
        motivo = "Sintomas respiratórios / Queixa de tosse e odinofagia"
        achados_exame += " Oroscopia com hiperemia leve de orofaringe, sem placas purulentas. AP: Murmúrio vesicular presente bilateralmente, sem ruídos adventícios."
        avaliacao = "Infecção aguda de vias aéreas superiores (IVAS) de provável etiologia viral."
        conduta = "Repouso, hidratação vigorosa, lavagem nasal frequente com soro fisiológico 0,9%. Sinais de alerta orientados."
        prescricao = "1. Paracetamol 750mg - 1 comprimido VO de 8/8h em caso de dor ou febre (por até 5 dias)\n2. Soro Fisiológico 0,9% - Instilar 5ml em cada narina várias vezes ao dia"
        
        problemas.append(ProblemaCreate(tipo_codigo="CIAP2", codigo="R74", descricao="Infecção aguda das vias aéreas superiores (IVAS)", situacao="ATIVO"))
        problemas.append(ProblemaCreate(tipo_codigo="CID10", codigo="J00", descricao="Nasofaringite aguda [resfriado comum]", situacao="ATIVO"))

    # Padrão: Diabetes / Glicemia
    elif any(k in texto for k in ["glicemia", "diabet", "sede", "urina"]):
        motivo = "Acompanhamento de Diabetes Mellitus"
        avaliacao = "Diabetes Mellitus em acompanhamento na Atenção Primária."
        conduta = "Ajuste dietético, controle glicêmico domiciliar. Retorno em 30 dias com exames."
        prescricao = "1. Metformina 850mg - 1 comprimido VO após o almoço e jantar"
        exames = "Hemoglobina Glicada (HbA1c), Glicemia em jejum, Microalbuminúria, Creatinina"

        problemas.append(ProblemaCreate(tipo_codigo="CIAP2", codigo="T90", descricao="Diabetes não insulino-dependente", situacao="ATIVO"))
        problemas.append(ProblemaCreate(tipo_codigo="CID10", codigo="E11", descricao="Diabetes mellitus não-insulino-dependente", situacao="ATIVO"))

    # Checagem de segurança de alergia na prescrição gerada
    if cidadao and cidadao.alergias and prescricao:
        alergias_paciente = cidadao.alergias.lower()
        if "dipirona" in alergias_paciente and "dipirona" in prescricao.lower():
            alertas.append("BLOQUEIO DE SEGURANÇA: Dipirona foi removida da prescrição devido a histórico de alergia do paciente!")
            prescricao = prescricao.replace("2. Dipirona 500mg - 1 comprimido VO de 6/6h se dor intensa (se não houver contraindicação)", "2. Paracetamol 750mg - 1 comprimido VO de 8/8h se dor (substituído por alergia)")

    return CopilotSOAPResponse(
        subjetivo_motivo=motivo,
        subjetivo_notas=notas_subjetivo,
        objetivo_exame_fisico=achados_exame,
        avaliacao_notas=avaliacao,
        plano_conduta=conduta,
        plano_prescricoes=prescricao,
        plano_exames=exames,
        problemas_sugeridos=problemas,
        alertas_seguranca=alertas
    )
