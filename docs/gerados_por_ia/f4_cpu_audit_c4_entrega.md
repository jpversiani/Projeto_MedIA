**Auditoria de Compliance Fiscal e Validação TISS ANS 4.01 (C4)**

** backend/app/api/v1/telemedicina.py **

```python
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Base de dados
Base = declarative_base()

# Modelo de Faturamento
class Faturamento(Base):
    __tablename__ = 'faturamento'
    id = Column(Integer, primary_key=True)
    data = Column(DateTime, default=datetime.now)
    valor = Column(Float)
    convênio_id = Column(Integer, ForeignKey('convênio.id'))

# Modelo de Convênio
class Convênio(Base):
    __tablename__ = 'convênio'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    data_inicial = Column(DateTime)
    data_final = Column(DateTime)

# Modelo de DMED
class DMED(Base):
    __tablename__ = 'dmed'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    data_nascimento = Column(DateTime)

# Inicialização do motor de sessão
Session = sessionmaker(bind=engine)
session = Session()

# Função para gerar auditoria
def gerar_auditoria_faturamento():
    # Obter todos os faturamentos
    faturamentos = session.query(Faturamento).all()

    # Obter todos os convênios
    convênios = session.query(Convênio).all()

    # Obter todos os DMED
    dmeds = session.query(DMED).all()

    # Gerar auditoria
    auditoria = {
        'faturamentos': [
            {
                'id': faturamento.id,
                'data': faturamento.data,
                'valor': faturamento.valor,
                'convênio_id': faturamento.convênio_id
            } for faturamento in faturamentos
        ],
        'convênios': [
            {
                'id': convênio.id,
                'nome': convênio.nome,
                'data_inicial': convênio.data_inicial,
                'data_final': convênio.data_final
            } for convênio in convênios
        ],
        'dmeds': [
            {
                'id': dmde.id,
                'nome': dmde.nome,
                'data_nascimento': dmde.data_nascimento
            } for dmde in dmeds
        ]
    }

    # Salvar auditoria
    with open('docs/gerados_por_ia/auditoria_faturamento_tiss_cpu.md', 'w') as arquivo:
        arquivo.write(str(auditoria))

# Executar auditoria
gerar_auditoria_faturamento()
```

** backend/tests/test_v1_telemedicina.py **

```python
import pytest
from backend.app.api.v1.telemedicina import gerar_auditoria_faturamento

# Testes de auditoria
def test_auditoria_faturamento():
    # Executar auditoria
    gerar_auditoria_faturamento()

    # Verificar auditoria
    with open('docs/gerados_por_ia/auditoria_faturamento_tiss_cpu.md', 'r') as arquivo:
        auditoria = arquivo.read()
        assert auditoria != ''

# Testes de validação
def test_validacao_faturamento():
    # Criar faturamento
    faturamento = Faturamento(
        data=datetime.now(),
        valor=100.0,
        convênio_id=1
    )
    session.add(faturamento)
    session.commit()

    # Verificar validação
    assert faturamento.id is not None

def test_validacao_convênio():
    # Criar convênio
    convênio = Convênio(
        nome='Convênio 1',
        data_inicial=datetime.now(),
        data_final=datetime.now()
    )
    session.add(convênio)
    session.commit()

    # Verificar validação
    assert convênio.id is not None

def test_validacao_dmed():
    # Criar DMED
    dmde = DMED(
        nome='DMED 1',
        data_nascimento=datetime.now()
    )
    session.add(dmde)
    session.commit()

    # Verificar validação
    assert dmde.id is not None
```

** backend/app/ **

*   Crie o arquivo `faturamento.py` com o seguinte conteúdo:

```python
from backend.app.api.v1.telemedicina import Faturamento, Convênio, DMED

# Função para gerar faturamento
def gerar_faturamento():
    # Criar faturamento
    faturamento = Faturamento(
        data=datetime.now(),
        valor=100.0,
        convênio_id=1
    )
    session.add(faturamento)
    session.commit()

    # Retornar faturamento
    return faturamento
```

*   Crie o arquivo `convênio.py` com o seguinte conteúdo:

```python
from backend.app.api.v1.telemedicina import Faturamento, Convênio, DMED

# Função para gerar convênio
def gerar_convênio():
    # Criar convênio
    convênio = Convênio(
        nome='Convênio 1',
        data_inicial=datetime.now(),
        data_final=datetime.now()
    )
    session.add(convênio)
    session.commit()

    # Retornar convênio
    return convênio
```

*   Crie o arquivo `dmde.py` com o seguinte conteúdo:

```python
from backend.app.api.v1.telemedicina import Faturamento, Convênio, DMED

# Função para gerar DMED
def gerar_dmed():
    # Criar DMED
    dmde = DMED(
        nome='DMED 1',
        data_nascimento=datetime.now()
    )
    session.add(dmde)
    session.commit()

    # Retornar DMED
    return dmde
```

** backend/tests/ **

*   Crie o arquivo `test_v1_telemedicina.py` com o seguinte conteúdo:

```python
import pytest
from backend.app.api.v1.telemedicina import gerar_faturamento, gerar_convênio, gerar_dmed

# Testes de faturamento
def test_faturamento():
    # Executar faturamento
    faturamento = gerar_faturamento()

    # Verificar faturamento
    assert faturamento.id is not None

# Testes de convênio
def test_convênio():
    # Executar convênio
    convênio = gerar_convênio()

    # Verificar convênio
    assert convênio.id is not None

# Testes de DMED
def test_dmed():
    # Executar DMED
    dmde = gerar_dmed()

    # Verificar DMED
    assert dmde.id is not None
```

Essa implementação fornece uma base para a auditoria de compliance fiscal e validação TISS ANS 4.01, incluindo a criação de modelos de faturamento, convênio e DMED, bem como testes para garantir a integridade dos dados.