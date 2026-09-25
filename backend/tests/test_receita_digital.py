# Arquivo: backend/tests/test_receita_digital.py
"""Testes do Serviço de Validação Criptográfica da Receita Digital (C2).

Cobre: serialização canônica, hash SHA-256, assinatura HMAC-SHA256,
detecção de adulteração de dosagens/medicamentos, validação do documento
emitido e conferência da dispensação farmacêutica.

Conformidade: Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0,
padrões SUS/APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF) e
cobertura de testes automatizados com pytest.
"""

from __future__ import annotations

import base64
import hashlib
import json
import unicodedata
from datetime import datetime, timedelta, timezone

import pytest

from app.models.receita import Medicamento, ReceitaDigital
from app.services.receita_digital import (
    ALGORITMO_ASSINATURA,
    VARIAVEL_AMBIENTE_CHAVE,
    AssinadorReceitaDigital,
    AssinaturaInvalidaError,
    DispensacaoInvalidaError,
    HashInvalidoError,
    PrescricaoInvalidaError,
    gerar_hash_prescricao,
    serializar_canonico,
    validar_documento_emitido,
    verificar_dispensacao,
)

CHAVE_TESTE: bytes = b"chave-hmac-teste-projeto-media-32b"
CNS_VALIDO: str = "110433218196000"
CPF_VALIDO: str = "52998224725"
DATA_EMISSAO_FIXA: datetime = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
CAMPOS_METADADOS: tuple[str, ...] = (
    "hash_assinatura",
    "assinatura",
    "algoritmo_assinatura",
    "data_assinatura",
)


def _prescricao(**substituicoes: object) -> ReceitaDigital:
    dados: dict[str, object] = {
        "cns_paciente": CNS_VALIDO,
        "cpf_paciente": CPF_VALIDO,
        "cid10": "J00",
        "ciap2": "R74",
        "data_emissao": DATA_EMISSAO_FIXA,
        "medicamentos": [
            Medicamento(
                nome="Amoxicilina", dosagem="500mg", frequencia="8/8h", quantidade=10
            ),
            Medicamento(
                nome="Paracetamol", dosagem="750mg", frequencia="6/6h", quantidade=20
            ),
        ],
        "observacoes": "Tomar conforme orientação médica.",
    }
    dados.update(substituicoes)
    return ReceitaDigital.model_validate(dados)


def _adulterar(receita: ReceitaDigital, campo: str, valor: object) -> ReceitaDigital:
    return receita.model_copy(update={campo: valor})


def _item_dispensado(**substituicoes: object) -> Medicamento:
    dados: dict[str, object] = {
        "nome": "Amoxicilina",
        "dosagem": "500mg",
        "frequencia": "8/8h",
        "quantidade": 10,
    }
    dados.update(substituicoes)
    return Medicamento.model_validate(dados)


@pytest.fixture
def prescricao_valida() -> ReceitaDigital:
    return _prescricao()


@pytest.fixture
def prescricao_vazia() -> ReceitaDigital:
    return _prescricao(medicamentos=[])


@pytest.fixture
def assinador() -> AssinadorReceitaDigital:
    return AssinadorReceitaDigital(CHAVE_TESTE)


@pytest.fixture
def receita_assinada(
    assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
) -> ReceitaDigital:
    return assinador.assinar(prescricao_valida)


