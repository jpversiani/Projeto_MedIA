"""Motor de sugestões do Copiloto Clínico (C22) — Projeto MedIA.

Geração determinística (baseada em regras e protocolos SUS/APS) de:
  - Alertas de risco/alergia (piscantes no painel lateral do médico);
  - Rascunho SOAP (S·O·A·P) a partir do contexto do atendimento;
  - Exames complementares sugeridos por problema (CIAP-2/CID-10);
  - Dosagens usuais do SUS conforme RENAME 2022 / PCDT do Ministério da Saúde.

O motor é puro (sem I/O): recebe os objetos de domínio e devolve esquemas
Pydantic v2 estritos. A decisão clínica final é sempre do médico
(CFM Resolução 2.314/2022) — toda saída é marcada como sugestão.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Final, Iterable

from app.models.atendimento import AtendimentoSOAP
from app.models.cidadao import Cidadao
from app.schemas.copiloto import (
    AlertaClinicoOut,
    DosagemSUSOut,
    ExameComplementarOut,
    SeveridadeAlerta,
    SugestaoSOAPOut,
    TipoAlerta,
)

MODELO_CDS: Final[str] = "MedIA-CDS-1.0 (regras SUS/APS determinísticas)"
FONTE_MOTOR: Final[str] = "MedIA Copiloto CDS v1.0"

# ---------------------------------------------------------------------------
# Base de conhecimento SUS/APS (curada; por CID-10 com espelho CIAP-2)
# ---------------------------------------------------------------------------

# (cid10, ciap2, nome do problema) -> exames complementares usuais na APS
EXAMES_COMPLEMENTARES: Final[dict[str, tuple[ExameComplementarOut, ...]]] = {
    ("I10", "K86"): (
        ExameComplementarOut(
            id="ex-creatinina",
            nome="Creatinina sérica (TFG estimada)",
            justificativa="Avaliação de lesão de órgão-alvo renal na hipertensão (PCC/Ministério da Saúde).",
            cid10="I10",
            ciap2="K86",
        ),
        ExameComplementarOut(
            id="ex-potassio",
            nome="Potássio sérico",
            justificativa="Avaliação eletrolítica antes de IECA/BRA (PCC Hipertensão Arterial).",
            cid10="I10",
            ciap2="K86",
        ),
        ExameComplementarOut(
            id="ex-ecg",
            nome="ECG de repouso",
            justificativa="Rastreio de hipertrofia ventricular e arritmias (PCC Hipertensão Arterial).",
            cid10="I10",
            ciap2="K86",
        ),
        ExameComplementarOut(
            id="ex-glicemia-jejum",
            nome="Glicemia de jejum",
            justificativa="Rastreio de diabetes em hipertenso (Caderno de Atenção Básica 37).",
            cid10="I10",
            ciap2="K86",
        ),
    ),
    ("E11", "T90"): (
        ExameComplementarOut(
            id="ex-hba1c",
            nome="Hemoglobina glicada (HbA1c)",
            justificativa="Controle glicêmico trimestral no diabetes tipo 2 (PCC Diabetes).",
            prioridade="rotina",
            cid10="E11",
            ciap2="T90",
        ),
        ExameComplementarOut(
            id="ex-glicemia-jejum",
            nome="Glicemia de jejum",
            justificativa="Monitoramento capilar/laboratorial do diabetes (PCC Diabetes).",
            cid10="E11",
            ciap2="T90",
        ),
        ExameComplementarOut(
            id="ex-creatinina",
            nome="Creatinina sérica (TFG estimada)",
            justificativa="Rastreio anual de nefropatia diabética (PCC Diabetes).",
            cid10="E11",
            ciap2="T90",
        ),
        ExameComplementarOut(
            id="ex-fundo-olho",
            nome="Fundo de olho (retinopatia)",
            justificativa="Rastreio anual de retinopatia diabética (PCC Diabetes).",
            cid10="E11",
            ciap2="T90",
        ),
    ),
    ("J45", "R96"): (
        ExameComplementarOut(
            id="ex-espirometria",
            nome="Espirometria com prova broncodilatadora",
            justificativa="Confirmação do diagnóstico e controle da asma (PCDT Asma).",
            cid10="J45",
            ciap2="R96",
        ),
    ),
    ("E66", "T82"): (
        ExameComplementarOut(
            id="ex-hba1c",
            nome="Hemoglobina glicada (HbA1c)",
            justificativa="Rastreio de resistência insulínica na obesidade (Caderno AB 38).",
            cid10="E66",
            ciap2="T82",
        ),
        ExameComplementarOut(
            id="ex-lipidograma",
            nome="Lipidograma (colesterol total e frações)",
            justificativa="Estratificação de risco cardiovascular (Diretriz SBC).",
            cid10="E66",
            ciap2="T82",
        ),
    ),
}

# (cid10, ciap2, nome) -> dosagens usuais SUS (RENAME 2022 / PCDT)
DOSAGENS_SUS: Final[dict[str, tuple[DosagemSUSOut, ...]]] = {
    ("I10", "K86"): (
        DosagemSUSOut(
            id="dos-losartana",
            medicamento="Losartana (DCB 04736)",
            apresentacao="comprimido 50 mg",
            posologia="50 mg via oral, 1x ao dia, por tempo indeterminado (titular até 100 mg/dia)",
            cid10="I10",
            ciap2="K86",
            referencia="RENAME 2022 / PCC Hipertensão Arterial",
        ),
        DosagemSUSOut(
            id="dos-hidroclorotiazida",
            medicamento="Hidroclorotiazida (DCB 04052)",
            apresentacao="comprimido 25 mg",
            posologia="25 mg via oral, 1x ao dia, pela manhã",
            cid10="I10",
            ciap2="K86",
            referencia="RENAME 2022 / PCC Hipertensão Arterial",
        ),
    ),
    ("E11", "T90"): (
        DosagemSUSOut(
            id="dos-metformina",
            medicamento="Cloridrato de Metformina (DCB 03433)",
            apresentacao="comprimido 850 mg",
            posologia="850 mg via oral, 2x ao dia, junto às refeições",
            cid10="E11",
            ciap2="T90",
            referencia="RENAME 2022 / PCC Diabetes",
        ),
        DosagemSUSOut(
            id="dos-glibenclamida",
            medicamento="Glibenclamida (DCB 03333)",
            apresentacao="comprimido 5 mg",
            posologia="5 mg via oral, 1x ao dia, junto ao café da manhã",
            cid10="E11",
            ciap2="T90",
            referencia="RENAME 2022 / PCC Diabetes",
        ),
    ),
    ("J45", "R96"): (
        DosagemSUSOut(
            id="dos-salbutamol",
            medicamento="Salbutamol (DCB 05636)",
            apresentacao="aerossol 100 mcg/dose",
            posologia="100-200 mcg inalado, 8/8 h, se dispneia (resgate)",
            cid10="J45",
            ciap2="R96",
            referencia="RENAME 2022 / PCDT Asma",
        ),
        DosagemSUSOut(
            id="dos-budesonida",
            medicamento="Budesonida (DCB 02592)",
            apresentacao="aerossol 200 mcg/dose",
            posologia="200 mcg inalado, 2x ao dia (manutenção)",
            cid10="J45",
            ciap2="R96",
            referencia="RENAME 2022 / PCDT Asma",
        ),
    ),
}

# Palavras-chave de red flags clínicas no subjetivo/motivo (triagem assistencial)
RED_FLAGS: Final[tuple[tuple[tuple[str, ...], str, str], ...]] = (
    (
        ("dor torácica", "dor no peito", "opressão torácica"),
        "Dor torácica — suspeita de síndrome coronariana aguda",
        "Encaminhar imediatamente para emergência (SAMU 192); não manejável na APS.",
    ),
    (
        ("dispneia intensa", "falta de ar intensa", "cianose"),
        "Dispneia intensa — instabilidade respiratória",
        "Avaliar sinais vitais e encaminhar para emergência (SAMU 192).",
    ),
    (
        ("cefaleia súbita", "pior dor de cabeça", "convulsão"),
        "Sinal de alerta neurológico",
        "Encaminhar para emergência; investigar causa secundária.",
    ),
)

# Substâncias teratogênicas usuais (uso em gestantes — risco alto)
TERATOGENICOS: Final[frozenset[str]] = frozenset(
    {"ibuprofeno", "ácido acetilsalicílico", "aspirina", "captopril", "losartana", "enalapril", "estatina"}
)


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _id_estavel(*partes: str) -> str:
    """ID determinístico (hash SHA-256 curto) para deduplicar alertas no WS."""
    base = "|".join(partes)
    return f"alr-{hashlib.sha256(base.encode('utf-8')).hexdigest()[:16]}"


def _normalizar(texto: str) -> str:
    import re
    import unicodedata

    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(ch)
    )
    return re.sub(r"\s+", " ", sem_acento.strip().lower())


class MotorSugestoesCopiloto:
    """Motor determinístico de alertas e sugestões SUS/APS (C22)."""

    def gerar_alertas(
        self,
        atendimento: AtendimentoSOAP,
        cidadao: Cidadao,
        problemas: Iterable[tuple[str, str, str]],
    ) -> tuple[AlertaClinicoOut, ...]:
        alertas: list[AlertaClinicoOut] = []
        momento = _agora()

        # 1) ALERGIAS registradas no cadastro do cidadão (crítico — piscante)
        if cidadao.alergias:
            for item in cidadao.alergias.split(";"):
                substancia = item.strip()
                if not substancia:
                    continue
                alertas.append(
                    AlertaClinicoOut(
                        id=_id_estavel("alergia", str(cidadao.id), substancia),
                        tipo=TipoAlerta.ALERGIA,
                        severidade=SeveridadeAlerta.CRITICO,
                        titulo=f"ALERGIA: {substancia}",
                        descricao=(
                            f"Cidadão com alergia registrada a '{substancia}' (cadastro e-SUS APS). "
                            "Evitar prescrição de substância ou classe correlata."
                        ),
                        conduta_recomendada=(
                            "Não prescrever a substância/classe alergênica; revisar DCB de "
                            "qualquer medicamento sugerido antes do aceite."
                        ),
                        substancia=substancia,
                        fonte="Cadastro e-SUS APS (alergias autorreferidas)",
                        criado_em=momento,
                    )
                )

        # 2) GESTAÇÃO — risco de teratogenicidade (alto — piscante)
        if cidadao.gestante:
            alertas.append(
                AlertaClinicoOut(
                    id=_id_estavel("gestante", str(cidadao.id)),
                    tipo=TipoAlerta.RISCO,
                    severidade=SeveridadeAlerta.ALTO,
                    titulo="Gestante — risco teratogênico",
                    descricao=(
                        "Cidadão em gestação. IECA/BRA, AAS e AINEs são contraindicados "
                        "na gestação (MS/PCDT)."
                    ),
                    conduta_recomendada="Revisar farmacoterapia; preferir paracetamol como analgésico.",
                    fonte="PCC Saúde da Gestante / Ministério da Saúde",
                    criado_em=momento,
                )
            )

        # 3) CONDIÇÕES CRÔNICAS do cadastro e dos problemas ativos (moderado)
        condicoes_cadastro: tuple[tuple[bool, str, str], ...] = (
            (cidadao.hipertenso, "I10", "Hipertensão arterial"),
            (cidadao.diabetico, "E11", "Diabetes mellitus tipo 2"),
        )
        for ativa, cid10, titulo in condicoes_cadastro:
            if ativa:
                alertas.append(
                    AlertaClinicoOut(
                        id=_id_estavel("condicao", str(cidadao.id), cid10),
                        tipo=TipoAlerta.RISCO,
                        severidade=SeveridadeAlerta.MODERADO,
                        titulo=f"Condição crônica ativa: {titulo}",
                        descricao=(
                            f"Cidadão com {titulo.lower()} registrada no cadastro do e-SUS APS "
                            "(lista de problemas ativa)."
                        ),
                        conduta_recomendada="Avaliar adesão, PA/glicemia atuais e metas do PCC correspondente.",
                        cid10=cid10,
                        fonte="e-SUS APS (Lista de Problemas)",
                        criado_em=momento,
                    )
                )

        for tipo_codigo, codigo, descricao in problemas:
            if tipo_codigo != "CID10":
                continue
            alertas.append(
                AlertaClinicoOut(
                    id=_id_estavel("problema", str(atendimento.id), codigo),
                    tipo=TipoAlerta.RISCO,
                    severidade=SeveridadeAlerta.MODERADO,
                    titulo=f"Problema ativo: {descricao} (CID-10 {codigo})",
                    descricao=f"Condição ativa na lista de problemas do atendimento: {descricao}.",
                    conduta_recomendada="Correlacionar com a queixa atual e revisar plano terapêutico.",
                    cid10=codigo,
                    fonte="e-SUS APS (Lista de Problemas)",
                    criado_em=momento,
                )
            )

        # 4) RED FLAGS clínicas no motivo/subjetivo (crítico — piscante)
        texto_clinico = _normalizar(
            " ".join(filter(None, [atendimento.subjetivo_motivo, atendimento.subjetivo_notas]))
        )
        for palavras, titulo, conduta in RED_FLAGS:
            if any(palavra in texto_clinico for palavra in palavras):
                alertas.append(
                    AlertaClinicoOut(
                        id=_id_estavel("redflag", str(atendimento.id), titulo),
                        tipo=TipoAlerta.RED_FLAG_CLINICA,
                        severidade=SeveridadeAlerta.CRITICO,
                        titulo=titulo,
                        descricao=(
                            f"Termo de alerta identificado no relato ({', '.join(palavras[:2])}). "
                            "Requer decisão imediata sobre encaminhamento."
                        ),
                        conduta_recomendada=conduta,
                        fonte="Protocolo de triagem MedIA / Cadernos AB",
                        criado_em=momento,
                    )
                )

        # 5) TERATOGENICIDADE — interação contexto gestação × prescrição atual
        if cidadao.gestante and atendimento.plano_prescricoes:
            prescricao = _normalizar(atendimento.plano_prescricoes)
            for substancia in TERATOGENICOS:
                if substancia in prescricao:
                    alertas.append(
                        AlertaClinicoOut(
                            id=_id_estavel("terato", str(atendimento.id), substancia),
                            tipo=TipoAlerta.INTERACAO_MEDICAMENTOSA,
                            severidade=SeveridadeAlerta.CRITICO,
                            titulo=f"Interação: {substancia} em gestante",
                            descricao=(
                                f"Prescrição contém '{substancia}', medicamento "
                                "contraindicado na gestação."
                            ),
                            conduta_recomendada="Substituir por alternativa segura (ex.: paracetamol).",
                            substancia=substancia,
                            fonte="RENAME 2022 / PCC Saúde da Gestante",
                            criado_em=momento,
                        )
                    )

        # Deduplicação estável por id (alertas piscantes não se repetem)
        vistos: set[str] = set()
        alertas_unicos: list[AlertaClinicoOut] = []
        for alerta in alertas:
            if alerta.id not in vistos:
                vistos.add(alerta.id)
                alertas_unicos.append(alerta)
        return tuple(alertas_unicos)

    def sugerir_exames(self, problemas: Iterable[tuple[str, str, str]]) -> tuple[ExameComplementarOut, ...]:
        sugeridos: dict[str, ExameComplementarOut] = {}
        for tipo_codigo, codigo, _ in problemas:
            if tipo_codigo != "CID10":
                continue
            for chave, exames in EXAMES_COMPLEMENTARES.items():
                if chave[0] == codigo:
                    for exame in exames:
                        sugeridos.setdefault(exame.id, exame)
        return tuple(sugeridos.values())

    def sugerir_dosagens(self, problemas: Iterable[tuple[str, str, str]]) -> tuple[DosagemSUSOut, ...]:
        sugeridas: dict[str, DosagemSUSOut] = {}
        for tipo_codigo, codigo, _ in problemas:
            if tipo_codigo != "CID10":
                continue
            for chave, dosagens in DOSAGENS_SUS.items():
                if chave[0] == codigo:
                    for dosagem in dosagens:
                        sugeridas.setdefault(dosagem.id, dosagem)
        return tuple(sugeridas.values())

    def sugerir_soap(
        self,
        atendimento: AtendimentoSOAP,
        cidadao: Cidadao,
        problemas: Iterable[tuple[str, str, str]],
        exames: tuple[ExameComplementarOut, ...],
        dosagens: tuple[DosagemSUSOut, ...],
    ) -> SugestaoSOAPOut:
        nome = cidadao.nome_completo or "cidadão não identificado"
        cns = cidadao.cns or "CNS ausente (verificar CPF no cadastro)"

        subjetivo = (
            f"Cidadã(o) {nome} (CNS {cns}). Motivo do contato: "
            f"{atendimento.subjetivo_motivo or 'não informado'}."
        )
        if atendimento.subjetivo_notas:
            subjetivo += f" História atual: {atendimento.subjetivo_notas}"

        objetivo_parts: list[str] = []
        if atendimento.objetivo_exame_fisico:
            objetivo_parts.append(f"Exame físico: {atendimento.objetivo_exame_fisico}")
        if atendimento.objetivo_antropometria_sinais:
            objetivo_parts.append(f"Sinais vitais/antropometria: {atendimento.objetivo_antropometria_sinais}")
        objetivo = "; ".join(objetivo_parts) if objetivo_parts else "Sem sinais vitais/exame físico registrados no contexto."

        nomes_problemas = [descricao for _, _, descricao in problemas]
        cid_codes = sorted({codigo for tipo, codigo, _ in problemas if tipo == "CID10"})
        ciap_codes = sorted({codigo for tipo, codigo, _ in problemas if tipo == "CIAP2"})
        avaliacao = (
            f"Avaliação (SOAP-A): {'; '.join(nomes_problemas) if nomes_problemas else 'em definição pelo médico'}"
            + (f". CID-10: {', '.join(cid_codes)}" if cid_codes else "")
            + (f". CIAP-2: {', '.join(ciap_codes)}" if ciap_codes else "")
        )

        plano_parts: list[str] = []
        if exames:
            plano_parts.append(
                "Exames complementares sugeridos: "
                + "; ".join(f"{e.nome} ({e.prioridade})" for e in exames)
            )
        if dosagens:
            plano_parts.append(
                "Farmacoterapia usual SUS: " + "; ".join(f"{d.medicamento} — {d.posologia}" for d in dosagens)
            )
        plano_parts.append("Orientações não farmacológicas e retorno conforme PCC correspondente.")
        plano = " ".join(plano_parts)

        return SugestaoSOAPOut(
            subjetivo=subjetivo[:2000],
            objetivo=objetivo[:2000],
            avaliacao=avaliacao[:2000],
            plano=plano[:4000],
            cid10_sugerido=cid_codes[0] if cid_codes else None,
            ciap2_sugerido=ciap_codes[0] if ciap_codes else None,
            confianca=0.72,
            modelo=MODELO_CDS,
            gerado_em=_agora(),
        )


def id_evento_ws(atendimento_id: int, sequencia: int) -> str:
    """Identificador de evento WS (rastreabilidade de telemetria pseudonimizada)."""
    return f"ws-{uuid.uuid5(uuid.NAMESPACE_URL, f'copiloto/{atendimento_id}/{sequencia}')}"
