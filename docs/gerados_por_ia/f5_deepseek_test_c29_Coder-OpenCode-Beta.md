O usuário pede para criar backend/tests/test_sync_offline.py para o Projeto MedIA, validando três coisas: sincronização de fila outbox sem perda de dados; resolução correta de conflito de prontuário modificado concorrentemente; validação de integridade criptográfica do lote sincronizado.

Preciso entender o contexto: Projeto MedIA, backend com Python 3.12, Pydantic v2, SQLAlchemy 2.0, padrões SUS/APS (CIAP-2, CID-10, SOAP, CNS/CPF). O teste deve ser executado com pytest.

Preciso criar um arquivo de teste que valide esses comportamentos. Mas não tenho o código-fonte do projeto. Preciso inferir ou criar mocks/implementações mínimas para testar. O usuário pede "crie backend/tests/test_sync_offline.py" validando esses cenários. Provavelmente espera que eu escreva testes que possam ser executados contra o código existente, mas como não tenho o código, devo criar um teste que defina classes/funções mock ou que importe módulos esperados. Melhor abordagem: criar um arquivo de teste que seja auto-contido, com fixtures e classes auxiliares que simulam o comportamento esperado, mas que também possa ser adaptado. No entanto, o pedido é específico: "Para o Projeto MedIA, crie backend/tests/test_sync_offline.py". Então devo criar o arquivo de teste.

Preciso garantir que o teste cubra:

1) Sincronização de fila outbox sem perda de dados: testar que eventos enfileirados no outbox são todos sincronizados, mesmo se houver falhas parciais, e que nenhum dado é perdido.

2) Resolução correta de conflito de prontuário modificado concorrentemente: testar que quando dois dispositivos modificam o mesmo prontuário offline, o conflito é resolvido corretamente (ex: última escrita vence, ou merge, ou versão). Preciso definir uma estratégia de resolução.

3) Validação de integridade criptográfica do lote sincronizado: testar que o lote de dados sincronizados tem uma assinatura/hash que garante integridade, e que qualquer alteração é detectada.

Como não há código, vou criar um teste que define classes e funções auxiliares dentro do próprio arquivo de teste, simulando o domínio. Mas isso não testaria o código real. Talvez o projeto já tenha esses componentes. O usuário não forneceu detalhes. Posso assumir que existem módulos como `backend.app.services.sync`, `backend.app.models.outbox`, etc. Mas não sei.

Uma abordagem comum em tarefas de geração de código: criar testes que definem o comportamento esperado, usando mocks e fakes, e que podem ser executados isoladamente. O usuário pede "Execute com precisão conforme as diretrizes." Então devo fornecer um arquivo de teste completo e executável.

Vou criar um arquivo de teste que:

- Define uma estrutura mínima de classes para representar Outbox, Prontuário, LoteSincronizacao, etc., usando Pydantic v2 e SQLAlchemy 2.0 (mas como é teste, posso usar modelos em memória ou SQLite).
- Implementa funções de sincronização e resolução de conflito dentro do próprio teste (como helpers) para validar os cenários.
- Usa `pytest` e `pytest-asyncio` se necessário.

Mas o ideal é que o teste importe do código real. Como não tenho, vou criar um teste que é auto-suficiente, mas com comentários indicando onde integrar.

Vou estruturar o arquivo:

- Imports: pytest, pydantic, sqlalchemy, hashlib, hmac, etc.
- Definição de modelos Pydantic: `Prontuario`, `EventoOutbox`, `LoteSincronizacao`.
- Definição de classes de serviço: `OutboxService`, `SyncService`, `ConflitoResolver`.
- Testes para cada cenário.

Preciso garantir que os testes realmente validem os requisitos.

Vou pensar em cada cenário:

### 1. Sincronização de fila outbox sem perda de dados

- Criar um outbox com N eventos.
- Simular sincronização onde alguns eventos falham na primeira tentativa, mas são retentados.
- Verificar que todos os eventos são processados e nenhum é perdido.
- Usar um banco de dados SQLite em memória com SQLAlchemy para persistir a fila.

### 2. Resolução de conflito de prontuário modificado concorrentemente

- Dois dispositivos (A e B) modificam o mesmo prontuário offline a partir da mesma versão base.
- Ambos geram eventos de modificação.
- Ao sincronizar, o sistema detecta conflito (mesmo prontuário, versão base igual, mudanças diferentes).
- Aplica uma política de resolução (ex: last-write-wins baseado em timestamp, ou merge de campos).
- Verificar que o prontuário final é consistente e que nenhuma atualização é perdida silenciosamente.

### 3. Validação de integridade criptográfica do lote sincronizado

