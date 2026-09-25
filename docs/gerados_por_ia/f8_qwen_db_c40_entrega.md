Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a "Health Campaigns Repository and Send History" (C40) for the "MedIA" project.
   - **Requirements:**
     - Track sent messages, confirmation status by patient, and data protection audit log.
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, identification by CNS/CPF.
     - Full compliance and automated test coverage with pytest.
     - Provide complete, executable code. Specify file paths in code blocks.
   - **Output:** Code for the repository file and corresponding tests.

2.  **Deconstruct Requirements & Architecture:**
   - **Domain:** Health campaigns (Campanhas de Saúde), message sending history, patient confirmation, audit logs.
   - **Standards:** CIAP-2 (Classificação Internacional de Atenção Primária), CID-10 (ICD-10), SOAP (Subjective, Objective, Assessment, Plan), CNS (Cartão Nacional de Saúde), CPF (Cadastro de Pessoas Físicas).
   - **Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2.0 (async/sync? I'll assume async for modern FastAPI/SQLAlchemy 2.0 patterns, but I'll make it compatible. I'll use `sqlalchemy.orm` and `sqlalchemy.ext.asyncio` if needed, but for simplicity and broad compatibility, I'll stick to SQLAlchemy 2.0 synchronous ORM with async session support in mind, or just use standard SQLAlchemy 2.0 with type hints. I'll explicitly use `sqlalchemy` 2.0 syntax).
   - **Repository Pattern:** Needs models, repository class with methods for CRUD and specific tracking/audit operations.
   - **Testing:** Pytest with full coverage. Need to mock DB or use in-memory SQLite.

3.  **Design Models (Pydantic + SQLAlchemy):**
   - `Campaign` (Campanha): id, name, description, status, created_at, updated_at
   - `CampaignMessage` (Mensagem da Campanha): id, campaign_id, patient_cns, patient_cpf, message_content, status (sent, delivered, confirmed, failed), sent_at, confirmed_at, ciap2_codes, cid10_codes, soap_notes
   - `AuditLog` (Log de Auditoria): id, campaign_id, message_id, action, details, performed_by, timestamp, ip_address, compliance_status
   - I'll define SQLAlchemy ORM models and Pydantic schemas for validation.

   Let's draft the SQLAlchemy models:
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
   from sqlalchemy.orm import DeclarativeBase, relationship
   from sqlalchemy.sql import func
   import enum

   class Base(DeclarativeBase):
       pass

   class MessageStatus(str, enum.Enum):
       PENDING = "pending"
       SENT = "sent"
       DELIVERED = "delivered"
       CONFIRMED = "confirmed"
       FAILED = "failed"

   class AuditAction(str, enum.Enum):
       SEND = "send"
       CONFIRM = "confirm"
       REVOKE_CONSENT = "revoke_consent"
       EXPORT = "export"
       AUDIT_CHECK = "audit_check"

   class Campaign(Base):
       __tablename__ = "campaigns"
       id = Column(Integer, primary_key=True)
       name = Column(String(255), nullable=False)
       description = Column(Text, nullable=True)
       status = Column(String(50), default="draft")
       created_at = Column(DateTime, server_default=func.now())
       updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
       messages = relationship("CampaignMessage", back_populates="campaign")

   class CampaignMessage(Base):
       __tablename__ = "campaign_messages"
       id = Column(Integer, primary_key=True)
       campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
       patient_cns = Column(String(15), nullable=False) # CNS format
       patient_cpf = Column(String(14), nullable=False) # CPF format
       message_content = Column(Text, nullable=False)
       status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
       sent_at = Column(DateTime, nullable=True)
       confirmed_at = Column(DateTime, nullable=True)
       ciap2_codes = Column(Text, nullable=True) # JSON string or comma-separated
       cid10_codes = Column(Text, nullable=True)
       soap_notes = Column(Text, nullable=True)
       campaign = relationship("Campaign", back_populates="messages")
       audit_logs = relationship("AuditLog", back_populates="message")

   class AuditLog(Base):
       __tablename__ = "audit_logs"
       id = Column(Integer, primary_key=True)
       campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
       message_id = Column(Integer, ForeignKey("campaign_messages.id"), nullable=True)
       action = Column(Enum(AuditAction), nullable=False)
       details = Column(Text, nullable=True)
       performed_by = Column(String(100), nullable=False)
       timestamp = Column(DateTime, server_default=func.now())
       ip_address = Column(String(45), nullable=True)
       compliance_status = Column(String(50), default="compliant")
       campaign = relationship("Campaign", back_populates="audit_logs")
       message = relationship("CampaignMessage", back_populates="audit_logs")
   ```

   Wait, SQLAlchemy 2.0 prefers `Mapped` and `mapped_column`. I'll use modern SQLAlchemy 2.0 syntax:
   ```python
   from sqlalchemy.orm import Mapped, mapped_column, relationship
   from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum as SAEnum
   from sqlalchemy.sql import func
   import enum

   class Base(DeclarativeBase):
       pass

   class MessageStatus(str, enum.Enum):
       PENDING = "pending"
       SENT = "sent"
       DELIVERED = "delivered"
       CONFIRMED = "confirmed"
       FAILED = "failed"

   class AuditAction(str, enum.Enum):
       SEND = "send"
       CONFIRM = "confirm"
       REVOKE_CONSENT = "revoke_consent"
       EXPORT = "export"
       AUDIT_CHECK = "audit_check"

   class Campaign(Base):
       __tablename__ = "campaigns"
       id: Mapped[int] = mapped_column(primary_key=True)
       name: Mapped[str] = mapped_column(String(255))
       description: Mapped[str | None] = mapped_column(Text)
       status: Mapped[str] = mapped_column(String(50), default="draft")
       created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
       messages: Mapped[list["CampaignMessage"]] = relationship(back_populates="campaign")
       audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="campaign")

   class CampaignMessage(Base):
       __tablename__ = "campaign_messages"
       id: Mapped[int] = mapped_column(primary_key=True)
       campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
       patient_cns: Mapped[str] = mapped_column(String(15))
       patient_cpf: Mapped[str] = mapped_column(String(14))
       message_content: Mapped[str] = mapped_column(Text)
       status: Mapped[MessageStatus] = mapped_column(SAEnum(MessageStatus), default=MessageStatus.PENDING)
       sent_at: Mapped[datetime | None] = mapped_column(DateTime)
       confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
       ciap2_codes: Mapped[str | None] = mapped_column(Text)
       cid10_codes: Mapped[str | None] = mapped_column(Text)
       soap_notes: Mapped[str | None] = mapped_column(Text)
       campaign: Mapped["Campaign"] = relationship(back_populates="messages")
       audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="message")

   class AuditLog(Base):
       __tablename__ = "audit_logs"
       id: Mapped[int] = mapped_column(primary_key=True)
       campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
       message_id: Mapped[int | None] = mapped_column(ForeignKey("campaign_messages.id"))
       action: Mapped[AuditAction] = mapped_column(SAEnum(AuditAction))
       details: Mapped[str | None] = mapped_column(Text)
       performed_by: Mapped[str] = mapped_column(String(100))
       timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
       ip_address: Mapped[str | None] = mapped_column(String(45))
       compliance_status: Mapped[str] = mapped_column(String(50), default="compliant")
       campaign: Mapped["Campaign"] = relationship(back_populates="audit_logs")
       message: Mapped["CampaignMessage"] = relationship(back_populates="audit_logs")
   ```
   Need to import `datetime` and handle forward references properly. I'll use `from __future__ import annotations` or string annotations.

4.  **Design Pydantic Schemas (v2):**
   - Need schemas for validation and API interaction.
   - `CampaignCreate`, `CampaignRead`
   - `MessageCreate`, `MessageRead`, `MessageUpdate`
   - `AuditLogRead`
   - Use `ConfigDict` from pydantic.

   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from datetime import datetime
   from typing import Optional, List
   import re

   class CampaignCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=255)
       description: Optional[str] = None
       model_config = ConfigDict(str_strip_whitespace=True)

   class CampaignRead(BaseModel):
       id: int
       name: str
       description: Optional[str]
       status: str
       created_at: datetime
       updated_at: datetime
       model_config = ConfigDict(from_attributes=True)

   class MessageCreate(BaseModel):
       campaign_id: int
       patient_cns: str = Field(..., pattern=r"^\d{15}$")
       patient_cpf: str = Field(..., pattern=r"^\d{11}$")
       message_content: str = Field(..., min_length=1)
       ciap2_codes: Optional[List[str]] = None
       cid10_codes: Optional[List[str]] = None
       soap_notes: Optional[str] = None

       @field_validator("ciap2_codes")
       @classmethod
       def validate_ciap2(cls, v):
           if v:
               for code in v:
                   if not re.match(r"^[A-Z]\d{2}$", code):
                       raise ValueError("CIAP-2 code must match pattern: Letter + 2 digits (e.g., A01)")
           return v

       @field_validator("cid10_codes")
       @classmethod
       def validate_cid10(cls, v):
           if v:
               for code in v:
                   if not re.match(r"^[A-Z]\d{2}(\.\d{1,4})?$", code):
                       raise ValueError("CID-10 code must match pattern (e.g., A00.0)")
           return v

   class MessageRead(BaseModel):
       id: int
       campaign_id: int
       patient_cns: str
       patient_cpf: str
       message_content: str
       status: str
       sent_at: Optional[datetime]
       confirmed_at: Optional[datetime]
       ciap2_codes: Optional[List[str]]
       cid10_codes: Optional[List[str]]
       soap_notes: Optional[str]
       model_config = ConfigDict(from_attributes=True)

   class AuditLogRead(BaseModel):
       id: int
       campaign_id: int
       message_id: Optional[int]
       action: str
       details: Optional[str]
       performed_by: str
       timestamp: datetime
       ip_address: Optional[str]
       compliance_status: str
       model_config = ConfigDict(from_attributes=True)
   ```

