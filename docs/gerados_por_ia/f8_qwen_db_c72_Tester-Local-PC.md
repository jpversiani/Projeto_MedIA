Here's a thinking process:

1.  **Understand User Request:**
   - **Role:** Software Engineer (Tester)
   - **Task:** Create `backend/app/repositories/campanhas_repo.py` for a project called "MedIA".
   - **Features:** Campaign repository for health campaigns and sending history. Track sent messages, patient confirmation status, and data protection audit logs.
   - **Architecture Guidelines:**
     - Python 3.12, strict typing with Pydantic v2 and SQLAlchemy 2.0.
     - SUS/APS standards: CIAP-2, CID-10, SOAP method, CNS/CPF identification.
     - Full compliance and automated test coverage with pytest.
   - **Output Requirement:** Provide complete, executable code. Specify file paths in code blocks.

2.  **Deconstruct Requirements:**
   - **File:** `backend/app/repositories/campanhas_repo.py`
   - **Models (Pydantic v2):** Need schemas for campaigns, message history, confirmation status, audit logs.
   - **Database Models (SQLAlchemy 2.0):** Need ORM models corresponding to the Pydantic schemas.
   - **Repository Methods:** CRUD for campaigns, track messages, update confirmation status, log audit events.
   - **Standards Integration:** CIAP-2, CID-10, SOAP, CNS/CPF fields in models.
   - **Testing:** Provide pytest tests covering all repository methods and models.
   - **Compliance:** Data protection (LGPD/GDPR) audit logs, strict typing, Pydantic v2, SQLAlchemy 2.0.

