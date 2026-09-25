"""Testes para o cliente SISAB (C4) - envio de lotes com retry e parsing de recibos."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import httpx
import pytest
import asyncio
import time

from app.services.sisab_client import (
    FichaSISAB,
    LoteInvalidoError,
    LoteSISAB,
    ReciboItem,
    ReciboSISAB,
    SISABClient,
    StatusRecibo,
    TipoFicha,
    TimeoutSISABError,
)

CNS_VALIDO = "123456789012348"
CNS_INVALIDO = "123456789012345"
CNES_VALIDO = "1234567"
CPF_VALIDO = "52998224725"
CIAP2_VALIDO = "A01"
CID10_VALIDO = "I10"


def _ficha_valida(**overrides) -> FichaSISAB:
    defaults = dict(
        cns=CNS_VALIDO,
        cpf=None,
        cnes=CNES_VALIDO,
        ciap2=CIAP2_VALIDO,
        cid10=CID10_VALIDO,
        data_atendimento="2024-01-01T00:00:00+00:00",
    )
    defaults.update(overrides)
    return FichaSISAB(**defaults)


def _lote_valido(**overrides) -> LoteSISAB:
    defaults = dict(
        lote_id="LOTE-001",
        cnes_origem=CNES_VALIDO,
        fichas=[_ficha_valida()],
    )
    defaults.update(overrides)
    return LoteSISAB(**defaults)


class TestFichaSISAB:
    """Testes do modelo FichaSISAB."""

    def test_criar_ficha_valida(self):
        ficha = _ficha_valida()
        assert ficha.cns == CNS_VALIDO
        assert ficha.cnes == CNES_VALIDO
        assert ficha.ciap2 == "A01"

    def test_ficha_com_cid10(self):
        ficha = _ficha_valida(cid10="I10.9")
        assert ficha.cid10 == "I10.9"

    def test_ficha_sem_cpf(self):
        ficha = _ficha_valida(cpf=None)
        assert ficha.cpf is None

    def test_ficha_cns_invalido_raise(self):
        with pytest.raises(Exception):
            _ficha_valida(cns="123")

    def test_ficha_tipo_ficha_enum(self):
        ficha = _ficha_valida(tipo_ficha=TipoFicha.VISITA_DOMICILIAR)
        assert ficha.tipo_ficha == TipoFicha.VISITA_DOMICILIAR

    def test_ficha_data_iso(self):
        ficha = _ficha_valida(data_atendimento="2024-06-15T10:30:00Z")
        assert ficha.data_atendimento == "2024-06-15T10:30:00Z"

    def test_ficha_data_invalida_raise(self):
        with pytest.raises(Exception):
            _ficha_valida(data_atendimento="not-a-date")

    def test_ficha_cpf_invalido_raise(self):
        with pytest.raises(Exception):
            _ficha_valida(cpf="123")

    def test_ficha_ciap2_invalido_raise(self):
        with pytest.raises(Exception):
            _ficha_valida(ciap2="ABC123")


class TestLoteSISAB:
    """Testes do modelo LoteSISAB."""

    def test_criar_lote_valido(self):
        lote = _lote_valido()
        assert lote.lote_id == "LOTE-001"
        assert lote.total_fichas == 1

    def test_lote_com_multiplas_fichas(self):
        fichas = [_ficha_valida(), _ficha_valida(cns="223456789012348")]
        lote = _lote_valido(fichas=fichas)
        assert lote.total_fichas == 2

    def test_lote_vazio_raise(self):
        with pytest.raises(Exception):
            LoteSISAB(lote_id="LOTE-001", cnes_origem=CNES_VALIDO, fichas=[])

    def test_lote_cnes_origem_normalizado(self):
        lote = _lote_valido(cnes_origem="1234567")
        assert lote.cnes_origem == CNES_VALIDO


class TestReciboSISAB:
    """Testes do modelo ReciboSISAB."""

    def test_recibo_sucesso(self):
        recibo = ReciboSISAB(
            lote_id="LOTE-001",
            status_geral=StatusRecibo.SUCCESS,
            total_registros=1,
            registros_sucesso=1,
            registros_erro=0,
            itens=[ReciboItem(sequencial=0, status=StatusRecibo.SUCCESS)],
        )
        assert recibo.sucesso_total is True

    def test_recibo_com_erro(self):
        recibo = ReciboSISAB(
            lote_id="LOTE-001",
            status_geral=StatusRecibo.ERROR,
            total_registros=1,
            registros_sucesso=0,
            registros_erro=1,
            itens=[ReciboItem(sequencial=0, status=StatusRecibo.ERROR, mensagem="Rejeitado")],
        )
        assert recibo.sucesso_total is False

    def test_recibo_parsing_json(self, client: SISABClient):
        data = {
            "lote_id": "LOTE-001",
            "status": "success",
            "totalRegistros": 2,
            "sucesso": 2,
            "erro": 0,
            "itens": [
                {"sequencial": 0, "status": "success", "codigoRetorno": "0"},
                {"sequencial": 1, "status": "success", "codigoRetorno": "0"},
            ],
        }
        recibo = client._parse_recibo(data)
        assert recibo.lote_id == "LOTE-001"
        assert recibo.total_registros == 2
        assert recibo.registros_sucesso == 2
        assert recibo.registros_erro == 0
        assert len(recibo.itens) == 2

    def test_recibo_parsing_xml_legacy(self, client: SISABClient):
        data = {
            "numeroLote": "LOTE-002",
            "statusGeral": "error",
            "total_registros": 1,
            "sucesso": 0,
            "erro": 1,
            "registros": [
                {"sequencial": 0, "status": "error", "codigo_retorno": "E001", "msg": "CNS invalido"},
            ],
        }
        recibo = client._parse_recibo(data)
        assert recibo.lote_id == "LOTE-002"
        assert recibo.status_geral == StatusRecibo.ERROR
        assert recibo.itens[0].codigo_retorno == "E001"

    def test_recibo_com_aviso(self):
        recibo = ReciboSISAB(
            lote_id="LOTE-003",
            status_geral=StatusRecibo.WARNING,
            total_registros=1,
            registros_sucesso=0,
            registros_erro=0,
            registros_aviso=1,
            itens=[ReciboItem(sequencial=0, status=StatusRecibo.WARNING)],
        )
        assert recibo.sucesso_total is False

    def test_recibo_data_processamento(self):
        now = datetime.now(timezone.utc)
        recibo = ReciboSISAB(
            lote_id="LOTE-004",
            status_geral=StatusRecibo.SUCCESS,
            total_registros=0,
            data_processamento=now,
        )
        assert recibo.data_processamento is not None


class TestSISABClient:
    """Testes do SISABClient."""

    @pytest.fixture
    def client(self) -> SISABClient:
        return SISABClient(base_url="https://apisus.gov.br", timeout_seg=10.0, max_retries=2)

    @pytest.fixture
    def lote(self) -> LoteSISAB:
        return _lote_valido()

    async def test_enviar_lote_sucesso(self, client: SISABClient, lote: LoteSISAB):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "lote_id": "LOTE-001",
            "status": "success",
            "totalRegistros": 1,
            "sucesso": 1,
            "erro": 0,
            "itens": [{"sequencial": 0, "status": "success"}],
        }
        mock_response.text = "<recibo>ok</recibo>"

        mock_post = AsyncMock(return_value=mock_response)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            recibo = await client.enviar_lote(lote)

        assert recibo.lote_id == "LOTE-001"
        assert recibo.sucesso_total is True

    async def test_enviar_lote_timeout_retry_exausto(self, client: SISABClient, lote: LoteSISAB):
        mock_post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            with pytest.raises(TimeoutSISABError):
                await client.enviar_lote(lote)

        assert mock_post.call_count == client.max_retries

    async def test_enviar_lote_conerror_retry_exausto(self, client: SISABClient, lote: LoteSISAB):
        mock_post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            with pytest.raises(TimeoutSISABError):
                await client.enviar_lote(lote)

    async def test_enviar_lote_http_500_retry(self, client: SISABClient, lote: LoteSISAB):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_post = AsyncMock(return_value=mock_response)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            with pytest.raises(TimeoutSISABError):
                await client.enviar_lote(lote)

        assert mock_post.call_count == client.max_retries

    async def test_enviar_lote_http_422_sem_retry(self, client: SISABClient, lote: LoteSISAB):
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unprocessable", request=MagicMock(), response=mock_response
        )
        mock_post = AsyncMock(return_value=mock_response)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            with pytest.raises(Exception):
                await client.enviar_lote(lote)

        assert mock_post.call_count == 1

    def test_validar_lote_valido(self, client: SISABClient, lote: LoteSISAB):
        client._validar_lote(lote)

    def test_validar_lote_vazio_raise(self, client: SISABClient):
        lote_vazio = _lote_valido(fichas=[])
        with pytest.raises(LoteInvalidoError):
            client._validar_lote(lote_vazio)

    def test_validar_lote_sem_ciap_e_cid_raise(self, client: SISABClient):
        ficha = _ficha_valida(ciap2=None, cid10=None)
        lote = _lote_valido(fichas=[ficha])
        with pytest.raises(LoteInvalidoError):
            client._validar_lote(lote)

    def test_backoff_nao_excede_maximo(self):
        async def _test():
            t0 = time.time()
            await SISABClient._backoff(10, base=1.0, maximo=5.0)
            elapsed = time.time() - t0
            assert elapsed < 10.0
        asyncio.run(_test())

    async def test_close_client(self, client: SISABClient):
        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        client._client = mock_client

        await client.close()
        mock_client.aclose.assert_awaited_once()

    async def test_context_manager(self):
        with patch("app.services.sisab_client.httpx.AsyncClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.is_closed = False
            mock_instance.aclose = AsyncMock()
            MockClient.return_value = mock_instance

            async with SISABClient(base_url="https://apisus.gov.br") as client:
                assert client._client is not None

            mock_instance.aclose.assert_awaited_once()


class TestValidadores:
    """Testes dos validadores utilizados pelo SISABClient."""

    def test_validar_ficha_com_ciap(self, client: SISABClient):
        ficha = _ficha_valida()
        lote = _lote_valido(fichas=[ficha])
        client._validar_lote(lote)

    def test_validar_ficha_com_cid10(self, client: SISABClient):
        ficha = _ficha_valida(ciap2=None, cid10="I10")
        lote = _lote_valido(fichas=[ficha])
        client._validar_lote(lote)

    def test_validar_ficha_sem_ciap_cid_raise(self, client: SISABClient):
        ficha = _ficha_valida(ciap2=None, cid10=None)
        lote = _lote_valido(fichas=[ficha])
        with pytest.raises(LoteInvalidoError):
            client._validar_lote(lote)


