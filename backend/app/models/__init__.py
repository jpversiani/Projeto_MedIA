# Importa explicitamente todos os modelos SQLAlchemy para registro no Base
from app.models.cidadao import Cidadao
from app.models.estabelecimento import Estabelecimento, Equipe
from app.models.profissional import Profissional
from app.models.fila import FilaAcolhimento
from app.models.atendimento import AtendimentoSOAP, AtendimentoProblema
Atendimento = AtendimentoSOAP  # Alias para compatibilidade com serviços legados e testes
from app.models.atendimento_offline import AtendimentoOffline, StatusSincronizacao, SyncState
from app.models.prontuario import ProntuarioProblema
from app.models.terminologia import CIAP2, CID10
from app.models.telemedicina import SalaVirtual, Teleconsulta, DocumentoEmitido
from app.models.farmacia import Receita, ReceitaItem, Dispensacao, DispensacaoItem
from app.models.copiloto import CopilotoAuditoria
from app.models.mensageria import MensagemPreventiva, AlertaBuscaAtiva
from app.models.convenios import Operadora, Plano, GuiaTISS, LancamentoFinanceiro
from app.models.usuario import Usuario, VinculoClinica, PapelUsuarioEnum, AuditTrail
