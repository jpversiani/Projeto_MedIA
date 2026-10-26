"""CLI da política de retenção (LGPD).

Uso, a partir de ``backend/``::

    python -m app.tools.retencao                # plano (padrão: não altera nada)
    python -m app.tools.retencao --executar     # aplica de verdade
    python -m app.tools.retencao --json         # saída para automação/cron

O padrão é **somente leitura**. Rodar sem ``--executar`` nunca apaga nada; a
opção existe para que o comando seja seguro de rodar em produção por engano.
"""

from __future__ import annotations

import argparse
import json
import sys

from app.core.database import SessionLocal
from app.services.retencao_dados import ExecucaoNaoConfirmada, ServicoRetencao


def _imprimir_tabela(linhas) -> None:
    print(f"{'REGRA':<38} {'AÇÃO':<11} {'PRAZO':>7} {'AFETADOS':>9}  BASE LEGAL")
    print("-" * 118)
    for item in linhas:
        base = item["base_legal"]
        if len(base) > 50:
            base = base[:47] + "..."
        print(
            f"{item['regra']:<38} {item['acao']:<11} "
            f"{item['retencao_dias']:>7} {item['afetados']:>9}  {base}"
        )


def principal(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.tools.retencao",
        description="Avalia e aplica a política de retenção de dados (LGPD Art. 16).",
    )
    parser.add_argument(
        "--executar",
        action="store_true",
        help="Aplica as regras destrutivas. Sem esta opção, apenas relata.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Saída em JSON (para cron/observabilidade)."
    )
    parser.add_argument(
        "--regra",
        action="append",
        dest="regras",
        help="Executa apenas a(s) regra(s) informada(s). Pode repetir.",
    )
    argumentos = parser.parse_args(argv)

    db = SessionLocal()
    servico = ServicoRetencao()

    try:
        if not argumentos.executar:
            plano = servico.plano(db)
            dados = [regra.como_dicionario() for regra in plano]
            if argumentos.json:
                print(
                    json.dumps(
                        {
                            "modo": "plano",
                            "regras": dados,
                            "total_afetavel": sum(
                                r["afetados"] for r in dados if r["acao"] != "REVISAR"
                            ),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                print("PLANO DE RETENÇÃO (nada foi alterado)\n")
                _imprimir_tabela(dados)
                print(
                    "\nPara aplicar: python -m app.tools.retencao --executar\n"
                    "Registros clínicos não são apagados: guarda mínima de 20 anos "
                    "(CFM 1.821/2007)."
                )
            return 0

        relatorio = servico.executar(
            db, regras=argumentos.regras, confirmar=True, ip_origem="cli"
        )
        if argumentos.json:
            print(json.dumps(relatorio, ensure_ascii=False, indent=2))
        else:
            print("RETENÇÃO EXECUTADA\n")
            _imprimir_tabela(relatorio["regras"])
            print(f"\nTotal de registros afetados: {relatorio['total_afetado']}")
            print("Evento EXECUTAR_RETENCAO_DADOS gravado na trilha de auditoria.")
        return 0
    except ExecucaoNaoConfirmada as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(principal())
