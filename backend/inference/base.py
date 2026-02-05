"""
Base Inference Class

Provides common functionality for all AI model inference:
- Model loading with CPU/GPU fallback
- Error handling and graceful degradation
- Lazy loading (models loaded on first use)
- Offline-first enforcement
"""

# Must be set before importing torch/transformers to prevent macOS mutex locks.
# The underlying C libraries (OpenMP, MKL, HF tokenizers) read these at init time.
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
os.environ.setdefault("RAYON_NUM_THREADS", "1")

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseInference(ABC):
    """Base class for all model inference"""

    def __init__(self, model_path: Optional[Path] = None, device: str = "auto"):
        """
        Initialize inference engine

        Args:
            model_path: Path to model weights (if None, uses stub)
            device: 'cpu', 'cuda', 'mps', or 'auto' (auto-detect)
        """
        self.model_path = model_path
        self.device = self._determine_device(device)
        self.model = None
        self.tokenizer = None
        self.processor = None
        self._model_loaded = False

        logger.info(f"Initialized {self.__class__.__name__} with device={self.device}")

    def _determine_device(self, device: str) -> str:
        """Determine which device to use for inference (CUDA → MPS → CPU)"""
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                if torch.backends.mps.is_available():
                    return "mps"
                return "cpu"
            except ImportError:
                logger.warning("PyTorch not installed, defaulting to CPU")
                return "cpu"
        return device

    def _load_model(self) -> bool:
        """
        Load model weights (lazy loading on first inference)

        Returns:
            bool: True if model loaded successfully, False if using stub
        """
        if self._model_loaded:
            return True

        if self.model_path is None or not self.model_path.exists():
            logger.warning(
                f"{self.__class__.__name__}: Model not found at {self.model_path}. "
                "Using stub responses. Download model to enable real inference."
            )
            return False

        try:
            logger.info(f"Loading model from {self.model_path}...")
            self._load_model_weights()
            self._model_loaded = True
            logger.info(f"Model loaded successfully on {self.device}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}. Falling back to stub responses.")
            return False

    @abstractmethod
    def _load_model_weights(self):
        """Load actual model weights (implemented by subclasses)"""
        pass

    @abstractmethod
    def _generate_stub_response(self, **kwargs) -> Dict[str, Any]:
        """Generate stub response when model unavailable (implemented by subclasses)"""
        pass

    def is_model_available(self) -> bool:
        """Check if real model is loaded"""
        return self._model_loaded

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model"""
        return {
            "model_class": self.__class__.__name__,
            "model_path": str(self.model_path) if self.model_path else None,
            "device": self.device,
            "model_loaded": self._model_loaded,
            "using_stub": not self._model_loaded
        }
