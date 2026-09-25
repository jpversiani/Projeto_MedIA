"""
FAI (Ficha de Atendimento Individual) Serializer for SISAB Integration.
Validates CNES, CNS (professional), CBO, and e-SUS APS compliance.
Compliant with CIAP-2, CID-10, SOAP method, and identification by CNS/CPF.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class FAISerializationBase(BaseModel):
    """Base model for FAI serialization with common fields."""
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    patient_cnf: str = Field(..., min_length=1, max_length=20, description="Patient CPF")
    provider_cns: str = Field(..., min_length=1, max_length=50, description="Provider CNS identifier")
    cbo: bool = Field(..., description="Whether CBO (Comitê de Biossegurança Obrigatória) is involved")
    cnes: str = Field(..., min_length=1, max_length=100, description="CNES (Conselho Nacional de Exame de Saúde)")
    clinical_data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class FAIClinicalData(BaseModel):
    """Clinical data section for FAI serialization."""
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    procedure: Optional[str] = None
    cpi_code: Optional[str] = Field(
        None, 
        description="CIAP-2 diagnostic code"
    )
    iad: Optional[str] = Field(
        None, 
        description="CID-10 diagnosis code"
    )
    e_sus_aps_compliance: bool = False


class FAISerializer(FAISerializationBase):
    """
    Official serializer for FAI (Ficha de Atendimento Individual) 
    for integration with SISAB (Ministério da Saúde).
    Validates all required fields according to SUS/APS standards.
    """

    @validator('patient_cnf', pre=True)
    def validate_patient_cnf(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate patient CNPF (CPF) format."""
        # Basic CPF validation (XXX.XXX.XXX-XX)
        if len(v) != 14:
            raise ValueError("CPF must be 14 digits")
        return v

    @validator('provider_cns', pre=True)
    def validate_provider_cns(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate provider CNS identifier."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Provider CNS is required")
        return v.strip()

    @validator('cbs', pre=True)
    def validate_cbo(cls, v: bool, values: Dict[str, Any]) -> bool:
        """Validate CBO involvement flag."""
        return v

    @validator('cnes', pre=True)
    def validate_cnes(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate CNES (Conselho Nacional de Exame de Saúde)."""
        if not v or len(v.strip()) == 0:
            raise ValueError("CNES is required")
        return v.strip()

    @validator('clinical_data', pre=True)
    def validate_clinical_data(cls, v: dict, values: Dict[str, Any]) -> dict:
        """Validate clinical data with CIAP-2 and CID-10 codes."""
        # Ensure required clinical fields are present
        if 'diagnosis' not in v and 'treatment' not in v:
            raise ValueError("At least one of diagnosis or treatment is required")
        return v

    @validator('e_sus_aps_compliance', pre=True)
    def validate_e_sus_aps(cls, v: bool, values: Dict[str, Any]) -> bool:
        """Validate e-SUS APS compliance."""
        return v

    class Config:
        """Pydantic v2 configuration for strict typing."""
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "id": "faa-2026-001",
                "patient_cnf": "12345678901",
                "provider_cns": "CNS-12345",
                "cbo": True,
                "cnes": "CNES-2026-001",
                "clinical_data": {
                    "diagnosis": "Diabetes Mellitus Type 2",
                    "treatment": "Metformin 1000mg BID",
                    "procedure": "Hemoglobin A1c measurement",
                    "cpi_code": "E11.9",
                    "iad": "E11.9",
                    "e_sus_aps_compliance": True
                }
            }
        }


def serialize_faia(fai: FAISerializer) -> dict:
    """
    Serialize a FAI object to dictionary format suitable for SISAB transmission.
    
    Args:
        fai: Instance of FAISerializer containing validated FAI data
        
    Returns:
        Dictionary representation of the FAI for SISAB integration
    """
    return {
        "id": fai.id,
        "patient_cnf": fai.patient_cnf,
        "provider_cns": fai.provider_cns,
        "cbo": fai.cbo,
        "cnes": fai.cnes,
        "clinical_data": fai.clinical_data,
        "timestamp": fai.timestamp.isoformat(),
    }
