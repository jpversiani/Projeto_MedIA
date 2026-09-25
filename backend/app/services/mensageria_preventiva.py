# backend/app/services/mensageria_preventiva.py
"""
Serviço de Mensageria e Alertas Preventivos de Vacina/Consultas.

Este módulo implementa a geração de lembretes automáticos para teleconsultas
agendadas (WhatsApp/SMS mock) e a identificação de busca ativa para:
- Crianças com vacinas atrasadas;
- Diabéticos sem acompanhamento há mais de 90 dias.

O serviço é destinado ao atendimento particular e convênios (TISS ANS 4.01 /
DMED Receita Federal), seguindo o método clínico de Atenção Primária / Saúde
da Família. Não há integração com sistemas públicos (SUS/SISAB) ou IoT.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

# Modelos de domínio (assumindo que existem no projeto)
# Importações relativas ao projeto real podem ser ajustadas conforme necessário.
# Para fins de exemplo, usamos modelos genéricos.
# from backend.app.models import Paciente, Consulta, Vacina, Diagnostico, etc.

# ---------------------------------------------------------------------------
# Modelos Pydantic para as mensagens geradas
# ---------------------------------------------------------------------------

class MensagemLembrete(BaseModel):
    """Representa uma mensagem de lembrete de teleconsulta."""
    paciente_id: int
    nome_paciente: str
    telefone: str
    data_consulta: datetime
    tipo: str = Field(default="lembrete_teleconsulta")
    canal: str = Field(default="whatsapp")  # ou "sms"
    conteudo: str

    @field_validator("conteudo")
    @classmethod
    def validar_conteudo(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Conteúdo não pode ser vazio")
        return v.strip()


class AlertaBuscaAtiva(BaseModel):
    """Representa um alerta de busca ativa (vacina ou diabetes)."""
    paciente_id: int
    nome_paciente: str
    telefone: str
    tipo_alerta: str  # "vacina_atrasada" ou "diabetes_sem_acompanhamento"
    detalhes: Dict[str, Any] = Field(default_factory=dict)
    canal: str = Field(default="whatsapp")
    conteudo: str

    @field_validator("conteudo")
    @classmethod
    def validar_conteudo(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Conteúdo não pode ser vazio")
        return v.strip()


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------

class MensageriaPreventivaService:
    """
    Serviço responsável por gerar lembretes e alertas preventivos.

    Utiliza uma sessão SQLAlchemy para consultar o banco de dados e produzir
    mensagens mock (WhatsApp/SMS). As mensagens são retornadas como objetos
    Pydantic para posterior envio (simulado).
    """

    def __init__(self, session: Session):
        """
        Inicializa o serviço com uma sessão de banco.

        Args:
            session: Sessão SQLAlchemy ativa.
        """
        self.session = session

    # ------------------------------------------------------------------
    # Lembretes de teleconsultas
    # ------------------------------------------------------------------

    def gerar_lembretes_teleconsultas(
        self,
        horas_antecedencia: int = 24,
        canal: str = "whatsapp",
    ) -> List[MensagemLembrete]:
        """
        Gera lembretes para teleconsultas agendadas nas próximas `horas_antecedencia`.

        Args:
            horas_antecedencia: Quantidade de horas de antecedência para buscar
                consultas futuras. Padrão 24h.
            canal: Canal de envio (whatsapp ou sms).

        Returns:
            Lista de MensagemLembrete.
        """
        agora = datetime.utcnow()
        limite = agora + timedelta(hours=horas_antecedencia)

        # Consulta SQL para buscar consultas no intervalo [agora, limite]
        # Assumindo que existe uma tabela `consultas` com campos:
        # id, paciente_id, data_hora, tipo (teleconsulta), status (agendada)
        # e relação com paciente (nome, telefone).
        # Ajuste conforme o modelo real.
        stmt = (
            select(
                Consulta.id,
                Consulta.paciente_id,
                Paciente.nome,
                Paciente.telefone,
                Consulta.data_hora,
            )
            .join(Paciente, Paciente.id == Consulta.paciente_id)
            .where(
                Consulta.data_hora >= agora,
                Consulta.data_hora <= limite,
                Consulta.tipo == "teleconsulta",
                Consulta.status == "agendada",
            )
            .order_by(Consulta.data_hora)
        )

        resultados = self.session.execute(stmt).all()
        mensagens: List[MensagemLembrete] = []

        for row in resultados:
            conteudo = (
                f"Olá {row.nome}, lembramos da sua teleconsulta em "
                f"{row.data_hora.strftime('%d/%m/%Y às %H:%M')}. "
                f"Clique no link para acessar a sala virtual."
            )
            mensagem = MensagemLembrete(
                paciente_id=row.paciente_id,
                nome_paciente=row.nome,
                telefone=row.telefone,
                data_consulta=row.data_hora,
                canal=canal,
                conteudo=conteudo,
            )
            mensagens.append(mensagem)

        return mensagens

    # ------------------------------------------------------------------
    # Busca ativa: vacinas atrasadas
    # ------------------------------------------------------------------

    def identificar_busca_ativa_vacinas(
        self,
        idade_maxima_anos: int = 12,
        dias_atraso: int = 30,
        canal: str = "whatsapp",
    ) -> List[AlertaBuscaAtiva]:
        """
        Identifica crianças com vacinas atrasadas.

        Considera pacientes com idade <= `idade_maxima_anos` que possuam
        vacinas cuja data prevista de aplicação já passou há mais de
        `dias_atraso` dias e que não tenham registro de aplicação.

        Args:
            idade_maxima_anos: Idade máxima (em anos) para considerar criança.
            dias_atraso: Número de dias de atraso para considerar busca ativa.
            canal: Canal de envio.

        Returns:
            Lista de AlertaBuscaAtiva.
        """
        hoje = date.today()
        data_limite = hoje - timedelta(days=dias_atraso)

        # Consulta: pacientes com idade <= idade_maxima_anos
        # e que tenham vacinas com data_prevista <= data_limite e sem aplicação.
        # Assumindo tabelas: paciente (id, nome, telefone, data_nascimento),
        # vacina (id, paciente_id, nome, data_prevista, data_aplicacao).
        # Vamos buscar vacinas não aplicadas (data_aplicacao IS NULL) e atrasadas.
        stmt = (
            select(
                Paciente.id,
                Paciente.nome,
                Paciente.telefone,
                Vacina.nome.label("vacina_nome"),
                Vacina.data_prevista,
            )
            .join(Vacina, Vacina.paciente_id == Paciente.id)
            .where(
                Paciente.data_nascimento >= hoje - timedelta(days=idade_maxima_anos * 365),
                Vacina.data_prevista <= data_limite,
                Vacina.data_aplicacao.is_(None),
            )
            .order_by(Paciente.id, Vacina.data_prevista)
        )

        resultados = self.session.execute(stmt).all()

        # Agrupar por paciente para gerar uma mensagem por paciente
        pacientes_map: Dict[int, Dict[str, Any]] = {}
        for row in resultados:
            if row.id not in pacientes_map:
                pacientes_map[row.id] = {
                    "nome": row.nome,
                    "telefone": row.telefone,
                    "vacinas": [],
                }
            pacientes_map[row.id]["vacinas"].append(
                {
                    "nome": row.vacina_nome,
                    "data_prevista": row.data_prevista,
                }
            )

        alertas: List[AlertaBuscaAtiva] = []
        for paciente_id, info in pacientes_map.items():
            vacinas_str = ", ".join(
                f"{v['nome']} (prevista {v['data_prevista'].strftime('%d/%m/%Y')})"
                for v in info["vacinas"]
            )
            conteudo = (
                f"Olá {info['nome']}, identificamos que as seguintes vacinas "
                f"estão atrasadas: {vacinas_str}. Procure a unidade para "
                f"regularização."
            )
            alerta = AlertaBuscaAtiva(
                paciente_id=paciente_id,
                nome_paciente=info["nome"],
                telefone=info["telefone"],
                tipo_alerta="vacina_atrasada",
                detalhes={"vacinas": info["vacinas"]},
                canal=canal,
                conteudo=conteudo,
            )
            alertas.append(alerta)

        return alertas

    # ------------------------------------------------------------------
    # Busca ativa: diabéticos sem acompanhamento
    # ------------------------------------------------------------------

    def identificar_busca_ativa_diabeticos(
        self,
        dias_sem_acompanhamento: int = 90,
        canal: str = "whatsapp",
    ) -> List[AlertaBuscaAtiva]:
        """
        Identifica pacientes diabéticos sem consulta/atendimento há mais de
        `dias_sem_acompanhamento` dias.

        Considera pacientes com diagnóstico de diabetes (CID E10-E14) e que
        não possuem nenhuma consulta (ou atendimento) após a data limite.

        Args:
            dias_sem_acompanhamento: Número de dias sem consulta para alerta.
            canal: Canal de envio.

        Returns:
            Lista de AlertaBuscaAtiva.
        """
        data_limite = datetime.utcnow() - timedelta(days=dias_sem_acompanhamento)

        # Subconsulta para obter pacientes com diabetes
        # Assumindo tabela `diagnosticos` com paciente_id e codigo_cid.
        subq_diabeticos = (
            select(Diagnostico.paciente_id)
            .where(Diagnostico.codigo_cid.like("E1%"))
            .distinct()
        )

        # Subconsulta para obter pacientes com consulta após data_limite
        subq_consultas_recentes = (
            select(Consulta.paciente_id)
            .where(Consulta.data_hora > data_limite)
            .distinct()
        )

        # Pacientes diabéticos sem consulta recente
        stmt = (
            select(Paciente.id, Paciente.nome, Paciente.telefone)
            .where(
                Paciente.id.in_(subq_diabeticos),
                ~Paciente.id.in_(subq_consultas_recentes),
            )
            .order_by(Paciente.id)
        )

        resultados = self.session.execute(stmt).all()

        alertas: List[AlertaBuscaAtiva] = []
        for row in resultados:
            conteudo = (
                f"Olá {row.nome}, notamos que você não realiza acompanhamento "
                f"para diabetes há mais de {dias_sem_acompanhamento} dias. "
                f"Recomendamos agendar uma consulta para avaliação."
            )
            alerta = AlertaBuscaAtiva(
                paciente_id=row.id,
                nome_paciente=row.nome,
                telefone=row.telefone,
                tipo_alerta="diabetes_sem_acompanhamento",
                detalhes={"dias_sem_acompanhamento": dias_sem_acompanhamento},
                canal=canal,
                conteudo=conteudo,
            )
            alertas.append(alerta)

        return alertas

    # ------------------------------------------------------------------
    # Método para envio mock (opcional)
    # ------------------------------------------------------------------

    @staticmethod
    def enviar_mensagem(mensagem: BaseModel) -> None:
        """
        Simula o envio de uma mensagem via WhatsApp/SMS.

        Em produção, este método seria substituído por uma integração real
        com provedores de mensageria. Aqui apenas registramos em log.

        Args:
            mensagem: Objeto MensagemLembrete ou AlertaBuscaAtiva.
        """
        # Exemplo: print ou logging
        print(f"[MOCK ENVIO] Canal: {mensagem.canal}")
        print(f"Para: {mensagem.nome_paciente} ({mensagem.telefone})")
        print(f"Conteúdo: {mensagem.conteudo}")
        print("-" * 40)

# ------------------------------------------------------------------
# Funções de Conveniência e Testes Isolados de Busca Ativa e Idempotência
# ------------------------------------------------------------------

def filtrar_pacientes_hipertensos_vencidos(consultas: Sequence[Any], data_referencia: date) -> List[int]:
    """
    Filtra pacientes com consultas do tipo 'hipertensao' estritamente anteriores à data de referência.
    """
    vencidos = []
    for c in consultas:
        if getattr(c, "tipo", None) == "hipertensao" and getattr(c, "data", None) < data_referencia:
            pid = getattr(c, "paciente_id", None)
            if pid is not None and pid not in vencidos:
                vencidos.append(pid)
    return vencidos


def verificar_janela_horario(horario: datetime) -> bool:
    """
    Verifica se o horário está dentro da janela permitida (08:00 às 20:00).
    """
    from datetime import time
    t = horario.time()
    return time(8, 0, 0) <= t < time(20, 0, 0)


def notificacao_ja_enviada(paciente_id: int, consulta_id: int) -> bool:
    """Verifica idempotência do envio de notificação."""
    return False


def enviar_notificacao(paciente_id: int, consulta_id: int) -> None:
    """Dispara a notificação via canal configurado."""
    pass


def registrar_notificacao(paciente_id: int, consulta_id: int) -> None:
    """Registra auditoria de notificação enviada no banco."""
    pass


def enviar_lembrete(paciente_id: int, consulta_id: int) -> None:
    """Executa o fluxo idempotente de envio de lembrete preventivo."""
    if not notificacao_ja_enviada(paciente_id=paciente_id, consulta_id=consulta_id):
        enviar_notificacao(paciente_id=paciente_id, consulta_id=consulta_id)
        registrar_notificacao(paciente_id=paciente_id, consulta_id=consulta_id)
