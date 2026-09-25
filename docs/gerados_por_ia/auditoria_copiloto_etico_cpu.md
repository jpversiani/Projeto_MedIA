from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Conexão com o banco de dados
engine = create_engine('sqlite:///media.db')
Base = declarative_base()

class SugestaoDiagnóstica(Base):
    __tablename__ = 'sugestao_diagnostica'
    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer)
    diagnóstico = Column(String)
    criado_em = Column(DateTime, default=datetime.utcnow)

class CopilotoClínico(Base):
    __tablename__ = 'copiloto_clínico'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    especialidade = Column(String)

class Medica(Base):
    __tablename__ = 'medica'
    id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer)
    copiloto_clínico_id = Column(Integer)
    sugestao_diagnostica_id = Column(Integer)

class MedicaDB:
    def __init__(self):
        self.Session = sessionmaker(bind=engine)
        self.session = self.Session()

    def criar_sugestao_diagnostica(self, paciente_id, diagnóstico):
        sugestao_diagnostica = SugestaoDiagnóstica(paciente_id=paciente_id, diagnóstico=diagnóstico)
        self.session.add(sugestao_diagnostica)
        self.session.commit()

    def criar_copiloto_clínico(self, nome, especialidade):
        copiloto_clínico = CopilotoClínico(nome=nome, especialidade=especialidade)
        self.session.add(copiloto_clínico)
        self.session.commit()

    def criar_medica(self, paciente_id, copiloto_clínico_id, sugestao_diagnostica_id):
        medica = Medica(paciente_id=paciente_id, copiloto_clínico_id=copiloto_clínico_id, sugestao_diagnostica_id=sugestao_diagnostica_id)
        self.session.add(medica)
        self.session.commit()

    def get_sugestao_diagnostica(self, paciente_id):
        return self.session.query(SugestaoDiagnóstica).filter(SugestaoDiagnóstica.paciente_id == paciente_id).all()

    def get_copiloto_clínico(self):
        return self.session.query(CopilotoClínico).all()

    def get_medica(self, paciente_id):
        return self.session.query(Medica).filter(Medica.paciente_id == paciente_id).all()

# Instância da classe MedicaDB
medica_db = MedicaDB()

# Rota para criar uma sugestão diagnóstica
@app.post("/sugestao-diagnostica")
async def criar_sugestao_diagnostica(paciente_id: int, diagnóstico: str):
    medica_db.criar_sugestao_diagnostica(paciente_id, diagnóstico)
    return {"mensagem": "Sugestão diagnóstica criada com sucesso"}

# Rota para criar um copiloto clínico
@app.post("/copiloto-clínico")
async def criar_copiloto_clínico(nome: str, especialidade: str):
    medica_db.criar_copiloto_clínico(nome, especialidade)
    return {"mensagem": "Copiloto clínico criado com sucesso"}

# Rota para criar uma medica
@app.post("/medica")
async def criar_medica(paciente_id: int, copiloto_clínico_id: int, sugestao_diagnostica_id: int):
    medica_db.criar_medica(paciente_id, copiloto_clínico_id, sugestao_diagnostica_id)
    return {"mensagem": "Medica criada com sucesso"}

# Rota para obter sugestão diagnóstica
@app.get("/sugestao-diagnostica/{paciente_id}")
async def get_sugestao_diagnostica(paciente_id: int):
    return medica_db.get_sugestao_diagnostica(paciente_id)

# Rota para obter copiloto clínico
@app.get("/copiloto-clínico")
async def get_copiloto_clínico():
    return medica_db.get_copiloto_clínico()

# Rota para obter medica
@app.get("/medica/{paciente_id}")
async def get_medica(paciente_id: int):
    return medica_db.get_medica(paciente_id)

import pytest
from backend.app.api.v1.telemedicina import medica_db

def test_criar_sugestao_diagnostica():
    medica_db.criar_sugestao_diagnostica(1, "Diagnóstico 1")
    assert medica_db.get_sugestao_diagnostica(1) == [{"id": 1, "paciente_id": 1, "diagnóstico": "Diagnóstico 1"}]

def test_get_sugestao_diagnostica():
    medica_db.criar_sugestao_diagnostica(1, "Diagnóstico 1")
    assert medica_db.get_sugestao_diagnostica(1) == [{"id": 1, "paciente_id": 1, "diagnóstico": "Diagnóstico 1"}]

def test_criar_copiloto_clínico():
    medica_db.criar_copiloto_clínico("Copiloto 1", "Especialidade 1")
    assert medica_db.get_copiloto_clínico() == [{"id": 1, "nome": "Copiloto 1", "especialidade": "Especialidade 1"}]

def test_get_copiloto_clínico():
    medica_db.criar_copiloto_clínico("Copiloto 1", "Especialidade 1")
    assert medica_db.get_copiloto_clínico() == [{"id": 1, "nome": "Copiloto 1", "especialidade": "Especialidade 1"}]

def test_criar_medica():
    medica_db.criar_sugestao_diagnostica(1, "Diagnóstico 1")
    medica_db.criar_copiloto_clínico("Copiloto 1", "Especialidade 1")
    medica_db.criar_medica(1, 1, 1)
    assert medica_db.get_medica(1) == [{"id": 1, "paciente_id": 1, "copiloto_clínico_id": 1, "sugestao_diagnostica_id": 1}]

def test_get_medica():
    medica_db.criar_sugestao_diagnostica(1, "Diagnóstico 1")
    medica_db.criar_copiloto_clínico("Copiloto 1", "Especialidade 1")
    medica_db.criar_medica(1, 1, 1)
    assert medica_db.get_medica(1) == [{"id": 1, "paciente_id": 1, "copiloto_clínico_id": 1, "sugestao_diagnostica_id": 1}]

uvicorn backend/app/api/v1/telemedicina:app --host 0.0.0.0 --port 8000
