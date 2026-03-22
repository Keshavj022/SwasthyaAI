#!/usr/bin/env python3
"""
One-time script to download all AI models from Hugging Face.

Run from the backend directory:

    python scripts/download_models.py

or with a token:

    HF_TOKEN=hf_... python scripts/download_models.py

Models downloaded:
  - google/medgemma-1.5-4b-it  (MedGemma — text + image generation)
  - google/medsiglip-448       (MedSigLIP — zero-shot image classification)
  - google/medasr              (MedASR — medical speech-to-text)

The models are cached in ~/.cache/huggingface by default (standard HF behaviour).
Override with MODEL_CACHE_DIR in .env or the --cache-dir flag.

Requirements:
  pip install transformers>=5.0.0 huggingface_hub torch torchvision
  pip install librosa soundfile   # for MedASR audio support
"""

import argparse
import sys
import os
from pathlib import Path

# Allow importing from the parent backend directory
sys.path.insert(0, str(Path(__file__).parent.parent))


def _load_settings():
    """Try to load .env settings; fall back to environment variables."""
    try:
        from config import settings
        return settings
    except Exception:
        return None


def download_medgemma(model_id: str, token: str | None, cache_dir: str | None) -> bool:
    """Download MedGemma (AutoModelForImageTextToText)."""
    print(f"\n[1/3] Downloading MedGemma: {model_id}")
    try:
        from transformers import AutoProcessor, AutoModelForImageTextToText
        import torch

        print("  → Downloading processor …")
        AutoProcessor.from_pretrained(model_id, token=token, cache_dir=cache_dir)

        print("  → Downloading model weights (this may take several minutes) …")
        AutoModelForImageTextToText.from_pretrained(
            model_id,
            token=token,
            cache_dir=cache_dir,
            torch_dtype=torch.float16,
        )
        print("  ✓ MedGemma downloaded successfully")
        return True
    except Exception as exc:
        print(f"  ✗ MedGemma download failed: {exc}")
        return False


def download_medsiglip(model_id: str, token: str | None, cache_dir: str | None) -> bool:
    """Download MedSigLIP (AutoModel)."""
    print(f"\n[2/3] Downloading MedSigLIP: {model_id}")
    try:
        from transformers import AutoProcessor, AutoModel
        import torch

        print("  → Downloading processor …")
        AutoProcessor.from_pretrained(model_id, token=token, cache_dir=cache_dir)

        print("  → Downloading model weights …")
        AutoModel.from_pretrained(
            model_id,
            token=token,
            cache_dir=cache_dir,
            torch_dtype=torch.float16,
        )
        print("  ✓ MedSigLIP downloaded successfully")
        return True
    except Exception as exc:
        print(f"  ✗ MedSigLIP download failed: {exc}")
        return False


def download_medasr(model_id: str, token: str | None, cache_dir: str | None) -> bool:
    """Download MedASR (ASR pipeline)."""
    print(f"\n[3/3] Downloading MedASR: {model_id}")
    try:
        from transformers import pipeline
        import torch

        print("  → Downloading ASR pipeline (processor + model) …")
        pipeline(
            "automatic-speech-recognition",
            model=model_id,
            token=token,
            cache_dir=cache_dir,
            torch_dtype=torch.float32,
            device=-1,  # CPU for download
        )
        print("  ✓ MedASR downloaded successfully")
        return True
    except Exception as exc:
        print(f"  ✗ MedASR download failed: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Download SwasthyaAI AI models from Hugging Face")
    parser.add_argument("--token", default=None, help="Hugging Face access token (or set HF_TOKEN env var)")
    parser.add_argument("--cache-dir", default=None, help="Directory to cache models (default: ~/.cache/huggingface)")
    parser.add_argument("--skip-medgemma", action="store_true", help="Skip MedGemma download")
    parser.add_argument("--skip-medsiglip", action="store_true", help="Skip MedSigLIP download")
    parser.add_argument("--skip-medasr", action="store_true", help="Skip MedASR download")
    args = parser.parse_args()

    settings = _load_settings()

    # Resolve token: CLI > env > .env settings
    token = (
        args.token
        or os.environ.get("HF_TOKEN")
        or (settings.HF_TOKEN if settings and settings.HF_TOKEN else None)
    )
    if not token:
        print("Warning: No HF_TOKEN found. Downloads of gated models will fail.")
        print("  Set HF_TOKEN in .env, as an env var, or pass --token <your_token>\n")

    # Resolve model IDs from settings or defaults
    medgemma_id = getattr(settings, "MEDGEMMA_MODEL_ID", "google/medgemma-1.5-4b-it") if settings else "google/medgemma-1.5-4b-it"
    medsiglip_id = getattr(settings, "MEDSIGLIP_MODEL_ID", "google/medsiglip-448") if settings else "google/medsiglip-448"
    medasr_id = getattr(settings, "MEDASR_MODEL_ID", "google/medasr") if settings else "google/medasr"

    # Resolve cache dir: CLI > .env settings
    cache_dir = (
        args.cache_dir
        or (settings.MODEL_CACHE_DIR if settings and settings.MODEL_CACHE_DIR else None)
    )

    print("=== SwasthyaAI Model Downloader ===")
    print(f"Cache dir: {cache_dir or '~/.cache/huggingface (default)'}")
    print(f"Token:     {'provided' if token else 'NOT provided (gated models will fail)'}")

    results = {}

    if not args.skip_medgemma:
        results["MedGemma"] = download_medgemma(medgemma_id, token, cache_dir)
    else:
        print("\n[1/3] Skipping MedGemma")

    if not args.skip_medsiglip:
        results["MedSigLIP"] = download_medsiglip(medsiglip_id, token, cache_dir)
    else:
        print("\n[2/3] Skipping MedSigLIP")

    if not args.skip_medasr:
        results["MedASR"] = download_medasr(medasr_id, token, cache_dir)
    else:
        print("\n[3/3] Skipping MedASR")

    # Summary
    print("\n=== Download Summary ===")
    all_ok = True
    for name, ok in results.items():
        status = "✓ OK" if ok else "✗ FAILED"
        print(f"  {name}: {status}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\nAll models downloaded. Start the server with:")
        print("  cd backend && uvicorn main:app --host 127.0.0.1 --port 8000\n")
    else:
        print("\nSome downloads failed. Check errors above.")
        print("Common causes:")
        print("  - Model is gated: accept licence on huggingface.co and provide HF_TOKEN")
        print("  - Model ID changed: update MEDGEMMA_MODEL_ID / MEDSIGLIP_MODEL_ID / MEDASR_MODEL_ID in .env")
        print("  - transformers version too old: pip install 'transformers>=5.0.0'\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
