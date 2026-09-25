O usuário quer que eu crie um arquivo de testes unitários para algoritmos de triagem de risco (C11) no projeto MedIA. O caminho é backend/tests/test_triagem_clinica.py. O teste deve cobrir: 1) classificação correta de emergência hipertensiva; 2) rebaixamento adequado de casos estáveis; 3) cálculo correto do escore MEWS pediátrico e adulto.

Preciso entender o contexto: O Projeto MedIA, presumivelmente um sistema de saúde com backend em Python, FastAPI, Pydantic v2, SQLAlchemy 2.0. Padrões SUS/APS, CIAP-2, CID-10, SOAP, CNS/CPF.

A tarefa é criar testes unitários para algoritmos de triagem de risco. O teste deve verificar a lógica de triagem clínica. Provavelmente existe um módulo de triagem clínica no backend que implementa esses algoritmos. Mas o usuário pede apenas para criar o arquivo de teste, não o código de produção. No entanto, devemos criar testes que possam ser executados. Isso implica que precisamos assumir uma interface para o algoritmo de triagem. Como não nos deram o código, precisamos projetar os testes de forma que verifiquem a funcionalidade esperada, possivelmente usando mocks ou assumindo que existem funções específicas.

A tarefa: "crie backend/tests/test_triagem_clinica.py testando: 1) classificação correta de emergência hipertensiva; 2) rebaixamento adequado de casos estáveis; 3) cálculo correto do escore MEWS pediátrico e adulto."

Vamos interpretar: existem funções que realizam triagem, e o teste deve validar seu comportamento. Precisamos definir essas funções nos testes. Normalmente, em um projeto real, os testes importariam do módulo de produção. Mas como não temos o código, podemos criar testes que falham até que a implementação seja fornecida, mas o ideal é escrever testes que passem com uma implementação esperada.

Dado que o usuário pede "Testes Unitários de Algoritmos de Triagem de Risco (C11)", provavelmente é parte de um conjunto de requisitos do sistema. Vou supor que existem funções como:

- triagem_emergencia_hipertensiva(pressao_sistolica, pressao_diastolica, sintomas, etc.) -> classificação
- triagem_rebaixamento(caso) -> rebaixamento
- calcular_mews_pediatrico(parametros) -> escore
- calcular_mews_adulto(parametros) -> escore

Ou talvez uma classe TriagemClinica. Sem saber, devemos definir a interface no teste. Mas o teste deve ser executável; se as funções não existirem, os testes falharão. Poderíamos criar um arquivo de teste com funções que importam de um módulo de produção que não existe, resultando em erro. Isso não é bom.

A alternativa: criar o arquivo de teste com funções que são projetadas para testar a lógica de triagem, mas que usam mocks ou implementações internas? Não, teste unitário deve testar o código real.

Outra interpretação: o usuário quer que eu crie os testes como parte do desenvolvimento, e talvez também os algoritmos? A tarefa diz "crie backend/tests/test_triagem_clinica.py testando...". Não pede para criar o código de produção. Mas para os testes funcionarem, precisamos de código de produção. Podemos assumir que ele já existe (ou será criado por outro agente). Portanto, devemos escrever os testes de acordo com uma interface esperada.

Vou procurar pistas no prompt: "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)." Isso sugere que o sistema usa esses padrões. Os testes podem verificar se a triagem retorna códigos CIAP-2/CID-10, ou se os dados do paciente incluem CNS/CPF. Mas a tarefa específica é testar algoritmos de triagem de risco, não esses padrões em si.

Para MEWS: Modified Early Warning Score. Existem versões pediátricas e adultas. MEWS pediátrico (PEWS) e MEWS adulto. O escore é baseado em parâmetros fisiológicos: frequência cardíaca, pressão arterial sistólica, frequência respiratória, temperatura, nível de consciência. Para pediátrico, pode variar com a idade.

Vou assumir que o módulo de triagem clínica está em backend/app/services/triagem_clinica.py ou algo assim. Mas o caminho do teste é backend/tests/test_triagem_clinica.py. Vou criar testes que importam funções desses módulos.

Como o usuário não especificou os nomes exatos, posso escolher nomes plausíveis e documentar no teste. No entanto, para garantir que o teste seja executável, posso incluir um esboço dos módulos? Não, isso seria criar código de produção extra.

A melhor abordagem: escrever testes que assumem a existência de funções com nomes e assinaturas razoáveis, e usar pytest. Se o leitor quiser executar, ele precisará criar essas funções. Mas o usuário pede apenas o arquivo de teste. Posso fornecer o arquivo de teste e, opcionalmente, sugerir a interface.

Talvez a tarefa seja parte de um contexto maior onde já existe o código de triagem. Como não tenho acesso, vou criar testes genéricos que verificam comportamentos esperados.

Vou detalhar:

1) Classificação correta de emergência hipertensiva:
- Emergência hipertensiva é quando PA muito alta (>=180/120) com lesão de órgão-alvo (sintomas como dor torácica, dispneia, déficit neurológico, etc.). Urgência hipertensiva é PA alta sem lesão. Precisamos testar que a função classifica corretamente.

