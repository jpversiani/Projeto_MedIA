"""Testes da teleconsulta real (T3): sinalização WebRTC de ponta a ponta.

O que estes testes fixam — e que antes não existia:

* o ``offer`` vai **só para o outro participante** (antes era republicado para
  todos, inclusive para quem ofertou, e a negociação nunca fechava);
* ``peer_joined``/``peer_left`` avisam o médico quando o paciente entra ou cai;
* o segundo participante é quem cria a oferta (evita glare);
* a sala exige token quando a autenticação está ligada — o papel não pode vir
  da query string;
* teleconsulta encerrada, sala inexistente e sala cheia são recusadas;
* mensagem malformada não derruba a chamada em andamento.
"""

import pytest
from starlette.websockets import WebSocketDisconnect
from sqlalchemy.orm import sessionmaker

from app.api.v1 import telemedicina_ws as ws_mod
from app.models.estabelecimento import Estabelecimento
from app.models.telemedicina import SalaVirtual, StatusTeleconsulta
from app.models.usuario import PapelUsuarioEnum, Usuario, VinculoClinica
from app.services.auth_service import create_access_token
from app.services.signaling_hub import (
    Participante,
    ParticipanteJaConectado,
    SalaOcupada,
    SignalingHub,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def ambiente_ws(db_session, monkeypatch):
    """Aponta o handler WS para o banco hermético da suíte.

    O handler abre sessões próprias (`SessionLocal`), porque uma rota WebSocket
    não passa por `Depends(get_db)`. Sem este override elas iriam para o
    `sqlite:///:memory:` global, que não tem as tabelas criadas.
    """
    fabrica = sessionmaker(
        bind=db_session.get_bind(), autocommit=False, autoflush=False
    )
    monkeypatch.setattr(ws_mod, "SessionLocal", fabrica)

    criados = {"usuarios": [], "salas": []}

    def _novo_usuario(email, nome, papel, estabelecimento_id):
        usuario = Usuario(email=email, nome=nome, is_active=True)
        db_session.add(usuario)
        db_session.commit()
        db_session.refresh(usuario)
        db_session.add(
            VinculoClinica(
                usuario_id=usuario.id,
                estabelecimento_id=estabelecimento_id,
                papel=papel,
                is_default=True,
            )
        )
        db_session.commit()
        criados["usuarios"].append(usuario.id)
        vinculo = (
            db_session.query(VinculoClinica)
            .filter(VinculoClinica.usuario_id == usuario.id)
            .first()
        )
        return usuario, vinculo

    def _nova_sala(codigo, status=StatusTeleconsulta.AGENDADA, expiracao=None):
        sala = SalaVirtual(
            codigo_sala=codigo, status=status, data_expiracao=expiracao
        )
        db_session.add(sala)
        db_session.commit()
        criados["salas"].append(codigo)
        return sala

    estabelecimento = db_session.query(Estabelecimento).order_by(Estabelecimento.id).first()

    medico, vinculo_medico = _novo_usuario(
        "t3.medico@media-t3.com.br", "Dra. Teleconsulta", PapelUsuarioEnum.MEDICO,
        estabelecimento.id,
    )
    paciente, vinculo_paciente = _novo_usuario(
        "t3.paciente@media-t3.com.br", "Paciente Teleconsulta", PapelUsuarioEnum.PACIENTE,
        estabelecimento.id,
    )
    recepcao, _ = _novo_usuario(
        "t3.recepcao@media-t3.com.br", "Recepção Teleconsulta", PapelUsuarioEnum.RECEPCAO,
        estabelecimento.id,
    )

    yield {
        "db": db_session,
        "fabrica": fabrica,
        "estabelecimento": estabelecimento,
        "medico": (medico, vinculo_medico),
        "paciente": (paciente, vinculo_paciente),
        "recepcao": recepcao,
        "nova_sala": _nova_sala,
        "token_medico": create_access_token(medico, vinculo_medico),
        "token_paciente": create_access_token(paciente, vinculo_paciente),
    }

    db_session.rollback()
    for codigo in criados["salas"]:
        db_session.query(SalaVirtual).filter(SalaVirtual.codigo_sala == codigo).delete()
    for usuario_id in criados["usuarios"]:
        db_session.query(VinculoClinica).filter(
            VinculoClinica.usuario_id == usuario_id
        ).delete()
        db_session.query(Usuario).filter(Usuario.id == usuario_id).delete()
    db_session.commit()


@pytest.fixture
def auth_ligada(monkeypatch):
    """Liga a exigência de token no handler WS."""

    class _SettingsProtegidas:
        require_auth = True
        ice_servers = [{"urls": "stun:stun.l.google.com:19302"}]
        WS_SALA_MAX_PARTICIPANTES = 2
        WS_TIMEOUT_OCIOSO_SEGUNDOS = 900

    monkeypatch.setattr(ws_mod, "settings", _SettingsProtegidas())
    return _SettingsProtegidas()


def _url(codigo, papel="medico", token=None, prefixo="/api/v1"):
    partes = [f"{prefixo}/ws/telemedicina/sala/{codigo}", f"papel={papel}"]
    if token:
        partes.append(f"token={token}")
    return "?".join([partes[0], "&".join(partes[1:])])


def _fechar_com_codigo(ws):
    """Consome até a desconexão e devolve o código de fechamento."""
    try:
        while True:
            ws.receive_json()
    except WebSocketDisconnect as erro:
        return erro.code


# ----------------------------------------------------------------------
# Hub de sinalização (unidade)
# ----------------------------------------------------------------------
def _participante(nome, papel, usuario_id=None, ws=None):
    return Participante(
        usuario_id=usuario_id,
        nome=nome,
        papel=papel,
        websocket=ws,
        codigo_sala="sala-unit",
    )


@pytest.mark.asyncio
async def test_hub_nao_roteia_para_o_remetente():
    """O ponto central do T3: quem oferta não recebe a própria oferta."""
    hub = SignalingHub(max_por_sala=2)
    enviados_a, enviados_b = [], []

    class _WS:
        def __init__(self, destino):
            self.destino = destino

        async def send_json(self, mensagem):
            self.destino.append(mensagem)

    a = _participante("A", "medico", 1, _WS(enviados_a))
    b = _participante("B", "paciente", 2, _WS(enviados_b))

    await hub.entrar("sala-unit", a)
    await hub.entrar("sala-unit", b)

    entregues = await hub.enviar_para_outros("sala-unit", a.identificador, {"tipo": "offer"})

    assert entregues == 1
    assert enviados_b == [{"tipo": "offer"}]
    assert enviados_a == []


@pytest.mark.asyncio
async def test_hub_recusa_terceiro_participante():
    hub = SignalingHub(max_por_sala=2)

    class _WS:
        async def send_json(self, mensagem):
            return None

    await hub.entrar("sala-unit", _participante("A", "medico", 1, _WS()))
    await hub.entrar("sala-unit", _participante("B", "paciente", 2, _WS()))

    with pytest.raises(SalaOcupada):
        await hub.entrar("sala-unit", _participante("C", "paciente", 3, _WS()))


@pytest.mark.asyncio
async def test_hub_recusa_conexao_duplicada_do_mesmo_usuario():
    hub = SignalingHub(max_por_sala=2)

    class _WS:
        async def send_json(self, mensagem):
            return None

    await hub.entrar("sala-unit", _participante("A", "medico", 1, _WS()))
    with pytest.raises(ParticipanteJaConectado):
        await hub.entrar("sala-unit", _participante("A", "medico", 1, _WS()))


# ----------------------------------------------------------------------
# Handshake e presença
# ----------------------------------------------------------------------
def test_entrada_avisa_presenca_e_define_quem_cria_a_oferta(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_presenca")

    with client.websocket_connect(_url("sala_t3_presenca", "medico")) as medico:
        boas_vindas = medico.receive_json()
        assert boas_vindas["tipo"] == "sala_ingressada"
        assert boas_vindas["payload"]["seu_papel"] == "medico"
        assert boas_vindas["payload"]["participantes"] == []
        # Primeiro a entrar espera: quem oferece é o segundo.
        assert boas_vindas["payload"]["deve_criar_oferta"] is False
        assert boas_vindas["payload"]["ice_servers"]

        with client.websocket_connect(_url("sala_t3_presenca", "paciente")) as paciente:
            entrada_paciente = paciente.receive_json()
            assert entrada_paciente["payload"]["deve_criar_oferta"] is True
            assert len(entrada_paciente["payload"]["participantes"]) == 1

            aviso = medico.receive_json()
            assert aviso["tipo"] == "peer_joined"
            assert aviso["payload"]["participante"]["papel"] == "paciente"


def test_offer_chega_ao_outro_lado_e_nao_volta_ao_remetente(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_offer")

    with client.websocket_connect(_url("sala_t3_offer", "medico")) as medico:
        medico.receive_json()

        with client.websocket_connect(_url("sala_t3_offer", "paciente")) as paciente:
            paciente.receive_json()
            medico.receive_json()  # peer_joined

            paciente.send_json(
                {"tipo": "offer", "payload": {"sdp": "v=0\r\no=- 1 1 IN IP4 0.0.0.0"}}
            )
            oferta = medico.receive_json()
            assert oferta["tipo"] == "offer"
            assert oferta["payload"]["sdp"].startswith("v=0")
            assert oferta["de_papel"] == "paciente"

            # Se o servidor tivesse ecoado a oferta, a próxima mensagem do
            # paciente seria o próprio "offer". Um ping prova o contrário.
            paciente.send_json({"tipo": "ping", "payload": {}})
            assert paciente.receive_json()["tipo"] == "pong"

            medico.send_json(
                {"tipo": "answer", "payload": {"sdp": "v=0\r\no=- 2 2 IN IP4 0.0.0.0"}}
            )
            resposta = paciente.receive_json()
            assert resposta["tipo"] == "answer"


def test_ice_candidate_e_repassado(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_ice")

    with client.websocket_connect(_url("sala_t3_ice", "medico")) as medico:
        medico.receive_json()
        with client.websocket_connect(_url("sala_t3_ice", "paciente")) as paciente:
            paciente.receive_json()
            medico.receive_json()

            paciente.send_json(
                {"tipo": "ice_candidate", "payload": {"candidate": "candidate:1 1 UDP"}}
            )
            recebido = medico.receive_json()
            assert recebido["tipo"] == "ice_candidate"
            assert recebido["payload"]["candidate"].startswith("candidate:")


def test_peer_left_quando_o_paciente_cai(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_saida")

    with client.websocket_connect(_url("sala_t3_saida", "medico")) as medico:
        medico.receive_json()
        with client.websocket_connect(_url("sala_t3_saida", "paciente")) as paciente:
            paciente.receive_json()
            medico.receive_json()  # peer_joined

        saida = medico.receive_json()
        assert saida["tipo"] == "peer_left"
        assert saida["payload"]["participante"]["papel"] == "paciente"


def test_leave_sala_encerra_a_conexao(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_leave")

    with client.websocket_connect(_url("sala_t3_leave", "medico")) as ws:
        ws.receive_json()
        ws.send_json({"tipo": "leave_sala", "payload": {}})
        assert _fechar_com_codigo(ws) == 1000


# ----------------------------------------------------------------------
# Autenticação
# ----------------------------------------------------------------------
def test_sem_token_e_recusado_quando_auth_ligada(client, ambiente_ws, auth_ligada):
    ambiente_ws["nova_sala"]("sala_t3_sem_token")

    with client.websocket_connect(_url("sala_t3_sem_token", "medico")) as ws:
        erro = ws.receive_json()
        assert erro["tipo"] == "erro"
        assert "token" in erro["payload"]["motivo"].lower()
        assert _fechar_com_codigo(ws) == 4401


def test_token_invalido_e_recusado(client, ambiente_ws, auth_ligada):
    ambiente_ws["nova_sala"]("sala_t3_token_ruim")

    with client.websocket_connect(
        _url("sala_t3_token_ruim", "medico", token="nao-e-um-jwt")
    ) as ws:
        assert ws.receive_json()["tipo"] == "erro"
        assert _fechar_com_codigo(ws) == 4401


def test_token_valido_entra_com_o_papel_do_token(client, ambiente_ws, auth_ligada):
    ambiente_ws["nova_sala"]("sala_t3_token_ok")

    # A query diz "paciente", mas o token é de médico: o token vence.
    with client.websocket_connect(
        _url("sala_t3_token_ok", "paciente", token=ambiente_ws["token_medico"])
    ) as ws:
        entrada = ws.receive_json()
        assert entrada["tipo"] == "sala_ingressada"
        assert entrada["payload"]["seu_papel"] == "medico"


def test_recepcao_nao_participa_da_teleconsulta(client, ambiente_ws, auth_ligada):
    ambiente_ws["nova_sala"]("sala_t3_recepcao")
    recepcao = ambiente_ws["recepcao"]
    vinculo = (
        ambiente_ws["db"]
        .query(VinculoClinica)
        .filter(VinculoClinica.usuario_id == recepcao.id)
        .first()
    )
    token = create_access_token(recepcao, vinculo)

    with client.websocket_connect(
        _url("sala_t3_recepcao", "medico", token=token)
    ) as ws:
        erro = ws.receive_json()
        assert erro["tipo"] == "erro"
        assert _fechar_com_codigo(ws) == 4401


# ----------------------------------------------------------------------
# Regras da sala
# ----------------------------------------------------------------------
def test_sala_encerrada_e_recusada(client, ambiente_ws, auth_ligada):
    ambiente_ws["nova_sala"]("sala_t3_encerrada", status=StatusTeleconsulta.CONCLUIDA)

    with client.websocket_connect(
        _url("sala_t3_encerrada", "medico", token=ambiente_ws["token_medico"])
    ) as ws:
        erro = ws.receive_json()
        assert "encerrada" in erro["payload"]["motivo"].lower()
        assert _fechar_com_codigo(ws) == 4404


def test_sala_inexistente_e_recusada_com_auth_ligada(client, ambiente_ws, auth_ligada):
    with client.websocket_connect(
        _url("sala_t3_nao_existe", "medico", token=ambiente_ws["token_medico"])
    ) as ws:
        assert ws.receive_json()["tipo"] == "erro"
        assert _fechar_com_codigo(ws) == 4404


def test_sala_cheia_recusa_o_terceiro(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_cheia")

    with client.websocket_connect(_url("sala_t3_cheia", "medico")) as medico:
        medico.receive_json()
        with client.websocket_connect(_url("sala_t3_cheia", "paciente")) as paciente:
            paciente.receive_json()
            medico.receive_json()

            with client.websocket_connect(_url("sala_t3_cheia", "paciente")) as terceiro:
                erro = terceiro.receive_json()
                assert erro["tipo"] == "erro"
                assert "cheia" in erro["payload"]["motivo"].lower()
                assert _fechar_com_codigo(terceiro) == 4409


# ----------------------------------------------------------------------
# Robustez
# ----------------------------------------------------------------------
def test_mensagem_malformada_nao_derruba_a_chamada(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_malformada")

    with client.websocket_connect(_url("sala_t3_malformada", "medico")) as ws:
        ws.receive_json()
        ws.send_text("isto nao e json")
        assert ws.receive_json()["tipo"] == "erro"

        ws.send_json({"nao_tem_tipo": True})
        assert ws.receive_json()["tipo"] == "erro"

        # A conexão continua viva — antes, qualquer uma das duas derrubava tudo.
        ws.send_json({"tipo": "ping", "payload": {}})
        assert ws.receive_json()["tipo"] == "pong"


def test_tipo_desconhecido_responde_erro_sem_fechar(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_desconhecido")

    with client.websocket_connect(_url("sala_t3_desconhecido", "medico")) as ws:
        ws.receive_json()
        ws.send_json({"tipo": "hackear", "payload": {}})
        erro = ws.receive_json()
        assert erro["tipo"] == "erro"
        assert "desconhecido" in erro["payload"]["motivo"].lower()


def test_offer_sem_sdp_responde_erro(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_sem_sdp")

    with client.websocket_connect(_url("sala_t3_sem_sdp", "medico")) as ws:
        ws.receive_json()
        ws.send_json({"tipo": "offer", "payload": {}})
        erro = ws.receive_json()
        assert erro["tipo"] == "erro"
        assert "sdp" in erro["payload"]["motivo"]


def test_estado_clinico_e_repassado_ao_outro_papel(client, ambiente_ws):
    ambiente_ws["nova_sala"]("sala_t3_estado")

    with client.websocket_connect(_url("sala_t3_estado", "medico")) as medico:
        medico.receive_json()
        with client.websocket_connect(_url("sala_t3_estado", "paciente")) as paciente:
            paciente.receive_json()
            medico.receive_json()

            medico.send_json(
                {"tipo": "estado_medico", "payload": {"status": "em_andamento"}}
            )
            estado = paciente.receive_json()
            assert estado["tipo"] == "estado_medico"
            assert estado["payload"]["status"] == "em_andamento"
