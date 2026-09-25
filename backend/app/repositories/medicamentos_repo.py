# Arquivo: backend/app/repositories/medicamentos_repo.py
     from __future__ import annotations
     from typing import Optional, List
     from pydantic import BaseModel, Field
     from sqlalchemy import select, Column, Integer, String, Float
     from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
     import enum

     # Base class for SQLAlchemy models
     class Base(DeclarativeBase):
         pass

     # SQLAlchemy Model
     class Medicamento(Base):
         __tablename__ = "rename_sus_medicamentos"
         id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
         principio_ativo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
         concentracao: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
         forma_farmaceutica: Mapped[str] = mapped_column(String(100), nullable=False)
         via_administracao: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
         registro_anvisa: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
         nome_comercial: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

     # Pydantic Schemas
     class MedicamentoFilter(BaseModel):
         principio_ativo: Optional[str] = Field(None, description="Filtro por princípio ativo")
         concentracao: Optional[str] = Field(None, description="Filtro por concentração")
         forma_farmaceutica: Optional[str] = Field(None, description="Filtro por forma farmacêutica")
         pagina: int = Field(1, ge=1)
         itens_por_pagina: int = Field(20, ge=1, le=100)

     class MedicamentoResponse(BaseModel):
         id: int
         principio_ativo: str
         concentracao: Optional[str]
         forma_farmaceutica: str
         via_administracao: Optional[str]
         registro_anvisa: Optional[str]
         nome_comercial: Optional[str]

         model_config = {"from_attributes": True}

     # Repository
     class MedicamentosRepository:
         def __init__(self, session: Session):
             self.session = session

         def buscar_medicamentos(self, filtros: MedicamentoFilter) -> tuple[List[MedicamentoResponse], int]:
             # Build query
             stmt = select(Medicamento)
             if filtros.principio_ativo:
                 stmt = stmt.where(Medicamento.principio_ativo.ilike(f"%{filtros.principio_ativo}%"))
             if filtros.concentracao:
                 stmt = stmt.where(Medicamento.concentracao == filtros.concentracao)
             if filtros.forma_farmaceutica:
                 stmt = stmt.where(Medicamento.forma_farmaceutica.ilike(f"%{filtros.forma_farmaceutica}%"))

             # Count total
             count_stmt = select(func.count()).select_from(stmt.subquery())
             total = self.session.execute(count_stmt).scalar_one()

             # Apply pagination
             stmt = stmt.offset((filtros.pagina - 1) * filtros.itens_por_pagina).limit(filtros.itens_por_pagina)
             results = self.session.execute(stmt).scalars().all()

             # Convert to Pydantic
             response_list = [MedicamentoResponse.model_validate(m) for m in results]
             return response_list, total

# Arquivo: backend/app/repositories/test_medicamentos_repo.py
     import pytest
     from sqlalchemy import create_engine
     from sqlalchemy.orm import sessionmaker
     from app.repositories.medicamentos_repo import Base, Medicamento, MedicamentosRepository, MedicamentoFilter
     from typing import List

     @pytest.fixture
     def engine():
         return create_engine("sqlite:///:memory:", echo=False)

     @pytest.fixture
     def session(engine):
         Base.metadata.create_all(engine)
         SessionLocal = sessionmaker(bind=engine)
         sess = SessionLocal()
         yield sess
         sess.close()

     @pytest.fixture
     def repo(session):
         return MedicamentosRepository(session)

     @pytest.fixture
     def seed_data(session):
         # Insert test data
         meds = [
             Medicamento(principio_ativo="Dipirona Sódica", concentracao="500mg", forma_farmaceutica="Comprimido", via_administracao="Oral", registro_anvisa="1.2345678901234", nome_comercial="Novalgina"),
             Medicamento(principio_ativo="Paracetamol", concentracao="750mg", forma_farmaceutica="Comprimido", via_administracao="Oral", registro_anvisa="9.8765432109876", nome_comercial="Dafilon"),
             Medicamento(principio_ativo="Ibuprofeno", concentracao="600mg", forma_farmaceutica="Cápsula", via_administracao="Oral", registro_anvisa="5.5555555555555", nome_comercial="Alivium"),
         ]
         session.add_all(meds)
         session.commit()
         return meds

     def test_buscar_por_principio_ativo(repo, seed_data):
         filtros = MedicamentoFilter(principio_ativo="dipirona")
         resultados, total = repo.buscar_medicamentos(filtros)
         assert total == 1
         assert len(resultados) == 1
         assert resultados[0].principio_ativo == "Dipirona Sódica"

     def test_buscar_por_concentracao(repo, seed_data):
         filtros = MedicamentoFilter(concentracao="750mg")
         resultados, total = repo.buscar_medicamentos(filtros)
         assert total == 1
         assert resultados[0].concentracao == "750mg"

     def test_buscar_por_forma_farmaceutica(repo, seed_data):
         filtros = MedicamentoFilter(forma_farmaceutica="comprimido")
         resultados, total = repo.buscar_medicamentos(filtros)
         assert total == 2
         assert all(r.forma_farmaceutica == "Comprimido" for r in resultados)

     def test_buscar_sem_filtros(repo, seed_data):
         filtros = MedicamentoFilter()
         resultados, total = repo.buscar_medicamentos(filtros)
         assert total == 3
         assert len(resultados) == 3

     def test_paginacao(repo, seed_data):
         filtros = MedicamentoFilter(pagina=1, itens_por_pagina=2)
         resultados, total = repo.buscar_medicamentos(filtros)
         assert total == 3
         assert len(resultados) == 2

         filtros2 = MedicamentoFilter(pagina=2, itens_por_pagina=2)
         resultados2, _ = repo.buscar_medicamentos(filtros2)
         assert len(resultados2) == 1

from sqlalchemy import Column, Integer, String, select, func
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from pydantic import BaseModel, Field, ConfigDict
   class MedicamentoResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
