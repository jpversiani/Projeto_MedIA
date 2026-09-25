Vamos analisar a tarefa. Precisamos criar um arquivo de testes para o backend, focado em testes de precisão algorítmica dos indicadores e agregações. O nome do arquivo é `backend/tests/test_analytics_kpis.py`. Devemos validar três coisas: 
1. Cálculo exato da taxa de absenteísmo com divisão protegida por zero.
2. Verificar consistência da matriz de heatmap.
3. Testar agregações de diagnóstico prevalente por CIAP-2.

O projeto é MedIA, que parece ser um sistema de saúde com padrões SUS/APS. Vamos criar os testes usando pytest, Pydantic v2, SQLAlchemy 2.0.

Precisamos entender quais funções ou classes estão envolvidas. Como não temos o código-fonte, vamos supor que existe uma lógica de cálculo em algum módulo do backend, por exemplo, `backend/app/services/analytics.py` ou similar. Vamos criar testes que testam essas funções hipotéticas.

Vou estruturar o arquivo de testes da seguinte forma:

- Importações necessárias (pytest, pydantic, sqlalchemy, etc.)
- Fixtures para criar dados de exemplo.
- Testes para taxa de absenteísmo.
- Testes para consistência da matriz de heatmap.
- Testes para agregações de diagnóstico por CIAP-2.

Como não temos código real, vou definir funções de exemplo dentro do próprio teste para simular o comportamento esperado. Ou, melhor, vou criar os testes de forma que eles testem funções reais que serão implementadas no código, mas como estamos escrevendo apenas os testes, vou documentar as suposições.

Alternativa: podemos criar um módulo de teste que testa funções específicas que serão definidas no futuro. Para que os testes sejam executados, precisamos de pelo menos as funções a serem testadas. Então, posso criar funções auxiliares no próprio arquivo de teste (mas não é ideal). Melhor: criar um arquivo de teste que importa funções de um módulo de serviço e testa. Como não sabemos se o módulo existe, posso supor que ele existe e escrever os testes de acordo com a interface esperada.

Vou definir a interface: 
- `calcular_taxa_absenteismo(total_consultas, faltas)` -> retorna float.
- `gerar_matriz_heatmap(dados)` -> retorna uma matriz (lista de listas) com valores normalizados.
- `agregar_diagnosticos_por_ciap2(consultas)` -> retorna um dicionário com contagem por código CIAP-2.

Vou criar os testes usando essas funções, e no final, incluir um bloco de teste que verifica que essas funções existem (apenas para garantir que os testes falham se não implementadas). Mas, talvez seja melhor apenas escrever os testes e deixar o usuário implementar as funções.

No contexto da tarefa, somos um agente coder que deve entregar o código de teste. Vou escrever testes que são precisos e cobrem os requisitos.

Vou considerar também a tipagem estrita com Pydantic v2 e SQLAlchemy 2.0. Isso pode aparecer em fixtures que usam modelos SQLAlchemy. Mas para testes de cálculo, podemos usar objetos simples.

Vou criar um arquivo de teste com os seguintes casos:

1. Teste de taxa de absenteísmo:
   - Dado total_consultas=100, faltas=10 -> taxa=0.1 (ou 10%).
   - Divisão por zero: total_consultas=0 -> deve retornar 0 ou None, mas precisamos proteger.

2. Teste da matriz de heatmap:
   - Consistência: a soma de todas as células deve ser igual a 1 (se normalizada), ou verificar que não há valores fora do intervalo [0,1]. Além disso, verificar que as dimensões estão corretas.

3. Teste de agregação por CIAP-2:
   - Dado uma lista de consultas com códigos CIAP-2, verificar que a contagem está correta.

Vou incluir também testes de edge cases.

Agora, escreverei o arquivo com docstrings explicando as suposições. Para garantir que os testes possam rodar sem o código real, posso criar um esqueleto de funções dentro do próprio teste (mas não é recomendado). Outra abordagem: usar `pytest.importorskip` para pular se o módulo não existir, mas então não teremos testes executando. Melhor é escrever testes que assumem que as funções existem em um módulo `backend.app.services.analytics` e usar `pytest.importorskip` para pular se não existir, mas isso faria os testes serem ignorados. Como a tarefa pede para criar testes, vou assumir que o módulo existe e escrever os testes de forma que eles sejam executados se o módulo estiver presente.

Talvez seja melhor criar testes que testam funções que serão implementadas no futuro, mas como estamos fornecendo apenas os testes, o usuário terá que implementar as funções para que os testes passem.

Vou escrever o código de teste com essas funções de exemplo definidas no próprio arquivo de teste? Não, porque os testes devem testar a implementação real. Mas como não temos, vou deixar comentários explicando o que esperamos.

Decisão: Vou criar o arquivo de teste importando de `backend.app.services.analytics` as funções, e usar `pytest.importorskip` para pular se não existir, mas isso faria os testes não rodarem. Talvez seja melhor criar um teste que verifica a existência dessas funções e depois os demais testes usam essas funções. Se não existirem, os testes falharão, o que é esperado. Vou fazer isso.

