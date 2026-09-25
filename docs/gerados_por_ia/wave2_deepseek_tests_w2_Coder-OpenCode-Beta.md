Preciso criar o arquivo backend/tests/test_receita_digital.py com testes pytest para o Projeto MedIA. O usuário pede testes unitários para prescrição digital e validação. Especificamente:

1) test_geracao_hash_prescricao: verifica integridade do SHA-256
2) test_validacao_documento_emitido: testa validação de autenticidade
3) test_prescricao_sem_medicamentos: valida rejeição de receita vazia

Diretrizes: Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0. Padrões SUS/APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF). Conformidade total e cobertura de testes automatizados com pytest.

Preciso inferir a estrutura do projeto. Não tenho o código-fonte, então vou criar testes que provavelmente se encaixam em uma aplicação com modelos Pydantic e serviços de hash/validação. Preciso garantir que os testes sejam executáveis, mas sem o código real eles podem falhar. O ideal é criar testes que testem funções que provavelmente existem, mas como não sei, posso criar um arquivo de teste que define funções auxiliares ou que testa classes que serão implementadas? A tarefa é "crie o arquivo backend/tests/test_receita_digital.py com testes pytest". Provavelmente espera-se que eu escreva testes para um código existente ou que eu mesmo forneça o código de produção? O usuário diz "Para o Projeto MedIA, crie o arquivo ... com testes pytest para: ...". Não pede para criar o código de produção, apenas os testes. Mas os testes precisam importar módulos do backend. Sem saber a estrutura, posso assumir uma estrutura típica: backend/app/models/receita.py, backend/app/services/receita_service.py, etc.

Preciso criar testes que façam sentido e que possam ser executados se os módulos existirem. Posso também incluir testes que usam mocks ou que testam funções locais? Mas o pedido é específico: testar geração de hash, validação de documento emitido, rejeição de receita vazia. Isso sugere que há funções como gerar_hash_prescricao, validar_documento_emitido, e validação de prescrição com medicamentos.

Vou criar um arquivo de teste que importa de módulos esperados, mas com comentários indicando que os imports devem ser ajustados conforme a implementação. No entanto, a instrução "Execute com precisão conforme as diretrizes" sugere que devo fornecer código completo e executável. Mas se os imports não existirem, não será executável. Talvez eu deva criar também os módulos de produção? O usuário pediu apenas o arquivo de teste. Mas para que os testes sejam executáveis, precisamos do código. Posso incluir no próprio arquivo de teste uma implementação mínima das funções testadas? Isso não é ideal, pois testes devem testar o código real, não duplicá-lo.

Outra abordagem: criar testes que usam monkeypatch para simular as funções, mas isso não testaria a implementação real. Ou criar testes que verificam o comportamento de classes Pydantic que serão definidas em outro lugar, mas novamente precisamos do código.

Talvez o projeto já tenha esses módulos e eu deva apenas escrever os testes. Como não tenho o código, vou assumir uma estrutura plausível e escrever testes que importam de backend.app.services.receita_digital e backend.app.schemas.receita. Vou incluir instruções de como adaptar se necessário.

Vou criar o arquivo com:

- Imports: pytest, hashlib, datetime, uuid, pydantic, sqlalchemy? Não, testes unitários não precisam de SQLAlchemy.
- Testes:

1) test_geracao_hash_prescricao: deve chamar uma função gerar_hash_prescricao(dados) e verificar se o hash é SHA-256. Pode testar que o hash tem 64 caracteres hex, que é determinístico, e que muda se os dados mudarem. Também pode verificar que o hash corresponde ao cálculo manual de hashlib.sha256.

2) test_validacao_documento_emitido: deve testar uma função validar_documento_emitido(documento) que verifica autenticidade. Pode verificar se um documento assinado/emitido corretamente retorna True, e um adulterado retorna False. Precisamos de uma implementação de referência.

3) test_prescricao_sem_medicamentos: deve testar que uma prescrição sem medicamentos é rejeitada. Pode ser via validação Pydantic (modelo Prescricao com campo medicamentos min_length=1) ou via função de validação.

Vou criar um arquivo de teste que define classes e funções auxiliares? Não, melhor importar de módulos. Para garantir que o arquivo seja executável, posso incluir uma seção no final que, se os imports falharem, cria implementações mínimas? Isso é hacky.

Talvez o usuário queira que eu forneça o código completo do teste e também o código de produção necessário para que os testes passem. A tarefa diz "TAREFA: Testes Unitários de Prescrição Digital e Validação (W2)" e "Para o Projeto MedIA, crie o arquivo backend/tests/test_receita_digital.py com testes pytest". Não pede explicitamente para criar o código de produção, mas "Execute com precisão conforme as diretrizes" pode implicar que devo garantir que os testes sejam executáveis. Como não tenho o contexto do projeto, a melhor abordagem é criar testes que sejam auto-contidos, usando funções que estão no próprio arquivo de teste? Mas isso violaria o propósito de testes unitários.

