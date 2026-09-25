O projeto principal está no diretório pai. Vou estudar as convenções existentes antes de criar o arquivo.
O projeto já contém um `consultas_repo.py`. Vou verificar o estado do git e as dependências reais (modelos, validador de CNS, Base) para garantir correção.
Sandboxes vazias → o entregável vai no meu diretório de trabalho. Vou confirmar o padrão dos outros repositórios antes de escrever.
Convenções confirmadas. Escrevendo o arquivo no diretório de trabalho do sandbox:
Arquivo criado. Agora vou validá-lo funcionalmente (import + operações de agenda em SQLite em memória) contra os módulos reais do projeto:
Erro no teste (minha asserção contava consultas do João como da Maria). Corrigindo:
Comportamento correto do módulo (CNS malformado → `CNSInvalidoError`). Corrigindo o teste para usar um CNS válido porém desconhecido e limpando resíduo:
Validação funcional OK. Agora verificação estática (sintaxe, ruff/pyflakes, mypy se disponíveis):
Concluído. Arquivo criado em `backend/app/repositories/consultas_repo.py` (sandbox), idêntico ao canônico do projeto e validado funcionalmente contra os módulos reais (`ValidadorCNS`, `Cidadao`, `Profissional`, `Estabelecimento`, `Base`).

**Entrega — `ConsultasRepository` (SQLAlchemy 2.0 + Pydantic v2, tipagem estrita, pt-BR):**
- **Agendar consulta APS**: CNS validado pelo algoritmo oficial MS/DATASUS, conflito de agenda do profissional (`ConflitoDeAgendaError`), CIAP-2/CID-10 com regex canônica, prioridade Manchester
- **Listagens**: `listar_por_profissional` (cronológica ou priorizada) e `listar_por_dia` com ordenação SQL via `case()` — Vermelho > Laranja > Amarelo > Verde > Azul
- **Cancelamento** com motivo obrigatório, `cancelado_por`/`cancelado_em` e bloqueio de transições inválidas (`AGENDADA`/`CONFIRMADA` apenas)
- **Histórico longitudinal por CNS** (linha de vida, decrescente) + desfechos `registrar_atendimento`/`registrar_falta`
- **Absenteísmo (no-show)**: `AbsenteismoResumo` com taxa `faltas/(realizadas+faltas)` em %, calculada por agregação SQL

**Verificação executada** (SQLite em memória, Python 3.12 + SQLAlchemy 2.1 + Pydantic 2.13): agendamento, recusa de sobreposição de agenda, ordenação Manchester exata, cancelamento + re-cancelamento recusado, histórico por CNS com formatação, taxa de absenteísmo (50% e 0%), erros de domínio (`CNSInvalidoError`, `CidadaoNaoEncontradoError`, `EstabelecimentoNaoEncontradoError`, `TransicaoDeStatusInvalidaError`) e serialização `ConsultaAPSRead.de_orm` — 10/10 blocos OK.