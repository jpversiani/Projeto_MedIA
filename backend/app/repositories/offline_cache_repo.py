# Arquivo: backend/app/repositories/offline_cache_repo.py
   from __future__ import annotations
   import json
   from datetime import datetime, timezone
   from enum import Enum
   from typing import Optional, Sequence
   from uuid import UUID, uuid4

   from pydantic import BaseModel, Field, ConfigDict
   from sqlalchemy import String, Text, DateTime, Integer, Enum as SAEnum, func
   from sqlalchemy.orm import Mapped, mapped_column, Session, DeclarativeBase
   from sqlalchemy import select

   # ... define base, models, enums, repository ...
