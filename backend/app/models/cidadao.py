from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, event
from sqlalchemy.orm import relationship
from app.core.crypto import CampoProtegido, hash_busca
from app.core.database import Base

class Cidadao(Base):
    __tablename__ = "cidadaos"

    id = Column(Integer, primary_key=True, index=True)
    # Cifrados em repouso (AES-256-GCM). A unicidade e a busca usam os índices
    # cegos `*_hash` (HMAC), porque o mesmo CPF cifrado gera textos diferentes.
    cns = Column(CampoProtegido, nullable=True) # Cartão Nacional de Saúde
    cpf = Column(CampoProtegido, nullable=True)
    cns_hash = Column(String(64), unique=True, index=True, nullable=True)
    cpf_hash = Column(String(64), unique=True, index=True, nullable=True)
    nome_completo = Column(String(200), nullable=False, index=True)
    nome_social = Column(String(200), nullable=True)
    nome_mae = Column(String(200), nullable=True)
    data_nascimento = Column(Date, nullable=False)
    sexo = Column(String(1), nullable=False) # M (Masculino), F (Feminino), I (Indeterminado)
    raca_cor = Column(String(20), default="Parda") # Branca, Preta, Parda, Amarela, Indígena
    
    # Contato e Localização
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    cep = Column(String(8), nullable=True)
    logradouro = Column(String(200), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    municipio_ibge = Column(String(7), nullable=True) # Ex: 3143302 (Montes Claros - MG)

    # Condições de saúde autorreferidas na APS
    hipertenso = Column(Boolean, default=False)
    diabetico = Column(Boolean, default=False)
    gestante = Column(Boolean, default=False)
    fumante = Column(Boolean, default=False)
    alergias = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    acolhimentos = relationship("FilaAcolhimento", back_populates="cidadao")
    atendimentos = relationship("AtendimentoSOAP", back_populates="cidadao")


@event.listens_for(Cidadao, "before_insert")
@event.listens_for(Cidadao, "before_update")
def _sincronizar_indices_cegos(mapper, connection, target):
    """Mantém `cpf_hash`/`cns_hash` coerentes com o texto claro.

    Fica no evento do ORM (e não em cada rota) porque o CPF é gravado em vários
    lugares — cadastro, seed, importação. Um `UPDATE` em massa via
    `query.update()` NÃO dispara este hook: use atributo por atributo.
    """
    target.cpf_hash = hash_busca(target.cpf)
    target.cns_hash = hash_busca(target.cns)
