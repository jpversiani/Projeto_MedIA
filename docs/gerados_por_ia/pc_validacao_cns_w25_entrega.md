O arquivo já existe com implementação completa. Vou executar os testes embutidos para validar:
O arquivo `backend/app/services/validacao_cns.py` já existe e atende integralmente à tarefa — verifiquei os CNS de exemplo contra o algoritmo oficial (soma ponderada pesos 15→1, múltiplo de 11): todos corretos.

Conteúdo confirmado:
- `ValidadorCNS` com validação do DV (15→1, % 11 == 0), dígito inicial 1/2 (definitivo) e 7/8/9 (provisório) — `e_valido`, `e_provisorio`, `e_definitivo`, `validar()`, `formatar()` (000 0000 0000 000), `calcular_digito_verificador()`.
- Tipo `CNS` (Pydantic v2, `Annotated[str, AfterValidator]`) para schemas de API.
- Mensagens/docstrings em pt-BR, tipagem estrita, 12 testes pytest-style em `__main__` — todos passando:

```
12 teste(s) executado(s) com sucesso.
```