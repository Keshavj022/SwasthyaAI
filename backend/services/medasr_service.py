"""
Thin MedASR / Whisper speech-to-text wrapper.

Uses the HF automatic-speech-recognition pipeline from model_loader. Handles
long audio via chunking (chunk_length_s / stride_length_s from settings).

Default model is Whisper (works on transformers<5); google/medasr is the
gated, advanced clinical option (English-only, requires transformers>=5).

Returns a clearly-labelled stub (``stub_mode=True``) when no ASR model is
loaded; it never invents a transcript.

Public API:
    transcribe(audio_bytes, audio_format="wav", chunk_length_s=None,
               stride_length_s=None)
        -> {"text", "chunks", "language", "model", "stub_mode", "note", ...}
"""

import logging
import os
import tempfile
from typing import Any, Dict, Optional

from config import settings
from services.model_loader import get_medasr

logger = logging.getLogger(__name__)

VOICE_DISCLAIMER = (
    "This transcription was produced by automated speech recognition and may "
    "contain errors. Verify all medical terminology before clinical use."
)

STUB_NOTE = (
    "Speech-to-text model not loaded — this is non-authoritative demo output. "
    "No real transcription was performed."
)


def is_available() -> bool:
    """True when an ASR pipeline (MedASR or Whisper) is loaded."""
    return get_medasr() is not None


def _stub(reason: str = "") -> Dict[str, Any]:
    return {
        "text": "",
        "chunks": [],
        "language": "en",
        "model": "stub",
        "stub_mode": True,
        "note": STUB_NOTE if not reason else f"{STUB_NOTE} ({reason})",
        "disclaimer": VOICE_DISCLAIMER,
    }


def transcribe(
    audio_bytes: bytes,
    audio_format: str = "wav",
    chunk_length_s: Optional[int] = None,
    stride_length_s: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Transcribe audio bytes to text.

    Args:
        audio_bytes: raw audio file bytes (wav/mp3/webm/ogg/m4a/flac).
        audio_format: file-extension hint used for the temp file.
        chunk_length_s / stride_length_s: long-audio chunking (defaults from
            settings: MEDASR_CHUNK_LENGTH_S / MEDASR_STRIDE_LENGTH_S).

    Returns a dict that always carries ``stub_mode``. On failure or when no
    model is loaded, ``text`` is empty and ``stub_mode`` is True.
    """
    pipe = get_medasr()
    if pipe is None:
        return _stub("model_not_loaded")

    if not audio_bytes:
        result = _stub("empty_audio")
        result["stub_mode"] = False  # model is loaded; just no audio to decode
        result["note"] = "No audio data was provided."
        return result

    chunk = chunk_length_s or settings.MEDASR_CHUNK_LENGTH_S
    stride = stride_length_s or settings.MEDASR_STRIDE_LENGTH_S
    suffix = f".{audio_format.lstrip('.')}" if audio_format else ".wav"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Try with word-level timestamps; fall back gracefully if the model /
        # transformers build does not support them.
        try:
            result = pipe(
                tmp_path,
                chunk_length_s=chunk,
                stride_length_s=stride,
                return_timestamps="word",
            )
        except Exception as exc:
            logger.info(f"ASR word timestamps unsupported ({exc}); retrying plain")
            result = pipe(tmp_path, chunk_length_s=chunk, stride_length_s=stride)

        text = (result.get("text") or "").strip() if isinstance(result, dict) else str(result)
        chunks = result.get("chunks", []) if isinstance(result, dict) else []

        return {
            "text": text,
            "chunks": chunks,
            "language": "en",
            "model": settings.MEDASR_REPO_ID,
            "stub_mode": False,
            "disclaimer": VOICE_DISCLAIMER,
        }
    except Exception as exc:
        logger.error(f"ASR transcription error: {exc}")
        result = _stub(f"inference_error: {exc}")
        return result
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:  # pragma: no cover - best effort cleanup
                pass
