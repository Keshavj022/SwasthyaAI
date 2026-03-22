"""
MedSigLIP inference service.

Provides zero-shot medical image classification via the locally loaded
google/medsiglip-448 vision-language model.

Images are resized to 448x448 as required by MedSigLIP.
Label sets are curated per imaging modality to match clinical relevance.

All functions return None on failure so callers degrade gracefully to stubs.
"""

import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Zero-shot text label sets per imaging modality.
# These are fed to the model alongside the image; softmax scores are returned.
LABEL_SETS: Dict[str, List[str]] = {
    "chest_xray": [
        "normal chest X-ray",
        "pneumonia", "consolidation", "opacity", "infiltrate",
        "pleural effusion", "pneumothorax",
        "cardiomegaly", "pulmonary edema",
        "pulmonary nodule", "lung mass", "atelectasis",
    ],
    "ct_chest": [
        "normal chest CT",
        "pulmonary embolism", "consolidation", "ground glass opacity",
        "pleural effusion", "pneumothorax", "lung mass", "lymphadenopathy",
        "emphysema", "bronchiectasis",
    ],
    "ct_head": [
        "normal brain CT",
        "intracranial hemorrhage", "ischemic stroke infarct",
        "brain mass", "hydrocephalus", "cerebral edema", "subdural hematoma",
    ],
    "ct_abdomen": [
        "normal abdominal CT",
        "appendicitis", "bowel obstruction", "pneumoperitoneum",
        "liver mass", "kidney stone", "ascites", "pancreatitis",
    ],
    "mri_brain": [
        "normal brain MRI",
        "brain tumor", "multiple sclerosis", "ischemic infarct",
        "intracranial hemorrhage", "white matter changes", "demyelination",
    ],
    "dermatology": [
        "normal skin",
        "melanoma", "basal cell carcinoma", "squamous cell carcinoma",
        "benign melanocytic nevus", "atypical nevus", "seborrheic keratosis",
        "actinic keratosis", "dermatitis", "psoriasis",
    ],
    "pathology": [
        "normal tissue",
        "adenocarcinoma", "squamous cell carcinoma", "lymphoma",
        "inflammation", "necrosis", "fibrosis",
    ],
    "other": [
        "normal medical image",
        "abnormal finding",
        "requires specialist review",
    ],
}


def classify_image(
    image_path: str,
    modality: str,
    top_k: int = 5,
) -> Optional[List[Dict]]:
    """
    Zero-shot classify a medical image using MedSigLIP.

    Args:
        image_path: Absolute path to the image file.
        modality: One of the keys in LABEL_SETS (e.g. "chest_xray").
        top_k: Number of top labels to return.

    Returns:
        List of {"label": str, "score": float} dicts sorted by score desc,
        or None if the model is unavailable or the call fails.
    """
    try:
        from services.model_loader import get_medsiglip
        import torch
        from PIL import Image

        model, processor = get_medsiglip()
        if model is None or processor is None:
            return None

        labels = LABEL_SETS.get(modality, LABEL_SETS["other"])

        image = Image.open(image_path).convert("RGB")
        # MedSigLIP requires 448×448 input resolution
        image = image.resize((448, 448))

        inputs = processor(
            text=labels,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.inference_mode():
            outputs = model(**inputs)

        # logits_per_image: shape (1, num_labels) — similarity scores
        logits = outputs.logits_per_image
        probs = logits.softmax(dim=-1)[0]

        results = [
            {"label": label, "score": float(prob)}
            for label, prob in zip(labels, probs)
        ]
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    except Exception as exc:
        logger.warning(f"MedSigLIP classification failed: {exc}")
        return None
