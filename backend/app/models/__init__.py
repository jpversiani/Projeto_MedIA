"""Registro central dos modelos ORM do PEC (SQLAlchemy 2.0).

Importar este pacote garante que todas as classes estejam registradas no
``Base.metadata`` antes de qualquer configuração de mappers (relationships
resolvidas por nome de classe).
"""

from app.models.atendimento import AtendimentoProblema, AtendimentoSOAP
from app.models.atendimento_offline import AtendimentoOffline, StatusSincronizacao
from app.models.cidadao import Cidadao
from app.models.copiloto import CopilotoAuditoria
from app.models.estabelecimento import Equipe, Estabelecimento
from app.models.fila import FilaAcolhimento
from app.models.prontuario import ProntuarioProblema
from app.models.profissional import Profissional

__all__ = [
    "AtendimentoProblema",
    "AtendimentoSOAP",
    "AtendimentoOffline",
    "StatusSincronizacao",
    "Cidadao",
    "CopilotoAuditoria",
    "Equipe",
    "Estabelecimento",
    "FilaAcolhimento",
    "ProntuarioProblema",
    "Profissional",
]
