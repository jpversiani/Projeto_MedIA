from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

import app.models
from app.core.config import settings
from app.core.database import engine, SessionLocal, Base
from app.api.v1.router import api_router
from app.seeds.init_data import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas se ainda não existirem
    Base.metadata.create_all(bind=engine)
    
    # Aplica seeds iniciais de dados
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
        
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Réplica de Arquitetura Aberta do e-SUS APS (Prontuário Eletrônico do Cidadão - PEC)",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Servir interface estática web se o diretório existir
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(os.path.join(static_dir, "index.html"))
