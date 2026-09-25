O usuário pede para criar testes unitários para algoritmos de triagem de risco no projeto MedIA. Especificamente, backend/tests/test_triagem_clinica.py testando:
1) classificação correta de emergência hipertensiva;
2) rebaixamento adequado de casos estáveis;
3) cálculo correto do escore MEWS pediátrico e adulto.

Preciso entender o contexto. O projeto MedIA parece ser um sistema de saúde com padrões SUS/APS, CIAP-2, CID-10, SOAP, CNS/CPF. A arquitetura usa Python 3.12, Pydantic v2, SQLAlchemy 2.0. Preciso criar testes unitários para algoritmos de triagem de risco. Não há código existente mencionado, então preciso inferir ou criar uma estrutura de teste que possa ser executada. O usuário pede "Execute com precisão conforme as diretrizes." Provavelmente espera que eu forneça o código do arquivo de teste e talvez também os módulos necessários para que os testes passem. Mas a tarefa é especificamente "crie backend/tests/test_triagem_clinica.py testando..." Então devo criar o arquivo de teste. No entanto, para que os testes sejam executáveis, precisamos de implementações dos algoritmos. Talvez o projeto já tenha esses algoritmos, mas não foram fornecidos. Preciso criar testes que possam ser executados contra uma implementação esperada. Posso criar testes que definem o comportamento esperado, e talvez também fornecer implementações mínimas para que os testes passem? O usuário pede apenas os testes. Mas "Execute com precisão conforme as diretrizes" pode significar que devo fornecer o código completo e executável, incluindo talvez stubs ou implementações de referência? Vou analisar.

A tarefa: "TAREFA: Testes Unitários de Algoritmos de Triagem de Risco (C23)" - C23 pode ser um código de requisito. "INSTRUÇÕES: Para o Projeto MedIA, crie backend/tests/test_triagem_clinica.py testando: 1) classificação correta de emergência hipertensiva; 2) rebaixamento adequado de casos estáveis; 3) cálculo correto do escore MEWS pediátrico e adulto."

Então o entregável é o arquivo de teste. Mas para que os testes sejam úteis, eles devem referenciar funções/classes existentes no backend. Como não temos o código, precisamos definir uma interface esperada. Podemos criar testes que importam de módulos como `backend.app.services.triagem` ou similar. Precisamos garantir que os testes sejam executáveis? O usuário diz "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0." Isso sugere que o código de teste deve seguir essas diretrizes. "Manter conformidade total e cobertura de testes automatizados com pytest." Então o arquivo de teste deve ser escrito com pytest.

Vou supor que existem módulos no backend que implementam:
- Uma função para classificar emergência hipertensiva, talvez `classificar_emergencia_hipertensiva(pressao_arterial, sintomas)` ou algo assim.
- Uma função para rebaixar casos estáveis, talvez `rebaixar_nivel_risco(nivel_atual, criterios_estabilidade)`.
- Uma função para calcular MEWS (Modified Early Warning Score) para adultos e pediátricos, talvez `calcular_mews_adulto(frequencia_cardiaca, pressao_sistolica, frequencia_respiratoria, temperatura, nivel_consciencia)` e `calcular_mews_pediatrico(...)`.

Mas não sabemos os nomes exatos. Para criar testes que possam ser executados, podemos definir uma interface e então fornecer implementações mock? Não, testes unitários devem testar o código real. Sem o código real, não podemos executar. Talvez o projeto já tenha esses algoritmos e o usuário quer apenas os testes. Como não temos acesso, podemos criar testes que importam de módulos que esperamos existir. Mas se não existirem, os testes falharão. O usuário pode esperar que eu também crie os algoritmos? A tarefa diz "crie backend/tests/test_triagem_clinica.py testando..." Não diz para criar os algoritmos. Mas "Execute com precisão conforme as diretrizes" pode implicar que devemos fornecer uma solução completa e funcional. Em cenários de engenharia de software, quando pedem testes, geralmente o código já existe. Mas aqui não temos. Talvez o usuário queira que eu forneça tanto os testes quanto as implementações para que os testes passem, demonstrando como seria. No entanto, o pedido específico é apenas o arquivo de teste. Vou reler: "TAREFA: Testes Unitários de Algoritmos de Triagem de Risco (C23) ... Para o Projeto MedIA, crie backend/tests/test_triagem_clinica.py testando: ..." A tarefa é criar o arquivo de teste. Ponto. Mas "Execute com precisão conforme as diretrizes" pode ser uma instrução para agir como um agente que executa a tarefa, ou seja, gerar o código do teste.

Vou criar um arquivo de teste abrangente que define os casos de teste para os três requisitos. Para que seja executável, preciso assumir uma interface. Posso documentar essa interface nos comentários. Também posso incluir testes que verificam o comportamento esperado, mesmo que as funções ainda não existam, mas isso resultaria em falhas. Talvez o usuário queira que os testes sejam a especificação. Em TDD, escrevemos testes primeiro. Então isso é aceitável.