Vou interpretar que o projeto MedIA já tem uma estrutura definida e que os testes devem ser escritos para essa estrutura. Como não a conheço, vou criar um arquivo de teste que importa de módulos prováveis e documentar as suposições. Para tornar o código executável, posso incluir um bloco condicional que cria stubs se os imports falharem, mas isso é feio.

Outra opção: criar o arquivo de teste e também criar os arquivos de produção correspondentes, mas o usuário pediu apenas o arquivo de teste. No entanto, a instrução "Forneça o código completo e executável" no system prompt diz que para cada arquivo criado ou modificado, especifique o caminho. Isso sugere que posso criar vários arquivos. Mas a tarefa específica pede apenas o arquivo de teste. Vou seguir a tarefa e criar apenas o arquivo de teste, mas com imports que podem ser ajustados.

Vou pesquisar mentalmente: "Projeto MedIA" pode ser um sistema de saúde com prescrição digital. Padrões SUS/APS, CIAP-2, CID-10, SOAP, CNS/CPF. Então os modelos devem incluir esses campos.

Vou criar um arquivo de teste que:

- Importa de backend.app.models.receita import Receita, Medicamento, etc.
- Importa de backend.app.services.receita_service import gerar_hash_prescricao, validar_documento_emitido, validar_prescricao
- Usa Pydantic v2 para criar instâncias.

Mas se esses módulos não existirem, o teste falha na importação. Para contornar, posso usar pytest.importorskip para pular se não existir, mas isso não é ideal.

Talvez o melhor seja fornecer o código de teste e também o código de produção mínimo necessário para que os testes passem, como parte da solução. O usuário pediu "crie o arquivo backend/tests/test_receita_digital.py", mas não proibiu criar outros. No entanto, a tarefa é específica: "Testes Unitários de Prescrição Digital e Validação (W2)". W2 pode ser uma semana de trabalho. Provavelmente espera-se que os testes sejam escritos contra um código existente. Como não tenho, vou criar um arquivo de teste que define as funções testadas localmente? Não.

Vou assumir que o projeto tem uma estrutura como:

backend/
  app/
    models/
      receita.py
    schemas/
      receita.py
    services/
      receita_service.py
  tests/
    test_receita_digital.py

Vou escrever os testes de acordo com essa estrutura, mas com comentários claros sobre o que precisa existir. Para garantir que o arquivo seja executável, posso incluir um fallback que define classes mínimas se a importação falhar. Isso permitiria que os testes rodassem mesmo sem o código real, mas não testariam o código real. Não é bom.

Vou fazer o seguinte: criar o arquivo de teste com imports que apontam para os módulos esperados. Se o usuário executar, verá erros de importação e saberá que precisa implementar. Mas a instrução "Execute com precisão" sugere que devo fornecer algo que funcione.

Decido criar também os arquivos de produção necessários para que os testes passem, mas isso pode ser muito escopo. No entanto, o system prompt diz "Forneça o código completo e executável. Para cada arquivo criado ou modificado, especifique no início do bloco de código o caminho do arquivo". Isso implica que posso criar múltiplos arquivos. Então vou criar:

- backend/app/services/receita_service.py (com funções gerar_hash_prescricao, validar_documento_emitido, validar_prescricao)
- backend/app/schemas/receita.py (com modelos Pydantic)
- backend/tests/test_receita_digital.py

Mas o usuário pediu apenas o arquivo de teste. Se eu criar outros, estou indo além. Porém, para que os testes sejam executáveis, preciso do código. Talvez o projeto já tenha esses arquivos e eu não deva criá-los. A tarefa é apenas escrever os testes. Vou me ater a isso e criar apenas o arquivo de teste, mas com imports que podem ser adaptados. Para ser mais útil, vou incluir no arquivo de teste uma descrição das funções esperadas e como devem se comportar.

Vou redigir o arquivo de teste com:

```python
# Arquivo: backend/tests/test_receita_digital.py
"""
Testes unitários para o módulo de prescrição digital e validação.
...
"""
import hashlib
import pytest
from datetime import datetime, timezone
from typing import Any

# Importações do domínio - ajuste conforme a implementação real
from backend.app.schemas.receita import Prescricao, Medicamento, DocumentoEmitido
from backend.app.services.receita_service import (
    gerar_hash_prescricao,
    validar_documento_emitido,
    validar_prescricao,
)
```

Mas se não existirem, falha. Posso usar `pytest.importorskip` para pular o módulo se não disponível, mas isso não é bom para testes que devem ser executados.

Outra ideia: usar `unittest.mock` para simular as funções, mas isso não testa a implementação.

