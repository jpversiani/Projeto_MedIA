from sqlalchemy import String, Integer
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   from typing import Optional, List
   from pydantic import BaseModel, Field

   class Base(DeclarativeBase):
       pass

   class Medicamento(Base):
       __tablename__ = "medicamentos"
       id: Mapped[int] = mapped_column(Integer, primary_key=True)
       codigo_sis: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
       principio_ativo: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
       concentracao: Mapped[str] = mapped_column(String(50), nullable=False)
       forma_farmaceutica: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
       laboratorio: Mapped[str] = mapped_column(String(200), nullable=True)
       dosagem: Mapped[str] = mapped_column(String(50), nullable=True)
       via_administracao: Mapped[str] = mapped_column(String(50), nullable=True)
       registro_anvisa: Mapped[str] = mapped_column(String(50), nullable=True)
       status_sus: Mapped[str] = mapped_column(String(20), default="ATIVO")

class MedicamentosRepository:
       def __init__(self, session: Session):
           self.session = session

       def buscar_por_principio_ativo(self, principio_ativo: str) -> List[Medicamento]:
           stmt = select(Medicamento).where(Medicamento.principio_ativo.ilike(f"%{principio_ativo}%"))
           return list(self.session.scalars(stmt).all())

       def buscar_por_concentracao(self, concentracao: str) -> List[Medicamento]:
           stmt = select(Medicamento).where(Medicamento.concentracao.ilike(f"%{concentracao}%"))
           return list(self.session.scalars(stmt).all())

       def buscar_por_forma_farmaceutica(self, forma_farmaceutica: str) -> List[Medicamento]:
           stmt = select(Medicamento).where(Medicamento.forma_farmaceutica.ilike(f"%{forma_farmaceutica}%"))
           return list(self.session.scalars(stmt).all())

       def buscar_medicamentos(self, principio_ativo: Optional[str] = None, concentracao: Optional[str] = None, forma_farmaceutica: Optional[str] = None) -> List[Medicamento]:
           stmt = select(Medicamento)
           if principio_ativo:
               stmt = stmt.where(Medicamento.principio_ativo.ilike(f"%{principio_ativo}%"))
           if concentracao:
               stmt = stmt.where(Medicamento.concentracao.ilike(f"%{concentracao}%"))
           if forma_farmaceutica:
               stmt = stmt.where(Medicamento.forma_farmaceutica.ilike(f"%{forma_farmaceutica}%"))
           return list(self.session.scalars(stmt).all())

class MedicamentoResponse(BaseModel):
       id: int
       codigo_sis: str
       principio_ativo: str
       concentracao: str
       forma_farmaceutica: str
       laboratorio: Optional[str] = None
       dosagem: Optional[str] = None
       via_administracao: Optional[str] = None
       registro_anvisa: Optional[str] = None
       status_sus: str

       class ConfigDict = {"from_attributes": True} # Pydantic v2 uses model_config

# Arquivo: backend/app/repositories/medicamentos_repo.py
   from __future__ import annotations

   from typing import Optional, List
   from pydantic import BaseModel, ConfigDict, Field
   from sqlalchemy import String, Integer
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
   from sqlalchemy import select

   class Base(DeclarativeBase):
       pass

   class MedicamentoModel(Base):
       """
       Modelo ORM para fármacos padronizados da RENAME/SUS.
       Conformidade com padrões SUS/APS: estrutura preparada para integração com CIAP-2, CID-10,
       método SOAP e identificação por CNS/CPF em camadas superiores.
       """
       __tablename__ = "medicamentos"

       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
       codigo_sis: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
       principio_ativo: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
       concentracao: Mapped[str] = mapped_column(String(50), nullable=False)
       forma_farmaceutica: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
       laboratorio: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
       dosagem: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       via_administracao: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       registro_anvisa: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
       status_sus: Mapped[str] = mapped_column(String(20), default="ATIVO", nullable=False)

   class MedicamentoResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       codigo_sis: str
       principio_ativo: str
       concentracao: str
       forma_farmaceutica: str
       laboratorio: Optional[str] = None
       dosagem: Optional[str] = None
       via_administracao: Optional[str] = None
       registro_anvisa: Optional[str] = None
       status_sus: str

   class MedicamentosRepository:
       """
       Repositório para busca e filtragem de fármacos padronizados (RENAME/SUS).
       Utiliza SQLAlchemy 2.0 com tipagem estrita e Pydantic v2 para validação.
       """
       def __init__(self, session: Session) -> None:
           self.session = session

       def buscar_por_principio_ativo(self, principio_ativo: str) -> List[MedicamentoModel]:
           stmt = select(MedicamentoModel).where(MedicamentoModel.principio_ativo.ilike(f"%{principio_ativo}%"))
           return list(self.session.scalars(stmt).all())

       def buscar_por_concentracao(self, concentracao: str) -> List[MedicamentoModel]:
           stmt = select(MedicamentoModel).where(MedicamentoModel.concentracao.ilike(f"%{concentracao}%"))
           return list(self.session.scalars(stmt).all())

       def buscar_por_forma_farmaceutica(self, forma_farmaceutica: str) -> List[MedicamentoModel]:
           stmt = select(MedicamentoModel).where(MedicamentoModel.forma_farmaceutica.ilike(f"%{forma_farmaceutica}%"))
           return list(self.session.scalars(stmt).all())

       def buscar_medicamentos(
           self,
           principio_ativo: Optional[str] = None,
           concentracao: Optional[str] = None,
           forma_farmaceutica: Optional[str] = None
       ) -> List[MedicamentoModel]:
           stmt = select(MedicamentoModel)
           if principio_ativo:
               stmt = stmt.where(MedicamentoModel.principio_ativo.ilike(f"%{principio_ativo}%"))
           if concentracao:
               stmt = stmt.where(MedicamentoModel.concentracao.ilike(f"%{concentracao}%"))
           if forma_farmaceutica:
               stmt = stmt.where(MedicamentoModel.forma_farmaceutica.ilike(f"%{forma_farmaceutica}%"))
           return list(self.session.scalars(stmt).all())

       def converter_para_dto(self, medicamentos: List[MedicamentoModel]) -> List[MedicamentoResponse]:
           return [MedicamentoResponse.model_validate(m) for m in medicamentos]
