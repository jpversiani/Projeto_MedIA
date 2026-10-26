"""Endpoints de conformidade e ciclo de vida do dado (LGPD).

O encarregado de dados (DPO) precisa conseguir responder "o que este sistema
guarda e por quanto tempo" sem abrir o banco. Aqui ficam duas rotas:

* ``GET /conformidade/retencao`` — o plano: cada regra, o prazo, a base legal e
  quantos registros seriam afetados hoje. **Não altera nada.**
* ``POST /conformidade/retencao/executar`` — aplica as regras destrutivas. Exige
  ``{"confirmar": true}`` no corpo e papel de administrador, porque apagar dado
  pessoal não tem desfazer e precisa de rastro.

A execução grava ``EXECUTAR_RETENCAO_DADOS`` na trilha de auditoria.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rbac import (
    PAPEIS_GESTAO,
    ContextoClinico,
    dependencias_rbac,
    get_contexto_clinico,
)
from app.services.retencao_dados import ExecucaoNaoConfirmada, ServicoRetencao

# Leitura para gestão; execução é restrita a ADMIN (verificado na rota).
router = APIRouter(
    prefix="/conformidade",
    tags=["Conformidade"],
    dependencies=dependencias_rbac(*PAPEIS_GESTAO),
)


class ExecucaoRetencaoRequest(BaseModel):
    confirmar: bool = Field(
        default=False,
        description="Deve ser true. Protege contra execução acidental.",
    )
    regras: Optional[List[str]] = Field(
        default=None,
        description="Lista de regras a executar. Vazio/omitido = todas as destrutivas.",
    )


@router.get("/retencao")
def consultar_plano_retencao(db: Session = Depends(get_db)):
    """Plano de retenção: prazos, base legal e volume afetado (somente leitura)."""
    servico = ServicoRetencao()
    plano = servico.plano(db)

    return {
        "consultado_em": datetime.now(timezone.utc).isoformat(),
        "aviso": (
            "Este plano não altera dados. Registros clínicos NÃO são apagados: a "
            "guarda mínima do prontuário é de 20 anos (CFM 1.821/2007 e 2.314/2022) "
            "e a anonimização de dado clínico é decisão humana, não automática."
        ),
        "regras": [regra.como_dicionario() for regra in plano],
        "total_afetavel": sum(
            regra.afetados for regra in plano if regra.acao != "REVISAR"
        ),
        "total_para_revisao": sum(
            regra.afetados for regra in plano if regra.acao == "REVISAR"
        ),
    }


@router.post("/retencao/executar", status_code=status.HTTP_200_OK)
def executar_retencao(
    dados: ExecucaoRetencaoRequest,
    request: Request,
    db: Session = Depends(get_db),
    contexto: ContextoClinico = Depends(get_contexto_clinico),
):
    """Aplica a política de retenção (irreversível). Somente administrador."""
    # O router já exige um dos papéis de gestão; a checagem explícita garante que
    # só ADMIN chegue aqui mesmo se PAPEIS_GESTAO ganhar outros papéis no futuro.
    papel = getattr(getattr(contexto, "papel", None), "value", None)
    if contexto is not None and papel is not None and papel != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente administrador pode executar a política de retenção.",
        )

    servico = ServicoRetencao()
    try:
        relatorio = servico.executar(
            db,
            regras=dados.regras,
            confirmar=dados.confirmar,
            usuario_id=getattr(contexto, "usuario_id", None),
            ip_origem=getattr(getattr(request, "client", None), "host", None),
        )
    except ExecucaoNaoConfirmada as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)
        ) from erro

    return relatorio
