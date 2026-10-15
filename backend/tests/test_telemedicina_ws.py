"""
Testes automatizados com Pytest para o Hub WebSocket de Teleconsulta do MedIA.
Valida signaling WebRTC, troca de mensagens SDP, ICE candidates e sincronização de estado.
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.api.v1.telemedicina_ws import (
    PapelParticipante,
    TipoMensagemWS,
    EstadoSessao,
    ConsentimentoBase,
    AtualizacaoEstadoMedico,
    AtualizacaoEstadoPaciente,
    EnvelopeEntrada,
    EnvelopeSaida,
    HubTelemedicinaWS,
    MensagemSDPSignal,
)


def test_papel_participante_enum():
    """Testa enum PapelParticipante."""
    assert PapelParticipante.MEDICO.value == "medico"
    assert PapelParticipante.PACIENTE.value == "paciente"


def test_tipo_mensagem_ws_enum():
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
    valores_reais = {status.value for status in StatusTeleconsulta}
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
    hub.criar_sala("TEST-SALA-STATS", mock_db)

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
    assert sala.status.value == "aguardando_medico"

    # Adicionar uma conexão mock
    hub._filas["TEST-SALA-CLOSE"].append(Mock())

    hub.encerrar_sala("TEST-SALA-CLOSE")

    assert "TEST-SALA-CLOSE" not in hub._filas
    assert "TEST-SALA-CLOSE" not in hub._salas


def test_hub_telemedicina_pub_evento():
    """Testa publicação de evento no HubTelemedicinaWS."""
    mock_db = Mock()

    hub = HubTelemedicinaWS()
    hub.criar_sala("TEST-SALA-EVENTO", mock_db)

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
    hub = HubTelemedicinaWS()
    mock_db = Mock()

    sala = hub.criar_sala("TEST-SALA-PART", mock_db)
    assert sala.status.value == "aguardando_medico"

    # Criar participante mock
    participante = Mock()
    participante.papel = PapelParticipante.MEDICO

    hub.adicionar_participante("TEST-SALA-PART", participante)
    assert len(sala.participantes) == 1

    hub.remover_participante("TEST-SALA-PART", PapelParticipante.MEDICO)
    assert len(sala.participantes) == 0


def test_hub_publicar_com_exclusao_de_fila():
    """Garante que publicar com excluir_fila não replica a mensagem para o remetente."""
    hub = HubTelemedicinaWS()
    hub.criar_sala("SALA-ECHO-TEST")

    fila_medico = Mock()
    fila_paciente = Mock()

    hub.registrar_fila("SALA-ECHO-TEST", PapelParticipante.MEDICO, fila_medico)
    hub.registrar_fila("SALA-ECHO-TEST", PapelParticipante.PACIENTE, fila_paciente)

    evento = {"tipo": "offer", "sdp": "v=0..."}
    entregues = hub.publicar("SALA-ECHO-TEST", evento, excluir_fila=fila_medico)

    assert entregues == 1
    fila_medico.put_nowait.assert_not_called()
    fila_paciente.put_nowait.assert_called_once_with(evento)


def test_hub_listar_participantes():
    """Testa listagem dos papéis conectados em uma sala."""
    hub = HubTelemedicinaWS()
    hub.criar_sala("SALA-LIST-TEST")

    assert hub.listar_participantes("SALA-LIST-TEST") == []

    hub.registrar_fila("SALA-LIST-TEST", PapelParticipante.MEDICO, Mock())
    assert hub.listar_participantes("SALA-LIST-TEST") == ["medico"]

    hub.registrar_fila("SALA-LIST-TEST", PapelParticipante.PACIENTE, Mock())
    assert hub.listar_participantes("SALA-LIST-TEST") == ["medico", "paciente"]


def test_websocket_papel_invalido(client):
    """Garante que conectar com papel desconhecido rejeita com código 4400."""
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/ws/telemedicina/sala/SALA-INV?papel=alienigena"):
            pass
    assert exc_info.value.code == 4400


def test_websocket_signaling_bidirecional_webrtc(client):
    """Valida o ciclo completo de signaling WebRTC entre Médico e Paciente."""
    codigo_sala = "SALA-WEBRTC-SUITE-1"

    with client.websocket_connect(f"/api/v1/ws/telemedicina/sala/{codigo_sala}?papel=medico") as ws_medico:
        # Médico recebe confirmação de conexão
        msg_init_medico = ws_medico.receive_json()
        assert msg_init_medico["tipo"] == "ok"
        assert msg_init_medico["payload"]["evento"] == "conectado"
        assert msg_init_medico["payload"]["papel"] == "medico"

        # Médico testa ping/pong
        ws_medico.send_json({"tipo": "ping", "payload": {}})
        msg_pong = ws_medico.receive_json()
        assert msg_pong["tipo"] == "pong"

        with client.websocket_connect(f"/api/v1/ws/telemedicina/sala/{codigo_sala}?papel=paciente") as ws_paciente:
            # Paciente recebe confirmação
            msg_init_paciente = ws_paciente.receive_json()
            assert msg_init_paciente["tipo"] == "ok"
            assert msg_init_paciente["payload"]["evento"] == "conectado"
            assert msg_init_paciente["payload"]["papel"] == "paciente"

            # Médico recebe aviso de que o paciente entrou
            msg_peer_joined = ws_medico.receive_json()
            assert msg_peer_joined["tipo"] == "peer_joined"
            assert msg_peer_joined["payload"]["papel"] == "paciente"

            # Médico envia Offer WebRTC
            sdp_offer = {"sdp": "v=0\r\no=- 1 1 IN IP4 127.0.0.1", "type": "offer"}
            ws_medico.send_json({"tipo": "offer", "payload": sdp_offer})

            # Paciente recebe Offer
            msg_offer_recebida = ws_paciente.receive_json()
            assert msg_offer_recebida["tipo"] == "offer"
            assert msg_offer_recebida["de_papel"] == "medico"
            assert msg_offer_recebida["payload"]["sdp"] == sdp_offer["sdp"]

            # Paciente envia Answer WebRTC
            sdp_answer = {"sdp": "v=0\r\no=- 2 2 IN IP4 127.0.0.1", "type": "answer"}
            ws_paciente.send_json({"tipo": "answer", "payload": sdp_answer})

            # Médico recebe Answer
            msg_answer_recebida = ws_medico.receive_json()
            assert msg_answer_recebida["tipo"] == "answer"
            assert msg_answer_recebida["de_papel"] == "paciente"
            assert msg_answer_recebida["payload"]["sdp"] == sdp_answer["sdp"]

            # Médico envia ICE candidate
            ice_medico = {"candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 50000 typ host", "sdpMid": "0"}
            ws_medico.send_json({"tipo": "ice_candidate", "payload": ice_medico})

            # Paciente recebe ICE candidate do médico
            msg_ice_paciente = ws_paciente.receive_json()
            assert msg_ice_paciente["tipo"] == "ice_candidate"
            assert msg_ice_paciente["payload"]["candidate"] == ice_medico["candidate"]

            # Paciente envia ICE candidate
            ice_paciente = {"candidate": "candidate:2 1 UDP 2130706431 192.168.1.101 50001 typ host", "sdpMid": "0"}
            ws_paciente.send_json({"tipo": "ice_candidate", "payload": ice_paciente})

            # Médico recebe ICE candidate do paciente
            msg_ice_medico = ws_medico.receive_json()
            assert msg_ice_medico["tipo"] == "ice_candidate"
            assert msg_ice_medico["payload"]["candidate"] == ice_paciente["candidate"]

        # Ao sair do bloco do paciente (desconexão), o médico recebe peer_left
        msg_peer_left = ws_medico.receive_json()
        assert msg_peer_left["tipo"] == "peer_left"
        assert msg_peer_left["payload"]["papel"] == "paciente"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

