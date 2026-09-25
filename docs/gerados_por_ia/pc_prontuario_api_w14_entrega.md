O arquivo já existe no projeto. Vou verificar o estado do git e rodar os testes para validar a implementação:
A implementação já existe e está completa. Vou executar os testes para validar:
A tarefa já está implementada e validada. O arquivo `backend/app/api/v1/prontuario.py` contém exatamente o solicitado, e os 4 testes em `backend/tests/test_prontuario.py` passaram.

**Endpoints implementados** (`backend/app/api/v1/prontuario.py`):

| Rota | Função | Códigos HTTP |
|---|---|---|
| `GET /prontuario/{cns}` | `obter_resumo_prontuario` :143 — problemas ativos (Lista de Problemas + episódios SOAP), alergias e medicamentos em uso | 200 / 404 / 422 |
| `GET /prontuario/{cns}/evolucoes` | `listar_evolucoes_prontuario` :237 — paginação por offset (`skip`/`limit≤100`) | 200 / 404 / 422 |
| `POST /prontuario/{cns}/alergia` | `registrar_alergia_prontuario` :274 — duplicidade → 422 | 201 / 404 / 422 |
| `POST /prontuario/{cns}/problema` | `registrar_problema_prontuario` :313 — validação CIAP-2/CID-10 e duplicidade | 201 / 404 / 422 |

**Conformidade verificada:**
- `Depends(get_db)` em todas as rotas; CNS validado com `Path(pattern=r"^\d{15}$")`
- Schemas Pydantic v2 em `backend/app/schemas/prontuario.py` (validador de código por terminologia, `Literal` para CIAP2/CID10)
- Router registrado em `backend/app/api/v1/router.py:17`
- Docstrings/mensagens em pt-BR; SQLAlchemy 2.0 tipado

```
4 passed, 18 warnings in 0.23s
```

Nenhuma alteração foi necessária — o código está pronto e em conformidade com as diretrizes.