class TestSerializacaoCanonica:
    def test_chaves_ordenadas_e_separadores_compactos(
        self, prescricao_valida: ReceitaDigital
    ) -> None:
        canonic = serializar_canonico(prescricao_valida)
        payload = json.loads(canonic)
        assert list(payload) == sorted(payload)
        assert ", " not in canonic and '": ' not in canonic

    def test_exclui_metadados_de_integridade(self, receita_assinada: ReceitaDigital) -> None:
        payload = json.loads(serializar_canonico(receita_assinada))
        for campo in CAMPOS_METADADOS:
            assert campo not in payload
        assert "cns_paciente" in payload and "medicamentos" in payload

    def test_normalizacao_unicode_nfc(self) -> None:
        decomposto = unicodedata.normalize("NFD", "Dipirona sódica")
        receita_decomposta = _prescricao(
            medicamentos=[
                Medicamento(nome=decomposto, dosagem="500mg", frequencia="6/6h", quantidade=2)
            ]
        )
        receita_composta = _prescricao(
            medicamentos=[
                Medicamento(
                    nome="Dipirona sódica", dosagem="500mg", frequencia="6/6h", quantidade=2
                )
            ]
        )
        assert unicodedata.normalize("NFC", decomposto) != decomposto
        assert serializar_canonico(receita_decomposta) == serializar_canonico(receita_composta)
        assert gerar_hash_prescricao(receita_decomposta) == gerar_hash_prescricao(
            receita_composta
        )

    def test_datetime_normalizado_em_utc(self) -> None:
        naive = _prescricao(data_emissao=datetime(2026, 9, 25, 9, 0, 0))
        utc = _prescricao(data_emissao=DATA_EMISSAO_FIXA)
        brasilia = _prescricao(
            data_emissao=datetime(2026, 9, 25, 9, 0, 0, tzinfo=timezone(timedelta(hours=-3)))
        )
        canonic = serializar_canonico(naive)
        assert serializar_canonico(utc) == canonic
        assert serializar_canonico(brasilia) == canonic
        assert canonic.count("2026-09-25T12:00:00+00:00") == 1

    def test_ordem_da_lista_de_medicamentos_preservada(
        self, prescricao_valida: ReceitaDigital
    ) -> None:
        invertida = _prescricao(medicamentos=list(reversed(prescricao_valida.medicamentos)))
        assert serializar_canonico(prescricao_valida) != serializar_canonico(invertida)


