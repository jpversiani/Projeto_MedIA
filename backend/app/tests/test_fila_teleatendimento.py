"""Testes automatizados para fila_teleatendimento.py."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.services.fila_teleatendimento import (
    ClassificacaoRisco,
    FilaAcolhimentoService,
    FilaSnapshot,
    HubFilaWS,
    NotificacaoFila,
    PacienteFilaIn,
    PacienteFilaOut,
    Prioridade,
    StatusFila,
    TEMPO_ALVO_MINUTOS,
    TEMPO_MEDIO_CONSULTA_MINUTOS,
    TipoDemanda,
    TipoEventoFila,
    classificar_por_sinais_vitais,
    obter_hub_fila,
    tempo_espera_por_classificacao,
    validar_ciap2,
    validar_cid10,
    validar_documento,
)
from app.services.validadores import CNSInvalidoError, CPFInvalidoError, CodigoClinicoInvalidoError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def unidade_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def service(unidade_id: str) -> FilaAcolhimentoService:
    return FilaAcolhimentoService(unidade_id=unidade_id)


@pytest.fixture
def paciente_cns() -> PacienteFilaIn:
    return PacienteFilaIn(
        paciente_id=uuid.uuid4(),
        nome_social="João da Silva Santos",
        documento_tipo="CNS",
        documento="110433218196000",
        classificacao_risco=ClassificacaoRisco.VERDE,
        queixa_ciap2="A03",
        cid10_suspeita="J06",
        unidade_id=uuid.uuid4(),
        tipo_demanda=TipoDemanda.ESPONTANEA,
    )


@pytest.fixture
def paciente_vermelho() -> PacienteFilaIn:
    return PacienteFilaIn(
        paciente_id=uuid.uuid4(),
        nome_social="Maria Costa Lima",
        documento_tipo="CNS",
        documento="110433218196001",
        classificacao_risco=ClassificacaoRisco.VERMELHO,
        queixa_ciap2="A80",
        cid10_suspeita="R40.2",
        unidade_id=uuid.uuid4(),
        tipo_demanda=TipoDemanda.URGENCIA,
        sinais_vitais={"pa_sistolica": 90, "saturacao_o2": 85},
    )


@pytest.fixture
def paciente_laranja() -> PacienteFilaIn:
    return PacienteFilaIn(
        paciente_id=uuid.uuid4(),
        nome_social="Pedro Henrique Alves",
        documento_tipo="CNS",
        documento="110433218196002",
        classificacao_risco=ClassificacaoRisco.LARANJA,
        queixa_ciap2="K86",
        unidade_id=uuid.uuid4(),
        tipo_demanda=TipoDemanda.AGENDADA,
    )


@pytest.fixture
def paciente_cpf() -> PacienteFilaIn:
    return PacienteFilaIn(
        paciente_id=uuid.uuid4(),
        nome_social="Ana Paula Souza",
        documento_tipo="CPF",
        documento="52998224725",
        classificacao_risco=ClassificacaoRisco.AZUL,
        unidade_id=uuid.uuid4(),
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Validação de documentos
# ---------------------------------------------------------------------------


class TestValidarDocumento:
    def test_valida_cns_valido(self) -> None:
        resultado = validar_documento("110433218196000", "CNS")
        assert resultado == "110433218196000"

    def test_valida_cns_com_mascara(self) -> None:
        resultado = validar_documento("110 4332 1819 6000", "CNS")
        assert resultado == "110433218196000"

    def test_valida_cpf_valido(self) -> None:
        resultado = validar_documento("52998224725", "CPF")
        assert resultado == "52998224725"

    def test_cns_invalido_raise(self) -> None:
        with pytest.raises(CNSInvalidoError):
            validar_documento("000000000000000", "CNS")

    def test_cpf_invalido_raise(self) -> None:
        with pytest.raises(CPFInvalidoError):
            validar_documento("00000000000", "CPF")

    def test_tipo_invalido_raise(self) -> None:
        with pytest.raises(ValueError, match="Tipo de documento inválido"):
            validar_documento("12345", "RG")


class TestValidarCIAP2:
    def test_valida_ciap2(self) -> None:
        assert validar_ciap2("A03") == "A03"
        assert validar_ciap2("k86") == "K86"

    def test_ciap2_invalido_raise(self) -> None:
        with pytest.raises(CodigoClinicoInvalidoError):
            validar_ciap2("Z")

    def test_ciap2_none(self) -> None:
        assert validar_ciap2(None) is None  # type: ignore[arg-type]


class TestValidarCID10:
    def test_valida_cid10(self) -> None:
        assert validar_cid10("I10") == "I10"
        assert validar_cid10("i10") == "I10"
        assert validar_cid10("J06") == "J06"

    def test_cid10_com_extensao(self) -> None:
        assert validar_cid10("N39.0") == "N39.0"

    def test_cid10_invalido_raise(self) -> None:
        with pytest.raises(CodigoClinicoInvalidoError):
            validar_cid10("Z999")


# ---------------------------------------------------------------------------
# PacienteFilaIn — validação Pydantic
# ---------------------------------------------------------------------------


class TestPacienteFilaIn:
    def test_cria_com_cns(self, paciente_cns: PacienteFilaIn) -> None:
        assert paciente_cns.documento == "110433218196000"
        assert paciente_cns.documento_tipo == "CNS"

    def test_cria_com_cpf(self, paciente_cpf: PacienteFilaIn) -> None:
        assert paciente_cpf.documento == "52998224725"
        assert paciente_cpf.documento_tipo == "CPF"

    def test_normaliza_cns_com_espacos(self) -> None:
        p = PacienteFilaIn(
            paciente_id=uuid.uuid4(),
            nome_social="Teste",
            documento_tipo="CNS",
            documento="110 4332 1819 6000",
            classificacao_risco=ClassificacaoRisco.VERDE,
            unidade_id=uuid.uuid4(),
        )
        assert p.documento == "110433218196000"

    def test_rejeita_cns_invalido(self) -> None:
        with pytest.raises(ValidationError):
            PacienteFilaIn(
                paciente_id=uuid.uuid4(),
                nome_social="Teste",
                documento_tipo="CNS",
                documento="000000000000000",
                classificacao_risco=ClassificacaoRisco.VERDE,
                unidade_id=uuid.uuid4(),
            )

    def test_rejeita_cpf_invalido(self) -> None:
        with pytest.raises(ValidationError):
            PacienteFilaIn(
                paciente_id=uuid.uuid4(),
                nome_social="Teste",
                documento_tipo="CPF",
                documento="00000000000",
                classificacao_risco=ClassificacaoRisco.VERDE,
                unidade_id=uuid.uuid4(),
            )

    def test_normaliza_ciap2(self, paciente_cns: PacienteFilaIn) -> None:
        assert paciente_cns.queixa_ciap2 == "A03"

    def test_normaliza_cid10(self, paciente_cns: PacienteFilaIn) -> None:
        assert paciente_cns.cid10_suspeita == "J06"


# ---------------------------------------------------------------------------
# Prioridades e tempos
# ---------------------------------------------------------------------------


class TestPrioridades:
    def test_ordem_prioridade(self) -> None:
        assert Prioridade.VERMELHO < Prioridade.LARANJA
        assert Prioridade.LARANJA < Prioridade.AMARELO
        assert Prioridade.AMARELO < Prioridade.VERDE
        assert Prioridade.VERDE < Prioridade.AZUL

    def test_tempos_alvo(self) -> None:
        assert TEMPO_ALVO_MINUTOS[ClassificacaoRisco.VERMELHO] == 0
        assert TEMPO_ALVO_MINUTOS[ClassificacaoRisco.LARANJA] == 10
        assert TEMPO_ALVO_MINUTOS[ClassificacaoRisco.AMARELO] == 60
        assert TEMPO_ALVO_MINUTOS[ClassificacaoRisco.VERDE] == 120
        assert TEMPO_ALVO_MINUTOS[ClassificacaoRisco.AZUL] == 240

    def test_tempo_espera_por_classificacao(self) -> None:
        assert tempo_espera_por_classificacao(ClassificacaoRisco.VERMELHO) == 0
        assert tempo_espera_por_classificacao(ClassificacaoRisco.AZUL) == 240


# ---------------------------------------------------------------------------
# Classificação por sinais vitais
# ---------------------------------------------------------------------------


class TestClassificarSinaisVitais:
    def test_vermelho_pressao(self) -> None:
        assert (
            classificar_por_sinais_vitais({"pa_sistolica": 200})
            == ClassificacaoRisco.VERMELHO
        )

    def test_vermelho_saturacao(self) -> None:
        assert (
            classificar_por_sinais_vitais({"saturacao_o2": 85})
            == ClassificacaoRisco.VERMELHO
        )

    def test_vermelho_frequencia_cardiaca(self) -> None:
        assert (
            classificar_por_sinais_vitais({"frequencia_cardiaca": 140})
            == ClassificacaoRisco.VERMELHO
        )

    def test_vermelho_frequencia_respiratoria(self) -> None:
        assert (
            classificar_por_sinais_vitais({"frequencia_respiratoria": 35})
            == ClassificacaoRisco.VERMELHO
        )

    def test_vermelho_temperatura(self) -> None:
        assert (
            classificar_por_sinais_vitais({"temperatura": 41.0})
            == ClassificacaoRisco.VERMELHO
        )

    def test_laranjo_pressao(self) -> None:
        assert (
            classificar_por_sinais_vitais({"pa_sistolica": 165})
            == ClassificacaoRisco.LARANJA
        )

    def test_laranjo_saturacao(self) -> None:
        assert (
            classificar_por_sinais_vitais({"saturacao_o2": 92})
            == ClassificacaoRisco.LARANJA
        )

    def test_verde_por_padrao(self) -> None:
        assert (
            classificar_por_sinais_vitais({"pa_sistolica": 120})
            == ClassificacaoRisco.VERDE
        )

    def test_vazio_retorna_verde(self) -> None:
        assert classificar_por_sinais_vitais({}) == ClassificacaoRisco.VERDE


# ---------------------------------------------------------------------------
# FilaAcolhimentoService — operações principais
# ---------------------------------------------------------------------------


class TestFilaAcolhimentoService:
    def test_entrar_na_fila(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        resultado = _run(service.entrar_na_fila(paciente_cns))
        assert resultado.id is not None
        assert resultado.nome_social == "João da Silva Santos"
        assert resultado.classificacao_risco == ClassificacaoRisco.VERDE
        assert resultado.status == StatusFila.AGUARDANDO

    def test_entrar_na_fila_retorna_paciente_out(
        self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn
    ) -> None:
        resultado = _run(service.entrar_na_fila(paciente_cns))
        assert isinstance(resultado, PacienteFilaOut)
        assert resultado.paciente_id == paciente_cns.paciente_id

    def test_entrar_na_fila_com_cpf(self, service: FilaAcolhimentoService, paciente_cpf: PacienteFilaIn) -> None:
        resultado = _run(service.entrar_na_fila(paciente_cpf))
        assert resultado.documento == "52998224725"
        assert resultado.documento_tipo == "CPF"

    def test_proximo_da_fila_vazia(self, service: FilaAcolhimentoService) -> None:
        resultado = _run(service.proximo_da_fila())
        assert resultado is None

    def test_proximo_da_fila_retorna_aguardando(
        self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn
    ) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        proximo = _run(service.proximo_da_fila())
        assert proximo is not None
        assert proximo.status == StatusFila.AGUARDANDO

    def test_chamar_proximo(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        chamado = _run(service.chamar_proximo())
        assert chamado is not None
        assert chamado.status == StatusFila.CHAMADO
        assert chamado.chamado_em is not None

    def test_chamar_proximo_vazia(self, service: FilaAcolhimentoService) -> None:
        resultado = _run(service.chamar_proximo())
        assert resultado is None

    def test_iniciar_atendimento(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        chamado = _run(service.chamar_proximo())
        assert chamado is not None
        em_atendimento = _run(service.iniciar_atendimento(chamado.id))
        assert em_atendimento.status == StatusFila.EM_ATENDIMENTO
        assert em_atendimento.atendido_em is not None

    def test_finalizar_atendimento(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        chamado = _run(service.chamar_proximo())
        assert chamado is not None
        _run(service.iniciar_atendimento(chamado.id))
        finalizado = _run(service.finalizar_atendimento(chamado.id))
        assert finalizado.status == StatusFila.FINALIZADO

    def test_cancelar(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        cancelado = _run(service.cancelar(paciente_cns.paciente_id))
        assert cancelado.status == StatusFila.EVASAO

    def test_iniciar_atendimento_status_invalido(
        self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn
    ) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        with pytest.raises(ValueError, match="esperado CHAMADO"):
            _run(service.iniciar_atendimento(paciente_cns.paciente_id))

    def test_finalizar_atendimento_id_invalido(
        self, service: FilaAcolhimentoService
    ) -> None:
        fake_id = uuid.uuid4()
        with pytest.raises(KeyError):
            _run(service.finalizar_atendimento(fake_id))

    def test_cancelar_id_invalido(self, service: FilaAcolhimentoService) -> None:
        fake_id = uuid.uuid4()
        with pytest.raises(KeyError):
            _run(service.cancelar(fake_id))

    def test_entrar_na_fila_retorna_id_unico(
        self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn, paciente_cpf: PacienteFilaIn
    ) -> None:
        r1 = _run(service.entrar_na_fila(paciente_cns))
        r2 = _run(service.entrar_na_fila(paciente_cpf))
        assert r1.id != r2.id


# ---------------------------------------------------------------------------
# Prioridade no heap
# ---------------------------------------------------------------------------


class TestPrioridadeHeap:
    def test_vermelho_antes_de_verde(
        self, service: FilaAcolhimentoService, paciente_vermelho: PacienteFilaIn, paciente_cns: PacienteFilaIn
    ) -> None:
        _run(service.entrar_na_fila(paciente_cns))  # VERDE
        _run(service.entrar_na_fila(paciente_vermelho))  # VERMELHO
        proximo = _run(service.proximo_da_fila())
        assert proximo is not None
        assert proximo.classificacao_risco == ClassificacaoRisco.VERMELHO

    def test_fifo_mesma_prioridade(
        self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn
    ) -> None:
        p1 = PacienteFilaIn(
            paciente_id=uuid.uuid4(),
            nome_social="Primeiro",
            documento_tipo="CNS",
            documento="110433218196010",
            classificacao_risco=ClassificacaoRisco.VERDE,
            unidade_id=uuid.uuid4(),
        )
        p2 = PacienteFilaIn(
            paciente_id=uuid.uuid4(),
            nome_social="Segundo",
            documento_tipo="CNS",
            documento="110433218196011",
            classificacao_risco=ClassificacaoRisco.VERDE,
            unidade_id=uuid.uuid4(),
        )
        _run(service.entrar_na_fila(p1))
        _run(service.entrar_na_fila(p2))
        proximo = _run(service.proximo_da_fila())
        assert proximo is not None
        assert proximo.nome_social == "Primeiro"

    def test_ordem_completa_prioridades(
        self, service: FilaAcolhimentoService
    ) -> None:
        cores = [
            ClassificacaoRisco.AZUL,
            ClassificacaoRisco.VERMELHO,
            ClassificacaoRisco.VERDE,
            ClassificacaoRisco.LARANJA,
            ClassificacaoRisco.AMARELO,
        ]
        for cor in cores:
            p = PacienteFilaIn(
                paciente_id=uuid.uuid4(),
                nome_social=f"Paciente {cor}",
                documento_tipo="CNS",
                documento="110433218196012",
                classificacao_risco=cor,
                unidade_id=uuid.uuid4(),
            )
            _run(service.entrar_na_fila(p))

        proximo = _run(service.proximo_da_fila())
        assert proximo is not None
        assert proximo.classificacao_risco == ClassificacaoRisco.VERMELHO


# ---------------------------------------------------------------------------
# Snapshot da fila
# ---------------------------------------------------------------------------


class TestFilaSnapshot:
    def test_snapshot_vazia(self, service: FilaAcolhimentoService) -> None:
        snap = _run(service.get_snapshot())
        assert isinstance(snap, FilaSnapshot)
        assert snap.total_aguardando == 0
        assert snap.total_chamado == 0
        assert snap.total_em_atendimento == 0
        assert snap.total_finalizado == 0
        assert snap.total_evasao == 0
        assert snap.proximos == []
        assert snap.risco_prioritario is None
        assert snap.tempo_medio_espera_min == 0.0

    def test_snapshot_com_pacientes(
        self, service: FilaAcolhimentoService, paciente_vermelho: PacienteFilaIn, paciente_cns: PacienteFilaIn
    ) -> None:
        _run(service.entrar_na_fila(paciente_vermelho))
        _run(service.entrar_na_fila(paciente_cns))
        snap = _run(service.get_snapshot())
        assert snap.total_aguardando == 2
        assert snap.risco_prioritario == ClassificacaoRisco.VERMELHO
        assert len(snap.proximos) >= 1

    def test_snapshot_por_status(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        aguardando = _run(service.get_por_status(StatusFila.AGUARDANDO))
        assert len(aguardando) == 1
        chamados = _run(service.get_por_status(StatusFila.CHAMADO))
        assert len(chamados) == 0

    def test_snapshot_contagem_por_status(
        self, service: FilaAcolhimentoService, paciente_vermelho: PacienteFilaIn, paciente_cns: PacienteFilaIn
    ) -> None:
        _run(service.entrar_na_fila(paciente_vermelho))
        _run(service.entrar_na_fila(paciente_cns))
        _run(service.chamar_proximo())
        snap = _run(service.get_snapshot())
        assert snap.total_aguardando == 1
        assert snap.total_chamado == 1


# ---------------------------------------------------------------------------
# Cálculo de tempo de espera
# ---------------------------------------------------------------------------


class TestTempoEspera:
    def test_tempo_espera_base(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        espera = service.calcular_tempo_espera(paciente_cns)
        assert espera == 120  # VERDE = 120 min

    def test_tempo_espera_vermelho(self, service: FilaAcolhimentoService, paciente_vermelho: PacienteFilaIn) -> None:
        espera = service.calcular_tempo_espera(paciente_vermelho)
        assert espera == 0  # VERMELHO = 0 min

    def test_tempo_espera_laranja(self, service: FilaAcolhimentoService, paciente_laranja: PacienteFilaIn) -> None:
        espera = service.calcular_tempo_espera(paciente_laranja)
        assert espera == 10  # LARANJA = 10 min

    def test_tempo_espera_considerando_fila(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        p2 = PacienteFilaIn(
            paciente_id=uuid.uuid4(),
            nome_social="Segundo",
            documento_tipo="CNS",
            documento="110433218196013",
            classificacao_risco=ClassificacaoRisco.VERDE,
            unidade_id=uuid.uuid4(),
        )
        _run(service.entrar_na_fila(paciente_cns))
        espera = service.calcular_tempo_espera_considerando_fila(paciente_cns, 0)
        assert espera == 120  # Ninguém na frente com prioridade maior


# ---------------------------------------------------------------------------
# HubFilaWS
# ---------------------------------------------------------------------------


class TestHubFilaWS:
    def test_conectar_desconectar(self) -> None:
        hub = HubFilaWS()
        uid = str(uuid.uuid4())
        fila, lock = hub.conectar(uid)
        assert isinstance(fila, asyncio.Queue)
        assert isinstance(lock, asyncio.Lock)
        hub.desconectar(uid, fila)

    def test_conectar_multiplo(self) -> None:
        hub = HubFilaWS()
        uid = str(uuid.uuid4())
        fila1, _ = hub.conectar(uid)
        fila2, _ = hub.conectar(uid)
        assert hub._stats[uid]["conexoes"] == 2
        hub.desconectar(uid, fila1)
        hub.desconectar(uid, fila2)

    def test_publicar(self) -> None:
        hub = HubFilaWS()
        uid = str(uuid.uuid4())
        fila, _ = hub.conectar(uid)
        notif = NotificacaoFila(
            tipo=TipoEventoFila.PACIENTE_ENTRADA,
            paciente=None,
            mensagem="Teste",
        )
        entregues = hub.publicar(uid, notif)
        assert entregues == 1
        loop = asyncio.new_event_loop()
        try:
            msg = loop.run_until_complete(fila.get())
            assert isinstance(msg, NotificacaoFila)
            assert msg.tipo == TipoEventoFila.PACIENTE_ENTRADA
        finally:
            loop.close()
        hub.desconectar(uid, fila)

    def test_obter_stats(self) -> None:
        hub = HubFilaWS()
        uid = str(uuid.uuid4())
        fila, _ = hub.conectar(uid)
        stats = hub.obter_stats(uid)
        assert stats["unidade_id"] == uid
        assert stats["conexoes"] == 1
        hub.desconectar(uid, fila)

    def test_obter_hub_global(self) -> None:
        hub = obter_hub_fila()
        assert isinstance(hub, HubFilaWS)


# ---------------------------------------------------------------------------
# NotificacaoFila
# ---------------------------------------------------------------------------


class TestNotificacaoFila:
    def test_cria_notificacao(self) -> None:
        notif = NotificacaoFila(
            tipo=TipoEventoFila.PACIENTE_ENTRADA,
            paciente=None,
            mensagem="Teste de notificação",
        )
        assert notif.tipo == TipoEventoFila.PACIENTE_ENTRADA
        assert notif.mensagem == "Teste de notificação"
        assert notif.timestamp is not None

    def test_notificacao_com_erro(self) -> None:
        notif = NotificacaoFila(
            tipo=TipoEventoFila.ERRO,
            paciente=None,
            mensagem="Erro no processamento",
            erro="CNS inválido",
        )
        assert notif.erro == "CNS inválido"
        assert notif.tipo == TipoEventoFila.ERRO


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestEnums:
    def test_classificacao_risco_values(self) -> None:
        assert ClassificacaoRisco.VERMELHO.value == "VERMELHO"
        assert ClassificacaoRisco.AZUL.value == "AZUL"

    def test_status_fila_values(self) -> None:
        assert StatusFila.AGUARDANDO.value == "AGUARDANDO_ATENDIMENTO"
        assert StatusFila.FINALIZADO.value == "FINALIZADO"
        assert StatusFila.EVASAO.value == "EVASAO"

    def test_tipo_demanda_values(self) -> None:
        assert TipoDemanda.ESPONTANEA.value == "ESPONTANEA"
        assert TipoDemanda.AGENDADA.value == "AGENDADA"
        assert TipoDemanda.URGENCIA.value == "URGENCIA"

    def test_prioridade_int(self) -> None:
        assert int(Prioridade.VERMELHO) == 1
        assert int(Prioridade.AZUL) == 5


# ---------------------------------------------------------------------------
# Casos de borda
# ---------------------------------------------------------------------------


class TestCasosDeBorda:
    def test_chamar_proximo_apos_evasao(
        self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn
    ) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        _run(service.cancelar(paciente_cns.paciente_id))
        proximo = _run(service.proximo_da_fila())
        assert proximo is None

    def test_iniciar_atendimento_id_inexistente(
        self, service: FilaAcolhimentoService
    ) -> None:
        with pytest.raises(KeyError):
            _run(service.iniciar_atendimento(uuid.uuid4()))

    def test_get_por_status_vazio(self, service: FilaAcolhimentoService) -> None:
        resultado = _run(service.get_por_status(StatusFila.AGUARDANDO))
        assert resultado == []

    def test_finalizar_todos_status(self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        chamado = _run(service.chamar_proximo())
        assert chamado is not None
        _run(service.iniciar_atendimento(chamado.id))
        finalizado = _run(service.finalizar_atendimento(chamado.id))
        assert finalizado.status == StatusFila.FINALIZADO

    def test_snapshot_apos_finalizar(
        self, service: FilaAcolhimentoService, paciente_cns: PacienteFilaIn
    ) -> None:
        _run(service.entrar_na_fila(paciente_cns))
        chamado = _run(service.chamar_proximo())
        assert chamado is not None
        _run(service.iniciar_atendimento(chamado.id))
        _run(service.finalizar_atendimento(chamado.id))
        snap = _run(service.get_snapshot())
        assert snap.total_finalizado == 1
        assert snap.total_aguardando == 0

    def test_multiple_pacientes_mesma_prioridade(
        self, service: FilaAcolhimentoService
    ) -> None:
        p1 = PacienteFilaIn(
            paciente_id=uuid.uuid4(),
            nome_social="A",
            documento_tipo="CNS",
            documento="110433218196020",
            classificacao_risco=ClassificacaoRisco.AMARELO,
            unidade_id=uuid.uuid4(),
        )
        p2 = PacienteFilaIn(
            paciente_id=uuid.uuid4(),
            nome_social="B",
            documento_tipo="CNS",
            documento="110433218196021",
            classificacao_risco=ClassificacaoRisco.AMARELO,
            unidade_id=uuid.uuid4(),
        )
        p3 = PacienteFilaIn(
            paciente_id=uuid.uuid4(),
            nome_social="C",
            documento_tipo="CNS",
            documento="110433218196022",
            classificacao_risco=ClassificacaoRisco.AMARELO,
            unidade_id=uuid.uuid4(),
        )
        _run(service.entrar_na_fila(p1))
        _run(service.entrar_na_fila(p2))
        _run(service.entrar_na_fila(p3))

        snap = _run(service.get_snapshot())
        assert snap.total_aguardando == 3
        nomes = [p.nome_social for p in snap.proximos]
        assert nomes == ["A", "B", "C"]