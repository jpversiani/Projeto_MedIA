"""Serviço de Mensageria Preventiva - Lembretes e Alertas Preventivos."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.mensageria import MensagemPreventiva, AlertaBuscaAtiva
from app.schemas.mensageria import MensagemPreventivaSchema, AlertaBuscaAtivaSchema


class MensageriaPreventivaService:
    """Serviço responsável pela geração de lembretes automáticos e identificação de buscas ativas."""

    # Constantes de identificação SUS/APS
    CIAP2_VACINAS_ATRASADAS = "A96"
    CID10_VACINAS_ATRASADAS = "Z23"
    CIAP2_DIABETES = "T90"
    CID10_DIABETES = "E11.9"
    PRIORIDADE_ALTA = "ALTA"
    PRIORIDADE_MEDIA = "MEDIA"
    PRIORIDADE_BAISA = "BAIXA"

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------------------
    # Geração de lembretes automáticos para teleconsultas agendadas
    # ---------------------------------------------------------------------------

    def gerar_lembretes_teleconsulta(self, patient_id: int, days_ahead: int = 7) -> List[MensagemPreventiva]:
        """
        Gera lembretes automáticos para teleconsultas agendadas.

        Args:
            patient_id: ID do paciente.
            days_ahead: Dias antes da consulta para enviar o lembrete.

        Returns:
            Lista de mensagens de lembrete a serem enviadas via WhatsApp/SMS.
        """
        # Consulta teleconsultas agendadas para o paciente
        teleconsultas = self.db.query(
            MensagemPreventiva,
            MensagemPreventiva.teleconsulta_id,
            MensagemPreventiva.data_hora_inicio,
            MensagemPreventiva.status,
        ).filter(
            MensagemPreventiva.paciente_id == patient_id,
            MensagemPreventiva.teleconsulta_id.isnot(None),
            MensagemPreventiva.status.in_(["AGENDADA", "CONFIRMADA"]),
        ).order_by(MensagemPreventiva.data_hora_inicio.desc()).all()

        lembretes = []
        for tc in teleconsultas:
            # Calcula o horário do lembrete (2 dias antes da consulta)
            hora_consulta = tc.data_hora_inicio
            if hora_consulta is None:
                continue

            # Lembrete enviado 2 dias antes da consulta
            dia_lembrete = hora_consulta - timedelta(days=2)
            # Garante que não seja após o horário da consulta
            if dia_lembrete >= hora_consulta:
                dia_lembrete -= timedelta(days=1)

            # Verifica se já existe um lembrete pendente
            existing = self.db.query(MensagemPreventiva)
            existing = existing.filter(
                MensagemPreventiva.paciente_id == patient_id,
                MensagemPreventiva.teleconsulta_id == tc.id,
                MensagemPreventiva.status.in_(["PENDENTE"]),
            ).first()

            if existing and existing.status == "PENDENTE":
                # Já existe, atualiza status
                existing.status = "ENVIADO"
                existing.texto = self._criar_texto_lembrete(tc, dia_lembrete)
                existing.enviado_em = datetime.now(timezone.utc)
            elif existing and existing.status == "ENVIADO":
                # Já foi enviado, ignora
                continue
            else:
                # Cria novo lembrete
                lembrate = MensagemPreventiva(
                    paciente_id=patient_id,
                    teleconsulta_id=tc.id,
                    canal="WHATSAPP",
                    telefone=tc.teleconsela_telefone or "",
                    nome_destinatario=tc.nome_completo or "",
                    cns=tc.cns,
                    cpf=tc.cpf,
                    tipo_alerta=self.CIAP2_VACINAS_ATRASADAS,
                    texto=self._criar_texto_lembrete(tc, dia_lembrete),
                    status="PENDENTE",
                )
                self.db.add(lembrate)

        return lembretes

    def _criar_texto_lembrete(self, teleconsulta, dia_lembrete: datetime) -> str:
        """Cria o texto do lembrete de teleconsulta."""
        hoje = datetime.now(timezone.utc)
        descricao = (
            f"Lembrete: Sua teleconsulta está agendada para {dia_lembrete.strftime('%d/%m/%Y')} "
            f"às {dia_lembrete.strftime('%H:%M')} ({teleconsulta.data_hora_inicio.strftime('%H:%M')})"
        )
        return descricao

    # ---------------------------------------------------------------------------
    # Identificador de busca ativa para crianças com vacinas atrasadas
    # e diabéticos sem acompanhamento há mais de 90 dias
    # ---------------------------------------------------------------------------

    def identificar_vacinas_atrasadas(self, patient_id: int) -> List[dict]:
        """
        Identifica pacientes com vacinas atrasadas (CIAP-2 A96 / CID-10 Z23).

        Args:
            patient_id: ID do paciente.

        Returns:
            Lista de dicionários com informações sobre vacinas atrasadas.
        """
        # Consulta vacinas com status de aplicação anterior
        vacinas = self.db.query(
            MensagemPreventiva,
            MensagemPreventiva.vacinacao_id,
            MensagemPreventiva.teleconsulta_id,
            MensagemPreventiva.texto,
            MensagemPreventiva.status,
        ).filter(
            MensagemPreventiva.paciente_id == patient_id,
            MensagemPreventiva.teleconsulta_id.isnot(None),
            MensagemPreventiva.status.in_(["PENDENTE", "ENVIADO"]),
        ).all()

        atrasadas = []
        for item in vacinas:
            # Verifica se a vacina é para vacinação (CIAP-2 A96) ou COVID-19 (CID-10 Z23)
            if item.texto and item.texto.lower().startswith(self.CIAP2_VACINAS_ATRASADAS):
                atrasadas.append({
                    "id": item.id,
                    "vacina": item.texto.split(" ")[0] if item.texto else None,
                    "paciente_id": item.paciente_id,
                    "data_alerta": datetime.now(timezone.utc).isoformat(),
                    "descricao": item.texto,
                })

        return atrasadas

    def identificar_diabetes_sem_acompanhamento(self, patient_id: int) -> List[dict]:
        """
        Identifica diabéticos sem acompanhamento há mais de 90 dias.

        Args:
            patient_id: ID do paciente.

        Returns:
            Lista de dicionários com informações sobre diabéticos sem acompanhamento.
        """
        # Consulta atendimentos com foco em diabéticos (CIAP-2 T90 / CID-10 E11.9)
        atendimentos = self.db.query(
            AtendimentoSOAP,
            AtendimentoSOAP.profissional_id,
            AtendimentoSOAP.data_hora_inicio,
        ).filter(
            AtendimentoSOAP.profissional_id.isnot(None),
            AtendimentoSOAP.subjetivo_motivo.like("%diabetes%", case_sensitive=False),
        ).all()

        sem_acompanhamento = []
        for at in atendimentos:
            # Verifica se há mais de 90 dias desde o último contato
            if at.data_hora_inicio:
                dias_since = (datetime.now(timezone.utc) - at.data_hora_inicio).days
                if dias_since > 90:
                    sem_acompanhamento.append({
                        "id": at.id,
                        "profissional_id": at.profissional_id,
                        "data_ultimo_contato": at.data_hora_inicio.isoformat(),
                        "descricao": f"Diabético sem acompanhamento há {dias_since} dias",
                    })

        return sem_acompanhamento

    def gerar_alertas_ativas(self, patient_id: int) -> List[AlertaBuscaAtiva]:
        """
        Gera alertas de busca ativa para pacientes com vacinas atrasadas ou diabéticos sem acompanhamento.

        Args:
            patient_id: ID do paciente.

        Returns:
            Lista de alertas de busca ativa.
        """
        vacinas_atrasadas = self.identificar_vacinas_atrasadas(patient_id)
        diabetes_sem_acompanhamento = self.identificar_diabetes_sem_acompanhamento(patient_id)

        alertas = []

        # Adiciona alerta para vacinas atrasadas
        for vac in vacinas_atrasadas:
            alerta = AlertaBuscaAtiva(
                id=vac["id"],
                paciente_id=patient_id,
                tipo=self.CIAP2_VACINAS_ATRASADAS,
                prioridade=self.PRIORIDADE_ALTA,
                descricao=f"Vacina atrasada: {vac['descricao']}",
                detalhe=vac["vacina"],
                resolvido_em=None,
            )
            alertas.append(alerta)

        # Adiciona alerta para diabéticos sem acompanhamento
        for diag in diabetes_sem_acompanhamento:
            alerta = AlertaBuscaAtiva(
                id=diag["id"],
                paciente_id=patient_id,
                tipo=self.CIAP2_DIABETES,
                prioridade=self.PRIORIDADE_ALTA,
                descricao=f"Diabético sem acompanhamento há mais de 90 dias",
                detalhe=diag["descricao"],
                resolvido_em=None,
            )
            alertas.append(alerta)

        return alertas

    def gerar_alertas_compostas(self, patients: List[int]) -> List[AlertaBuscaAtiva]:
        """
        Gera alertas compostos para múltiplos pacientes.

        Args:
            patients: Lista de IDs de pacientes.

        Returns:
            Lista de alertas de busca ativa.
        """
        alertas = []
        for pid in patients:
            alertas.extend(self.gerar_alertas_ativas(pid))
        return alertas


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def criar_texto_lembrete(teleconsulta, dia_lembrete: datetime) -> str:
    """Cria o texto do lembrete de teleconsulta."""
    hoje = datetime.now(timezone.utc)
    descricao = (
        f"Lembrete: Sua teleconsulta está agendada para {dia_lembrete.strftime('%d/%m/%Y')} "
        f"às {dia_lembrete.strftime('%H:%M')} ({teleconsulta.data_hora_inicio.strftime('%H:%M')})"
    )
    return descricao
