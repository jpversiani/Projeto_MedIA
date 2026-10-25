"""Autorização por papel (RBAC) e escopo de tenant (multi-clínica).

Antes deste módulo existia apenas **autenticação**: o router clínico exigia
Bearer token, mas nenhuma rota verificava *quem* era o usuário. Na prática,
qualquer pessoa autenticada — inclusive uma recepcionista ou um paciente —
podia emitir receita, ler prontuário e exportar TISS.

Este módulo acrescenta duas coisas:

1. **RBAC** — cada módulo de rota declara os papéis aceitos
   (`dependencias_rbac(*PAPEIS_...)`).
2. **Escopo de tenant** — `filtrar_tenant()` restringe consultas à clínica
   ativa gravada no token, e `exigir_mesmo_estabelecimento()` impede escrita
   cruzada entre unidades.

Regra de compatibilidade (importante): a autorização só é aplicada quando
``settings.require_auth`` está ligado — o mesmo interruptor que já governa a
autenticação. Em desenvolvimento (padrão) a v1 segue utilizável sem token e a
suíte existente continua válida; em produção e nos testes que ligam o
interruptor, o RBAC é obrigatório.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import PapelUsuarioEnum


# ----------------------------------------------------------------------
# Papéis (matriz de acesso por área)
# ----------------------------------------------------------------------
PAPEIS_CLINICOS: tuple[PapelUsuarioEnum, ...] = (
    PapelUsuarioEnum.MEDICO,
    PapelUsuarioEnum.ADMIN,
)

PAPEIS_ACOLHIMENTO: tuple[PapelUsuarioEnum, ...] = (
    PapelUsuarioEnum.MEDICO,
    PapelUsuarioEnum.RECEPCAO,
    PapelUsuarioEnum.ADMIN,
)

PAPEIS_CADASTRO: tuple[PapelUsuarioEnum, ...] = (
    PapelUsuarioEnum.MEDICO,
    PapelUsuarioEnum.RECEPCAO,
    PapelUsuarioEnum.ADMIN,
    PapelUsuarioEnum.FARMACEUTICO,
)

PAPEIS_FARMACIA: tuple[PapelUsuarioEnum, ...] = (
    PapelUsuarioEnum.FARMACEUTICO,
    PapelUsuarioEnum.MEDICO,
    PapelUsuarioEnum.ADMIN,
)

PAPEIS_FATURAMENTO: tuple[PapelUsuarioEnum, ...] = (
    PapelUsuarioEnum.ADMIN,
    PapelUsuarioEnum.MEDICO,
)

PAPEIS_GESTAO: tuple[PapelUsuarioEnum, ...] = (
    PapelUsuarioEnum.ADMIN,
)


# ----------------------------------------------------------------------
# Contexto de autorização
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ContextoClinico:
    """Usuário autenticado + clínica ativa + papel naquela clínica."""

    usuario: object
    estabelecimento_id: Optional[int]
    papel: Optional[PapelUsuarioEnum]
    profissional_id: Optional[int] = None
    is_superuser: bool = False

    def tem_papel(self, *papeis: PapelUsuarioEnum) -> bool:
        if self.is_superuser:
            return True
        return self.papel in papeis


def get_contexto_clinico(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[ContextoClinico]:
    """Resolve o contexto do usuário a partir do token.

    Retorna ``None`` quando a autenticação está desligada (desenvolvimento),
    exatamente como ``settings.require_auth`` governa o router clínico. O
    import de ``get_current_user`` é local para não criar ciclo de importação
    entre ``app.core`` e ``app.api``.
    """
    if not settings.require_auth:
        return None

    from app.api.v1.auth import get_current_user
    from app.models.usuario import VinculoClinica

    usuario, clinica_id = get_current_user(
        request=request, authorization=authorization, db=db
    )

    if usuario.is_superuser:
        return ContextoClinico(
            usuario=usuario,
            estabelecimento_id=clinica_id,
            papel=PapelUsuarioEnum.ADMIN,
            is_superuser=True,
        )

    if clinica_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Token sem clínica ativa. Selecione uma unidade em "
                "POST /api/v1/auth/switch-clinic."
            ),
        )

    vinculo = (
        db.query(VinculoClinica)
        .filter(
            VinculoClinica.usuario_id == usuario.id,
            VinculoClinica.estabelecimento_id == clinica_id,
        )
        .first()
    )
    if vinculo is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não possui vínculo com a clínica ativa do token.",
        )

    return ContextoClinico(
        usuario=usuario,
        estabelecimento_id=clinica_id,
        papel=vinculo.papel,
        profissional_id=vinculo.profissional_id,
    )


# ----------------------------------------------------------------------
# Dependências de autorização
# ----------------------------------------------------------------------
def requer_papeis(*papeis: PapelUsuarioEnum):
    """Cria a dependência que exige um dos papéis informados."""

    def dependencia(
        contexto: Optional[ContextoClinico] = Depends(get_contexto_clinico),
    ) -> Optional[ContextoClinico]:
        if contexto is None:
            # Autenticação desligada (desenvolvimento): nada a autorizar.
            return None
        if contexto.is_superuser:
            return contexto
        if contexto.papel is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário sem papel definido na clínica ativa.",
            )
        if contexto.papel not in papeis:
            permitidos = ", ".join(sorted(p.value for p in papeis))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acesso negado para o papel {contexto.papel.value}. "
                    f"Perfis autorizados: {permitidos}."
                ),
            )
        return contexto

    return dependencia


def dependencias_rbac(*papeis: PapelUsuarioEnum) -> list:
    """Lista pronta para ``APIRouter(dependencies=...)``."""
    return [Depends(requer_papeis(*papeis))]


# ----------------------------------------------------------------------
# Escopo de tenant
# ----------------------------------------------------------------------
def filtrar_tenant(query, modelo, contexto: Optional[ContextoClinico]):
    """Restringe a consulta à clínica ativa do token.

    Sem contexto (desenvolvimento), a consulta segue intacta. Superusuário
    enxerga todas as unidades. Modelos sem ``estabelecimento_id`` também
    seguem intactos — nesse caso o controle é por papel, não por tenant.
    """
    if contexto is None or contexto.is_superuser:
        return query
    coluna = getattr(modelo, "estabelecimento_id", None)
    if coluna is None:
        return query
    if contexto.estabelecimento_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token sem clínica ativa. Selecione uma unidade antes de continuar.",
        )
    return query.filter(coluna == contexto.estabelecimento_id)


def exigir_mesmo_estabelecimento(
    estabelecimento_id_do_objeto: Optional[int],
    contexto: Optional[ContextoClinico],
    *,
    acao: str = "acessar",
) -> None:
    """Bloqueia acesso/escrita em registro de outra unidade."""
    if contexto is None or contexto.is_superuser:
        return
    if contexto.estabelecimento_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token sem clínica ativa. Selecione uma unidade antes de continuar.",
        )
    if estabelecimento_id_do_objeto is None:
        # Registro legado sem unidade não pode ser lido por tenant algum.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Registro sem unidade vinculada não pode ser acessado ({acao}).",
        )
    if int(estabelecimento_id_do_objeto) != int(contexto.estabelecimento_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Registro pertence a outra unidade. Acesso negado para {acao}.",
        )
