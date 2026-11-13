"""Teste de contrato dos imports locais do front-end.

Motivo: o merge T4 (``bbb1450``) removeu ``static/js/fila_espera.js`` por engano,
mas o ``app.js`` continua importando-o dinamicamente (``obterPainelFilaEspera``).
Resultado: a aba Acolhimento abria vazia e o erro só aparecia no console do
navegador. Nenhum teste pegava, porque a suíte de contrato verifica URLs de API
(``test_contrato_frontend.py``), não a existência dos módulos locais em disco.

Este teste varre o HTML/JS estático e confere que todo módulo local referenciado
por ``import(...)``, ``import ... from``, ``import "..."`` ou ``<script src>``
existe em disco. Se alguém remover um módulo sem remover quem o importa, a suíte
quebra aqui — é a classe inteira do bug, não só o caso da fila.

Comentários (incluindo exemplos de uso em JSDoc, que citam ``import`` de módulos
mortos) são removidos antes da varredura: o objetivo é o código que executa, não
a prosa. URLs externas (CDN) e especificadores bare não são módulos locais.
"""
import re
from pathlib import Path

import pytest

STATIC_DIR: Path = Path(__file__).resolve().parents[1] / "app" / "static"

ARQUIVOS_FRONTEND: list[Path] = sorted(
    p for p in STATIC_DIR.rglob("*")
    if p.suffix in (".html", ".js") and "node_modules" not in p.parts
)

# Mesma remoção de comentários do teste de contrato de API: exemplos de uso em
# JSDoc (linhas iniciadas por `*`) e blocos /* */ não são imports reais.
_COMENTARIOS = [
    re.compile(r"(?s)/\*.*?\*/"),        # /* ... */
    re.compile(r"(?m)//[^\n]*"),          # // ...
    re.compile(r"(?s)<!--.*?-->"),        # <!-- ... -->
    re.compile(r"(?m)^\s*\*.*?$"),        # continuação de JSDoc
]

# Cada padrão captura o especificador do módulo no grupo 1.
_PADROES_IMPORT = [
    re.compile(r"""import\(\s*["'`]([^"'`]+)["'`]\s*\)"""),  # import dinâmico
    re.compile(r"""from\s+["'`]([^"'`]+)["'`]"""),            # import/export ... from
    re.compile(r"""import\s+["'`]([^"'`]+)["'`]"""),          # import de efeito colateral
    re.compile(r"""<script[^>]+src=["']([^"']+)["']"""),      # <script src>
]


def _sem_comentarios(texto: str) -> str:
    for padrao in _COMENTARIOS:
        texto = padrao.sub(" ", texto)
    return texto


def _resolver(arquivo: Path, spec: str) -> Path | None:
    """Converte o especificador em caminho de disco, ou None se não for local.

    - ``https:``/``http:``/``data:``/``//cdn`` → externo, ignorado.
    - ``/static/...`` → relativo à raiz estática (como o servidor monta).
    - ``./x.js`` / ``../x.js`` → relativo ao arquivo que importa.
    - bare (``react``) → não usado neste projeto vanilla, ignorado.
    """
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", spec) or spec.startswith("//"):
        return None
    if spec.startswith("/static/"):
        return STATIC_DIR / spec[len("/static/"):]
    if spec.startswith("/"):
        return None  # absoluto fora de /static não é módulo nosso
    if spec.startswith("."):
        return (arquivo.parent / spec).resolve()
    return None


def _coletar_imports() -> list[tuple[Path, str, Path]]:
    achados: list[tuple[Path, str, Path]] = []
    for arquivo in ARQUIVOS_FRONTEND:
        texto = _sem_comentarios(arquivo.read_text(encoding="utf-8", errors="replace"))
        for padrao in _PADROES_IMPORT:
            for m in padrao.finditer(texto):
                spec = m.group(1)
                alvo = _resolver(arquivo, spec)
                if alvo is not None:
                    achados.append((arquivo, spec, alvo))
    return achados


IMPORTS_ENCONTRADOS: list[tuple[Path, str, Path]] = _coletar_imports()


def test_existe_algum_import_para_auditar() -> None:
    """Trava de sanidade: se o varrimento parar de achar imports, vira falso positivo."""
    assert IMPORTS_ENCONTRADOS, (
        "Nenhum import local encontrado no front-end. O padrão de busca quebrou "
        "— investigate antes de confiar nos testes abaixo."
    )
    # Âncora estável: o Cockpit sempre carrega app.js via <script src>.
    alvos = {alvo for _, _, alvo in IMPORTS_ENCONTRADOS}
    assert (STATIC_DIR / "app.js") in alvos, (
        "O varrimento não achou o <script src=/static/app.js> do index.html; "
        "o scanner provavelmente quebrou."
    )


@pytest.mark.parametrize(
    "arquivo,spec,alvo",
    IMPORTS_ENCONTRADOS,
    ids=[f"{a.relative_to(STATIC_DIR)}->{s}" for a, s, _ in IMPORTS_ENCONTRADOS],
)
def test_modulo_local_importado_existe(arquivo: Path, spec: str, alvo: Path) -> None:
    """Todo módulo local referenciado pelo front-end precisa existir em disco."""
    assert alvo.exists(), (
        f"{arquivo.relative_to(STATIC_DIR)} referencia {spec!r}, que não existe "
        f"em disco ({alvo.relative_to(STATIC_DIR) if alvo.is_relative_to(STATIC_DIR) else alvo}). "
        f"Um import órfão quebra a tela em runtime sem nenhum erro de backend — "
        f"foi o que aconteceu com fila_espera.js no merge T4."
    )