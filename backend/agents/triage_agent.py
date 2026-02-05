"""
Triage & Emergency Risk Agent - Classifies urgency and identifies emergencies.

Responsibilities:
- Classify urgency levels (EMERGENCY, URGENT, ROUTINE, SELF_CARE)
- Identify life-threatening emergencies requiring immediate 911 call
- Apply rule-based logic with conservative safety thresholds
- Escalate to human healthcare providers when needed
- Provide clear explanations of urgency to users

Safety Philosophy:
- CONSERVATIVE: When in doubt, escalate
- RULE-BASED: Deterministic triage rules, not just AI opinion
- TIME-SENSITIVE: Emphasize that minutes matter in emergencies
- CLEAR COMMUNICATION: Users must understand urgency level

Current Implementation: Rule-based triage with comprehensive emergency detection
Production: Can be enhanced with vitals integration and patient history
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class TriageAgent(BaseAgent):
    """
    Emergency triage and urgency classification agent.
    Uses rule-based logic to identify emergencies and classify urgency.
    """

    def __init__(self):
        super().__init__()
        self.name = "triage"

        # CRITICAL: Life-threatening emergencies requiring 911
        self.emergency_keywords = {
            # Cardiac/Circulatory
            "chest pain", "chest pressure", "crushing chest pain",
            "severe chest pain", "heart attack",

            # Respiratory
            "can't breathe", "difficulty breathing", "cannot breathe",
            "shortness of breath severe", "choking", "gasping for air",
            "blue lips", "cyanosis",

            # Neurological
            "stroke", "facial drooping", "face drooping",
            "arm weakness", "can't move arm", "can't move leg",
            "slurred speech", "confusion sudden",
            "loss of consciousness", "unconscious", "unresponsive",
            "seizure", "convulsion",
            "worst headache of life", "thunderclap headache",

            # Trauma
            "severe bleeding", "bleeding won't stop", "hemorrhage",
            "severe head injury", "head trauma severe",
            "broken bone protruding", "compound fracture",

            # Allergic/Anaphylaxis
            "throat swelling", "throat closing", "can't swallow",
            "severe allergic reaction", "anaphylaxis",
            "tongue swelling", "face swelling sudden",

            # Mental Health
            "suicidal", "want to die", "going to kill myself",
            "homicidal", "going to hurt someone",

            # Other Critical
            "severe abdominal pain", "abdomen rigid",
            "vomiting blood", "coughing up blood", "hematemesis",
            "severe burn", "third degree burn",
            "severe poisoning", "overdose"
        }

        # URGENT: Need medical attention within hours (not 911, but ER/urgent care)
        self.urgent_keywords = {
            "high fever", "fever over 103", "fever won't go down",
            "severe pain", "pain 8/10", "pain 9/10", "pain 10/10",
            "dehydration severe", "can't keep fluids down",
            "difficulty urinating", "no urine",
            "severe diarrhea", "bloody stool", "black stool",
            "severe vomiting", "persistent vomiting",
            "severe headache", "migraine severe",
            "neck stiffness with fever", "stiff neck",
            "severe rash", "rash spreading rapidly",
            "infected wound", "wound red and swollen",
            "possible fracture", "may be broken",
            "eye injury", "vision loss sudden",
            "severe toothache", "dental abscess"
        }

        # Vital signs thresholds
        self.vital_thresholds = {
            # Adult thresholds (age >= 18)
            "adult": {
                "heart_rate": {"critical_low": 40, "low": 50, "high": 120, "critical_high": 140},
                "blood_pressure_systolic": {"critical_low": 90, "low": 100, "high": 160, "critical_high": 180},
                "blood_pressure_diastolic": {"critical_low": 60, "low": 65, "high": 100, "critical_high": 110},
                "temperature_c": {"critical_low": 35.0, "low": 36.0, "high": 38.5, "critical_high": 40.0},
                "respiratory_rate": {"critical_low": 8, "low": 12, "high": 24, "critical_high": 30},
                "oxygen_saturation": {"critical_low": 90, "low": 93}
            },
            # Pediatric thresholds (age < 18)
            "pediatric": {
                "heart_rate": {"critical_low": 60, "low": 70, "high": 140, "critical_high": 180},
                "temperature_c": {"critical_low": 35.0, "low": 36.0, "high": 38.5, "critical_high": 40.5},
                "respiratory_rate": {"critical_low": 12, "low": 16, "high": 40, "critical_high": 60},
                "oxygen_saturation": {"critical_low": 90, "low": 93}
            },
            # Elderly thresholds (age >= 65) - more conservative
            "elderly": {
                "heart_rate": {"critical_low": 50, "low": 55, "high": 110, "critical_high": 130},
                "blood_pressure_systolic": {"critical_low": 100, "low": 110, "high": 150, "critical_high": 170},
                "temperature_c": {"critical_low": 35.5, "low": 36.0, "high": 38.0, "critical_high": 39.5},
                "oxygen_saturation": {"critical_low": 92, "low": 94}
            }
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Perform triage assessment and classify urgency level.

        Expected context:
        - symptoms: List of symptoms
        - vital_signs: Dict of vital sign measurements (optional)
        - duration: How long symptoms present (optional)
        - severity: Patient's self-reported severity (optional)
        - patient_context: Age, conditions, pregnancy status (optional)
        """
        # Extract information
        symptoms = request.context.get("symptoms", [])
        message = request.message.lower()
        vital_signs = request.context.get("vital_signs")
        duration = request.context.get("duration", "").lower()
        severity = request.context.get("severity", "").lower()
        patient_context = request.context.get("patient_context", {})

        # Perform triage assessment
        urgency_level, reasoning, emergency_actions = self._assess_urgency(
            symptoms=symptoms,
            message=message,
            vital_signs=vital_signs,
            duration=duration,
            severity=severity,
            patient_context=patient_context
        )

        # Build red flags list
        red_flags = self._identify_red_flags(
            symptoms=symptoms,
            message=message,
            vital_signs=vital_signs,
            urgency_level=urgency_level
        )

        # Determine if escalation needed
        requires_escalation = urgency_level in ["EMERGENCY", "URGENT"]

        # Build recommendation
        recommendation = self._get_recommendation(urgency_level, emergency_actions)

        # Calculate confidence
        confidence = self._calculate_confidence(
            symptoms=symptoms,
            vital_signs=vital_signs,
            patient_context=patient_context
        )

        # Suggest next agents
        suggested_agents = []
        if urgency_level == "EMERGENCY":
            # For emergencies, no other agents - just call 911
            pass
        elif urgency_level == "URGENT":
            suggested_agents.append("diagnostic_support")  # Help understand condition
            suggested_agents.append("health_memory")  # Check patient history
        else:
            suggested_agents.append("diagnostic_support")
            suggested_agents.append("communication")  # Symptom guidance

        # Build response data
        data = {
            "urgency_level": urgency_level,
            "urgency_description": self._get_urgency_description(urgency_level),
            "recommended_action": recommendation["action"],
            "timeframe": recommendation["timeframe"],
            "reasoning": reasoning,
            "emergency_actions": emergency_actions if urgency_level == "EMERGENCY" else [],
            "when_to_escalate": self._get_escalation_criteria(urgency_level),
            "warning_signs": self._get_warning_signs(symptoms, patient_context),
            "disclaimer": self._get_triage_disclaimer()
        }

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data=data,
            confidence=confidence,
            reasoning=f"Triage assessment: {urgency_level} - {reasoning}",
            red_flags=red_flags,
            requires_escalation=requires_escalation,
            suggested_agents=suggested_agents
        )

    def _assess_urgency(
        self,
        symptoms: List[str],
        message: str,
        vital_signs: Optional[Dict],
        duration: str,
        severity: str,
        patient_context: Dict
    ) -> Tuple[str, str, List[str]]:
        """
        Assess urgency level using rule-based triage logic.

        Returns:
            (urgency_level, reasoning, emergency_actions)
        """
        emergency_actions = []
        reasoning_parts = []

        # RULE 1: Check for emergency keywords
        for keyword in self.emergency_keywords:
            if keyword in message or any(keyword in str(s).lower() for s in symptoms):
                reasoning_parts.append(f"Emergency keyword detected: '{keyword}'")
                emergency_actions.append("🚨 CALL 911 IMMEDIATELY")
                emergency_actions.append(f"Emergency symptom: {keyword}")
                return "EMERGENCY", "; ".join(reasoning_parts), emergency_actions

        # RULE 2: Check vital signs for critical values
        if vital_signs:
            vital_emergency, vital_reasoning = self._check_vital_signs(vital_signs, patient_context)
            if vital_emergency:
                reasoning_parts.append(vital_reasoning)
                emergency_actions.append("🚨 CALL 911 - Critical vital signs")
                emergency_actions.append(vital_reasoning)
                return "EMERGENCY", "; ".join(reasoning_parts), emergency_actions

        # RULE 3: Special populations - lower threshold
        special_pop_urgent, special_reasoning = self._check_special_populations(
            symptoms, patient_context, duration, severity
        )
        if special_pop_urgent:
            reasoning_parts.append(special_reasoning)
            if "EMERGENCY" in special_reasoning.upper():
                emergency_actions.append("🚨 CALL 911 - High-risk population")
                return "EMERGENCY", "; ".join(reasoning_parts), emergency_actions
            else:
                return "URGENT", "; ".join(reasoning_parts), []

        # RULE 4: Check for urgent keywords
        for keyword in self.urgent_keywords:
            if keyword in message or any(keyword in str(s).lower() for s in symptoms):
                reasoning_parts.append(f"Urgent keyword detected: '{keyword}'")
                return "URGENT", "; ".join(reasoning_parts), []

        # RULE 5: Severity and duration assessment
        if severity in ["severe", "very severe", "unbearable"]:
            reasoning_parts.append(f"Self-reported severity: {severity}")
            return "URGENT", "; ".join(reasoning_parts), []

        # RULE 6: Prolonged symptoms
        if self._is_prolonged(duration):
            reasoning_parts.append(f"Prolonged symptoms: {duration}")
            return "ROUTINE", "; ".join(reasoning_parts), []

        # RULE 7: Multiple symptoms
        if len(symptoms) >= 4:
            reasoning_parts.append(f"Multiple symptoms ({len(symptoms)}) - consider medical evaluation")
            return "ROUTINE", "; ".join(reasoning_parts), []

        # Default: Self-care appropriate
        reasoning_parts.append("Symptoms appear mild and manageable")
        return "SELF_CARE", "; ".join(reasoning_parts), []

    def _check_vital_signs(
        self,
        vital_signs: Dict,
        patient_context: Dict
    ) -> Tuple[bool, str]:
        """
        Check if vital signs indicate emergency.

        Returns:
            (is_emergency, reasoning)
        """
        age = patient_context.get("age", 30)

        # Determine which threshold set to use
        if age < 18:
            thresholds = self.vital_thresholds["pediatric"]
        elif age >= 65:
            thresholds = self.vital_thresholds["elderly"]
        else:
            thresholds = self.vital_thresholds["adult"]

        # Check each vital sign
        # Heart rate
        if "heart_rate" in vital_signs:
            hr = vital_signs["heart_rate"]
            hr_thresh = thresholds.get("heart_rate", {})
            if hr <= hr_thresh.get("critical_low", 0):
                return True, f"Critical bradycardia: HR {hr} bpm"
            if hr >= hr_thresh.get("critical_high", 999):
                return True, f"Critical tachycardia: HR {hr} bpm"

        # Blood pressure
        if "blood_pressure_systolic" in vital_signs:
            sbp = vital_signs["blood_pressure_systolic"]
            sbp_thresh = thresholds.get("blood_pressure_systolic", {})
            if sbp <= sbp_thresh.get("critical_low", 0):
                return True, f"Critical hypotension: BP {sbp} mmHg"
            if sbp >= sbp_thresh.get("critical_high", 999):
                return True, f"Hypertensive crisis: BP {sbp} mmHg"

        # Temperature
        if "temperature" in vital_signs:
            temp = vital_signs["temperature"]
            temp_thresh = thresholds.get("temperature_c", {})
            if temp <= temp_thresh.get("critical_low", 0):
                return True, f"Critical hypothermia: {temp}°C"
            if temp >= temp_thresh.get("critical_high", 999):
                return True, f"Critical hyperthermia: {temp}°C"

        # Respiratory rate
        if "respiratory_rate" in vital_signs:
            rr = vital_signs["respiratory_rate"]
            rr_thresh = thresholds.get("respiratory_rate", {})
            if rr <= rr_thresh.get("critical_low", 0):
                return True, f"Critical bradypnea: RR {rr}/min"
            if rr >= rr_thresh.get("critical_high", 999):
                return True, f"Critical tachypnea: RR {rr}/min"

        # Oxygen saturation
        if "oxygen_saturation" in vital_signs:
            spo2 = vital_signs["oxygen_saturation"]
            spo2_thresh = thresholds.get("oxygen_saturation", {})
            if spo2 <= spo2_thresh.get("critical_low", 0):
                return True, f"Critical hypoxia: SpO2 {spo2}%"

        return False, ""

    def _check_special_populations(
        self,
        symptoms: List[str],
        patient_context: Dict,
        duration: str,
        severity: str
    ) -> Tuple[bool, str]:
        """
        Apply more conservative thresholds for special populations.

        Special populations:
        - Infants (< 3 months)
        - Elderly (>= 75)
        - Pregnant
        - Immunocompromised
        - Chronic conditions (heart disease, diabetes, COPD)
        """
        age = patient_context.get("age")
        is_pregnant = patient_context.get("pregnant", False)
        conditions = patient_context.get("conditions", [])

        # Infant - very conservative
        if age and age < 0.25:  # < 3 months (0.25 years)
            if any(s.lower() in ["fever", "temperature", "not eating", "lethargic"] for s in symptoms):
                return True, "EMERGENCY: Infant with concerning symptoms"
            return True, "URGENT: Infant - medical evaluation needed"

        # Young child with fever
        if age and age < 5:
            if any("fever" in str(s).lower() for s in symptoms):
                if severity in ["severe", "high"]:
                    return True, "URGENT: Young child with high fever"

        # Elderly
        if age and age >= 75:
            if len(symptoms) >= 2:
                return True, "URGENT: Elderly patient with multiple symptoms"
            if any(s.lower() in ["confusion", "fall", "weakness", "chest"] for s in symptoms):
                return True, "EMERGENCY: Elderly with high-risk symptoms"

        # Pregnant
        if is_pregnant:
            pregnancy_concerns = ["bleeding", "pain", "contractions", "decreased movement", "headache severe"]
            if any(concern in str(symptoms).lower() for concern in pregnancy_concerns):
                return True, "URGENT: Pregnancy-related symptoms require OB evaluation"

        # Immunocompromised
        if any(c.lower() in ["hiv", "cancer", "chemotherapy", "transplant", "immunosuppressed"] for c in conditions):
            if any("fever" in str(s).lower() for s in symptoms):
                return True, "URGENT: Immunocompromised patient with fever"

        # Chronic heart/lung conditions
        high_risk_conditions = ["heart disease", "copd", "asthma", "heart failure", "coronary artery disease"]
        if any(cond.lower() in str(conditions).lower() for cond in high_risk_conditions):
            respiratory_symptoms = ["shortness of breath", "chest pain", "difficulty breathing"]
            if any(sym in str(symptoms).lower() for sym in respiratory_symptoms):
                return True, "EMERGENCY: High-risk patient with cardiac/respiratory symptoms"

        return False, ""

    def _is_prolonged(self, duration: str) -> bool:
        """Check if symptoms have been present for a prolonged period."""
        prolonged_indicators = [
            "weeks", "months", "week", "month",
            "7 days", "8 days", "9 days", "10 days",
            "two weeks", "three weeks"
        ]
        return any(indicator in duration for indicator in prolonged_indicators)

    def _identify_red_flags(
        self,
        symptoms: List[str],
        message: str,
        vital_signs: Optional[Dict],
        urgency_level: str
    ) -> List[str]:
        """Identify specific red flags for this presentation."""
        red_flags = []

        # Emergency keywords as red flags
        for keyword in self.emergency_keywords:
            if keyword in message or any(keyword in str(s).lower() for s in symptoms):
                red_flags.append(f"🚨 EMERGENCY: {keyword.title()}")

        # Vital sign red flags
        if vital_signs:
            if vital_signs.get("oxygen_saturation", 100) < 92:
                red_flags.append(f"🚨 Low oxygen: SpO2 {vital_signs['oxygen_saturation']}%")
            if vital_signs.get("temperature", 37) >= 40:
                red_flags.append(f"🚨 Very high fever: {vital_signs['temperature']}°C")
            if vital_signs.get("heart_rate", 70) >= 130:
                red_flags.append(f"⚠️ Rapid heart rate: {vital_signs['heart_rate']} bpm")

        # Combination red flags
        symptom_str = " ".join([str(s).lower() for s in symptoms]) + " " + message
        if "chest pain" in symptom_str and "shortness of breath" in symptom_str:
            red_flags.append("🚨 EMERGENCY: Chest pain + difficulty breathing")

        return red_flags

    def _get_recommendation(self, urgency_level: str, emergency_actions: List[str]) -> Dict:
        """Get recommended action based on urgency level."""
        recommendations = {
            "EMERGENCY": {
                "action": "🚨 CALL 911 IMMEDIATELY - DO NOT DRIVE YOURSELF",
                "timeframe": "NOW - Every minute counts"
            },
            "URGENT": {
                "action": "Seek medical care within 2-4 hours (ER or urgent care)",
                "timeframe": "Within 2-4 hours"
            },
            "ROUTINE": {
                "action": "Schedule appointment with primary care provider",
                "timeframe": "Within 1-3 days"
            },
            "SELF_CARE": {
                "action": "Self-care appropriate; monitor symptoms",
                "timeframe": "Self-monitor; seek care if worsens"
            }
        }

        return recommendations.get(urgency_level, recommendations["ROUTINE"])

    def _get_escalation_criteria(self, urgency_level: str) -> List[str]:
        """Get criteria for when to escalate to higher urgency level."""
        if urgency_level in ["EMERGENCY", "URGENT"]:
            return [
                "If symptoms worsen at any time",
                "If new symptoms develop",
                "If you feel something is seriously wrong"
            ]
        else:
            return [
                "Symptoms persist beyond 3-5 days",
                "Symptoms worsen instead of improve",
                "New concerning symptoms develop (fever, severe pain, etc.)",
                "You develop any emergency symptoms"
            ]

    def _get_warning_signs(self, symptoms: List[str], patient_context: Dict) -> List[str]:
        """Get warning signs to watch for."""
        warnings = [
            "Difficulty breathing or shortness of breath",
            "Chest pain or pressure",
            "Confusion or difficulty staying awake",
            "Severe or persistent vomiting",
            "Inability to keep down fluids"
        ]

        # Add age-specific warnings
        age = patient_context.get("age")
        if age and age < 5:
            warnings.extend([
                "Fever >104°F (40°C)",
                "Inconsolable crying",
                "Not drinking fluids"
            ])
        elif age and age >= 65:
            warnings.extend([
                "Falls or dizziness",
                "Confusion or memory problems"
            ])

        return warnings

    def _calculate_confidence(
        self,
        symptoms: List[str],
        vital_signs: Optional[Dict],
        patient_context: Dict
    ) -> float:
        """Calculate confidence in triage assessment."""
        confidence = 0.70  # Base confidence

        # More information = higher confidence
        if vital_signs:
            confidence += 0.15
        if patient_context.get("age"):
            confidence += 0.05
        if len(symptoms) >= 2:
            confidence += 0.05
        if patient_context.get("conditions"):
            confidence += 0.05

        return min(confidence, 0.95)

    def _get_urgency_description(self, urgency_level: str) -> str:
        """Get human-readable description of urgency level."""
        descriptions = {
            "EMERGENCY": "Life-threatening emergency requiring immediate 911 call",
            "URGENT": "Urgent medical attention needed within hours",
            "ROUTINE": "Medical evaluation recommended within days",
            "SELF_CARE": "Self-care appropriate with symptom monitoring"
        }
        return descriptions.get(urgency_level, "Unknown urgency level")

    def _get_triage_disclaimer(self) -> str:
        """Get mandatory triage disclaimer."""
        return (
            "⚠️ TRIAGE DISCLAIMER: This triage assessment is for guidance only and does NOT "
            "replace professional medical evaluation. If you believe you have a medical emergency, "
            "call 911 immediately. Trust your instincts - if you feel something is seriously wrong, "
            "seek emergency care. This system is CONSERVATIVE and may recommend higher levels of "
            "care out of caution for patient safety. Always consult healthcare providers for "
            "medical decisions."
        )

    def get_capabilities(self) -> List[str]:
        """Return keywords that trigger this agent."""
        return [
            "triage", "emergency", "urgent", "how serious",
            "should i go to er", "call 911", "ambulance",
            "urgency", "priority", "severity"
        ]

    def get_description(self) -> str:
        """Return agent description."""
        return "Emergency triage and urgency classification - identifies emergencies and recommends appropriate care level"

    def get_confidence_threshold(self) -> float:
        """Minimum confidence to activate this agent."""
        return 0.60
