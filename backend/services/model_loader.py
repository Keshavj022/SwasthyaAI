"""
Central singleton loader for the three local Health AI (HAI-DEF) models.

- MedGemma  (text + image, AutoModelForImageTextToText)  -> clinical reasoning agents
- MedSigLIP (zero-shot image classifier, AutoModel/SigLIP) -> image analysis agent
- MedASR / Whisper (speech-to-text pipeline)              -> voice agent

Design goals (offline-first, graceful degradation):
- Each model is loaded ONCE, lazily, on first use, and kept resident for the
  process lifetime (large weights => never load per-request).
- Loading is feature-flagged via settings.MEDGEMMA_MODE / MEDSIGLIP_MODE /
  MEDASR_MODE (booleans). When a flag is False, the weights are absent, or a
  dependency is missing, the getter returns None and callers fall back to a
  clearly-labelled stub. NOTHING here may raise to the caller — load failures
  are logged and degrade to stub.
- Device / dtype per AI_MODELS_REFERENCE: bf16 on CUDA/MPS, fp32 on CPU. No
  bitsandbytes on macOS (MPS) / CPU.
- Offline env vars (HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE / HF_HOME) are
  already exported by config.py at import time.

Thread-safe via a module-level lock with double-checked locking so the heavy
load runs exactly once even under concurrent first requests.
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Tuple

from config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()

# ── Module-level singletons ─────────────────────────────────────────────────
_medgemma_model = None
_medgemma_processor = None
_medgemma_attempted = False

_medsiglip_model = None
_medsiglip_processor = None
_medsiglip_attempted = False

_medasr_pipe = None
_medasr_attempted = False


# ── Device / dtype helpers ──────────────────────────────────────────────────

def _resolve_device() -> str:
    """Resolve the runtime device (cuda > mps > cpu), honoring settings."""
    configured = (settings.MODEL_DEVICE or "auto").lower()
    if configured in {"cuda", "mps", "cpu"}:
        return configured
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except Exception:  # pragma: no cover - torch missing
        return "cpu"
    return "cpu"


def _resolve_dtype(device: str):
    """bf16 on GPU/MPS, fp32 on CPU — unless explicitly overridden."""
    import torch

    override = (settings.MODEL_DTYPE or "auto").lower()
    if override == "float32":
        return torch.float32
    if override == "float16":
        return torch.float16
    if override == "bfloat16":
        return torch.bfloat16
    # auto
    if device == "cpu":
        return torch.float32
    return torch.bfloat16


def _model_source(repo_id: str, local_path: Path) -> str:
    """
    Prefer a self-contained local snapshot directory if it has weights;
    otherwise fall back to the repo id (resolved from the HF cache offline).
    """
    try:
        if local_path and Path(local_path).exists():
            has_weights = any(Path(local_path).glob("*.safetensors")) or any(
                Path(local_path).glob("*.bin")
            )
            if has_weights:
                return str(local_path)
    except Exception:  # pragma: no cover - defensive
        pass
    return repo_id


# ── MedGemma ────────────────────────────────────────────────────────────────

def get_medgemma() -> Tuple[Optional[object], Optional[object]]:
    """Return (model, processor) for MedGemma, or (None, None) if unavailable."""
    global _medgemma_model, _medgemma_processor, _medgemma_attempted
    if _medgemma_model is not None:
        return _medgemma_model, _medgemma_processor
    if _medgemma_attempted:
        return None, None
    with _lock:
        if _medgemma_model is not None:
            return _medgemma_model, _medgemma_processor
        if _medgemma_attempted:
            return None, None
        _medgemma_attempted = True
        if not settings.MEDGEMMA_MODE:
            logger.info("MedGemma disabled (MEDGEMMA_MODE=False); using stubs")
            return None, None
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForImageTextToText

            source = _model_source(settings.MEDGEMMA_REPO_ID, settings.MEDGEMMA_MODEL_PATH)
            device = _resolve_device()
            dtype = _resolve_dtype(device)
            logger.info(f"Loading MedGemma from {source} (device={device}, dtype={dtype})")

            _medgemma_processor = AutoProcessor.from_pretrained(
                source, local_files_only=True
            )
            device_map = "auto" if device == "cuda" else None
            _medgemma_model = AutoModelForImageTextToText.from_pretrained(
                source,
                torch_dtype=dtype,
                device_map=device_map,
                low_cpu_mem_usage=True,
                local_files_only=True,
            )
            if device_map is None:
                _medgemma_model = _medgemma_model.to(device)
            _medgemma_model.eval()
            logger.info("MedGemma loaded successfully")
        except Exception as exc:
            logger.error(f"MedGemma load failed: {exc} — falling back to stubs")
            _medgemma_model = None
            _medgemma_processor = None
    return _medgemma_model, _medgemma_processor


# ── MedSigLIP ────────────────────────────────────────────────────────────────

def get_medsiglip() -> Tuple[Optional[object], Optional[object]]:
    """Return (model, processor) for MedSigLIP, or (None, None) if unavailable."""
    global _medsiglip_model, _medsiglip_processor, _medsiglip_attempted
    if _medsiglip_model is not None:
        return _medsiglip_model, _medsiglip_processor
    if _medsiglip_attempted:
        return None, None
    with _lock:
        if _medsiglip_model is not None:
            return _medsiglip_model, _medsiglip_processor
        if _medsiglip_attempted:
            return None, None
        _medsiglip_attempted = True
        if not settings.MEDSIGLIP_MODE:
            logger.info("MedSigLIP disabled (MEDSIGLIP_MODE=False); using stubs")
            return None, None
        try:
            import torch
            from transformers import AutoModel, AutoProcessor

            source = _model_source(settings.MEDSIGLIP_REPO_ID, settings.MEDSIGCLIP_MODEL_PATH)
            device = _resolve_device()
            # MedSigLIP ships fp32; on CPU keep fp32 (bf16 is slow/unsupported).
            dtype = _resolve_dtype(device)
            logger.info(f"Loading MedSigLIP from {source} (device={device}, dtype={dtype})")

            _medsiglip_processor = AutoProcessor.from_pretrained(
                source, local_files_only=True
            )
            _medsiglip_model = AutoModel.from_pretrained(
                source,
                torch_dtype=dtype,
                attn_implementation="sdpa",
                low_cpu_mem_usage=True,
                local_files_only=True,
            ).to(device)
            _medsiglip_model.eval()
            logger.info("MedSigLIP loaded successfully")
        except Exception as exc:
            logger.error(f"MedSigLIP load failed: {exc} — falling back to stubs")
            _medsiglip_model = None
            _medsiglip_processor = None
    return _medsiglip_model, _medsiglip_processor


# ── MedASR / Whisper ─────────────────────────────────────────────────────────

def get_medasr() -> Optional[object]:
    """Return a HF automatic-speech-recognition pipeline, or None if unavailable."""
    global _medasr_pipe, _medasr_attempted
    if _medasr_pipe is not None:
        return _medasr_pipe
    if _medasr_attempted:
        return None
    with _lock:
        if _medasr_pipe is not None:
            return _medasr_pipe
        if _medasr_attempted:
            return None
        _medasr_attempted = True
        if not settings.MEDASR_MODE:
            logger.info("MedASR disabled (MEDASR_MODE=False); using stubs")
            return None
        try:
            import torch
            from transformers import pipeline as hf_pipeline

            source = _model_source(settings.MEDASR_REPO_ID, settings.MEDASR_MODEL_PATH)
            device = _resolve_device()
            # Keep ASR in fp32 on CPU/MPS for stability; fp16 only worthwhile on CUDA.
            dtype = torch.float16 if device == "cuda" else torch.float32
            # transformers pipeline wants an int device index for cuda, str otherwise.
            pipe_device = 0 if device == "cuda" else device
            logger.info(f"Loading MedASR/ASR from {source} (device={device})")

            _medasr_pipe = hf_pipeline(
                "automatic-speech-recognition",
                model=source,
                torch_dtype=dtype,
                device=pipe_device,
                model_kwargs={"local_files_only": True},
            )
            logger.info("MedASR/ASR pipeline loaded successfully")
        except Exception as exc:
            logger.error(f"MedASR load failed: {exc} — falling back to stubs")
            _medasr_pipe = None
    return _medasr_pipe


# ── Preload + status ──────────────────────────────────────────────────────────

def preload_models() -> None:
    """
    Eagerly attempt to load all enabled models at startup.

    Called from main.py lifespan. MUST NOT raise — any failure degrades to stub
    so the API always boots. Disabled models are skipped instantly.
    """
    logger.info("Preloading local AI models (enabled flags decide what loads)...")
    try:
        if settings.MEDGEMMA_MODE:
            get_medgemma()
        if settings.MEDSIGLIP_MODE:
            get_medsiglip()
        if settings.MEDASR_MODE:
            get_medasr()
    except Exception as exc:  # pragma: no cover - getters already swallow
        logger.error(f"Unexpected error during model preload: {exc}")
    loaded = [m["name"] for m in model_status() if m["loaded"]]
    if loaded:
        logger.info(f"Model preloading complete; loaded: {', '.join(loaded)}")
    else:
        logger.info("Model preloading complete; all models in stub mode")


def _device_label() -> str:
    try:
        return _resolve_device()
    except Exception:  # pragma: no cover
        return "cpu"


def model_status() -> list:
    """
    Snapshot of each model's status for /health/ai-status and the admin panel.

    Returns a list of dicts:
        {name, enabled, loaded, stub, device, repoId}
    `stub` is True whenever the model is NOT serving real inference (disabled,
    failed to load, or not yet loaded while enabled).
    """
    device = _device_label()
    medgemma_loaded = _medgemma_model is not None
    medsiglip_loaded = _medsiglip_model is not None
    medasr_loaded = _medasr_pipe is not None
    return [
        {
            "name": "MedGemma",
            "enabled": bool(settings.MEDGEMMA_MODE),
            "loaded": medgemma_loaded,
            "stub": not medgemma_loaded,
            "device": device,
            "repoId": settings.MEDGEMMA_REPO_ID,
        },
        {
            "name": "MedSigLIP",
            "enabled": bool(settings.MEDSIGLIP_MODE),
            "loaded": medsiglip_loaded,
            "stub": not medsiglip_loaded,
            "device": device,
            "repoId": settings.MEDSIGLIP_REPO_ID,
        },
        {
            "name": "MedASR",
            "enabled": bool(settings.MEDASR_MODE),
            "loaded": medasr_loaded,
            "stub": not medasr_loaded,
            "device": device,
            "repoId": settings.MEDASR_REPO_ID,
        },
    ]
