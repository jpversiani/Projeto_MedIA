# Importa explicitamente todos os modelos SQLAlchemy para registro no Base

# Alias público para compatibilidade com serviços legados e testes.
Atendimento = None

from app.models.atendimento import AtendimentoProblema  # noqa: F401
from app.models.atendimento import AtendimentoSOAP
from app.models.agendamento import Agendamento  # noqa: F401
from app.models.agendamento import TipoAtendimento  # noqa: F401
from app.models.agendamento import StatusAgendamento  # noqa: F401
from app.models.atendimento_offline import AtendimentoOffline  # noqa: F401
from app.models.atendimento_offline import StatusSincronizacao  # noqa: F401
from app.models.atendimento_offline import SyncState  # noqa: F401
from app.models.cidadao import Cidadao  # noqa: F401
from app.models.convenios import Operadora  # noqa: F401
from app.models.convenios import Plano  # noqa: F401
from app.models.convenios import GuiaTISS  # noqa: F401
from app.models.convenios import LancamentoFinanceiro  # noqa: F401
from app.models.documento_cfm import DocumentoCFM  # noqa: F401
from app.models.estabelecimento import Estabelecimento  # noqa: F401
from app.models.estabelecimento import Equipe  # noqa: F401
from app.models.farmacia import Receita  # noqa: F401
from app.models.farmacia import ReceitaItem  # noqa: F401
from app.models.farmacia import Dispensacao  # noqa: F401
from app.models.farmacia import DispensacaoItem  # noqa: F401
from app.models.fila import FilaAcolhimento  # noqa: F401
from app.models.mensageria import MensagemPreventiva  # noqa: F401
from app.models.mensageria import AlertaBuscaAtiva  # noqa: F401
from app.models.prontuario import ProntuarioProblema  # noqa: F401
from app.models.profissional import Profissional  # noqa: F401
from app.models.telemedicina import SalaVirtual  # noqa: F401
from app.models.telemedicina import Teleconsulta  # noqa: F401
from app.models.telemedicina import DocumentoEmitido  # noqa: F401
from app.models.terminologia import CIAP2  # noqa: F401
from app.models.terminologia import CID10  # noqa: F401
from app.models.terminologia import CID11  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.usuario import VinculoClinica  # noqa: F401
from app.models.usuario import PapelUsuarioEnum  # noqa: F401
from app.models.usuario import AuditTrail  # noqa: F401
from app.models.copiloto import CopilotoAuditoria  # noqa: F401

# Mantém o alias público para compatibilidade
Atendimento = AtendimentoSOAP
