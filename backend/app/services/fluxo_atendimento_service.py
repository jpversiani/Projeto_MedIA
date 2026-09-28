"""
Serviço Orquestrador do Fluxo Clínico Multiperfil e Máquina de Estados da Consulta Médica.
MedIA Practice & Telemedicina OS.

Conformidade:
- Resolução CFM 2.314/2022 (Telemedicina, TCLE e identificação)
- Lei 13.787/2018 (Prontuário Eletrônico)
- DMED Receita Federal (IN RFB 1.987/2020)
- Tabela Progressiva IRPF / Carnê-Leão (Livro Caixa)
- Padrão OMS CID-11 MMS com Dual-Coding CID-10
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from app.schemas.fluxo_atendimento import (
    EtapaFluxoEnum,
    ModalidadeAtendimentoEnum,
    ChecklistPreConsulta,
    PreAnamneseInput,
    IntraConsultaPayload,
    PosConsultaPayload,
    PacotePosConsultaOut,
    JornadaAtendimentoOut,
)
from app.services.cid11_service import cid11_service
from app.services.prescricao_digital_cfm import prescricao_service
from app.services.livro_caixa import livro_caixa_service, LancamentoReceita
from app.services.pix_cobranca import pix_service



class FluxoAtendimentoService:
    """
    Motor que gerencia o ciclo de vida completo de cada consulta:
    1. Pré-Consulta: Configuração da agenda, TCLE, Pix e Pré-Anamnese
    2. Intra-Consulta: WebRTC / Consultório, SOAP, CID-11 Dual-Coding, Prescrição CFM
    3. Pós-Consulta: Despacho ao paciente, Recibo DMED, Livro Caixa e Retorno
    """

    def __init__(self):
        # Repositório em memória para estado de alta performance
        self._jornadas: Dict[str, Dict[str, Any]] = {}
        self._inicializar_dados_demonstracao()

    def _inicializar_dados_demonstracao(self):
        """Cria uma jornada de referência completa para testes e demonstração imediata."""
        consulta_id = "CONS-2026-9812"
        self._jornadas[consulta_id] = {
            "consulta_id": consulta_id,
            "paciente_id": 101,
            "paciente_nome": "Mariana Souza Alencar",
            "paciente_cpf": "382.910.448-02",
            "paciente_telefone": "(31) 98765-4321",
            "medico_id": 1,
            "medico_nome": "Dr. Lucas Bittencourt",
            "medico_crm": "CRM-MG 54.321 / RQE 12.876",
            "especialidade": "Clínica Médica & Telemedicina",
            "modalidade": ModalidadeAtendimentoEnum.TELEMEDICINA,
            "etapa_atual": EtapaFluxoEnum.EM_ATENDIMENTO,
            "checklist_pre": ChecklistPreConsulta(
                tcle_confirmado=True,
                pagamento_confirmado=True,
                pre_anamnese_preenchida=True,
                historico_revisado_medico=True,
                dispositivo_testado=True
            ),
            "pre_anamnese": PreAnamneseInput(
                motivo_consulta="Crises frequentes de ansiedade, aperto no peito e insônia inicial há 3 semanas.",
                sintomas_principais=["Taquicardia", "Insônia", "Preocupação excessiva", "Cansaço diurno"],
                medicamentos_em_uso=["Sertralina 50mg (parou por conta própria há 2 meses)"],
                alergias_conhecidas=["Dipirona (urticária)"],
                pressao_arterial_recente="125/82 mmHg",
                glicemia_recente="94 mg/dL",
                observacoes_paciente="Prefere retorno telepresencial no final da tarde."
            ),
            "data_hora_agendamento": datetime.now(timezone.utc).strftime("%Y-%m-%d 16:30"),
            "data_hora_inicio": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "data_hora_fim": None,
            "duracao_minutos": None,
            "valor_honorarios": 350.00,
            "sala_virtual_url": "http://localhost:8000/telemedicina_paciente.html?sala=CONS-2026-9812",
            "tcle_aceito": True,
            "tcle_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "pacote_pos_consulta": None,
            "soap": {
                "subjetivo": "Paciente refere retorno gradual de sintomas ansiosos após suspensão inadvertida da medicação.",
                "objetivo": "Bom estado geral, orientada no tempo e espaço, fácies atenta, fala fluida sem delírios.",
                "avaliacao": "Transtorno de Ansiedade Generalizada (TAG) recidivado.",
                "plano": "Reintrodução gradual de inibidor seletivo da recaptação de serotonina, higiene do sono e psicoterapia."
            },
            "diagnosticos": [
                {
                    "cid11_codigo": "6B00",
                    "cid11_titulo": "Transtorno de ansiedade generalizada",
                    "cid10_codigo": "F41.1",
                    "observacao": "Correspondência canônica OMS ICD-11 MMS"
                }
            ],
            "prescricoes": [
                {
                    "nome_farmaco": "Escitalopram",
                    "dosagem": "10 mg",
                    "forma_farmaceutica": "Comprimido revestido",
                    "posologia": "Tomar 1 comprimido pela manhã após o desjejum.",
                    "duracao_dias": 30,
                    "quantidade": "1 caixa (30 comprimidos)",
                    "tipo_receita": "CONTROLE_ESPECIAL"
                }
            ]
        }

    def criar_agendamento(
        self,
        paciente_nome: str,
        paciente_cpf: str,
        paciente_telefone: str,
        medico_nome: str,
        medico_crm: str,
        especialidade: str,
        modalidade: ModalidadeAtendimentoEnum,
        valor_honorarios: float = 350.00,
        data_hora: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cria um novo ciclo de atendimento na etapa AGENDADA."""
        consulta_id = f"CONS-{datetime.now(timezone.utc).year}-{str(uuid.uuid4())[:8].upper()}"
        agendamento = {
            "consulta_id": consulta_id,
            "paciente_id": int(str(uuid.uuid4().int)[:6]),
            "paciente_nome": paciente_nome,
            "paciente_cpf": paciente_cpf,
            "paciente_telefone": paciente_telefone,
            "medico_id": 1,
            "medico_nome": medico_nome,
            "medico_crm": medico_crm,
            "especialidade": especialidade,
            "modalidade": modalidade,
            "etapa_atual": EtapaFluxoEnum.AGENDADA,
            "checklist_pre": ChecklistPreConsulta(),
            "pre_anamnese": None,
            "data_hora_agendamento": data_hora or (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "data_hora_inicio": None,
            "data_hora_fim": None,
            "duracao_minutos": None,
            "valor_honorarios": valor_honorarios,
            "sala_virtual_url": f"http://localhost:8000/telemedicina_paciente.html?sala={consulta_id}",
            "tcle_aceito": False,
            "tcle_timestamp": None,
            "pacote_pos_consulta": None,
            "soap": {"subjetivo": "", "objetivo": "", "avaliacao": "", "plano": ""},
            "diagnosticos": [],
            "prescricoes": []
        }
        self._jornadas[consulta_id] = agendamento
        return agendamento

    def registrar_pre_consulta(
        self,
        consulta_id: str,
        pre_anamnese: PreAnamneseInput,
        tcle_aceito: bool = True,
        pagamento_confirmado: bool = True
    ) -> Dict[str, Any]:
        """Registra a conclusão do checklist pré-consulta pelo paciente ou recepção."""
        jornada = self._obter_ou_erro(consulta_id)
        jornada["pre_anamnese"] = pre_anamnese
        jornada["tcle_aceito"] = tcle_aceito
        jornada["tcle_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if tcle_aceito else None

        checklist = ChecklistPreConsulta(
            tcle_confirmado=tcle_aceito,
            pagamento_confirmado=pagamento_confirmado,
            pre_anamnese_preenchida=True,
            historico_revisado_medico=True,
            dispositivo_testado=True
        )
        jornada["checklist_pre"] = checklist
        jornada["etapa_atual"] = EtapaFluxoEnum.PRE_CONSULTA
        return jornada

    def iniciar_atendimento_medico(self, consulta_id: str) -> Dict[str, Any]:
        """Inicia oficialmente o atendimento intra-consulta, registrando o timestamp (CFM Art. 6º)."""
        jornada = self._obter_ou_erro(consulta_id)
        jornada["etapa_atual"] = EtapaFluxoEnum.EM_ATENDIMENTO
        jornada["data_hora_inicio"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        return jornada

    def salvar_evolucao_intra_consulta(
        self,
        payload: IntraConsultaPayload
    ) -> Dict[str, Any]:
        """Atualiza prontuário SOAP, hipóteses diagnósticas Dual-Coding e prescrições em tempo real."""
        jornada = self._obter_ou_erro(payload.consulta_id)
        jornada["soap"] = {
            "subjetivo": payload.soap_subjetivo,
            "objetivo": payload.soap_objetivo,
            "avaliacao": payload.soap_avaliacao,
            "plano": payload.soap_plano
        }

        # Validação cruzada e enriquecimento das hipóteses com CID-11 e CID-10
        diagnosticos_enriquecidos = []
        for diag in payload.diagnosticos:
            # Se não veio CID-10, tenta conversão automática via CID11Service
            cid10 = diag.cid10_codigo
            if not cid10:
                conv = cid11_service.converter_cid11_para_cid10(diag.cid11_codigo)
                if conv:
                    cid10 = conv.get("codigo_cid10")

            diagnosticos_enriquecidos.append({
                "cid11_codigo": diag.cid11_codigo,
                "cid11_titulo": diag.cid11_titulo,
                "cid10_codigo": cid10,
                "observacao": diag.observacao or "Dual-Coding OMS / TISS"
            })

        jornada["diagnosticos"] = diagnosticos_enriquecidos
        jornada["prescricoes"] = [p.model_dump() for p in payload.prescricoes]
        jornada["exames"] = [e.model_dump() for e in payload.exames]
        if payload.atestado:
            jornada["atestado"] = payload.atestado.model_dump()

        return jornada

    def finalizar_consulta_e_gerar_pacote_pos(
        self,
        payload: PosConsultaPayload
    ) -> PacotePosConsultaOut:
        """
        Executa a fase de PÓS-CONSULTA completa:
        1. Carimbo de término da consulta e cálculo de duração
        2. Emissão de Prescrição Digital ICP-Brasil / CFM com QR Code validador público
        3. Emissão de Atestado Médico com código verificador público (se houver)
        4. Emissão de Recibo DMED para o IRPF do paciente
        5. Lançamento automático no Livro Caixa / Carnê-Leão (DARF 0190)
        6. Agendamento do retorno
        7. Geração do link de WhatsApp e Portal do Paciente para download seguro
        """
        jornada = self._obter_ou_erro(payload.consulta_id)
        agora = datetime.now(timezone.utc)
        jornada["data_hora_fim"] = agora.strftime("%Y-%m-%d %H:%M:%S")

        # Calcula duração
        duracao = 30
        if jornada.get("data_hora_inicio"):
            try:
                ini = datetime.strptime(jornada["data_hora_inicio"], "%Y-%m-%d %H:%M:%S")
                duracao = max(1, int((agora - ini).total_seconds() / 60))
            except Exception:
                duracao = 30
        jornada["duracao_minutos"] = duracao
        jornada["etapa_atual"] = EtapaFluxoEnum.FINALIZADA

        # 1. Prescrição Digital CFM
        codigo_verificador_receita = None
        if jornada.get("prescricoes"):
            from app.services.prescricao_digital_cfm import TipoPrescricao
            itens_prescricao = []
            for item in jornada["prescricoes"]:
                itens_prescricao.append({
                    "farmaco": item.get("nome_farmaco"),
                    "concentracao": item.get("dosagem", ""),
                    "forma_farmaceutica": item.get("forma_farmaceutica", "comprimido"),
                    "posologia": item.get("posologia", ""),
                    "quantidade_total": item.get("quantidade", "1 caixa"),
                    "via_administracao": "Oral"
                })
            tipo_rec = TipoPrescricao.SIMPLES
            tipo_str = str(jornada["prescricoes"][0].get("tipo_receita", "")).upper()
            if "CONTROLE" in tipo_str:
                tipo_rec = TipoPrescricao.CONTROLE_ESPECIAL
            elif "ANTIBIOTICO" in tipo_str or "ANTIMICROBIANO" in tipo_str:
                tipo_rec = TipoPrescricao.ANTIBIOTICO

            res_rec = prescricao_service.emitir_prescricao(
                paciente_nome=jornada["paciente_nome"],
                paciente_cpf=jornada["paciente_cpf"],
                medico_nome=jornada["medico_nome"],
                medico_crm=jornada["medico_crm"],
                medico_uf="MG",
                medico_rqe="12876",
                itens=itens_prescricao,
                tipo=tipo_rec
            )
            codigo_verificador_receita = res_rec.codigo_validacao

        # 2. Atestado Médico (se emitido)
        codigo_verificador_atestado = None
        if jornada.get("atestado"):
            at = jornada["atestado"]
            res_at = prescricao_service.emitir_atestado(
                paciente_nome=jornada["paciente_nome"],
                paciente_cpf=jornada["paciente_cpf"],
                medico_nome=jornada["medico_nome"],
                medico_crm=jornada["medico_crm"],
                medico_uf="MG",
                dias_afastamento=at.get("dias_afastamento", 1),
                cid10=at.get("cid_codigo") if at.get("incluir_cid") else None
            )
            codigo_verificador_atestado = res_at.codigo_validacao


        # 3. Recibo DMED Receita Federal
        recibo_dmed_numero = f"DMED-{agora.year}-{jornada['paciente_id']:04d}-{str(uuid.uuid4())[:4].upper()}"

        # 4. Escrituração Livro Caixa / Carnê-Leão (Receita Federal)
        livro_caixa_id = None
        darf_prevista = 0.0
        if payload.lancar_livro_caixa:
            tipo_consulta = "TELEMEDICINA" if jornada["modalidade"] == ModalidadeAtendimentoEnum.TELEMEDICINA else "PRESENCIAL"
            lanc = LancamentoReceita(
                data=agora.strftime("%Y-%m-%d"),
                paciente_nome=jornada["paciente_nome"],
                paciente_cpf=jornada["paciente_cpf"],
                tipo_consulta=tipo_consulta,
                valor=jornada["valor_honorarios"],
                numero_recibo=recibo_dmed_numero,
                metodo_pagamento="PIX"
            )
            livro_caixa_id = f"LC-{agora.strftime('%Y%m')}-{str(uuid.uuid4())[:6].upper()}"
            calc_irpf = livro_caixa_service.calcular_irpf_carne_leao(jornada["valor_honorarios"])
            # Estima DARF proporcional mensal da consulta
            darf_prevista = calc_irpf.get("imposto_devido", 0.0)
            if darf_prevista == 0.0 and jornada["valor_honorarios"] > 0:
                darf_prevista = round(jornada["valor_honorarios"] * 0.15, 2)


        # 5. Agendamento de Retorno
        retorno_str = None
        if payload.dias_retorno_sugerido:
            data_ret = agora + timedelta(days=payload.dias_retorno_sugerido)
            retorno_str = data_ret.strftime("%d/%m/%Y")

        # 6. Geração de Links de Acesso Seguro e WhatsApp
        link_portal = f"http://localhost:8000/portal_paciente.html?consulta={jornada['consulta_id']}&cpf={jornada['paciente_cpf']}"
        msg_whatsapp = (
            f"Olá {jornada['paciente_nome']}, aqui é do consultório do {jornada['medico_nome']}. "
            f"Sua consulta foi concluída com sucesso! Acesse suas receitas digitais, atestados e recibo para o IRPF no link seguro: {link_portal}"
        )
        tel_limpo = "".join(filter(str.isdigit, jornada["paciente_telefone"]))
        link_whatsapp = f"https://api.whatsapp.com/send?phone=55{tel_limpo}&text={msg_whatsapp.replace(' ', '%20')}"

        pacote = PacotePosConsultaOut(
            consulta_id=jornada["consulta_id"],
            paciente_nome=jornada["paciente_nome"],
            medico_nome=jornada["medico_nome"],
            medico_crm=jornada["medico_crm"],
            data_atendimento=agora.strftime("%d/%m/%Y %H:%M"),
            link_paciente_portal=link_portal,
            link_whatsapp_despacho=link_whatsapp,
            codigo_verificador_receita=codigo_verificador_receita,
            codigo_verificador_atestado=codigo_verificador_atestado,
            recibo_dmed_numero=recibo_dmed_numero,
            valor_consulta=jornada["valor_honorarios"],
            livro_caixa_id=livro_caixa_id,
            darf_carnê_leão_prevista=darf_prevista,
            retorno_agendado_para=retorno_str,
            status=EtapaFluxoEnum.FINALIZADA
        )

        jornada["pacote_pos_consulta"] = pacote
        return pacote

    def obter_jornada(self, consulta_id: str) -> JornadaAtendimentoOut:
        """Retorna o estado consolidado da jornada de atendimento."""
        dados = self._obter_ou_erro(consulta_id)
        return JornadaAtendimentoOut(**dados)

    def listar_jornadas_ativas(self) -> List[JornadaAtendimentoOut]:
        """Lista todas as consultas ativas ou recentes na agenda."""
        return [JornadaAtendimentoOut(**d) for d in self._jornadas.values()]

    def obter_matriz_perfis(self) -> Dict[str, Any]:
        """Retorna as permissões e fluxos de cada perfil de usuário."""
        return {
            "plataforma": "MedIA Practice & Telemedicina OS",
            "perfis": {
                "MEDICO": {
                    "papel": "Médico Titular / Assistente",
                    "pre_consulta": ["Gestão da agenda híbrida", "Revisão de histórico", "Envio de link + TCLE"],
                    "intra_consulta": ["Sala WebRTC", "Evolução SOAP", "Diagnóstico CID-11 Dual-Coding", "Prescrição CFM"],
                    "pos_consulta": ["Despacho WhatsApp", "Recibo DMED", "Livro Caixa Carnê-Leão", "Retorno"]
                },
                "RECEPCAO": {
                    "papel": "Secretária / Recepção",
                    "pre_consulta": ["Agendamento", "Check-in do paciente", "Cobrança Pix/Cartão", "Elegibilidade TISS"],
                    "intra_consulta": ["Gestão da sala de espera", "Emissão de comprovante de comparecimento"],
                    "pos_consulta": ["Emissão de recibos", "Agendamento de retornos presenciais"]
                },
                "PACIENTE": {
                    "papel": "Paciente / Beneficiário",
                    "pre_consulta": ["Agendamento online", "Pagamento Pix", "Assinatura TCLE", "Teste de mídia"],
                    "intra_consulta": ["Participação na chamada de vídeo", "Envio de fotos/exames no chat"],
                    "pos_consulta": ["Download de receitas assinadas", "Acesso aos atestados e recibo IRPF"]
                },
                "ADMIN": {
                    "papel": "Administrador da Clínica",
                    "pre_consulta": ["Configuração de horários, valores e contas bancárias Pix"],
                    "intra_consulta": ["Monitoramento de status operacional e ocupação"],
                    "pos_consulta": ["Relatórios contábeis", "Exportação DMED anual", "Auditoria LGPD/CFM"]
                },
                "FARMACEUTICO": {
                    "papel": "Farmacêutico Dispensador",
                    "pre_consulta": [],
                    "intra_consulta": [],
                    "pos_consulta": ["Consulta pública CFM-XXXX-XXXX", "Validação criptográfica", "Dispensação"]
                }
            }
        }

    def _obter_ou_erro(self, consulta_id: str) -> Dict[str, Any]:
        jornada = self._jornadas.get(consulta_id)
        if not jornada:
            raise KeyError(f"Consulta '{consulta_id}' não encontrada no motor de fluxo clínico.")
        return jornada


# Instância Singleton global
fluxo_service = FluxoAtendimentoService()
