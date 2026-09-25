# backend/tests/test_mensageria_preventiva.py

"""
Testes das regras de busca ativa e prevenção de spam clínico (C16).

Cobrem:
1. Filtro de pacientes com consultas de hipertensão vencidas.
2. Respeito à janela de tolerância de horário para envio de lembretes.
3. Idempotência no disparo de notificações.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

import pytest

# Importações das funções de negócio (implementadas em backend/app/services/mensageria_preventiva.py)
from backend.app.services.mensageria_preventiva import (
    filtrar_pacientes_hipertensos_vencidos,
    verificar_janela_horario,
    enviar_lembrete,
)


# ------------------------------------------------------------------------------
# Mocks de domínio (substituem os modelos ORM para testes isolados)
# ------------------------------------------------------------------------------

@dataclass
class MockConsulta:
    id: int
    paciente_id: int
    tipo: str
    data: date
    horario: time = time(9, 0)


@dataclass
class MockPaciente:
    id: int
    nome: str
    consultas: list[MockConsulta] = None

    def __post_init__(self):
        if self.consultas is None:
            self.consultas = []


# ------------------------------------------------------------------------------
# Testes do filtro de pacientes hipertensos com consultas vencidas
# ------------------------------------------------------------------------------

class TestFiltroPacientesHipertensosVencidos:
    """Regra de busca ativa: apenas pacientes com consulta de hipertensão vencida."""
    def test_filtra_somente_consultas_hipertensao_vencidas(self):
        hoje = date(2025, 3, 15)

        consultas = [
            MockConsulta(id=1, paciente_id=101, tipo="hipertensao", data=hoje - timedelta(days=2)),
            MockConsulta(id=2, paciente_id=102, tipo="hipertensao", data=hoje + timedelta(days=1)),
            MockConsulta(id=3, paciente_id=103, tipo="diabetes", data=hoje - timedelta(days=2)),
            MockConsulta(id=4, paciente_id=104, tipo="hipertensao", data=hoje),
        ]

        resultado = filtrar_pacientes_hipertensos_vencidos(consultas, data_referencia=hoje)

        assert resultado == [101]

    def test_retorna_lista_vazia_se_nenhum_vencido(self):
        hoje = date(2025, 3, 15)

        consultas = [
            MockConsulta(id=5, paciente_id=201, tipo="hipertensao", data=hoje + timedelta(days=1)),
            MockConsulta(id=6, paciente_id=202, tipo="outro", data=hoje - timedelta(days=1)),
        ]

        resultado = filtrar_pacientes_hipertensos_vencidos(consultas, data_referencia=hoje)

        assert resultado == []

    def test_ignora_consultas_do_mesmo_dia(self):
        hoje = date(2025, 3, 15)

        consultas = [
            MockConsulta(id=7, paciente_id=301, tipo="hipertensao", data=hoje),
        ]

        resultado = filtrar_pacientes_hipertensos_vencidos(consultas, data_referencia=hoje)

        assert resultado == []


# ------------------------------------------------------------------------------
# Testes da janela de tolerância de horário
# ------------------------------------------------------------------------------

class TestJanelaToleranciaHorario:
    @pytest.mark.parametrize("horario", [
        datetime(2025, 3, 15, 8, 0, 0),
        datetime(2025, 3, 15, 12, 30, 0),
        datetime(2025, 3, 15, 19, 59, 59),
    ])
    def test_dentro_da_janela(self, horario):
        assert verificar_janela_horario(horario) is True

    @pytest.mark.parametrize("horario", [
        datetime(2025, 3, 15, 0, 0, 0),
        datetime(2025, 3, 15, 7, 59, 59),
        datetime(2025, 3, 15, 20, 0, 0),
        datetime(2025, 3, 15, 23, 59, 59),
    ])
    def test_fora_da_janela(self, horario):
        assert verificar_janela_horario(horario) is False


# ------------------------------------------------------------------------------
# Testes de idempotência no envio de notificações
# ------------------------------------------------------------------------------

class TestIdempotenciaNotificacoes:
    def test_envio_duplicado_nao_gera_duas_notificacoes(self):
        paciente_id = 42
        consulta_id = 77

        # Simula comportamento interno: na primeira chamada não existe notificação,
        # na segunda já existe (porque foi registrada).
        with patch(
            "backend.app.services.mensageria_preventiva.notificacao_ja_enviada"
        ) as mock_ja_enviada, patch(
            "backend.app.services.mensageria_preventiva.enviar_notificacao"
        ) as mock_sender, patch(
            "backend.app.services.mensageria_preventiva.registrar_notificacao"
        ) as mock_registra:

            mock_ja_enviada.side_effect = [False, True]

            enviar_lembrete(paciente_id=paciente_id, consulta_id=consulta_id)
            enviar_lembrete(paciente_id=paciente_id, consulta_id=consulta_id)

            # O canal de envio deve ser chamado exatamente uma vez
            mock_sender.assert_called_once_with(paciente_id=paciente_id, consulta_id=consulta_id)
            # O registro também deve ocorrer apenas uma vez
            mock_registra.assert_called_once_with(paciente_id=paciente_id, consulta_id=consulta_id)

    def test_sem_envio_quando_notificacao_ja_existe(self):
        paciente_id = 10
        consulta_id = 20

        with patch(
            "backend.app.services.mensageria_preventiva.notificacao_ja_enviada"
        ) as mock_ja_enviada, patch(
            "backend.app.services.mensageria_preventiva.enviar_notificacao"
        ) as mock_sender, patch(
            "backend.app.services.mensageria_preventiva.registrar_notificacao"
        ) as mock_registra:

            mock_ja_enviada.return_value = True

            enviar_lembrete(paciente_id=paciente_id, consulta_id=consulta_id)

            mock_sender.assert_not_called()
            mock_registra.assert_not_called()
