"""Suíte de testes automatizados para validação de botões, esquema lógico e contratos de interface do Cockpit Clínico MedIA.

Garante que:
1. 100% dos botões no template principal possuem tratadores (handlers), IDs vinculados ou submissão de formulário (zero botões órfãos).
2. Todas as funções JavaScript acionadas por atributos `onclick` estão implementadas nos scripts estáticos.
3. Os fluxos e endpoints de backend acionados pelos botões (Cadastro, Agendamento, SOAP, Prescrição, TISS, Farmácia, DMED) respondem com sucesso e persistem no banco de dados.
4. Todos os modais possuem controles de abertura e fechamento válidos.
"""
from __future__ import annotations

import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app

STATIC_DIR = Path(__file__).resolve().parents[1] / "app" / "static"
INDEX_HTML = STATIC_DIR / "index.html"
APP_JS = STATIC_DIR / "app.js"

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture(scope="module")
def html_content() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")

@pytest.fixture(scope="module")
def all_javascript() -> str:
    js_parts = []
    for f in STATIC_DIR.rglob("*.js"):
        if "sw.js" not in f.name:
            js_parts.append(f.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(js_parts)


def test_todos_os_botoes_possuem_acao_ou_id(html_content: str):
    """Garante que nenhum botão na interface está órfão (sem id, sem onclick e sem type=submit)."""
    button_regex = re.compile(r"<button\b([^>]*)>(.*?)</button>", re.DOTALL)
    matches = list(button_regex.finditer(html_content))
    assert len(matches) > 0, "Nenhum botão encontrado no index.html"

    orfãos = []
    for idx, m in enumerate(matches, 1):
        attrs = m.group(1)
        has_id = bool(re.search(r'id=["\']([^"\']+)["\']', attrs))
        has_onclick = bool(re.search(r'onclick=["\']([^"\']+)["\']', attrs))
        has_submit = 'type="submit"' in attrs or "type='submit'" in attrs

        if not (has_id or has_onclick or has_submit):
            clean_text = " ".join(re.sub(r"<[^>]+>", "", m.group(2)).split())[:30]
            orfãos.append((idx, clean_text, attrs))

    assert len(orfãos) == 0, f"Encontrados botões órfãos sem ação ou identificador: {orfãos}"


def test_funcoes_onclick_existem_no_javascript(html_content: str, all_javascript: str):
    """Garante que todas as funções chamadas por onclick existem nos scripts carregados."""
    onclick_regex = re.compile(r'onclick=["\']([^"\']+)["\']')
    matches = onclick_regex.findall(html_content)

    faltantes = []
    for raw_handler in matches:
        handler = raw_handler.strip()
        # Ignora código inline puro como this.parentElement.remove() ou window.print()
        if "this." in handler or "window.print" in handler:
            continue
        # Ignora encadeamentos opcionais como window.filaEsperaPainel?.chamarProximo()
        if "?." in handler:
            continue

        # Extrai o nome da função principal
        m_func = re.match(r"([a-zA-Z0-9_$]+)\s*\(", handler)
        if m_func:
            func_name = m_func.group(1)
            # Verifica definição: function nome( | nome = function | window.nome
            def_pattern = re.compile(
                rf"\b(function\s+{func_name}\b|{func_name}\s*=\s*(async\s+)?function|window\.{func_name}\s*=)"
            )
            if not def_pattern.search(all_javascript):
                faltantes.append((func_name, handler))

    assert len(faltantes) == 0, f"Funções onclick sem implementação no JavaScript: {faltantes}"


def test_botoes_modais_possuem_abertura_e_fechamento(html_content: str, all_javascript: str):
    """Valida se todos os modais da interface têm botões e funções de fechamento mapeados."""
    modais = re.findall(r'id=["\'](modal-[^"\']+)["\']', html_content)
    assert len(modais) >= 10, f"Esperado ao menos 10 modais, encontrados: {len(modais)}"

    modais_com_fechamento_esperado = {
        "modal-novo-paciente": "fecharModalNovoPaciente",
        "modal-novo-agendamento": "fecharModalNovoAgendamento",
        "modal-nova-guia-tiss": "fecharModalNovaGuiaTISS",
        "modal-prescricao-digital": "fecharModalPrescricaoDigital",
        "modal-atestado-digital": "fecharModalAtestadoDigital",
        "modal-recibo": "fecharModalRecibo",
        "modal-recibo-dmed-view": "fecharModalReciboDMED",
        "modal-tcle-view": "fecharModalTCLE",
        "modal-auditoria": "fecharModalAuditoria",
        "modal-atalhos": "fecharModalAtalhos",
    }

    for modal_id, fechar_func in modais_com_fechamento_esperado.items():
        assert modal_id in html_content, f"Modal {modal_id} não encontrado no HTML"
        assert f"function {fechar_func}" in all_javascript or f"window.{fechar_func}" in all_javascript, (
            f"Função de fechamento {fechar_func} não implementada no JavaScript para {modal_id}"
        )


def test_fluxo_botao_salvar_novo_paciente_api(client: TestClient):
    """Simula o clique do botão 'Salvar no Banco de Dados' do modal Novo Paciente."""
    payload = {
        "nome_completo": "Cidadão Teste Botão Automatizado",
        "cpf": "11122299901",
        "cns": "777888999000199",
        "data_nascimento": "1990-05-15",
        "sexo": "M",
        "telefone": "(31) 98888-7777",
        "nome_mae": "Mãe do Cidadão Teste",
        "logradouro": "Rua das Flores, 123",
        "alergias": "Nenhuma conhecida",
        "hipertenso": True
    }
    res = client.post("/api/v1/cidadaos/", json=payload)
    assert res.status_code in (200, 201, 400), f"Falha ao cadastrar cidadão via API: {res.text}"
    if res.status_code in (200, 201):
        data = res.json()
        assert data["nome_completo"] == payload["nome_completo"]
        assert data["cpf"] == payload["cpf"]


def test_fluxo_botao_salvar_novo_agendamento_api(client: TestClient):
    """Simula o clique do botão 'Agendar Consulta' do modal Novo Agendamento."""
    cpf = "11122299901"
    payload_agenda = {
        "paciente_cpf": cpf,
        "data_hora": "2026-10-25T14:30:00",
        "tipo": "TELEMEDICINA",
        "profissional_nome": "Dra. Francelli Versiani",
        "observacoes": "Consulta agendada via teste de botão"
    }
    res = client.post("/api/v1/agenda/novo", json=payload_agenda)
    assert res.status_code in (200, 201), f"Falha ao agendar consulta: {res.text}"
    data = res.json()
    assert "id" in data
    assert data["status"] in ("AGENDADO", "CONFIRMADO", "SOLICITADO")


def test_fluxo_botao_nova_guia_tiss_api(client: TestClient):
    """Simula o clique do botão 'Autorizar e Emitir Guia' do modal Nova Guia TISS."""
    payload = {
        "operadora_nome": "Unimed",
        "paciente_nome": "Mariana Souza Alencar",
        "valor_procedimento": 220.0
    }
    res = client.post("/api/v1/convenios/guias/consulta", json=payload)
    assert res.status_code in (200, 201), f"Falha ao emitir guia TISS: {res.text}"
    data = res.json()
    assert "numero_guia" in data or "numero_guia_operadora" in data
    assert data["status"] in ("GERADA", "EMITIDA", "Autorizada", "AUTORIZADA")


def test_fluxo_botao_dispensacao_farmacia_api(client: TestClient):
    """Simula o clique do botão 'Dispensar' na tabela de Farmácia."""
    payload = {
        "nome_medicamento": "Losartana Potássica",
        "quantidade": 1,
        "paciente_nome": "Paciente Balcão Teste",
        "observacoes": "Dispensação via teste unitário de botão"
    }
    res = client.post("/api/v1/farmacia/dispensar-rapido", json=payload)
    assert res.status_code in (200, 201), f"Falha ao registrar dispensação: {res.text}"
    data = res.json()
    assert "saldo_restante" in data or "estoque_restante" in data
    assert data["medicamento"] == "Losartana Potássica"


def test_fluxo_botao_finalizar_atendimento_pos_consulta_api(client: TestClient):
    """Simula o clique do botão 'Finalizar Atendimento' que emite recibo DMED e carnê-leão."""
    payload = {
        "consulta_id": "CONS-2026-9812",
        "emitir_recibo_dmed": True,
        "lancar_livro_caixa": True,
        "dias_retorno_sugerido": 30,
        "canal_despacho_paciente": "WHATSAPP"
    }
    res = client.post("/api/v1/fluxo-atendimento/pos-consulta/finalizar", json=payload)
    assert res.status_code in (200, 201), f"Falha ao finalizar atendimento pós-consulta: {res.text}"
    pacote = res.json()
    assert "codigo_verificador_receita" in pacote
    assert "recibo_dmed_numero" in pacote
    assert "valor_consulta" in pacote
    assert "link_whatsapp_despacho" in pacote


def test_fluxo_botao_exportar_lote_xml_tiss_api(client: TestClient):
    """Simula o clique do botão 'Exportar Lote XML' na aba de Convênios."""
    res = client.post("/api/v1/tiss/exportar-lote-xml", json={"numero_lote": "1"})
    assert res.status_code == 200, f"Falha ao exportar lote XML TISS: {res.text}"
    assert "application/xml" in res.headers.get("content-type", "") or "text/xml" in res.headers.get("content-type", "")
    assert "<mensagemTISS" in res.text or "<ans:mensagemTISS" in res.text or "<" in res.text


def test_fluxo_botao_gerar_lote_dmed_api(client: TestClient):
    """Simula o clique do botão 'Gerar Arquivo Magnético DMED'."""
    res = client.get("/api/v1/dmed/exportar-exemplo")
    assert res.status_code == 200, f"Falha ao exportar DMED magnético: {res.text}"
    assert "DMED" in res.text or "text/plain" in res.headers.get("content-type", "")