5.  **Design Repository Class:**
   - Needs methods for:
     - `create_campaign`
     - `get_campaign`
     - `send_message` (updates status, logs audit)
     - `confirm_message` (patient confirmation)
     - `get_campaign_history`
     - `get_audit_logs`
     - `check_compliance` (audit check)
   - Use SQLAlchemy 2.0 async/sync? I'll write it with `AsyncSession` as it's standard for modern FastAPI, but I'll make it clear. Actually, I'll use synchronous `Session` for simplicity in testing, but add type hints for `AsyncSession` if needed. I'll stick to `Session` from `sqlalchemy.orm` for broader compatibility, but note it's SQLAlchemy 2.0 style.
   - I'll implement it with `AsyncSession` as it's more modern, but I'll make sure it's testable. Actually, for pytest, synchronous is easier. I'll use `Session` but type it as `Session`. I'll add `async` support comments if needed, but keep it simple.
   - Wait, the prompt says "SQLAlchemy 2.0". I'll use `Session` from `sqlalchemy.orm`.
   - I'll structure the repository to accept a `Session` in `__init__` or as a method parameter. I'll use dependency injection style: `def __init__(self, session: Session): ...`

   Repository methods:
   - `create_campaign(campaign: CampaignCreate) -> Campaign`
   - `get_campaign(campaign_id: int) -> Campaign | None`
   - `send_message(msg: MessageCreate, performed_by: str, ip: str | None) -> CampaignMessage`
   - `confirm_message(message_id: int, performed_by: str, ip: str | None) -> CampaignMessage`
   - `get_campaign_history(campaign_id: int) -> list[CampaignMessage]`
   - `get_audit_logs(campaign_id: int, message_id: int | None = None) -> list[AuditLog]`
   - `check_compliance(campaign_id: int) -> dict` (returns audit summary)

   I'll implement these with SQLAlchemy 2.0 `select`, `insert`, `update`, `delete`.

   Let's draft the repository code carefully.

   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import select, update, insert
   from datetime import datetime
   from typing import Optional, List, Dict, Any
   import enum

   # ... (imports for models and schemas) ...

   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       async def create_campaign(self, data: CampaignCreate) -> Campaign:
           # synchronous in this example, but can be adapted
           campaign = Campaign(
               name=data.name,
               description=data.description,
               status="draft"
           )
           self.session.add(campaign)
           self.session.flush()
           return campaign

       # ... other methods ...
   ```

   Actually, I'll make it fully synchronous for simplicity, but I'll add `async def` if needed. The prompt doesn't specify async, so I'll stick to sync SQLAlchemy 2.0 for clarity and testability. I'll note that it's compatible with both.

   Let's refine the repository with proper SQLAlchemy 2.0 syntax:
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import select, update, insert, func
   from datetime import datetime
   from typing import Optional, List, Dict, Any
   import json

   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       def create_campaign(self, data: CampaignCreate) -> Campaign:
           campaign = Campaign(
               name=data.name,
               description=data.description,
               status="draft"
           )
           self.session.add(campaign)
           self.session.flush()
           self.session.refresh(campaign)
           return campaign

       def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
           stmt = select(Campaign).where(Campaign.id == campaign_id)
           return self.session.execute(stmt).scalar_one_or_none()

       def send_message(self, data: MessageCreate, performed_by: str, ip_address: Optional[str] = None) -> CampaignMessage:
           # Validate CNS/CPF format again (already in pydantic, but good to be safe)
           # Create message
           msg = CampaignMessage(
               campaign_id=data.campaign_id,
               patient_cns=data.patient_cns,
               patient_cpf=data.patient_cpf,
               message_content=data.message_content,
               status=MessageStatus.SENT,
               sent_at=datetime.utcnow(),
               ciap2_codes=json.dumps(data.ciap2_codes) if data.ciap2_codes else None,
               cid10_codes=json.dumps(data.cid10_codes) if data.cid10_codes else None,
               soap_notes=data.soap_notes
           )
           self.session.add(msg)
           self.session.flush()

           # Audit log
           audit = AuditLog(
               campaign_id=data.campaign_id,
               message_id=msg.id,
               action=AuditAction.SEND,
               details=f"Message sent to CNS {data.patient_cns}",
               performed_by=performed_by,
               ip_address=ip_address,
               compliance_status="compliant"
           )
           self.session.add(audit)
           self.session.commit()
           self.session.refresh(msg)
           return msg

       def confirm_message(self, message_id: int, performed_by: str, ip_address: Optional[str] = None) -> CampaignMessage:
           stmt = select(CampaignMessage).where(CampaignMessage.id == message_id