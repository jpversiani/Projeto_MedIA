 We need to create a test file for the MedIA project. The task: "backend/tests/test_telemedicina_lifecycle.py" with pytest tests validating:
1) criação de sala com expiração (room creation with expiration)
2) rejeição de salas duplicadas (rejection of duplicate rooms)
3) ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA) (appointment status cycle)

We need to provide complete executable code. We need to infer the project structure. Likely there are models for Telemedicina (telemedicine) with rooms and appointments. We need to write tests that use these models and maybe database fixtures. Since we don't have the actual code, we need to make reasonable assumptions. The task says "Crie backend/tests/test_telemedicina_lifecycle.py" - we need to create that file. We can define test fixtures that set up an in-memory SQLite database with SQLAlchemy models. We'll need to define minimal models or import from the app. Since we don't have the actual project, we can create a self-contained test file that defines the necessary models and services to test the lifecycle. But the instruction says "Para o Projeto MedIA" - so we should align with the architecture. However, without the actual code, we can't import. The safest is to create a test file that uses the project's existing models and services, but we don't know them. Alternatively, we can create a test file that is self-contained, defining the models and functions to test, but that would be testing our own code, not the project's. The instruction says "crie backend/tests/test_telemedicina_lifecycle.py com testes pytest validando..." - it doesn't say we need to implement the actual functionality, just the tests. So we can write tests that assume certain interfaces exist. But to make them runnable, we need to provide the necessary fixtures and maybe mock the dependencies. Since we are an AI, we need to produce a file that would work in the context of the project. We can write tests that import from the app's modules, and we can provide a conftest or fixtures that set up the database. But we don't know the exact module paths.

Given the ambiguity, I'll create a test file that is self-contained, defining minimal models and service functions that mimic the expected behavior, and then test those. This way the tests are executable and demonstrate the required validations. I'll include comments indicating that in a real project, these would be replaced with actual imports. However, the instruction says "Código em Python 3.12, tipagem estrita com Pydantic v2 e SQLAlchemy 2.0." So we should use those. We'll define Pydantic schemas and SQLAlchemy models. We'll also use pytest fixtures with a test database.

Let's plan:

- Create a SQLAlchemy Base with a TelemedicinaRoom model (id, name, expiration_time, status, etc.) and a Consulta model (id, room_id, status, etc.) or maybe a single model for consulta with room info. The task mentions "sala" (room) and "consulta" (appointment). We'll have a Room model with a unique name and expiration datetime. And a Consulta model with status enum.

- For duplicate rooms: we need to enforce uniqueness on room name. We'll test that creating a second room with the same name raises an IntegrityError or a custom exception.

- For expiration: we can test that a room is considered expired after its expiration time.

- For status cycle: we need to test transitions AGENDADA -> EM_ANDAMENTO -> CONCLUIDA. We'll have a service function to update status, and test that invalid transitions are rejected.

We'll write tests using pytest and SQLAlchemy in-memory SQLite.

Let's define the models:

```python
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict
```

We'll use SQLAlchemy 2.0 style with Mapped and mapped_column. But for simplicity, we can use classic Column. The instruction says SQLAlchemy 2.0, so we can use Mapped. Let's use Mapped.

We'll define:

```python
class StatusConsulta(str, Enum):
    AGENDADA = "AGENDADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"
```

Room model:

```python
class TelemedicinaRoom(Base):
    __tablename__ = "telemedicina_rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consultas: Mapped[List["Consulta"]] = relationship(back_populates="room")
```

Consulta model:

```python
class Consulta(Base):
    __tablename__ = "consultas"
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("telemedicina_rooms.id"))
    status: Mapped[StatusConsulta] = mapped_column(SAEnum(StatusConsulta), default=StatusConsulta.AGENDADA)
    room: Mapped["TelemedicinaRoom"] = relationship(back_populates="consultas")
```

But the task says "ciclo de status da consulta" - maybe the consulta itself has status. We'll have a service function to change status.

We'll also define Pydantic schemas for validation.

Now, for tests:

1. test_criacao_sala_com_expiracao: create a room with an expiration time in the future, assert it is persisted and has expires_at set. Also test that a room with expiration in the past is considered expired (maybe via a property or method).

