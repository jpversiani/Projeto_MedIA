# Arquivo: backend/tests/test_receita_digital.py
"""
Testes unitários do Serviço de Validação Criptográfica da Receita Digital (C18).

Cobre:
1. Serialização JSON canônica determinística (chaves ordenadas, NFC, UTC).
2. Geração do hash SHA-256 canônico da prescrição (integridade do conteúdo).
3. Assinatura digital HMAC-SHA256 e metadados de integridade.
4. Verificação e detecção de adulteração de dosagens, medicamentos e
   quantidades dispensadas após a emissão.

Conformidade com:
- Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0.
- Padrões SUS/APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF).
- Cobertura de testes automatizados com pytest.
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
    HashInvalidoError,
    PrescricaoInvalidaError,
    gerar_hash_prescricao,
    serializar_canonico,
    validar_documento_emitido,
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
    """Cria uma prescrição clínica válida com dados SUS fixos."""
    dados: dict[str, object] = {
        "cns_paciente": CNS_VALIDO,
        "cpf_paciente": CPF_VALIDO,
        "cid10": "J00",
        "ciap2": "R74",
        "data_emissao": DATA_EMISSAO_FIXA,
        "medicamentos": [
            Medicamento(
                nome="Amoxicilina",
                dosagem="500mg",
                frequencia="8/8h",
                quantidade=10,
            ),
            Medicamento(
                nome="Paracetamol",
                dosagem="750mg",
                frequencia="6/6h",
                quantidade=20,
            ),
        ],
        "observacoes": "Tomar conforme orientação médica.",
    }
    dados.update(substituicoes)
    return ReceitaDigital.model_validate(dados)


def _substituir_medicamento(
    prescricao: ReceitaDigital, indice: int, **substituicoes: object
) -> Medicamento:
    medicamento = prescricao.medicamentos[indice]
    return medicamento.model_copy(update=substituicoes)


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


def _adulterar(receita: ReceitaDigital, campo: str, valor: object) -> ReceitaDigital:
    """Simula adulteração do conteúdo clínico preservando hash e assinatura."""
    return receita.model_copy(update={campo: valor})


# ----------------------------------------------------------------------
# Serialização JSON canônica
# ----------------------------------------------------------------------


class TestSerializacaoCanonica:
    """A serialização canônica deve ser determinística e excluir metadados."""

    def test_chaves_ordenadas_e_separadores_compactos(self, prescricao_valida: ReceitaDigital) -> None:
        canonic_json = serializar_canonico(prescricao_valida)
        payload = json.loads(canonic_json)
        assert list(payload) == sorted(payload)
        assert ", " not in canonic_json and '": ' not in canonic_json

    def test_exclui_metadados_de_integridade(self, receita_assinada: ReceitaDigital) -> None:
        canonic_json = serializar_canonico(receita_assinada)
        payload = json.loads(canonic_json)
        for campo in CAMPOS_METADADOS:
            assert campo not in payload
        assert "cns_paciente" in payload and "medicamentos" in payload

    def test_normalizacao_unicode_nfc(self) -> None:
        nome_decomposto = unicodedata.normalize("NFD", "Dipirona sódica")
        receita_decomposta = _prescricao(
            medicamentos=[Medicamento(nome=nome_decomposto, dosagem="500mg", frequencia="6/6h", quantidade=2)]
        )
        receita_composta = _prescricao(
            medicamentos=[Medicamento(nome="Dipirona sódica", dosagem="500mg", frequencia="6/6h", quantidade=2)]
        )
        assert unicodedata.normalize("NFC", nome_decomposto) != nome_decomposto
        assert serializar_canonico(receita_decomposta) == serializar_canonico(receita_composta)
        assert gerar_hash_prescricao(receita_decomposta) == gerar_hash_prescricao(receita_composta)

    def test_datetime_normalizado_em_utc(self) -> None:
        receita_naive = _prescricao(data_emissao=datetime(2026, 9, 25, 9, 0, 0))
        receita_utc = _prescricao(data_emissao=datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc))
        receita_fuso = _prescricao(
            data_emissao=datetime(2026, 9, 25, 9, 0, 0, tzinfo=timezone(timedelta(hours=-3)))
        )
        canonic = serializar_canonico(receita_naive)
        assert serializar_canonico(receita_utc) == canonic
        assert serializar_canonico(receita_fuso) == canonic
        assert canonic.count("2026-09-25T12:00:00+00:00") == 1

    def test_ordem_da_lista_de_medicamentos_e_preservada(self, prescricao_valida: ReceitaDigital) -> None:
        invertida = _prescricao(
            medicamentos=list(reversed(prescricao_valida.medicamentos))
        )
        assert serializar_canonico(prescricao_valida) != serializar_canonico(invertida)


# ----------------------------------------------------------------------
# Geração do hash SHA-256 canônico
# ----------------------------------------------------------------------


class TestGeracaoHashPrescricao:
    """Testes para a geração do hash SHA-256 canônico da prescrição."""

    def test_geracao_hash_prescricao(self, prescricao_valida: ReceitaDigital) -> None:
        """Hash é SHA-256 válido (64 hex minúsculos) e determinístico."""
        hash1 = gerar_hash_prescricao(prescricao_valida)
        hash2 = gerar_hash_prescricao(prescricao_valida)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)
        assert hash1 == hash2

    def test_hash_consistente_com_sha256_manual(self, prescricao_valida: ReceitaDigital) -> None:
        """O hash corresponde ao SHA-256 manual sobre o JSON canônico."""
        esperado = hashlib.sha256(
            serializar_canonico(prescricao_valida).encode("utf-8")
        ).hexdigest()
        assert gerar_hash_prescricao(prescricao_valida) == esperado

    def test_hash_muda_com_dados_diferentes(self, prescricao_valida: ReceitaDigital) -> None:
        """Alterações no conteúdo clínico alteram o hash."""
        hash_original = gerar_hash_prescricao(prescricao_valida)
        modificada = prescricao_valida.model_copy(update={"observacoes": "Nova observação"})
        assert hash_original != gerar_hash_prescricao(modificada)

    def test_hash_sensivel_a_dosagem_e_medicamentos(self, prescricao_valida: ReceitaDigital) -> None:
        """Cada campo clínico relevante altera o hash (dosagem, nome, quantidade, frequência)."""
        hash_original = gerar_hash_prescricao(prescricao_valida)
        cenarios = [
            {"medicamentos": [_substituir_medicamento(prescricao_valida, 0, dosagem="5000mg")] + prescricao_valida.medicamentos[1:]},
            {"medicamentos": [_substituir_medicamento(prescricao_valida, 0, nome="Amoxicilina Sódica")] + prescricao_valida.medicamentos[1:]},
            {"medicamentos": [_substituir_medicamento(prescricao_valida, 0, quantidade=100)] + prescricao_valida.medicamentos[1:]},
            {"medicamentos": [_substituir_medicamento(prescricao_valida, 0, frequencia="4/4h")] + prescricao_valida.medicamentos[1:]},
        ]
        for cenario in cenarios:
            assert hash_original != gerar_hash_prescricao(prescricao_valida.model_copy(update=cenario))

    def test_hash_imutavel_apos_assinatura(self, prescricao_valida: ReceitaDigital, assinador: AssinadorReceitaDigital) -> None:
        """Metadados de integridade não alteram o hash canônico do conteúdo."""
        hash_antes = gerar_hash_prescricao(prescricao_valida)
        assinada = assinador.assinar(prescricao_valida)
        assert gerar_hash_prescricao(assinada) == hash_antes
        assert assinada.hash_assinatura == hash_antes

    def test_prescricao_vazia_nao_gera_hash(self, prescricao_vazia: ReceitaDigital) -> None:
        """Prescrição sem medicamentos deve ser rejeitada na geração do hash."""
        with pytest.raises(PrescricaoInvalidaError) as exc_info:
            gerar_hash_prescricao(prescricao_vazia)
        assert "medicamento" in str(exc_info.value).lower()


# ----------------------------------------------------------------------
# Assinatura digital (HMAC-SHA256)
# ----------------------------------------------------------------------


class TestAssinaturaDigital:
    """Testes para a assinatura digital da receita emitida."""

    def test_assinar_preenche_metadados_de_integridade(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        assinada = assinador.assinar(prescricao_valida)
        assert assinada.hash_assinatura == gerar_hash_prescricao(prescricao_valida)
        assert assinada.algoritmo_assinatura == ALGORITMO_ASSINATURA
        assert assinada.data_assinatura is not None
        base64.b64decode(assinada.assinatura or "", validate=True)
        assert len(base64.b64decode(assinada.assinatura or "")) == 32

    def test_assinar_nao_modifica_original(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        antes = prescricao_valida.model_dump()
        assinador.assinar(prescricao_valida)
        assert prescricao_valida.model_dump() == antes

    def test_assinatura_deterministica_por_conteudo(
        self, assinador: AssinadorReceitaDigital, prescricao_valida: ReceitaDigital
    ) -> None:
        assinada_1 = assinador.assinar(prescricao_valida)
        assinada_2 = assinador.assinar(prescricao_valida)
        assert assinada_1.assinatura == assinada_2.assinatura
        assert assinada_1.hash_assinatura == assinada_2.hash_assinatura

    def test_chaves_diferentes_geram_assinaturas_diferentes(
        self, prescricao_valida: ReceitaDigital
    ) -> None:
        assinada_1 = AssinadorReceitaDigital(b"chave-valida-unidade-basica-01").assinar(prescricao_valida)
        assinada_2 = AssinadorReceitaDigital(b"chave-valida-unidade-basica-02").assinar(prescricao_valida)
        assert assinada_1.assinatura != assinada_2.assinatura

    def test_chave_id_deterministica(self) -> None:
        assert AssinadorReceitaDigital(CHAVE_TESTE).chave_id == AssinadorReceitaDigital(CHAVE_TESTE).chave_id
        assert len(AssinadorReceitaDigital(CHAVE_TESTE).chave_id) == 16
        assert AssinadorReceitaDigital(CHAVE_TESTE).chave_id != AssinadorReceitaDigital(
            b"outra-chave-valida-de-32-bytes!!"
        ).chave_id

    def test_gerar_chave_produz_chave_aleatoria(self) -> None:
        chave_1 = AssinadorReceitaDigital.gerar_chave()
        chave_2 = AssinadorReceitaDigital.gerar_chave()
        assert len(chave_1) == 32
        assert chave_1 != chave_2

    def test_chave_fraca_ou_invalida_gera_erro(self) -> None:
        with pytest.raises(ValueError):
            AssinadorReceitaDigital(b"curta")
        with pytest.raises(TypeError):
            AssinadorReceitaDigital(12345)  # type: ignore[arg-type]

    def test_assinar_prescricao_sem_medicamentos(
        self, assinador: AssinadorReceitaDigital, prescricao_vazia: ReceitaDigital
    ) -> None:
        with pytest.raises(PrescricaoInvalidaError) as exc_info:
            assinador.assinar(prescricao_vazia)
        assert "medicamento" in str(exc_info.value).lower()


# ----------------------------------------------------------------------
# Verificação de integridade (detecção de adulteração)
# ----------------------------------------------------------------------


class TestVerificacaoIntegridade:
    """Verificação contra adulteração de dosagens ou medicamentos dispensados."""

    def test_receita_integra_passa_na_verificacao(
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
        receita_adulterada = receita_assinada.model_copy(update={"medicamentos": medicamentos})
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(receita_adulterada)

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
        valor: object,
    ) -> None:
        receita_adulterada = _adulterar(receita_assinada, campo, valor)
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(receita_adulterada)

    def test_troca_de_medicamento_dispensado_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        medicamentos = list(receita_assinada.medicamentos)
        medicamentos[0] = Medicamento(
            nome="Diazepam", dosagem="10mg", frequencia="8/8h", quantidade=10
        )
        receita_trocada = receita_assinada.model_copy(update={"medicamentos": medicamentos})
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(receita_trocada)

    def test_adulteracao_de_dosagem_com_hash_recalculado_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        """Atacante altera dosagem e recalcula o hash, mas não possui a chave."""
        medicamentos = list(receita_assinada.medicamentos)
        medicamentos[0] = medicamentos[0].model_copy(update={"dosagem": "500mg -> 5000mg"})
        receita_falsificada = receita_assinada.model_copy(
            update={
                "medicamentos": medicamentos,
                "hash_assinatura": gerar_hash_prescricao(
                    receita_assinada.model_copy(update={"medicamentos": medicamentos})
                ),
            }
        )
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(receita_falsificada)

    def test_chave_incorreta_e_detectada(
        self, receita_assinada: ReceitaDigital
    ) -> None:
        outro_assinador = AssinadorReceitaDigital(b"chave-de-outra-unidade-32bytes")
        with pytest.raises(AssinaturaInvalidaError):
            outro_assinador.verificar(receita_assinada)

    def test_assinatura_corrompida_e_detectada(
        self, assinador: AssinadorReceitaDigital, receita_assinada: ReceitaDigital
    ) -> None:
        receita_corrompida = _adulterar(receita_assinada, "assinatura", "###nao-base64###")
        with pytest.raises(AssinaturaInvalidaError):
            assinador.verificar(receita_corrompida)

    def test_algoritmo_desconhecido_e_rejeitado(
        self, receita_assinada: ReceitaDigital
    ) -> None:
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


# ----------------------------------------------------------------------
# Validação do documento emitido
# ----------------------------------------------------------------------


class TestValidacaoDocumentoEmitido:
    """Contrato de validação do documento emitido pelo PEC."""

    def test_validacao_documento_emitido(self, receita_assinada: ReceitaDigital) -> None:
        assert validar_documento_emitido(receita_assinada, chave=CHAVE_TESTE) is True

    def test_validacao_documento_invalido(self, receita_assinada: ReceitaDigital) -> None:
        adulterada = _adulterar(receita_assinada, "hash_assinatura", "hash_invalido")
        with pytest.raises(PrescricaoInvalidaError):
            validar_documento_emitido(adulterada, chave=CHAVE_TESTE)

    def test_validacao_documento_sem_assinatura(self, prescricao_valida: ReceitaDigital) -> None:
        with pytest.raises(PrescricaoInvalidaError) as exc_info:
            validar_documento_emitido(prescricao_valida, chave=CHAVE_TESTE)
        assert "assinada" in str(exc_info.value).lower()

    def test_prescricao_sem_medicamentos(self, prescricao_vazia: ReceitaDigital) -> None:
        with pytest.raises(PrescricaoInvalidaError) as exc_info:
            validar_documento_emitido(prescricao_vazia, chave=CHAVE_TESTE)
        assert "medicamentos" in str(exc_info.value).lower()

    def test_prescricao_com_medicamentos_aceita(
        self, receita_assinada: ReceitaDigital
    ) -> None:
        validar_documento_emitido(receita_assinada, chave=CHAVE_TESTE)

    def test_erros_de_integridade_sao_prescricao_invalida(
        self, receita_assinada: ReceitaDigital
    ) -> None:
        assert issubclass(HashInvalidoError, PrescricaoInvalidaError)
        assert issubclass(AssinaturaInvalidaError, PrescricaoInvalidaError)

    def test_chave_via_variavel_de_ambiente(
        self, receita_assinada: ReceitaDigital, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(VARIAVEL_AMBIENTE_CHAVE, CHAVE_TESTE.decode("ascii"))
        assert validar_documento_emitido(receita_assinada) is True

    def test_chave_ausente_gera_runtime_error(
        self, receita_assinada: ReceitaDigital, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(VARIAVEL_AMBIENTE_CHAVE, raising=False)
        with pytest.raises(RuntimeError) as exc_info:
            validar_documento_emitido(receita_assinada)
        assert VARIAVEL_AMBIENTE_CHAVE in str(exc_info.value)

    def test_chave_em_texto_e_aceita(self, receita_assinada: ReceitaDigital) -> None:
        assert (
            validar_documento_emitido(receita_assinada, chave=CHAVE_TESTE.decode("ascii"))
            is True
        )