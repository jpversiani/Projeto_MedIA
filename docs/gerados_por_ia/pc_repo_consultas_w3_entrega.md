O projeto principal está em `/home/jpversiani/Projeto_MedIA/backend`. Vou ler os repositórios e modelos existentes para alinhar as convenções antes de criar o arquivo.
Vou verificar os demais repositórios e a configuração de versões para alinhar o estilo completo.
Convenções mapeadas. Vou conferir o modelo de Estabelecimento para os relacionamentos e então escrever o arquivo.
Agora vou criar o arquivo-alvo no sandbox com o padrão do projeto (Base compartilhada de `app.core.database`, SQLAlchemy 2.0, Pydantic v2).
Ambiente confirmado (Python 3.12, SQLAlchemy 2.0.54, Pydantic 2.13.5). Criando o arquivo-alvo:
Arquivo criado. Agora vou verificar executando um teste de fumaça em `/tmp/opencode` com um pacote `app` de apoio (réplica dos módulos reais do projeto):
Vou limpar os hacks de import no teste antes de rodar:
O modelo real `Cidadao` tem relacionamentos com `FilaAcolhimento`/`AtendimentoSOAP`. Vou copiar esses modelos para o stub:
A ordenação Manchester está correta — o teste não considerava a primeira consulta VERDE (9h). Corrigindo a expectativa:
Todos os 17 checks passaram. Verificação final de sintaxe e tipagem (se disponível):
Arquivo criado e validado. Resumo:

**`backend/app/repositories/consultas_repo.py`** — self-contained, alinhado ao padrão do projeto (Base compartilhada de `app.core.database`, integração com `Cidadao`/`Profissional`/`Estabelecimento` e reuso do `ValidadorCNS` oficial do MS):

- **Modelo ORM SQLAlchemy 2.0**: `ConsultaAPS` (tabela `consultas_aps`) com `Mapped`/`mapped_column`, FKs, índices compostos (profissional+data, cidadão+data) e relações com `lazy="selectin"`
- **Enums `StrEnum`**: `StatusConsulta` (AGENDADA→FALTA/CANCELADA), `PrioridadeManchester` (5 cores com ordem canônica), `TipoConsultaAPS`
- **`ConsultasRepository`** (sessão síncrona):
  - `agendar()` — valida CNS (algoritmo oficial do MS), CIAP-2/CID-10, existência dos participantes e **conflito de sobreposição de agenda** do profissional
  - `listar_por_profissional()` — agenda cronológica com filtros de período
  - `listar_por_dia()` — **ordenação por prioridade Manchester** (Vermelho→Azul, via expressão SQL `case`) e por horário
  - `cancelar()` — motivo obrigatório + trilha de auditoria (quem/quando), só nos status mutáveis
  - `registrar_falta()` / `registrar_atendimento()` — desfechos para absenteísmo
  - `historico_por_cns()` — linha de vida longitudinal do cidadão
  - `contadores_absenteismo_por_cns()` — totais + taxa no-show (`faltas/(realizadas+faltas)`)
- **Schemas Pydantic v2** strict: `ConsultaAPSCreate`, `ConsultaCancelamentoInput`, `ConsultaAPSRead` (com `de_orm`) e `AbsenteismoResumo`; exceções de domínio dedicadas (conflito de agenda, transição inválida, lookups)

Verificação executada em `/tmp/opencode` (venv do projeto: SQLAlchemy 2.0.54, Pydantic 2.13.5, Python 3.12): **17/17 checks** — agendamento, conflito, ordenação Manchester, cancelamento, no-show, histórico, contadores (taxa 50% corretamente calculada) e todas as validações Pydantic.