No início, vou usar `pytest.importorskip` para pular todo o módulo se não for possível importar as funções, mas isso não testa nada. Prefiro criar os testes de forma que eles chamem as funções diretamente e, se não existirem, o teste falha com erro de importação, o que é aceitável.

Vou também incluir exemplos de dados usando Pydantic para validação, se aplicável.

Vou escrever o código.

Estrutura:

```python
# Arquivo: backend/tests/test_analytics_kpis.py
"""
Testes de precisão algorítmica dos indicadores e agregações para o Projeto MedIA.
Cobre:
- Cálculo exato da taxa de absenteísmo com divisão protegida por zero.
- Consistência da matriz de heatmap.
- Agregações de diagnóstico prevalente por CIAP-2.
"""

import pytest
from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# Suposição: as funções a serem testadas estão em backend.app.services.analytics
from backend.app.services.analytics import (
    calcular_taxa_absenteismo,
    gerar_matriz_heatmap,
    agregar_diagnosticos_por_ciap2,
)

# ========== Fixtures ==========

class Consulta(BaseModel):
    """Modelo Pydantic para uma consulta, usado nos testes."""
    id: int
    ciap2: str  # Código CIAP-2
    compareceu: bool
    data: str

@pytest.fixture
def consultas_exemplo():
    """Exemplo de lista de consultas para testes."""
    return [
        Consulta(id=1, ciap2="A01", compareceu=True, data="2024-01-01"),
        Consulta(id=2, ciap2="A01", compareceu=False, data="2024-01-02"),
        Consulta(id=3, ciap2="B02", compareceu=True, data="2024-01-03"),
        Consulta(id=4, ciap2="B02", compareceu=True, data="2024-01-04"),
        Consulta(id=5, ciap2="C03", compareceu=False, data="2024-01-05"),
        Consulta(id=6, ciap2="A01", compareceu=True, data="2024-01-06"),
    ]

# ========== Testes para Taxa de Absenteísmo ==========

class TestTaxaAbsenteismo:
    """Testes para o cálculo da taxa de absenteísmo."""

    def test_taxa_normal(self):
        """Caso normal: 10 faltas em 100 consultas -> 10%."""
        total = 100
        faltas = 10
        resultado = calcular_taxa_absenteismo(total, faltas)
        assert resultado == pytest.approx(0.1)

    def test_taxa_com_zero_total(self):
        """Divisão por zero: total=0 deve retornar 0 (ou None) sem erro."""
        with pytest.raises(ZeroDivisionError):
            # Se a função não proteger, deve lançar erro. Se proteger, deve retornar 0.
            # Vamos testar que retorna 0.
            resultado = calcular_taxa_absenteismo(0, 0)
            assert resultado == 0

    def test_taxa_todas_faltas(self):
        """Todas as consultas foram faltas -> taxa = 1.0."""
        resultado = calcular_taxa_absenteismo(10, 10)
        assert resultado == 1.0

    def test_taxa_nenhuma_falta(self):
        """Nenhuma falta -> taxa = 0.0."""
        resultado = calcular_taxa_absenteismo(50, 0)
        assert resultado == 0.0

    def test_taxa_maior_que_um(self):
        """Faltas maiores que total deve ser tratado (ex: 15 faltas em 10 consultas) -> erro ou valor?."""
        # Esperamos que a função valide e levante erro ou normalize.
        with pytest.raises(ValueError):
            calcular_taxa_absenteismo(10, 15)

# ========== Testes para Matriz de Heatmap ==========

class TestMatrizHeatmap:
    """Testes para a consistência da matriz de heatmap."""

    @pytest.fixture
    def dados_heatmap(self):
        """Dados de exemplo para gerar heatmap."""
        # Suponha que a função recebe uma lista de consultas e retorna uma matriz 2D
        # de frequência relativa entre categorias (ex: período do dia vs dia da semana).
        return [
            {"dia": "seg", "periodo": "manha", "quantidade": 10},
            {"dia": "seg", "periodo": "tarde", "quantidade": 5},
            {"dia": "ter", "periodo": "manha", "quantidade": 8},
            {"dia": "ter", "periodo": "tarde", "quantidade": 12},
        ]

    def test_matriz_consistente(self, dados_heatmap):
        """Verifica que a soma de todos os elementos da matriz é igual a 1 (se normalizada)."""
        matriz = gerar_matriz_heatmap(dados_heatmap)
        # matriz é uma lista de listas de floats
        soma_total = sum(sum(linha) for linha in matriz)
        assert soma_total == pytest.approx(1.0)

    def test_matriz_valores_no_intervalo(self, dados_heatmap):
        """Todos os valores da matriz devem estar entre 0 e 1."""
        matriz = gerar_matriz_heatmap(dados_heatmap)
        for linha in matriz:
            for valor in linha:
                assert 0.0 <= valor <= 1.0

    def test_matriz_dimensoes(self, dados_heatmap):
        """Verifica que a matriz tem dimensões esperadas (ex: 7 dias x 2 períodos)."""
        matriz = gerar_matriz_heatmap(dados_heatmap)
        # Supondo que o heatmap é dia x período, esperamos 7x2 (dias da semana)
        assert len(matriz) == 7  # dias
        assert all(len(linha) == 2 for linha in matriz)  # períodos

    def test_matriz_vazia(self):
        """Matriz com dados vazios deve retornar uma matriz de zeros ou levantar erro."""
        with pytest.raises(ValueError):
            gerar_matriz_heatmap([])

# ========== Testes para Agregação de Diagnóstico por CIAP-2 ==========

class TestAgregacaoCiap2:
    """Testes para agregação de diagnósticos prevalentes por CIAP-2."""

    def test_agregacao_contagem(self, consultas_exemplo):
        """Verifica a contagem correta de consultas por código CIAP-2."""
        agregado = agregar_diagnosticos_por_ciap2(consultas_exemplo)
        # Esperamos: A01:3, B02:2, C03:1
        assert agregado["A01"] == 3
        assert agregado["B02"] == 2
        assert agregado["C03"] == 1

    def test_agregacao_ordem(self, consultas_exemplo):
        """Verifica que o dicionário está ordenado por contagem decrescente."""
        agregado = agregar_diagnosticos_por_ciap2(consultas_exemplo)
        # Ordenar por valor decrescente
        itens = list(agregado.items())
        for i in range(len(itens)-1):
            assert itens[i][1] >= itens[i+1][1]

    def test_agregacao_somente_compareceram(self, consultas_exemplo):
        """Se considerarmos apenas consultas que compareceram, a contagem muda."""
        consultas_compareceram = [c for c in consultas_exemplo if c.compareceu]
        agregado = agregar_diagnosticos_por_ciap2(consultas_compareceram)
        assert agregado["A01"] == 2  # id 1 e 6
        assert agregado["B02"] == 2
        assert "C03" not in agregado  # não compareceu

    def test_agregacao_vazia(self):
        """Lista vazia deve retornar dicionário vazio."""
        agregado = agregar_diagnosticos_por_ciap2([])
        assert agregado == {}
```

