"""
Medical Image Analysis Agent - Analyzes medical images using MedSigLIP.

Responsibilities:
- Accept medical images (X-ray, CT, MRI, dermatology, pathology)
- Perform feature extraction and abnormality detection using MedSigLIP
- Provide structured findings with confidence scores
- Highlight regions of interest
- Generate natural language descriptions
- NEVER make definitive radiological diagnoses

Safety Boundaries:
- Decision support ONLY, not diagnostic authority
- Always recommend radiologist/specialist review
- Provide confidence scores for all findings
- Flag limitations and uncertainties
- Mandatory imaging disclaimers

Current Implementation: Ready for MedSigLIP integration (stub responses)
Production: Integrate MedSigLIP for vision-language model inference
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from typing import List, Dict, Optional, Any
import base64
import logging
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

# Map the agent's internal modality keys -> MedSigLIP service label-set keys.
_MODALITY_TO_SIGLIP = {
    "chest_xray": "chest_xray",
    "ct_chest": "chest_xray",
    "ct_head": "general",
    "ct_abdomen": "general",
    "mri_brain": "general",
    "dermatology": "dermatology",
    "pathology": "histopathology",
    "other": "general",
}


class ImageAnalysisAgent(BaseAgent):
    """
    Medical image analysis using MedSigLIP vision-language model.

    Supports multiple modalities:
    - Chest X-rays
    - CT scans
    - MRI scans
    - Dermatology images
    - Pathology slides
    """

    def __init__(self):
        super().__init__()
        self.name = "image_analysis"

        # Supported image modalities
        self.supported_modalities = {
            "chest_xray": "Chest X-ray (PA/AP/Lateral)",
            "ct_chest": "CT Chest",
            "ct_head": "CT Head",
            "ct_abdomen": "CT Abdomen/Pelvis",
            "mri_brain": "MRI Brain",
            "dermatology": "Dermatology/Skin Lesion",
            "pathology": "Pathology Slide",
            "other": "Other Medical Image"
        }

        # Common findings templates by modality
        self.finding_templates = {
            "chest_xray": [
                "opacity", "infiltrate", "consolidation", "effusion",
                "pneumothorax", "cardiomegaly", "mass", "nodule"
            ],
            "dermatology": [
                "lesion", "rash", "discoloration", "texture change",
                "asymmetry", "border irregularity", "color variation"
            ]
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Analyze medical image and provide findings.

        Expected context:
        - image_path: Path to image file (or image_data: base64 encoded)
        - modality: Image modality (chest_xray, ct_chest, dermatology, etc.)
        - clinical_context: Patient symptoms, history (optional)
        - comparison_images: Prior images for comparison (optional)
        - analysis_type: "finding_detection" | "abnormality_classification" | "region_description"
        """
        # Extract context
        image_path = request.context.get("image_path")
        image_data = request.context.get("image_data")
        modality = request.context.get("modality", "other")
        clinical_context = request.context.get("clinical_context")
        analysis_type = request.context.get("analysis_type", "finding_detection")

        # Validate image input
        if not image_path and not image_data and not request.attachments:
            return self._error_response(
                "No image provided",
                "Please provide image_path, image_data, or attachments"
            )

        # Validate modality
        if modality not in self.supported_modalities:
            return self._error_response(
                f"Unsupported modality: {modality}",
                f"Supported modalities: {', '.join(self.supported_modalities.keys())}"
            )

        # Resolve a single base64 payload (image_data or first attachment).
        if not image_data and request.attachments:
            image_data = request.attachments[0]

        # Perform image analysis based on type
        if analysis_type == "finding_detection":
            result = await self._detect_findings(
                image_path=image_path,
                modality=modality,
                clinical_context=clinical_context,
                image_data=image_data,
            )
        elif analysis_type == "abnormality_classification":
            result = await self._classify_abnormality(
                image_path=image_path,
                modality=modality,
                image_data=image_data,
            )
        elif analysis_type == "region_description":
            result = await self._describe_region(
                image_path=image_path,
                modality=modality
            )
        else:
            return self._error_response(
                f"Unknown analysis_type: {analysis_type}",
                "Supported types: finding_detection, abnormality_classification, region_description"
            )

        return result

    def _load_pil_image(
        self,
        image_path: Optional[str],
        image_data: Optional[str],
    ):
        """Load a PIL image from a base64 payload or a file path (or None)."""
        try:
            from PIL import Image as PILImage
        except Exception:
            return None
        try:
            if image_data:
                raw = image_data
                # Strip a possible data URL prefix.
                if isinstance(raw, str) and "," in raw[:64] and raw.lstrip().startswith("data:"):
                    raw = raw.split(",", 1)[1]
                decoded = base64.b64decode(raw)
                return PILImage.open(BytesIO(decoded)).convert("RGB")
            if image_path and Path(image_path).exists():
                return PILImage.open(image_path).convert("RGB")
        except Exception as exc:
            logger.error(f"Image decode failed: {exc}")
        return None

    async def _detect_findings(
        self,
        image_path: Optional[str],
        modality: str,
        clinical_context: Optional[Dict],
        image_data: Optional[str] = None,
    ) -> AgentResponse:
        """
        Detect visual findings in a medical image.

        Two-stage when models are loaded:
          Stage 1 — MedSigLIP zero-shot classification (sigmoid scoring).
          Stage 2 — MedGemma radiology-style report using Stage 1 context.
        Falls back to a clearly-labelled stub (stub_mode=True) otherwise.
        """
        real_findings = await self._real_finding_detection(
            image_path=image_path, image_data=image_data, modality=modality,
            clinical_context=clinical_context,
        )
        if real_findings is not None:
            findings_data = real_findings
        else:
            # Stub fallback — keep structured demo output, mark it non-authoritative.
            findings_data = await self._call_medsigLIP_finding_detection(
                image_path=image_path,
                modality=modality,
                clinical_context=clinical_context,
            )
            findings_data["stub_mode"] = True

        # Parse findings
        findings = findings_data["findings"]
        overall_impression = findings_data["impression"]
        confidence = findings_data["confidence"]
        stub_mode = findings_data.get("stub_mode", True)

        # Identify red flags
        red_flags = self._identify_imaging_red_flags(findings, modality)

        # Determine if escalation needed
        requires_escalation = len(red_flags) > 0 or any(
            f.get("severity") in ["critical", "urgent"] for f in findings
        )

        # Build response data
        data = {
            "modality": self.supported_modalities[modality],
            "analysis_type": "finding_detection",
            "image_quality": findings_data.get("image_quality", "adequate"),
            "findings": findings,
            "regions_of_interest": findings_data.get("regions", []),
            "overall_impression": overall_impression,
            "clinical_correlation": self._get_clinical_correlation_notes(modality),
            "recommended_next_steps": findings_data.get("next_steps", []),
            "limitations": self._get_limitations(),
            "models_used": findings_data.get("models_used", []),
            "report": findings_data.get("report"),
            "stub_mode": stub_mode,
            "stub_note": (
                "AI model not loaded — demo output. Findings below are NOT real "
                "image analysis."
            ) if stub_mode else None,
            "disclaimer": self._get_imaging_disclaimer()
        }

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data=data,
            confidence=confidence,
            reasoning=f"Image analysis performed on {modality} - {len(findings)} findings detected",
            red_flags=red_flags,
            requires_escalation=requires_escalation,
            suggested_agents=["diagnostic_support"] if findings else []
        )

    async def _classify_abnormality(
        self,
        image_path: Optional[str],
        modality: str,
        image_data: Optional[str] = None,
    ) -> AgentResponse:
        """
        Classify abnormality in a medical image.

        Uses real MedSigLIP zero-shot scoring when available; otherwise returns
        a clearly-labelled stub (stub_mode=True).
        """
        classification_data = None
        try:
            from services import medsiglip_service

            if medsiglip_service.is_available():
                image = self._load_pil_image(image_path, image_data)
                if image is not None:
                    siglip_key = _MODALITY_TO_SIGLIP.get(modality, "general")
                    cls = medsiglip_service.classify_image(image, modality=siglip_key)
                    if not cls.get("stub_mode"):
                        is_abnormal = bool(cls.get("is_abnormal"))
                        classification_data = {
                            "classification": (
                                f"Abnormal — {cls.get('top_finding')}" if is_abnormal
                                else f"Likely normal — {cls.get('top_finding')}"
                            ),
                            "confidence": float(cls.get("confidence") or 0.0),
                            "reasoning": (
                                "MedSigLIP zero-shot classification (sigmoid scoring)."
                            ),
                            "characteristics": [
                                f"{f['label']} ({f['probability']:.1%})"
                                for f in cls.get("all_findings", [])[:5]
                            ],
                            "differential": [],
                            "red_flags": (
                                ["Abnormal features — specialist review recommended"]
                                if is_abnormal else []
                            ),
                            "requires_specialist": is_abnormal,
                            "stub_mode": False,
                        }
        except Exception as exc:
            logger.error(f"MedSigLIP abnormality classification failed: {exc}")

        if classification_data is None:
            classification_data = await self._call_medsigLIP_classification(
                image_path=image_path,
                modality=modality
            )
            classification_data["stub_mode"] = True

        stub_mode = classification_data.get("stub_mode", True)
        data = {
            "modality": self.supported_modalities[modality],
            "analysis_type": "abnormality_classification",
            "classification": classification_data["classification"],
            "confidence": classification_data["confidence"],
            "reasoning": classification_data["reasoning"],
            "characteristics": classification_data.get("characteristics", []),
            "differential_considerations": classification_data.get("differential", []),
            "stub_mode": stub_mode,
            "stub_note": (
                "AI model not loaded — demo output, not a real classification."
            ) if stub_mode else None,
            "disclaimer": self._get_imaging_disclaimer()
        }

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data=data,
            confidence=classification_data["confidence"],
            reasoning=f"{modality} abnormality classification completed",
            red_flags=classification_data.get("red_flags", []),
            requires_escalation=classification_data.get("requires_specialist", False),
            suggested_agents=["diagnostic_support"]
        )

    async def _describe_region(
        self,
        image_path: Optional[str],
        modality: str
    ) -> AgentResponse:
        """
        Generate natural language description of specific region in image.
        """
        description_data = await self._call_medsigLIP_description(
            image_path=image_path,
            modality=modality
        )

        data = {
            "modality": self.supported_modalities[modality],
            "analysis_type": "region_description",
            "description": description_data["description"],
            "anatomical_structures": description_data.get("structures", []),
            "notable_features": description_data.get("features", []),
            "stub_mode": True,
            "stub_note": (
                "AI model not loaded — demo output, not a real region description."
            ),
            "disclaimer": self._get_imaging_disclaimer()
        }

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data=data,
            confidence=description_data["confidence"],
            reasoning="Image region described using vision-language model",
            red_flags=[],
            requires_escalation=False
        )

    async def _real_finding_detection(
        self,
        image_path: Optional[str],
        image_data: Optional[str],
        modality: str,
        clinical_context: Optional[Dict],
    ) -> Optional[Dict[str, Any]]:
        """
        Real two-stage analysis via MedSigLIP (+ optional MedGemma report).

        Returns a findings dict (stub_mode=False) on success, or None when the
        image model is unavailable / the image cannot be decoded — letting the
        caller fall back to the labelled stub.
        """
        try:
            from services import medsiglip_service, medgemma_service
        except Exception:
            return None

        if not medsiglip_service.is_available():
            return None

        image = self._load_pil_image(image_path, image_data)
        if image is None:
            return None

        siglip_key = _MODALITY_TO_SIGLIP.get(modality, "general")
        cls = medsiglip_service.classify_image(image, modality=siglip_key)
        if cls.get("stub_mode"):
            return None

        models_used = ["google/medsiglip-448"]
        top = cls.get("top_finding") or "finding"
        confidence = float(cls.get("confidence") or 0.0)
        is_abnormal = bool(cls.get("is_abnormal"))

        findings = [
            {
                "finding": f["label"],
                "location": "see image",
                "severity": "moderate" if is_abnormal and i == 0 else "mild",
                "confidence": f["probability"],
                "description": f["label"],
                "differential": [],
            }
            for i, f in enumerate(cls.get("all_findings", [])[:5])
            if f["probability"] >= 0.30 or i == 0
        ]

        impression = (
            f"MedSigLIP top match: {top} (confidence {confidence:.1%}). "
            + ("Abnormal features suggested — " if is_abnormal else "Appears within normal limits — ")
            + "radiologist review required for definitive interpretation."
        )

        # Stage 2: optional MedGemma natural-language report (image+text).
        report = None
        if medgemma_service.is_available():
            ctx = (
                f"Imaging modality: {modality}\n"
                f"MedSigLIP zero-shot top finding: {top} ({confidence:.1%}); "
                f"abnormal={is_abnormal}.\n"
                f"Clinical context: {clinical_context or 'not provided'}\n\n"
                "Write a concise radiology-style report: Impression, Findings, "
                "Recommendations, and any urgent flags. Decision support only."
            )
            gem = medgemma_service.generate_text(ctx, image=image, max_new_tokens=400)
            if not gem.get("stub_mode") and gem.get("text"):
                report = gem["text"]
                impression = report
                models_used.append("MedGemma")

        return {
            "image_quality": "adequate",
            "confidence": confidence,
            "findings": findings,
            "regions": [],
            "impression": impression,
            "report": report,
            "next_steps": [
                "Radiologist/specialist review required",
                "Correlate with clinical presentation",
            ],
            "models_used": models_used,
            "stub_mode": False,
        }

    async def _call_medsigLIP_finding_detection(
        self,
        image_path: Optional[str],
        modality: str,
        clinical_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Call MedSigLIP for finding detection.

        STUB IMPLEMENTATION - Ready for production integration.

        Production Integration:
        1. Load image: PIL.Image.open(image_path)
        2. Preprocess: MedSigLIP preprocessing pipeline
        3. Encode image: model.encode_image(image)
        4. Encode text prompts: model.encode_text(finding_prompts)
        5. Compute similarities: cosine_similarity(image_features, text_features)
        6. Threshold and rank findings
        7. Generate natural language report

        Example with HuggingFace:
        ```python
        from transformers import AutoProcessor, AutoModel
        import torch

        processor = AutoProcessor.from_pretrained("google/medsigLIP")
        model = AutoModel.from_pretrained("google/medsigLIP")

        image = Image.open(image_path)
        inputs = processor(images=image, return_tensors="pt")

        with torch.no_grad():
            image_features = model.get_image_features(**inputs)

        # Zero-shot classification with finding templates
        finding_texts = ["opacity", "infiltrate", "normal lung"]
        text_inputs = processor(text=finding_texts, return_tensors="pt", padding=True)
        text_features = model.get_text_features(**text_inputs)

        # Compute similarity
        similarity = (image_features @ text_features.T).softmax(dim=-1)
        ```

        See MEDSIGCLIP_INTEGRATION_GUIDE.md for detailed instructions.
        """
        # TODO: Replace with actual MedSigLIP call in production

        # STUB: Return mock findings based on modality
        if modality == "chest_xray":
            return {
                "image_quality": "adequate",
                "confidence": 0.75,
                "findings": [
                    {
                        "finding": "Opacity in right lower lobe",
                        "location": "Right lower lobe",
                        "size": "Approximately 3x2 cm",
                        "severity": "moderate",
                        "confidence": 0.78,
                        "description": "Ill-defined opacity consistent with possible infiltrate",
                        "differential": ["Pneumonia", "Atelectasis", "Mass"]
                    },
                    {
                        "finding": "Mild cardiomegaly",
                        "location": "Cardiac silhouette",
                        "severity": "mild",
                        "confidence": 0.65,
                        "description": "Cardiothoracic ratio appears mildly increased",
                        "differential": ["Volume overload", "Cardiomyopathy", "Technical factors"]
                    }
                ],
                "regions": [
                    {
                        "region": "Right lower lobe",
                        "coordinates": {"x": 250, "y": 180, "width": 80, "height": 60},
                        "description": "Area of increased opacity"
                    }
                ],
                "impression": "Findings suggestive of right lower lobe opacity, possibly pneumonia. Mild cardiac enlargement noted. Radiologist review recommended for definitive interpretation.",
                "next_steps": [
                    "Correlate with clinical symptoms (fever, cough, dyspnea)",
                    "Consider CT chest if diagnosis unclear",
                    "Radiologist review required",
                    "Follow-up imaging may be indicated based on treatment response"
                ]
            }
        elif modality == "dermatology":
            return {
                "image_quality": "good",
                "confidence": 0.72,
                "findings": [
                    {
                        "finding": "Pigmented lesion with irregular borders",
                        "location": "Lesion in image",
                        "severity": "moderate",
                        "confidence": 0.72,
                        "description": "Asymmetric pigmented lesion with irregular border and color variation",
                        "differential": ["Atypical nevus", "Melanoma", "Dysplastic nevus"]
                    }
                ],
                "regions": [
                    {
                        "region": "Central lesion",
                        "coordinates": {"x": 150, "y": 150, "width": 100, "height": 100},
                        "description": "Pigmented lesion with ABCDE features"
                    }
                ],
                "impression": "Pigmented lesion with concerning features (asymmetry, border irregularity, color variation). Dermatology evaluation recommended for clinical correlation and possible biopsy.",
                "next_steps": [
                    "Dermatology consultation recommended",
                    "Consider dermoscopy for detailed examination",
                    "Biopsy may be indicated based on clinical assessment",
                    "Document lesion size and characteristics for monitoring"
                ]
            }
        else:
            return {
                "image_quality": "adequate",
                "confidence": 0.65,
                "findings": [
                    {
                        "finding": "Image analysis pending",
                        "location": "General",
                        "severity": "unknown",
                        "confidence": 0.65,
                        "description": "Modality-specific analysis requires specialist review",
                        "differential": []
                    }
                ],
                "regions": [],
                "impression": "Specialist review required for definitive interpretation.",
                "next_steps": ["Radiologist/specialist review required"]
            }

    async def _call_medsigLIP_classification(
        self,
        image_path: Optional[str],
        modality: str
    ) -> Dict[str, Any]:
        """
        Call MedSigLIP for abnormality classification.
        STUB - Ready for production integration.
        """
        # STUB: Mock classification
        if modality == "dermatology":
            return {
                "classification": "Concerning - Dermatology evaluation recommended",
                "confidence": 0.70,
                "reasoning": "Lesion exhibits ABCDE criteria: Asymmetry, Border irregularity, Color variation",
                "characteristics": [
                    "Asymmetric shape",
                    "Irregular borders",
                    "Multiple colors present",
                    "Diameter >6mm"
                ],
                "differential": [
                    "Atypical nevus",
                    "Melanoma (requires biopsy to rule out)",
                    "Dysplastic nevus"
                ],
                "red_flags": ["Features concerning for melanoma - urgent dermatology referral"],
                "requires_specialist": True
            }
        elif modality == "chest_xray":
            return {
                "classification": "Abnormal - Infiltrate present",
                "confidence": 0.75,
                "reasoning": "Opacity in right lower lobe consistent with infiltrate",
                "characteristics": [
                    "Right lower lobe opacity",
                    "Ill-defined margins",
                    "Air bronchograms possibly present"
                ],
                "differential": [
                    "Community-acquired pneumonia",
                    "Aspiration pneumonia",
                    "Atelectasis"
                ],
                "red_flags": [],
                "requires_specialist": False
            }
        else:
            return {
                "classification": "Specialist review required",
                "confidence": 0.60,
                "reasoning": "Modality requires radiologist interpretation",
                "characteristics": [],
                "differential": [],
                "red_flags": [],
                "requires_specialist": True
            }

    async def _call_medsigLIP_description(
        self,
        image_path: Optional[str],
        modality: str
    ) -> Dict[str, Any]:
        """
        Call MedSigLIP for natural language description generation.
        STUB - Ready for production integration.
        """
        # STUB: Mock description
        return {
            "description": f"Medical image showing anatomical structures typical of {modality}. Detailed description requires specialist review.",
            "confidence": 0.65,
            "structures": ["Anatomical structures visible"],
            "features": ["Standard imaging features"]
        }

    def _identify_imaging_red_flags(self, findings: List[Dict], modality: str) -> List[str]:
        """Identify critical findings that require immediate attention."""
        red_flags = []

        for finding in findings:
            severity = finding.get("severity", "").lower()
            finding_name = finding.get("finding", "").lower()

            # Critical findings by modality
            if modality == "chest_xray":
                if "pneumothorax" in finding_name:
                    red_flags.append("🚨 CRITICAL: Pneumothorax detected - immediate clinical correlation required")
                elif "mass" in finding_name or "malignancy" in finding_name:
                    red_flags.append("⚠️ Concerning finding: Mass/lesion - oncology consultation may be needed")
                elif severity == "critical":
                    red_flags.append(f"🚨 CRITICAL: {finding['finding']}")

            elif modality == "dermatology":
                if "melanoma" in finding_name or severity in ["critical", "urgent"]:
                    red_flags.append("⚠️ Concerning features - urgent dermatology evaluation recommended")

            elif modality == "ct_head":
                if "hemorrhage" in finding_name or "bleed" in finding_name:
                    red_flags.append("🚨 CRITICAL: Intracranial hemorrhage - immediate neurosurgical consultation")
                elif "mass" in finding_name:
                    red_flags.append("⚠️ Mass effect - urgent neurology/neurosurgery consultation")

        return red_flags

    def _get_clinical_correlation_notes(self, modality: str) -> List[str]:
        """Get modality-specific clinical correlation notes."""
        notes = {
            "chest_xray": [
                "Correlate with patient symptoms (cough, fever, dyspnea)",
                "Consider patient risk factors (smoking, exposure history)",
                "Review vitals (oxygen saturation, temperature)",
                "Compare with prior imaging if available"
            ],
            "dermatology": [
                "Assess lesion clinically (palpation, dermoscopy)",
                "Document size, shape, color, borders",
                "Obtain patient history (changes over time, symptoms)",
                "Consider patient risk factors (sun exposure, family history)"
            ],
            "ct_chest": [
                "Correlate with clinical presentation",
                "Review laboratory values",
                "Consider indication for study",
                "Compare with prior imaging"
            ]
        }
        return notes.get(modality, ["Clinical correlation with radiologist recommended"])

    def _get_limitations(self) -> List[str]:
        """Get standard imaging AI limitations."""
        return [
            "AI analysis is preliminary and for decision support only",
            "Cannot replace radiologist/specialist interpretation",
            "Findings require clinical correlation",
            "Image quality and technical factors may affect analysis",
            "No comparison with prior studies",
            "Cannot account for all clinical context"
        ]

    def _get_imaging_disclaimer(self) -> str:
        """Get mandatory imaging analysis disclaimer."""
        return (
            "⚠️ IMAGING DISCLAIMER: This AI analysis is for clinical decision support only "
            "and does NOT constitute a radiological diagnosis or interpretation. All imaging "
            "findings MUST be reviewed and interpreted by a qualified radiologist or specialist. "
            "This analysis cannot replace professional radiological interpretation. Clinical "
            "correlation is essential. The final diagnosis and treatment decisions must be made "
            "by licensed healthcare providers based on comprehensive clinical assessment."
        )

    def _error_response(self, error: str, details: str) -> AgentResponse:
        """Generate error response."""
        return AgentResponse(
            success=False,
            agent_name=self.name,
            data={
                "error": error,
                "details": details
            },
            confidence=0.0,
            reasoning=error,
            red_flags=[],
            requires_escalation=False
        )

    def get_capabilities(self) -> List[str]:
        """Return keywords that trigger this agent."""
        return [
            "xray", "x-ray", "scan", "ct", "mri", "image", "imaging",
            "analyze image", "chest xray", "ct scan", "skin lesion",
            "dermatology", "radiology", "radiograph"
        ]

    def get_description(self) -> str:
        """Return agent description."""
        return "Medical image analysis using MedSigLIP - analyzes X-rays, CT, MRI, dermatology images (decision support only)"

    def get_confidence_threshold(self) -> float:
        """Minimum confidence to activate this agent."""
        return 0.50