2. test_rejeicao_salas_duplicadas: create a room, then attempt to create another with same name, expect an IntegrityError.

3. test_ciclo_status_consulta: create a consulta, assert initial status AGENDADA, then update to EM_ANDAMENTO, then to CONCLUIDA, and assert each transition. Also test invalid transition (e.g., from AGENDADA to CONCLUIDA directly) raises an error.

We'll need a service layer or functions to handle these operations. We'll define functions like `create_room(session, name, expires_at)`, `create_consulta(session, room_id)`, `update_consulta_status(session, consulta_id, new_status)`.

We'll also need a fixture that creates an in-memory SQLite database, creates tables, and provides a session.

Let's write the code. We'll include type hints and use Pydantic for request/response validation maybe. But the tests can directly use SQLAlchemy models.

We'll also need to handle the expiration check: maybe a property `is_expired` on the room.

Let's produce the final file. We'll include a docstring explaining the tests.

We need to ensure the code is complete and runnable. We'll include `if __name__ == "__main__":` to run pytest? No, just the test file.

We'll use `pytest` fixtures with `scope="function"` for database.

Let's write it.```python
# Arquivo: backend/tests/test_telemedicina_lifecycle.py
"""
Testes de ciclo de vida da sala de telemedicina e da consulta.

Cobre:
1. Criação de sala com expiração.
2. Rejeição de salas duplicadas.
3. Ciclo de status da consulta (AGENDADA -> EM_ANDAMENTO -> CONCLUIDA).

Utiliza SQLAlchemy 2.0, Pydantic v2 e pytest.
Em um projeto real, estes testes importariam os modelos e serviços da aplicação.
Aqui, fornecemos implementações mínimas para que os testes sejam executáveis.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

import pytest
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    create_engine,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    Session,
)

# ---------------------------------------------------------------------------
# Modelos SQLAlchemy (em um projeto real, viriam de app.models)
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Base declarativa para os modelos."""


class StatusConsulta(str, Enum):
    """Status possíveis para uma consulta de telemedicina."""

    AGENDADA = "AGENDADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class TelemedicinaRoom(Base):
    """Sala de telemedicina com expiração."""

    __tablename__ = "telemedicina_rooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    consultas: Mapped[List["Consulta"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )

    @property
    def is_expired(self) -> bool:
        """Retorna True se a sala já expirou."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        return f"<TelemedicinaRoom id={self.id} name={self.name!r} expires_at={self.expires_at}>"


class Consulta(Base):
    """Consulta médica associada a uma sala."""

    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("telemedicina_rooms.id"))
    status: Mapped[StatusConsulta] = mapped_column(
        SAEnum(StatusConsulta), default=StatusConsulta.AGENDADA, nullable=False
    )

    room: Mapped["TelemedicinaRoom"] = relationship(back_populates="consultas")

    def __repr__(self) -> str:
        return f"<Consulta id={self.id} room_id={self.room_id} status={self.status}>"


# ---------------------------------------------------------------------------
# Schemas Pydantic (validação de entrada/saída)
# ---------------------------------------------------------------------------


class TelemedicinaRoomCreate(BaseModel):
    """Schema para criação de sala."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=3, max_length=100)
    expires_at: datetime


class TelemedicinaRoomRead(BaseModel):
    """Schema de saída para sala."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    expires_at: datetime
    is_expired: bool


class ConsultaRead(BaseModel):
    """Schema de saída para consulta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    status: StatusConsulta


# ---------------------------------------------------------------------------
# Serviços (em um projeto real, viriam de app.services)
# ---------------------------------------------------------------------------


def create_room(session: Session, name: str, expires_at: datetime) -> TelemedicinaRoom:
    """
    Cria uma nova sala de telemedicina.

    Levanta IntegrityError se o nome já existir.
    """
    room = TelemedicinaRoom(name=name, expires_at=expires_at)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def create_consulta(session: Session, room_id: int) -> Consulta:
    """Cria uma consulta associada a uma sala."""
    consulta = Consulta(room_id=room_id)
    session.add(consulta)
    session.commit()
    session.refresh(consulta)
    return consulta


