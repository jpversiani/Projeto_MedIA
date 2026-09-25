# Dashboard Executivo Interativo - Projeto MedIA

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── analytics.py
│   ├── static/
│   │   └── dashboard_analytics.html
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_schemas.py
│   ├── test_api.py
│   └── test_dashboard.py
├── requirements.txt
└── pytest.ini
```

---

## Arquivo: `backend/app/__init__.py`

```python
# Arquivo: backend/app/__init__.py
"""
Projeto MedIA - Sistema de Gerenciamento de Clínicas
Padrões SUS/APS: CIAP-2, CID-10, Método SOAP, Identificação CNS/CPF
"""

from .models import db
from .schemas import BaseSchema
from .api.analytics import analytics_bp

__all__ = ["db", "BaseSchema", "analytics_bp"]
```

---

## Arquivo: `backend/app/models.py`

```python
# Arquivo: backend/app/models.py
"""
Modelos SQLAlchemy 2.0 para o Projeto MedIA
Padrões: SUS/APS, CIAP-2, CID-10, Método SOAP, Identificação CNS/CPF
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    check,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)
from sqlalchemy.sql import func

# ============================================================
# Base Model
# ============================================================

class Base(DeclarativeBase):
    """Base declarativa com padrão de identificador único."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ============================================================
    # Identificação SUS/APS - CNS/CPF
    # ============================================================

    def _validate_cns(self, value: str) -> None:
        """Validação de CNS (Cadastro Nacional de Segurança) - 11 dígitos."""
        if not value or len(value) != 11:
            raise ValueError("CNS deve ter exatamente 11 dígitos")
        if not value.isdigit():
            raise ValueError("CNS deve conter apenas dígitos")

    def _validate_cpf(self, value: str) -> None:
        """Validação de CPF - 14 dígitos com verificação matemática."""
        if not value or len(value) != 14:
            raise ValueError("CPF deve ter exatamente 14 dígitos")
        if not value.replace("-", "").replace(".", "").isdigit():
            raise ValueError("CPF deve conter apenas dígitos")

        # Verificação matemática do CPF
        digits = [int(d) for d in value.replace("-", "").replace(".", "")]
        if digits[0] == digits[1] == digits[2]:
            raise ValueError("CPF inválido: dígitos iniciais iguais")

        total = sum(digits[i] * (10 - i) for i in range(9))
        remainder = total % 11
        if remainder < 2:
            check_digit1 = 0
        else:
            check_digit1 = 11 - (remainder // 10)

        total2 = sum(digits[i] * (11 - i) for i in range(10))
        remainder2 = total2 % 11
        if remainder2 < 2:
            check_digit2 = 0
        else:
            check_digit2 = 11 - (remainder2 // 10)

        if digits[9] != check_digit1 or digits[10] != check_digit2:
            raise ValueError("CPF inválido: verificação matemática falhou")

    # ============================================================
    # Modelo Paciente
    # ============================================================

    class Patient(Base):
        """
        Modelo Paciente com identificação CNS/CPF.
        Padrão SUS/APS: Identificação única por CNS/CPF.
        """

        __tablename__ = "pacientes"

        # Identificação SUS/APS
        cns: Mapped[str] = mapped_column(
            String(11), unique=True, nullable=False, index=True
        )
        cpf: Mapped[Optional[str]] = mapped_column(
            String(14), nullable=True
        )
        nome: Mapped[str] = mapped_column(String(100), nullable=False)
        sobrenome: Mapped[str] = mapped_column(String(100), nullable=False)
        data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
        gender: Mapped[str] = mapped_column(
            Enum("M", "F", "O", name="gender_enum", create_type=False),
            nullable=False,
            default="M",
        )
        address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
        phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
        email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
        status: Mapped[str] = mapped_column(
            Enum("ativo", "inativo", "desativado", name="status_enum", create_type=False),
            nullable=False,
            default="ativo",
        )
        registration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

        # Relações
        appointments: Mapped[list["Appointment"]] = relationship(
            back_populates="paciente"
        )

        def __init__(
            self,
            cns: str,
            cpf: Optional[str] = None,
            nome: str = "",
            sobrenome: str = "",
            data_nascimento: Optional[date] = None,
            gender: str = "M",
            address: Optional[str] = None,
            phone: Optional[str] = None,
            email: Optional[str] = None,
            status: str = "ativo",
            registration_date: Optional[date] = None,
        ) -> None:
            self.cns = cns
            self.cpf = cpf
            self.nome = nome
            self.sobrenome = sobrenome
            self.data_nascimento = data_nascimento or date.today()
            self.gender = gender
            self.address = address
            self.phone = phone
            self.email = email
            self.status = status
            self.registration_date = registration_date

        @validates("cns")
        def validate_cns(self, key: str, value: str) -> str:
            self._validate_cns(value)
            return value

        @validates("cpf")
        def validate_cpf(self, key: str, value: Optional[str]) -> Optional[str]:
            if value:
                self._validate_cpf(value)
            return value

        def full_name(self) -> str:
            return f"{self.nome} {self.sobrenome}".strip()

        def __repr__(self) -> str:
            return f"<Patient cns={self.cns} nome={self.full_name()}>"

    # ============================================================
    # Modelo Citação
    # ============================================================

    class Citaacao(Base):
        """
        Modelo Citação com método SOAP.
        Padrão SUS/APS: Registro de citação com SOAP.
        """

        __tablename__ = "citacoes"

        # Identificação SUS/APS
        cns: Mapped[str] = mapped_column(
            String(11), nullable=False, index=True
        )
        cpf: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)
        data_citaacao: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
        hora_citaacao: Mapped[Optional[datetime]] = mapped_column(
            DateTime(timezone=True), nullable=True
        )
        status: Mapped[str] = mapped_column(
            Enum(
                "agendada",
                "em_progr",
                "realizada",
                "cancelada",
                "adiado",
                name="citaacao_status_enum",
                create_type=False,
            ),
            nullable=False,
            default="agendada",
        )
        motivo_citaacao: Mapped[Optional[str]] = mapped_column(
            String(100), nullable=True
        )
        nota_sop: Mapped[Optional[str]] = mapped_column(
            Text, nullable=True
        )
        nota_sop_resumo: Mapped[Optional[str]] = mapped_column(
            String(500), nullable=True
        )
        hora_sop: Mapped[Optional[datetime]] = mapped_column(
            DateTime(timezone=True), nullable=True
        )
        hora_sop_resumo: Mapped[Optional[datetime]] = mapped_column(
            DateTime(timezone=True), nullable=True
        )
        hora_sop_final: Mapped[Optional[datetime]] = mapped_column(
            DateTime(timezone=True), nullable=True
        )
        duration_minutes: Mapped[Optional[int]] = mapped_column(
            Integer, nullable=True
        )
        valor: Mapped[Optional[Decimal]] = mapped_column(
            Decimal(10, 2), nullable=True
        )
        tipo_sobrenome: Mapped[str] = mapped_column(
            Enum(
                "M",
                "F",
                "O",
                name="sobrenome_enum",
                create_type=False,
            ),
            nullable=False,
            default="M",
        )
        data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
        address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
        phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
        email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
        status: Mapped[str] = mapped_column(
            Enum(
                "ativo",
                "inativo",
                "desativado",
                name="status_enum",
                create_type=False,
            ),
            nullable=False,
            default="ativo",
        )
        registration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

        # Relações
        paciente: Mapped["Patient"] = relationship(
            back_populates="citacoes"
        )
        procedimentos: Mapped[list["Procedimento"]] = relationship(
            back_populates="citaacao"
        )

        def __init__(
            self,
            cns: str,
            cpf: Optional[str] = None,
            data_citaacao: Optional[datetime] = None,
            hora_citaacao: Optional[datetime] = None,
            status: str = "agendada",
            motivo_citaacao: Optional[str] = None,
            nota_sop: Optional[str] = None,
            nota_sop_resumo: Optional[str] = None,
            hora_sop: Optional[datetime] = None,
            hora_sop_resumo: Optional[datetime] = None,
            hora_sop_final: Optional[datetime] = None,
            duration_minutes: Optional[int] = None,
            valor: Optional[Decimal] = None,
            tipo_sobrenome: str = "M",
            data_nascimento: Optional[date] = None,
            address: Optional[str] = None,
            phone: Optional[str] = None,
            email: Optional[str] = None,
            status: str = "ativo",
            registration_date: Optional[date] = None,
        ) -> None:
            self.cns = cns
            self.cpf = cpf
            self.data_citaacao = data_citaacao or datetime.now()
            self.hora_citaacao = hora_citaacao
            self.status = status
            self.moto_citaacao = motivo_citaacao
            self.nota_sop = nota_sop
            self.nota_sop_resumo = nota_sop_resumo
            self.hora_sop = hora_sop
            self.hora_sop_resumo = hora_sop_resumo
            self.hora_sop_final = hora_sop_final
            self.duration_minutes = duration_minutes
            self.valor = valor
            self.tipo_sobrenome = tipo_sobrenome
            self.data_nascimento = data_nascimento or date.today()
            self.address = address
            self.phone = phone
            self.email = email
            self.status = status
            self.registration_date = registration_date

        @validates("cns")
        def validate_cns(self, key: str, value: str) -> str:
            self._validate_cns(value)
            return value

        @validates("cpf")
        def validate_cpf(self, key: str, value: Optional[str]) -> Optional[str]:
            if value:
                self._validate_cpf(value)
            return value

        def duration(self) -> int:
            if self.hora_sop and self.hora_sop_final:
                delta = self.hora_sop_final - self.hora_sop
                return int(delta.total_seconds() / 60)
            return self.duration_minutes or 0

        def __repr__(self) -> str:
            return f"<Citaacao cns={self.cns} status={self.status}>"

    # ============================================================
    # Modelo Procedimento (CIAP-2)
    # ============================================================

    class Procedimento(Base):
        """
        Modelo Procedimento com classificação CIAP-2.
        Padrão SUS/APS: Classificação por CIAP-2.
        """

        __tablename__ = "procedimentos"

        # Identificação CIAP-2
        ciap2_code: Mapped[str] = mapped_column(
            String(10), nullable=False, index=True
        )
        ciap2_description: Mapped[str] = mapped_column(
            String(255), nullable=False
        )
        ciap2_category: Mapped[str] = mapped_column(
            String(50), nullable=False
        )
        ciap2_subcategory: Mapped[str] = mapped_column(
            String(50), nullable=True
        )
        ciap2_level: Mapped[str] = mapped_column(
            String(20), nullable=True
        )
        ciap2_level_description: MMapped[str] = mapped_column(
            String(100), nullable=True
        )
        ciap2_level_code: Mapped[Optional[str]] = mapped_column(
            String(10), nullable=True
        )
        ciap2_level_description