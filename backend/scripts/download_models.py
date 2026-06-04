#!/usr/bin/env python3
"""
One-time downloader for the three gated HAI-DEF models.

Run this ONCE while online (after accepting the model terms on Hugging Face and
setting HF_TOKEN). It caches the weights into MODELS_DIR so the app can run
fully offline afterwards. Safe to run repeatedly — already-downloaded files are
skipped by huggingface_hub.

Prerequisites
-------------
1. Accept the Health AI Developer Foundations terms for EACH repo:
     - https://huggingface.co/google/medgemma-4b-it      (or google/medgemma-1.5-4b-it)
     - https://huggingface.co/google/medsiglip-448
     - https://huggingface.co/google/medasr               (gated; advanced voice)
   Whisper (openai/whisper-large-v3-turbo, the default voice model) is NOT gated.
2. Create a read-scope HF token and set it in backend/.env as HF_TOKEN=hf_...
   (or export HF_TOKEN in your shell).

Usage
-----
    python backend/scripts/download_models.py
    # download a single model:
    python backend/scripts/download_models.py --only medgemma
    python backend/scripts/download_models.py --only medsiglip,medasr

Disk: ~12 GB for the full default set (MedGemma ~9 GB, MedSigLIP ~3.6 GB,
Whisper turbo ~1.6 GB). google/medasr is ~1.4 GB if used.
"""

import argparse
import os
import sys
from pathlib import Path

# Make `config` importable (scripts/ is one level below backend/).
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


def _load_settings():
    """Import app settings, but defeat the offline env so we CAN download."""
    # config.py exports HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE at import time;
    # we must clear them BEFORE huggingface_hub is used so downloads work.
    from config import settings  # noqa: E402  (deferred on purpose)

    for var in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        os.environ.pop(var, None)
    return settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Download HAI-DEF model weights.")
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated subset: medgemma,medsiglip,medasr (default: all)",
    )
    args = parser.parse_args()

    settings = _load_settings()

    token = settings.HF_TOKEN or os.getenv("HF_TOKEN", "")
    if not token:
        print("ERROR: HF_TOKEN is not set.")
        print("  -> Add HF_TOKEN=hf_... to backend/.env (read scope) and retry.")
        print("  -> Get one at https://huggingface.co/settings/tokens")
        return 1

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub is not installed.")
        print("  -> pip install 'huggingface_hub[cli]'")
        return 1

    models_dir = Path(settings.MODELS_DIR)
    hf_home = Path(settings.HF_HOME)
    models_dir.mkdir(parents=True, exist_ok=True)
    hf_home.mkdir(parents=True, exist_ok=True)

    # (key, repo_id, friendly name, local snapshot dir, approx size)
    all_models = [
        ("medgemma", settings.MEDGEMMA_REPO_ID, "MedGemma (text+image)",
         settings.MEDGEMMA_MODEL_PATH, "~9 GB"),
        ("medsiglip", settings.MEDSIGLIP_REPO_ID, "MedSigLIP (image classifier)",
         settings.MEDSIGCLIP_MODEL_PATH, "~3.6 GB"),
        ("medasr", settings.MEDASR_REPO_ID, "ASR / voice (Whisper or MedASR)",
         settings.MEDASR_MODEL_PATH, "~1.6 GB"),
    ]

    wanted = {k.strip().lower() for k in args.only.split(",") if k.strip()}
    selected = [m for m in all_models if not wanted or m[0] in wanted]
    if wanted and not selected:
        print(f"ERROR: --only '{args.only}' matched no models. "
              f"Choose from: {', '.join(m[0] for m in all_models)}")
        return 1

    print(f"\nDownloading {len(selected)} model(s) into snapshot dirs under {models_dir}")
    print(f"HF cache (HF_HOME): {hf_home}\n")

    failures = 0
    for key, repo_id, name, local_dir, size in selected:
        local_dir = Path(local_dir)
        print(f"==> {name}  [{repo_id}]  ({size})")
        print(f"    target: {local_dir}")
        try:
            local_dir.mkdir(parents=True, exist_ok=True)
            snapshot_download(
                repo_id=repo_id,
                token=token,
                local_dir=str(local_dir),
                cache_dir=str(hf_home),
            )
            print(f"    OK — {name} ready.\n")
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures += 1
            print(f"    FAILED: {exc}")
            print(f"    Hint: accept the terms at https://huggingface.co/{repo_id} "
                  f"with the SAME account that owns HF_TOKEN.\n")

    if failures:
        print(f"Completed with {failures} failure(s). "
              f"Re-run after accepting terms / checking your token.")
        return 1

    print("All requested models downloaded.")
    print("Enable them in backend/.env (MEDGEMMA_MODE=true, etc.) and restart the API.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
