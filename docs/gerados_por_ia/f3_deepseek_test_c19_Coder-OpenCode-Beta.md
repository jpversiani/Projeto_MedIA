O usuário pede para criar um arquivo de teste unitário para algoritmos de triagem de risco (C19) para o projeto MedIA. O arquivo deve ser backend/tests/test_triagem_clinica.py. Deve testar três coisas: classificação correta de emergência hipertensiva, rebaixamento adequado de casos estáveis, e cálculo correto do escore MEWS pediátrico e adulto.

Preciso entender o contexto do projeto MedIA. Provavelmente é um sistema de telemedicina/APS. Preciso assumir a existência de classes/funções que implementam esses algoritmos. Como não foi fornecido código existente, devo criar o arquivo de teste assumindo que existem módulos com funções específicas. Para o teste ser executável, preciso criar também implementações mínimas ou assumir que o código existe e apenas testar via mocks? A instrução diz "crie backend/tests/test_triagem_clinica.py testando: ...". Provavelmente devemos escrever testes unitários para funções que já existem ou que serão criadas. Mas como não temos o código, podemos definir interfaces esperadas e testar com dados de exemplo.

Preciso criar um arquivo de teste com pytest. Vou supor que existem funções como:

- `classificar_emergencia_hipertensiva(pressao_arterial: PressaoArterial, sintomas: List[str]) -> bool` (ou algo assim)
- `rebaixar_caso_estavel(estabilidade: Estabilidade) -> bool` ou função que decide se pode rebaixar.
- `calcular_mews_pediatrico(paciente: Paciente) -> int`
- `calcular_mews_adulto(paciente: Paciente) -> int`

Ou podem ser classes. Como não sei, vou criar testes que importam de módulos esperados e uso fixtures de dados.

Vou estruturar o teste com três classes ou funções de teste. Usarei pytest e algumas bibliotecas como pydantic, mas não necessariamente.

Além disso, devo garantir que o código segue as diretrizes: Python 3.12, tipagem estrita com Pydantic v2, SQLAlchemy 2.0, padrões SUS/APS, etc. Mas para testes unitários, podemos apenas testar a lógica pura.

Vou criar um arquivo com testes que verificam os cenários solicitados.

Primeiro, devo definir o que é emergência hipertensiva. Segundo o SUS, emergência hipertensiva é quando há pressão arterial muito alta (geralmente > 180/120) acompanhada de lesão de órgão-alvo (sintomas como cefaleia intensa, dispneia, dor torácica, etc.). Então a função deve verificar se a PA está alta e há sintomas. Caso estável (PA alta mas sem sintomas) seria urgência hipertensiva, não emergência.

Para o rebaixamento de casos estáveis: provavelmente se refere a triagem, por exemplo, se um paciente está estável, pode ser rebaixado de uma classificação de risco (ex: de vermelho para amarelo) ou de emergência para urgência. Preciso interpretar: "rebaixamento adequado de casos estáveis" - pode ser testar que uma função que decide se um caso pode ser rebaixado de nível de prioridade, dado que está estável.

Para MEWS (Modified Early Warning Score) existem versões pediátricas e adultas. O escore avalia parâmetros como frequência cardíaca, respiratória, pressão arterial sistólica, temperatura, nível de consciência. Para pediatria há adaptações.

Vou criar testes unitários que usam fixtures com dados de exemplo e verificam se as funções retornam o esperado.

Como não temos implementações, posso criar stubs simples no próprio arquivo de teste ou assumir que o código será implementado posteriormente. Mas a tarefa é criar o arquivo de teste. Acho que devemos criar um arquivo de teste que importa de um módulo `backend.app.services.triagem` ou algo assim. Para garantir que o teste seja executável, podemos definir as funções dentro do próprio arquivo de teste? Não, testes devem testar código de produção. Mas como o código não existe, talvez devamos criar testes que usem mocks e verifiquem a lógica se as funções fossem implementadas. Ou podemos criar uma implementação mínima em um módulo separado? O usuário pediu apenas o arquivo de teste. Talvez devamos criar o teste assumindo que o código exista e, se não existir, o teste falhará. Mas isso não é ideal.

Podemos criar um esqueleto do código de produção também? O pedido é "crie backend/tests/test_triagem_clinica.py testando: ..." - então apenas o arquivo de teste. Provavelmente o projeto já tem código, e o usuário quer testes para ele. Mas não temos contexto. Vou supor que existem funções com nomes específicos. Vou criar o teste de forma que seja facilmente adaptável.

Outra abordagem: criar o teste com funções que importam de um módulo `backend.app.core.triagem` e usar `pytest.importorskip` para pular se não existir. Mas isso não seria um teste completo.

A melhor prática seria criar o teste com base em uma interface definida. Vou definir as funções em um módulo `backend/app/core/triagem.py` (mas não vou criar esse módulo, apenas referenciar). Para garantir que o teste funcione, posso criar o teste usando mocks com `unittest.mock` para simular o comportamento? Não, testes unitários devem testar o código real.

