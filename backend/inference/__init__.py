"""
AI Model Inference Module

Provides inference interfaces for:
- MedGemma: Medical text understanding & clinical reasoning
- MedSigLIP: Medical image analysis
- MedASR: Medical speech-to-text

All models support CPU/GPU fallback and graceful degradation to stubs.
"""

from .base import BaseInference
from .medgemma import MedGemmaInference
from .medsigLIP import MedSigLIPInference
from .medasr import MedASRInference

__all__ = [
    "BaseInference",
    "MedGemmaInference",
    "MedSigLIPInference",
    "MedASRInference",
]
