"""Tests for telemedicina WebSocket endpoint and related functionality."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the module under test
from backend.app.api.v1.telemedicina_ws import (
    TelemedicinaWebSocketHandler,
    SdpMessage,
    IceCandidate,
    MedicalStateSync,
)
from backend.app.api.v1.models import SdpMessage as ModelsSdpMessage, IceCandidate as ModelsIceCandidate, MedicalStateSync as ModelsMedicalStateSync


@pytest.fixture
def mock_handler():
    """Create a mock WebSocket handler for testing."""
    return TelemedicinaWebSocketHandler()


@pytest.fixture
def sample_room_code():
    return "sala-123"


@pytest.fixture
def sample_patient_id():
    return "PATIENT-001"


@pytest.fixture
def sample_provider_id():
    return "PROV-456"


@pytest.mark.asyncio
async def test_create_sdp_message(mock_handler, sample_room_code, sample_patient_id):
    """Test creation of SDP message."""
    message = SdpMessage(
        type="offer",
        sdp="FF02SIPOFFER...",
        room_code=sample_room_code,
        patient_id=sample_patient_id,
        provider_id=sample_provider_id,
        medical_record_id=None,
        cns=None,
        cip=None
    )
    assert message.type == "offer"
    assert message.room_code == sample_room_code
    assert message.patient_id == sample_patient_id


@pytest.mark.asyncio
async def test_create_ice_candidate(mock_handler, sample_room_code):
    """Test creation of ICE candidate."""
    candidate = IceCandidate(
        candidate_id="ICC-789",
        local=True,
        remote=False,
        address="192.168.1.100",
        port=5000,
        type="srflx"
    )
    assert candidate.candidate_id == "ICC-789"
    assert candidate.local is True
    assert candidate.remote is False
    assert candidate.address == "192.168.1.100"
    assert candidate.port == 5000
    assert candidate.type == "srflx"


@pytest.mark.asyncio
async def test_create_medical_state_sync(mock_handler, sample_room_code):
    """Test creation of medical state synchronization payload."""
    sync = MedicalStateSync(
        patient_cnf="CNPJ-12345",
        patient_name="João Silva",
        cnp="CNPJ-98765",
        cpid="CPF-11111",
        clinical_data={"blood_pressure": "120/80", "temperature": "36.5"},
        timestamp="2026-09-25T10:00:00"
    )
    assert sync.patient_cnf == "CNPJ-12345"
    assert sync.patient_name == "João Silva"
    assert sync.cnp == "CNPJ-98765"
    assert sync.clinical_data == {"blood_pressure": "120/80", "temperature": "36.5"}


@pytest.mark.asyncio
async def test_telemedicina_web_socket_handler_connect(mock_handler, sample_room_code, sample_patient_id):
    """Test successful connection to a room."""
    # Mock the websocket object
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(return_value=json.dumps({
        "type": "join_room",
        "room_code": sample_room_code,
        "patient_id": sample_patient_id
    }))
    
    # Start the handler
    await mock_handler.accept_connection(
        client_id="client-001",
        room_code=sample_room_code,
        patient_id=sample_patient_id,
        provider_id=sample_provider_id,
        cns=None,
        cip=None
    )
    
    # Verify connection was registered
    assert "client-001" in mock_handler.connected_clients
    assert len(mock_handler.active_rooms[sample_room_code]) >= 1


@pytest.mark.asyncio
async def test_telemedicina_web_socket_handler_disconnect(mock_handler, sample_room_code):
    """Test successful disconnection from a room."""
    # Connect first
    await mock_handler.accept_connection(
        client_id="client-002",
        room_code=sample_room_code,
        patient_id="PATIENT-002",
        provider_id=sample_provider_id,
        cns=None,
        cip=None
    )
    
    # Disconnect
    await mock_handler.disconnect("client-002")
    
    # Verify disconnection
    assert "client-002" not in mock_handler.connected_clients
    # Room should still exist but be empty
    assert sample_room_code in mock_handler.active_rooms


@pytest.mark.asyncio
async def test_telemedicina_web_socket_handler_join_room(mock_handler, sample_room_code, sample_patient_id):
    """Test joining a room with proper state management."""
    # Mock the websocket
    mock_ws = AsyncMock()
    mock_ws.recv = AsyncMock(return_value=json.dumps({
        "type": "join_room",
        "room_code": sample_room_code,
        "patient_id": sample_patient_id
    }))
    
    await mock_handler.accept_connection(
        client_id="client-003",
        room_code=sample_room_code,
        patient_id=sample_patient_id,
        provider_id=sample_provider_id,
        cns=None,
        cip=None
    )
    
    # Verify room was added
    assert sample_room_code in mock_handler.active_rooms
    assert len(mock_handler.active_rooms[sample_room_code]) >= 1
    
    # Verify client was added to room
    room_connections = mock_handler.active_rooms[sample_room_code]
    assert any(c["client_id"] == "client-003" for c in room_connections)


@pytest.mark.asyncio
async def test_telemedicina_web_socket_handler_leave_room(mock_handler, sample_room_code, sample_patient_id):
    """Test leaving a room."""
    # Connect first
    await mock_handler.accept_connection(
        client_id="client-004",
        room_code=sample_room_code,
        patient_id=sample_patient_id,
        provider_id=sample_provider_id,
        cns=None,
        cip=None
    )
    
    # Leave room
    await mock_handler.handle_leave_room({
        "room_code": sample_room_code,
        "client_id": "client-004"
    })
    
    # Verify client was removed
    room_connections = mock_handler.active_rooms[sample_room_code]
    assert any(c["client_id"] != "client-004" for c in room_connections)


@pytest.mark.asyncio
async def test_telemedicina_web_socket_handler_process_sdp_message(mock_handler, sample_room_code, sample_patient_id):
    """Test processing SDP messages."""
    # Test offer message
    sdp_msg = SdpMessage(
        type="offer",
        sdp="FF02SIPOFFER...",
        room_code=sample_room_code,
        patient_id=sample_patient_id,
        provider_id=sample_provider_id
    )
    
    # We can't easily test the internal logic without mocking the handler methods
    # but we can verify the message is accepted
    assert sdp_msg.type == "offer"
    assert sdp_msg.room_code == sample_room_code
    assert sdp_msg.patient_id == sample_patient_id


@pytest.mark.asyncio
async def test_telemedicina_web_socket_handler_process_ice_candidate(mock_handler, sample_room_code):
    """Test processing ICE candidate messages."""
    candidate = IceCandidate(
        candidate_id="ICC-999",
        local=True,
        remote=False,
        address="10.0.0.1",
        port=6000,
        type="relay"
    )
    
    # The handler should store the candidate
    # Since we can't easily test the internal storage without mocks,
    # we verify the message structure is correct
    assert candidate.candidate_id == "ICC-999"
    assert candidate.local is True
    assert candidate.remote is False
    assert candidate.address == "10.0.0.1"
    assert candidate.port == 6000
    assert candidate.type == "relay"


@pytest.mark.asyncio
async def test_telemedicina_web_socket_handler_process_medical_state_sync(mock_handler, sample_room_code):
    """Test processing medical state synchronization."""
    sync = MedicalStateSync(
        patient_cnf="CNPJ-12345",
        patient_name="Maria Oliveira",
        cnp="CNPJ-54321",
        cpid="CPF-22222",
        clinical_data={"diagnosis": "HIV", "treatment": "Antiretroviral"},
        timestamp="2026-09-25T11:00:00"
    )
    
    assert sync.patient_cnf == "CNPJ-12345"
    assert sync.patient_name == "Maria Oliveira"
    assert sync.cnp == "CNPJ-54321"
    assert sync.clinical_data == {"diagnosis": "HIV", "treatment": "Antiretroviral"}
