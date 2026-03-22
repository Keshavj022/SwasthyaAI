"""
MedASR inference service.

Provides medical speech-to-text transcription via the locally loaded
google/medasr model (Conformer-based, medical vocabulary optimised).

Accepts either a file path or base64-encoded audio bytes.
Temporary files from base64 input are cleaned up after transcription.

All functions return None on failure so callers degrade gracefully to stubs.
"""

import logging
import base64
import tempfile
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def transcribe(
    audio_path: Optional[str] = None,
    audio_data_b64: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Transcribe medical audio using MedASR.

    Provide exactly one of:
      - audio_path: path to an audio file on disk (wav/mp3/flac/etc.)
      - audio_data_b64: base64-encoded audio bytes (written to a temp file)

    Returns:
        {"text": str, "confidence": float}, or None if unavailable/failed.

    The confidence is derived from per-chunk scores when available; otherwise
    a fixed 0.85 estimate is used (MedASR does not expose per-frame posteriors
    at the pipeline level).
    """
    tmp_path: Optional[str] = None
    try:
        from services.model_loader import get_medasr

        pipe = get_medasr()
        if pipe is None:
            return None

        # Resolve audio source
        if audio_data_b64:
            audio_bytes = base64.b64decode(audio_data_b64)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name
            path_to_use = tmp_path
        elif audio_path:
            path_to_use = audio_path
        else:
            logger.warning("transcribe() called with no audio source")
            return None

        result = pipe(path_to_use, return_timestamps=False)

        if isinstance(result, dict):
            text = result.get("text", "").strip()
            chunks = result.get("chunks", [])
        else:
            text = str(result).strip()
            chunks = []

        if chunks:
            scores = [c.get("score", 0.85) for c in chunks if "score" in c]
            confidence = sum(scores) / len(scores) if scores else 0.85
        else:
            confidence = 0.85

        return {"text": text, "confidence": confidence}

    except Exception as exc:
        logger.warning(f"MedASR transcription failed: {exc}")
        return None

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
