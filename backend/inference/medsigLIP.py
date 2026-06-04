"""
MedSigLIP Inference

Provides inference for medical image analysis using Google's MedSigLIP model
(medical fine-tune of SigLIP vision-language model).

Model: google/medsigLIP
Use cases:
- Medical image classification
- Radiology report generation
- Medical image question answering
- Zero-shot medical image analysis
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from PIL import Image

from .base import BaseInference

logger = logging.getLogger(__name__)


class MedSigLIPInference(BaseInference):
    """MedSigLIP model inference for medical image analysis"""

    # Common medical image modalities
    SUPPORTED_MODALITIES = [
        "x-ray", "ct", "mri", "ultrasound", "pathology",
        "dermatology", "ophthalmology", "endoscopy"
    ]

    def service_available(self) -> bool:
        """Real MedSigLIP is served via the central service layer."""
        try:
            from services import medsiglip_service
            return medsiglip_service.is_available()
        except Exception:
            return False

    def _load_model_weights(self):
        """Load MedSigLIP model weights"""
        try:
            import torch
            from transformers import AutoModel, AutoProcessor

            logger.info(f"Loading MedSigLIP from {self.model_path}")

            self.processor = AutoProcessor.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )

            logger.info("Loading model weights (this may take a moment)...")
            model_dtype = torch.float32 if self.device == "cpu" else torch.float16
            self.model = AutoModel.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                dtype=model_dtype,
                low_cpu_mem_usage=True  # Helps with memory and mutex issues on macOS
            )

            logger.info(f"Moving model to {self.device} ({model_dtype})...")
            self.model.to(self.device)
            self.model.eval()

        except Exception as e:
            logger.error(f"Failed to load MedSigLIP: {e}")
            raise

    async def analyze_image(
        self,
        image_path: Union[str, Path],
        modality: str,
        clinical_context: Optional[str] = None,
        questions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze medical image using MedSigLIP

        Args:
            image_path: Path to medical image file
            modality: Type of medical image (x-ray, ct, mri, etc.)
            clinical_context: Optional clinical information
            questions: Optional specific questions about the image

        Returns:
            Dict with image analysis, findings, confidence (carries stub_mode)
        """
        try:
            from services import medsiglip_service

            image = Image.open(image_path).convert("RGB")
            svc = medsiglip_service.classify_image(image, modality=modality)
            if not svc.get("stub_mode"):
                findings = {
                    "modality": modality,
                    "top_finding": svc.get("top_finding"),
                    "is_abnormal": svc.get("is_abnormal"),
                    "key_findings": [
                        f"{f['label']} ({f['probability']:.1%})"
                        for f in svc.get("all_findings", [])[:5]
                    ],
                    "confidence": svc.get("confidence", 0.0),
                    "all_findings": svc.get("all_findings", []),
                    "clinical_context": clinical_context,
                    "disclaimer": svc.get("disclaimer"),
                    "model": svc.get("model"),
                    "stub_mode": False,
                }
                return self._enforce_safety(findings, modality)
        except Exception as e:
            logger.error(f"MedSigLIP service analysis failed: {e}")

        return self._generate_stub_response(
            modality=modality,
            clinical_context=clinical_context,
        )

    async def classify_image(
        self,
        image_path: Union[str, Path],
        candidates: List[str],
        modality: str
    ) -> Dict[str, Any]:
        """
        Zero-shot medical image classification

        Args:
            image_path: Path to medical image
            candidates: List of possible conditions/findings
            modality: Image modality

        Returns:
            Dict with ranked classifications and confidences (carries stub_mode)
        """
        # Route through the central MedSigLIP service. It uses SIGMOID scoring
        # (not softmax) and padding="max_length" per the SigLIP spec, returning
        # a clearly-labelled stub when the real model is not loaded.
        try:
            from services import medsiglip_service

            image = Image.open(image_path).convert("RGB")
            svc = medsiglip_service.classify_image(
                image, modality=modality, labels=candidates
            )
            if not svc.get("stub_mode"):
                results = [
                    {
                        "condition": f["label"],
                        "confidence": f["probability"],
                        "rank": i + 1,
                    }
                    for i, f in enumerate(svc.get("all_findings", []))
                ]
                return {
                    "classifications": results,
                    "modality": modality,
                    "top_finding": svc.get("top_finding"),
                    "is_abnormal": svc.get("is_abnormal"),
                    "disclaimer": svc.get("disclaimer"),
                    "model": svc.get("model"),
                    "stub_mode": False,
                }
        except Exception as e:
            logger.error(f"MedSigLIP service classification failed: {e}")

        return self._generate_stub_classification(candidates)

    def _build_image_prompt(
        self,
        modality: str,
        clinical_context: Optional[str],
        questions: Optional[List[str]]
    ) -> str:
        """Build prompt for image analysis"""

        prompt = f"Analyze this {modality} image."

        if clinical_context:
            prompt += f"\nClinical context: {clinical_context}"

        if questions:
            prompt += "\nAnswer these questions: " + "; ".join(questions)

        prompt += "\nProvide key findings, but do not provide definitive diagnoses."

        return prompt

    def _extract_findings(self, outputs, modality: str) -> Dict[str, Any]:
        """Extract findings from model output"""

        # This is model-specific and depends on MedSigLIP's output format
        # Placeholder implementation

        return {
            "modality": modality,
            "key_findings": [
                "Image analysis completed",
                "Further review by radiologist recommended"
            ],
            "abnormalities_detected": [],
            "confidence": 0.7,
            "quality_assessment": "Adequate for interpretation",
            "recommended_follow_up": [
                "Radiologist review required",
                "Correlate with clinical findings"
            ],
            "disclaimer": "This is decision support only. Images must be reviewed by qualified radiologists/clinicians."
        }

    def _enforce_safety(self, findings: Dict[str, Any], modality: str) -> Dict[str, Any]:
        """Ensure image analysis complies with safety requirements"""

        # Real model output: mark non-stub unless a caller already set it.
        findings.setdefault("stub_mode", False)

        # Always include disclaimer
        if "disclaimer" not in findings:
            findings["disclaimer"] = "This is decision support only. Images must be reviewed by qualified radiologists/clinicians."

        # Ensure confidence score
        if "confidence" not in findings:
            findings["confidence"] = 0.5
        else:
            findings["confidence"] = max(0.0, min(1.0, findings["confidence"]))

        # Add modality if missing
        if "modality" not in findings:
            findings["modality"] = modality

        return findings

    def _generate_stub_response(
        self,
        modality: str,
        clinical_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate stub response when model unavailable"""

        return {
            "modality": modality,
            "key_findings": [
                f"{modality.upper()} image received",
                "AI-based analysis not available (model not loaded)",
                "Image should be reviewed by qualified radiologist/clinician"
            ],
            "abnormalities_detected": [],
            "confidence": 0.2,
            "quality_assessment": "Unable to assess (AI model unavailable)",
            "recommended_follow_up": [
                "Immediate review by qualified radiologist required",
                "Correlate with clinical presentation",
                f"Consider additional {modality} views if clinically indicated"
            ],
            "clinical_context": clinical_context,
            "disclaimer": "This is decision support only. Images must be reviewed by qualified radiologists/clinicians.",
            "stub_mode": True
        }

    def _generate_stub_classification(self, candidates: List[str]) -> Dict[str, Any]:
        """Generate stub classification response"""

        return {
            "classifications": [
                {
                    "condition": condition,
                    "confidence": 1.0 / len(candidates),
                    "rank": i + 1
                }
                for i, condition in enumerate(candidates)
            ],
            "disclaimer": "This is decision support only. Images must be reviewed by qualified radiologists/clinicians.",
            "stub_mode": True
        }
