O Pydantic não está instalado (o pytest está), então farei a integração com o Pydantic v2 opcional. Vou gerar vetores de teste CNS válidos primeiro:
Prefix `10000300000000` requires DV=10 (not representable) — good negative test vector. Now creating the module:
Preciso corrigir dois problemas: um auxiliar de teste defeituoso e a falta do classmethod `calcular_digito_verificador`:
A verificação de substring na mensagem de erro diferencia maiúsculas de minúsculas ("Dígito" vs "dígito"). Corrigindo o teste:
All 13 tests pass both via `__main__` and pytest. Final review of the file:
Concluído. Arquivo criado: `backend/app/services/validacao_cns.py` (+ `__init__.py` dos pacotes para importação `backend.app.services.validacao_cns`).

**Implementação** (`backend/app/services/validacao_cns.py`):
- `ValidadorCNS` — algoritmo oficial MS/DATASUS: 15 dígitos, primeiro dígito `1/2/7/8/9`, soma ponderada com pesos **15 → 1** múltipla de **11**; CNS **provisório (7/8/9)** e **definitivo (1/2)** identificados via `e_provisorio`/`e_definitivo`.
- `validar()` lança `CNSInvalidoError` (subclasse de `ValueError`) com mensagens em PT-BR; `e_valido` valida sem exceção.
- `formatar()` / `__str__` na forma canônica `000 0000 0000 000`; normaliza `.`, `-` e espaços.
- `calcular_digito_verificador()` calcula o DV (15º dígito) de um prefixo de 14 dígitos.
- Tipo Pydantic v2 opcional `CNS` (`Annotated[str, AfterValidator(...)]`) para schemas de API, com fallback gracioso se pydantic não estiver instalado.

**Verificação**: 13 testes embutidos (asserts pytest-style em `__main__`) passam via `python -m backend.app.services.validacao_cns` e via `pytest` (13 passed), além de fuzzer com 2000 casos aleatórios consistente com a especificação.