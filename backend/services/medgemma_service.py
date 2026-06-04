"""
Thin MedGemma inference wrapper (text + multimodal image+text).

Used by the clinical-reasoning agents (communication, diagnostic, image,
voice, drug-info fallback, health-support). All functions return a clear,
labelled stub result with ``stub_mode=True`` when the model is not loaded —
they never fabricate authoritative medical findings.

Public API:
    generate_text(prompt, system_prompt=None, image=None, max_new_tokens=None)
        -> {"text": str, "stub_mode": bool, ...}
    generate_structured(prompt, output_schema, system_prompt=None, max_new_tokens=None)
        -> {"data": dict|None, "stub_mode": bool, "raw": str|None}
"""

import json
import logging
from typing import Any, Dict, Optional

from config import settings
from services.model_loader import get_medgemma

logger = logging.getLogger(__name__)

MEDICAL_DISCLAIMER = (
    "This is AI-generated clinical decision support only. It does not replace "
    "professional medical advice, diagnosis, or treatment. Always consult a "
    "qualified healthcare professional."
)

STUB_NOTE = (
    "AI model not loaded — this is non-authoritative demo output. Download the "
    "medical models and enable them to receive real AI-generated analysis."
)

_SYSTEM_PROMPT = (
    "You are SwasthyaAI, a medical AI assistant providing clinical decision "
    "support.\n"
    "RULES YOU MUST ALWAYS FOLLOW:\n"
    "1. Provide decision SUPPORT only — never make definitive diagnoses.\n"
    "2. For emergencies (chest pain, difficulty breathing, unconsciousness, "
    "stroke symptoms), say clearly: go to the emergency room or call emergency "
    "services immediately.\n"
    "3. Never prescribe medications or specific doses.\n"
    "4. Express appropriate uncertainty: use 'may indicate', 'could suggest', "
    "'a doctor should confirm'.\n"
    "5. Keep language simple and clear.\n"
)


def is_available() -> bool:
    """True when the real MedGemma weights are loaded."""
    model, _ = get_medgemma()
    return model is not None


def _stub_text(reason: str = "") -> Dict[str, Any]:
    return {
        "text": "",
        "stub_mode": True,
        "model": "stub",
        "note": STUB_NOTE,
        "disclaimer": MEDICAL_DISCLAIMER,
    }


def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    image: Optional[Any] = None,
    max_new_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run MedGemma text (or image+text) generation.

    Returns a dict that always carries ``stub_mode``:
        {"text": str, "stub_mode": bool, "model": str, "disclaimer": str,
         "note": str?}
    When the model is not loaded, ``text`` is empty and ``stub_mode`` is True;
    callers must render their own structured stub rather than treating an empty
    string as a real answer.
    """
    model, processor = get_medgemma()
    if model is None or processor is None:
        return _stub_text("model_not_loaded")

    try:
        import torch

        sys_prompt = system_prompt or _SYSTEM_PROMPT
        user_content = []
        if image is not None:
            user_content.append({"type": "image", "image": image})
        user_content.append({"type": "text", "text": prompt})
        messages = [
            {"role": "system", "content": [{"type": "text", "text": sys_prompt}]},
            {"role": "user", "content": user_content},
        ]

        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(model.device)

        input_len = inputs["input_ids"].shape[-1]
        tokens = max_new_tokens or settings.MEDGEMMA_MAX_NEW_TOKENS
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=tokens, do_sample=False)
        new_tokens = output[0][input_len:]
        text = processor.decode(new_tokens, skip_special_tokens=True).strip()

        return {
            "text": text,
            "stub_mode": False,
            "model": settings.MEDGEMMA_REPO_ID,
            "disclaimer": MEDICAL_DISCLAIMER,
        }
    except Exception as exc:
        logger.error(f"MedGemma inference error: {exc}")
        return _stub_text(f"inference_error: {exc}")


def generate_structured(
    prompt: str,
    output_schema: Dict[str, Any],
    system_prompt: Optional[str] = None,
    max_new_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Ask MedGemma to return a JSON object matching ``output_schema``.

    Returns:
        {"data": dict|None, "stub_mode": bool, "raw": str|None, "model": str,
         "disclaimer": str}
    ``data`` is None (with stub_mode True) when the model is unavailable OR the
    output could not be parsed as JSON.
    """
    schema_str = json.dumps(output_schema, indent=2)
    full_prompt = (
        f"{prompt}\n\n"
        "Respond ONLY with a valid JSON object matching this schema exactly "
        "(no markdown fences, no prose outside the JSON):\n"
        f"{schema_str}"
    )
    result = generate_text(
        full_prompt,
        system_prompt=system_prompt,
        max_new_tokens=max_new_tokens or 1024,
    )
    if result.get("stub_mode"):
        return {
            "data": None,
            "stub_mode": True,
            "raw": None,
            "model": "stub",
            "note": STUB_NOTE,
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    raw = result.get("text", "")
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= 0:
            raise ValueError("no JSON object in response")
        parsed = json.loads(raw[start:end])
        return {
            "data": parsed,
            "stub_mode": False,
            "raw": raw,
            "model": settings.MEDGEMMA_REPO_ID,
            "disclaimer": MEDICAL_DISCLAIMER,
        }
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(f"MedGemma structured parse failed: {exc}; raw={raw[:200]!r}")
        # Real model ran but produced unparseable output: still mark stub so the
        # caller does NOT present unstructured text as an authoritative result.
        return {
            "data": None,
            "stub_mode": True,
            "raw": raw,
            "model": settings.MEDGEMMA_REPO_ID,
            "note": "Model output could not be parsed as structured JSON.",
            "disclaimer": MEDICAL_DISCLAIMER,
        }
