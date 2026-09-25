O arquivo `backend/app/repositories/consultas_repo.py` já existe no projeto e está completo (811 linhas). Vou apenas validar que está íntegro e sem erros:
O arquivo `backend/app/repositories/consultas_repo.py` já existe no repositório e atende integralmente à tarefa — compilado sem erros (811 linhas). Ele já contém:

- **`ConsultasRepository`** (SQLAlchemy 2.0, `Mapped`/`mapped_column`, tipagem estrita)
- **`agendar()`** — validação CNS (algoritmo MS/DATASUS via `ValidadorCNS`), conflito de agenda, CIAP-2/CID-10
- **`listar_por_profissional()`** e **`listar_por_dia()`** — com ordenação por prioridade Manchester (Vermelho → Azul via `case` SQL)
- **`cancelar()`** — motivo obrigatório + auditoria (`cancelado_por`, `cancelado_em`)
- **`historico_por_cns()`** — linha de vida do cidadão, decrescente
- **`contadores_absenteismo_por_cns()`** — taxa de no-show = faltas / (realizadas + faltas)
- Schemas Pydantic v2 (`ConsultaAPSCreate`, `ConsultaAPSRead`, `AbsenteismoResumo`), exceções de domínio e docstrings/mensagens em pt-BR

Nenhuma alteração foi necessária.