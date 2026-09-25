O usuário pede para criar um arquivo de teste backend/tests/test_sync_offline.py para o Projeto MedIA, validando três coisas: sincronização de fila outbox sem perda de dados, resolução de conflito de prontuário modificado concorrentemente, e validação de integridade criptográfica do lote sincronizado.

Preciso entender o contexto: Projeto MedIA, provavelmente um sistema de saúde com padrões SUS/APS, CIAP-2, CID-10, método SOAP, CNS/CPF. O backend usa Python 3.12, Pydantic v2, SQLAlchemy 2.0. Testes com pytest.

O usuário quer que eu crie o arquivo de teste. Mas para criar testes, preciso supor ou definir algumas estruturas de código existentes. Como não há código fornecido, devo criar testes que validem funcionalidades hipotéticas, mas de forma plausível e consistente com a arquitetura. Ou seja, devo escrever testes que exercitam funções/módulos que provavelmente existem no backend, como um serviço de sincronização offline, um repositório de outbox, etc.

Preciso garantir que os testes sejam executáveis. Para isso, posso definir fixtures e mocks, e talvez criar classes/objetos fictícios dentro do próprio arquivo de teste para simular o comportamento esperado. Mas o ideal é que os testes sejam escritos contra interfaces reais. Como não temos o código real, posso criar testes que usam mocks de funções que seriam implementadas, mas isso pode ser considerado "testes falsos". No entanto, a tarefa é criar o arquivo de teste, não implementar o backend. Então posso assumir que existem módulos como `backend.app.services.sync_offline`, `backend.app.models.outbox`, etc., e escrever testes que importam esses módulos. Mas se eles não existirem, os testes falharão. Para evitar isso, posso criar o arquivo de teste com imports condicionais ou com definições locais de classes para simular. Mas a instrução diz "Crie backend/tests/test_sync_offline.py validando: ...". Provavelmente espera-se que o arquivo seja parte de um projeto existente, mas como não temos, devemos fornecer um arquivo de teste bem estruturado que possa ser adaptado.

Vou adotar uma abordagem: criar o arquivo de teste com fixtures que usam um banco de dados SQLite em memória, SQLAlchemy 2.0, e definir modelos e serviços mínimos dentro do próprio arquivo de teste? Isso não é ideal porque testes devem testar o código real, não duplicá-lo. Mas como não temos o código, talvez seja aceitável criar um arquivo de teste que define classes de apoio para simular o ambiente, e então testar a lógica de sincronização de forma isolada.

Outra abordagem: escrever testes que usam `unittest.mock` para simular as dependências, e testar funções que seriam chamadas. Por exemplo, testar que `sync_outbox()` chama `process_outbox()` e `mark_as_synced()` sem perda de dados, usando mocks. Isso é mais viável.

Preciso também considerar os requisitos específicos:

1) sincronização de fila outbox sem perda de dados: deve verificar que todos os itens da fila são processados e marcados como sincronizados, mesmo se ocorrerem erros em alguns itens? Ou que a fila é atômica? Provavelmente testar que após a sincronização, não há itens pendentes e que todos os eventos foram enviados.

2) resolução correta de conflito de prontuário modificado concorrentemente: deve testar que quando duas versões de um prontuário são modificadas ao mesmo tempo, o conflito é resolvido de acordo com alguma política (ex: última escrita vence, ou merge, ou versão mais recente). Preciso definir uma política. No contexto de saúde, pode ser importante preservar dados clínicos, então talvez a resolução seja baseada em timestamps ou em um vetor de versões.

3) validação de integridade criptográfica do lote sincronizado: deve verificar que o lote de dados sincronizados tem uma assinatura ou hash que garante integridade, e que qualquer alteração é detectada.

Vou criar um arquivo de teste que define alguns modelos e serviços fictícios, mas com nomes que sugiram a implementação real. Para que os testes sejam executáveis, vou incluir tudo no próprio arquivo, mas com comentários indicando onde estariam os imports reais. No entanto, isso pode ser considerado "código de teste" que não testa nada real. Mas a tarefa é apenas criar o arquivo de teste, então talvez seja aceitável.

Uma alternativa melhor: escrever testes que usam a biblioteca `pytest` e `pytest-asyncio` (se for async), mas não sei se o backend é async. Vou assumir que é síncrono, com SQLAlchemy 2.0.

Vou estruturar o arquivo da seguinte forma:

- Imports: pytest, sqlalchemy, pydantic, datetime, uuid, hashlib, hmac, etc.
- Definição de modelos SQLAlchemy para OutboxItem e Prontuario (apenas para teste, mas com comentário de que são representações).
- Definição de serviços: `SyncService` com métodos `sync_outbox()`, `resolve_conflict()`, `validate_batch_integrity()`.
- Testes para cada requisito.