Mas, as funções `calcular_taxa_absenteismo`, `gerar_matriz_heatmap` e `agregar_diagnosticos_por_ciap2` ainda não existem. Para que os testes rodem, precisamos implementá-las. Como a tarefa pede apenas os testes, vou deixar isso comentado. No entanto, para que o arquivo de teste seja executável, poderíamos criar um módulo de exemplo no próprio teste? Não, porque o propósito é testar o código real.

Talvez seja melhor criar testes que usam funções reais que serão implementadas, e no arquivo de teste, importar de um módulo que ainda não existe. O usuário que receber esses testes precisará implementar as funções. Isso é comum em desenvolvimento orientado a testes.

Vou incluir também testes de tipagem com Pydantic v2, mas os testes acima já usam Pydantic para os modelos. SQLAlchemy pode ser usado em fixtures para criar banco de dados em memória, mas não é necessário para esses testes de cálculo puro.

Vou melhorar os testes para verificar o comportamento de divisão por zero explicitamente. O teste `test_taxa_com_zero_total` atualmente tem um `pytest.raises(ZeroDivisionError)` mas depois chama a função e espera 0. Isso está mal escrito. Vou corrigir: verificar que a função retorna 0 em vez de lançar erro. Se a função não proteger, o teste falhará com ZeroDivisionError, o que é o esperado (mostrando que não está protegida). Para fazer isso, escrevo:

```python
def test_taxa_com_zero_total(self):
    resultado = calcular_taxa_absenteismo(0, 0)
    assert resultado == 0
```

Se a função não proteger, isso lançará ZeroDivisionError e o teste falhará, indicando que a proteção não foi implementada. Isso é bom.

Além disso, devemos testar a divisão protegida por zero para o caso de total=0 e faltas=0, e talvez total=0 e faltas>0 (o que é inválido). Vou adicionar.

Vou também adicionar testes para a matriz de heatmap considerando que a função pode receber dados com chaves diferentes. Mas vou manter simples.

Agora, escrever o código final com comentários e docstrings.

Vou colocar o código final.```python
# Arquivo: backend/tests/test_analytics_kpis.py
"""
Testes de precisão algorítmica dos indicadores e agregações para o Projeto MedIA.

Cobre:
- Cálculo exato da taxa de absenteísmo com divisão protegida por zero.
- Consistência da matriz de heatmap.
- Agregações de diagnóstico prevalente por CIAP-2.

Padrões utilizados:
- Python 3.12, Pydantic v2, SQLAlchemy 2.0 (usados nas fixtures/estruturas de dados).
- pytest para execução.
"""

import pytest
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# =============================================================================
# Suposição: as funções a serem testadas estão em backend.app.services.analytics
# =============================================================================
from backend.app.services.analytics import (
    calcular_taxa_absenteismo,
    gerar_matriz_heatmap,
    agregar_diagnosticos_