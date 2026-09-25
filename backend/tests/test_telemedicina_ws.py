"""
Testes automatizados com Pytest para o Hub WebSocket de Teleconsulta do MedIA.
Valida signaling WebRTC, troca de mensagens SDP, ICE candidates e sincronização de estado.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from app.api.v1.telemedicina_ws import (
    PapelParticipante,
    TipoMensagemWS,
    EstadoSessao,
    HubTelemedicinaWS,
    ConsentimentoBase,
    AtualizacaoEstadoMedico,
    AtualizacaoEstadoPaciente,
    MensagemSDPSignal,
    EnvelopeEntrada,
    EnvelopeSaida,
)
from app.models.telemedicina import StatusTeleconsulta


def test_papel_participante_enum():
    """Testa enum PapelParticipante."""
    assert PapelParticipante.MEDICO.value == "medico"
    assert PapelParticipante.PACIENTE.value == "paciente"


def test_tipomessage_ws_enum():
    """Testa enum TipoMensagemWS."""
    tipos_importantes = {
        "offer", "answer", "ice_candidate",
        "estado_medico", "estado_paciente", "consentimento"
    }
    tipos_reais = {t.value for t in TipoMensagemWS}
    assert tipos_importantes.issubset(tipos_reais)


def test_estados_sessao_enum():
    """Testa enum EstadoSessao."""
    valores_validos = {
        "aguardando_medico", "aguardando_paciente",
        "em_andamento", "concluido", "cancelado"
    }
    valores_reais = {s.value for s in EstadoSessao}
    assert valores_validos == valores_reais


def test_status_teleconsulta_enum():
    """Testa enum StatusTeleconsulta."""
    from app.models.telemedicina import StatusTeleconsulta

    valores_validos = {"AGENDADA", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA", "SUSPENSA"}
    valores_reais = {s.value for s in StatusTeleconsulta}
    assert valores_validos == valores_reais


def test_consentimento_schema():
    """Testa Pydantic ConsentimentoBase."""
    consentimento = ConsentimentoBase(
        cns_profissional="110 4332 1819 6000",
        escopo="dados_clinicos",
        metodo_contato="websocket"
    )
    assert consentimento.cns_profissional == "110433218196000"
    assert consentimento.escopo == "dados_clinicos"
    assert consentimento.metodo_contato == "websocket"


def test_atualizacao_estado_medico_schema():
    """Testa Pydantic AtualizacaoEstadoMedico."""
    estado_medico = AtualizacaoEstadoMedico(
        status="em_andamento",
        cns_medico="110 4332 1819 6000"
    )
    assert estado_medico.status == "em_andamento"
    assert estado_medico.cns_medico == "110433218196000"


def test_atualizacao_estado_paciente_schema():
    """Testa Pydantic AtualizacaoEstadoPaciente."""
    estado_paciente = AtualizacaoEstadoPaciente(
        cns_paciente="110 4332 1819 6000",
        status="em_andamento",
        queixa_principal="Tosse"
    )
    assert estado_paciente.cns_paciente == "110433218196000"
    assert estado_paciente.status == "em_andamento"
    assert estado_paciente.queixa_principal == "Tosse"


def test_mensagem_sdp_signal_schema():
    """Testa Pydantic MensagemSDPSignal."""
    mensagem_sdp = MensagemSDPSignal(
        tipo="offer",
        sala_codigo="SALA-123456",
        sdp="v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\nm=audio 9 UDP/TLS/RTP/SAVPF 9\r\nc=IN IP4 0.0.0.0\r\na=rtpmap:9 G722/8000/1"
    )
    assert mensagem_sdp.tipo == "offer"
    assert mensagem_sdp.sala_codigo == "SALA-123456"
    assert "v=0" in mensagem_sdp.sdp


def test_envelope_entrada_schema():
    """Testa Pydantic EnvelopeEntrada."""
    envelope = EnvelopeEntrada(
        tipo="estado_medico",
        payload={"status": "em_andamento"}
    )
    assert envelope.tipo == "estado_medico"
    assert envelope.payload["status"] == "em_andamento"


def test_envelope_saida_schema():
    """Testa Pydantic EnvelopeSaida."""
    envelope = EnvelopeSaida(
        tipo="estado_paciente",
        de_papel="paciente",
        payload={"queixa_principal": "Tosse"},
        timestamp=datetime.now(timezone.utc)
    )
    assert envelope.tipo == "estado_paciente"
    assert envelope.de_papel == "paciente"
    assert envelope.payload["queixa_principal"] == "Tosse"


def test_hub_telemedicina_criar_sala():
    """Testa criação de sala virtual no HubTelemedicinaWS."""
    mock_db = Mock()

    hub = HubTelemedicinaWS()
    sala = hub.criar_sala("TEST-SALA-001", mock_db)
    assert sala.codigo == "TEST-SALA-001"
    assert len(sala.participantes) == 0
    assert sala.status.value == "aguardando_medico"


def test_hub_telemedicina_estatisticas():
    """Testa obtenção de estatísticas da sala no HubTelemedicinaWS."""
    mock_db = Mock()

    hub = HubTelemedicinaWS()
    sala = hub.criar_sala("TEST-SALA-STATS", mock_db)

    stats = hub.obter_estatisticas("TEST-SALA-STATS")
    assert stats["sala_codigo"] == "TEST-SALA-STATS"
    assert "conexoes" in stats
    assert "eventos" in stats
    assert "timestamp" in stats


def test_hub_telemedicina_encerrar_sala():
    """Testa encerramento de sala virtual no HubTelemedicinaWS."""
    mock_db = Mock()

    hub = HubTelemedicinaWS()
    sala = hub.criar_sala("TEST-SALA-CLOSE", mock_db)

    # Adicionar uma conexão mock
    fila = Mock()
    hub._filas["TEST-SALA-CLOSE"].append(fila)

    hub.encerrar_sala("TEST-SALA-CLOSE")

    assert "TEST-SALA-CLOSE" not in hub._filas
    assert "TEST-SALA-CLOSE" not in hub._salas


def test_hub_telemedicina_pub_evento():
    """Testa publicação de evento no HubTelemedicinaWS."""
    mock_db = Mock()

    hub = HubTelemedicinaWS()
    sala = hub.criar_sala("TEST-SALA-EVENTO", mock_db)

    evento = {
        "tipo": "estado_medico",
        "payload": {"status": "em_andamento"},
        "de_papel": "medico",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entregues = hub.publicar("TEST-SALA-EVENTO", evento, {"medico", "paciente"})
    assert entregues >= 0

    # Verificar estatísticas
    assert hub._stats["TEST-SALA-EVENTO"]["eventos"] == 1


def test_hub_telemedicina_adicionar_remover_participante():
    """Testa adicionar e remover participante no HubTelemedicinaWS."""
    from unittest.mock import Mock

    hub = HubTelemedicinaWS()
    mock_db = Mock()

    sala = hub.criar_sala("TEST-SALA-PART", mock_db)

    # Criar participante mock
    participante = Mock()
    participante.papel = PapelParticipante.MEDICO

    hub.adicionar_participante("TEST-SALA-PART", participante)
    assert len(sala.participantes) == 1

    hub.remover_participante("TEST-SALA-PART", PapelParticipante.MEDICO)
    assert len(sala.participantes) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])