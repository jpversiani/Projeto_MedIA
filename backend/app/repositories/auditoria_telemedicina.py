# Arquivo: backend/app/repositories/auditoria_telemedicina.py
   from __future__ import annotations
   import uuid
   import enum
   from datetime import datetime, timezone
   from typing import Any, Optional
   from sqlalchemy import (
       String,
       Text,
       DateTime,
       func,
       select,
       insert,
       update,
   )
   from sqlalchemy.orm import (
       DeclarativeBase,
       Mapped,
       mapped_column,
       Session,
       async_sessionmaker,
   )
   from pydantic import BaseModel, Field, field_validator

   # ... (definitions)
