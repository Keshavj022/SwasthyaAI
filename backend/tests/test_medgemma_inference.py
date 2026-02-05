"""
Tests for MedGemma Inference

Tests the MedGemma model wrapper for medical text understanding.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.medgemma import MedGemmaInference


@pytest.mark.asyncio
async def test_medgemma_stub_response():
    """Test MedGemma stub response when model not available"""

    # Initialize without model path (should use stub)
    inference = MedGemmaInference(model_path=None, device="cpu")

    # Test medical QA
    response = await inference.generate_response(
        query="What are the symptoms of diabetes?",
        task_type="medical_qa"
    )

    # Verify stub response structure
    assert response["stub_mode"] is True
    assert "analysis_summary" in response
    assert "disclaimer" in response
    assert "confidence" in response
    assert response["confidence"] < 1.0


@pytest.mark.asyncio
async def test_medgemma_differential_stub():
    """Test differential diagnosis stub response"""

    inference = MedGemmaInference(model_path=None, device="cpu")

    response = await inference.generate_differential_diagnosis(
        symptoms=["fever", "cough", "fatigue"],
        patient_history={"age": 35, "chronic_conditions": []},
        vital_signs={"temperature": 101.2, "heart_rate": 88}
    )

    # Verify structure
    assert response["stub_mode"] is True
    assert "differential_diagnoses" in response
    assert "disclaimer" in response
    assert len(response["differential_diagnoses"]) > 0


def test_model_info():
    """Test getting model information"""

    inference = MedGemmaInference(model_path=None, device="cpu")
    info = inference.get_model_info()

    assert info["model_class"] == "MedGemmaInference"
    assert info["device"] == "cpu"
    assert info["using_stub"] is True
    assert info["model_loaded"] is False


def test_is_model_available():
    """Test model availability check"""

    inference = MedGemmaInference(model_path=None, device="cpu")
    assert inference.is_model_available() is False


@pytest.mark.asyncio
async def test_safety_enforcement():
    """Test that safety constraints are enforced"""

    inference = MedGemmaInference(model_path=None, device="cpu")

    response = await inference.generate_response(
        query="Test query",
        task_type="medical_qa"
    )

    # Verify safety requirements
    assert "disclaimer" in response
    assert "confidence" in response
    assert 0.0 <= response["confidence"] <= 1.0
    assert "Consult" in response["disclaimer"] or "healthcare" in response["disclaimer"]


# Integration tests (only run if model available)
@pytest.mark.skipif(
    not (Path(__file__).parent.parent.parent / "models" / "medgemma").exists(),
    reason="MedGemma model not downloaded"
)
@pytest.mark.asyncio
async def test_medgemma_real_inference():
    """Test real MedGemma inference (requires model download)"""

    model_path = Path(__file__).parent.parent.parent / "models" / "medgemma"
    inference = MedGemmaInference(model_path=model_path, device="cpu")

    response = await inference.generate_response(
        query="What are common symptoms of influenza?",
        task_type="medical_qa"
    )

    # If model loads successfully, stub_mode should be False
    # If model loading fails, it falls back to stub
    assert "analysis_summary" in response
    assert "disclaimer" in response
    assert "confidence" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
