O projeto real está na raiz do workspace. Vou ler os arquivos-chave para seguir as convenções existentes.
Vou verificar os seeds (formato de CNS usado nos dados) e o modelo de terminologia para alinhar validações.
Contexto mapeado. Vou verificar dois detalhes de runtime (Pydantic `from_attributes` com atributo ausente e `Path(pattern=...)`) e então implementar.
Agora os schemas Pydantic v2:
Agora o arquivo alvo obrigatório — as rotas REST do Prontuário:
Pequenas correções (f-string desnecessária e constante não usada) e registro do router:
Agora os testes de verificação:
4/4 testes passaram. Agora a suíte completa para garantir que nada quebrou:
Os 7 erros de coleta são pré-existentes (módulos ausentes como `services.analytics`, `services.sisab_export` — não relacionados ao prontuário). Vou confirmar rodando a suíte que coleta, sem esses módulos quebrados:
Módulos afetados diretamente pelas mudanças passam (8/8). Vou inspecionar as falhas restantes para confirmar que são pré-existentes:
Falhas confirmadas como alheias ao prontuário (testes de conteúdo de arquivo JS do WebRTC). Verificação rigorosa de baseline — vou esconder temporariamente minhas 2 modificações em arquivos existentes e rodar o mesmo subconjunto:
Curioso: com minhas mudanças há menos falhas que no baseline. Vou comparar as listas exatas de testes com falha para garantir que nenhuma falha nova foi introduzida:
As 4 falhas extras no baseline são em `test_api_telemedicina.py` e somem com minhas mudanças — sinal de acoplamento estranho. Vou examinar o erro real dessas falhas no baseline:
404 no baseline. Vou rodar o mesmo teste isolado com minhas mudanças ativas para ver a diferença real:
Mistério resolvido: o `git stash` também reverteu um registro de telemedicina **pré-existente e não commitado** — as 4 falhas "extras" do baseline eram artefato disso, não regressão minha. Verificação final da suíte executável completa:
Endpoints REST do Prontuário do Cidadão implementados e verificados (4/4 testes novos passando).

**Arquivos criados/alterados:**
- `backend/app/api/v1/prontuario.py` (alvo obrigatório) — rotas com `Depends(get_db)`, docstrings e mensagens em PT-BR:
  - `GET /prontuario/{cns}` — resumo com identificação SUS, problemas ativos (merge Lista de Problemas + episódios SOAP, sem duplicidades por CIAP-2/CID-10), alergias autorreferidas e medicamentos em uso derivados das prescrições do plano SOAP (`plano_prescricoes`, formato `Medicamento - detalhe`, dedupe case-insensitive).
  - `GET /prontuario/{cns}/evolucoes` — atendimentos SOAP paginados por offset (`skip`/`limit`, máx. 100) com envelope `{total, skip, limit, itens}`.
  - `POST /prontuario/{cns}/alergia` — 201; duplicidade → 422.
  - `POST /prontuario/{cns}/problema` — 201; valida código por terminologia (regex oficial CIAP-2/CID-10, igual a `models/receita.py`), duplicidade ativa → 422.
  - CNS no path com `pattern=r"^\d{15}$"` → 422 automático; cidadão inexistente → 404.
- `backend/app/models/prontuario.py` — `ProntuarioProblema` em SQLAlchemy 2.0 tipado (`Mapped`/`mapped_column`), com `data_registro` timezone-aware UTC.
- `backend/app/schemas/prontuario.py` — schemas Pydantic v2 (`Literal`, `StringConstraints`, `model_validator`, `from_attributes`).
- `backend/app/models/__init__.py` e `backend/app/api/v1/router.py` — registro do modelo e do router.
- `backend/tests/test_prontuario.py` — 4 testes cobrindo 422 (CNS malformado, código malformado, terminologia inválida, duplicidades, limites de paginação), 404, 201 e o fluxo completo do resumo.

**Verificação:** `test_prontuario.py` 4/4; suíte coletável 28 passed — as 10 falhas restantes são todas em `test_webrtc_manager.py` (assertions de conteúdo de JS de outra task, pré-existentes) e 7 módulos de teste quebram na coleta por módulos ausentes (`services.analytics`, `services.sisab_export`), também pré-existentes e não relacionados.