Considerando o contexto, talvez o projeto já tenha essas funções implementadas. Como não temos acesso, vou escrever testes que presumem a existência de funções com assinaturas razoáveis e documentar o que esperam. Vou usar `pytest.fixture` para fornecer dados de exemplo.

Vou criar o arquivo com três conjuntos de testes:

1. Teste de classificação de emergência hipertensiva: usar casos como PA 200/130 com sintomas neurológicos -> deve ser emergência; PA 160/100 sem sintomas -> não é emergência.

2. Teste de rebaixamento de casos estáveis: por exemplo, um paciente com sinais vitais estáveis e sem queixas agudas deve ser rebaixado de prioridade alta para média.

3. Teste de MEWS: fornecer dados vitais e verificar se o escore calculado é o esperado, tanto para adulto quanto pediátrico.

Preciso definir as assinaturas das funções. Vou supor:

- `def classificar_emergencia_hipertensiva(pressao_arterial: tuple[int, int], sintomas: list[str]) -> bool` - retorna True se emergência.
- `def rebaixar_caso_estavel(classificacao_risco: str, estabilidade: bool) -> str` - dado uma classificação atual e estabilidade, retorna a nova classificação (ex: "vermelho" -> "amarelo").
- `def calcular_mews_adulto(fc: int, fr: int, pas: int, temp: float, nivel_consciencia: int) -> int` - retorna escore.
- `def calcular_mews_pediatrico(fc: int, fr: int, pas: int, temp: float, nivel_consciencia: int) -> int` - retorna escore.

Mas MEWS pediátrico pode variar com idade, então talvez precise de idade. Vou incluir idade.

Melhor: `def calcular_mews(paciente: Paciente) -> int` onde Paciente tem idade, sinais vitais. Mas como não tenho modelo, vou simplificar.

Vou criar funções que aceitam parâmetros individuais.

Como não tenho implementação, vou usar `pytest.skip` se as funções não existirem? Isso não é bom.

Talvez devamos criar um arquivo de teste que testa uma implementação fictícia dentro do próprio teste? Não, o ideal é testar o código real.

Vou criar o arquivo de teste com imports e escrever testes que, se o código não existir, falharão. Isso incentiva o desenvolvimento. Mas o usuário pediu para criar o teste, então talvez o código já exista.

Vou supor que existe um módulo `backend.app.services.triagem` com classes como `TriagemService`. Mas para simplificar, vou criar funções puras.

Vou escrever o teste com base em funções que eu acho que são razoáveis. Vou também adicionar um teste de que a função de MEWS adulto retorna 0 para parâmetros normais.

Além disso, vou incluir testes de borda.

Vou criar o arquivo.

Estrutura:

```python
# Arquivo: backend/tests/test_triagem_clinica.py
import pytest
from backend.app.services.triagem import (
    classificar_emergencia_hipertensiva,
    rebaixar_caso_estavel,
    calcular_mews_adulto,
    calcular_mews_pediatrico,
)
```

Mas isso pode falhar se o módulo não existir. Talvez devamos criar um conftest ou algo. Mas o usuário só pediu o arquivo de teste.

Talvez devêssemos criar o arquivo de teste com as funções definidas localmente? Não, isso não seria um teste unitário do código de produção.

Penso que podemos criar o arquivo de teste com a intenção de que essas funções existam. O usuário pode depois implementá-las.

Vou escrever testes que usam `pytest.raises` para erros também.

Vou incluir docstrings explicando o que cada teste verifica.

Também vou usar tipagem estrita, Pydantic talvez para modelos de dados, mas não é necessário para testes.

Vou usar `from pydantic import BaseModel` para criar modelos de exemplo? Talvez.

Vou criar um modelo de PressaoArterial e Sintomas.

Mas para simplificar, posso usar tuplas.

Vou escrever o teste.

Como o pedido menciona C19 (COVID-19?) talvez o projeto seja sobre triagem de COVID, mas não interfere.

Vou escrever:

