"""Testes do backup verificável (``scripts/backup_db.py``).

Backup sem verificação é esperança, não é backup. Estes testes cobrem o ciclo
completo: copiar → checksum no manifesto → conferir → restaurar, além das
recusas de segurança (restaurar sem confirmação, arquivo adulterado).
"""

import importlib.util
import shutil
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture
def dir_temporario():
    """Diretório temporário **dentro do workspace**.

    Dois detalhes aprendidos na prática:

    * o `tmp_path` do pytest vive em ``%TEMP%``, fora do workspace, e o sandbox de
      arquivos nega escrita lá;
    * `tempfile.mkdtemp` cria o diretório com ``mode=0o700``, e no Windows o
      Python 3.13 traduz isso para uma ACL restritiva — criar *filhos* dentro
      dele falha. Por isso o diretório é criado com `mkdir()` simples e nome
      único, e removido no fim.
    """
    base = RAIZ / ".tmp_testes"
    base.mkdir(exist_ok=True)
    criado = base / f"t{uuid4().hex[:12]}"
    criado.mkdir()
    try:
        yield criado
    finally:
        shutil.rmtree(criado, ignore_errors=True)
        if base.exists() and not any(base.iterdir()):
            base.rmdir()


def _carregar_modulo():
    caminho = RAIZ / "scripts" / "backup_db.py"
    spec = importlib.util.spec_from_file_location("backup_db", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


backup_db = _carregar_modulo()


def _criar_banco(caminho: Path) -> Path:
    conn = sqlite3.connect(caminho)
    try:
        conn.execute("CREATE TABLE pacientes (id INTEGER PRIMARY KEY, nome TEXT)")
        conn.execute("INSERT INTO pacientes (nome) VALUES ('Maria')")
        conn.execute("INSERT INTO pacientes (nome) VALUES ('João')")
        conn.commit()
    finally:
        conn.close()
    return caminho


def test_backup_cria_arquivo_verificado_com_manifesto(dir_temporario):
    origem = _criar_banco(dir_temporario / "origem.db")
    destino = dir_temporario / "backups"

    relatorio = backup_db.executar_backup(
        destino, {"tipo": "sqlite", "caminho": origem}
    )

    arquivo = Path(relatorio["arquivo"])
    assert arquivo.exists()
    assert relatorio["integridade"] == "ok"
    assert relatorio["tabelas"] == 1
    assert len(relatorio["sha256"]) == 64

    # O manifesto registra o checksum que permite detectar adulteração depois.
    registros = backup_db.ler_manifesto(destino)
    assert len(registros) == 1
    assert registros[0]["arquivo"] == arquivo.name
    assert registros[0]["sha256"] == relatorio["sha256"]


def test_backup_preserva_o_conteudo(dir_temporario):
    origem = _criar_banco(dir_temporario / "origem.db")
    relatorio = backup_db.executar_backup(
        dir_temporario / "backups", {"tipo": "sqlite", "caminho": origem}
    )

    conn = sqlite3.connect(relatorio["arquivo"])
    try:
        nomes = [linha[0] for linha in conn.execute("SELECT nome FROM pacientes ORDER BY id")]
    finally:
        conn.close()
    assert nomes == ["Maria", "João"]


def test_verificacao_aprova_backup_intacto(dir_temporario):
    origem = _criar_banco(dir_temporario / "origem.db")
    destino = dir_temporario / "backups"
    relatorio = backup_db.executar_backup(destino, {"tipo": "sqlite", "caminho": origem})

    verificacao = backup_db.verificar_backup(Path(relatorio["arquivo"]), destino)
    assert verificacao["confere"] is True
    assert verificacao["integridade"] == "ok"


def test_verificacao_detecta_adulteracao(dir_temporario):
    origem = _criar_banco(dir_temporario / "origem.db")
    destino = dir_temporario / "backups"
    relatorio = backup_db.executar_backup(destino, {"tipo": "sqlite", "caminho": origem})

    arquivo = Path(relatorio["arquivo"])
    with open(arquivo, "ab") as manipulador:
        manipulador.write(b"\x00" * 16)

    with pytest.raises(RuntimeError, match="não corresponde ao manifesto"):
        backup_db.verificar_backup(arquivo, destino)


def test_restauracao_exige_confirmacao(dir_temporario):
    origem = _criar_banco(dir_temporario / "origem.db")
    destino = dir_temporario / "backups"
    relatorio = backup_db.executar_backup(destino, {"tipo": "sqlite", "caminho": origem})

    alvo = dir_temporario / "restaurado.db"
    with pytest.raises(RuntimeError, match="--forcar"):
        backup_db.restaurar_backup(Path(relatorio["arquivo"]), alvo, forcar=False)
    assert not alvo.exists()


def test_restauracao_devolve_os_dados(dir_temporario):
    origem = _criar_banco(dir_temporario / "origem.db")
    destino = dir_temporario / "backups"
    relatorio = backup_db.executar_backup(destino, {"tipo": "sqlite", "caminho": origem})

    alvo = dir_temporario / "restaurado.db"
    backup_db.restaurar_backup(Path(relatorio["arquivo"]), alvo, forcar=True)

    conn = sqlite3.connect(alvo)
    try:
        total = conn.execute("SELECT count(*) FROM pacientes").fetchone()[0]
    finally:
        conn.close()
    assert total == 2


def test_poda_mantem_apenas_as_copias_recentes(dir_temporario):
    destino = dir_temporario / "backups"
    destino.mkdir()

    # Simula cinco backups antigos (só o nome importa para a poda).
    for indice in range(5):
        arquivo = destino / f"esus_2026010{indice}_120000.db"
        arquivo.write_bytes(b"x")

    removidos = backup_db.podar_antigos(destino, manter=2)
    restantes = sorted(arquivo.name for arquivo in destino.glob("esus_*.db"))

    assert len(removidos) == 3
    assert len(restantes) == 2


def test_poda_nao_apaga_arquivos_alheios(dir_temporario):
    destino = dir_temporario / "backups"
    destino.mkdir()
    importante = destino / "anotacoes_do_dba.txt"
    importante.write_text("não apague", encoding="utf-8")
    (destino / "esus_a.db").write_bytes(b"x")

    backup_db.podar_antigos(destino, manter=1)

    assert importante.exists()


def test_backup_de_banco_inexistente_falha_alto(dir_temporario):
    with pytest.raises(FileNotFoundError):
        backup_db.executar_backup(
            dir_temporario / "backups",
            {"tipo": "sqlite", "caminho": dir_temporario / "nao_existe.db"},
        )