- Criar um lote de eventos serializados.
- Calcular um hash/assinatura HMAC sobre o conteúdo.
- Verificar que o hash é válido.
- Alterar um byte no lote e verificar que a validação falha.

Vou implementar isso com classes simples.

Como o usuário menciona "Padrões do SUS / APS (CIAP-2, CID-10, método SOAP, identificação por CNS/CPF)", posso incluir campos como `cns`, `cpf`, `cid10`, `ciap2`, `metodo_soap` nos modelos de prontuário.

Vou criar o arquivo com bastante cuidado.

Primeiro, vou definir a estrutura de diretórios: `backend/tests/test_sync_offline.py`. O arquivo deve ser executável com pytest.

Vou escrever o código:

```python
# backend/tests/test_sync_offline.py
"""
Testes de Resolução de Conflitos e Integridade Offline (C29)

Valida:
1. Sincronização de fila outbox sem perda de dados.
2. Resolução correta de conflito de prontuário modificado concorrentemente.
3. Validação de integridade criptográfica do lote sincronizado.

Conformidade com:
- Python 3.12, Pydantic v2, SQLAlchemy 2.0
- Padrões SUS/APS: CIAP-2, CID-10, SOAP, CNS/CPF
"""
```

Agora imports:

```python
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import pytest
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
```

Preciso de um modelo SQLAlchemy para outbox. Vou definir uma classe `EventoOutboxORM` e uma classe `ProntuarioORM` para persistência.

Mas para simplificar, posso usar apenas modelos Pydantic e simular a fila em memória. No entanto, o requisito "fila outbox" sugere persistência. Vou usar SQLite em memória com SQLAlchemy para dar realismo.

Vou definir:

- `Base(DeclarativeBase)`
- `EventoOutboxORM`: id, prontuario_id, versao_base, dados_json, status (pendente, processado, falha), criado_em, processado_em, tentativas.
- `ProntuarioORM`: id, cns, cpf, dados_json, versao, atualizado_em.

Mas para o teste de conflito, preciso de um modelo de prontuário com campos estruturados. Vou usar Pydantic para o domínio e SQLAlchemy para persistência.

Vou criar:

```python
class Prontuario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    cns: str
    cpf: str
    cid10: Optional[str] = None
    ciap2: Optional[str] = None
    metodo_soap: Optional[str] = None  # S, O, A, P
    conteudo_clinico: str
    versao: int = 1
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

E o evento de outbox:

```python
class EventoOutbox(BaseModel):
    id: str
    prontuario_id: str
    versao_base: int
    dados: Dict[str, Any]
    status: str = "pendente"
    tentativas: int = 0
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Agora, o serviço de sincronização. Vou criar uma classe `SyncService` que:

- `processar_outbox()`: pega eventos pendentes, tenta aplicar, se falhar incrementa tentativas e marca como falha após N tentativas.
- `resolver_conflito(prontuario_atual, evento)`: aplica política de resolução.

Para o teste, vou implementar uma função `sincronizar_evento(evento, prontuario_atual)` que retorna o prontuario atualizado ou levanta conflito.

Política de resolução: last-write-wins por timestamp, mas com registro de conflito. Ou merge de campos. Vou escolher uma política simples: se `versao_base` do evento == `versao` do prontuario atual, aplica diretamente e incrementa versão. Se não, há conflito. Para resolução, comparar `atualizado_em` do evento com o do prontuario atual; o mais recente vence. Mas como o evento contém dados completos do prontuário, podemos substituir.

No entanto, para testar "resolução correta", preciso de um cenário onde dois eventos concorrentes são aplicados e o resultado é previsível. Vou usar uma política de merge para campos não conflitantes e last-write-wins para campos conflitantes.

Vou simplificar: o prontuário tem um dicionário `campos` que pode ser mesclado. Cada evento contém um dicionário de alterações parciais. A resolução de conflito faz merge dos dicionários, com resolução de conflitos por campo usando timestamp.

Mas o modelo acima tem `conteudo_clinico` como string. Vou mudar para `campos: Dict[str, Any]` para facilitar merge.

Vou definir:

```python
class Prontuario(BaseModel):
    id: str
    cns: str
    cpf: str
    cid10: Optional[str] = None
    ciap2: Optional[str] = None
    metodo_soap: Optional[str] = None
    campos: Dict[str, Any] = Field(default_factory=dict)
    versao: int = 1
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Evento de alteração:

```python
class EventoAlteracao(BaseModel):
    prontuario_id: str
    versao_base: int
    campos_alterados: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Agora, o `SyncService`:

```python
class SyncService:
    def __init__(self, max_tentativas: int = 3):
        self.max_tentativas = max_tentativas

    def aplicar_evento(self, prontuario: Prontuario, evento: EventoAlteracao) -> Prontuario:
        if evento.versao_base != prontuario.versao:
            raise ConflitoError(...)
        novos_campos = {**prontuario.campos, **evento.campos_alterados}
        prontuario.campos = novos_campos
        prontuario.versao += 1
        prontuario.atualizado_em = evento.timestamp
        return prontuario

    def resolver_conflito(self, prontuario_atual: Prontuario, evento: EventoAlteracao) -> Prontuario:
        # merge por campo, último timestamp vence
        # para simplificar, se evento.timestamp > prontuario_atual.atualizado_em, aplica, senão mantém
        if evento.timestamp > prontuario_atual.atualizado_em:
            return self.aplicar_evento(prontuario_atual, evento)
        return prontuario_atual
```

Mas isso não é um merge, é last-write-wins. Para testar "resolução correta", posso verificar que o resultado é o esperado.

Vou implementar um merge mais sofisticado: para cada campo alterado no evento, se o campo não existe no prontuario atual, adiciona; se existe, compara timestamps de modificação por campo. Mas isso exigiria manutenção de metadados por campo. Vou simplificar: o evento contém `campos_alterados` com valores e o timestamp do evento é o momento da alteração. Se dois eventos alteram o mesmo campo, o que tiver timestamp mais recente vence. Para campos diferentes, ambos são incorporados.

Então:

```python
def resolver_conflito(self, prontuario_atual: Prontuario, evento: EventoAlteracao) -> Prontuario:
    # Se a versão base do evento é anterior à versão atual, há conflito.
    if evento.versao_base < prontuario_atual.versao:
        # Merge: para cada campo, se o campo foi alterado no evento e não foi alterado no prontuario atual desde a versão base, aplica.
        # Mas não temos histórico de alterações por campo. Vamos assumir que o prontuario_atual.campos contém os valores mais recentes conhecidos.
        # Para simplificar, se o timestamp do evento é maior que o timestamp do prontuario, aplica tudo; senão, descarta.
        if evento.timestamp > prontuario_atual.atualizado_em:
            return self.aplicar_evento(prontuario_atual, evento)
        return prontuario_atual
    else:
        return self.aplicar_evento(prontuario_atual, evento)
```

Isso é last-write-wins. Para testar "resolução correta", posso verificar que o prontuário final contém os campos do evento mais recente.

Mas o requisito diz "resolução correta de conflito de prontuário modificado concorrentemente". Isso pode ser interpretado como: quando dois dispositivos modificam o mesmo prontuário, o sistema deve detectar e resolver sem perder dados. Uma política comum é "merge de campos" onde alterações em campos diferentes são preservadas. Vou implementar um merge por campo com base em timestamps por campo.

Para isso, o prontuário precisa armazenar, para cada campo, o timestamp da última modificação. Vou adicionar `campos_metadata: Dict[str, datetime]`.

```python
class Prontuario(BaseModel):
    id: str
    cns: str
    cpf: str
    cid10: Optional[str] = None
    ciap2: Optional[str] = None
    metodo_soap: Optional[str] = None
    campos: Dict[str, Any] = Field(default_factory=dict)
    campos_metadata: Dict[str, datetime] = Field(default_factory=dict)
    versao: int = 1
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Evento de alteração:

```python
class EventoAlteracao(BaseModel):
    prontuario_id: str
    versao_base: int
    campos_alterados: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

Agora, `aplicar_evento` sem conflito:

```python
def aplicar_evento(self, prontuario: Prontuario, evento: EventoAlteracao) -> Prontuario:
    if evento.versao_base != prontuario.versao:
        raise ConflitoError(...)
    for campo, valor in evento.campos_alterados.items():
        prontuario.campos[campo] = valor
        prontuario.campos_metadata[campo] = evento.timestamp
    prontuario.versao += 1
    prontuario.atualizado_em = evento.timestamp
    return prontuario
```

`resolver_conflito`:

```python
def resolver_conflito(self, prontuario_atual: Prontuario, evento: EventoAlteracao) -> Prontuario:
    if evento.versao_base == prontuario_atual.versao:
        return self.aplicar_evento(prontuario_atual, evento)
    # Conflito: merge por campo
    for campo, valor in evento.campos_alterados.items():
        if campo not in prontuario_atual.campos_metadata:
            # campo novo, aplica
            prontuario_atual.campos[campo] = valor
            prontuario_atual.campos_metadata[campo] = evento.timestamp
        else:
            # se o evento é mais recente que a última modificação conhecida do campo, aplica
            if evento.timestamp > prontuario_atual.campos_metadata[campo]:
               