```python
# Arquivo: backend/tests/test_triagem_clinica.py
"""Testes unitários para algoritmos de triagem de risco clínico.

Este módulo cobre:
1. Classificação de emergência hipertensiva.
2. Rebaixamento adequado de casos estáveis.
3. Cálculo do escore MEWS pediátrico e adulto.
"""

import pytest
from pydantic import BaseModel, Field

# Assume-se que as funções estão em backend/app/services/triagem.py
from backend.app.services.triagem import (
    classificar_emergencia_hipertensiva,
    rebaixar_caso_estavel,
    calcular_mews_adulto,
    calcular_mews_pediatrico,
)


class PressaoArterial(BaseModel):
    sistolica: int
    diastolica: int


class SinaisVitais(BaseModel):
    frequencia_cardiaca: int
    frequencia_respiratoria: int
    pressao_sistolica: int
    temperatura: float
    nivel_consciencia: int  # Escala AVPU: 0 = Alerta, 1 = Voz, 2 = Dor, 3 = Sem resposta


class TestEmergenciaHipertensiva:
    def test_classifica_com_sintomas_graves(self):
        # PA 200/130 com cefaleia intensa e dispneia
        pa = PressaoArterial(sistolica=200, diastolica=130)
        sintomas = ["cefaleia intensa", "dispneia", "dor torácica"]
        assert classificar_emergencia_hipertensiva(pa, sintomas) is True

    def test_nao_classifica_sem_sintomas(self):
        # PA 180/110 sem sintomas (urgência, não emergência)
        pa = PressaoArterial(sistolica=180, diastolica=110)
        sintomas = []
        assert classificar_emergencia_hipertensiva(pa, sintomas) is False

    def test_nao_classifica_pa_limite(self):
        # PA 160/100 com sintomas leves -> não emergência
        pa = PressaoArterial(sistolica=160, diastolica=100)
        sintomas = ["tontura"]
        assert classificar_emergencia_hipertensiva(pa, sintomas) is False


class TestRebaixamentoCasoEstavel:
    def test_rebaixa_vermelho_para_amarelo(self):
        # Paciente classificado como vermelho (emergência) mas estável -> deve rebaixar
        assert rebaixar_caso_estavel("vermelho", estabilidade=True) == "amarelo"

    def test_nao_rebaixa_se_instavel(self):
        # Paciente instável não deve ser rebaixado
        assert rebaixar_caso_estavel("vermelho", estabilidade=False) == "vermelho"

    def test_nao_rebaixa_se_ja_amarelo_e_estavel(self):
        # Amarelo estável permanece amarelo (não rebaixa para verde automaticamente)
        assert rebaixar_caso_estavel("amarelo", estabilidade=True) == "amarelo"


class TestMewsAdulto:
    def test_escore_zero_para_sinais_normais(self):
        # FC 80, FR 16, PAS 120, T 36.5, alerta
        vitais = SinaisVitais(
            frequencia_cardiaca=80,
            frequencia_respiratoria=16,
            pressao_sistolica=120,
            temperatura=36.5,
            nivel_consciencia=0,
        )
        assert calcular_mews_adulto(vitais) == 0

    def test_escore_aumenta_com_taquicardia(self):
        # FC 130, outros normais
        vitais = SinaisVitais(
            frequencia_cardiaca=130,
            frequencia_respiratoria=16,
            pressao_sistolica=120,
            temperatura=36.5,
            nivel_consciencia=0,
        )
        # FC > 120 dá +3 no MEWS adulto (padrão)
        assert calcular_mews_adulto(vitais) == 3

    def test_escore_aumenta_com_rebaixamento_consciencia(self):
        # Nível de consciência V (1) dá +1
        vitais = SinaisVitais(
            frequencia_cardiaca=80,
            frequencia_respiratoria=16,
            pressao_sistolica=120,
            temperatura=36.5,
            nivel_consciencia=1,
        )
        assert calcular_mews_adulto(vitais) == 1


class TestMewsPediatrico:
    def test_escore_zero_para_sinais_normais(self):
        # Criança 5 anos: FC 100, FR 20, PAS 90, T 36.5, alerta
        vitais = SinaisVitais(
            frequencia_cardiaca=100,
            frequencia_respiratoria=20,
            pressao_sistolica=90,
            temperatura=36.5,
            nivel_consciencia=0,
        )
        assert calcular_mews_pediatrico(vitais, idade=5) == 0

    def test_escore_alto_com_bradicardia_extrema(self):
        # Criança 1 ano: FC 50, FR 30, PAS 80, T 37, alerta
        vitais = SinaisVitais(
            frequencia_cardiaca=50,
            frequencia_respiratoria=30,
            pressao_sistolica=80,
            temperatura=37.0,
            nivel_consciencia=0,
        )
        # Bradicardia grave deve dar escore alto
        assert calcular_mews_pediatrico(vitais, idade=1) >= 3

    def test_escore_com_temperatura_alta(self):
        # Criança 3 anos: FC 120, FR 25, PAS 95, T 39.5, alerta
        vitais = SinaisVitais(
            frequencia_cardiaca=120,
            frequencia_respiratoria=25,
            pressao_sistolica=95,
            temperatura=39.5,
            nivel_consciencia=0,
        )
        # Temperatura > 38.5 dá +2 no MEWS pediátrico (padrão)
        assert calcular_mews_pediatrico(vitais, idade=3) >= 2
```

Mas note que `calcular_mews_adulto` e `calcular_mews_pediatrico` recebem `SinaisVitais` e idade (para pediátrico). A assinatura que defini não era exatamente essa. Vou ajustar.

Melhor: `calcular_mews_adulto(sinais_vitais: SinaisVitais) -> int` e `calcular_mews_pediatrico(sinais_vitais: SinaisVitais, idade: int) -> int`.

No teste, estou passando `vitais` e idade para pediátrico. Ok.

Também `classificar_emergencia_hipertensiva` recebe `PressaoArterial` e lista de sintomas. Ok.

Agora, o problema é que as funções não existem. Preciso garantir que o arquivo de teste possa rodar sem esses imports? Não, deve rodar. Talvez devamos usar `pytest.importorskip` para pular se não existir, mas isso não é um teste real.

Talvez o usuário espere que criemos o teste e também o código de produção? Mas ele pediu apenas o arquivo de teste. Vou assum