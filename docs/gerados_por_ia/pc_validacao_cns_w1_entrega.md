O sandbox é meu diretório de trabalho; vou verificar as convenções de estilo dos services reais do projeto antes de criar o arquivo alvo.
Python 3.12 disponível, mas sem pydantic/pytest no sandbox — então o módulo será stdlib puro com tipagem estrita (consistente com os services reais do projeto, que não importam pydantic), e os testes embutidos usarão asserts puros em `__main__`, executáveis sem dependências.

Antes de escrever o arquivo, vou computar vetores de teste válidos com o algoritmo oficial (soma ponderada 15→1, múltiplo de 11) para embutir apenas valores verificados:
Meu scratch tinha erro de comprimento (prefixos com 13 dígitos). Recalculando corretamente com prefixos de 14 dígitos + DV de peso 1:
Vetores verificados (soma % 11 == 0): definitivos `116809660000001`, `211680966000008`, `198450013720000`; provisórios 7/8/9: `700000000000005`, `811680966000006`, `911680966000002`, `998450013720001`. Agora vou criar o arquivo alvo:
Agora vou corrigir dois detalhes: a anotação de tipo do runner e vetores de teste para prefixos 3/4/6 com DV genuinamente correto (rejeição inequívoca pelo prefixo). Calculando:
Editação correta. Agora corrigindo a anotação de tipo do runner `__main__`:
Removi sem querer as linhas do `try` na edição. Verificando e reparando:
Adicionando o import de `Callable` e executando os testes embutidos:
13/13 aprovados. Verificações finais: execução como módulo do pacote, compilação, lint (ruff, se disponível) e conferência do algoritmo contra a implementação de referência independente:
Tudo verificado contra a referência independente. Só falta ajustar a linha 97 (105 caracteres) para manter o padrão de estilo:
Concluído. `backend/app/services/validacao_cns.py` (336 linhas) com **13/13 testes embutidos aprovados** e algoritmo conferido contra implementação de referência independente (14 vetores válidos + 10 inválidos).

**Classe `ValidadorCNS`** (API completa):
- `validar(cns) -> bool` — validação oficial completa: 15 dígitos, prefixo (1/2 definitivo, 7/8/9 provisório) e dígito verificador
- `validar_digito_verificador(cns) -> bool` — soma ponderada pelos pesos **15 até 1** (DV recebe peso 1), válida se **múltiplo de 11** (ex.: CNS canônico do manual do MS `116 8096 6000 0001` → soma 396)
- `validar_ou_lancar(cns) -> str` — rígida, com `CNSInvalidoError` portando `cns` e `motivo` detalhado (prefixo, DV, caracteres não numéricos, tamanho)
- `formatar(cns) -> str` — máscara canônica `116 8096 6000 0001`
- `obter_tipo(cns) -> Literal["DEFINITIVO", "PROVISORIO"]` e `eh_provisorio(cns)` — suporte a provisórios 7/8/9
- Extras: `limpar`, `calcular_soma_ponderada`, `calcular_digito_verificador` (útil para seeds de pacientes)

**Nota:** a máscara do enunciado (`000 0000 0000 000`) tem 14 dígitos; o CNS oficial tem 15, então a máscara canônica implementada é `000 0000 0000 0000` (grupos 3-4-4-4).

**Observações técnicas:** tipagem estrita (`Final`, `ClassVar`, `Literal`, `zip(strict=True)`), mensagens/docstrings em PT-BR, testes executáveis via `python backend/app/services/validacao_cns.py` ou `python -m backend.app.services.validacao_cns` — stdlib pura, sem dependências externas.