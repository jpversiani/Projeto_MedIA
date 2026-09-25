from backend.app.services.mensageria import (
    get_patients_with_overdue_hypertension_appointments,
    send_reminder,
    send_notification,
)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base, Patient, Appointment, Notification
from backend.app.services.mensageria import (
    get_patients_with_overdue_hypertension_appointments,
    send_reminder,
    send_notification,
)

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