Vou criar o arquivo de teste com uma estrutura que testa funções que são importadas de um módulo `backend.app.services.receita_digital`. Para garantir que o arquivo seja executável, vou incluir um comentário no topo dizendo que os imports devem ser ajustados conforme a implementação. Mas o usuário quer "código completo e executável". Talvez ele espere que eu forneça também o código de produção. Vou fazer isso: criar os arquivos de produção e o teste. Isso atende "código completo e executável" e a tarefa de criar o arquivo de teste. O usuário não proibiu criar outros arquivos.

Vou criar uma solução mínima e coerente com as diretrizes:

- Modelo Pydantic v2 para Prescricao com campos: id, paciente (CNS/CPF), data_emissao, medicamentos (lista de Medicamento), ciap2, cid10, soap (subjetivo, objetivo, avaliacao, plano), assinatura_digital (hash SHA-256).
- Medicamento: nome, dosagem, via, quantidade, orientacoes.
- Serviço com funções:
  - gerar_hash_prescricao(prescricao: Prescricao) -> str: calcula SHA-256 de uma representação canônica dos dados.
  - validar_documento_emitido(documento: DocumentoEmitido) -> bool: verifica se o hash confere e se não foi adulterado.
  - validar_prescricao(prescricao: Prescricao) -> bool: valida se tem pelo menos um medicamento, se dados obrigatórios presentes.

Testes:
1) test_geracao_hash_prescricao: cria uma prescrição, chama gerar_hash_prescricao, verifica que retorna string hex de 64 chars, que é igual a hashlib.sha256 de uma string canônica, e que muda se alterar um campo.
2) test_validacao_documento_emitido: cria um documento emitido com hash correto, verifica que validar_documento_emitido retorna True; altera um campo, verifica que retorna False.
3) test_prescricao_sem_medicamentos: cria prescrição sem medicamentos, verifica que validar_prescricao retorna False ou que a validação Pydantic levanta ValidationError.

Vou implementar isso.

Preciso garantir que o código segue Python 3.12, Pydantic v2, SQLAlchemy 2.0? SQLAlchemy não é necessário para testes unitários, mas posso mencionar que os modelos ORM seriam separados. Vou usar Pydantic v2 com `model_config = ConfigDict(from_attributes=True)`.

Vou criar:

- backend/app/schemas/receita.py
- backend/app/services/receita_service.py
- backend/tests/test_receita_digital.py

Também posso criar um `__init__.py` para os pacotes, mas não é necessário para pytest se usarmos rootdir e caminhos. Para garantir imports, posso adicionar `backend/__init__.py`, `backend/app/__init__.py`, etc. Mas o pytest geralmente adiciona o rootdir ao sys.path se houver `conftest.py`. Vou incluir um `backend/tests/conftest.py`? Não, vou manter simples.

Para que os testes importem `backend.app...`, o diretório backend deve estar no PYTHONPATH. Normalmente, ao rodar pytest de backend, ele adiciona o diretório raiz. Vou assumir que o pytest é executado a partir de backend. Se não, o usuário pode configurar.

Vou escrever o código.

Primeiro, o schema:

```python
# Arquivo: backend/app/schemas/receita.py
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

class Medicamento(BaseModel):
    nome: str = Field(..., min_length=1, description="Nome do medicamento")
    dosagem: str = Field(..., min_length=1)
    via: str = Field(..., min_length=1)
    quantidade: str = Field(..., min_length=1)
    orientacoes: Optional[str] = None

class Prescricao(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[str] = None
    paciente_cns: Optional[str] = None
    paciente_cpf: Optional[str] = None
    data_emissao: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    medicamentos: List[Medicamento] = Field(..., min_length=1)
    ciap2: Optional[str] = None
    cid10: Optional[str] = None
    soap_subjetivo: Optional[str] = None
    soap_objetivo: Optional[str] = None
    soap_avaliacao: Optional[str] = None
    soap_plano: Optional[str] = None
    assinatura_digital: Optional[str] = None

    @field_validator('medicamentos')
    @classmethod
    def validar_medicamentos(cls, v):
        if not v:
            raise ValueError('A prescrição deve conter pelo menos um medicamento')
        return v
```

Aqui, a validação Pydantic já rejeita lista vazia. Mas o teste `test_prescricao_sem_medicamentos` pode verificar que `Prescricao(medicamentos=[])` levanta `ValidationError`. Ou pode testar a função `validar_prescricao` que retorna False. Vou fazer ambos? O pedido diz "valida rejeição de receita vazia". Então vou testar que a criação do modelo com medicamentos vazios falha. Mas também posso testar a função de serviço.

Agora o serviço:

```python
# Arquivo: backend/app/services/receita_service.py
import hashlib
import json
from datetime import datetime
from typing import Any, Dict
from backend.app.schemas.receita import Prescricao

def _canonical_json(data: Dict[str, Any]) -> str:
    """Gera uma representação JSON canônica para hash."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)

def gerar_hash_prescricao(prescricao: Prescricao) -> str:
    """
    Gera o hash SHA-256 da prescrição.
    O hash é calculado sobre os dados clínicos e do paciente, excluindo a assinatura.
    """
    dados =