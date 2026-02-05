"""
Tests for MedASR Inference

Tests the MedASR model wrapper for medical speech-to-text.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from inference.medasr import MedASRInference


@pytest.mark.asyncio
async def test_medasr_stub_response():
    """Test MedASR stub response when model not available"""

    # Initialize without model path (should use stub)
    inference = MedASRInference(model_path=None, device="cpu")

    # Test transcription (without actual audio)
    response = await inference.transcribe_audio(
        audio_file="/tmp/dummy.wav",  # Dummy path
        language="en",
        mode="dictation"
    )

    # Verify stub response structure
    assert response["stub_mode"] is True
    assert "transcription" in response
    assert "disclaimer" in response
    assert "error" in response
    assert response["confidence"] == 0.0


@pytest.mark.asyncio
async def test_medasr_diarization_stub():
    """Test speaker diarization stub response"""

    inference = MedASRInference(model_path=None, device="cpu")

    response = await inference.transcribe_with_speaker_diarization(
        audio_file="/tmp/dummy.wav",
        num_speakers=2
    )

    # Verify structure
    assert response["stub_mode"] is True
    assert "segments" in response
    assert "disclaimer" in response


def test_model_info():
    """Test getting model information"""

    inference = MedASRInference(model_path=None, device="cpu")
    info = inference.get_model_info()

    assert info["model_class"] == "MedASRInference"
    assert info["device"] == "cpu"
    assert info["using_stub"] is True
    assert info["model_loaded"] is False


def test_supported_formats():
    """Test that supported audio formats are defined"""

    assert ".wav" in MedASRInference.SUPPORTED_FORMATS
    assert ".mp3" in MedASRInference.SUPPORTED_FORMATS
    assert ".flac" in MedASRInference.SUPPORTED_FORMATS


@pytest.mark.asyncio
async def test_safety_enforcement():
    """Test that safety constraints are enforced"""

    inference = MedASRInference(model_path=None, device="cpu")

    response = await inference.transcribe_audio(
        audio_file="/tmp/dummy.wav",
        mode="dictation"
    )

    # Verify safety requirements
    assert "disclaimer" in response
    assert "reviewed" in response["disclaimer"].lower() or "medical personnel" in response["disclaimer"].lower()


# Integration tests (only run if model available)
@pytest.mark.skipif(
    not (Path(__file__).parent.parent.parent / "models" / "medasr").exists(),
    reason="MedASR model not downloaded"
)
@pytest.mark.asyncio
async def test_medasr_real_inference():
    """Test real MedASR inference (requires model download and test audio)"""

    model_path = Path(__file__).parent.parent.parent / "models" / "medasr"
    inference = MedASRInference(model_path=model_path, device="cpu")

    # This test would need an actual audio file
    # Skipping actual inference test without real audio
    info = inference.get_model_info()
    assert info["model_class"] == "MedASRInference"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
