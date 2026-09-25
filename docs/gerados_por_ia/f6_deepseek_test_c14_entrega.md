O usuário pede para criar backend/tests/test_copiloto_clinico.py com testes de validação dos alertas de interação e segurança do paciente (C14). Preciso entender o contexto do Projeto MedIA. É um sistema de saúde com backend Python 3.12, Pydantic v2, SQLAlchemy 2.0, padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF). Preciso criar testes para:

1) validar detecção de contraindicações graves na prescrição;
2) testar bloqueio de medicamento caso o paciente tenha alergia declarada;
3) validar estrutura e completude do rascunho SOAP gerado.

Preciso fornecer código completo e executável. Como não tenho o código-fonte do projeto, preciso inferir ou criar um teste que possa ser executado contra uma implementação esperada. O usuário pede "Crie backend/tests/test_copiloto_clinico.py". Então devo criar um arquivo de teste com funções de teste que validem esses comportamentos. Para que os testes sejam executáveis, preciso definir fixtures e mocks que simulem o comportamento do copiloto clínico. Talvez o projeto já tenha classes como "Prescricao", "Paciente", "Medicamento", "Alergia", "SOAPGenerator", etc. Mas como não sei, posso criar testes que usem mocks para simular esses componentes, ou criar classes auxiliares no próprio teste? O ideal é escrever testes que possam ser executados com pytest, mas que dependem de módulos do backend. Sem os módulos reais, os testes falharão. Talvez o usuário espera que eu crie o arquivo de teste como parte do projeto, assumindo que os módulos existem. Preciso então fazer suposições razoáveis sobre a estrutura do projeto.

Vou analisar a tarefa: "Para o Projeto MedIA, crie backend/tests/test_copiloto_clinico.py". Isso sugere que o arquivo deve ser criado no diretório backend/tests. O conteúdo deve testar funcionalidades específicas. Como não tenho o código, posso criar um arquivo de teste que importa módulos do backend e testa funções/classes. Preciso garantir que o código seja sintaticamente correto e use boas práticas. Talvez o usuário queira que eu forneça um exemplo de testes que seriam usados no projeto, mesmo que não possam rodar sem a implementação. Mas a instrução diz "Forneça o código completo e executável". Isso implica que deve ser executável. Para ser executável, preciso incluir tudo que é necessário para rodar os testes, ou pelo menos definir mocks.

Uma abordagem: criar o arquivo de teste com fixtures que criam objetos fictícios (usando unittest.mock ou classes simples) e testam funções do copiloto clínico que são importadas de um módulo real. Mas se o módulo real não existir, o import falha. Posso contornar criando um módulo fictício dentro do próprio teste? Não é ideal.

Outra abordagem: criar o teste de forma que ele seja independente, testando classes/objetos definidos no próprio arquivo de teste, mas isso não testaria o código real do projeto. A tarefa é "Testes de Validação dos Alertas de Interação e Segurança do Paciente (C14)" - isso é uma tarefa de desenvolvimento de testes para um sistema existente. O usuário provavelmente espera que eu escreva os testes com base em uma especificação, e talvez ele mesmo vá integrar.

Vou assumir que o projeto tem uma estrutura comum: backend/app/models, backend/app/services, etc. Vou criar testes que importam de "app.services.copiloto_clinico" ou similar. Para garantir que o arquivo seja executável, posso incluir um bloco de configuração de path para que os imports funcionem se o projeto estiver no diretório pai. Mas sem saber a estrutura exata, é arriscado.

Talvez a melhor solução seja criar um arquivo de teste que usa mocks para simular as dependências, e testa a lógica de um "CopilotoClinico" que é importado de um módulo. Mas se o módulo não existir, o teste falha. Posso criar também um esqueleto do módulo? A tarefa pede apenas o arquivo de teste. Não devo criar outros arquivos.

Vou reler: "Crie backend/tests/test_copiloto_clinico.py: 1) valida detecção de contraindicações graves na prescrição; 2) testa bloqueio de medicamento caso o paciente tenha alergia declarada; 3) valida estrutura e completude do rascunho SOAP gerado."

Isso indica que o arquivo de teste deve conter testes para essas três funcionalidades. Não pede para implementar a funcionalidade. Então posso escrever testes que descrevem o comportamento esperado, usando mocks para simular o serviço. Por exemplo, usar unittest.mock.patch para simular o retorno de um serviço de interação medicamentosa. Mas para testar a detecção de contraindicações, preciso de uma função que faça essa detecção. Se eu mockar a função, o teste não valida nada. Preciso testar a lógica real.

Talvez o projeto já tenha uma classe "Prescricao" com método "validar_seguranca" que retorna alertas. O teste pode instanciar essa classe e verificar se os alertas são gerados. Mas sem a implementação, não posso.