No entanto, a diretriz "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0" sugere que os testes devem usar tipagem e talvez Pydantic para modelos de dados. Posso criar modelos Pydantic para os dados de entrada (pressão arterial, sinais vitais) e usar nos testes.

Vou estruturar o arquivo de teste com:
- Imports de pytest, pydantic, talvez datetime.
- Definição de modelos de dados Pydantic para PressaoArterial, SinaisVitais, etc., se necessário.
- Testes para classificação de emergência hipertensiva: casos com PA muito alta (>=180/120) com sintomas de lesão de órgão-alvo, casos sem sintomas, casos limítrofes.
- Testes para rebaixamento de casos estáveis: verificar que um paciente classificado como alto risco pode ser rebaixado se estável por um período, ou que não é rebaixado se não atender critérios.
- Testes para MEWS: calcular escores para diferentes combinações de sinais vitais, comparar com valores esperados.

Preciso definir as funções alvo. Vou criar nomes plausíveis:
- `classificar_emergencia_hipertensiva(pas: int, pad: int, sintomas_lesao_orgao_alvo: bool) -> bool` ou retorna um nível de risco.
- `rebaixar_risco(nivel_atual: str, tempo_estavel_horas: float, criterios_adicionais: dict) -> str` ou algo assim.
- `calcular_mews_adulto(fc: int, pas: int, fr: int, temperatura: float, nivel_consciencia: str) -> int`
- `calcular_mews_pediatrico(fc: int, pas: int, fr: int, temperatura: float, nivel_consciencia: str, idade_meses: int) -> int` (pois pediátrico depende da idade).

Mas não sabemos. Para tornar os testes mais robustos, posso usar `pytest.importorskip` para pular se os módulos não existirem? Isso permitiria que o arquivo de teste fosse coletado sem falhar, mas os testes seriam ignorados. No entanto, o usuário quer testes que verifiquem o comportamento. Se pularmos, não testamos nada. Melhor assumir que os módulos existem e documentar.

Outra abordagem: criar os testes usando monkeypatch para simular as funções? Não, isso não testaria a implementação real.

Vou criar o arquivo de teste com uma estrutura clara, usando `from backend.app.services.triagem import ...` e, no topo, um comentário explicando que os testes assumem essa interface. Se o usuário tiver uma interface diferente, ele pode ajustar.

Além disso, a diretriz menciona "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)". Isso pode ser relevante para os dados de entrada, como incluir CNS/CPF nos modelos. Mas para testes de algoritmos de triagem, talvez não seja necessário. Posso incluir um modelo de paciente com CNS/CPF para contexto.

Vou criar um arquivo de teste bem completo, com docstrings e casos parametrizados.

Primeiro, vou definir os modelos Pydantic:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from enum import Enum
```

Modelo para PressaoArterial:

```python
class PressaoArterial(BaseModel):
    sistolica: int = Field(..., ge=50, le=300, description="Pressão arterial sistólica em mmHg")
    diastolica: int = Field(..., ge=30, le=200, description="Pressão arterial diastólica em mmHg")
```

Modelo para SinaisVitais:

```python
class SinaisVitais(BaseModel):
    frequencia_cardiaca: int = Field(..., ge=20, le=250)
    pressao_sistolica: int = Field(..., ge=50, le=300)
    frequencia_respiratoria: int = Field(..., ge=5, le=100)
    temperatura: float = Field(..., ge=30, le=45)
    nivel_consciencia: Literal["alerta", "voz", "dor", "nao_responsivo"] = "alerta"
