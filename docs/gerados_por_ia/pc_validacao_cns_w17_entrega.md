O projeto principal já possui esse serviço; o sandbox de trabalho está vazio, então vou criar a implementação em `backend/app/services/validacao_cns.py` no diretório de trabalho. Verifiquei o algoritmo oficial (pesos 15→1, múltiplo de 11) e validei manualmente os números CNS que usarei nos testes.
Agora vou executar os testes embutidos para verificar:
`backend/app/services/validacao_cns.py` criado e verificado:

- **`ValidadorCNS`** — valida DV conforme o algoritmo oficial do MS: 15 dígitos, início em 1/2/7/8/9, soma ponderada com pesos **15 → 1** múltipla de **11**; entrada normalizada de pontuação (`.`/`-`/espaços).
- **CNS provisório** — propriedades `e_provisorio` (7/8/9) e `e_definitivo` (1/2), com `validar()` encadeável e erros específicos (`CNSInvalidoError`) em pt-BR.
- **Formatação canônica** — `formatar()`/`__str__` no padrão `000 0000 0000 000`; bônus: `calcular_digito_verificador()` para gerar o 15º dígito.
- **Pydantic v2** — tipo `CNS = Annotated[str, AfterValidator(...)]` para uso em schemas, com fallback se pydantic ausente.
- **Testes embutidos** — 12 testes pytest-style executados via `__main__`: todos `[OK]` (pydantic 2.13.5 ativo), além de doctests verificados (2 passed).