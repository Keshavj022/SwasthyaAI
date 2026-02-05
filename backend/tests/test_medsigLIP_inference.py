"""
Tests for MedSigLIP Inference

Tests the MedSigLIP model wrapper for medical image analysis.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.medsigLIP import MedSigLIPInference


@pytest.mark.asyncio
async def test_medsigLIP_stub_response():
    """Test MedSigLIP stub response when model not available"""

    # Initialize without model path (should use stub)
    inference = MedSigLIPInference(model_path=None, device="cpu")

    # Test image analysis (without actual image)
    response = await inference.analyze_image(
        image_path="/tmp/dummy.jpg",  # Dummy path
        modality="x-ray",
        clinical_context="Chest pain evaluation"
    )

    # Verify stub response structure
    assert response["stub_mode"] is True
    assert "modality" in response
    assert response["modality"] == "x-ray"
    assert "disclaimer" in response
    assert "key_findings" in response


@pytest.mark.asyncio
async def test_medsigLIP_classification_stub():
    """Test image classification stub response"""

    inference = MedSigLIPInference(model_path=None, device="cpu")

    response = await inference.classify_image(
        image_path="/tmp/dummy.jpg",
        candidates=["normal", "pneumonia", "covid-19"],
        modality="x-ray"
    )

    # Verify structure
    assert response["stub_mode"] is True
    assert "classifications" in response
    assert len(response["classifications"]) == 3
    assert "disclaimer" in response


def test_model_info():
    """Test getting model information"""

    inference = MedSigLIPInference(model_path=None, device="cpu")
    info = inference.get_model_info()

    assert info["model_class"] == "MedSigLIPInference"
    assert info["device"] == "cpu"
    assert info["using_stub"] is True
    assert info["model_loaded"] is False


def test_supported_modalities():
    """Test that supported modalities are defined"""

    assert "x-ray" in MedSigLIPInference.SUPPORTED_MODALITIES
    assert "ct" in MedSigLIPInference.SUPPORTED_MODALITIES
    assert "mri" in MedSigLIPInference.SUPPORTED_MODALITIES


@pytest.mark.asyncio
async def test_safety_enforcement():
    """Test that safety constraints are enforced"""

    inference = MedSigLIPInference(model_path=None, device="cpu")

    response = await inference.analyze_image(
        image_path="/tmp/dummy.jpg",
        modality="x-ray"
    )

    # Verify safety requirements
    assert "disclaimer" in response
    assert "radiologist" in response["disclaimer"].lower() or "clinician" in response["disclaimer"].lower()


# Integration tests (only run if model available)
@pytest.mark.skipif(
    not (Path(__file__).parent.parent.parent / "models" / "medsigLIP").exists(),
    reason="MedSigLIP model not downloaded"
)
@pytest.mark.asyncio
async def test_medsigLIP_real_inference():
    """Test real MedSigLIP inference (requires model download and test image)"""

    model_path = Path(__file__).parent.parent.parent / "models" / "medsigLIP"
    inference = MedSigLIPInference(model_path=model_path, device="cpu")

    # This test would need an actual medical image
    # Skipping actual inference test without real image
    info = inference.get_model_info()
    assert info["model_class"] == "MedSigLIPInference"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