Vou supor uma função `classificar_emergencia_hipertensiva(pressao_sistolica, pressao_diastolica, sintomas)` que retorna um enum ou string: "EMERGENCIA", "URGENCIA", "SEM_URGENCIA".

2) Rebaixamento adequado de casos estáveis:
- "Rebaixamento" pode se referir à triagem de Manchester? Ou rebaixamento de prioridade? Em triagem de risco, às vezes pacientes podem ter o nível de urgência rebaixado se os sintomas não são tão graves. Ou pode ser sobre rebaixamento de classificação após reavaliação. Vou interpretar como um algoritmo que decide se um caso estável pode ser rebaixado de prioridade (ex: de urgente para não urgente). Talvez seja uma função `rebaixar_caso(paciente, sintomas)` que retorna se é seguro rebaixar.

3) Cálculo correto do escore MEWS pediátrico e adulto:
- Funções `calcular_mews_adulto(frequencia_cardiaca, pressao_sistolica, frequencia_respiratoria, temperatura, nivel_consciencia)` e `calcular_mews_pediatrico(..., idade)` ou faixa etária.

Vou pesquisar mentalmente os valores do MEWS adulto:

Adult MEWS (Modified Early Warning Score) comumente:
- Frequência cardíaca (bpm): <=40 = 2, 41-50 = 1, 51-100 = 0, 101-110 = 1, 111-129 = 2, >=130 = 3
- Pressão arterial sistólica (mmHg): <=70 = 3, 71-80 = 2, 81-100 = 1, 101-199 = 0, >=200 = 2 (algumas variações)
- Frequência respiratória (rpm): <=9 = 2, 10-14 = 0, 15-20 = 0 (ou 1 se >=21?), 21-29 = 2, >=30 = 3
- Temperatura (°C): <=35 = 2, 35.1-36 = 0, 36.1-38 = 0, 38.1-38.5 = 1, >=38.6 = 2
- Nível de consciência (AVPU): Alerta=0, Voz=1, Dor=2, Inconsciente=3

Mas há variações. Vou usar uma tabela comum.

Pediatric MEWS (PEWS) é diferente, usa parâmetros como frequência cardíaca, frequência respiratória, pressão arterial sistólica, temperatura, consciência, com ajuste por idade. Existem várias escalas, como PEWS (Bedside PEWS) que pontua comportamento, cardiovascular, respiratório. Mas para simplificar, posso assumir uma função que usa tabelas por faixa etária.

Preciso de uma especificação. Como o usuário menciona "escore MEWS pediátrico e adulto", provavelmente quer que os testes verifiquem o cálculo numérico.

Vou criar testes parametrizados com valores esperados.

Mas, sem o código real, os testes não passarão. Talvez o usuário espere que eu crie tanto o teste quanto a implementação? A tarefa diz "crie backend/tests/test_triagem_clinica.py testando...". Isso indica que o arquivo de teste é o entregável. Pode ser que o código de produção já exista e eu só preciso escrever os testes.

Considerando isso, vou assumir que existe um módulo chamado `backend.app.services.triagem_clinica` com funções:

- `classificar_emergencia_hipertensiva(pressao_sistolica: int, pressao_diastolica: int, sintomas: list[str]) -> str`
- `avaliar_rebaixamento(sinais_vitais: dict, comorbidades: list[str], sintomas: list[str]) -> bool` ou similar
- `calcular_mews_adulto(frequencia_cardiaca: int, pressao_sistolica: int, frequencia_respiratoria: int, temperatura: float, nivel_consciencia: str) -> int`
- `calcular_mews_pediatrico(idade_meses: int, frequencia_cardiaca: int, frequencia_respiratoria: int, pressao_sistolica: int, temperatura: float, nivel_consciencia: str) -> int`

Vou definir assinaturas e escrever testes que verificam a lógica. Se o módulo não existir, os testes falharão com erro de importação. Para evitar isso, poderia colocar um comentário de que assume a interface. Mas o usuário pediu código completo e executável. "Forneça o código completo e executável." Portanto, devo fornecer um arquivo que seja executável, ou seja, que possa rodar. Para isso, ou forneço a implementação também, ou uso mocks.

Uma solução: escrever os testes de forma que importem do módulo de produção e, se não existir, gerem um erro claro. Mas "executável" significa que deve rodar sem erros? Não, teste unitário deve passar. Se não houver implementação, não passa.

Acho que a melhor abordagem é criar o arquivo de teste e também sugerir a implementação mínima para que os testes passem. Mas o prompt diz "crie backend/tests/test_triagem_clinica.py". Não pede para criar outros arquivos. No entanto, se eu criar apenas o teste, ele não será executável sem a implementação.

Talvez o ambiente já tenha a implementação. Vou confiar nisso e escrever o teste com importações apropriadas. Para garantir, posso usar `pytest.importorskip` para pular se o módulo não estiver disponível, mas isso não testa.

