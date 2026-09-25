"""Testes unitários para o módulo de triagem clínica (APS - Manchester Adaptado)."""

import pytest
from datetime import datetime
from pydantic import BaseModel

# Importar os modelos do módulo
from backend.app.services.triagem_clinica import (
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


class TestNivelRisco:
    """Testes para a enumeração de níveis de risco."""

    def test_niveis_existentes(self):
        assert NivelRisco.VERMELHO.value == "VERMELHO"
        assert NivelRisco.LARANJA.value == "LARANJA"
        assert NivelRisco.AMARELO.value == "AMARELO"
        assert NivelRisco.VERDE.value == "VERDE"
        assert NivelRisco.AZUL.value == "AZUL"

    def test_peso_ordem(self):
        assert NivelRisco.VERMELHO.peso_ordem == 1
        assert NivelRisco.LARANJA.peso_ordem == 2
        assert NivelRisco.AMARELO.peso_ordem == 3
        assert NivelRisco.VERDE.peso_ordem == 4
        assert NivelRisco.AZUL.peso_ordem == 5

    def test_tempo_maximo_espera(self):
        assert evaluate_extreme_vitals().tempo_maximo_espera_min == 120  # Verde
        assert evaluate_extreme_vitals().tempo_maximo_espera_min == 60  # Vermelho

    def test_condicao_sus(self):
        # Vermelho
        assert evaluate_extreme_vitals()['problemas'] == []
        assert evaluate_extreme_vitals()['pontuacao'] == 0
        # Verde
        assert evaluate_extreme_vitals()['problemas'] == []
        assert evaluate_extreme_vitals()['pontuacao'] == 0


class TestQueixaSentinela:
    """Testes para as queixas sentinelas."""

    def test_list_of_sentinels(self):
        sentinelas = [
            QueixaSentinela.DOR_TORACICA,
            QueixaSentinela.DISPNEIA,
            QueixaSentinela.DEFICIT_NEUROLOGICO,
            QueixaSentinela.SANGRAMENTO_GRAVE,
        ]
        assert len(sentinelas) == 4
        assert QueixaSentinela.DOR_TORACICA in sentinelas
        assert QueixaSentinela.DISPNEIA in sentinelas

    def test_invalid_sentinel_raises_error(self):
        with pytest.raises(ValueError, match="Pelo menos uma queixa sentinela deve ser informada"):
            PacienteTriagem(
                nome="Teste",
                cns="123456789",
                cpf="123.456.789-01",
                idade_anos=30,
                queixas=[],  # Sem queixas
            )


class TestCaracteristicasDorToracica:
    """Testes para características da dor torácica."""

    def test_caracteristicas_dor_toracica_defaults(self):
        dt = CaracteristicasDorToracica()
        assert dt.em_aperto is False
        assert dt.irradia_braco_mandibula is False
        assert dt.sudorese is False
        assert dt.nasoceira is False
        assert dt.inicio_brusco is False
        assert dt.esforco is False
        assert dt.duracao_min is None

    def test_caracteristicas_dor_toracica_with_values(self):
        dt = CaracteristicasDorToracica(
            em_aperto=True,
            irradia_braco_mandibula=True,
            sudorese=True,
            inicio_brusco=True,
            esforco=True,
            duracao_min=45,
        )
        assert dt.em_aperto is True
        assert dt.irradia_braco_mandibula is True
        assert dt.sudorese is True
        assert dt.inicio_brusco is True
        assert dt.esforco is True
        assert dt.duracao_min == 45

    def test_diagnostico_cid10(self):
        dt = CaracteristicasDorToracica(
            em_aperto=True,
            irradia_braco_mandibula=True,
        )
        assert dt.diagnostico_cid10 == "I20"

    def test_diagnostico_cid10_no_pressao(self):
        dt = CaracteristicasDorToracica(
            em_aperto=False,
            irradia_braco_mandibula=False,
        )
        assert dt.diagnostico_cid10 == "R07.2"


class TestCaracteristicasDispneia:
    """Testes para características da dispneia."""

    def test_caracteristicas_dispneia_defaults(self):
        dt = CaracteristicasDispneia()
        assert dt.fala_entrecortada is False
        assert dt.uso_musculatura_acessoria is False
        assert dt.cianose is False
        assert dt.inicio_brusco is False
        assert dt.ortopneia is False
        assert dt.escala_glasgow is None
        assert dt.nivel_consciencia is None
        assert dt.escala_dor is None

    def test_diagnostico_cid10(self):
        dt = CaracteristicasDispneia(
            fala_entrecortada=True,
            uso_musculatura_acessoria=False,
            cianose=False,
            inicio_brusco=False,
            ortopneia=False,
        )
        assert dt.diagnostico_cid10 == "R06.02"


class TestSinaisVitais:
    """Testes para sinais vitais."""

    def test_sinais_vitais_defaults(self):
        sv = SinaisVitais()
        assert sv.pa_sistolica is None
        assert sv.pa_diistolica is None
        assert sv.frequencia_cardiaca is None
        assert sv.frequencia_respiratoria is None
        assert sv.temperatura is None
        assert sv.saturacao_o2 is None
        assert sv.escala_glasgow is None
        assert sv.nivel_consciencia is None
        assert sv.escala_dor is None

    def test_sinais_vitais_com_full_data(self):
        sv = SinaisVitais(
            pa_sistolica=150,
            pa_diistolica=100,
            frequencia_cardiaca=140,
            frequencia_respiratoria=30,
            temperatura=38.5,
            saturacao_o2=72.0,
            escala_glasgow=7,
            nivel_consciencia="A",
            escala_dor=8,
        )
        assert sv.pa_sistolica == 150
        assert sv.pa_diistolica == 100
        assert sv.frequencia_cardiaca == 140
        assert sv.frequencia_respiratoria == 30
        assert sv.temperatura == 38.5
        assert sv.saturacao_o2 == 72.0
        assert sv.escala_glasgow == 7
        assert sv.nivel_consciencia == "A"
        assert sv.escala_dor == 8

    def test_calcular_escore_mews(self):
        sv = SinaisVitais(
            pa_sistolica=180,
            pa_diistolica=110,
            frequencia_cardiaca=130,
            frequencia_respiratoria=30,
            temperatura=39.0,
            saturacao_o2=88.0,
            escala_glasgow=6,
            nivel_consciencia="A",
            escala_dor=5,
        )
        # Scores: PA 180->3, PA 110->2, FC 130->3, FR 30->3, Temp 39->2, Sat 88->2, GCS 6->3, Consciencia A->3, Dor 5->2
        # Total: 3+2+3+3+2+2+3+3+2 = 23
        assert sv.calcular_escore_mews() == 23


class TestPacienteTriagem:
    """Testes para o modelo PacienteTriagem."""

    def test_paciente_triagem_basic(self):
        # Valid CPF format (15 digits)
        cpf = "123.456.789.901"
        pt = PacienteTriagem(
            nome="João Silva",
            cns=cpf,
            cpf=cpf,
            idade_anos=35,
            idade_meses=5,
            sexo="M",
            gestante=False,
            sinais_vitais=None,
            queixas=[QueixaSentinela.DOR_TORACICA],
            caracteristicas_dor_toracica=None,
            caracteristicas_dispneia=None,
        )
        assert pt.nome == "João Silva"
        assert pt.cns == cpf
        assert pt.cpf == cpf
        assert pt.idade_anos == 35
        assert pt.idade_meses == 5
        assert pt.sexo == "M"
        assert pt.queixas == [QueixaSentinela.DOR_TORACICA]
        assert pt.caracteristicas_dor_toracica is None
        assert pt.caracteristicas_dispneia is None

    def test_paciente_triagem_com_sinais_vitais(self):
        sv = SinaisVitais(
            pa_sistolica=140,
            pa_diistolica=100,
            frequencia_cardiaca=120,
            frequencia_respiratoria=28,
            temperatura=38.0,
            saturacao_o2=75.0,
            escala_glasgow=8,
            nivel_consciencia="A",
            escala_dor=6,
        )
        pt = PacienteTriagem(
            nome="Maria Santos",
            cns="987.654.321-00",
            cpf="987.654.321-00",
            idade_anos=40,
            idade_meses=2,
            sexo="F",
            sinais_vitais=sv,
            queixas=[QueixaSentinela.DISPNEIA],
            caracteristicas_dor_toracica=None,
            caracteristicas_dispneia=None,
        )
        assert pt.idade_estruturada == "Idade não informada"  # pois idade_meses é 2
        assert pt.queixas == [QueixaSentinela.DISPNEIA]

    def test_validacao_queixas_sentinelas(self):
        # Com queixa sentinela válida
        pt = PacienteTriagem(
            nome="Teste",
            cns="123.456.789-01",
            cpf="123.456.789-01",
            idade_anos=30,
            queixas=[QueixaSentinela.DOR_TORACICA],
        )
        # Deve passar na validação
        assert True

    def test_validacao_cns(self):
        # CNS inválido
        with pytest.raises(ValueError, match="CNS inválido"):
            PacienteTriagem(nome="Teste", cns="invalid-cns", cpf="123.456.789-01")

    def test_validacao_cpf(self):
        # CPF inválido
        with pytest.raises(ValueError, match="CPF inválido"):
            PacienteTriagem(nome="Teste", cns="123.456.789-01", cpf="123.abc.def.ghij")

    def test_validacao_queixas_falta_sentinela(self):
        # Sem queixa sentinela
        with pytest.raises(ValueError, match="Pelo menos uma queixa sentinela deve ser informada"):
            PacienteTriagem(
                nome="Teste",
                cns="123.456.789-01",
                cpf="123.456.789-01",
                idade_anos=30,
                queixas=[],
            )


class TestResultadoTriagem:
    """Testes para o modelo ResultadoTriagem."""

    def test_resultado_triagem_basic(self):
        # Criando um paciente com risco vermelho
        pt = PacienteTriagem(
            nome="João",
            cns="123.456.789-01",
            cpf="123.456.789-01",
            idade_anos=40,
            queixas=[QueixaSentinela.DOR_TORACICA],
            sinais_vitais=SinaisVitais(
                pa_sistolica=180,
                pa_diistolica=120,
                frequencia_cardiaca=140,
                frequencia_respiratoria=30,
                temperatura=39.0,
                saturacao_o2=72.0,
                escala_glasgow=6,
                nivel_consciencia="A",
                escala_dor=8,
            ),
        )
        resultado = ResultadoTriagem(
            nivel=pt.classificar_risco_manchester(),
            tempo_maximo_espera_min=pt.tempo_maximo_espera_min(),
            discriminadores=pt.evaluate_extreme_vitals(pt.sinais_vitais, pt.idade_anos),
            justificativa="...",
            condutas=[],
            ciap2_sugeridos=pt.ciap2_recomendado,
            cid10_sugeridos=pt.cid10_recomendado,
            soap_subjetivo=pt.soap_subjetivo(),
            soap_objetivo=pt.soap_objetivo(),
            soap_avaliacao=pt.soap_avaliacao(),
            soap_plano=pt.soap_plano(),
        )
        assert resultado.nivel == NivelRisco.VERMELHO
        assert resultado.tempo_maximo_espera_min == 0  # Vermelho
        assert len(resultado.discriminadores) > 0

    def test_classificar_risco_manchester(self):
        # Risco vermelho (score >= 10)
        pt = PacienteTriagem(
            nome="João",
            cns="123.456.789-01",
            cpf="123.456.789-01",
            idade_anos=40,
            queixas=[QueixaSentinela.DOR_TORACICA],
            sinais_vitais=SinaisVitais(
                pa_sistolica=180,
                pa_diistolica=120,
                frequencia_cardiaca=140,
                frequencia_respiratoria=30,
                temperatura=39.0,
                saturacao_o2=72.0,
                escala_glasgow=6,
                nivel_consciencia="A",
                escala_dor=8,
            ),
        )
        assert pt.classificar_risco_manchester() == NivelRisco.VERMELHO

    def test_tempo_regulacao_sus(self):
        # Tempo de regulação SUS por nível de risco
        for nivel in [NivelRisco.VERMELHO, NivelRisco.LARANJA, NivelRisco.AMARELO, NivelRisco.VERDE, NivelRisco.AZUL]:
            resultado = ResultadoTriagem(
                nivel=nivel,
                tempo_maximo_espera_min=pt.tempo_maximo_espera_min(),
                discriminadores=[],
                justificativa="",
                condutas=[],
                ciap2_sugeridos=[],
                cid10_sugeridos=[],
                soap_subjetivo="",
                soap_objetivo="",
                soap_avaliacao="",
                soap_plano="",
            )
            # Verificar se o tempo está correto
            expected = {
                NivelRisco.VERMELHO: 0,
                NivelRisco.LARANJA: 10,
                NivelRisco.AMARELO: 240,
                NivelRisco.VERDE: 720,
                NivelRisco.AZUL: 1440,
            }
            assert resultado.tempo_regulacao_sus() == expected[nivel]


class TestFuncoes_Externas:
    """Testes para funções externas do módulo."""

    def test_evaluate_extreme_vitals(self):
        # Sinais vitais normais
        sv = SinaisVitais()
        problemas, pontuacao = evaluate_extreme_vitals(sv)
        assert len(problemas) == 0
        assert pontuacao == 0

    def test_evaluate_extreme_vitals_critical(self):
        # Sinais vitais críticos
        sv = SinaisVitais(
            pa_sistolica=200,
            pa_diistolica=150,
            frequencia_cardiaca=150,
            frequencia_respiratoria=35,
            temperatura=41.0,
            saturacao_o2=70.0,
            escala_glasgow=5,
            nivel_consciencia="P",
            escala_dor=9,
        )
        problemas, pontuacao = evaluate_extreme_vitals(sv)
        assert len(problemas) > 0
        assert pontuacao >= 10  # Deveria ser alto devido aos sinais críticos

    def test_evaluate_sentinel_complaints(self):
        # Queixa sentinela sem características
        problemas, pontuacao = evaluate_sentinel_complaints([QueixaSentinela.DOR_TORACICA])
        assert len(problemas) == 2  # Dor torácica + outra categoria
        assert pontuacao >= 2

    def test_evaluate_sentinel_complaints_complete(self):
        # Queixa sentinela com características
        problemas, pontuacao = evaluate_sentinel_complaints(
            [QueixaSentinela.DOR_TORACICA, QueixaSentinela.DISPNEIA]
        )
        assert len(problemas) == 4  # Cada queixa gera problemas
        assert pontuacao >= 5

    def test_assign_priority_level(self):
        # Prioridade vermelha (>= 10 pontos)
        assert assign_priority_level(10, []) == NivelRisco.VERMELHO
        # Prioridade amarela (5-9 pontos)
        assert assign_priority_level(7, []) == NivelRisco.LARANJA
        # Prioridade verde (2-4 pontos)
        assert assign_priority_level(5, []) == NivelRisco.AMARELO
        # Prioridade azul (< 2 pontos)
        assert assign_priority_level(1, []) == NivelRisco.AZUL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
