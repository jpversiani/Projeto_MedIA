 ```python
# Arquivo: backend/tests/test_convenios_tiss.py
"""
Testes unitários para validação de guias TISS e relatórios fiscais.

Cobre:
1. Validação de preenchimento obrigatório da guia TISS de consulta.
2. Integridade dos dados fiscais do recibo de reembolso (CRM, CPF paciente, valor pago).
3. Cálculo correto do relatório anual consolidado da DMED.
"""

import pytest
from pydantic import ValidationError

# Importações dos módulos de produção (assumindo que existam)
from backend.app.schemas.tiss import GuiaTISSConsulta, ReciboReembolso
from backend.app.services.dmed import calcular_relatorio_dmed_anual


class TestGuiaTISSConsultaValidation:
    """Testes de validação de preenchimento obrigatório da guia TISS de consulta."""

    def test_guia_valida_com_campos_obrigatorios(self):
        """Uma guia com todos os campos obrigatórios deve ser aceita."""
        guia = GuiaTISSConsulta(
            numero_guia="GUIA123456",
            data_emissao="2025-01-10",
            paciente_nome="Maria da Silva",
            paciente_carteira="CARTAO123",
            profissional_crm="CRM/SP123456",
            profissional_uf="SP",
            codigo_consulta="10101010",
            data_consulta="2025-01-15",
            valor_consulta=150.00,
        )
        assert guia.numero_guia == "GUIA123456"

    @pytest.mark.parametrize(
        "campo, valor",
        [
            ("numero_guia", None),
            ("data_emissao", None),
            ("paciente_nome", ""),
            ("paciente_carteira", None),
            ("profissional_crm", None),
            ("profissional_uf", ""),
            ("codigo_consulta", None),
            ("data_consulta", None),
            ("valor_consulta", None),
        ],
    )
    def test_guia_invalida_quando_campo_obrigatorio_ausente(self, campo, valor):
        """Campos obrigatórios não podem ser nulos ou vazios."""
        dados = {
            "numero_guia": "GUIA123456",
            "data_emissao": "2025-01-10",
            "paciente_nome": "Maria da Silva",
            "paciente_carteira": "CARTAO123",
            "profissional_crm": "CRM/SP123456",
            "profissional_uf": "SP",
            "codigo_consulta": "10101010",
            "data_consulta": "2025-01-15",
            "valor_consulta": 150.00,
        }
        dados[campo] = valor
        with pytest.raises(ValidationError):
            GuiaTISSConsulta(**dados)

    def test_guia_invalida_quando_valor_consulta_negativo(self):
        """Valor da consulta não pode ser negativo."""
        with pytest.raises(ValidationError):
            GuiaTISSConsulta(
                numero_guia="GUIA123456",
                data_emissao="2025-01-10",
                paciente_nome="Maria da Silva",
                paciente_carteira="CARTAO123",
                profissional_crm="CRM/SP123456",
                profissional_uf="SP",
                codigo_consulta="10101010",
                data_consulta="2025-01-15",
                valor_consulta=-10.00,
            )


class TestReciboReembolsoFiscalData:
    """Testes de integridade dos dados fiscais do recibo de reembolso."""

    def test_recibo_valido_com_dados_fiscais_corretos(self):
        """Recibo com CRM, CPF e valor válidos deve ser aceito."""
        recibo = ReciboReembolso(
            crm="CRM/SP123456",
            cpf_paciente="12345678901",
            valor_pago=250.50,
            data_atendimento="2025-01-15",
            numero_guia="GUIA123456",
        )
        assert recibo.crm == "CRM/SP123456"
        assert recibo.cpf_paciente == "12345678901"
        assert recibo.valor_pago == 250.50

    @pytest.mark.parametrize(
        "crm, cpf, valor",
        [
            ("CRM/SP123", "12345678901", 100.0),  # CRM muito curto
            ("CRM/SP123456", "123456789", 100.0),  # CPF inválido
            ("CRM/SP123456", "12345678901", -1.0),  # valor negativo
            ("CRM/SP123456", "12345678901", 0),  # valor zero
        ],
    )
    def test_recibo_invalido_quando_dados_fiscais_incorretos(self, crm, cpf, valor):
        """Dados fiscais inválidos devem gerar erro de validação."""
        with pytest.raises(ValidationError):
            ReciboReembolso(
                crm=crm,
                cpf_paciente=cpf,
                valor_pago=valor,
                data_atendimento="2025-01-15",
                numero_guia="GUIA123456",
            )

    def test_recibo_invalido_quando_cpf_formato_incorreto(self):
        """CPF deve ter exatamente 11 dígitos numéricos."""
        with pytest.raises(ValidationError):
            ReciboReembolso(
                crm="CRM/SP123456",
                cpf_paciente="123.456.789-01",  # formato com pontuação
                valor_pago=100.0,
                data_atendimento="2025-01-15",
                numero_guia="GUIA123456",
            )


class TestRelatorioAnualDMED:
    """Testes de cálculo do relatório anual consolidado da DMED."""

    def test_calculo_simples_com_um_operadora(self):
        """Deve somar os valores pagos por operadora corretamente."""
        registros = [
            {"operadora": "Unimed", "valor": 100.0, "ano": 2024},
            {"operadora": "Unimed", "valor": 250.50, "ano": 2024},
            {"operadora": "Unimed", "valor": 50.0, "ano": 2024},
        ]
        relatorio = calcular_relatorio_dmed_anual(registros)
        assert relatorio["Unimed"] == pytest.approx(400.50)

    def test_calculo_com_multiplas_operadoras(self):
        """Deve agrupar por operadora e somar os valores."""
        registros = [
            {"operadora": "Unimed", "valor": 100.0, "ano": 2024},
            {"operadora": "Bradesco Saúde", "valor": 200.0, "ano": 2024},
            {"operadora": "Unimed", "valor": 50.0, "ano": 2024},
            {"operadora": "Amil", "valor": 75.0, "ano": 2024},
        ]
        relatorio = calcular_relatorio_dmed_anual(registros)
        assert relatorio["Unimed"] == pytest.approx(150.0)
        assert relatorio["Bradesco Saúde"] == pytest.approx(200.0)
        assert relatorio["Amil"] == pytest.approx(75.0)

    def test_calculo_ignora_registros_de_outros_anos(self):
        """O relatório anual deve considerar apenas o ano informado (padrão atual)."""
        registros = [
            {"operadora": "Unimed", "valor": 100.0, "ano": 2023},
            {"operadora": "Unimed", "valor": 200.0, "ano": 2024},
            {"operadora": "Bradesco Saúde", "valor": 50.0, "ano": 2024},
        ]
        relatorio = calcular_relatorio_dmed_anual(registros, ano=2024)
        assert relatorio["Unimed"] == pytest.approx(200.0)
        assert relatorio["Bradesco Saúde"] == pytest.approx(50.0)
        assert "2023" not in relatorio

    def test_calculo_vazio_quando_sem_registros(self):
        """Sem registros, o relatório deve ser um dicionário vazio."""
        assert calcular_relatorio_dmed_anual([]) == {}

    def test_calculo_ignora_valores_nulos(self):
        """Registros com valor nulo devem ser ignorados na soma."""
        registros = [
            {"operadora": "Unimed", "valor": None, "ano": 2024},
            {"operadora": "Unimed", "valor": 100.0, "ano": 2024},
        ]
        relatorio = calcular_relatorio_dmed_anual(registros)
        assert relatorio["Unimed"] == pytest.approx(100.0)
```