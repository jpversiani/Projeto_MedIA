# Arquivo: backend/tests/test_webrtc_manager.py
"""
Testes do Módulo WebRTC de Gerenciamento de Mídia Local (C1) — Projeto MedIA.

O artefato `backend/app/static/js/webrtc_manager.js` é executado no navegador,
porém o pipeline de CI do MedIA é 100% Python/pytest. Assim, o contrato do
módulo é auditado por análise estática do código-fonte, garantindo:

1) Exportação da classe WebRTCManager como módulo ES (navegadores modernos);
2) Captura correta via getUserMedia (perfis clínico de áudio/vídeo, deviceId);
3) Seleção dinâmica de microfone/câmera (enumerateDevices + devicechange);
4) Mute/unmute por MediaStreamTrack.enabled (padrão da plataforma);
5) Manipulação de RTCPeerConnection (offer/answer SDP, ICE, replaceTrack);
6) Conformidade SUS/APS e LGPD (CNS/CPF nunca vão para SDP/candidatos ICE);
7) Regressão contra APIs inválidas/inexistentes (versão anterior quebrada).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CAMINHO_MODULO = (
    Path(__file__).resolve().parents[1] / "app" / "static" / "js" / "webrtc_manager.js"
)

# APIs que não existem na plataforma WebRTC (regressão da implementação quebrada).
APIS_INVALIDAS = (
    "getTracksByType",      # inexistente; correto: getAudioTracks/getVideoTracks
    "getUserDevices",       # inexistente; correto: enumerateDevices
    "enableMicrophone",     # inexistente em getUserMedia
    "deviceIndex",          # inexistente em getUserMedia (usar deviceId)
    "maxBandwidth",         # inexistente na API moderna (usar sender.setParameters)
    ".mute =",              # mute controla-se por track.enabled, não por atributo
    "ontrackchange",        # evento inexistente em RTCPeerConnection
    "getMedia()",           # inexistente em MediaRecorder
    "mediaRecorder.getMedia",
)


@pytest.fixture(scope="module")
def codigo_fonte() -> str:
    """Lê o código-fonte do módulo WebRTC para as asserções estáticas."""
    assert CAMINHO_MODULO.exists(), f"Módulo não encontrado: {CAMINHO_MODULO}"
    return CAMINHO_MODULO.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Módulo e classe exportados
# ---------------------------------------------------------------------------
def test_arquivo_e_cabecalho_jsdoc(codigo_fonte: str) -> None:
    """O arquivo declara o escopo C1 e o domínio de teleconsulta (SUS/APS)."""
    cabecalho = codigo_fonte[:2500]
    assert "Módulo WebRTC de Gerenciamento de Mídia Local (C1)" in cabecalho
    assert "teleconsulta" in cabecalho.lower()
    assert "SUS/APS" in cabecalho


def test_classe_exportada_como_modulo_es(codigo_fonte: str) -> None:
    """A classe WebRTCManager é exportada como módulo ES."""
    assert "export class WebRTCManager" in codigo_fonte
    # Convenção do repositório (fila_espera.js): módulo ES, sem globals improvisados.
    assert "window.WebRTCManager" not in codigo_fonte
    assert "module.exports" not in codigo_fonte


# ---------------------------------------------------------------------------
# 2) Captura de mídia via getUserMedia
# ---------------------------------------------------------------------------
def test_captura_get_user_media_com_perfil_clinico(codigo_fonte: str) -> None:
    """getUserMedia com perfil clínico e restrição exata de deviceId."""
    assert "navigator.mediaDevices.getUserMedia" in codigo_fonte
    # Perfil clínico de áudio (Resolução CFM 2.314/2022 exige qualidade na APS).
    for recurso in ("echoCancellation", "noiseSuppression", "autoGainControl"):
        assert recurso in codigo_fonte, f"perfil de áudio ausente: {recurso}"
    # Perfil de vídeo de consulta.
    for recurso in ("width", "height", "frameRate"):
        assert recurso in codigo_fonte, f"perfil de vídeo ausente: {recurso}"
    # Seleção de periférico usa deviceId exato (padrão da plataforma).
    assert re.search(r"deviceId:\s*\{\s*exact:", codigo_fonte)


def test_consentimento_obrigatorio_antes_da_captura(codigo_fonte: str) -> None:
    """A captura exige consentimento explícito (LGPD + CFM 2.314/2022)."""
    assert "registrarConsentimento" in codigo_fonte
    assert re.search(
        r"if\s*\(\s*!this\.#consentimentoRegistrado\s*\)", codigo_fonte
    ), "iniciarCaptura deve bloquear captura sem consentimento"
    assert "LGPD" in codigo_fonte


# ---------------------------------------------------------------------------
# 3) Seleção dinâmica de microfone/câmera
# ---------------------------------------------------------------------------
def test_selecao_dinamica_de_dispositivos(codigo_fonte: str) -> None:
    """Enumeração de dispositivos e reatividade a hotplug (devicechange)."""
    assert "navigator.mediaDevices.enumerateDevices" in codigo_fonte
    for metodo in ("alternarMicrofone", "alternarCamera", "listarDispositivos"):
        assert re.search(rf"\b{metodo}\s*\(", codigo_fonte), f"método ausente: {metodo}"
    # Listener de hotplug de periféricos, removido no encerramento.
    assert 'addEventListener("devicechange"' in codigo_fonte
    assert 'removeEventListener("devicechange"' in codigo_fonte
    # Tipos de dispositivo da plataforma.
    for tipo in ("audioinput", "videoinput"):
        assert tipo in codigo_fonte


# ---------------------------------------------------------------------------
# 4) Controle de mute/unmute
# ---------------------------------------------------------------------------
def test_controle_de_mute_unmute_por_enabled(codigo_fonte: str) -> None:
    """Mute/unmute via MediaStreamTrack.enabled, preservando estado na troca."""
    for metodo in ("alternarMuteAudio", "definirMuteAudio", "alternarMuteVideo"):
        assert re.search(rf"\b{metodo}\s*\(", codigo_fonte), f"método ausente: {metodo}"
    # Semântica correta: enabled = false silencia sem encerrar a faixa.
    assert re.search(r"enabled\s*=\s*!", codigo_fonte)
    # Preserva mute ao trocar de periférico (sem feedback de áudio ao retomar).
    assert "preserva o estado de mute" in codigo_fonte


# ---------------------------------------------------------------------------
# 5) Manipulação de RTCPeerConnection
# ---------------------------------------------------------------------------
def test_manipulacao_de_rtcpeerconnection(codigo_fonte: str) -> None:
    """Ciclo completo de negociação SDP e sinalização ICE."""
    assert "new RTCPeerConnection(" in codigo_fonte
    for metodo in (
        "createOffer",
        "createAnswer",
        "setLocalDescription",
        "setRemoteDescription",
        "addIceCandidate",
    ):
        assert re.search(rf"\.{metodo}\s*\(", codigo_fonte), f"chamada ausente: {metodo}"
    # Eventos essenciais de mídia e conectividade.
    for evento in ("onicecandidate", "ontrack", "onconnectionstatechange"):
        assert re.search(rf"\.{evento}\s*=", codigo_fonte), f"evento ausente: {evento}"
    assert "connectionState" in codigo_fonte
    # Servidores ICE configuráveis (STUN padrão + TURN opcional).
    assert "stun:stun.l.google.com:19302" in codigo_fonte
    assert "iceServers" in codigo_fonte


def test_substituicao_de_faixa_sem_renegociacao(codigo_fonte: str) -> None:
    """Troca de periférico em consulta ativa usa replaceTrack (sem renegociação)."""
    assert ".replaceTrack(" in codigo_fonte
    assert "getSenders()" in codigo_fonte


def test_candidato_ice_antecipado_e_ignorado(codigo_fonte: str) -> None:
    """Candidatos ICE remotos só são aplicados após remoteDescription."""
    trecho = re.search(
        r"async adicionarCandidatoRemota.*?\n  \}", codigo_fonte, re.DOTALL
    )
    assert trecho is not None, "método adicionarCandidatoRemota ausente"
    assert "remoteDescription" in trecho.group(0)


# ---------------------------------------------------------------------------
# 6) Conformidade SUS/APS e LGPD
# ---------------------------------------------------------------------------
def test_identificacao_sus_aps_e_lgpd(codigo_fonte: str) -> None:
    """CNS/CPF são aceitos como identificação local e protegidos (LGPD)."""
    assert "cns" in codigo_fonte and "cpf" in codigo_fonte
    assert "LGPD" in codigo_fonte
    assert "CFM" in codigo_fonte  # Resolução 2.314/2022 (teleconsulta)
    # Identificação nunca é interpolada em SDP ou candidatos ICE.
    interpolacao_sensivel = re.search(
        r"(sdp|descricao|candidate|candidato|oferta|resposta)[^\n]*\$\{",
        codigo_fonte,
        re.IGNORECASE,
    )
    assert interpolacao_sensivel is None, (
        "CNS/CPF não podem ser interpolados em mensagens de sinalização (LGPD)"
    )


def test_sem_gravacao_de_midia_no_modulo(codigo_fonte: str) -> None:
    """C1 não grava mídia: gravação com consentimento é responsabilidade de outro módulo."""
    assert "MediaRecorder" not in codigo_fonte


# ---------------------------------------------------------------------------
# 7) Encerramento e regressões
# ---------------------------------------------------------------------------
def test_encerramento_limpa_recursos(codigo_fonte: str) -> None:
    """fechar() encerra faixas locais e fecha a PeerConnection."""
    metodo = re.search(r"  fechar\(\) \{.*?\n  \}", codigo_fonte, re.DOTALL)
    assert metodo is not None, "método fechar() ausente"
    corpo = metodo.group(0)
    assert ".stop()" in corpo
    assert ".close()" in corpo


def test_ausencia_de_apis_invalidas(codigo_fonte: str) -> None:
    """Regressão: nenhuma API inexistente/inventada da versão anterior."""
    for api in APIS_INVALIDAS:
        assert api not in codigo_fonte, f"API inválida detectada: {api}"


def test_balanco_estrutural_do_modulo(codigo_fonte: str) -> None:
    """Sanidade estrutural: chaves de blocos abrem e fecham em equilíbrio."""
    corpo = codigo_fonte
    for abre, fecha in (("{", "}"), ("(", ")"), ("[", "]")):
        assert corpo.count(abre) == corpo.count(fecha), (
            f"Desequilíbrio de delimitadores {abre}{fecha} no módulo"
        )
    # Declaração de classe única e sem duplicidade de métodos públicos.
    assert len(re.findall(r"\bclass\s+WebRTCManager\b", codigo_fonte)) == 1