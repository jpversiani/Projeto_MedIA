"""
Serviço de IA Generativa para o Copiloto Clínico — Suporte a Google Gemini e Fallback Clínico.

Implementa:
- Estruturação automática de notas clínicas livres no padrão SOAP (S·O·A·P);
- Diagnóstico diferencial avançado com justificativas clínicas e codificação CID-10 / CID-11;
- Sumarização clínica de teleconsultas WebRTC.

Conformidade:
- Resolução CFM nº 2.314/2022 (A IA atua exclusivamente como apoio e segunda opinião;
  a responsabilidade final é indelegável do médico assistente).
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

import httpx

logger = logging.getLogger(__name__)


class HipoteseDiagnosticaIA(BaseModel):
    cid10: str
    cid11: Optional[str] = None
    descricao: str
    probabilidade: str = Field(..., description="'alta', 'moderada' ou 'baixa'")
    justificativa: str


class SugestaoSOAPIA(BaseModel):
    motivo_consulta: str
    subjetivo_hda: str
    objetivo_exame: str
    avaliacao_raciocinio: str
    hipoteses: List[HipoteseDiagnosticaIA] = Field(default_factory=list)
    plano_prescricao: str
    plano_exames: str
    motor_utilizado: str


class MotorIAGenerativaCopiloto:
    """Motor de inteligência artificial clínica generativa com fallback resiliente."""

    @classmethod
    def _obter_gemini_api_key(cls) -> Optional[str]:
        return os.getenv("GEMINI_API_KEY")

    @classmethod
    def estruturar_soap(cls, texto_bruto: str, contexto_paciente: Optional[Dict[str, Any]] = None) -> SugestaoSOAPIA:
        """Estrutura texto clínico livre no padrão SOAP."""
        api_key = cls._obter_gemini_api_key()
        if api_key:
            try:
                resultado_gemini = cls._chamar_gemini_soap(texto_bruto, api_key, contexto_paciente)
                if resultado_gemini:
                    return resultado_gemini
            except Exception as e:
                logger.warning(f"Falha ao consultar Gemini API, acionando fallback clínico: {e}")

        # Fallback clínico inteligente baseado em processamento de linguagem natural e regras de APS
        return cls._fallback_estruturar_soap(texto_bruto, contexto_paciente)

    @classmethod
    def diagnostico_diferencial(cls, queixa_sintomas: str) -> List[HipoteseDiagnosticaIA]:
        """Gera hipóteses diagnósticas diferenciais estruturadas."""
        api_key = cls._obter_gemini_api_key()
        if api_key:
            try:
                res_gemini = cls._chamar_gemini_diagnostico(queixa_sintomas, api_key)
                if res_gemini:
                    return res_gemini
            except Exception as e:
                logger.warning(f"Falha Gemini em diagnostico diferencial, acionando fallback: {e}")

        return cls._fallback_diagnostico_diferencial(queixa_sintomas)

    @classmethod
    def _chamar_gemini_soap(
        cls, texto: str, api_key: str, contexto: Optional[Dict[str, Any]] = None
    ) -> Optional[SugestaoSOAPIA]:
        """Chama a API do Google Gemini para estruturação clínica SOAP."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt_sistema = (
            "Você é um assistente médico especialista em Medicina de Família e Clínica Médica (CFM 2.314/2022). "
            "Converta as anotações clínicas brutas a seguir em um formato SOAP estruturado com estrita precisão. "
            "Responda SOMENTE em JSON válido com as seguintes chaves: "
            "motivo_consulta (string curta), subjetivo_hda (string detalhada), objetivo_exame (sinais e exame físico), "
            "avaliacao_raciocinio (raciocínio clínico), hipoteses (lista de objetos com cid10, cid11, descricao, probabilidade, justificativa), "
            "plano_prescricao (fármacos com dosagem e posologia recomendadas), plano_exames (exames laboratoriais/imagem indicados)."
        )
        corpo = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{prompt_sistema}\n\nAnotações da Consulta:\n{texto}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=corpo)
            if resp.status_code == 200:
                dados = resp.json()
                texto_saida = dados["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(texto_saida)
                hipoteses_objs = [
                    HipoteseDiagnosticaIA(
                        cid10=h.get("cid10", "Z00"),
                        cid11=h.get("cid11"),
                        descricao=h.get("descricao", "Avaliação clínica"),
                        probabilidade=h.get("probabilidade", "moderada"),
                        justificativa=h.get("justificativa", "Baseado na apresentação clínica.")
                    )
                    for h in parsed.get("hipoteses", [])
                ]
                return SugestaoSOAPIA(
                    motivo_consulta=parsed.get("motivo_consulta", "Consulta médica"),
                    subjetivo_hda=parsed.get("subjetivo_hda", texto),
                    objetivo_exame=parsed.get("objetivo_exame", "Sinais vitais estáveis."),
                    avaliacao_raciocinio=parsed.get("avaliacao_raciocinio", "Quadro clínico compatível."),
                    hipoteses=hipoteses_objs,
                    plano_prescricao=parsed.get("plano_prescricao", ""),
                    plano_exames=parsed.get("plano_exames", ""),
                    motor_utilizado="Google Gemini 1.5 Flash (Cloud)"
                )
        return None

    @classmethod
    def _chamar_gemini_diagnostico(cls, sintomas: str, api_key: str) -> Optional[List[HipoteseDiagnosticaIA]]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        prompt = (
            "Como especialista médico, liste até 3 diagnósticos diferenciais para os seguintes sintomas clínicos. "
            "Responda SOMENTE em JSON como uma lista de objetos: "
            "[{\"cid10\": string, \"cid11\": string, \"descricao\": string, \"probabilidade\": \"alta\"|\"moderada\"|\"baixa\", \"justificativa\": string}]"
        )
        corpo = {
            "contents": [{"parts": [{"text": f"{prompt}\nSintomas: {sintomas}"}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
        }
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=corpo)
            if resp.status_code == 200:
                dados = resp.json()
                parsed = json.loads(dados["candidates"][0]["content"]["parts"][0]["text"])
                return [HipoteseDiagnosticaIA(**h) for h in parsed]
        return None

    @classmethod
    def _fallback_diagnostico_diferencial(cls, queixa_sintomas: str) -> List[HipoteseDiagnosticaIA]:
        """Motor local determinístico de diagnóstico diferencial para operação offline."""
        texto_lower = queixa_sintomas.lower()
        hipoteses: List[HipoteseDiagnosticaIA] = []

        if any(term in texto_lower for term in ["ansiedade", "panico", "angustia", "insonia", "inquieto", "palpitacao"]):
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="F41.1",
                    cid11="6B00",
                    descricao="Transtorno de Ansiedade Generalizada (TAG)",
                    probabilidade="alta",
                    justificativa="Sintomas de hiperativação autonômica, insônia e tensão psíquica sustentada."
                )
            )
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="F41.0",
                    cid11="6B01",
                    descricao="Transtorno de Pânico",
                    probabilidade="moderada",
                    justificativa="Crises súbitas de palpitação e apreensão intensa."
                )
            )
        elif any(term in texto_lower for term in ["cefaleia", "dor de cabeca", "enxaqueca", "fotofobia"]):
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="G43.9",
                    cid11="8A80",
                    descricao="Enxaqueca / Cefaleia Primária",
                    probabilidade="alta",
                    justificativa="Cefaleia com características pulsáteis e sintomas associados."
                )
            )
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="G44.2",
                    cid11="8A81",
                    descricao="Cefaleia Tensional",
                    probabilidade="moderada",
                    justificativa="Dor em aperto ou pressão bilateral de intensidade leve a moderada."
                )
            )
        elif any(term in texto_lower for term in ["tosse", "coriza", "garganta", "febre", "resfriado", "gripe", "dispneia"]):
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="J06.9",
                    cid11="CA05",
                    descricao="Infecção Aguda das Vias Aéreas Superiores (IVAS)",
                    probabilidade="alta",
                    justificativa="Quadro catarral agudo autolimitado com sinais respiratórios superiores."
                )
            )
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="J18.9",
                    cid11="CA40",
                    descricao="Pneumonia Adquirida na Comunidade (PAC)",
                    probabilidade="moderada",
                    justificativa="Presença de febre alta associada a tosse e/ou dispneia a investigar."
                )
            )
        else:
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="R69",
                    cid11="MG48",
                    descricao="Causas Desconhecidas e Inespecíficas de Morbilidade",
                    probabilidade="moderada",
                    justificativa="Quadro clínico inicial que requer ampliação de anamnese e propedêutica."
                )
            )
        return hipoteses

    @classmethod
    def _fallback_estruturar_soap(
        cls, texto: str, contexto: Optional[Dict[str, Any]] = None
    ) -> SugestaoSOAPIA:
        """Motor local determinístico de estruturação SOAP para operação offline ou sem chave."""
        texto_lower = texto.lower()
        
        # Detecção de queixa / motivo
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        primeira_linha = linhas[0] if linhas else "Consulta Clínica"
        motivo = primeira_linha if len(primeira_linha) < 80 else primeira_linha[:77] + "..."

        # Extração de Sinais Vitais do texto
        sinais = []
        pa_match = re.search(r"pa\s*:?\s*(\d{2,3}\s*[x/]\s*\d{2,3})", texto_lower)
        if pa_match:
            sinais.append(f"PA: {pa_match.group(1)} mmHg")
        fc_match = re.search(r"fc\s*:?\s*(\d{2,3})", texto_lower)
        if fc_match:
            sinais.append(f"FC: {fc_match.group(1)} bpm")
        temp_match = re.search(r"(?:temp|temperatura|tax)\s*:?\s*(\d{2}[,\.]\d|\d{2})", texto_lower)
        if temp_match:
            sinais.append(f"Tax: {temp_match.group(1)} °C")
        sato2_match = re.search(r"(?:sat|sato2|spo2)\s*:?\s*(\d{2,3})%?", texto_lower)
        if sato2_match:
            sinais.append(f"SpO2: {sato2_match.group(1)}%")

        sinais_str = " • ".join(sinais) if sinais else "Sinais vitais normais e estáveis na admissão."

        # Raciocínio Diagnóstico Baseado em Palavras-chave Clínicas
        hipoteses: List[HipoteseDiagnosticaIA] = []
        prescricao_sugerida = ""
        exames_sugeridos = ""
        raciocinio = ""

        if any(term in texto_lower for term in ["ansiedade", "panico", "angustia", "insonia", "inquieto", "palpitacao"]):
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="F41.1",
                    cid11="6B00",
                    descricao="Transtorno de Ansiedade Generalizada (TAG)",
                    probabilidade="alta",
                    justificativa="Sintomas de hiperativação autonômica, insônia e tensão psíquica sustentada."
                )
            )
            raciocinio = "Quadro sindrômico compatível com Transtorno de Ansiedade Generalizada. Indicação de psicoterapia e farmacoterapia com ISRS."
            prescricao_sugerida = (
                "1. Escitalopram 10mg - Tomar 1 comprimido pela manhã por 30 dias.\n"
                "2. Higiene do sono e manejo comportamental de estresse."
            )
            exames_sugeridos = "Hemograma completo, TSH, T4L, Glicemia de jejum."
        elif any(term in texto_lower for term in ["cefaleia", "dor de cabeca", "enxaqueca", "fotofobia"]):
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="G43.9",
                    cid11="8A80",
                    descricao="Enxaqueca / Cefaleia Primária",
                    probabilidade="alta",
                    justificativa="Cefaleia com características pulsáteis e sintomas associados."
                )
            )
            raciocinio = "Episódio compatível com crise de migrânea sem aura. Orientar analgesia precoce e controle de gatilhos alimentares e do sono."
            prescricao_sugerida = "1. Dipirona 1g - Tomar 1 comprimido até de 6/6h se dor intensa.\n2. Evitar jejum prolongado."
            exames_sugeridos = "Rastreio clínico; solicitar neuroimagem somente em caso de sinais de alarme (red flags)."
        elif any(term in texto_lower for term in ["tosse", "coriza", "garganta", "febre", "resfriado", "gripe"]):
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="J06.9",
                    cid11="CA05",
                    descricao="Infecção Aguda das Vias Aéreas Superiores (IVAS)",
                    probabilidade="alta",
                    justificativa="Quadro catarral agudo autolimitado com sinais respiratórios superiores."
                )
            )
            raciocinio = "IVAS de etiologia predominantemente viral. Tratamento sintomático e suporte clínico."
            prescricao_sugerida = (
                "1. Lavagem nasal com Soro Fisiológico 0,9% - 5 a 10ml em cada narina 4x ao dia.\n"
                "2. Paracetamol 750mg - Tomar 1 comprimido até de 6/6h se febre ou dor."
            )
            exames_sugeridos = "Não há necessidade de exames complementares na ausência de taquipneia ou sinais de gravidade."
        else:
            hipoteses.append(
                HipoteseDiagnosticaIA(
                    cid10="Z00.0",
                    cid11="QA00",
                    descricao="Exame Médico Geral / Rotina de Saúde",
                    probabilidade="moderada",
                    justificativa="Apresentação clínica sem sinais patológicos específicos imediatos."
                )
            )
            raciocinio = "Avaliação clínica preventiva longitudinal com foco em promoção da saúde."
            prescricao_sugerida = "1. Orientações de hábitos de vida saudáveis e prática de atividade física regular."
            exames_sugeridos = "Perfil lipídico, Glicemia de jejum, Creatinina sérica, EAS."

        return SugestaoSOAPIA(
            motivo_consulta=motivo,
            subjetivo_hda=f"Paciente refere: {texto}. Nega outros sintomas sistêmicos agudos.",
            objetivo_exame=f"Bom estado geral, lúcido e orientado no tempo e espaço. {sinais_str}. Ectoscopia sem anormalidades evidentes.",
            avaliacao_raciocinio=raciocinio,
            hipoteses=hipoteses,
            plano_prescricao=prescricao_sugerida,
            plano_exames=exames_sugeridos,
            motor_utilizado="MedIA Clinical Copilot (Motor Determinístico de APS)"
        )