3.  **Design Database Models (SQLAlchemy 2.0):**
   - `Campaign`: id, name, description, start_date, end_date, status, created_at, updated_at
   - `CampaignMessage`: id, campaign_id, recipient_cpf, recipient_cns, message_content, status (sent, delivered, confirmed, failed), sent_at, confirmed_at, cid10_code, ciap2_code, soap_notes
   - `AuditLog`: id, campaign_id, message_id, action, details, performed_by, timestamp, ip_address, user_agent
   - Relationships: Campaign -> CampaignMessage, CampaignMessage -> AuditLog (or just campaign_id/message_id)

   Let's define them with SQLAlchemy 2.0 syntax:
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
   from datetime import datetime
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
       MESSAGE_SENT = "message_sent"
       MESSAGE_CONFIRMED = "message_confirmed"
       MESSAGE_FAILED = "message_failed"
       DATA_ACCESS = "data_access"
       DATA_MODIFIED = "data_modified"
       DATA_DELETED = "data_deleted"

   class Campaign(Base):
       __tablename__ = "campaigns"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       name: Mapped[str] = mapped_column(String(100), nullable=False)
       description: Mapped[str | None] = mapped_column(Text)
       start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
       status: Mapped[str] = mapped_column(String(20), default="draft")
       created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       messages: Mapped[list["CampaignMessage"]] = relationship(back_populates="campaign")

   class CampaignMessage(Base):
       __tablename__ = "campaign_messages"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       campaign_id: Mapped[int] = mapped_column(Integer, ForeignKey("campaigns.id"))
       recipient_cpf: Mapped[str] = mapped_column(String(14), nullable=False)
       recipient_cns: Mapped[str | None] = mapped_column(String(15))
       message_content: Mapped[str] = mapped_column(Text, nullable=False)
       status: Mapped[str] = mapped_column(String(20), default="pending")
       sent_at: Mapped[datetime | None] = mapped_column(DateTime)
       confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
       cid10_code: Mapped[str | None] = mapped_column(String(10))
       ciap2_code: Mapped[str | None] = mapped_column(String(10))
       soap_notes: Mapped[str | None] = mapped_column(Text)
       campaign: Mapped["Campaign"] = relationship(back_populates="messages")
       audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="message")

   class AuditLog(Base):
       __tablename__ = "audit_logs"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       campaign_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("campaigns.id"))
       message_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("campaign_messages.id"))
       action: Mapped[str] = mapped_column(String(50), nullable=False)
       details: Mapped[str | None] = mapped_column(Text)
       performed_by: Mapped[str] = mapped_column(String(100), nullable=False)
       timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       ip_address: Mapped[str | None] = mapped_column(String(45))
       user_agent: Mapped[str | None] = mapped_column(String(255))
       campaign: Mapped["Campaign"] = relationship(back_populates="audit_logs")
       message: Mapped["CampaignMessage"] = relationship(back_populates="audit_logs")
   ```
   Wait, I need to be careful with SQLAlchemy 2.0 syntax. `Mapped` and `mapped_column` are correct. I'll add `__tablename__` and relationships properly. Also, need to handle forward references or import later. I'll keep it clean.

4.  **Design Pydantic Schemas (v2):**
   - Need request/response models for campaigns and messages.
   - Use `ConfigDict` for `from_attributes = True`.
   - Include validation for CPF/CNS format if possible, but keep it simple for now.
   - Include CID-10, CIAP-2, SOAP fields.

   ```python
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from datetime import datetime
   from typing import Optional
   import re

   class CampaignCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=100)
       description: Optional[str] = None
       start_date: datetime
       end_date: datetime
       status: str = "draft"

       @field_validator("end_date")
       @classmethod
       def validate_dates(cls, v, info):
           if info.data.get("start_date") and v < info.data["start_date"]:
               raise ValueError("end_date must be after start_date")
           return v

   class CampaignResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       name: str
       description: Optional[str]
       start_date: datetime
       end_date: datetime
       status: str
       created_at: datetime
       updated_at: datetime

   class MessageStatusEnum(str, Enum):
       PENDING = "pending"
       SENT = "sent"
       DELIVERED = "delivered"
       CONFIRMED = "confirmed"
       FAILED = "failed"

   class CampaignMessageCreate(BaseModel):
       campaign_id: int
       recipient_cpf: str = Field(..., pattern=r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
       recipient_cns: Optional[str] = Field(None, pattern=r"^\d{15}$")
       message_content: str = Field(..., min_length=1)
       status: MessageStatusEnum = MessageStatusEnum.PENDING
       cid10_code: Optional[str] = None
       ciap2_code: Optional[str] = None
       soap_notes: Optional[str] = None

       @field_validator("recipient_cns")
       @classmethod
       def validate_cns(cls, v):
           if v is not None and len(v) != 15:
               raise ValueError("CNS must be exactly 15 digits")
           return v

   class CampaignMessageResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       campaign_id: int
       recipient_cpf: str
       recipient_cns: Optional[str]
       message_content: str
       status: str
       sent_at: Optional[datetime]
       confirmed_at: Optional[datetime]
       cid10_code: Optional[str]
       ciap2_code: Optional[str]
       soap_notes: Optional[str]

   class AuditLogCreate(BaseModel):
       campaign_id: Optional[int] = None
       message_id: Optional[int] = None
       action: str
       details: Optional[str] = None
       performed_by: str
       ip_address: Optional[str] = None
       user_agent: Optional[str] = None

   class AuditLogResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       campaign_id: Optional[int]
       message_id: Optional[int]
       action: str
       details: Optional[str]
       performed_by: str
       timestamp: datetime
       ip_address: Optional[str]
       user_agent: Optional[str]
   ```
   Need to import `Enum` from `enum`. Also, Pydantic v2 uses `field_validator`. I'll adjust imports.

5.  **Design Repository Class:**
   - Use SQLAlchemy async or sync? The prompt doesn't specify, but modern apps use async. I'll use sync for simplicity but note it, or use async with `AsyncSession`. I'll stick to sync `Session` for broader compatibility, but I'll make it clear. Actually, I'll use `Session` from `sqlalchemy.orm`.
   - Methods:
     - `create_campaign(session, data)`
     - `get_campaign(session, campaign_id)`
     - `list_campaigns(session, status=None)`
     - `create_message(session, data)`
     - `update_message_status(session, message_id, new_status)`
     - `confirm_message(session, message_id, confirmed_at)`
     - `log_audit(session, data)`
     - `get_audit_logs(session, campaign_id=None, message_id=None)`
   - I'll wrap them in a class `CampanhasRepository`.
   - Use type hints strictly.
   - Handle transactions properly.

   Let's draft the repository:
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import select
   from typing import List, Optional
   from datetime import datetime
   import logging

   logger = logging.getLogger(__name__)

   class CampanhasRepository:
       def __init__(self, session: Session):
           self.session = session

       def create_campaign(self, data: CampaignCreate) -> Campaign:
           campaign = Campaign(
               name=data.name,
               description=data.description,
               start_date=data.start_date,
               end_date=data.end_date,
               status=data.status
           )
           self.session.add(campaign)
           self.session.flush()
           self._log_audit(campaign.id, None, "CAMPAIGN_CREATED", f"Criada campanha: {data.name}")
           return campaign

       def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
           return self.session.get(Campaign, campaign_id)

       def list_campaigns(self, status: Optional[str] = None) -> List[Campaign]:
           stmt = select(Campaign)
           if status:
               stmt = stmt.where(Campaign.status == status)
           return list(self.session.execute(stmt).scalars().all())

       def create_message(self, data: CampaignMessageCreate) -> CampaignMessage:
           message = CampaignMessage(
               campaign_id=data.campaign_id,
               recipient_cpf=data.recipient_cpf,
               recipient_cns=data.recipient_cns,
               message_content=data.message_content,
               status=data.status.value,
               cid10_code=data.cid10_code,
               ciap2_code=data.ciap2_code,
               soap_notes=data.soap_notes
           )
           self.session.add(message)
           self.session.flush()
           self._log_audit(message.campaign_id, message.id, "MESSAGE_CREATED", f"Mensagem criada para CPF: {data.recipient_cpf}")
           return message

       def update_message_status(self, message_id: int, new_status: str) -> Optional[CampaignMessage]:
           message = self.session.get(CampaignMessage, message_id)
           if not message:
               return None
           old_status = message.status
           message.status = new_status
           if new_status == "sent":
               message.sent_at = datetime.utcnow()
           self.session.flush()
           self._log_audit(message.campaign_id, message.id, "MESSAGE_STATUS_UPDATED", f"Status alterado de {old_status} para {new_status}")
           return message

       def confirm_message(self, message_id: int) -> Optional[CampaignMessage]:
           message = self.session.get(CampaignMessage, message_id)
           if not message:
               return None
           if message.status != "delivered":
               raise ValueError("Mensagem deve estar como 'delivered' para confirmação")
           message.status = "confirmed"
           message.confirmed_at = datetime.utcnow()
           self.session.flush()
           self._log_audit(message.campaign_id, message.id, "MESSAGE_CONFIRMED", "Confirmação de recebimento registrada")
           return message

       def log_audit(self, data: AuditLogCreate) -> AuditLog:
           log = AuditLog(
               campaign_id=data.campaign_id,
               message_id=data.message_id,
               action=data.action,
               details=data.details,
               performed_by=data.performed_by,
               ip_address=data.ip_address,
               user_agent=data.user_agent
           )
           self.session.add(log)
           self.session.flush()
           return log

       def get_audit_logs(self, campaign_id: Optional[int] = None, message_id: Optional[int] = None) -> List[AuditLog]:
           stmt = select(AuditLog)
           if campaign_id:
               stmt = stmt.where(AuditLog.campaign_id == campaign_id)
           if message_id:
               stmt = stmt.where(AuditLog.message_id == message_id)
           stmt = stmt.order_by(AuditLog.timestamp.desc())
           return list(self.session.execute(stmt).scalars().all())

       def _log_audit(self, campaign_id: Optional[int], message_id: Optional[int], action: str, details: str):
           # Simplified audit logging for internal use
           log = AuditLog(
               campaign_id=campaign_id,
               message_id=message_id,
               action=action,
               details=details,
               performed_by="system",
               ip_address="127.0.0.1",
               user_agent="MedIA-Repository"
           )
           self.session.add(log)
   ```
   Wait, I need to import the models and schemas. I'll put them in the same file as requested, or import from a separate file? The prompt says "crie backend/app/repositories/campanhas_repo.py com modelos e métodos de registro". So I'll include models and schemas in this file for simplicity, or structure it properly. I'll keep everything in one file as requested, but organize it clearly.

   I need to fix the `_log_audit` method to not cause infinite recursion or issues. It's fine.
   I'll add proper imports and type hints.
   I'll also add `from enum import Enum` and adjust Pydantic imports.

   Let's refine the file structure:
   - Imports
   - Enums
   - SQLAlchemy Models
   - Pydantic Schemas
   - Repository Class
   - Test file (pytest)

   I'll make sure the code is strictly typed and uses SQLAlchemy 2.0 syntax correctly.
   For SQLAlchemy 2.0, `mapped_column` is correct. I'll use `Column` for simplicity if needed, but `mapped_column` is preferred in 2.0. I'll stick to `mapped_column`.
   I'll add `__future__` annotations if needed, but Python 3.12 supports modern syntax.

   Let's draft the complete `campanhas_repo.py`:

   ```python
   # Arquivo: backend/app/repositories/campanhas_repo.py
   from __future__ import annotations
   from datetime import datetime
   from enum import Enum
   from typing import Optional, List
   from pydantic import BaseModel, Field, ConfigDict, field_validator
   from sqlalchemy import select, String, Text, DateTime, Integer, ForeignKey
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
   import logging

   logger = logging.getLogger(__name__)

   # --- Enums ---
   class MessageStatus(str, Enum):
       PENDING = "pending"
       SENT = "sent"
       DELIVERED = "delivered"
       CONFIRMED = "confirmed"
       FAILED = "failed"

   class AuditAction(str, Enum):
       CAMPAIGN_CREATED = "CAMPAIGN_CREATED"
       CAMPAIGN_UPDATED = "CAMPAIGN_UPDATED"
       MESSAGE_CREATED = "MESSAGE_CREATED"
       MESSAGE_STATUS_UPDATED = "MESSAGE_STATUS_UPDATED"
       MESSAGE_CONFIRMED = "MESSAGE_CONFIRMED"
       MESSAGE_FAILED = "MESSAGE_FAILED"
       DATA_ACCESS = "DATA_ACCESS"
       DATA_MODIFIED = "DATA_MODIFIED"
       DATA_DELETED = "DATA_DELETED"

   # --- SQLAlchemy Models ---
   class Base(DeclarativeBase):
       pass

   class Campaign(Base):
       __tablename__ = "campaigns"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       name: Mapped[str] = mapped_column(String(100),