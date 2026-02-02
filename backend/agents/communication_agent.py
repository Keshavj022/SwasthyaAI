"""
Doctor-Patient Communication Agent using MedGemma.

Responsibilities:
- Medical Q&A (patient questions → evidence-based answers)
- Simplify medical explanations (medical jargon → plain language)
- Generate visit summaries (clinical notes → patient-friendly summaries)
- Explain lab results in context
- Provide medication information
- Assess symptoms for triage guidance (NOT diagnosis)

All responses pass through Safety Agent and include explainability metadata.
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from agents.prompts.medgemma_prompts import MedGemmaPrompts
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class CommunicationAgent(BaseAgent):
    """
    Doctor-Patient Communication Agent using MedGemma.

    Handles all text-based communication tasks including Q&A,
    simplification, and summarization with medical safety guardrails.
    """

    def __init__(self):
        super().__init__()
        self.name = "communication"
        self.prompts = MedGemmaPrompts()

        # Model configuration (for actual MedGemma integration)
        self.model_name = "medgemma-7b"  # Or medgemma-2b for faster inference
        self.max_tokens = 1024
        self.temperature = 0.3  # Lower temperature for medical accuracy

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Route communication request to appropriate handler.

        Expected context keys:
        - task_type: "qa", "simplify", "visit_summary", "lab_results", "medication", "symptoms"
        - Additional keys depend on task_type
        """
        task_type = request.context.get("task_type", "qa")

        handlers = {
            "qa": self._handle_medical_qa,
            "simplify": self._handle_simplify,
            "visit_summary": self._handle_visit_summary,
            "lab_results": self._handle_lab_results,
            "medication": self._handle_medication,
            "symptoms": self._handle_symptoms
        }

        handler = handlers.get(task_type)
        if not handler:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                data={
                    "error": f"Unknown task_type: {task_type}",
                    "supported_types": list(handlers.keys())
                },
                confidence=0.0,
                reasoning="Invalid task type specified",
                red_flags=[],
                requires_escalation=False
            )

        return await handler(request)

    async def _handle_medical_qa(self, request: AgentRequest) -> AgentResponse:
        """
        Handle medical Q&A requests.

        Required context:
        - question: Patient's medical question
        Optional context:
        - patient_context: Patient information (age, conditions, medications, allergies)
        - conversation_history: Previous Q&A exchanges
        """
        question = request.context.get("question")
        if not question:
            return self._error_response("'question' required for medical Q&A")

        patient_context = request.context.get("patient_context")
        conversation_history = request.context.get("conversation_history")

        # Generate MedGemma prompt
        prompt = self.prompts.medical_qa(
            question=question,
            patient_context=patient_context,
            conversation_history=conversation_history
        )

        # Call MedGemma model
        model_response = await self._call_medgemma(prompt)

        # Parse response
        parsed = self._parse_qa_response(model_response)

        # Check for red flags
        red_flags = self._detect_red_flags(question, parsed)

        # Calculate confidence
        confidence = self._calculate_confidence(parsed)

        # Determine if escalation needed
        requires_escalation = len(red_flags) > 0 or confidence < 0.50

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "medical_qa",
                "question": question,
                "answer": parsed.get("main_answer", ""),
                "key_points": parsed.get("key_points", []),
                "when_to_seek_care": parsed.get("when_to_seek_care", ""),
                "confidence_explanation": parsed.get("confidence_explanation", ""),
                "reasoning": parsed.get("reasoning", ""),
                "has_patient_context": patient_context is not None
            },
            confidence=confidence,
            reasoning=f"Medical Q&A response generated. {parsed.get('reasoning', '')}",
            red_flags=red_flags,
            requires_escalation=requires_escalation,
            suggested_agents=["diagnostic_support"] if "diagnos" in question.lower() else []
        )

    async def _handle_simplify(self, request: AgentRequest) -> AgentResponse:
        """
        Simplify complex medical text.

        Required context:
        - medical_text: Text to simplify
        Optional context:
        - reading_level: Target reading level (default: "8th grade")
        - patient_context: For personalization
        """
        medical_text = request.context.get("medical_text")
        if not medical_text:
            return self._error_response("'medical_text' required for simplification")

        reading_level = request.context.get("reading_level", "8th grade")
        patient_context = request.context.get("patient_context")

        # Generate prompt
        prompt = self.prompts.simplify_medical_text(
            medical_text=medical_text,
            reading_level=reading_level,
            patient_context=patient_context
        )

        # Call MedGemma
        model_response = await self._call_medgemma(prompt)

        # Parse response
        parsed = self._parse_simplify_response(model_response)

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "simplify",
                "original_text": medical_text[:200] + "..." if len(medical_text) > 200 else medical_text,
                "simplified_explanation": parsed.get("simplified_explanation", ""),
                "key_terms_explained": parsed.get("key_terms_explained", {}),
                "what_this_means": parsed.get("what_this_means", ""),
                "questions_for_doctor": parsed.get("questions_for_doctor", []),
                "reading_level": reading_level
            },
            confidence=0.85,  # High confidence for simplification task
            reasoning="Medical text simplified while maintaining accuracy",
            red_flags=[],
            requires_escalation=False
        )

    async def _handle_visit_summary(self, request: AgentRequest) -> AgentResponse:
        """
        Generate patient-friendly visit summary.

        Required context:
        - visit_data: Dictionary with visit information
        Optional context:
        - audience: "patient" or "provider" (default: "patient")
        """
        visit_data = request.context.get("visit_data")
        if not visit_data:
            return self._error_response("'visit_data' required for visit summary")

        audience = request.context.get("audience", "patient")

        # Generate prompt
        prompt = self.prompts.generate_visit_summary(
            visit_data=visit_data,
            audience=audience
        )

        # Call MedGemma
        model_response = await self._call_medgemma(prompt)

        # Parse response
        parsed = self._parse_visit_summary_response(model_response)

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "visit_summary",
                "visit_summary": parsed.get("visit_summary", ""),
                "key_findings": parsed.get("key_findings", []),
                "treatment_plan": parsed.get("treatment_plan", ""),
                "follow_up_actions": parsed.get("follow_up_actions", []),
                "warning_signs": parsed.get("warning_signs", []),
                "questions_for_next_visit": parsed.get("questions_for_next_visit", []),
                "audience": audience
            },
            confidence=0.90,  # High confidence for summarization
            reasoning="Visit summary generated from documented clinical data",
            red_flags=[],
            requires_escalation=False
        )

    async def _handle_lab_results(self, request: AgentRequest) -> AgentResponse:
        """
        Explain lab results in patient-friendly language.

        Required context:
        - lab_results: List of lab test results
        Optional context:
        - patient_context: For contextualized interpretation
        """
        lab_results = request.context.get("lab_results")
        if not lab_results:
            return self._error_response("'lab_results' required for lab explanation")

        patient_context = request.context.get("patient_context")

        # Generate prompt
        prompt = self.prompts.contextualize_lab_results(
            lab_results=lab_results,
            patient_context=patient_context
        )

        # Call MedGemma
        model_response = await self._call_medgemma(prompt)

        # Parse response
        parsed = self._parse_lab_results_response(model_response)

        # Check for critical values
        critical_flags = [
            lab for lab in lab_results
            if lab.get("flag") == "critical"
        ]
        red_flags = [
            f"Critical lab value: {lab['test_name']}"
            for lab in critical_flags
        ]

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "lab_results",
                "overall_summary": parsed.get("overall_summary", ""),
                "individual_results_explained": parsed.get("individual_results_explained", []),
                "what_this_might_mean": parsed.get("what_this_might_mean", ""),
                "next_steps": parsed.get("next_steps", ""),
                "questions_for_doctor": parsed.get("questions_for_doctor", []),
                "critical_values_count": len(critical_flags)
            },
            confidence=0.80,
            reasoning="Lab results explained in patient context",
            red_flags=red_flags,
            requires_escalation=len(critical_flags) > 0
        )

    async def _handle_medication(self, request: AgentRequest) -> AgentResponse:
        """
        Provide medication information and education.

        Required context:
        - medication: Dictionary with medication details
        Optional context:
        - patient_context: For drug interaction checking
        """
        medication = request.context.get("medication")
        if not medication:
            return self._error_response("'medication' required for medication explanation")

        patient_context = request.context.get("patient_context")

        # Generate prompt
        prompt = self.prompts.medication_explanation(
            medication=medication,
            patient_context=patient_context
        )

        # Call MedGemma
        model_response = await self._call_medgemma(prompt)

        # Parse response
        parsed = self._parse_medication_response(model_response)

        # Check for drug interaction warnings (basic keyword detection)
        red_flags = []
        if patient_context and "allergies" in patient_context:
            med_name = medication.get("medication_name", "").lower()
            for allergy in patient_context.get("allergies", []):
                if allergy.lower() in med_name:
                    red_flags.append(f"⚠️ ALLERGY ALERT: Patient allergic to {allergy}")

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "medication",
                "medication_name": medication.get("medication_name", ""),
                "what_it_does": parsed.get("what_it_does", ""),
                "how_to_take_it": parsed.get("how_to_take_it", ""),
                "common_side_effects": parsed.get("common_side_effects", []),
                "important_warnings": parsed.get("important_warnings", []),
                "missed_dose": parsed.get("missed_dose", ""),
                "when_to_call_doctor": parsed.get("when_to_call_doctor", [])
            },
            confidence=0.85,
            reasoning="Medication information provided from evidence-based sources",
            red_flags=red_flags,
            requires_escalation=len(red_flags) > 0,
            suggested_agents=["drug_info"] if len(red_flags) > 0 else []
        )

    async def _handle_symptoms(self, request: AgentRequest) -> AgentResponse:
        """
        Assess symptoms and provide triage guidance (NOT diagnosis).

        Required context:
        - symptoms: List of reported symptoms
        Optional context:
        - duration: How long symptoms present
        - severity: mild/moderate/severe
        - patient_context: Patient information
        """
        symptoms = request.context.get("symptoms")
        if not symptoms:
            return self._error_response("'symptoms' required for symptom assessment")

        duration = request.context.get("duration")
        severity = request.context.get("severity")
        patient_context = request.context.get("patient_context")

        # Generate prompt
        prompt = self.prompts.symptom_checker(
            symptoms=symptoms,
            duration=duration,
            severity=severity,
            patient_context=patient_context
        )

        # Call MedGemma
        model_response = await self._call_medgemma(prompt)

        # Parse response
        parsed = self._parse_symptoms_response(model_response)

        # Determine urgency and escalation
        urgency = parsed.get("urgency_level", "ROUTINE")
        red_flags = parsed.get("red_flags", [])

        requires_escalation = (
            urgency in ["EMERGENCY", "URGENT"] or
            len(red_flags) > 0
        )

        # Confidence based on symptom clarity
        confidence = 0.75 if len(symptoms) >= 2 else 0.60

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "symptom_assessment",
                "symptoms": symptoms,
                "urgency_level": urgency,
                "possible_considerations": parsed.get("possible_considerations", []),
                "red_flags": red_flags,
                "self_care_suggestions": parsed.get("self_care_suggestions", []),
                "when_to_seek_care": parsed.get("when_to_seek_care", ""),
                "questions_to_prepare": parsed.get("questions_to_prepare", [])
            },
            confidence=confidence,
            reasoning=f"Symptom assessment: {urgency} level urgency",
            red_flags=red_flags,
            requires_escalation=requires_escalation,
            suggested_agents=["triage"] if requires_escalation else []
        )

    async def _call_medgemma(self, prompt: str) -> str:
        """
        Call MedGemma model with prompt.

        TODO: Replace with actual MedGemma API/inference call.
        Current implementation is a stub for testing.

        Integration options:
        1. Local inference with Ollama: ollama run medgemma
        2. HuggingFace Transformers: transformers.AutoModelForCausalLM
        3. vLLM for faster inference
        4. LangChain integration

        Args:
            prompt: Formatted prompt for MedGemma

        Returns:
            Model-generated response text
        """
        # STUB IMPLEMENTATION
        # In production, replace with actual model call:
        #
        # Option 1: Ollama
        # import ollama
        # response = ollama.generate(model='medgemma', prompt=prompt)
        # return response['response']
        #
        # Option 2: HuggingFace
        # from transformers import AutoTokenizer, AutoModelForCausalLM
        # tokenizer = AutoTokenizer.from_pretrained("google/medgemma-7b")
        # model = AutoModelForCausalLM.from_pretrained("google/medgemma-7b")
        # inputs = tokenizer(prompt, return_tensors="pt")
        # outputs = model.generate(**inputs, max_new_tokens=self.max_tokens)
        # return tokenizer.decode(outputs[0])
        #
        # Option 3: API endpoint (if MedGemma hosted)
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "http://localhost:8000/generate",
        #         json={"prompt": prompt, "max_tokens": self.max_tokens}
        #     )
        #     return response.json()["text"]

        # For now, return a structured stub response
        return """
**Main Answer:**
This is a placeholder response from the MedGemma stub. In production, this would be replaced with actual medical AI model output. The response would provide evidence-based information relevant to the user's question while maintaining appropriate medical safety boundaries.

**Key Points:**
- Professional medical evaluation recommended
- Multiple factors should be considered
- Individual circumstances vary

**When to Seek Care:**
If symptoms persist or worsen, consult a healthcare provider.

**Confidence Level:**
Moderate - This assessment is based on limited information and should be confirmed by a healthcare professional.

**Reasoning:**
Response generated using clinical guidelines and evidence-based medicine principles. However, individual assessment by a qualified healthcare provider is necessary for accurate diagnosis and treatment.
"""

    def _parse_qa_response(self, response: str) -> Dict[str, Any]:
        """Parse Medical Q&A response from MedGemma."""
        # Simple parser - in production, use more robust parsing
        lines = response.strip().split("\n")

        parsed = {
            "main_answer": "",
            "key_points": [],
            "when_to_seek_care": "",
            "confidence_explanation": "",
            "reasoning": ""
        }

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "**Main Answer:**" in line or "Main Answer:" in line:
                current_section = "main_answer"
            elif "**Key Points:**" in line or "Key Points:" in line:
                current_section = "key_points"
            elif "**When to Seek Care:**" in line or "When to Seek Care:" in line:
                current_section = "when_to_seek_care"
            elif "**Confidence Level:**" in line or "Confidence Level:" in line:
                current_section = "confidence_explanation"
            elif "**Reasoning:**" in line or "Reasoning:" in line:
                current_section = "reasoning"
            elif current_section:
                if current_section == "key_points" and line.startswith("-"):
                    parsed["key_points"].append(line[1:].strip())
                else:
                    if isinstance(parsed[current_section], list):
                        continue
                    parsed[current_section] += " " + line

        return parsed

    def _parse_simplify_response(self, response: str) -> Dict[str, Any]:
        """Parse text simplification response."""
        return {
            "simplified_explanation": response[:500],  # Stub parsing
            "key_terms_explained": {},
            "what_this_means": "Medical information explained in plain language",
            "questions_for_doctor": []
        }

    def _parse_visit_summary_response(self, response: str) -> Dict[str, Any]:
        """Parse visit summary response."""
        return {
            "visit_summary": response[:500],
            "key_findings": [],
            "treatment_plan": "Follow provider recommendations",
            "follow_up_actions": [],
            "warning_signs": [],
            "questions_for_next_visit": []
        }

    def _parse_lab_results_response(self, response: str) -> Dict[str, Any]:
        """Parse lab results explanation response."""
        return {
            "overall_summary": response[:300],
            "individual_results_explained": [],
            "what_this_might_mean": "Results should be discussed with your healthcare provider",
            "next_steps": "Follow up with your doctor",
            "questions_for_doctor": []
        }

    def _parse_medication_response(self, response: str) -> Dict[str, Any]:
        """Parse medication explanation response."""
        return {
            "what_it_does": "Medication information from evidence-based sources",
            "how_to_take_it": "Follow prescriber instructions",
            "common_side_effects": [],
            "important_warnings": [],
            "missed_dose": "Contact your pharmacist for guidance",
            "when_to_call_doctor": []
        }

    def _parse_symptoms_response(self, response: str) -> Dict[str, Any]:
        """Parse symptom assessment response."""
        # Extract urgency level from response
        urgency = "ROUTINE"
        response_upper = response.upper()
        if "EMERGENCY" in response_upper:
            urgency = "EMERGENCY"
        elif "URGENT" in response_upper:
            urgency = "URGENT"
        elif "SELF-CARE" in response_upper:
            urgency = "SELF-CARE"

        return {
            "urgency_level": urgency,
            "possible_considerations": [],
            "red_flags": [],
            "self_care_suggestions": [],
            "when_to_seek_care": "Consult healthcare provider if symptoms persist",
            "questions_to_prepare": []
        }

    def _detect_red_flags(self, question: str, parsed_response: Dict) -> List[str]:
        """Detect emergency red flags in question or response."""
        red_flags = []

        # Emergency keywords
        emergency_keywords = [
            "chest pain", "can't breathe", "difficulty breathing",
            "severe bleeding", "unconscious", "suicide", "suicidal",
            "stroke", "heart attack", "seizure", "severe headache",
            "can't move", "paralysis", "severe burn"
        ]

        question_lower = question.lower()
        for keyword in emergency_keywords:
            if keyword in question_lower:
                red_flags.append(f"⚠️ EMERGENCY KEYWORD: {keyword}")

        return red_flags

    def _calculate_confidence(self, parsed_response: Dict) -> float:
        """Calculate confidence score based on response quality."""
        confidence = 0.75  # Base confidence

        # Increase if reasoning provided
        if parsed_response.get("reasoning") and len(parsed_response["reasoning"]) > 50:
            confidence += 0.10

        # Increase if key points provided
        if len(parsed_response.get("key_points", [])) >= 2:
            confidence += 0.05

        return min(confidence, 0.95)  # Cap at 95%

    def _error_response(self, error_message: str) -> AgentResponse:
        """Generate error response."""
        return AgentResponse(
            success=False,
            agent_name=self.name,
            data={"error": error_message},
            confidence=0.0,
            reasoning=error_message,
            red_flags=[],
            requires_escalation=False
        )

    def get_capabilities(self) -> List[str]:
        return [
            "medical question", "explain", "simplify", "visit summary",
            "lab results", "medication", "symptoms", "q&a", "communication",
            "patient education", "health literacy"
        ]

    def get_description(self) -> str:
        return "Doctor-Patient Communication using MedGemma: Q&A, simplification, visit summaries, medication education"

    def get_confidence_threshold(self) -> float:
        return 0.60
