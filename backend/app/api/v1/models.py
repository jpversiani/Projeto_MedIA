"""Pydantic models for telemedicina WebSocket communication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SdpMessage(BaseModel):
    """SDP message for WebSocket communication."""
    type: str = Field(..., description="Type of SDP message: offer, answer, ice_candidate, sync")
    sdp: str = Field(..., description="Raw SDP string")
    room_code: str = Field(..., description="Room identifier")
    timestamp: datetime = Field(default_factory=datetime.now)
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    provider_id: Optional[str] = Field(None, description="Provider/clinic identifier")
    medical_record_id: Optional[str] = Field(None, description="Medical record ID")
    cns: Optional[str] = Field(None, description="CNS identifier")
    cip: Optional[str] = Field(None, description="CIP identifier")


class IceCandidate(BaseModel):
    """ICE candidate for WebRTC signaling."""
    candidate_id: str
    local: bool
    remote: bool
    address: str
    port: int
    type: str = Field(..., description="Candidate type: host, srflx, relay")
    timestamp: datetime = Field(default_factory=datetime.now)


class MedicalStateSync(BaseModel):
    """Medical state synchronization payload for telemedicina room."""
    patient_cnf: str = Field(..., description="Patient CPF identifier")
    patient_name: Optional[str] = Field(None, description="Patient name")
    cnp: Optional[str] = Field(None, description="National health card number")
    cpid: Optional[str] = Field(None, description="Primary care ID")
    clinical_data: dict
    timestamp: datetime = Field(default_factory=datetime.now)
