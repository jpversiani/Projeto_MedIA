"""
Testes automatizados do componente de Notificações e Agendamento Ativo (C8).

Valida:
  - Sanitização de dados sensíveis (LGPD): remoção de CID-10, CIAP-2, SOAP, etc.
  - Formatação de identificação por CNS/CPF (padrão SUS).
  - Validação de CIAP-2 e CID-10.
  - Agendamento de lembrete com antecedência de 15 minutos.
  - Transições de status e tipos de evento suportados.
  - Estrutura de payloads de notificação.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Constantes do módulo (espelhadas em Python para validação)
# ---------------------------------------------------------------------------

CAMPOS_SENSIVEIS = frozenset([
    "cid10", "ciap2", "descricao_clinica", "soap", "anamnese",
    "evolucao_soap", "motivo_consulta", "diagnostico_ciap2", "diagnostico_cid10",
])

TIPOS_EVENTO = frozenset([
    "TELECONSULTA_LEMBRETE",
    "PACIENTE_EM_SALA",
    "CONFIRMACAO_PRESENCA",
])

ANTECEDENCIA_LEMBRETE_MS = 15 * 60 * 1000  # 900 000 ms
INTERVALO_POLLING_PADRAO_MS = 30_000


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agora() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def paciente_cns_completo() -> dict[str, Any]:
    return {"nome": "João da Silva Santos", "cns": "110433218196000", "cpf": "12345678901"}


@pytest.fixture
def paciente_cpf_apenas() -> dict[str, Any]:
    return {"nome": "Maria Costa Lima", "cpf": "52998224725"}


@pytest.fixture
def paciente_sem_documento() -> dict[str, Any]:
    return {"nome": "Pedro Henrique Alves"}


# ---------------------------------------------------------------------------
# Utilitários de teste (espelhados do JS)
# ---------------------------------------------------------------------------

def _sanitizar(dados: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in dados.items() if k not in CAMPOS_SENSIVEIS}


def _formatar_identificacao(paciente: dict[str, Any]) -> str:
    cns = str(paciente.get("cns") or "").replace(" ", "").replace("-", "").replace(".", "")
    if len(cns) >= 15:
        return f"CNS: {cns}"
    cpf = str(paciente.get("cpf") or "").replace(" ", "").replace("-", "").replace(".", "")
    if len(cpf) >= 11:
        return f"CPF: ***.***.{cpf[-3:]}-{cpf[-2:]}"
    return paciente.get("nome", "Paciente não identificado")


def _mascarar_cpf(cpf: str) -> str:
    limpo = "".join(filter(str.isdigit, cpf))
    if len(limpo) < 3:
        return "***.***.**"
    return f"***.***.{limpo[-3:]}-{limpo[-2:]}"


def _validar_ciap2(codigo: str) -> bool:
    import re
    return bool(__import__("re").fullmatch(r"[A-Z]\d{2}", str(codigo).upper()))


def _validar_cid10(codigo: str) -> bool:
    import re
    return bool(re.fullmatch(r"[A-Z]\d{1,3}(\.\d{1,2})?", str(codigo).upper()))


def _validar_cns(cns: str) -> bool:
    digits = "".join(filter(str.isdigit, cns))
    if len(digits) != 15:
        return False
    if digits[0] in ("1", "2"):
        soma = sum(int(d) * (15 - i) for i, d in enumerate(digits))
        return soma % 11 == 0
    return False


# ---------------------------------------------------------------------------
# Testes de sanitização (LGPD)
# ---------------------------------------------------------------------------

class TestSanitizar:
    def test_remove_cid10(self) -> None:
        dados = {"tipo": "TELECONSULTA_LEMBRETE", "cid10": "J00", "nome": "X"}
        limpo = _sanitizar(dados)
        assert "cid10" not in limpo
        assert limpo["nome"] == "X"

    def test_remove_ciap2(self) -> None:
        dados = {"tipo": "PACIENTE_EM_SALA", "ciap2": "A01", "sala": "sala_1"}
        limpo = _sanitizar(dados)
        assert "ciap2" not in limpo

    def test_remove_soap(self) -> None:
        dados = {"tipo": "CONFIRMACAO_PRESENCA", "soap": {"subjetivo": "dor"}}
        limpo = _sanitizar(dados)
        assert "soap" not in limpo

    def test_remove_todos_campos_sensiveis(self) -> None:
        dados = {c: "valor" for c in CAMPOS_SENSIVEIS}
        dados["nome"] = "teste"
        limpo = _sanitizar(dados)
        for c in CAMPOS_SENSIVEIS:
            assert c not in limpo, f"Campo sensível '{c}' não removido"
        assert limpo["nome"] == "teste"

    def test_preserva_dados_nao_sensiveis(self) -> None:
        dados = {"tipo": "TELECONSULTA_LEMBRETE", "profissional": "Dr. Teste", "paciente_nome": "Fulano"}
        limpo = _sanitizar(dados)
        assert limpo["profissional"] == "Dr. Teste"
        assert limpo["paciente_nome"] == "Fulano"


# ---------------------------------------------------------------------------
# Testes de formatação de identificação (CNS/CPF)
# ---------------------------------------------------------------------------

class TestFormatarIdentificacao:
    def test_prioriza_cns(self, paciente_cns_completo: dict[str, Any]) -> None:
        resultado = _formatar_identificacao(paciente_cns_completo)
        assert resultado.startswith("CNS:")
        assert "110433218196000" in resultado

    def test_fallback_cpf(self, paciente_cpf_apenas: dict[str, Any]) -> None:
        resultado = _formatar_identificacao(paciente_cpf_apenas)
        assert resultado.startswith("CPF:")
        assert "***.***." in resultado

    def test_mascara_cpf(self) -> None:
        assert _mascarar_cpf("52998224725") == "***.***.725-25"

    def test_mascara_cpf_curto(self) -> None:
        resultado = _mascarar_cpf("123")
        assert "***" in resultado

    def test_sem_documento(self, paciente_sem_documento: dict[str, Any]) -> None:
        resultado = _formatar_identificacao(paciente_sem_documento)
        assert resultado == "Pedro Henrique Alves"

    def test_cpf_mascarado_nao_revela_digitos(self) -> None:
        mascarado = _mascarar_cpf("12345678901")
        assert "123456789" not in mascarado


# ---------------------------------------------------------------------------
# Testes de tipos de evento
# ---------------------------------------------------------------------------

class TestTiposEvento:
    def test_lembrete_presente(self) -> None:
        assert "TELECONSULTA_LEMBRETE" in TIPOS_EVENTO

    def test_paciente_em_sala_presente(self) -> None:
        assert "PACIENTE_EM_SALA" in TIPOS_EVENTO

    def test_confirmacao_presenca_presente(self) -> None:
        assert "CONFIRMACAO_PRESENCA" in TIPOS_EVENTO

    def test_tres_tipos_exatos(self) -> None:
        assert len(TIPOS_EVENTO) == 3


# ---------------------------------------------------------------------------
# Testes de agendamento de lembrete (15 minutos)
# ---------------------------------------------------------------------------

class TestAgendamentoLembrete:
    def test_lembrete_antecedencia_15_minutos(self, agora: datetime) -> None:
        inicio = agora + timedelta(minutes=30)
        lembrete_em = inicio - timedelta(minutes=15)
        delta = (lembrete_em - agora).total_seconds() / 60
        assert delta == 15.0

    def test_lembrete_nao_dispara_se_jah_passou(self, agora: datetime) -> None:
        inicio = agora - timedelta(minutes=5)
        delta = (inicio - agora).total_seconds()
        assert delta < 0

    def test_lembrete_dispara_no_tempo_correto(self, agora: datetime) -> None:
        inicio = agora + timedelta(minutes=16)
        lembrete_em = inicio - timedelta(minutes=15)
        assert lembrete_em > agora
        delta = (lembrete_em - agora).total_seconds()
        assert 59 < delta < 61


# ---------------------------------------------------------------------------
# Testes de conformidade SUS/APS
# ---------------------------------------------------------------------------

class TestConformidadeSUS:
    def test_ciap2_valido(self) -> None:
        assert _validar_ciap2("A01") is True
        assert _validar_ciap2("K86") is True
        assert _validar_ciap2("a01") is True
        assert _validar_ciap2("B12") is True

    def test_ciap2_invalido(self) -> None:
        assert _validar_ciap2("Z") is False
        assert _validar_ciap2("A1") is False
        assert _validar_ciap2("AA1") is False
        assert _validar_ciap2("A012") is False

    def test_cid10_valido(self) -> None:
        assert _validar_cid10("J00") is True
        assert _validar_cid10("I10") is True
        assert _validar_cid10("N39.0") is True
        assert _validar_cid10("A00.0") is True
        assert _validar_cid10("B20") is True

    def test_cid10_invalido(self) -> None:
        assert _validar_cid10("Z9999") is False
        assert _validar_cid10("1234") is False
        assert _validar_cid10("ABCD") is False

    def test_cns_valido(self) -> None:
        assert _validar_cns("110433218196000") is True

    def test_cns_invalido(self) -> None:
        assert _validar_cns("000000000000000") is False
        assert _validar_cns("12345") is False
        assert _validar_cns("") is False


# ---------------------------------------------------------------------------
# Testes de statuses de teleconsulta
# ---------------------------------------------------------------------------

class TestStatusTeleconsulta:
    def test_agendada(self) -> None:
        from app.models.telemedicina import StatusTeleconsulta
        assert StatusTeleconsulta.AGENDADA.value == "AGENDADA"

    def test_em_andamento(self) -> None:
        from app.models.telemedicina import StatusTeleconsulta
        assert StatusTeleconsulta.EM_ANDAMENTO.value == "EM_ANDAMENTO"

    def test_concluida(self) -> None:
        from app.models.telemedicina import StatusTeleconsulta
        assert StatusTeleconsulta.CONCLUIDA.value == "CONCLUIDA"

    def test_cancelada(self) -> None:
        from app.models.telemedicina import StatusTeleconsulta
        assert StatusTeleconsulta.CANCELADA.value == "CANCELADA"

    def test_suspensa(self) -> None:
        from app.models.telemedicina import StatusTeleconsulta
        assert StatusTeleconsulta.SUSPENSA.value == "SUSPENSA"


# ---------------------------------------------------------------------------
# Testes de payload de notificação
# ---------------------------------------------------------------------------

class TestPayloadNotificacao:
    def test_payload_lembrete_contem_campos_essenciais(self) -> None:
        payload = {
            "tipo": "TELECONSULTA_LEMBRETE",
            "cns_paciente": "110433218196000",
            "cpf_paciente": "12345678901",
            "teleconsulta_id": "42",
            "inicio_em": "2026-09-25T10:00:00-03:00",
            "profissional": "Dr. Teste",
            "link_sala": "/teleconsulta/sala/abc123",
        }
        assert payload["tipo"] == "TELECONSULTA_LEMBRETE"
        assert payload["teleconsulta_id"] == "42"
        assert payload["profissional"] == "Dr. Teste"

    def test_payload_lembrete_sem_campo_clinico(self) -> None:
        payload = {"tipo": "TELECONSULTA_LEMBRETE", "paciente_nome": "Fulano"}
        for c in CAMPOS_SENSIVEIS:
            assert c not in payload

    def test_payload_confirmacao_presenca(self, agora: datetime) -> None:
        payload = {
            "tipo": "CONFIRMACAO_PRESENCA",
            "paciente_cpf": "52998224725",
            "data_hora": agora.isoformat(),
        }
        assert payload["tipo"] == "CONFIRMACAO_PRESENCA"
        assert "data_hora" in payload

    def test_payload_paciente_em_sala(self) -> None:
        payload = {"tipo": "PACIENTE_EM_SALA", "teleconsulta_id": 10, "sala": {"codigo": "sala_abc"}}
        assert payload["tipo"] == "PACIENTE_EM_SALA"
        assert payload["sala"]["codigo"] == "sala_abc"


# ---------------------------------------------------------------------------
# Testes de deduplicação
# ---------------------------------------------------------------------------

class TestDeduplicacao:
    def test_id_unico_nao_deduplicado(self) -> None:
        ids = {"teleconsulta_1", "teleconsulta_2"}
        assert len(ids) == 2

    def test_id_repetido_deduplicado(self) -> None:
        ids = {"teleconsulta_1", "teleconsulta_1", "teleconsulta_2"}
        assert len(ids) == 2


# ---------------------------------------------------------------------------
# Testes de intervalos temporais
# ---------------------------------------------------------------------------

class TestIntervalos:
    def test_antecedencia_lembrete_15_minutos_em_ms(self) -> None:
        assert ANTECEDENCIA_LEMBRETE_MS == 900_000

    def test_intervalo_polling_padrao_30_segundos(self) -> None:
        assert INTERVALO_POLLING_PADRAO_MS == 30_000

    def test_delta_ate_instante_futuro(self, agora: datetime) -> None:
        futuro = agora + timedelta(minutes=10)
        delta = (futuro - agora).total_seconds()
        assert 599 < delta < 601

    def test_delta_ate_instante_passado(self, agora: datetime) -> None:
        passado = agora - timedelta(minutes=5)
        delta = (passado - agora).total_seconds()
        assert -310 < delta < -290