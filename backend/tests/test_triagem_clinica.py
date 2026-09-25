# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para o motor de inferência de risco clínico Manchester Adaptado (C3).

Cobre:
1. Classificação de risco por MEWS para sinais vitais extremos
2. Avaliação de queixas sentinelas (dor torácica, dispneia grave)
3. Atribuição de prioridades (Vermelho, Laranja, Amarelo, Verde, Azul)
4. Recomendações CIAP-2 e CID-10
5. Geração de registros SOAP
6. Integração SUS/APS (CNS/CPF, métodos de validação)

Padrões de arquitetura:
- Python 3.12, tipagem estrita
- Pydantic v2 para validação
- Padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF)
- Teste unitário completo com pytest
"""

import pytest
from decimal import Decimal

from app.services.triagem_clinica import (
    NivelRisco,
    QueixaSentinela,
    CaracteristicasDorToracica,
    CaracteristicasDispneia,
    SinaisVitais,
    PacienteTriagem,
    ResultadoTriagem,
    evaluate_extreme_vitals,
    evaluate_sentinel_complaints,
    assign_priority_level,
)


# ---------------------------------------------------------------------------
# 1. Testes básicos da estrutura
# ---------------------------------------------------------------------------
class TestNivelRiscoEnum:
    """Testes para o enum NivelRisco."""

    def test_todos_niveis_existem(self):
        """Verifica que todos os níveis de risco estão definidos."""
        niveis = list(NivelRisco)
        assert len(niveis) == 5
        assert NivelRisco.VERMELHO in niveis
        assert NivelRisco.LARANJA in niveis
        assert NivelRisco.AMARELO in niveis
        assert NivelRisco.VERDE in niveis
        assert NivelRisco.AZUL in niveis

    def test_peso_ordem(self):
        """Verifica os pesos de ordem corretos."""
        assert NivelRisco.VERMELHO.peso_ordem == 1
        assert NivelRisco.LARANJA.peso_ordem == 2
        assert NivelRisco.AMARELO.peso_ordem == 3
        assert NivelRisco.VERDE.peso_ordem == 4
        assert NivelRisco.AZUL.peso_ordem == 5

    def test_tempo_maximo_espera(self):
        """Verifica os tempos máximos de espera."""
        assert NivelRisco.VERDE.tempo_maximo_espera_min == 120
        assert NivelRisco.AZUL.tempo_maximo_espera_min == 240
        assert NivelRisco.VERMELHO.tempo_maximo_espera_min == 60
        assert NivelRisco.LARANJA.tempo_maximo_espera_min == 60
        assert NivelRisco.AMARELO.tempo_maximo_espera_min == 60


class TestQueixaSentinelaEnum:
    """Testes para o enum QueixaSentinela."""

    def test_queixas_sentinelas_principais(self):
        """Verifica as principais queixas sentinelas."""
        assert QueixaSentinela.DOR_TORACICA == "DOR_TORACICA"
        assert QueixaSentinela.DISPNEIA == "DISPNEIA"

    def test_todas_queixas_sentinelas(self):
        """Verifica que todas as queixas sentinelas estão definidas."""
        queixas = [
            QueixaSentinela.DOR_TORACICA,
            QueixaSentinela.DISPNEIA,
            QueixaSentinela.DEFICIT_NEUROLOGICO,
            QueixaSentinela.SANGRAMENTO_GRAVE,
            QueixaSentinela.REACAO_ALERGICA,
            QueixaSentinela.CONVULSAO,
            QueixaSentinela.PERDA_CONSCIENCIA,
            QueixaSentinela.FEBRE_PERSISTENTE,
            QueixaSentinela.VOMITO_PERSISTENTE,
            QueixaSentinela.CEFALEIA_BRUSCA,
            QueixaSentinela.DOR_ABDOMINAL_INTENSA,
            QueixaSentinela.GESTACAO_COMPLICACAO,
        ]
        assert len(queixas) == 12


class TestCaracteristicasDorToracica:
    """Testes para a estrutura CaracteristicasDorToracica."""

    def test_caracteristicas_padrao(self):
        """Verifica as características padrão."""
        caracteristicas = CaracteristicasDorToracica()
        assert caracteristicas.em_aperto is False
        assert caracteristicas.irradia_braco_mandibula is False
        assert caracteristicas.sudorese is False
        assert caracteristicas.nausea is False
        assert caracteristicas.inicio_brusco is False
        assert caracteristicas.esforco is False
        assert caracteristicas.duracao_min is None

    def test_caracteristicas_ativas(self):
        """Verifica as características ativas."""
        caracteristicas = CaracteristicasDorToracica(
            em_aperto=True,
            irradia_braco_mandibula=True,
            sudorese=True,
            nausea=True,
            inicio_brusco=True,
            esforco=True,
            duracao_min=30,
        )
        assert caracteristicas.em_aperto is True
        assert caracteristicas.irradia_braco_mandibula is True
        assert caracteristicas.diagnostico_cid10 == "I20"

    def test_caracteristicas_sem_irradicao(self):
        """Verifica o diagnóstico CID-10 para características sem irradiação."""
        caracteristicas = CaracteristicasDorToracica(em_aperto=True, irradia_braco_mandibula=False)
        assert caracteristicas.diagnostico_cid10 == "R07.2"


class TestCaracteristicasDispneia:
    """Testes para a estrutura CaracteristicasDispneia."""

    def test_caracteristicas_padrao(self):
        """Verifica as características padrão."""
        caracteristicas = CaracteristicasDispneia()
        assert caracteristicas.fala_entrecortada is False
        assert caracteristicas.uso_musculatura_acessoria is False
        assert caracteristicas.cianose is False
        assert caracteristicas.inicio_brusco is False
        assert caracteristicas.ortopneia is False

    def test_caracteristicas_diagnostico(self):
        """Verifica o diagnóstico CID-10 para dispneia."""
        caracteristicas = CaracteristicasDispneia(fala_entrecortada=True, uso_musculatura_acessoria=True)
        assert caracteristicas.diagnostico_cid10 == "R06.02"


class TestSinaisVitais:
    """Testes para a estrutura SinaisVitais."""

    def test_sinais_vitais_padrao(self):
        """Verifica os sinais vitais padrão."""
        sinais = SinaisVitais()
        assert sinais.pa_sistolica is None
        assert sinais.pa_diistolica is None
        assert sinais.frequencia_cardiaca is None
        assert sinais.frequencia_respiratoria is None
        assert sinais.temperatura is None
        assert sinais.saturacao_o2 is None
        assert sinais.escala_glasgow is None
        assert sinais.nivel_consciencia is None
        assert sinais.escala_dor is None

    def test_sinais_vitais_validacao_pa(self):
        """Verifica a validação de PA (PA diastólica < PA sistólica)."""
        with pytest.raises(ValueError, match="PA diastólica deve ser menor que PA sistólica"):
            SinaisVitais(pa_sistolica=120, pa_diistolica=120)

    def test_sinais_vitais_validacao_faixa(self):
        """Verifica a validação de faixas."""
        with pytest.raises(ValueError):
            SinaisVitais(pa_sistolica=300)
        with pytest.raises(ValueError):
            SinaisVitais(pa_diistolica=250)
        with pytest.raises(ValueError):
            SinaisVitais(frequencia_cardiaca=350)
        with pytest.raises(ValueError):
            SinaisVitais(frequencia_respiratoria=100)
        with pytest.raises(ValueError):
            SinaisVitais(temperatura=50.0)
        with pytest.raises(ValueError):
            SinaisVitais(saturacao_o2=150.0)
        with pytest.raises(ValueError):
            SinaisVitais(glicemia_capilar=2000)
        with pytest.raises(ValueError):
            SinaisVitais(escala_glasgow=20)
        with pytest.raises(ValueError):
            SinaisVitais(escala_dor=15)

    def test_calcular_escore_mews_adulto(self):
        """Verifica o cálculo de MEWS para adultos."""
        sinais = SinaisVitais(pa_sistolica=185, frequencia_cardiaca=135, temperatura=39.5)
        score = sinais.calcular_escore_mews(idade_anos=30)
        assert score == 8

    def test_calcular_escore_mews_pediatrico(self):
        """Verifica o cálculo de MEWS para pediatria."""
        sinais = SinaisVitais(frequencia_cardiaca=200, frequencia_respiratoria=40, temperatura=39.0)
        score = sinais.calcular_escore_mews(idade_anos=10)
        assert score == 9


class TestPacienteTriagem:
    """Testes para a estrutura PacienteTriagem."""

    def test_paciente_triagem_basico(self):
        """Verifica o paciente de triagem básico."""
        paciente = PacienteTriagem(
            nome="João Silva",
            cns="123 4567 8901 1234",
            cpf="123.456.789-10",
            idade_anos=45,
            idade_meses=None,
            sexo="M",
            sinais_vitais=SinaisVitais(pa_sistolica=180, pa_diistolica=120),
            queixas=[QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA],
        )

        assert paciente.nome == "João Silva"
        assert paciente.idade_estruturada == "45 ano(s)"
        assert paciente.classificar_risco_manchester == NivelRisco.VERMELHO

    def test_paciente_triagem_sem_idade(self):
        """Verifica o paciente de triagem sem idade."""
        paciente = PacienteTriagem(
            nome="Maria Souza",
            cns="123 4567 8901 1235",
            cpf="123.456.789-10",
            idade_anos=None,
            idade_meses=None,
            sexo="F",
            sinais_vitais=None,
            queixas=[QueixaSentinela.DEFICIT_NEUROLOGICO],
        )

        assert paciente.idade_estruturada == "Idade não informada"
        assert paciente.classificar_risco_manchester == NivelRisco.VERMELHO

    def test_paciente_triagem_cidap2_recomendado(self):
        """Verifica os códigos CIAP-2 recomendados."""
        paciente = PacienteTriagem(
            nome="Paciente",
            cns="123 4567 8901 1236",
            cpf="123.456.789-10",
            idade_anos=30,
            idade_meses=None,
            sexo="M",
            sinais_vitais=None,
            queixas=[QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA, QueixaSentinela.DEFICIT_NEUROLOGICO],
        )

        cidap2 = paciente.ciap2_recomendado
        assert "A01" in cidap2
        assert "A03" in cidap2
        assert "A80" in cidap2

    def test_paciente_triagem_cid10_recomendado(self):
        """Verifica os códigos CID-10 recomendados."""
        paciente = PacienteTriagem(
            nome="Paciente",
            cns="123 4567 8901 1237",
            cpf="123.456.789-10",
            idade_anos=30,
            idade_meses=None,
            sexo="M",
            sinais_vitais=None,
            queixas=[QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA],
        )

        cid10 = paciente.cid10_recomendado
        assert "R07.2" in cid10
        assert "R06.02" in cid10

    def test_paciente_triagem_soap(self):
        """Verifica a geração do registro SOAP."""
        paciente = PacienteTriagem(
            nome="Carlos Oliveira",
            cns="123 4567 8901 1238",
            cpf="123.456.789-10",
            idade_anos=60,
            idade_meses=3,
            sexo="M",
            sinais_vitais=SinaisVitais(pa_sistolica=170, pa_diistolica=100),
            queixas=[QueixaSentinela.DOR_TORACICA],
        )

        soap_subjetivo = paciente.soap_subjetivo
        assert "Carlos Oliveira" in soap_subjetivo
        assert "60 ano(s), 3 mês(es)" in soap_subjetivo

        soap_objetivo = paciente.soap_objetivo
        assert "PA 170/100" in soap_objetivo

        soap_avaliacao = paciente.soap_avaliacao
        assert "RISCO" in soap_avaliacao
        assert "Classificação CIDAP-2" in soap_avaliacao

        soap_plano = paciente.soap_plano
        assert "Intervenção imediata" in soap_plano

        soap_completo = paciente.soap_completo
        assert "S:" in soap_completo
        assert "O:" in soap_completo
        assert "A:" in soap_completo
        assert "P:" in soap_completo


class TestResultadoTriagem:
    """Testes para a estrutura ResultadoTriagem."""

    def test_resultado_triagem(self):
        """Verifica o resultado da triagem."""
        resultado = ResultadoTriagem(
            nivel=NivelRisco.VERMELHO,
            tempo_maximo_espera_min=60,
            discriminadores=["PA sistólica crítica", "Dor torácica crítica (pressão + irradiação)"],
            justificativa="Sinais vitais extremos e queixa sentinela crítica identificadas.",
            condutas=["Intervenção imediata", "Acionar SAMU-192"],
            ciap2_sugeridos=["A01", "A03"],
            cid10_sugeridos=["I20", "R06.02"],
            soap_subjetivo="Paciente João Silva, 45 ano(s), sexo M. Motivo da consulta: DOR_TORACICA, DISPNEIA.",
            soap_objetivo="PA 180/120 mmHg, FC 140 bpm",
            soap_avaliacao="Paciente apresenta risco VERMELHO com base em sinais vitais e sintomas. Classificação CIAP-2: A01, A03. Classificação CID-10: I20, R06.02.",
            soap_plano="Intervenção imediata, possível internação hospitalar.",
            pontuacao=12.5,
        )

        assert resultado.nivel == NivelRisco.VERMELHO
        assert resultado.tempo_maximo_espera_min == 60
        assert len(resultado.discriminadores) == 2
        assert "PA sistólica crítica" in resultado.discriminadores
        assert "Tempo de regulação no SUS" in resultado.tempo_regulacao_sus


class TestFuncoesAvaliacao:
    """Testes para as funções de avaliação."""

    def test_avaliar_sinais_vitais_extremos(self):
        """Verifica a avaliação de sinais vitais extremos."""
        sinais = SinaisVitais(pa_sistolica=190, pa_diistolica=125, temperatura=40.5)
        problemas, pontuacao = evaluate_extreme_vitals(sinais)

        assert "Hipertensão grave" in problemas
        assert "Hipertensão diastólica grave" in problemas
        assert "Hipertermia grave" in problemas
        assert pontuacao >= 8

    def test_avaliar_sinais_vitais_normais(self):
        """Verifica a avaliação de sinais vitais normais."""
        sinais = SinaisVitais(pa_sistolica=120, pa_diistolica=80, temperatura=36.5)
        problemas, pontuacao = evaluate_extreme_vitals(sinais)

        assert len(problemas) == 0
        assert pontuacao == 0

    def test_avaliar_queixas_sentinelas(self):
        """Verifica a avaliação de queixas sentinelas."""
        queixas = [QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA]
        problemas, pontuacao = evaluate_sentinel_complaints(queixas)

        assert "Dor torácica" in problemas
        assert "Dispneia" in problemas
        assert pontuacao == 4

    def test_avaliar_queixas_criticas(self):
        """Verifica a avaliação de queixas críticas."""
        caracteristicas = {
            "em_aperto": True,
            "irradia_braco_mandibula": True,
            "fala_entrecortada": True,
        }
        queixas = [QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA]
        problemas, pontuacao = evaluate_sentinel_complaints(queixas, caracteristicas)

        assert "Dor torácica crítica (pressão + irradiação)" in problemas
        assert "Dispneia crítica (fala entrecortada)" in problemas
        assert pontuacao == 6

    def test_atribuir_prioridade(self):
        """Verifica a atribuição de prioridade."""
        # Baixa pontuação, sem problemas críticos
        assert assign_priority_level(2, ["dor leve"]) == NivelRisco.VERDE

        # Pontuação média
        assert assign_priority_level(6, ["PA moderada"]) == NivelRisco.AMARELO

        # Alta pontuação
        assert assign_priority_level(9, ["PA grave", "dispneia moderada"]) == NivelRisco.LARANJA

        # Pontuação muito alta com problemas críticos
        assert assign_priority_level(15, ["PA grave", "Dor torácica crítica"]) == NivelRisco.VERMELHO


class TestClassificacaoCompleta:
    """Testes de classificação de risco completa."""

    def test_caso_critico_vermelho(self):
        """Verifica classificação crítica (Vermelho)."""
        paciente = PacienteTriagem(
            nome="Paciente Crítico",
            cns="123 4567 8901 2345",
            cpf="123.456.789-09",
            idade_anos=50,
            idade_meses=None,
            sexo="M",
            sinais_vitais=SinaisVitais(pa_sistolica=200, pa_diistolica=130, temperatura=41.0, saturacao_o2=85, escala_glasgow=5),
            queixas=[QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA, QueixaSentinela.DEFICIT_NEUROLOGICO],
            caracteristicas_dor_toracica=CaracteristicasDorToracica(em_aperto=True, irradia_braco_mandibula=True),
            caracteristicas_dispneia=CaracteristicasDispneia(fala_entrecortada=True),
        )

        nivel = paciente.classificar_risco_manchester
        assert nivel == NivelRisco.VERMELHO

    def test_caso_estavel_azul(self):
        """Verifica classificação estável (Azul)."""
        paciente = PacienteTriagem(
            nome="Paciente Estável",
            cns="987 6543 2109 8765",
            cpf="987.654.321-09",
            idade_anos=30,
            idade_meses=None,
            sexo="F",
            sinais_vitais=SinaisVitais(pa_sistolica=110, pa_diistolica=70),
            queixas=[QueixaSentinela.CEFALEIA_BRUSCA],
        )

        nivel = paciente.classificar_risco_manchester
        assert nivel == NivelRisco.AZUL

    def test_paciente_pediatrico(self):
        """Verifica classificação pediátrica."""
        paciente = PacienteTriagem(
            nome="Criança",
            cns="456 7890 1234 5678",
            cpf="456.789.012-34",
            idade_anos=5,
            idade_meses=0,
            sexo="M",
            sinais_vitais=SinaisVitais(frequencia_cardiaca=160, frequencia_respiratoria=35),
            queixas=[QueixaSentinela.FEBRE_PERSISTENTE],
        )

        nivel = paciente.classificar_risco_manchester
        assert nivel == NivelRisco.LARANJA

    def test_paciente_gestante(self):
        """Verifica classificação de paciente gestante."""
        paciente = PacienteTriagem(
            nome="Gestante",
            cns="789 0123 4567 8901",
            cpf="789.012.345-67",
            idade_anos=25,
            idade_meses=None,
            sexo="F",
            gestante=True,
            sinais_vitais=SinaisVitais(temperatura=38.0),
            queixas=[QueixaSentinela.GESTACAO_COMPLICACAO, QueixaSentinela.FEBRE_PERSISTENTE],
        )

        nivel = paciente.classificar_risco_manchester
        assert nivel == NivelRisco.LARANJA


class TestCasoEspecial:
    """Testes para casos especiais."""

    def test_paciente_sem_sinais_vitais(self):
        """Verifica paciente sem sinais vitais."""
        paciente = PacienteTriagem(
            nome="Sem Sinais",
            cns="123 4567 8901 2345",
            cpf="123.456.789-09",
            idade_anos=40,
            idade_meses=None,
            sexo="M",
            sinais_vitais=None,
            queixas=[QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA],
        )

        soap_objetivo = paciente.soap_objetivo
        assert "Sinais vitais não informados" in soap_objetivo

    def test_paciente_sem_cns_cpf(self):
        """Verifica paciente sem CNS/CPF."""
        paciente = PacienteTriagem(
            nome="Sem Identificação",
            cns=None,
            cpf=None,
            idade_anos=45,
            idade_meses=None,
            sexo="M",
            sinais_vitais=None,
            queixas=[QueixaSentinela.DEFICIT_NEUROLOGICO],
        )

        assert paciente.cns is None
        assert paciente.cpf is None

    def test_paciente_idade_meses(self):
        """Verifica paciente com meses de idade."""
        paciente = PacienteTriagem(
            nome="Bebê",
            cns="999 8888 7777 6666",
            cpf="999.888.777-66",
            idade_anos=0,
            idade_meses=6,
            sexo="F",
            sinais_vitais=None,
            queixas=[QueixaSentinela.FEBRE_PERSISTENTE],
        )

        assert paciente.idade_estruturada == "0 ano(s), 6 mês(es)"
