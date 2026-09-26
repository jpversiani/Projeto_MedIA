import pytest
from app.services.templates_especialidades import (
    CATALOGO_ESPECIALIDADES,
    obter_especialidade,
    listar_todas_especialidades,
)


def test_catalogo_especialidades_minimo():
    assert len(CATALOGO_ESPECIALIDADES) >= 6
    assert "clinica_medica" in CATALOGO_ESPECIALIDADES
    assert "cardiologia" in CATALOGO_ESPECIALIDADES
    assert "psiquiatria" in CATALOGO_ESPECIALIDADES
    assert "dermatologia" in CATALOGO_ESPECIALIDADES
    assert "pediatria" in CATALOGO_ESPECIALIDADES
    assert "endocrinologia" in CATALOGO_ESPECIALIDADES


def test_obter_especialidade_psiquiatria():
    esp = obter_especialidade("psiquiatria")
    assert esp.nome == "Psiquiatria & Saúde Mental"
    assert "Exame do Estado Mental" in esp.exame_fisico_template
    assert any("F41" in c["codigo"] for c in esp.principais_ciap2_cid10)
    assert len(esp.alertas_seguranca_telemedicina) > 0


def test_obter_especialidade_fallback_clinica_medica():
    esp = obter_especialidade("inexistente_qualquer")
    assert esp.codigo == "clinica_medica"
    assert esp.nome == "Clínica Médica / Geral"


def test_listar_todas_especialidades():
    lista = listar_todas_especialidades()
    assert len(lista) >= 6
    for item in lista:
        assert "codigo" in item
        assert "nome" in item
        assert "queixas" in item
        assert len(item["queixas"]) >= 3
        assert "exame_fisico_template" in item
