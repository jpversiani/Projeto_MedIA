Vamos criar um esquema Pydantic v2 para o módulo de telemedicina e escrever testes abrangentes em pytest para garantir a validação e a transição de status das teleconsultas.

### Esquema Pydantic v2

Primeiro, vamos definir os modelos Pydantic para representar os dados de agendamento e status de teleconsultas.

```python
# Arquivo: backend/app/schemas/telemedicina.py

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class TeleconsultaBase(BaseModel):
    paciente_cpf: str = Field(..., description="CPF do paciente")
    medico_crm: str = Field(..., description="CRM do médico")
    data_hora: datetime = Field(..., description="Data e hora da teleconsulta")
    ciap2: Optional[str] = Field(None, description="Código CIAP-2 para a consulta")
    cid10: Optional[str] = Field(None, description="Código CID-10 para a consulta")

    @validator('paciente_cpf')
    def validate_cpf(cls, v):
        if len(v) != 11 or not v.isdigit():
            raise ValueError("CPF deve conter exatamente 11 dígitos")
        return v

    @validator('medico_crm')
    def validate_crm(cls, v):
        if len(v) != 6 or not v.isdigit():
            raise ValueError("CRM deve conter exatamente 6 dígitos")
        return v

class TeleconsultaCreate(TeleconsultaBase):
    pass

class TeleconsultaStatus(BaseModel):
    status: str = Field(..., description="Status da teleconsulta")

    @validator('status')
    def validate_status(cls, v):
        if v not in ["agendada", "em_andamento", "concluida", "cancelada"]:
            raise ValueError("Status inválido")
        return v

class Teleconsulta(TeleconsultaBase):
    id: int
    status: str

    class Config:
        from_attributes = True
```

### Testes Automatizados com Pytest

Agora, vamos criar testes automatizados para validar a criação de agendamentos e a transição de status das teleconsultas.

```python
# Arquivo: backend/tests/test_telemedicina.py

import pytest
from datetime import datetime
from app.schemas.telemedicina import TeleconsultaCreate, TeleconsultaStatus, Teleconsulta

def test_teleconsulta_create_valid():
    data_hora = datetime.now()
    teleconsulta = TeleconsultaCreate(
        paciente_cpf="12345678901",
        medico_crm="123456",
        data_hora=data_hora,
        ciap2="A01",
        cid10="J00"
    )
    assert teleconsulta.paciente_cpf == "12345678901"
    assert teleconsulta.medico_crm == "123456"
    assert teleconsulta.data_hora == data_hora
    assert teleconsulta.ciap2 == "A01"
    assert teleconsulta.cid10 == "J00"

def test_teleconsulta_create_invalid_cpf():
    with pytest.raises(ValueError) as excinfo:
        TeleconsultaCreate(
            paciente_cpf="123",
            medico_crm="123456",
            data_hora=datetime.now()
        )
    assert "CPF deve conter exatamente 11 dígitos" in str(excinfo.value)

def test_teleconsulta_create_invalid_crm():
    with pytest.raises(ValueError) as excinfo:
        TeleconsultaCreate(
            paciente_cpf="12345678901",
            medico_crm="123",
            data_hora=datetime.now()
        )
    assert "CRM deve conter exatamente 6 dígitos" in str(excinfo.value)

def test_teleconsulta_status_valid():
    status = TeleconsultaStatus(status="agendada")
    assert status.status == "agendada"

def test_teleconsulta_status_invalid():
    with pytest.raises(ValueError) as excinfo:
        TeleconsultaStatus(status="invalid_status")
    assert "Status inválido" in str(excinfo.value)

def test_teleconsulta_model():
    data_hora = datetime.now()
    teleconsulta = Teleconsulta(
        id=1,
        paciente_cpf="12345678901",
        medico_crm="123456",
        data_hora=data_hora,
        status="agendada"
    )
    assert teleconsulta.id == 1
    assert teleconsulta.paciente_cpf == "12345678901"
    assert teleconsulta.medico_crm == "123456"
    assert teleconsulta.data_hora == data_hora
    assert teleconsulta.status == "agendada"
```

### Explicação dos Testes

1. **test_teleconsulta_create_valid**: Testa a criação de uma teleconsulta com dados válidos.
2. **test_teleconsulta_create_invalid_cpf**: Testa a criação de uma teleconsulta com CPF inválido.
3. **test_teleconsulta_create_invalid_crm**: Testa a criação de uma teleconsulta com CRM inválido.
4. **test_teleconsulta_status_valid**: Testa a definição de um status válido para uma teleconsulta.
5. **test_teleconsulta_status_invalid**: Testa a definição de um status inválido para uma teleconsulta.
6. **test_teleconsulta_model**: Testa a criação de um modelo de teleconsulta completo.

### Execução dos Testes

Para executar os testes, você pode usar o seguinte comando no terminal:

```bash
pytest backend/tests/test_telemedicina.py
```

Esses testes garantem que as novas regras de negócio sejam validadas corretamente e que o módulo de telemedicina funcione conforme esperado.