Mas para não duplicar código, posso usar mocks para simular o banco de dados e os serviços. Por exemplo, criar uma classe `OutboxRepository` mockada, e testar que `SyncService.sync_outbox()` chama os métodos corretos.

Vou fazer assim:

- Criar uma classe `OutboxItem` Pydantic model para representar o item.
- Criar uma classe `SyncService` que aceita um repositório e um validador.
- Nos testes, usar `unittest.mock.MagicMock` para simular o repositório e verificar interações.

Para o conflito de prontuário, posso criar uma função `resolve_prontuario_conflict(local, remote)` que implementa uma política de resolução (ex: baseada em `updated_at`). Testar com diferentes cenários.

Para integridade criptográfica, posso criar uma função `generate_batch_signature(batch)` e `verify_batch_signature(batch, signature)` usando HMAC ou hash. Testar que a assinatura é válida e que alterações invalidam.

Isso torna o arquivo de teste autocontido e executável, mas não testa o código real do projeto. No entanto, como não temos o código real, é o melhor que podemos fazer. Além disso, o usuário pediu "Crie backend/tests/test_sync_offline.py", então estamos criando um arquivo de teste que pode ser adaptado posteriormente.

Vou incluir comentários explicando que os modelos e serviços são simplificados para fins de teste e devem ser substituídos pelos reais.

Preciso garantir que o código seja Python 3.12, use Pydantic v2 e SQLAlchemy 2.0. Vou usar `from pydantic import BaseModel, Field`, `from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text`, `from sqlalchemy.orm import declarative_base, sessionmaker`.

Mas se eu definir modelos SQLAlchemy, preciso de um banco de dados. Posso usar SQLite em memória. Vou criar uma fixture que cria o banco, tabelas, e fornece uma sessão.

Vou planejar os testes:

1. `test_sync_outbox_no_data_loss`: 
   - Cria um banco com alguns itens na outbox.
   - Executa `sync_outbox()`.
   - Verifica que todos os itens foram marcados como `synced=True` e que o número de itens processados é igual ao total.
   - Simula uma falha em um item e verifica que ele não é marcado como sincronizado e permanece na fila.

2. `test_conflict_resolution_prontuario`:
   - Cria dois prontuários com versões diferentes e timestamps.
   - Executa `resolve_conflict()`.
   - Verifica que o resultado é o prontuário com timestamp mais recente (ou outra política).
   - Testa também que campos clínicos são preservados.

3. `test_batch_integrity_validation`:
   - Cria um lote de itens.
   - Gera assinatura.
   - Verifica que a assinatura é válida.
   - Modifica um item e verifica que a assinatura se torna inválida.

Vou implementar as funções de serviço dentro do arquivo de teste, mas com nomes que indiquem que são implementações de referência. Por exemplo:

```python
class SyncService:
    def __init__(self, session):
        self.session = session

    def sync_outbox(self):
        # implementação
```

Mas isso pode ser considerado "testar a implementação de teste", não o código real. No entanto, é comum em exercícios de criação de testes fornecer implementações mínimas para que os testes possam rodar. Vou fazer isso.

Vou também usar `pytest.fixture` para configurar o banco.

Agora, vamos escrever o código.

Primeiro, os imports:

```python
import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import pytest
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
```

Preciso de um modelo OutboxItem. Vou usar SQLAlchemy:

```python
Base = declarative_base()

class OutboxItem(Base):
    __tablename__ = "outbox_items"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_id = Column(String(36), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default="pending")  # pending, synced, failed
```

Para o prontuário, posso usar um modelo Pydantic, já que é mais simples para testar conflito:

```python
class Prontuario(BaseModel):
    id: str
    paciente_cns: str
    updated_at: datetime
    conteudo_clinico: dict
    versao: int = 1
```

Agora, as funções de serviço:

```python
class SyncService:
    def __init__(self, session):
        self.session = session

    def sync_outbox(self) -> int:
        pending_items = self.session.query(OutboxItem).filter(OutboxItem.sync_status == "pending").all()
        synced_count = 0
        for item in pending_items:
            try:
                # Simula envio para servidor
                self._send_to_server(item)
                item.sync_status = "synced"
                item.synced_at = datetime.now(timezone.utc)
                synced_count += 1
            except Exception:
                item.sync_status = "failed"
        self.session.commit()
        return synced_count

    def _send_to_server(self, item):
        # Simulação: se payload contém "error", lança exceção
        if "error" in item.payload:
            raise RuntimeError("Falha no envio")
```

Para resolução de conflito:

```python
def resolve_prontuario_conflict(local: Prontuario, remote: Prontuario) -> Prontuario:
    # Política: última escrita vence (baseado em updated_at)
    if local.updated_at >= remote.updated_at:
        return local
    return remote
```

Para integridade criptográfica:

```python
def generate_batch_signature(batch: List[dict], secret_key: str) -> str:
    serialized = "|".join(
        f"{item['id']}:{item['payload']}:{item['created_at'].isoformat()}" for item in batch
    )
    return hmac.new(secret_key.encode(), serialized.encode(), hashlib.sha256).hexdigest()

def verify_batch_signature(batch: List[dict], signature: str, secret_key: str) -> bool:
    expected = generate_batch_signature(batch, secret_key)
    return hmac.compare_digest(expected, signature)
```

Agora, os testes.

Para o teste de sync outbox, preciso de uma fixture que crie um banco SQLite em memória e uma sessão.

```python
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

Teste 1:

```python
def test_sync_outbox_no_data_loss(db_session):
    # Cria itens na outbox
    items = [
        OutboxItem(id=str(uuid.uuid4()), aggregate_id="agg1", event_type="prontuario.created", payload='{"foo": "bar"}'),
        OutboxItem(id=str(uuid.uuid4()), aggregate_id="agg2", event_type="prontuario.updated", payload='{"baz": "qux"}'),
    ]
    db_session.add_all(items)
    db_session.commit()

    service = SyncService(db_session)
    synced_count = service.sync_outbox()

    assert synced_count == 2
    remaining = db_session.query(OutboxItem).filter(OutboxItem.sync_status == "pending").count()
    assert remaining == 0
    synced = db_session.query(OutboxItem).filter(OutboxItem.sync_status == "synced").all()
    assert len(synced) == 2
    assert all(item.synced_at is not None for item in synced)
```

Teste de falha:

```python
def test_sync_outbox_retry_failed_items(db_session):
    # Um item com payload que causa erro
    item_ok = OutboxItem(id=str(uuid.uuid4()), aggregate_id="agg1", event_type="test", payload='{"ok": true}')
    item_fail = OutboxItem(id=str(uuid.uuid4()), aggregate_id="agg2", event_type="test", payload='{"error": true}')
    db_session.add_all([item_ok, item_fail])
    db_session.commit()

    service = SyncService(db_session)
    synced_count = service.sync_outbox()

    assert synced_count == 1
    failed = db_session.query(OutboxItem).filter(OutboxItem.sync_status == "failed").all()
    assert len(failed) == 1
    assert failed[0].id == item_fail.id
    # O item com falha não é perdido, permanece para retry
```

Teste de conflito:

```python
def test_conflict_resolution_uses_latest_timestamp():
    local = Prontuario(
        id="p1",
        paciente_cns="123456789012345",
        updated_at=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
        conteudo_clinico={"queixa": "dor de cabeça"},
        versao=2,
    )
    remote = Prontuario(
        id="p1",
        paciente_cns="123456789012345",
        updated_at=datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc),
        conteudo_clinico={"queixa": "dor abdominal"},
        versao=3,
    )
    resolved = resolve_prontuario_conflict(local, remote)
    assert resolved == remote
    assert resolved.conteudo_clinico == {"queixa": "dor abdominal"}
```

Também testar empate:

```python
def test_conflict_resolution_tie_prefers_local():
    local = Prontuario(id="p1", paciente_cns="123", updated_at=datetime(2024,1,1,10,0,tzinfo=timezone.utc), conteudo_clinico={"a":1}, versao=1)
    remote = Prontuario(id="p1", paciente_cns="123", updated_at=datetime(2024,1,1,10,0,tzinfo=timezone.utc), conteudo_clinico={"b":2}, versao=1)
    resolved = resolve_prontuario_conflict(local, remote)
    assert resolved == local
```

Teste de integridade:

```python
def test_batch_integrity_signature_valid():
    batch = [
        {"id": "1", "payload": "dados1", "created_at": datetime(2024,1,1,10,0,tzinfo=timezone.utc)},
        {"id": "2", "payload": "dados2", "created_at": datetime(2024,1,1,10,5,tzinfo=timezone.utc)},
    ]
    secret = "chave-secreta"
    signature = generate_batch_signature(batch, secret)
    assert verify_batch_signature(batch, signature, secret) is True

def test_batch_integrity_detects_tampering():
    batch = [
        {"id": "1", "payload": "dados1", "created_at": datetime(2024,1,1,10,0,tzinfo=timezone.utc)},
        {"id": "2", "payload": "dados2", "created_at": datetime(2024,1,1,10,5,tzinfo=timezone.utc)},
    ]
    secret = "chave-secreta"
    signature = generate_batch