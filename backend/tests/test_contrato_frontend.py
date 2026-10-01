"""Teste de contrato entre o front-end e a API.

Motivo: seis chamadas do front-end apontavam para rotas inexistentes e ninguém
notou, porque nenhuma delas é exercitada por teste. Um `POST
/api/v1/atendimentos/anamnese` respondia 405, o consentimento LGPD gravava em
uma rota 404 (nenhum termo era persistido) e o painel do Copiloto nunca
carregou nada — todas as URLs estavam sem o prefixo `/v1` e sem o segmento
`/atendimentos/{id}`.

Este teste varre o JavaScript e o HTML estáticos em busca de URLs de API e
confere cada uma contra a tabela de rotas real do FastAPI. Se alguém criar
uma rota no backend e errar o caminho no front-end, a suíte quebra aqui.
"""
import re
from pathlib import Path

import pytest

from app.main import app

STATIC_DIR = Path(__file__).resolve().parents[1] / "app" / "static"

# Extensões varridas. `.html` e `.js` cobrem todo o front-end atual.
ARQUIVOS_FRONTEND = sorted(
    p for p in STATIC_DIR.rglob("*")
    if p.suffix in (".html", ".js") and "node_modules" not in p.parts
)

# Padrão de URL de API em literais de string. Captura tanto '/api/v1/x' quanto
# `/api/v1/x` (template literal) e URLs em atributos href/src.
PADRAO_URL = re.compile(r"[\"'`](/api/v1/[A-Za-z0-9_\-/{}$.]*)[\"'`]")
# Service worker intercepta e pode conter rotas por conta própria.
IGNORAR = {"sw.js"}

# Comentários em JS e HTML. URLs citadas apenas em documentação explicativa não
# constituem chamada de rede: o objetivo deste teste é validar o código, não a
# prosa. Sem esta remoção, um comentário que descreve o endpoint antigo
# quebraria a suíte mesmo com o código correto.
_COMENTARIOS = [
    re.compile(r"(?s)/\*.*?\*/"),        # /* ... */
    re.compile(r"(?m)//[^\n]*"),          # // ...
    re.compile(r"(?s)<!--.*?-->"),        # <!-- ... -->
    re.compile(r"(?m)^\s*\*.*?$"),        # linhas decontinuacao de JSDoc
]


def _sem_comentarios(texto: str) -> str:
    """Remove comentários para que só literais de URL sejam considerados."""
    for padrao in _COMENTARIOS:
        texto = padrao.sub(" ", texto)
    return texto


def _rotas_do_backend() -> set[str]:
    """Caminhos declarados no OpenAPI, com e sem barra final."""
    caminhos = set()
    for caminho in app.openapi()["paths"]:
        caminhos.add(caminho)
        caminhos.add(caminho.rstrip("/") or "/")
    return caminhos


ROTAS = _rotas_do_backend()


def _coletar_urls() -> list[tuple[Path, str]]:
    achados: list[tuple[Path, str]] = []
    for arquivo in ARQUIVOS_FRONTEND:
        if arquivo.name in IGNORAR:
            continue
        texto = _sem_comentarios(arquivo.read_text(encoding="utf-8", errors="replace"))
        for m in PADRAO_URL.finditer(texto):
            achados.append((arquivo, m.group(1)))
    return achados


URLS_ENCONTRADAS = _coletar_urls()


def test_existe_alguma_url_para_auditar():
    """Trava de sanidade: se o varrimento parar de achar URLs, o teste vira falso positivo."""
    assert URLS_ENCONTRADAS, (
        "Nenhuma URL de API encontrada no front-end. O padrão de busca quebrou "
        "ou todo o front-end parou de chamar a API — investigate antes de confiar "
        "nos testes abaixo."
    )


@pytest.mark.parametrize(
    "arquivo,url",
    URLS_ENCONTRADAS,
    ids=[f"{a.relative_to(STATIC_DIR)}:{u}" for a, u in URLS_ENCONTRADAS],
)
def test_url_do_frontend_existe_no_backend(arquivo, url):
    """Cada URL chamada pelo front-end precisa corresponder a uma rota real.

    URLs com placeholder dinâmico (ex.: `/atendimentos/${id}/alertas`) são
    normalizadas para o segmento de parâmetro antes da comparação.
    """
    # Normaliza placeholders: ${id}, {id}, {atendimento_id} -> {param}
    normalizada = re.sub(r"\$\{[^}]*\}|\{[^}]*\}", "{param}", url)
    # Remove query string e barra final para casar com o OpenAPI.
    base = normalizada.split("?")[0].rstrip("/") or "/"

    if base in ROTAS:
        return

    # Se o placeholder está no MEIO do caminho (ex.: /atendimentos/{param}/alertas),
    # casa por padrão: mesmos segmentos estáticos na mesma posição relativa.
    if "{param}" in base:
        estaticos = [s for s in base.split("/") if s and s != "{param}"]
        candidatos = [
            r for r in ROTAS
            if len(r.split("/")) == len(base.split("/"))
            and all(
                s in r.split("/")
                for s in estaticos
                if not s.startswith("{")
            )
        ]
        assert candidatos, (
            f"{arquivo.relative_to(STATIC_DIR)} chama {url!r} e nenhuma rota "
            f"corresponde. Rotas próximas: "
            f"{sorted(r for r in ROTAS if 'alertas' in r or 'soap' in r)[:5]}"
        )
        return

    pytest.fail(
        f"{arquivo.relative_to(STATIC_DIR)} chama {url!r}, que não existe na API.\n"
        f"Rotas disponíveis sob /api/v1: "
        f"{sorted(r for r in ROTAS if r.startswith('/api/v1'))[:12]}"
    )


def test_consentimento_lgpd_aponta_para_rota_de_tcle():
    """O termo de consentimento precisa gravar em uma rota existente.

    Este endpoint apontava para `/api/v1/consentimento`, que nunca existiu: o
    registro de consentimento exigido pela CFM 2.314/2022 simplesmente não
    acontecia, e a falha era tratada como erro genérico.
    """
    arquivo = STATIC_DIR / "js" / "consentimento_lgpd.js"
    # Lemos o arquivo inteiro aqui de propósito: a asserção precisa garantir que
    # a rota antiga não volte nem como código nem como constante.
    texto = arquivo.read_text(encoding="utf-8")

    assert "/api/v1/telemedicina/tcle/registrar" in texto
    assert "/api/v1/telemedicina/tcle/registrar" in ROTAS


def test_paginas_estaticas_nao_sao_dumps_de_codigo():
    """Nenhum `.html` pode ser, na verdade, saída de `tree` ou código-fonte.

    Dois arquivos assim foram commitados com extensão `.html` e servidos
    publicamente em `/static/`, expondo a estrutura interna do projeto.
    """
    suspeitas = []
    for arquivo in ARQUIVOS_FRONTEND:
        if arquivo.suffix != ".html":
            continue
        texto = arquivo.read_text(encoding="utf-8", errors="replace")
        tem_html = "<html" in texto.lower() or "<!doctype" in texto.lower()
        tem_codigo = "def " in texto or "import " in texto or texto.lstrip().startswith("backend/")
        if not tem_html and tem_codigo:
            suspeitas.append(arquivo.relative_to(STATIC_DIR))

    assert not suspeitas, (
        f"Arquivos .html que nao sao HTML: {suspeitas}. "
        f"Serve codigo-fonte em vez de interface."
    )
