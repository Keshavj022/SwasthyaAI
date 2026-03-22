"""
MedGemma inference service.

Provides text-only and multimodal (text + image) generation via the locally
loaded google/medgemma-1.5-4b-it model.

All functions return None on failure so callers can degrade gracefully to stubs.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_text(
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
) -> Optional[str]:
    """
    Generate a text response from MedGemma given a plain-text prompt.

    Args:
        prompt: The full prompt string (caller is responsible for framing).
        max_new_tokens: Maximum tokens to generate.
        temperature: Sampling temperature (0 = greedy).

    Returns:
        Generated text string, or None if the model is unavailable.
    """
    try:
        from services.model_loader import get_medgemma
        import torch

        model, processor = get_medgemma()
        if model is None or processor is None:
            return None

        messages = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )

        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else None,
                do_sample=temperature > 0,
            )

        # Decode only the newly generated tokens (skip the input prompt)
        input_len = inputs["input_ids"].shape[-1]
        generated_ids = outputs[0][input_len:]
        text = processor.decode(generated_ids, skip_special_tokens=True)
        return text.strip()

    except Exception as exc:
        logger.warning(f"MedGemma text generation failed: {exc}")
        return None


def generate_with_image(
    prompt: str,
    image_path: str,
    max_new_tokens: int = 512,
) -> Optional[str]:
    """
    Generate a text response from MedGemma given a prompt and a local image file.

    Args:
        prompt: Text prompt to accompany the image.
        image_path: Absolute path to the image file (JPEG/PNG/etc.).
        max_new_tokens: Maximum tokens to generate.

    Returns:
        Generated text string, or None if the model is unavailable.
    """
    try:
        from services.model_loader import get_medgemma
        import torch
        from PIL import Image

        model, processor = get_medgemma()
        if model is None or processor is None:
            return None

        image = Image.open(image_path).convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )

        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
            )

        input_len = inputs["input_ids"].shape[-1]
        generated_ids = outputs[0][input_len:]
        text = processor.decode(generated_ids, skip_special_tokens=True)
        return text.strip()

    except Exception as exc:
        logger.warning(f"MedGemma image+text generation failed: {exc}")
        return None
