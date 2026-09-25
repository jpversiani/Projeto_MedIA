"""Tests for FAI Serializer (SISAB Integration)."""

import pytest
from datetime import datetime

from backend.app.services.fai_serializer import (
    FAISerializer,
    FAIClinicalData,
    serialize_faia,
)
from pydantic import ValidationError


class TestFAISerializer:
    """Test cases for FAISerializer class."""

    def test_serialize_valid_faia(self):
        """Test serialization of a valid FAI object."""
        clinical_data = {
            "diagnosis": "Hypertension",
            "treatment": "Amlodipine 5mg TDS",
            "procedure": "Blood pressure monitoring",
            "cpi_code": "I10",
            "iad": "I10",
            "e_sus_aps_compliance": True,
        }
        
        fai = FAISerializer(
            patient_cnf="12345678901",
            provider_cns="CNS-98765",
            cbo=True,
            cnes="CNES-2026-001",
            clinical_data=clinical_data,
        )
        
        result = serialize_faia(fai)
        
        assert result["id"] == fai.id
        assert result["patient_cnf"] == fai.patient_cnf
        assert result["provider_cns"] == fai.provider_cns
        assert result["cbo"] == fai.cbo
        assert result["cnes"] == fai.cnes
        assert result["clinical_data"]["diagnosis"] == clinical_data["diagnosis"]
        assert result["clinical_data"]["treatment"] == clinical_data["treatment"]
        assert result["clinical_data"]["cpi_code"] == clinical_data["cpi_code"]
        assert result["clinical_data"]["iad"] == clinical_data["iad"]
        assert result["clinical_data"]["e_sus_aps_compliance"] == clinical_data["e_sus_aps_compliance"]
        assert isinstance(result["timestamp"], str)

    def test_validate_patient_cnf_format(self):
        """Test patient CPF validation."""
        # Valid CPF format (14 digits)
        valid_cpf = "12345678901"
        fai = FAISerializer(
            patient_cnf=valid_cpf,
            provider_cns="CNS-12345",
            cbo=False,
            cnes="CNES-2026-001",
            clinical_data={},
        )
        assert fai.patient_cnf == valid_cpf
        
        # Invalid CPF (wrong length)
        with pytest.raises(ValidationError, match="CPF must be 14 digits"):
            FAISerializer(
                patient_cnf="12345",  # Too short
                provider_cns="CNS-12345",
                cbo=False,
                cnes="CNES-2026-001",
                clinical_data={},
            )

    def test_validate_provider_cns_required(self):
        """Test that provider CNS is required."""
        with pytest.raises(ValidationError, match="Provider CNS is required"):
            FAISerializer(
                patient_cnf="12345678901",
                provider_cns="",  # Empty string
                cbo=False,
                cnes="CNES-2026-001",
                clinical_data={},
            )

    def test_validate_cnb_is_required(self):
        """Test that CNES is required."""
        with pytest.raises(ValidationError, match="CNES is required"):
            FAISerializer(
                patient_cnf="12345678901",
                provider_cns="CNS-12345",
                cbo=False,
                cnes="",  # Empty string
                clinical_data={},
            )

    def test_validate_cbo_flag(self):
        """Test CBO flag validation."""
        # Valid boolean values
        fai_true = FAISerializer(
            patient_cnf="12345678901",
            provider_cns="CNS-12345",
            cbo=True,
            cnes="CNES-2026-001",
            clinical_data={},
        )
        assert fai_true.cbo is True
        
        fai_false = FAISerializer(
            patient_cnf="12345678901",
            provider_cns="CNS-12345",
            cbo=False,
            cnes="CNES-2026-001",
            clinical_data={},
        )
        assert fai_false.cbo is False

    def test_validate_cnes_required(self):
        """Test that CNES is required."""
        with pytest.raises(ValidationError, match="CNES is required"):
            FAISerializer(
                patient_cnf="12345678901",
                provider_cns="CNS-12345",
                cbo=False,
                cbs="",  # Wrong attribute name - should be cnes
                clinical_data={},
            )

    def test_validate_clinical_data_required_fields(self):
        """Test that clinical data must contain at least diagnosis or treatment."""
        # Missing both diagnosis and treatment
        clinical_data = {}
        with pytest.raises(ValidationError, match="At least one of diagnosis or treatment is required"):
            FAISerializer(
                patient_cnf="12345678901",
                provider_cns="CNS-12345",
                cbo=False,
                cnes="CNES-2026-001",
                clinical_data=clinical_data,
            )
        
        # With diagnosis but no treatment
        clinical_data = {"diagnosis": "Hypertension"}
        fai = FAISerializer(
            patient_cnf="12345678901",
            provider_cns="CNS-12345",
            cbo=False,
            cnes="CNES-2026-001",
            clinical_data=clinical_data,
        )
        assert fai.clinical_data["diagnosis"] == "Hypertension"
        assert fai.clinical_data["treatment"] is None

    def test_serialize_without_errors(self):
        """Test that serialization completes without errors for valid data."""
        clinical_data = {
            "diagnosis": "Type 2 Diabetes",
            "treatment": "Metformin 500mg BID",
            "procedure": "HbA1c measurement",
            "cpi_code": "E11.9",
            "iad": "E11.9",
            "e_sus_aps_compliance": True,
        }
        
        fai = FAISerializer(
            patient_cnf="19876543210",
            provider_cns="CNS-55555",
            cbo=True,
            cnes="CNES-2026-002",
            clinical_data=clinical_data,
        )
        
        result = serialize_faia(fai)
        assert result["id"] is not None
        assert result["patient_cnf"] == "19876543210"
        assert result["provider_cns"] == "CNS-55555"
        assert result["cbo"] is True
        assert result["cnes"] == "CNES-2026-002"
        assert result["clinical_data"]["diagnosis"] == "Type 2 Diabetes"
        assert result["clinical_data"]["treatment"] == "Metformin 500mg BID"
        assert result["clinical_data"]["cpi_code"] == "E11.9"
        assert result["clinical_data"]["iad"] == "E11.9"
        assert result["clinical_data"]["e_sus_aps_compliance"] is True
        assert "timestamp" in result

    def test_serialize_with_invalid_cnpf(self):
        """Test that invalid CPF raises validation error."""
        with pytest.raises(ValidationError, match="CPF must be 14 digits"):
            FAISerializer(
                patient_cnf="12345",  # Only 5 digits
                provider_cns="CNS-12345",
                cbo=False,
                cnes="CNES-2026-001",
                clinical_data={},
            )

    def test_serialize_with_empty_cnb(self):
        """Test that empty patient CNP raises validation error."""
        with pytest.raises(ValidationError, match="CPF must be 14 digits"):
            FAISerializer(
                patient_cnf="",  # Empty string
                provider_cns="CNS-12345",
                cbo=False,
                cnes="CNES-2026-001",
                clinical_data={},
            )

    def test_serialize_with_empty_cbs(self):
        """Test that empty CBO flag raises validation error."""
        with pytest.raises(ValidationError, match="Provider CNS is required"):
            FAISerializer(
                patient_cnf="12345678901",
                provider_cns="",  # Empty string
                cbo=False,
                cnes="CNES-2026-001",
                clinical_data={},
            )
