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
from pathlib import Path


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

        # Perform image analysis based on type
        if analysis_type == "finding_detection":
            result = await self._detect_findings(
                image_path=image_path,
                modality=modality,
                clinical_context=clinical_context
            )
        elif analysis_type == "abnormality_classification":
            result = await self._classify_abnormality(
                image_path=image_path,
                modality=modality
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

    async def _detect_findings(
        self,
        image_path: Optional[str],
        modality: str,
        clinical_context: Optional[Dict]
    ) -> AgentResponse:
        """
        Detect visual findings in medical image using MedSigLIP.

        In production:
        1. Load image
        2. Preprocess for MedSigLIP
        3. Extract visual features
        4. Compare with finding templates
        5. Generate natural language descriptions
        6. Return structured findings with confidence
        """
        # Call MedSigLIP model (stub for now)
        findings_data = await self._call_medsigLIP_finding_detection(
            image_path=image_path,
            modality=modality,
            clinical_context=clinical_context
        )

        # Parse findings
        findings = findings_data["findings"]
        overall_impression = findings_data["impression"]
        confidence = findings_data["confidence"]

        # Identify red flags
        red_flags = self._identify_imaging_red_flags(findings, modality)

        # Determine if escalation needed
        requires_escalation = len(red_flags) > 0 or any(
            f["severity"] in ["critical", "urgent"] for f in findings
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
        modality: str
    ) -> AgentResponse:
        """
        Classify abnormality in medical image.

        For dermatology: benign vs concerning lesion
        For chest X-ray: normal vs abnormal
        For CT: specific finding classification
        """
        classification_data = await self._call_medsigLIP_classification(
            image_path=image_path,
            modality=modality
        )

        data = {
            "modality": self.supported_modalities[modality],
            "analysis_type": "abnormality_classification",
            "classification": classification_data["classification"],
            "confidence": classification_data["confidence"],
            "reasoning": classification_data["reasoning"],
            "characteristics": classification_data.get("characteristics", []),
            "differential_considerations": classification_data.get("differential", []),
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

    async def _call_medsigLIP_finding_detection(
        self,
        image_path: Optional[str],
        modality: str,
        clinical_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Stage 1: MedSigLIP zero-shot classification to identify top findings.
        Stage 2: MedGemma multimodal narrative impression for context.

        Falls back to a safe stub when models are unavailable.
        """
        if not image_path:
            return self._stub_findings(modality)

        classifications = None
        try:
            from services import medsiglip_service
            classifications = medsiglip_service.classify_image(image_path, modality, top_k=5)
        except Exception:
            pass

        if classifications:
            top = classifications[0]
            top_label = top["label"]
            top_score = top["score"]

            severity = "normal" if "normal" in top_label.lower() else (
                "high" if top_score >= 0.8 else "moderate" if top_score >= 0.6 else "mild"
            )

            finding = {
                "finding": top_label,
                "location": "Image region",
                "severity": severity,
                "confidence": top_score,
                "description": (
                    f"MedSigLIP zero-shot classification: '{top_label}' "
                    f"(score {top_score:.2%})"
                ),
                "differential": [c["label"] for c in classifications[1:4]],
            }

            # MedGemma narrative impression (uses image if available)
            impression = (
                f"Primary finding: {top_label} (MedSigLIP confidence {top_score:.0%}). "
                "Radiologist/specialist review required."
            )
            try:
                from services import medgemma_service
                context_str = f"\nClinical context: {clinical_context}" if clinical_context else ""
                gemma_prompt = (
                    f"You are a medical AI assistant reviewing a {modality} image.{context_str}\n"
                    f"MedSigLIP analysis: primary finding '{top_label}' (confidence {top_score:.0%}). "
                    f"Other possibilities: {', '.join(c['label'] for c in classifications[1:3])}.\n\n"
                    "Provide a concise radiological impression (2-3 sentences) and 3 recommended "
                    "next steps. Do NOT make a definitive diagnosis. Recommend specialist review."
                )
                gemma_text = medgemma_service.generate_with_image(
                    prompt=gemma_prompt,
                    image_path=image_path,
                    max_new_tokens=256,
                )
                if gemma_text:
                    impression = gemma_text
            except Exception:
                pass

            return {
                "image_quality": "adequate",
                "confidence": top_score,
                "findings": [finding],
                "regions": [],
                "impression": impression,
                "next_steps": [
                    "Radiologist/specialist review required",
                    "Correlate with clinical symptoms",
                    "Consider follow-up imaging if indicated",
                ],
            }

        return self._stub_findings(modality)

    def _stub_findings(self, modality: str) -> Dict[str, Any]:
        """Return safe stub findings when AI models are unavailable."""
        return {
            "image_quality": "adequate",
            "confidence": 0.50,
            "findings": [
                {
                    "finding": "AI model unavailable — specialist review required",
                    "location": "General",
                    "severity": "unknown",
                    "confidence": 0.50,
                    "description": "Models not loaded. Manual radiologist review required.",
                    "differential": [],
                }
            ],
            "regions": [],
            "impression": (
                "AI image analysis unavailable. "
                "Radiologist/specialist review required."
            ),
            "next_steps": ["Radiologist/specialist review required"],
        }

    async def _call_medsigLIP_classification(
        self,
        image_path: Optional[str],
        modality: str
    ) -> Dict[str, Any]:
        """
        Classify abnormality using MedSigLIP zero-shot scores.
        Falls back to a safe stub when model unavailable.
        """
        if image_path:
            try:
                from services import medsiglip_service
                classifications = medsiglip_service.classify_image(image_path, modality, top_k=5)
                if classifications:
                    top = classifications[0]
                    top_label = top["label"]
                    top_score = top["score"]
                    is_normal = "normal" in top_label.lower()
                    requires_specialist = not is_normal and top_score > 0.4
                    red_flags = []
                    if not is_normal and top_score > 0.6:
                        red_flags.append(
                            f"Possible {top_label} — specialist evaluation recommended"
                        )
                    return {
                        "classification": top_label,
                        "confidence": top_score,
                        "reasoning": (
                            f"MedSigLIP zero-shot similarity score: {top_score:.2%}"
                        ),
                        "characteristics": [c["label"] for c in classifications[1:4]],
                        "differential": [c["label"] for c in classifications[1:4]],
                        "red_flags": red_flags,
                        "requires_specialist": requires_specialist,
                    }
            except Exception:
                pass

        return {
            "classification": "AI model unavailable — specialist review required",
            "confidence": 0.50,
            "reasoning": "MedSigLIP not loaded",
            "characteristics": [],
            "differential": [],
            "red_flags": [],
            "requires_specialist": True,
        }

    async def _call_medsigLIP_description(
        self,
        image_path: Optional[str],
        modality: str
    ) -> Dict[str, Any]:
        """
        Generate natural language description using MedGemma with the image.
        Falls back to a generic description when model is unavailable.
        """
        if image_path:
            try:
                from services import medgemma_service
                prompt = (
                    f"Describe this {modality} medical image in 2-3 sentences. "
                    "List the main anatomical structures visible and any notable features. "
                    "Do NOT make a diagnosis. Recommend specialist review."
                )
                description = medgemma_service.generate_with_image(
                    prompt=prompt, image_path=image_path, max_new_tokens=200
                )
                if description:
                    return {
                        "description": description,
                        "confidence": 0.75,
                        "structures": [],
                        "features": [],
                    }
            except Exception:
                pass

        return {
            "description": (
                f"Medical image ({modality}). "
                "AI description unavailable — detailed review requires specialist interpretation."
            ),
            "confidence": 0.50,
            "structures": [],
            "features": [],
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