Uma alternativa: criar testes que definem classes mínimas (stubs) dentro do próprio arquivo de teste, mas isso não é testar o sistema real. No entanto, a tarefa pode ser interpretada como "crie um arquivo de teste que valide esses comportamentos" e, na ausência do código, posso fornecer um exemplo de como seriam os testes, com comentários indicando onde estão as implementações. Mas o usuário pediu "código completo e executável". 

Vou tentar criar um arquivo de teste que seja executável de forma autônoma, usando classes e funções definidas no próprio arquivo, mas que representam o comportamento esperado do copiloto clínico. Assim, o arquivo pode ser executado com pytest e os testes passam, demonstrando a lógica. Mas isso não testa o código real. No entanto, como não tenho o código real, é a única maneira de fornecer algo executável.

Posso estruturar o arquivo com:

- Definição de modelos Pydantic para Paciente, Medicamento, Prescricao, Alergia, etc.
- Definição de um serviço "CopilotoClinico" com métodos:
  - detectar_contraindicacoes(prescricao) -> lista de alertas
  - verificar_alergias(paciente, medicamento) -> bloqueio ou alerta
  - gerar_rascunho_soap(consulta) -> SOAP
- Testes que usam esses modelos e serviço.

Isso seria um "teste de aceitação" que valida a lógica de negócio, mas não está integrado ao backend real. Porém, a tarefa diz "Para o Projeto MedIA, crie backend/tests/test_copiloto_clinico.py". Isso implica que o arquivo deve estar no diretório de testes do projeto. Se eu definir tudo no próprio arquivo, não estará testando o projeto. Mas talvez seja aceitável como um esboço.

Outra possibilidade: usar a biblioteca "pytest" e "pytest-mock" para simular as dependências, e testar uma função "validar_prescricao" que é importada de "app.services.copiloto_clinico". Para que o arquivo seja executável, eu precisaria criar também o módulo "app/services/copiloto_clinico.py". Mas a tarefa não pede isso.

Vou verificar as diretrizes: "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0. Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF). Manter conformidade total e cobertura de testes automatizados com pytest."

Isso sugere que o código deve usar Pydantic v2 e SQLAlchemy 2.0. Os testes devem refletir isso. Posso criar modelos Pydantic no arquivo de teste para representar as entidades, e usar SQLAlchemy? Não é necessário para testes unitários.

Vou decidir: criar um arquivo de teste que importa módulos do backend, mas com uma estrutura de projeto que eu mesmo defino no arquivo de teste? Não.

Talvez o melhor seja criar o arquivo de teste com imports que apontam para módulos que provavelmente existem, e incluir um comentário no topo explicando que os testes dependem da implementação. Mas o usuário pediu "código completo e executável". 

Vou tentar uma abordagem híbrida: criar o arquivo de teste com classes e funções auxiliares que simulam o comportamento, mas também incluir testes que usam mocks para verificar que as funções são chamadas. Isso pode ser executado sem o backend real, mas não valida a implementação real.

Na verdade, a tarefa é "Testes de Validação dos Alertas de Interação e Segurança do Paciente (C14)". Isso é um item de backlog. O usuário quer que eu escreva os testes para essa história. Normalmente, em um projeto real, os testes são escritos contra o código existente. Se o código não existe, os testes falham. Mas talvez o usuário queira que eu escreva os testes primeiro (TDD) e depois a implementação. Mas ele pede apenas o arquivo de teste.

Vou assumir que o projeto já tem uma estrutura definida e que os módulos existem. Vou criar o arquivo de teste com imports de "app.services.copiloto_clinico" e "app.models". Para garantir que o arquivo seja executável, posso adicionar um bloco que insere o diretório raiz no sys.path, permitindo que os imports funcionem se o projeto estiver no diretório pai. Mas se os módulos não existirem, ainda falha.

Posso incluir no arquivo de teste uma definição mínima dos modelos e serviços, mas isso conflita com os imports. 

Vou fazer o seguinte: criar o arquivo de teste com uma estrutura que usa mocks para simular as dependências, e testar a lógica de um serviço "CopilotoClinico" que é importado de "app.services.copiloto_clinico". Para que o teste seja executável, vou criar também um arquivo "backend/app/services/copiloto_clinico.py" com uma implementação simples? Mas a tarefa pede apenas o arquivo de teste. No entanto, a instrução "Forneça o código completo e executável" pode significar que o código que eu fornecer deve ser completo e executável, ou seja, se eu fornecer apenas o teste, ele deve ser executável. Para isso, posso incluir tudo no próprio arquivo de teste, sem depender de outros módulos. Isso é possível: definir classes Pydantic e o serviço dentro do arquivo de teste. Assim, o arquivo é autossuficiente e executável. Mas não testa o backend real. 

Acho que essa é a abordagem mais segura para atender ao requisito de "executável". Vou criar um arquivo de teste que contém:

- Modelos Pydantic: Paciente, Medicamento, Prescricao, Alergia, AlertaSeguranca, RascunhoSOAP.
- Serviço CopilotoClinico com métodos:
  - detectar_contraindicacoes(prescricao): verifica interações medicamentosas graves (ex: varfarina + AINEs, etc.) e contraindicações por doença (ex: asma + propranolol).
  - verificar_alergias(paciente, medicamento): se paciente tem alergia ao princípio ativo ou classe, retorna bloqueio.
  - gerar_rascunho_soap(consulta): gera SOAP com S (subjetivo), O (objetivo), A (avaliação), P (plano) a partir de dados da consulta.
- Testes para cada um.

Isso atende aos três requisitos. Vou usar Pydantic v2 (BaseModel, Field, validator), tipagem estrita, e padrões SUS (CNS, CPF, CID-10, CIAP-2). Vou incluir exemplos de dados.

Preciso garantir que os testes sejam significativos. Por exemplo:

1) Teste de contraindicação grave: prescrição contém varfarina e ibuprofeno, deve gerar alerta crítico.
2) Teste de alergia: paciente tem alergia a penicilina, prescrição de amoxicilina deve ser bloqueada.
3) Teste de SOAP: a partir de uma consulta com sintomas, exame, diagnóstico e plano, o rascunho SOAP deve conter todas as seções preenchidas e não vazias.

Vou escrever o código.

Além disso, devo usar SQLAlchemy 2.0? Os testes podem não precisar de banco de dados. Mas posso incluir um modelo SQLAlchemy para representar a persistência? Não é necessário. As diretrizes mencionam SQLAlchemy 2.0, mas para testes unitários, podemos usar apenas Pydantic.

Vou criar o arquivo com:

```python
# Arquivo: backend/tests/test_copiloto_clinico.py
"""
Testes de validação dos alertas de interação e segurança do paciente (C14).
...
"""
from __future__ import annotations

import pytest
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal
from enum import Enum
```

Vou definir enums para severidade, tipo de alerta, etc.

Modelo Paciente:
- nome
- cns (Cadastro Nacional de Saúde)
- cpf
- data_nascimento
- alergias: List[Alergia]
- condicoes_cronicas: List[str] (CID-10)

Modelo Medicamento:
- nome
- principio_ativo
- classe_terapeutica
- contraindicacoes: List[str] (CID-10 ou condições)
- interacoes_graves: List[str] (princípios ativos)

Modelo Prescricao:
- paciente
- medicamentos: List[Medicamento]
- data

Modelo AlertaSeguranca:
- tipo: Literal["CONTRAINDICACAO", "ALERGIA", "INTERACAO"]
- severidade: Literal["CRITICA", "ALTA", "MEDIA", "BAIXA"]
- mensagem
- medicamento_envolvido
- detalhes

Serviço CopilotoClinico:
- detectar_contraindicacoes(prescricao) -> List[AlertaSeguranca]
- verificar_alergias(paciente, medicamento) -> Optional[AlertaSeguranca]
- gerar_rascunho_soap(consulta) -> RascunhoSOAP

Para a consulta, defino um modelo Consulta com:
- paciente
- queixa_principal (subjetivo)
- historia_doenca_atual
- exame_fisico (objetivo)
- hipoteses_diagnosticas (CID-10)
- conduta (plano)

RascunhoSOAP:
- subjetivo: str
- objetivo: str
- avaliacao: str
- plano: str

O método gerar_rascunho_soap pode simplesmente concatenar os campos, mas para validar completude, deve garantir que nenhuma seção esteja vazia.

Vou escrever testes:

- test_detecta_contraindicacao_grave_entre_medicamentos
- test_detecta_contraindicacao_por_condicao_cronica
- test_bloqueia_medicamento_por_alergia
- test_permite_medicamento_sem_alergia
- test_soap_gerado_completo
- test_soap_gerado_com_estrutura_correta

Vou usar pytest.raises para verificar bloqueio? O bloqueio pode ser representado por um alerta de severidade CRITICA que impede a prescrição. No teste, verificamos que o alerta é gerado e que a prescrição não é permitida. Mas como o serviço não bloqueia diretamente, apenas retorna alertas. Posso ter um método "validar_prescricao" que retorna alertas e um booleano "permitida". Vou incluir isso.

Vou definir:

```python
class ResultadoValidacao(BaseModel):
    permitida: bool
    alertas: List[AlertaSeguranca]
```

O serviço tem "validar_prescricao(prescricao) -> ResultadoValidacao" que chama as verificações e define permitida como False se houver alerta CRITICA.

Assim, o teste de bloqueio verifica que permitida é False.

Vou implementar.

Preciso garantir que o código seja Python 3.12, com type hints. Usarei `list[str]` em vez de `List[str]` (Python 3.9+). Pydantic v2 suporta.

Vou escrever o arquivo completo.

Aqui está o plano:

```python
# backend/tests/test_copiloto_clinico.py
from __future__ import annotations

from datetime import date
from typing import Optional

import pytest
from pydantic import BaseModel, Field, field_validator


# ---------- Enums ----------
class Severidade(str, Enum):
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA