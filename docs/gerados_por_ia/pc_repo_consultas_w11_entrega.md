A tarefa tem como alvo `backend/app/repositories/consultas_repo.py` — o projeto principal já possui esse arquivo. Vou analisá-lo junto com os repositórios e modelos relacionados para seguir as convenções.
O projeto principal já contém esse arquivo. Vou verificar o contexto do git e as dependências para decidir onde o arquivo de destino deve ficar.
O arquivo existe no projeto principal como não rastreado (de uma execução anterior), mas o meu diretório de trabalho atual (sandbox) está vazio — o caminho de destino `backend/app/repositories/consultas_repo.py` é relativo ao cwd. Vou verificar as dependências nas quais a implementação se baseia.
O arquivo existente no projeto principal chama `ValidadorCNS.validar_ou_lancar()` / `ValidadorCNS.limpar()` — métodos que **não existem** em `validacao_cns.py` (ele possui apenas métodos de instância `validar()`, `digitos`, `formatar()`). Isso causaria falha em tempo de execução. Vou verificar as convenções de teste e os registros de modelos antes de escrever uma implementação corrigida no caminho alvo do sandbox.
Ambiente confirmado: Python 3.12.3, SQLAlchemy 2.0.54, Pydantic 2.13.5. Agora vou criar o arquivo alvo no diretório de trabalho com uma implementação corrigida (usando apenas APIs `ValidadorCNS` existentes).
Arquivo criado. Agora vou verificar de forma funcional carregando-o no contexto real do backend e testando cada operação com o banco de dados SQLite em memória.
Strict mode exige membros de enum em vez de strings — correto para uma tipagem estrita. Vou corrigir o script de verificação.
Bug no script de teste (não do módulo) — o loop tentava capturar `None` como uma classe de exceção. Reescrevendo essa seção de forma explícita:
O script novamente: CNS `999...` é rejeitado pelo validador no nível do schema; para testar `ProfissionalNaoEncontradoError` eu preciso de um CNS válido mas não registrado. Corrigindo:
Verificação funcional concluída. Executando verificações estáticas (myp/ruff se disponíveis) e compilando:
Concluído. Arquivo alvo criado em `backend/app/repositories/consultas_repo.py` (sandbox), 100% em Português do Brasil, Python 3.12 + SQLAlchemy 2.0 (`Mapped`/`mapped_column`) + Pydantic v2 estrito.

**`ConsultasRepository`** — operações implementadas:
- `agendar` — CNS validado pelo algoritmo oficial do MS/DATASUS, conflito de agenda do profissional, CIAP-2/CID-10 normalizados e data futura obrigatória
- `listar_por_profissional` — cronológica ou priorizada (opção `ordenar_por_prioridade`)
- `listar_por_dia` — ordenação SQL via `case()` pelos pesos Manchester (Vermelho→Azul), filtros opcionais de UBS/profissional
- `cancelar` — motivo obrigatório + auditoria (`cancelado_por`/`cancelado_em`) e transição de status controlada
- `historico_por_cns` — linha de vida longitudinal (mais recente primeiro)
- `contadores_absenteismo_por_cns` — taxa = faltas / (realizadas + faltas) em `AbsenteismoResumo`
- Apoio: `registrar_atendimento` / `registrar_falta` (alimentam o no-show)

**Verificação**: execução funcional contra os modelos reais (`Cidadao`, `Profissional`, `Estabelecimento`) no SQLite em memória com o venv do projeto — agendamento, ordenação Manchester, conflito de agenda, cancelamento, histórico e contadores (taxa 50%) validados; `py_compile` OK (não há mypy/ruff no ambiente).

Observação: existe uma cópia anterior deste arquivo em `Projeto_MedIA/backend/app/repositories/consultas_repo.py` (não rastreada no git) que chama `ValidadorCNS.limpar()`/`validar_ou_lancar()` — métodos que não existem no serviço de validação e quebrariam em runtime. A versão criada aqui corrige isso usando a API real (`ValidadorCNS(...).validar()`/`.digitos`).