class TestGeracaoHashPrescricao:
    def test_hash_deterministico_e_hexadecimal(self, prescricao_valida: ReceitaDigital) -> None:
        hash_1 = gerar_hash_prescricao(prescricao_valida)
        hash_2 = gerar_hash_prescricao(prescricao_valida)
        assert len(hash_1) == 64
        assert all(c in "0123456789abcdef" for c in hash_1)
        assert hash_1 == hash_2

    def test_hash_confere_com_sha256_manual(self, prescricao_valida: ReceitaDigital) -> None:
        esperado = hashlib.sha256(
            serializar_canonico(prescricao_valida).encode("utf-8")
        ).hexdigest()
        assert gerar_hash_prescricao(prescricao_valida) == esperado

    @pytest.mark.parametrize(
        ("campo", "valor"),
        [
            ("observacoes", "Nova observação"),
            ("cns_paciente", "213389083863796"),
            ("cpf_paciente", "11144477735"),
            ("cid10", "J45"),
            ("ciap2", "R95"),
        ],
    )
    def test_hash_sensivel_ao_conteudo_clinico(
        self, prescricao_valida: ReceitaDigital, campo: str, valor: str
    ) -> None:
        original = gerar_hash_prescricao(prescricao_valida)
        assert gerar_hash_prescricao(_adulterar(prescricao_valida, campo, valor)) != original

    @pytest.mark.parametrize(
        ("campo", "valor"),
        [
            ("dosagem", "5000mg"),
            ("nome", "Amoxicilina Sódica"),
            ("quantidade", 100),
            ("frequencia", "4/4h"),
        ],
    )
    def test_hash_sensivel_a_medicamentos(
        self, prescricao_valida: ReceitaDigital, campo: str, valor: object
    ) -> None:
        medicamentos = list(prescricao_valida.medicamentos)
        medicamentos[0] = medicamentos[0].model_copy(update={campo: valor})
        alterada = prescricao_valida.model_copy(update={"medicamentos": medicamentos})
        assert gerar_hash_prescricao(alterada) != gerar_hash_prescricao(prescricao_valida)

    def test_hash_imutavel_apos_assinatura(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        antes = gerar_hash_prescricao(prescricao_valida)
        assinada = assinador.assinar(prescricao_valida)
        assert gerar_hash_prescricao(assinada) == antes
        assert assinada.hash_assinatura == antes

    def test_prescricao_sem_medicamentos_rejeitada(
        self, prescricao_vazia: ReceitaDigital
    ) -> None:
        with pytest.raises(PrescricaoInvalidaError, match="medicamento"):
            gerar_hash_prescricao(prescricao_vazia)


class TestAssinaturaDigital:
    def test_assinar_preenche_metadados_de_integridade(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        assinada = assinador.assinar(prescricao_valida)
        assert assinada.hash_assinatura == gerar_hash_prescricao(prescricao_valida)
        assert assinada.algoritmo_assinatura == ALGORITMO_ASSINATURA
        assert assinada.data_assinatura is not None
        assert len(base64.b64decode(assinada.assinatura or "", validate=True)) == 32

    def test_assinar_nao_modifica_original(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        antes = prescricao_valida.model_dump()
        assinador.assinar(prescricao_valida)
        assert prescricao_valida.model_dump() == antes

    def test_assinatura_deterministica_por_conteudo(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        primeira = assinador.assinar(prescricao_valida)
        segunda = assinador.assinar(prescricao_valida)
        assert primeira.assinatura == segunda.assinatura
        assert primeira.hash_assinatura == segunda.hash_assinatura

    def test_chaves_diferentes_geram_assinaturas_diferentes(
        self, prescricao_valida: ReceitaDigital
    ) -> None:
        uma = AssinadorReceitaDigital(b"chave-valida-unidade-basica-01").assinar(prescricao_valida)
        outra = AssinadorReceitaDigital(b"chave-valida-unidade-basica-02").assinar(
            prescricao_valida
        )
        assert uma.assinatura != outra.assinatura

    def test_chave_id_deterministica_e_publica(self) -> None:
        assert AssinadorReceitaDigital(CHAVE_TESTE).chave_id == AssinadorReceitaDigital(
            CHAVE_TESTE
        ).chave_id
        assert len(AssinadorReceitaDigital(CHAVE_TESTE).chave_id) == 16
        assert AssinadorReceitaDigital(CHAVE_TESTE).chave_id != AssinadorReceitaDigital(
            b"outra-chave-valida-de-32-bytes!!"
        ).chave_id

    def test_gerar_chave_produz_chaves_aleatorias(self) -> None:
        chave_1 = AssinadorReceitaDigital.gerar_chave()
        chave_2 = AssinadorReceitaDigital.gerar_chave()
        assert len(chave_1) == 32
        assert chave_1 != chave_2

    def test_chave_curta_ou_nao_bytes_rejeitada(self) -> None:
        with pytest.raises(ValueError):
            AssinadorReceitaDigital(b"curta")
        with pytest.raises(TypeError):
            AssinadorReceitaDigital(12345)  # type: ignore[arg-type]

    def test_assinar_prescricao_sem_medicamentos(
        self, assinador: AssinadorReceitaDigital, prescricao_vazia: ReceitaDigital
    ) -> None:
        with pytest.raises(PrescricaoInvalidaError, match="medicamento"):
            assinador.assinar(prescricao_vazia)

    def test_data_assinatura_registrada_em_utc(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        assinada = assinador.assinar(prescricao_valida)
        assert assinada.data_assinatura is not None
        assert assinada.data_assinatura.tzinfo is not None
        assert assinada.data_assinatura.utcoffset() == timedelta(0)


class TestVerificacaoIntegridade:
    def test_receita_integra_e_valida(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        assert assinador.verificar(receita_assinada) is True
        assert validar_documento_emitido(receita_assinada, chave=CHAVE_TESTE) is True

    @pytest.mark.parametrize(
        ("campo", "valor"),
        [
            ("dosagem", "5000mg"),
            ("nome", "Omeprazol"),
            ("frequencia", "12/12h"),
            ("quantidade", 999),
        ],
    )
    def test_adulteracao_de_medicamento_e_detectada(
        self,
        assinador: AssinadorReceitaDigital,
        receita_assinada: ReceitaDigital,
        campo: str,
        valor: object,
    ) -> None:
        medicamentos = list(receita_assinada.medicamentos)
        medicamentos[0] = medicamentos[0].model_copy(update={campo: valor})
        adulterada = receita_assinada.model_copy(update={"medicamentos": medicamentos})
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(adulterada)

    @pytest.mark.parametrize(
        ("campo", "valor"),
        [
            ("cns_paciente", "213389083863796"),
            ("cpf_paciente", "11144477735"),
            ("cid10", "J45"),
            ("ciap2", "R95"),
            ("observacoes", "Texto alterado após a emissão."),
        ],
    )
    def test_adulteracao_de_dados_clinicos_e_detectada(
        self,
        assinador: AssinadorReceitaDigital,
        receita_assinada: ReceitaDigital,
        campo: str,
        valor: str,
    ) -> None:
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(_adulterar(receita_assinada, campo, valor))

    def test_adulteracao_com_hash_recalculado_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        medicamentos = list(receita_assinada.medicamentos)
        medicamentos[0] = medicamentos[0].model_copy(update={"dosagem": "5000mg"})
        sem_hash = receita_assinada.model_copy(update={"medicamentos": medicamentos})
        falsificada = sem_hash.model_copy(
            update={"hash_assinatura": gerar_hash_prescricao(sem_hash)}
        )
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(falsificada)

    def test_troca_de_medicamento_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        medicamentos = list(receita_assinada.medicamentos)
        medicamentos[0] = Medicamento(
            nome="Diazepam", dosagem="10mg", frequencia="8/8h", quantidade=10
        )
        trocada = receita_assinada.model_copy(update={"medicamentos": medicamentos})
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(trocada)

    def test_chave_deoutra_unidade_e_detectada(self, receita_assinada: ReceitaDigital) -> None:
        outro = AssinadorReceitaDigital(b"chave-de-outra-unidade-32bytes")
        with pytest.raises(AssinaturaInvalidaError):
            outro.verificar(receita_assinada)

    def test_assinatura_corrompida_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        corrompida = _adulterar(receita_assinada, "assinatura", "###nao-base64###")
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(corrompida)

    def test_algoritmo_desconhecido_e_rejeitado(self, receita_assinada: ReceitaDigital) -> None:
        receita = _adulterar(receita_assinada, "algoritmo_assinatura", "MD5")
        with pytest.raises(AssinaturaInvalidaError) as exc_info:
            validar_documento_emitido(receita, chave=CHAVE_TESTE)
        assert "algoritmo" in str(exc_info.value).lower()

    def test_hash_adulterado_e_detectado(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        receita = _adulterar(receita_assinada, "hash_assinatura", "a" * 64)
        with pytest.raises(HashInvalidoError):
            assinador.verificar(receita)

    def test_hash_malformado_e_detectado(self, receita_assinada: ReceitaDigital) -> None:
        receita = _adulterar(receita_assinada, "hash_assinatura", "nao-e-hash")
        with pytest.raises(PrescricaoInvalidaError):
            validar_documento_emitido(receita, chave=CHAVE_TESTE)

    def test_receita_nao_assinada_e_rejeitada(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        with pytest.raises(PrescricaoInvalidaError, match="assinada"):
            assinador.verificar(prescricao_valida)

    def test_prescricao_sem_medicamentos_e_rejeitada(
        self, assinador: AssinadorReceitaDigital, prescricao_vazia: ReceitaDigital
    ) -> None:
        with pytest.raises(PrescricaoInvalidaError, match="medicamentos"):
            assinador.verificar(prescricao_vazia)

    def test_hierarquia_de_excecoes(self) -> None:
        assert issubclass(HashInvalidoError, PrescricaoInvalidaError)
        assert issubclass(AssinaturaInvalidaError, PrescricaoInvalidaError)
        assert issubclass(DispensacaoInvalidaError, PrescricaoInvalidaError)

    def test_receita_integra_apos_roundtrip_json(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        transportada = ReceitaDigital.model_validate_json(
            receita_assinada.model_dump_json()
        )
        assert assinador.verificar(transportada) is True
        assert transportada.hash_assinatura == receita_assinada.hash_assinatura

    def test_roundtrip_json_de_dosagem_adulterada_e_detectado(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        payload = json.loads(receita_assinada.model_dump_json())
        payload["medicamentos"][0]["dosagem"] = "5000mg"
        adulterada = ReceitaDigital.model_validate(payload)
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(adulterada)


class TestValidacaoDocumentoEmitido:
    def test_chave_explicita_em_texto(self, receita_assinada: ReceitaDigital) -> None:
        assert validar_documento_emitido(receita_assinada, chave=CHAVE_TESTE.decode("ascii"))

    def test_chave_via_variavel_de_ambiente(
        self, receita_assinada: ReceitaDigital, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(VARIAVEL_AMBIENTE_CHAVE, CHAVE_TESTE.decode("ascii"))
        assert validar_documento_emitido(receita_assinada) is True

    def test_chave_ausente_gera_runtime_error(
        self, receita_assinada: ReceitaDigital, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(VARIAVEL_AMBIENTE_CHAVE, raising=False)
        with pytest.raises(RuntimeError, match=VARIAVEL_AMBIENTE_CHAVE):
            validar_documento_emitido(receita_assinada)

    def test_documento_adulterado_e_rejeitado(
        self, receita_assinada: ReceitaDigital
    ) -> None:
        adulterada = _adulterar(receita_assinada, "observacoes", " trocada ")
        with pytest.raises(PrescricaoInvalidaError):
            validar_documento_emitido(adulterada, chave=CHAVE_TESTE)


class TestVerificacaoDispensacao:
    def test_dispensacao_conforme_e_aceita(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        itens = [
            _item_dispensado(),
            _item_dispensado(
                nome="Paracetamol", dosagem="750mg", frequencia="6/6h", quantidade=20
            ),
        ]
        assert assinador.verificar_dispensacao(receita_assinada, itens) is True
        assert verificar_dispensacao(receita_assinada, itens, assinador) is True

    def test_dispensacao_fracionada_dentro_do_autorizado(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        itens = [_item_dispensado(quantidade=4), _item_dispensado(quantidade=6)]
        assert assinador.verificar_dispensacao(receita_assinada, itens) is True

    @pytest.mark.parametrize(
        ("campo", "valor"),
        [
            ("dosagem", "5000mg"),
            ("nome", "Omeprazol"),
            ("frequencia", "12/12h"),
        ],
    )
    def test_medicamento_dispensado_divergente_e_detectado(
        self,
        assinador: AssinadorReceitaDigital,
        receita_assinada: ReceitaDigital,
        campo: str,
        valor: str,
    ) -> None:
        with pytest.raises(DispensacaoInvalidaError):
            assinador.verificar_dispensacao(
                receita_assinada, [_item_dispensado(**{campo: valor})]
            )

    def test_quantidade_acima_da_prescrita_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        with pytest.raises(DispensacaoInvalidaError, match="excede"):
            verificar_dispensacao(
                receita_assinada, [_item_dispensado(quantidade=11)], assinador
            )

    def test_soma_de_baixas_fracionadas_excedentes_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        itens = [_item_dispensado(quantidade=6), _item_dispensado(quantidade=5)]
        with pytest.raises(DispensacaoInvalidaError):
            assinador.verificar_dispensacao(receita_assinada, itens)

    def test_dispensacao_vazia_e_rejeitada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        with pytest.raises(DispensacaoInvalidaError):
            assinador.verificar_dispensacao(receita_assinada, [])

    def test_receita_adulterada_bloqueia_dispensacao(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        medicamentos = list(receita_assinada.medicamentos)
        medicamentos[0] = medicamentos[0].model_copy(update={"dosagem": "5000mg"})
        adulterada = receita_assinada.model_copy(update={"medicamentos": medicamentos})
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar_dispensacao(adulterada, [_item_dispensado()])

    def test_receita_nao_assinada_bloqueia_dispensacao(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        with pytest.raises(PrescricaoInvalidaError, match="assinada"):
            assinador.verificar_dispensacao(prescricao_valida, [_item_dispensado()])

    def test_normalizacao_de_texto_na_dispensacao(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        nome_decomposto = unicodedata.normalize("NFD", "  AMOXICILINA  ")
        assert (
            assinador.verificar_dispensacao(
                receita_assinada, [_item_dispensado(nome=nome_decomposto)]
            )
            is True
        )


class TestSuperficiePublica:
    def test_all_expoe_o_ciclo_criptografico(self) -> None:
        import app.services.receita_digital as modulo

        assert set(modulo.__all__) >= {
            "serializar_canonico",
            "gerar_hash_prescricao",
            "AssinadorReceitaDigital",
            "validar_documento_emitido",
            "verificar_dispensacao",
        }
        for nome in modulo.__all__:
            assert hasattr(modulo, nome)
