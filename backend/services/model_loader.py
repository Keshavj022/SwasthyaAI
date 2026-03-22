"""
Thread-safe lazy-loading singletons for local AI models.

Supports CUDA, Apple MPS (Apple Silicon GPU), and CPU.
All models load on first use via double-checked locking.
A background preload is triggered at application startup.
"""

import threading
import logging
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()

# MedGemma (google/medgemma-1.5-4b-it) — multimodal text+image generation
_medgemma_model: Optional[Any] = None
_medgemma_processor: Optional[Any] = None
_medgemma_loaded: bool = False

# MedSigLIP (google/medsiglip-448) — zero-shot medical image classification
_medsiglip_model: Optional[Any] = None
_medsiglip_processor: Optional[Any] = None
_medsiglip_loaded: bool = False

# MedASR (google/medasr) — medical speech-to-text
_medasr_pipeline: Optional[Any] = None
_medasr_loaded: bool = False


def _get_device() -> str:
    """Return best available device: cuda > mps > cpu."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def get_medgemma() -> Tuple[Optional[Any], Optional[Any]]:
    """
    Return (model, processor) for MedGemma, loading on first call.

    MedGemma is AutoModelForImageTextToText (Gemma 3 multimodal).
    Apple MPS: load with float16, then .to('mps') — device_map='auto' not supported.
    CUDA: use device_map='auto' with bfloat16.
    CPU: float32, no device_map.
    """
    global _medgemma_model, _medgemma_processor, _medgemma_loaded

    if _medgemma_loaded:
        return _medgemma_model, _medgemma_processor

    with _lock:
        if _medgemma_loaded:  # double-checked
            return _medgemma_model, _medgemma_processor

        try:
            from config import settings
            if settings.MEDGEMMA_MODE == "disabled":
                logger.info("MedGemma disabled by config (MEDGEMMA_MODE=disabled)")
                return None, None

            import torch
            from transformers import AutoProcessor, AutoModelForImageTextToText

            model_id = settings.MEDGEMMA_MODEL_ID
            cache_dir = settings.MODEL_CACHE_DIR or None
            device = _get_device()
            token = settings.HF_TOKEN or None

            logger.info(f"Loading MedGemma '{model_id}' on device={device} ...")

            processor = AutoProcessor.from_pretrained(
                model_id,
                token=token,
                cache_dir=cache_dir,
            )

            if device == "mps":
                # device_map='auto' is not supported with MPS backends in accelerate.
                # Load on CPU with float16, then move to MPS.
                model = AutoModelForImageTextToText.from_pretrained(
                    model_id,
                    token=token,
                    cache_dir=cache_dir,
                    torch_dtype=torch.float16,
                ).to("mps")
            elif device == "cuda":
                model = AutoModelForImageTextToText.from_pretrained(
                    model_id,
                    token=token,
                    cache_dir=cache_dir,
                    device_map="auto",
                    torch_dtype=torch.bfloat16,
                )
            else:  # cpu
                model = AutoModelForImageTextToText.from_pretrained(
                    model_id,
                    token=token,
                    cache_dir=cache_dir,
                    torch_dtype=torch.float32,
                )

            model.eval()
            _medgemma_model = model
            _medgemma_processor = processor
            logger.info(f"MedGemma loaded successfully on {device}")

        except Exception as exc:
            logger.warning(f"MedGemma failed to load: {exc}")
            _medgemma_model = None
            _medgemma_processor = None
        finally:
            _medgemma_loaded = True

    return _medgemma_model, _medgemma_processor


def get_medsiglip() -> Tuple[Optional[Any], Optional[Any]]:
    """
    Return (model, processor) for MedSigLIP, loading on first call.

    MedSigLIP is a SigLIP-style vision-language model (AutoModel).
    Uses .to(device) for all backends including MPS.
    """
    global _medsiglip_model, _medsiglip_processor, _medsiglip_loaded

    if _medsiglip_loaded:
        return _medsiglip_model, _medsiglip_processor

    with _lock:
        if _medsiglip_loaded:
            return _medsiglip_model, _medsiglip_processor

        try:
            from config import settings
            if settings.MEDSIGLIP_MODE == "disabled":
                logger.info("MedSigLIP disabled by config (MEDSIGLIP_MODE=disabled)")
                return None, None

            import torch
            from transformers import AutoProcessor, AutoModel

            model_id = settings.MEDSIGLIP_MODEL_ID
            cache_dir = settings.MODEL_CACHE_DIR or None
            device = _get_device()
            token = settings.HF_TOKEN or None
            dtype = torch.float16 if device in ("cuda", "mps") else torch.float32

            logger.info(f"Loading MedSigLIP '{model_id}' on device={device} ...")

            processor = AutoProcessor.from_pretrained(
                model_id,
                token=token,
                cache_dir=cache_dir,
            )

            model = AutoModel.from_pretrained(
                model_id,
                token=token,
                cache_dir=cache_dir,
                torch_dtype=dtype,
            ).to(device)

            model.eval()
            _medsiglip_model = model
            _medsiglip_processor = processor
            logger.info(f"MedSigLIP loaded successfully on {device}")

        except Exception as exc:
            logger.warning(f"MedSigLIP failed to load: {exc}")
            _medsiglip_model = None
            _medsiglip_processor = None
        finally:
            _medsiglip_loaded = True

    return _medsiglip_model, _medsiglip_processor


def get_medasr() -> Optional[Any]:
    """
    Return the MedASR ASR pipeline, loading on first call.

    MedASR is a Conformer-based ASR model fine-tuned on medical audio.
    Requires transformers >= 5.0.0.
    """
    global _medasr_pipeline, _medasr_loaded

    if _medasr_loaded:
        return _medasr_pipeline

    with _lock:
        if _medasr_loaded:
            return _medasr_pipeline

        try:
            from config import settings
            if settings.MEDASR_MODE == "disabled":
                logger.info("MedASR disabled by config (MEDASR_MODE=disabled)")
                return None

            import torch
            from transformers import pipeline

            model_id = settings.MEDASR_MODEL_ID
            cache_dir = settings.MODEL_CACHE_DIR or None
            device = _get_device()
            token = settings.HF_TOKEN or None
            dtype = torch.float16 if device in ("cuda", "mps") else torch.float32

            logger.info(f"Loading MedASR '{model_id}' on device={device} ...")

            # pipeline 'device' param: int (cuda index), "mps", or -1 (cpu)
            if device == "cuda":
                device_arg: Any = 0
            elif device == "mps":
                device_arg = "mps"
            else:
                device_arg = -1

            pipe = pipeline(
                "automatic-speech-recognition",
                model=model_id,
                token=token,
                cache_dir=cache_dir,
                device=device_arg,
                torch_dtype=dtype,
            )

            _medasr_pipeline = pipe
            logger.info(f"MedASR loaded successfully on {device}")

        except Exception as exc:
            logger.warning(f"MedASR failed to load: {exc}")
            _medasr_pipeline = None
        finally:
            _medasr_loaded = True

    return _medasr_pipeline


def preload_all_models() -> None:
    """
    Trigger background preloading of all models at startup.

    Runs in a daemon thread so it doesn't block the server startup.
    First requests after startup will still be fast if models are cached.
    """
    def _load() -> None:
        logger.info("Background model preload started ...")
        get_medgemma()
        get_medsiglip()
        get_medasr()
        logger.info("Background model preload complete")

    t = threading.Thread(target=_load, daemon=True, name="ai-model-preloader")
    t.start()


def get_model_status() -> dict:
    """Return loading/availability status for all three models."""
    return {
        "medgemma": {
            "loaded": _medgemma_loaded,
            "available": _medgemma_model is not None,
        },
        "medsiglip": {
            "loaded": _medsiglip_loaded,
            "available": _medsiglip_model is not None,
        },
        "medasr": {
            "loaded": _medasr_loaded,
            "available": _medasr_pipeline is not None,
        },
        "device": _get_device(),
    }
