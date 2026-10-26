#!/usr/bin/env python3
"""Backup verificável do banco de dados do MedIA.

Um backup que não foi conferido não é um backup — é uma esperança. Este script
faz três coisas e recusa-se a fingir que fez a quarta:

1. **Copia** o banco de forma consistente (API de backup do SQLite, ou
   ``pg_dump`` quando o destino é PostgreSQL);
2. **Verifica** o resultado: SHA-256 registrado em manifesto, abertura do arquivo
   e ``PRAGMA integrity_check`` no caso do SQLite;
3. **Poda** backups antigos, mantendo as N cópias mais recentes;
4. **Restaura** mediante confirmação explícita (``--forcar``), porque sobrescrever
   o banco em uso é destrutivo.

Uso::

    python scripts/backup_db.py                      # backup do SQLite padrão
    python scripts/backup_db.py --manter 7           # retém 7 cópias
    python scripts/backup_db.py --verificar backups/esus_20261025_120000.db
    python scripts/backup_db.py --restaurar backups/esus_20261025_120000.db --forcar

Saída em JSON com ``--json``, para agendar por cron e monitorar.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
BACKUP_PADRAO = RAIZ / "backups"
BANCO_PADRAO = RAIZ / "backend" / "esus.db"
MANIFESTO = "manifesto.jsonl"


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def calcular_sha256(caminho: Path, blocos: int = 1 << 20) -> str:
    """SHA-256 em streaming — não carrega o arquivo inteiro na memória."""
    digesto = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(blocos), b""):
            digesto.update(bloco)
    return digesto.hexdigest()


def registrar_manifesto(destino: Path, entrada: Dict[str, Any]) -> None:
    """Anexa uma linha JSON ao manifesto de backups."""
    destino.mkdir(parents=True, exist_ok=True)
    with open(destino / MANIFESTO, "a", encoding="utf-8") as manifesto:
        manifesto.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def ler_manifesto(destino: Path) -> List[Dict[str, Any]]:
    caminho = destino / MANIFESTO
    if not caminho.exists():
        return []
    registros = []
    with open(caminho, encoding="utf-8") as manifesto:
        for linha in manifesto:
            linha = linha.strip()
            if not linha:
                continue
            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError:
                continue
    return registros


def podar_antigos(destino: Path, manter: int) -> List[Path]:
    """Remove os backups mais antigos, preservando os ``manter`` mais recentes.

    Só toca em arquivos que seguem o padrão gerado por este script (``esus_*`` ou
    ``pg_*``) — nunca apaga algo que o usuário tenha colocado na pasta.
    """
    if manter <= 0:
        return []
    candidatos = sorted(
        [
            arquivo
            for arquivo in destino.glob("*")
            if arquivo.is_file()
            and arquivo.name != MANIFESTO
            and (arquivo.name.startswith("esus_") or arquivo.name.startswith("pg_"))
        ],
        key=lambda arquivo: arquivo.stat().st_mtime,
        reverse=True,
    )
    removidos = []
    for arquivo in candidatos[manter:]:
        arquivo.unlink()
        removidos.append(arquivo)
    return removidos


# ----------------------------------------------------------------------
# SQLite
# ----------------------------------------------------------------------
def backup_sqlite(origem: Path, saida: Path) -> None:
    """Copia usando a API de backup do SQLite (consistente mesmo com o banco em uso).

    Um ``copy`` de arquivo pode capturar uma transação pela metade; a API de
    backup serializa o estado e produz um arquivo válido.
    """
    origem_conn = sqlite3.connect(f"file:{origem}?mode=ro", uri=True)
    try:
        destino_conn = sqlite3.connect(saida)
        try:
            origem_conn.backup(destino_conn)
        finally:
            destino_conn.close()
    finally:
        origem_conn.close()


def verificar_sqlite(caminho: Path) -> Dict[str, Any]:
    """Abre o backup e roda ``integrity_check`` — prova que o arquivo é legível."""
    conn = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    try:
        resultado = conn.execute("PRAGMA integrity_check").fetchone()
        integridade = resultado[0] if resultado else "sem resposta"
        tabelas = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0]
    finally:
        conn.close()
    return {"integridade": integridade, "tabelas": tabelas}


# ----------------------------------------------------------------------
# PostgreSQL
# ----------------------------------------------------------------------
def backup_postgres(url: str, saida: Path) -> None:
    """Usa ``pg_dump`` em formato custom (restaurável com ``pg_restore``)."""
    if shutil.which("pg_dump") is None:
        raise RuntimeError(
            "pg_dump não encontrado no PATH. Instale o cliente do PostgreSQL "
            "(postgresql-client) para fazer backup de um banco PostgreSQL."
        )
    subprocess.run(
        ["pg_dump", "--format=custom", "--file", str(saida), url],
        check=True,
        capture_output=True,
    )


def _detectar_origem(url: Optional[str], banco: Optional[Path]) -> Dict[str, Any]:
    """Resolve o que será copiado: um arquivo SQLite ou uma URL PostgreSQL."""
    if banco is not None:
        return {"tipo": "sqlite", "caminho": banco}

    if url is None:
        url = os.environ.get("DATABASE_URL", "").strip()

    if not url:
        return {"tipo": "sqlite", "caminho": BANCO_PADRAO}

    if url.startswith("sqlite"):
        # sqlite:///caminho/absoluto  ou  sqlite:///./relativo
        caminho = url.split("sqlite:///", 1)[-1]
        return {"tipo": "sqlite", "caminho": Path(caminho)}

    if url.startswith("postgresql") or url.startswith("postgres"):
        return {"tipo": "postgres", "url": url}

    raise RuntimeError(f"URL de banco não suportada para backup: {url}")


# ----------------------------------------------------------------------
# Comandos
# ----------------------------------------------------------------------
def executar_backup(
    destino: Path,
    origem: Optional[Dict[str, Any]] = None,
    manter: int = 7,
) -> Dict[str, Any]:
    """Faz o backup, confere e devolve o relatório."""
    origem = origem or _detectar_origem(None, None)
    destino.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if origem["tipo"] == "sqlite":
        arquivo_origem: Path = Path(origem["caminho"])
        if not arquivo_origem.exists():
            raise FileNotFoundError(f"Banco não encontrado: {arquivo_origem}")
        saida = destino / f"esus_{carimbo}.db"
        backup_sqlite(arquivo_origem, saida)
        verificacao = verificar_sqlite(saida)
        origem_descrita = str(arquivo_origem)
    else:
        saida = destino / f"pg_{carimbo}.dump"
        backup_postgres(origem["url"], saida)
        verificacao = {"integridade": "nao_verificavel_sem_servidor", "tabelas": None}
        origem_descrita = "postgresql://***"

    if verificacao["integridade"] not in ("ok", "nao_verificavel_sem_servidor"):
        saida.unlink(missing_ok=True)
        raise RuntimeError(
            f"Backup corrompido (integrity_check={verificacao['integridade']!r}); "
            "arquivo descartado."
        )

    sha256 = calcular_sha256(saida)
    entrada = {
        "arquivo": saida.name,
        "sha256": sha256,
        "bytes": saida.stat().st_size,
        "criado_em": datetime.now(timezone.utc).isoformat(),
        "origem": origem_descrita,
        "verificacao": verificacao,
    }
    registrar_manifesto(destino, entrada)

    removidos = podar_antigos(destino, manter)

    return {
        "arquivo": str(saida),
        "sha256": sha256,
        "bytes": entrada["bytes"],
        "tabelas": verificacao.get("tabelas"),
        "integridade": verificacao["integridade"],
        "podados": [str(arquivo) for arquivo in removidos],
    }


def verificar_backup(caminho: Path, destino: Optional[Path] = None) -> Dict[str, Any]:
    """Confere o SHA-256 contra o manifesto e testa a integridade do arquivo."""
    if not caminho.exists():
        raise FileNotFoundError(f"Backup não encontrado: {caminho}")

    sha256 = calcular_sha256(caminho)
    esperado = None
    for registro in ler_manifesto(destino or caminho.parent):
        if registro.get("arquivo") == caminho.name:
            esperado = registro.get("sha256")

    resultado: Dict[str, Any] = {
        "arquivo": str(caminho),
        "sha256": sha256,
        "sha256_no_manifesto": esperado,
        "confere": esperado is None or esperado == sha256,
    }

    if caminho.suffix == ".db":
        resultado.update(verificar_sqlite(caminho))

    if not resultado["confere"]:
        raise RuntimeError(
            "SHA-256 do arquivo não corresponde ao manifesto: o backup foi alterado "
            "ou corrompido."
        )
    if resultado.get("integridade") not in (None, "ok", "nao_verificavel_sem_servidor"):
        raise RuntimeError(f"integrity_check reprovou: {resultado['integridade']}")

    return resultado


def restaurar_backup(caminho: Path, destino_banco: Path, forcar: bool = False) -> Dict[str, Any]:
    """Copia o backup de volta sobre o banco. Exige ``--forcar``."""
    if not caminho.exists():
        raise FileNotFoundError(f"Backup não encontrado: {caminho}")
    if not forcar:
        raise RuntimeError(
            "Restaurar sobrescreve o banco em uso. Confirme com --forcar "
            "(e pare a aplicação antes)."
        )

    if caminho.suffix == ".gz":
        with gzip.open(caminho, "rb") as origem, open(destino_banco, "wb") as saida:
            shutil.copyfileobj(origem, saida)
    else:
        shutil.copy2(caminho, destino_banco)

    return {
        "restaurado_de": str(caminho),
        "para": str(destino_banco),
        "sha256": calcular_sha256(destino_banco),
    }


def principal(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/backup_db.py",
        description="Backup verificável do banco do MedIA.",
    )
    parser.add_argument("--destino", type=Path, default=BACKUP_PADRAO)
    parser.add_argument("--banco", type=Path, default=None, help="Arquivo SQLite de origem.")
    parser.add_argument("--url", default=None, help="DATABASE_URL (PostgreSQL).")
    parser.add_argument("--manter", type=int, default=7, help="Cópias a reter (padrão 7).")
    parser.add_argument("--json", action="store_true", help="Saída em JSON.")
    parser.add_argument("--verificar", type=Path, default=None, help="Verifica um backup.")
    parser.add_argument("--restaurar", type=Path, default=None, help="Restaura um backup.")
    parser.add_argument("--forcar", action="store_true", help="Confirma a restauração.")
    argumentos = parser.parse_args(argv)

    try:
        if argumentos.verificar:
            resultado = verificar_backup(argumentos.verificar, argumentos.destino)
            acao = "verificacao"
        elif argumentos.restaurar:
            banco = argumentos.banco or BANCO_PADRAO
            resultado = restaurar_backup(argumentos.restaurar, banco, argumentos.forcar)
            acao = "restauracao"
        else:
            origem = _detectar_origem(argumentos.url, argumentos.banco)
            resultado = executar_backup(argumentos.destino, origem, argumentos.manter)
            acao = "backup"
    except Exception as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1

    if argumentos.json:
        print(json.dumps({"acao": acao, **resultado}, ensure_ascii=False, indent=2))
    else:
        print(f"[{acao}] {resultado}")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
