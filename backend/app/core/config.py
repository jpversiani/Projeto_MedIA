import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "OpenSUS - Prontuário Eletrônico do Cidadão (PEC)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Suporta SQLite para desenvolvimento local imediato ou PostgreSQL em produção
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./esus.db")

settings = Settings()
