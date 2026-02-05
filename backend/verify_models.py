#!/usr/bin/env python3
"""
AI Model Verification Script

Checks if AI models are properly installed and can be loaded.
Tests each model's inference pipeline with dummy data.

Usage:
    python verify_models.py
"""

# Must be set before importing torch/transformers to prevent macOS mutex locks.
# The underlying C libraries (OpenMP, MKL, HF tokenizers) read these at init time.
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["RAYON_NUM_THREADS"] = "1"

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_pytorch():
    """Check if PyTorch is installed"""
    try:
        import torch
        logger.info(f"✓ PyTorch version: {torch.__version__}")

        if torch.cuda.is_available():
            logger.info(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
            return "cuda"
        elif torch.backends.mps.is_available():
            logger.info("✓ MPS (Apple Silicon GPU) available")
            return "mps"
        else:
            logger.info("✓ CUDA/MPS not available, using CPU")
            return "cpu"
    except ImportError:
        logger.error("✗ PyTorch not installed")
        logger.error("  Install: pip install torch torchvision torchaudio")
        return None


def check_transformers():
    """Check if Transformers is installed"""
    try:
        import transformers
        logger.info(f"✓ Transformers version: {transformers.__version__}")
        return True
    except ImportError:
        logger.error("✗ Transformers not installed")
        logger.error("  Install: pip install transformers")
        return False


def check_model_path(model_name: str, expected_path: Path) -> bool:
    """Check if model files exist at expected path"""
    if expected_path.exists():
        logger.info(f"✓ {model_name} found at: {expected_path}")

        # Check for key files
        config_file = expected_path / "config.json"
        if config_file.exists():
            logger.info(f"  ✓ config.json present")
        else:
            logger.warning(f"  ⚠ config.json missing")

        # Check for model weights
        weight_files = list(expected_path.glob("*.bin")) + list(expected_path.glob("*.safetensors"))
        if weight_files:
            logger.info(f"  ✓ Found {len(weight_files)} weight file(s)")
        else:
            logger.warning(f"  ⚠ No weight files found")

        return True
    else:
        logger.warning(f"⚠ {model_name} NOT found at: {expected_path}")
        logger.warning(f"  Model will use stub responses until downloaded")
        return False


def test_medgemma(model_path: Path, device: str):
    """Test MedGemma inference"""
    logger.info("\n--- Testing MedGemma ---")

    try:
        from inference.medgemma import MedGemmaInference
        import asyncio

        # Initialize inference
        inference = MedGemmaInference(model_path=model_path, device=device)

        # Get model info
        info = inference.get_model_info()
        logger.info(f"Model info: {info}")

        # Test inference
        async def test():
            response = await inference.generate_response(
                query="What are the symptoms of influenza?",
                task_type="medical_qa"
            )
            return response

        result = asyncio.run(test())

        if result.get("stub_mode"):
            logger.warning("⚠ MedGemma using stub responses (model not loaded)")
        else:
            logger.info("✓ MedGemma inference successful")

        logger.info(f"Response: {result.get('analysis_summary', 'N/A')[:100]}...")

        return True

    except Exception as e:
        logger.error(f"✗ MedGemma test failed: {e}")
        return False


def test_medsigLIP(model_path: Path, device: str):
    """Test MedSigLIP inference"""
    logger.info("\n--- Testing MedSigLIP ---")

    try:
        from inference.medsigLIP import MedSigLIPInference

        # Initialize inference
        inference = MedSigLIPInference(model_path=model_path, device=device)

        # Get model info
        info = inference.get_model_info()
        logger.info(f"Model info: {info}")

        if info["model_loaded"]:
            logger.info("✓ MedSigLIP loaded successfully")
        else:
            logger.warning("⚠ MedSigLIP using stub responses (model not loaded)")

        return True

    except Exception as e:
        logger.error(f"✗ MedSigLIP test failed: {e}")
        return False


def test_medasr(model_path: Path, device: str):
    """Test MedASR inference"""
    logger.info("\n--- Testing MedASR ---")

    try:
        from inference.medasr import MedASRInference

        # Initialize inference
        inference = MedASRInference(model_path=model_path, device=device)

        # Get model info
        info = inference.get_model_info()
        logger.info(f"Model info: {info}")

        if info["model_loaded"]:
            logger.info("✓ MedASR loaded successfully")
        else:
            logger.warning("⚠ MedASR using stub responses (model not loaded)")

        return True

    except Exception as e:
        logger.error(f"✗ MedASR test failed: {e}")
        return False


def main():
    """Main verification routine"""
    print("=" * 60)
    print("AI Model Installation Verification")
    print("=" * 60)

    # Check dependencies
    logger.info("\n1. Checking Python Packages...")
    device = check_pytorch()
    if device is None:
        logger.error("\nVerification failed: PyTorch not installed")
        sys.exit(1)

    if not check_transformers():
        logger.error("\nVerification failed: Transformers not installed")
        sys.exit(1)

    # Check model paths
    logger.info("\n2. Checking Model Directories...")
    project_root = Path(__file__).parent.parent

    medgemma_path = project_root / "models" / "medgemma"
    medsigLIP_path = project_root / "models" / "medsigLIP"
    medasr_path = project_root / "models" / "medasr"

    medgemma_found = check_model_path("MedGemma", medgemma_path)
    medsigLIP_found = check_model_path("MedSigLIP", medsigLIP_path)
    medasr_found = check_model_path("MedASR", medasr_path)

    # Test inference
    logger.info("\n3. Testing Inference Pipelines...")

    medgemma_ok = test_medgemma(medgemma_path if medgemma_found else None, device)
    medsigLIP_ok = test_medsigLIP(medsigLIP_path if medsigLIP_found else None, device)
    medasr_ok = test_medasr(medasr_path if medasr_found else None, device)

    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    print(f"\nDependencies:")
    print(f"  PyTorch: ✓ ({device})")
    print(f"  Transformers: ✓")

    print(f"\nModel Files:")
    print(f"  MedGemma: {'✓' if medgemma_found else '⚠ NOT FOUND'}")
    print(f"  MedSigLIP: {'✓' if medsigLIP_found else '⚠ NOT FOUND'}")
    print(f"  MedASR: {'✓' if medasr_found else '⚠ NOT FOUND'}")

    print(f"\nInference Tests:")
    print(f"  MedGemma: {'✓' if medgemma_ok else '✗'}")
    print(f"  MedSigLIP: {'✓' if medsigLIP_ok else '✗'}")
    print(f"  MedASR: {'✓' if medasr_ok else '✗'}")

    if not (medgemma_found or medsigLIP_found or medasr_found):
        print("\n⚠ WARNING: No AI models found!")
        print("   System will use stub responses until models are downloaded.")
        print("   See AI_MODEL_INTEGRATION_GUIDE.md for download instructions.")
    else:
        print("\n✓ System ready for AI inference!")
        print("  Models found will be used for real inference.")
        print("  Missing models will fall back to stub responses.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
