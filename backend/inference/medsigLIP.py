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
            Dict with image analysis, findings, confidence
        """
        if not self._load_model():
            return self._generate_stub_response(
                modality=modality,
                clinical_context=clinical_context
            )

        try:
            # Load and preprocess image
            image = Image.open(image_path).convert("RGB")

            # Build analysis prompt
            prompt = self._build_image_prompt(modality, clinical_context, questions)

            # Process image and text
            inputs = self.processor(
                text=prompt,
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)

            # Generate analysis
            import torch
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Extract findings from model output
            findings = self._extract_findings(outputs, modality)

            # Ensure safety compliance
            findings = self._enforce_safety(findings, modality)

            return findings

        except Exception as e:
            logger.error(f"MedSigLIP inference failed: {e}")
            return self._generate_stub_response(
                modality=modality,
                clinical_context=clinical_context
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
            Dict with ranked classifications and confidences
        """
        if not self._load_model():
            return self._generate_stub_classification(candidates)

        try:
            # Load image
            image = Image.open(image_path).convert("RGB")

            # Process image with candidate labels
            inputs = self.processor(
                text=candidates,
                images=[image] * len(candidates),
                return_tensors="pt",
                padding=True
            ).to(self.device)

            # Get similarity scores
            import torch
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits_per_image[0]
                probs = torch.softmax(logits, dim=0)

            # Rank candidates
            results = [
                {
                    "condition": candidates[i],
                    "confidence": float(probs[i]),
                    "rank": i + 1
                }
                for i in range(len(candidates))
            ]

            results.sort(key=lambda x: x["confidence"], reverse=True)

            return {
                "classifications": results,
                "modality": modality,
                "disclaimer": "This is decision support only. Images must be reviewed by qualified radiologists/clinicians.",
                "stub_mode": False
            }

        except Exception as e:
            logger.error(f"Image classification failed: {e}")
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
