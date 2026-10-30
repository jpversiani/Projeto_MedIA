"""Guardas estruturais da teleconsulta no frontend (T3).

Não há navegador na suíte, então estes testes não provam que o áudio sai do
alto-falante — eles travam decisões que já causaram bug e que quebrariam de novo
silenciosamente se alguém mexer no arquivo:

* a `RTCPeerConnection` **não** pode ser criada antes de a lista de ICE chegar
  (o bug real: subia só com STUN e o TURN configurado nunca era usado);
* a lista de ICE precisa ser aplicada *antes* da criação da conexão;
* as funções chamadas por `onclick` precisam ser globais (script clássico) ou
  expostas em `window` — senão o botão simplesmente não faz nada;
* todo `getElementById` da sessão deve existir no HTML correspondente.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "app" / "static"
JSDIR = RAIZ / "js"

SESSAO = (JSDIR / "teleconsulta_sessao.js").read_text(encoding="utf-8")
MANAGER = (JSDIR / "webrtc_manager.js").read_text(encoding="utf-8")
APP_JS = (RAIZ / "app.js").read_text(encoding="utf-8")
INDEX = (RAIZ / "index.html").read_text(encoding="utf-8")
PACIENTE = (RAIZ / "telemedicina_paciente.html").read_text(encoding="utf-8")


# ----------------------------------------------------------------------
# ICE: a ordem importa
# ----------------------------------------------------------------------
def test_preparo_de_midia_nao_cria_peer_connection():
    """`#criarWebRTC` só captura mídia — quem abre o par é `#garantirPeerConnection`."""
    inicio = SESSAO.index("async #criarWebRTC(")
    fim = SESSAO.index("async #garantirPeerConnection(")
    corpo = SESSAO[inicio:fim]
    assert "criarPeerConnection(" not in corpo, (
        "A PeerConnection está sendo criada antes de a lista de ICE chegar; "
        "o TURN do servidor nunca seria aplicado."
    )


def test_ice_do_servidor_e_aplicado_antes_de_criar_a_conexao():
    inicio = SESSAO.index("async #garantirPeerConnection(")
    corpo = SESSAO[inicio : inicio + 900]
    assert "definirIceServers(" in corpo
    assert corpo.index("definirIceServers(") < corpo.index("criarPeerConnection(")


def test_manager_expoe_definir_ice_servers():
    assert "definirIceServers(servidores)" in MANAGER
    # A RTCPeerConnection copia a configuração no construtor: precisa ler #config.
    assert "this.#config.turn" in MANAGER


def test_sala_ingressada_aplica_ice_antes_de_ofertar():
    inicio = SESSAO.index('case "sala_ingressada"')
    fim = SESSAO.index('case "peer_joined"', inicio)
    trecho = SESSAO[inicio:fim]
    assert "ice_servers" in trecho
    assert trecho.index("#garantirPeerConnection") < trecho.index("#ofertar")


def test_reconexao_forca_nova_coleta_de_candidatos():
    assert "restartIce()" in SESSAO


# ----------------------------------------------------------------------
# Ligação com o HTML (onclick só funciona se a função for global)
# ----------------------------------------------------------------------
def test_app_js_e_script_classico_e_carrega_no_index():
    """Se `app.js` virar módulo, todo `onclick=` do index quebra de uma vez."""
    assert '<script src="/static/app.js"></script>' in INDEX
    assert 'type="module"' not in INDEX.split('src="/static/app.js"')[0].split("<script")[-1]


def test_botao_de_conectar_aponta_para_funcao_global():
    assert "iniciarTeleconsultaWebRTC()" in INDEX
    assert re.search(r"^async function iniciarTeleconsultaWebRTC\(", APP_JS, re.MULTILINE)


def test_pagina_do_paciente_expoe_funcoes_para_onclick():
    for funcao in ("conectarSala", "alternarAudio", "alternarVideo", "encerrarChamada"):
        assert f"window.{funcao}" in PACIENTE, f"{funcao} não está exposta em window"
        assert f"{funcao}()" in PACIENTE or f'{funcao}(' in PACIENTE


def test_ids_usados_pela_pagina_do_paciente_existem():
    usados = set(re.findall(r"getElementById\('([a-z0-9-]+)'\)", PACIENTE))
    usados |= set(re.findall(r"querySelector\('#([a-z0-9-]+)'", PACIENTE))
    declarados = set(re.findall(r'id="([a-z0-9-]+)"', PACIENTE))
    faltando = usados - declarados
    assert not faltando, f"IDs referenciados e inexistentes no HTML: {sorted(faltando)}"


def test_ids_da_teleconsulta_existem_no_index():
    for identificador in (
        "btn-conectar-teleconsulta",
        "teleconsulta-status",
        "medico-video-local",
        "medico-video-remoto",
        "medico-aviso-esperando",
    ):
        assert f'id="{identificador}"' in INDEX, f"falta #{identificador} no index.html"


# ----------------------------------------------------------------------
# Segurança e limites conhecidos, declarados no código
# ----------------------------------------------------------------------
def test_token_vai_na_query_do_websocket_e_nao_em_texto_puro_no_log():
    assert "params.set(\"token\"" in SESSAO
    assert "console.log(this.#token" not in SESSAO


# ----------------------------------------------------------------------
# TM-4: a conversão para presencial usa o id REAL da teleconsulta
# ----------------------------------------------------------------------
def test_conversao_presencial_nao_usa_teleconsulta_id_fixo():
    """Antes o frontend enviava `teleconsulta_id: 1` fixo.

    Com vários atendimentos o registro da conversão (Art. 3º CFM) ia para a
    teleconsulta errada — ou para uma inexistente. A conversão agora resolve
    o id real (`resolverTeleconsultaAtiva`), e este teste impede que o
    literal fixo volte ao arquivo.
    """
    assert "teleconsulta_id: 1," not in APP_JS
    assert "resolverTeleconsultaAtiva" in APP_JS

    # Dentro de `acionarConversaoPresencial` o id vem do helper resolvido.
    inicio = APP_JS.index("async function acionarConversaoPresencial(")
    fim = APP_JS.index("\nfunction ", inicio + 10)
    corpo = APP_JS[inicio:fim]
    assert "resolverTeleconsultaAtiva()" in corpo
    assert "teleconsulta_id: teleconsultaId" in corpo