Outra possibilidade: usar monkeypatch para substituir as funções por versões simuladas? Não, isso seria testar o teste, não o algoritmo.

Vou decidir: escreverei o arquivo de teste com importações de `backend.app.services.triagem_clinica` (ou um caminho plausível). Se o usuário tiver o código, funcionará. Se não, ele saberá que precisa criar.

Além disso, devo incluir a estrutura do teste com classes ou funções. Usarei pytest. Vou incluir testes parametrizados para MEWS.

Preciso também considerar os padrões do SUS/APS. Talvez as funções de triagem retornem não apenas um valor, mas um objeto com classificação, código CIAP-2, etc. Mas não tenho detalhes.

Vou fazer o seguinte:

- Criar o arquivo `backend/tests/test_triagem_clinica.py`.
- No topo, imports: `import pytest`, `from datetime import datetime`, `from typing import ...`.
- Importar as funções do módulo de produção: `from app.services.triagem_clinica import ...` (ajustar caminho). O diretório `backend` é a raiz? Normalmente em projetos, há `backend/app/...`. O caminho do teste é `backend/tests/`. Para importar, precisamos que `backend` esteja no PYTHONPATH. Em projetos com pytest, o arquivo `pytest.ini` ou `pyproject.toml` configura. Vou usar `from app.services.triagem_clinica import ...` e assumir que a raiz é `backend`. Comumente, testes estão em `backend/tests` e app em `backend/app`.

Vou incluir comentários explicando a interface esperada.

Agora, detalhar cada teste:

1) Classificação correta de emergência hipertensiva:
- Caso com PA 190/120 e sintomas de dor torácica -> deve retornar "emergencia" (ou "EMERGÊNCIA").
- Caso com PA 180/110 sem sintomas -> deve retornar "urgencia" (ou "URGÊNCIA").
- Caso com PA 160/100 sem sintomas -> "normal" ou "sem_urgencia".

Vou usar enum? Não, string simples.

2) Rebaixamento adequado de casos estáveis:
- Suponha que temos um paciente com sinais vitais estáveis, sem comorbidades, sintomas leves. A função deve retornar True (pode rebaixar).
- Paciente instável, retorna False.
- Casos limítrofes.

3) MEWS adulto e pediátrico:
- Testar valores que resultam em escore conhecido.

Vou criar uma implementação de referência para os testes? Não, mas posso criar os testes com valores esperados baseados em tabelas comuns. Se a implementação real usar outras tabelas, os testes falharão, mas isso é esperado se o código não segue o padrão.

Para MEWS adulto, vou usar uma tabela específica e documentar. Para MEWS pediátrico, é mais complexo. Vou simplificar: assumir que a função pediátrica usa faixas etárias e tabelas específicas. Testarei alguns casos.

Vou também incluir testes de borda e erros.

Agora, escrever o código.

Mas antes, preciso verificar se o diretório `backend/tests` existe? Não sei. Vou assumir que sim.

Vou fornecer o arquivo completo com comentários.

Além disso, o usuário pediu "tipagem estrita com Pydantic v2 e SQLAlchemy 2.0" mas isso se refere à arquitetura do projeto, não necessariamente aos testes. No entanto, podemos usar Pydantic nos testes? Não é necessário. Vou apenas usar Python 3.12.

Vou criar o arquivo:

```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""
Testes unitários para os algoritmos de triagem de risco do Projeto MedIA.

Cobre:
1. Classificação correta de emergência hipertensiva.
2. Rebaixamento adequado de casos estáveis.
3. Cálculo do escore MEWS pediátrico e adulto.

Para executar:
    pytest backend/tests/test_triagem_clinica.py -v
"""
```

Agora, os imports. Preciso importar as funções do módulo de produção. Vou supor que o módulo está em `backend/app/services/triagem_clinica.py`. Então:

```python
from app.services.triagem_clinica import (
    classificar_emergencia_hipertensiva,
    avaliar_rebaixamento,
    calcular_mews_adulto,
    calcular_mews_pediatrico,
)
```

Vou definir constantes para as classificações.

Teste 1:

```python
def test_emergencia_hipertensiva_com_lesao_orgao_alvo():
    resultado = classificar_emergencia_hipertensiva(
        pressao_sistolica=190,
        pressao_diastolica=120,
        sintomas=["dor_toracica", "dispneia"]
    )
    assert resultado == "EMERGENCIA"
```

Outros casos.

Teste 2:

```python
def test_rebaixamento_caso_estavel():
    sinais_vitais = {"frequencia_cardiaca": 70, "pressao_sistolica": 120, "temperatura": 36.5}
    comorbidades = []
    sintomas = ["cefaleia"]
    assert avaliar_rebaixamento(sinais_vitais, comorbidades, sintomas) is True
```

Teste 3: MEWS.

Vou escolher uma tabela de referência e calcular os escores esperados.

Adult MEWS (fonte: http://www.ihi.org/resources/Pages/Tools/ModifiedEarlyWarningScore.aspx) - vou usar uma versão