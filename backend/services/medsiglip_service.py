"""
Thin MedSigLIP wrapper: zero-shot medical image classification.

MedSigLIP is a SigLIP two-tower model. Per the reference:
  - probabilities come from torch.SIGMOID on logits_per_image (NOT softmax),
    because it was trained with a pairwise sigmoid loss — each (image, label)
    score is an independent 0..1 probability.
  - the processor MUST be called with padding="max_length" (training parity).
  - images are 448x448 RGB.

Returns a clearly-labelled stub (``stub_mode=True``) when the model is not
loaded; it never fabricates authoritative findings.

Public API:
    classify_image(image, modality="general", labels=None)
        -> {"top_finding", "confidence", "is_abnormal", "all_findings",
            "modality", "stub_mode", "disclaimer", ...}
    infer_modality(filename) -> str
"""

import logging
from typing import Any, Dict, List, Optional

from services.model_loader import get_medsiglip

logger = logging.getLogger(__name__)

IMAGING_DISCLAIMER = (
    "This AI image analysis is decision support only and is NOT a radiological "
    "diagnosis. All medical images must be reviewed by a qualified radiologist "
    "or specialist."
)

STUB_NOTE = (
    "AI image model not loaded — this is non-authoritative demo output. No real "
    "image classification was performed."
)

# Zero-shot label sets by imaging modality. Phrased as clinical descriptions
# (SigLIP convention). Keep prompts short (<= 64 text tokens).
LABEL_SETS: Dict[str, List[str]] = {
    "chest_xray": [
        "a chest x-ray showing normal clear lungs with no abnormality",
        "a chest x-ray showing pneumonia or pulmonary consolidation",
        "a chest x-ray showing pleural effusion",
        "a chest x-ray showing cardiomegaly or an enlarged heart",
        "a chest x-ray showing pneumothorax or a collapsed lung",
        "a chest x-ray showing pulmonary edema",
        "a chest x-ray showing a pulmonary mass or nodule",
    ],
    "dermatology": [
        "a photo of normal healthy skin with no lesion",
        "a skin photo with features of melanoma or malignant tumor",
        "a photo of a benign skin mole or seborrheic keratosis",
        "a skin photo showing a rash or inflammatory dermatitis",
        "a skin photo showing signs of infection or cellulitis",
        "a skin photo showing a wound, ulcer, or open sore",
    ],
    "histopathology": [
        "histopathology of normal tissue with no malignancy",
        "histopathology showing invasive carcinoma or malignant cells",
        "histopathology showing benign proliferative tissue",
        "histopathology showing inflammatory infiltrate",
        "histopathology showing dysplasia or precancerous changes",
    ],
    "ophthalmology": [
        "a normal fundus photograph with no abnormality",
        "a fundus photograph showing diabetic retinopathy",
        "a fundus photograph showing glaucomatous optic nerve damage",
        "a fundus photograph showing age-related macular degeneration",
        "a fundus photograph showing hypertensive retinopathy",
    ],
    "general": [
        "a normal medical image with no significant pathological finding",
        "a medical image showing a mild abnormality",
        "a medical image showing a significant abnormality requiring attention",
        "a medical image showing a critical or life-threatening finding",
    ],
}


def is_available() -> bool:
    """True when the real MedSigLIP weights are loaded."""
    model, _ = get_medsiglip()
    return model is not None


def infer_modality(filename: Optional[str]) -> str:
    """Guess imaging modality from a file name; defaults to 'general'."""
    name = (filename or "").lower()
    if any(k in name for k in ["xray", "x-ray", "cxr", "chest", "lung", "thorax"]):
        return "chest_xray"
    if any(k in name for k in ["derm", "skin", "lesion", "rash", "melanoma", "mole"]):
        return "dermatology"
    if any(k in name for k in ["path", "hist", "biopsy", "slide", "micro"]):
        return "histopathology"
    if any(k in name for k in ["fundus", "retina", "eye", "optic", "macula"]):
        return "ophthalmology"
    return "general"


def _stub(modality: str, labels: List[str]) -> Dict[str, Any]:
    return {
        "top_finding": None,
        "confidence": 0.0,
        "is_abnormal": None,
        "all_findings": [],
        "candidate_labels": labels,
        "modality": modality,
        "stub_mode": True,
        "model": "stub",
        "note": STUB_NOTE,
        "disclaimer": IMAGING_DISCLAIMER,
    }


def classify_image(
    image: Any,
    modality: str = "general",
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Zero-shot classify a medical image with MedSigLIP.

    Args:
        image: a PIL.Image.Image (any mode; converted to RGB internally).
        modality: key into LABEL_SETS (chest_xray | dermatology | histopathology
            | ophthalmology | general).
        labels: optional explicit candidate labels overriding the modality set.

    Returns a dict with per-label sigmoid probabilities sorted descending, plus
    ``stub_mode`` (True when the model is unavailable).
    """
    candidate_labels = labels or LABEL_SETS.get(modality, LABEL_SETS["general"])

    model, processor = get_medsiglip()
    if model is None or processor is None:
        return _stub(modality, candidate_labels)

    try:
        import torch
        from PIL import Image as PILImage

        device = next(model.parameters()).device
        rgb = image.convert("RGB").resize((448, 448), PILImage.BILINEAR)

        inputs = processor(
            text=candidate_labels,
            images=[rgb] * len(candidate_labels),
            padding="max_length",
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)

        # SigLIP: independent per-pair probabilities via sigmoid (NOT softmax).
        probs = torch.sigmoid(outputs.logits_per_image[0]).float().cpu().tolist()

        findings = sorted(
            (
                {"label": candidate_labels[i], "probability": float(probs[i])}
                for i in range(len(candidate_labels))
            ),
            key=lambda x: x["probability"],
            reverse=True,
        )
        top = findings[0]
        is_abnormal = "normal" not in top["label"].lower()

        return {
            "top_finding": top["label"],
            "confidence": top["probability"],
            "is_abnormal": is_abnormal,
            "all_findings": findings,
            "candidate_labels": candidate_labels,
            "modality": modality,
            "stub_mode": False,
            "model": "google/medsiglip-448",
            "disclaimer": IMAGING_DISCLAIMER,
        }
    except Exception as exc:
        logger.error(f"MedSigLIP inference error: {exc}")
        result = _stub(modality, candidate_labels)
        result["note"] = f"Image classification failed: {exc}"
        return result