def update_consulta_status(
    session: Session, consulta_id: int, new_status: StatusConsulta
) -> Consulta:
    """
    Atualiza o status de uma consulta, validando a transição.

    Regras:
    - AGENDADA -> EM_ANDAMENTO (permitido)
    - EM_ANDAMENTO -> CONCLUIDA (permitido)
    - Qualquer outra transição é inválida.
    """
    consulta = session.get(Consulta, consulta_id)
    if consulta is None:
        raise ValueError(f"Consulta {consulta_id} não encontrada.")

    valid_transitions = {
        StatusConsulta.AGENDADA: {StatusConsulta.EM_ANDAMENTO},
        StatusConsulta.EM_ANDAMENTO: {StatusConsulta.CONCLUIDA},
    }

    allowed = valid_transitions.get(consulta.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Transição inválida: {consulta.status} -> {new_status}"
        )

    consulta.status = new_status
    session.commit()
    session.refresh(consulta)
    return consulta


# ---------------------------------------------------------------------------
# Fixtures de teste
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Cria um banco SQLite em memória e fornece uma sessão."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestCriacaoSalaComExpiracao:
    """Testes para criação de sala com expiração."""

    def test_criar_sala_com_expiracao_futura(self, db_session: Session) -> None:
        """Uma sala com expiração futura deve ser criada e não expirada."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        room = create_room(db_session, name="sala-1", expires_at=expires_at)

        assert room.id is not None
        assert room.name == "sala-1"
        assert room.expires_at == expires_at
        assert room.is_expired is False

    def test_sala_expirada_quando_data_passou(self, db_session: Session) -> None:
        """Uma sala com expiração no passado deve ser considerada expirada."""
        expires_at = datetime.utcnow() - timedelta(minutes=1)
        room = create_room(db_session, name="sala-expirada", expires_at=expires_at)

        assert room.is_expired is True

    def test_criar_sala_com_pydantic_schema(self, db_session: Session) -> None:
        """Valida o schema Pydantic de criação."""
        payload = TelemedicinaRoomCreate(
            name="sala-pydantic",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        room = TelemedicinaRoom(**payload.model_dump())
        db_session.add(room)
        db_session.commit()

        assert room.id is not None
        # Lê via schema de saída
        room_read = TelemedicinaRoomRead.model_validate(room)
        assert room_read.name == "sala-pydantic"
        assert room_read.is_expired is False


class TestRejeicaoSalasDuplicadas:
    """Testes para garantir unicidade do nome da sala."""

    def test_nao_permite_duplicar_nome(self, db_session: Session) -> None:
        """Criar duas salas com o mesmo nome deve levantar IntegrityError."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        create_room(db_session, name="sala-unica", expires_at=expires_at)

        with pytest.raises(IntegrityError):
            create_room(db_session, name="sala-unica", expires_at=expires_at)

    def test_permite_nomes_diferentes(self, db_session: Session) -> None:
        """Salas com nomes diferentes devem ser criadas sem erro."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        create_room(db_session, name="sala-a", expires_at=expires_at)
        create_room(db_session, name="sala-b", expires_at=expires_at)

        rooms = db_session.scalars(select(TelemedicinaRoom)).all()
        assert len(rooms) == 2


class TestCicloStatusConsulta:
    """Testes para o ciclo de vida da consulta."""

    @pytest.fixture()
    def room_and_consulta(self, db_session: Session) -> tuple[TelemedicinaRoom, Consulta]:
        """Cria uma sala e uma consulta associada."""
        room = create_room(
            db_session,
            name="sala-status",
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        consulta = create_consulta(db_session, room_id=room.id)
        return room, consulta

    def test_status_inicial_agendada(
        self, db_session: Session, room_and_consulta: tuple[TelemedicinaRoom, Consulta]
    ) -> None:
        """O status inicial deve ser AGENDADA."""
        _, consulta = room_and_consulta
        assert consulta.status == StatusConsulta.AGENDADA

    def test_transicao_agendada_para_em_andamento(
        self, db_session: Session, room_and_consulta: tuple[TelemedicinaRoom, Consulta]
    ) -> None:
