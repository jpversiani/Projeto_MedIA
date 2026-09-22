from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.copilot import CopilotSOAPRequest, CopilotSOAPResponse
from app.services.copilot_service import processar_copilot_soap

router = APIRouter(prefix="/copilot", tags=["BRHealth AI Copilot (Apoio Clínico)"])

@router.post("/gerar-soap", response_model=CopilotSOAPResponse)
def gerar_soap_com_ia(payload: CopilotSOAPRequest, db: Session = Depends(get_db)):
    """
    Recebe o relato livre da consulta (ou áudio transcrito) e gera a estrutura SOAP
    com sugestão de CIAP-2, CID-10 e validação de segurança médica.
    """
    return processar_copilot_soap(payload, db=db)
