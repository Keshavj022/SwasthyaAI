"""
Diagnostic Support Agent - Provides differential diagnosis suggestions using MedGemma.

Responsibilities:
- Analyze symptoms and clinical presentation
- Generate ranked differential diagnoses with confidence scores
- Highlight key features and missing information
- Detect red flags and emergency conditions
- NEVER make definitive diagnoses - decision support ONLY

Current Implementation: MedGemma-powered with stub responses
Production: Ready for real MedGemma integration (see MEDGEMMA_INTEGRATION_GUIDE.md)
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from agents.prompts.medgemma_prompts import MedGemmaPrompts
from typing import List, Dict, Optional
import re


class DiagnosticSupportAgent(BaseAgent):
    """
    Provides differential diagnosis support based on symptoms and clinical data.
    Uses MedGemma for medical reasoning and differential generation.
    """

    def __init__(self):
        super().__init__()
        self.name = "diagnostic_support"
        self.prompts = MedGemmaPrompts()

        # MedGemma model configuration
        self.model_name = "medgemma-7b"  # or "medgemma-3b" for faster inference
        self.temperature = 0.2  # Lower temperature for more deterministic medical reasoning
        self.max_tokens = 2000  # Enough for comprehensive differential

        # Emergency symptom keywords for red flag detection
        self.emergency_keywords = {
            "chest pain", "chest pressure", "crushing chest",
            "difficulty breathing", "can't breathe", "shortness of breath", "dyspnea",
            "severe bleeding", "bleeding heavily",
            "loss of consciousness", "unconscious", "unresponsive",
            "severe headache", "worst headache",
            "confusion", "altered mental status", "disoriented",
            "facial drooping", "arm weakness", "slurred speech",  # Stroke signs
            "severe abdominal pain",
            "suicidal", "want to die",
            "severe allergic reaction", "throat closing",
            "seizure"
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Generate differential diagnosis based on clinical presentation.

        Supports multiple input formats:
        1. Free-text symptom description
        2. Structured clinical data (symptoms, vitals, exam findings)
        3. Integration with Health Memory Agent for patient context
        """
        # Extract clinical information from request
        symptoms = request.context.get("symptoms", [])
        duration = request.context.get("duration")
        severity = request.context.get("severity")
        vital_signs = request.context.get("vital_signs")
        physical_exam = request.context.get("physical_exam")
        patient_context = request.context.get("patient_context")

        # If no structured symptoms, try to extract from message
        if not symptoms:
            symptoms = self._extract_symptoms_from_message(request.message)

        # Validate input
        if not symptoms:
            return AgentResponse(
                success=True,
                agent_name=self.name,
                data={
                    "message": "Unable to identify specific symptoms for differential diagnosis.",
                    "suggestion": "Please describe your symptoms in more detail.",
                    "helpful_questions": [
                        "When did symptoms start?",
                        "How severe are they (mild/moderate/severe)?",
                        "Any associated symptoms?",
                        "Any recent exposures or travel?",
                        "Any changes in existing medical conditions?",
                        "Any new medications or allergies?"
                    ]
                },
                confidence=0.30,
                reasoning="Insufficient symptom information provided",
                red_flags=[],
                requires_escalation=False
            )

        # Check for emergency symptoms immediately
        emergency_detected, emergency_flags = self._detect_emergency_symptoms(symptoms, request.message)

        # Generate MedGemma prompt
        prompt = self.prompts.differential_diagnosis(
            symptoms=symptoms,
            duration=duration,
            severity=severity,
            physical_exam=physical_exam,
            vital_signs=vital_signs,
            patient_context=patient_context
        )

        # Call MedGemma model (stub for now)
        medgemma_response = await self._call_medgemma(prompt)

        # Parse MedGemma response into structured format
        parsed_data = self._parse_differential_response(medgemma_response)

        # Add detected symptoms and emergency flags
        parsed_data["symptoms_analyzed"] = symptoms
        parsed_data["emergency_detected"] = emergency_detected

        # Combine red flags from parsing and emergency detection
        all_red_flags = list(set(parsed_data.get("red_flags", []) + emergency_flags))

        # Determine confidence based on available information
        confidence = self._calculate_confidence(
            symptoms, duration, severity, vital_signs, physical_exam, patient_context
        )

        # Determine if escalation needed
        requires_escalation = emergency_detected or len(all_red_flags) > 0

        # Build reasoning
        reasoning_parts = [f"Analyzed {len(symptoms)} symptoms"]
        if duration:
            reasoning_parts.append(f"duration: {duration}")
        if severity:
            reasoning_parts.append(f"severity: {severity}")
        if vital_signs:
            reasoning_parts.append("with vital signs")
        if physical_exam:
            reasoning_parts.append("with physical exam findings")

        reasoning = f"Differential diagnosis based on: {', '.join(reasoning_parts)}"

        # Suggest follow-up agents if needed
        suggested_agents = []
        if emergency_detected:
            suggested_agents.append("triage")  # Triage agent for emergency assessment
        if patient_context and patient_context.get("medications"):
            suggested_agents.append("drug_info")  # Check medication interactions
        suggested_agents.append("health_memory")  # Always suggest checking patient history

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data=parsed_data,
            confidence=confidence,
            reasoning=reasoning,
            red_flags=all_red_flags,
            requires_escalation=requires_escalation,
            suggested_agents=suggested_agents
        )

    async def _call_medgemma(self, prompt: str) -> str:
        """
        Call MedGemma model for differential diagnosis generation.

        STUB IMPLEMENTATION - Ready for production integration.

        Production Options:
        1. Ollama: ollama.generate(model="medgemma:7b", prompt=prompt)
        2. HuggingFace: AutoModelForCausalLM.from_pretrained("google/medgemma-7b")
        3. vLLM: openai.ChatCompletion.create() pointing to vLLM server
        4. Remote API: requests.post(MEDGEMMA_ENDPOINT, json={"prompt": prompt})

        See MEDGEMMA_INTEGRATION_GUIDE.md for detailed integration steps.
        """
        # TODO: Replace with actual MedGemma call in production
        # For now, return structured stub response

        # Simulate comprehensive differential diagnosis response
        stub_response = """DIFFERENTIAL DIAGNOSIS:

1. Viral Upper Respiratory Infection (Common Cold)
   - Likelihood: Most Likely
   - Confidence: 0.75
   - Supports: Typical presentation of viral URI, common in community settings, symptom constellation fits
   - Against: None specifically contradicting
   - Missing Info: Complete duration, presence of sick contacts, response to symptomatic treatment

2. Acute Bronchitis
   - Likelihood: Possible
   - Confidence: 0.60
   - Supports: Persistent cough, possible chest symptoms
   - Against: Would typically see more productive cough, chest discomfort
   - Missing Info: Cough characteristics (dry vs productive), chest pain, smoking history

3. Influenza
   - Likelihood: Possible
   - Confidence: 0.55
   - Supports: Seasonal timing, systemic symptoms if present
   - Against: Usually more severe systemic symptoms (myalgias, high fever)
   - Missing Info: Fever degree, body aches, vaccination status, exposure history

4. COVID-19
   - Likelihood: Possible
   - Confidence: 0.50
   - Supports: Respiratory symptoms, ongoing community transmission
   - Against: Symptom profile may vary
   - Missing Info: Loss of taste/smell, known exposures, testing status

5. Bacterial Sinusitis
   - Likelihood: Less Likely
   - Confidence: 0.40
   - Supports: If nasal congestion and facial pain/pressure present
   - Against: Typically develops after initial viral URI, needs specific symptoms
   - Missing Info: Facial pain, purulent nasal discharge, symptom duration >7-10 days

6. Pneumonia (Community-Acquired)
   - Likelihood: Rare but Serious
   - Confidence: 0.30
   - Supports: Respiratory symptoms
   - Against: Would expect fever, dyspnea, productive cough, systemic symptoms
   - Missing Info: Vital signs (fever, tachypnea, hypoxia), chest exam findings, CXR

RED FLAGS:
None identified from current presentation. Would require immediate evaluation if patient develops:
- High fever (>103°F/39.4°C) not responding to antipyretics
- Difficulty breathing or shortness of breath at rest
- Chest pain
- Altered mental status or severe lethargy
- Signs of dehydration (decreased urination, dizziness)

RECOMMENDED WORKUP:
- Complete history and physical examination
- Vital signs including pulse oximetry
- If fever or concerning symptoms: Consider rapid flu test, COVID-19 test
- If pneumonia suspected: Chest X-ray, complete blood count
- Throat culture if pharyngitis with tonsillar exudates (rule out Strep)

CLINICAL CORRELATION NEEDED:
- Exact symptom onset and progression timeline
- Fever pattern and degree
- Sick contacts or exposures
- Vaccination status (flu, COVID-19, pneumococcal)
- Comorbidities (COPD, asthma, immunocompromise)
- Current medications and allergies
- Social history (smoking, occupation, travel)

**IMPORTANT DISCLAIMER:**
This differential diagnosis is for clinical decision support only. It does not replace comprehensive patient evaluation, clinical judgment, or diagnostic testing. All diagnoses must be confirmed through appropriate clinical assessment and investigations by a licensed healthcare provider.
"""
        return stub_response

    def _parse_differential_response(self, response: str) -> Dict:
        """
        Parse MedGemma's differential diagnosis response into structured format.
        """
        data = {
            "differential_diagnoses": [],
            "red_flags": [],
            "recommended_workup": [],
            "clinical_correlation_needed": [],
            "disclaimer": ""
        }

        # Extract differential diagnoses
        diff_section = re.search(
            r"DIFFERENTIAL DIAGNOSIS:(.*?)(?:RED FLAGS:|$)",
            response,
            re.DOTALL | re.IGNORECASE
        )

        if diff_section:
            diff_text = diff_section.group(1)
            # Parse individual diagnoses (numbered list)
            diagnosis_pattern = r"(\d+)\.\s+(.+?)\n\s*-\s*Likelihood:\s*(.+?)\n\s*-\s*Confidence:\s*([\d.]+)\n\s*-\s*Supports:\s*(.+?)\n\s*-\s*Against:\s*(.+?)\n\s*-\s*Missing Info:\s*(.+?)(?=\n\d+\.|RED FLAGS:|RECOMMENDED WORKUP:|$)"

            for match in re.finditer(diagnosis_pattern, diff_text, re.DOTALL):
                diagnosis = {
                    "rank": int(match.group(1)),
                    "condition": match.group(2).strip(),
                    "likelihood": match.group(3).strip(),
                    "confidence": float(match.group(4).strip()),
                    "supporting_features": match.group(5).strip(),
                    "contradicting_features": match.group(6).strip(),
                    "missing_information": match.group(7).strip()
                }
                data["differential_diagnoses"].append(diagnosis)

        # Extract red flags
        red_flags_section = re.search(
            r"RED FLAGS:(.*?)(?:RECOMMENDED WORKUP:|$)",
            response,
            re.DOTALL | re.IGNORECASE
        )

        if red_flags_section:
            flags_text = red_flags_section.group(1)
            # Extract bullet points or lines
            for line in flags_text.split('\n'):
                line = line.strip()
                if line and line.startswith('-'):
                    flag = line.lstrip('- ').strip()
                    if flag and flag.lower() != "none identified from current presentation":
                        data["red_flags"].append(flag)

        # Extract recommended workup
        workup_section = re.search(
            r"RECOMMENDED WORKUP:(.*?)(?:CLINICAL CORRELATION NEEDED:|$)",
            response,
            re.DOTALL | re.IGNORECASE
        )

        if workup_section:
            workup_text = workup_section.group(1)
            for line in workup_text.split('\n'):
                line = line.strip()
                if line and line.startswith('-'):
                    data["recommended_workup"].append(line.lstrip('- ').strip())

        # Extract clinical correlation needed
        correlation_section = re.search(
            r"CLINICAL CORRELATION NEEDED:(.*?)(?:\*\*IMPORTANT DISCLAIMER|\*\*Disclaimer|$)",
            response,
            re.DOTALL | re.IGNORECASE
        )

        if correlation_section:
            correlation_text = correlation_section.group(1)
            for line in correlation_text.split('\n'):
                line = line.strip()
                if line and line.startswith('-'):
                    data["clinical_correlation_needed"].append(line.lstrip('- ').strip())

        # Extract disclaimer
        disclaimer_match = re.search(
            r"\*\*(?:IMPORTANT )?DISCLAIMER[:\*]*\s*(.+?)(?:\n\n|$)",
            response,
            re.DOTALL | re.IGNORECASE
        )

        if disclaimer_match:
            data["disclaimer"] = disclaimer_match.group(1).strip()
        else:
            data["disclaimer"] = "This differential diagnosis is for clinical decision support only. NOT a definitive diagnosis."

        # Add summary statistics
        data["total_diagnoses_considered"] = len(data["differential_diagnoses"])
        data["most_likely_diagnosis"] = (
            data["differential_diagnoses"][0]["condition"]
            if data["differential_diagnoses"]
            else "Unknown - insufficient information"
        )

        return data

    def _extract_symptoms_from_message(self, message: str) -> List[str]:
        """
        Extract symptoms from free-text message (simple keyword matching).
        In production, could use NER (Named Entity Recognition) for better extraction.
        """
        symptom_keywords = [
            "fever", "cough", "headache", "nausea", "vomiting",
            "diarrhea", "pain", "fatigue", "shortness of breath",
            "chest pain", "abdominal pain", "dizziness", "weakness",
            "sore throat", "runny nose", "congestion", "chills",
            "body aches", "muscle pain", "joint pain", "rash",
            "swelling", "bleeding", "confusion", "seizure"
        ]

        message_lower = message.lower()
        detected = []

        for symptom in symptom_keywords:
            if symptom in message_lower:
                detected.append(symptom)

        return detected

    def _detect_emergency_symptoms(self, symptoms: List[str], message: str) -> tuple:
        """
        Detect emergency symptoms that require immediate escalation.

        Returns:
            (emergency_detected: bool, emergency_flags: List[str])
        """
        message_lower = message.lower()
        symptoms_lower = [s.lower() for s in symptoms]

        emergency_flags = []

        # Check both symptoms list and message
        all_text = " ".join(symptoms_lower) + " " + message_lower

        for emergency_keyword in self.emergency_keywords:
            if emergency_keyword in all_text:
                flag_message = f"EMERGENCY: {emergency_keyword.title()} requires immediate medical evaluation"
                emergency_flags.append(flag_message)

        emergency_detected = len(emergency_flags) > 0

        return emergency_detected, emergency_flags

    def _calculate_confidence(
        self,
        symptoms: List[str],
        duration: Optional[str],
        severity: Optional[str],
        vital_signs: Optional[Dict],
        physical_exam: Optional[str],
        patient_context: Optional[Dict]
    ) -> float:
        """
        Calculate confidence score based on available clinical information.

        More information = higher confidence in differential diagnosis.
        """
        confidence = 0.50  # Base confidence

        # Symptom information
        if len(symptoms) >= 3:
            confidence += 0.10
        elif len(symptoms) >= 1:
            confidence += 0.05

        # Temporal information
        if duration:
            confidence += 0.10

        if severity:
            confidence += 0.05

        # Objective data
        if vital_signs:
            confidence += 0.15

        if physical_exam:
            confidence += 0.10

        # Patient context
        if patient_context:
            if patient_context.get("age"):
                confidence += 0.03
            if patient_context.get("conditions"):
                confidence += 0.05
            if patient_context.get("medications"):
                confidence += 0.02

        # Cap at reasonable maximum
        return min(confidence, 0.85)  # Never 100% confident in differential without full workup

    def get_capabilities(self) -> List[str]:
        """Return keywords that trigger this agent."""
        return [
            "diagnosis", "diagnostic", "differential",
            "what do i have", "what could this be",
            "possible conditions", "what's wrong with me"
        ]

    def get_description(self) -> str:
        """Return agent description."""
        return "Differential diagnosis support - suggests POSSIBLE conditions based on symptoms (NOT definitive diagnosis)"

    def get_confidence_threshold(self) -> float:
        """Minimum confidence to activate this agent."""
        return 0.50
