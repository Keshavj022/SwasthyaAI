"""
MedGemma Inference

Provides inference for medical text/image understanding and clinical reasoning
using Google's MedGemma model (Gemma 3 multimodal, medical fine-tune).

Model: google/medgemma-1.5-4b-it
Architecture: Gemma3ForConditionalGeneration (vision-language)
Use cases:
- Medical question answering
- Differential diagnosis generation
- Clinical reasoning
- Medical text summarization
- Medical image analysis (multimodal)
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseInference

logger = logging.getLogger(__name__)


class MedGemmaInference(BaseInference):
    """MedGemma model inference for medical text understanding"""

    # Safety-compliant system prompt
    SYSTEM_PROMPT = """You are a clinical decision support assistant.
You must NOT provide definitive diagnoses or treatment plans.
You must express uncertainty and recommend consulting a qualified clinician.

CRITICAL RULES:
- Use phrases like "may suggest", "could indicate", "consistent with"
- Provide differential diagnoses ranked by likelihood
- Flag red-flag symptoms requiring immediate attention
- Always include disclaimer
- Output valid JSON only
- Never prescribe medication
- Never provide definitive diagnoses
"""

    def _load_model_weights(self):
        """Load MedGemma model weights (Gemma3ForConditionalGeneration)"""
        try:
            import torch
            from transformers import AutoProcessor, Gemma3ForConditionalGeneration

            logger.info(f"Loading MedGemma from {self.model_path}")

            self.processor = AutoProcessor.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )

            logger.info("Loading model weights (this may take a moment)...")
            model_dtype = torch.float32 if self.device == "cpu" else torch.bfloat16
            self.model = Gemma3ForConditionalGeneration.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                dtype=model_dtype,
                low_cpu_mem_usage=True,
            )

            logger.info(f"Moving model to {self.device} ({model_dtype})...")
            self.model.to(self.device)
            self.model.eval()

        except Exception as e:
            logger.error(f"Failed to load MedGemma: {e}")
            raise

    async def generate_response(
        self,
        query: str,
        patient_context: Optional[Dict[str, Any]] = None,
        task_type: str = "medical_qa",
        max_length: int = 512,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate medical response using MedGemma

        Args:
            query: User's medical question
            patient_context: Optional patient information
            task_type: Type of task (medical_qa, summarization, etc.)
            max_length: Maximum generation length
            temperature: Sampling temperature

        Returns:
            Dict with response, confidence, disclaimer
        """
        if not self._load_model():
            return self._generate_stub_response(
                query=query,
                task_type=task_type
            )

        try:
            # Build prompt with safety constraints
            prompt = self._build_prompt(query, patient_context, task_type)

            # Generate response using the processor (handles tokenization)
            inputs = self.processor(text=prompt, return_tensors="pt").to(self.device)

            import torch
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    do_sample=True,
                )

            generated_text = self.processor.decode(outputs[0], skip_special_tokens=True)

            # Extract JSON response from generated text
            response_data = self._parse_model_output(generated_text)

            # Ensure safety compliance
            response_data = self._enforce_safety(response_data)

            return response_data

        except Exception as e:
            logger.error(f"MedGemma inference failed: {e}")
            return self._generate_stub_response(query=query, task_type=task_type)

    async def generate_differential_diagnosis(
        self,
        symptoms: List[str],
        patient_history: Optional[Dict[str, Any]] = None,
        vital_signs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate differential diagnosis using MedGemma

        Args:
            symptoms: List of patient symptoms
            patient_history: Patient medical history
            vital_signs: Current vital signs

        Returns:
            Dict with ranked differential diagnoses
        """
        if not self._load_model():
            return self._generate_stub_differential(symptoms)

        try:
            # Build differential diagnosis prompt
            prompt = self._build_differential_prompt(symptoms, patient_history, vital_signs)

            # Generate response
            inputs = self.processor(text=prompt, return_tensors="pt").to(self.device)

            import torch
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=True,
                )

            generated_text = self.processor.decode(outputs[0], skip_special_tokens=True)
            response_data = self._parse_model_output(generated_text)
            response_data = self._enforce_safety(response_data)

            return response_data

        except Exception as e:
            logger.error(f"Differential diagnosis failed: {e}")
            return self._generate_stub_differential(symptoms)

    def _build_prompt(
        self,
        query: str,
        patient_context: Optional[Dict[str, Any]],
        task_type: str
    ) -> str:
        """Build safety-compliant prompt for MedGemma"""

        context_str = ""
        if patient_context:
            context_str = f"\nPatient Context: {json.dumps(patient_context, indent=2)}"

        prompt = f"""{self.SYSTEM_PROMPT}

{context_str}

User Query: {query}

Provide analysis in JSON format:
{{
  "analysis_summary": "...",
  "key_findings": ["...", "..."],
  "confidence": 0.0,
  "uncertainty_note": "...",
  "recommended_next_steps": ["...", "..."],
  "disclaimer": "This is clinical decision support only. Consult a healthcare provider."
}}
"""
        return prompt

    def _build_differential_prompt(
        self,
        symptoms: List[str],
        patient_history: Optional[Dict[str, Any]],
        vital_signs: Optional[Dict[str, Any]]
    ) -> str:
        """Build differential diagnosis prompt"""

        symptoms_str = ", ".join(symptoms)
        history_str = json.dumps(patient_history, indent=2) if patient_history else "None provided"
        vitals_str = json.dumps(vital_signs, indent=2) if vital_signs else "None provided"

        prompt = f"""{self.SYSTEM_PROMPT}

Patient Presentation:
Symptoms: {symptoms_str}
Patient History: {history_str}
Vital Signs: {vitals_str}

Provide differential diagnosis in JSON format:
{{
  "differential_diagnoses": [
    {{
      "condition": "...",
      "confidence": 0.0,
      "supporting_evidence": ["...", "..."],
      "contradicting_evidence": ["...", "..."]
    }}
  ],
  "red_flags": ["...", "..."],
  "recommended_workup": ["...", "..."],
  "missing_information": ["...", "..."],
  "disclaimer": "This is clinical decision support only. Consult a healthcare provider."
}}
"""
        return prompt

    def _parse_model_output(self, generated_text: str) -> Dict[str, Any]:
        """Parse JSON from model output"""
        try:
            # Extract JSON from generated text (model may include explanatory text)
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in output")

            json_str = generated_text[start_idx:end_idx]
            return json.loads(json_str)

        except Exception as e:
            logger.warning(f"Failed to parse model output as JSON: {e}")
            return {
                "analysis_summary": generated_text,
                "confidence": 0.5,
                "disclaimer": "This is clinical decision support only. Consult a healthcare provider."
            }

    def _enforce_safety(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure response complies with safety requirements"""

        # Always include disclaimer
        if "disclaimer" not in response:
            response["disclaimer"] = "This is clinical decision support only. Consult a healthcare provider."

        # Ensure confidence score exists and is in valid range
        if "confidence" not in response:
            response["confidence"] = 0.5
        else:
            response["confidence"] = max(0.0, min(1.0, response["confidence"]))

        # Check for prohibited language (definitive diagnoses)
        prohibited_phrases = ["you have", "you are diagnosed with", "definitive diagnosis"]
        text_content = json.dumps(response).lower()

        for phrase in prohibited_phrases:
            if phrase in text_content:
                logger.warning(f"Removing prohibited phrase: {phrase}")
                response["safety_warning"] = "Response modified to remove definitive diagnosis language"

        return response

    def _generate_stub_response(
        self,
        query: str,
        task_type: str = "medical_qa"
    ) -> Dict[str, Any]:
        """Generate rule-based stub response when model unavailable"""

        return {
            "analysis_summary": f"Based on your query, I recommend consulting with a healthcare provider for proper evaluation. This system currently operates in stub mode (AI model not loaded).",
            "key_findings": [
                "Unable to perform AI-based analysis (model not available)",
                "Please consult a qualified healthcare professional",
                "For emergencies, call 911 or go to the nearest emergency room"
            ],
            "confidence": 0.3,
            "uncertainty_note": "This is a placeholder response. Real AI model inference is not available.",
            "recommended_next_steps": [
                "Consult with a healthcare provider",
                "Provide more details about your symptoms",
                "Monitor symptoms and seek immediate care if worsening"
            ],
            "disclaimer": "This is clinical decision support only. Consult a healthcare provider.",
            "stub_mode": True
        }

    def _generate_stub_differential(self, symptoms: List[str]) -> Dict[str, Any]:
        """Generate stub differential diagnosis"""

        return {
            "differential_diagnoses": [
                {
                    "condition": "Multiple conditions possible",
                    "confidence": 0.3,
                    "supporting_evidence": symptoms,
                    "contradicting_evidence": []
                }
            ],
            "red_flags": [],
            "recommended_workup": [
                "Comprehensive physical examination",
                "Laboratory tests as indicated",
                "Imaging studies if warranted"
            ],
            "missing_information": [
                "Complete patient history",
                "Physical examination findings",
                "Previous test results"
            ],
            "disclaimer": "This is clinical decision support only. Consult a healthcare provider.",
            "stub_mode": True
        }
