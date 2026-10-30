from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, event
from app.core.crypto import CampoProtegido, hash_busca
from app.core.database import Base

class Profissional(Base):
    __tablename__ = "profissionais"

    id = Column(Integer, primary_key=True, index=True)
    # CPF e CNS do prescritor cifrados em repouso; busca/unicidade pelos
    # índices cegos `*_hash` (mesmo esquema de `Cidadao`).
    cns = Column(CampoProtegido, nullable=False) # Cartão Nacional de Saúde
    cpf = Column(CampoProtegido, nullable=False)
    cns_hash = Column(String(64), unique=True, index=True, nullable=True)
    cpf_hash = Column(String(64), unique=True, index=True, nullable=True)
    nome = Column(String(200), nullable=False)
    cbo = Column(String(10), nullable=False) # Ex: 225142 (Médico da Estratégia de Saúde da Família), 223505 (Enfermeiro)
    cbo_descricao = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


@event.listens_for(Profissional, "before_insert")
@event.listens_for(Profissional, "before_update")
def _sincronizar_indices_cegos(mapper, connection, target):
    """Mantém `cpf_hash`/`cns_hash` coerentes com o texto claro."""
    target.cpf_hash = hash_busca(target.cpf)
    target.cns_hash = hash_busca(target.cns)