```

Para MEWS pediátrico, precisamos da idade. Podemos ter um modelo Pediatria com idade em meses.

Agora, as funções alvo. Vou supor que estão em `backend.app.services.triagem`. Vou criar os testes importando:

```python
from backend.app.services.triagem import (
    classificar_emergencia_hipertensiva,
    rebaixar_nivel_risco,
    calcular_mews_adulto,
    calcular_mews_pediatrico,
)
```

Mas se não existirem, os testes falham na importação. Para evitar isso, posso usar `pytest.importorskip`:

```python
triagem = pytest.importorskip("backend.app.services.triagem")
```

Então uso `triagem.classificar_emergencia_hipertensiva`. Isso faz com que o módulo seja importado; se não existir, todos os testes são pulados. Isso é útil para um ambiente onde o código ainda não foi implementado. Mas o usuário pediu "testes unitários" - normalmente eles devem rodar contra o código existente. Se o código não existe, pular é razoável. No entanto, a tarefa pode ser criar os testes como especificação, e o código será implementado depois. Vou usar `pytest.importorskip` para permitir que o arquivo seja coletado sem erro, mas os testes serão executados quando o módulo existir. Isso é uma boa prática para testes de integração.

Mas a diretriz "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0" - o arquivo de teste deve ser Python 3.12, usar type hints. Vou fazer isso.

Vamos detalhar os testes:

### 1) Classificação correta de emergência hipertensiva

Emergência hipertensiva é definida como PA sistólica >= 180 mmHg e/ou diastólica >= 120 mmHg, com evidência de lesão aguda de órgão-alvo (cérebro, coração, rins, etc.). Sem lesão, é urgência hipertensiva (PA muito alta mas sem lesão aguda). Precisamos testar que a função retorna verdadeiro para emergência e falso para não emergência.

Casos:
- PA 190/130 com sintomas (cefaleia intensa, escotomas, dor torácica, dispneia, déficit neurológico) -> emergência.
- PA 180/120 com sintomas -> emergência (limiar).
- PA 179/119 sem sintomas -> não emergência.
- PA 170/110 com sintomas -> não emergência (PA não atinge critério).
- PA 200/130 sem sintomas -> não emergência? Na prática, PA muito alta sem sintomas é urgência hipertensiva, não emergência. Então a função deve retornar False se não houver sintomas.
- PA 160/100 com sintomas -> não emergência.

A função pode ser `classificar_emergencia_hipertensiva(pas: int, pad: int, sintomas_lesao_orgao_alvo: bool) -> bool`.

Vou parametrizar.

### 2) Rebaixamento adequado de casos estáveis

Isso se refere a um protocolo de triagem onde pacientes classificados em alto risco podem ser rebaixados se permanecerem estáveis por um período. Por exemplo, um paciente com risco "vermelho" pode ser rebaixado para "laranja" se após 30 minutos os sinais vitais normalizarem. Precisamos testar que a função `rebaixar_nivel_risco` retorna o nível correto.

Vou supor que os níveis são: "vermelho", "laranja", "amarelo", "verde", "azul" (protocolo de Manchester). Ou talvez "emergencia", "urgente", "pouco_urgente", "nao_urgente". Vou usar o protocolo de Manchester: vermelho (emergência), laranja (muito urgente), amarelo (urgente), verde (pouco urgente), azul (não urgente). A função pode receber o nível atual, o tempo de estabilidade em minutos, e os sinais vitais atuais. Se o paciente está estável (sinais vitais dentro da normalidade) por um tempo mínimo, rebaixa um nível. Caso contrário, mantém.

Casos:
- Nível "laranja", estável por 30 minutos, sinais vitais normais -> rebaixa para "amarelo".
- Nível "laranja", estável por 10 minutos (menos que o mínimo) -> mantém "laranja".
- Nível "laranja", sinais vitais anormais -> mantém "laranja".
- Nível "vermelho" não deve ser rebaixado? Talvez nunca rebaixar vermelho, ou apenas com critérios muito rígidos. Vou testar que vermelho não é rebaixado.
- Nível "amarelo", estável -> rebaixa para "verde".
- Nível "verde", estável -> rebaixa para "azul".
- Nível "azul" não rebaixa mais.

A função pode ser `rebaixar_nivel_risco(nivel_atual: str, tempo_estavel_minutos: int, sinais_vitais_estaveis: bool) -> str`.

### 3) Cálculo correto do escore MEWS pediátrico e adulto

MEWS (Modified Early Warning Score) é usado para detectar deterioração clínica. Para adultos, os parâmetros são:
- Frequência cardíaca (bpm): 0 se 51-100, 1 se 41-50 ou 101-110, 2 se 111-129, 3 se >=130 ou <=40, etc. Preciso da tabela exata. Vou usar uma tabela comum:

Adulto:
- FC: <=40 = 3, 41-50 = 1, 51-100 = 0, 101-110 = 1, 111-129 = 2, >=130 = 3.
- PAS: <=70 = 3, 71-80 = 2, 81-100 = 1, 101-199 = 0, >=200 = 2? Algumas tabelas usam >=200 = 2. Vou adotar uma tabela padrão.
- FR: <=8 = 3, 9-11 = 1, 12-20 = 0, 21-24 = 2, >=25 = 3.
- Temperatura: <=35 = 3, 35.1-36 = 1, 36.1-38 = 0, 38.1-38.5 = 1, >=38.6 = 2.
- Nível de consciência (AVPU): Alerta = 0, Voz = 1, Dor = 2, Não responsivo = 3.

Para pediátrico, os valores variam com a idade. Existem tabelas específicas (PEWS). Mas o usuário diz "MEWS pediátrico", que pode ser uma adaptação. Vou supor que a função pediátrica recebe a idade em meses e os sinais vitais, e usa tabelas diferentes para faixas etárias. Para simplificar, posso testar com uma tabela fixa para uma faixa etária, por exemplo, lactentes. Mas sem a implementação, não sei. Posso criar testes que verificam o cálculo para valores conhecidos, assumindo uma tabela específica.

Vou definir uma tabela MEWS adulto e pediátrico nos próprios testes como referência, e comparar com a saída da função. Isso garante que