"""
Prescription & Medicine Knowledge Agent.

Responsibilities:
- Explain medications (generic/brand names, mechanism of action)
- Detect drug-drug interactions
- Check drug-allergy interactions using Health Memory
- Provide dosage education and administration guidance
- Flag contraindications and warnings

CRITICAL CONSTRAINTS:
- NO PRESCRIBING AUTHORITY - Cannot recommend, suggest, or prescribe medications
- All outputs include mandatory pharmaceutical disclaimers
- Must cross-check patient allergies and current medications
- Always recommends consulting pharmacist or prescriber
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class DrugInfoAgent(BaseAgent):
    """
    Medication knowledge and safety checking agent.

    Provides information about medications while enforcing strict safety boundaries.
    NO prescribing authority - information only.
    """

    def __init__(self):
        super().__init__()
        self.name = "drug_info"

        # Drug interaction database (stub - replace with real database)
        self._load_drug_database()

    def _load_drug_database(self):
        """
        Load drug interaction database.

        In production, replace with:
        - FDA drug interaction database
        - DrugBank API
        - First Databank (FDB) MedKnowledge
        - Lexicomp drug interaction database
        """
        # STUB: Simplified interaction database for demonstration
        self.drug_interactions = {
            "warfarin": {
                "major_interactions": ["aspirin", "ibuprofen", "naproxen"],
                "moderate_interactions": ["acetaminophen"],
                "description": "Anticoagulant - increases bleeding risk"
            },
            "metformin": {
                "major_interactions": ["contrast dye"],
                "moderate_interactions": ["alcohol"],
                "description": "Diabetes medication - can cause lactic acidosis"
            },
            "lisinopril": {
                "major_interactions": ["potassium supplements", "spironolactone"],
                "moderate_interactions": ["ibuprofen", "naproxen"],
                "description": "ACE inhibitor - can increase potassium levels"
            },
            "levothyroxine": {
                "major_interactions": ["calcium", "iron supplements"],
                "moderate_interactions": ["antacids"],
                "description": "Thyroid hormone - absorption affected by supplements"
            }
        }

        # Drug allergy cross-reactivity
        self.allergy_cross_reactivity = {
            "penicillin": ["amoxicillin", "ampicillin", "piperacillin"],
            "sulfa": ["sulfamethoxazole", "furosemide", "celecoxib"],
            "aspirin": ["nsaids", "ibuprofen", "naproxen"]
        }

        # Contraindications by condition
        self.contraindications = {
            "pregnancy": ["warfarin", "statins", "ace_inhibitors"],
            "kidney_disease": ["metformin", "nsaids"],
            "liver_disease": ["acetaminophen_high_dose", "statins"]
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Route drug information request to appropriate handler.

        Expected context keys:
        - task_type: "explain", "check_interactions", "check_allergies", "dosage_info"
        - medication: Drug name or list of drugs
        - patient_id: For accessing patient history (optional)
        """
        task_type = request.context.get("task_type", "explain")

        handlers = {
            "explain": self._explain_medication,
            "check_interactions": self._check_drug_interactions,
            "check_allergies": self._check_allergy_safety,
            "dosage_info": self._provide_dosage_info,
            "comprehensive_check": self._comprehensive_safety_check
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

    async def _explain_medication(self, request: AgentRequest) -> AgentResponse:
        """
        Provide comprehensive medication information.

        Required context:
        - medication: Drug name (generic or brand)
        Optional context:
        - patient_context: Patient conditions/allergies for personalized info
        """
        medication = request.context.get("medication")
        if not medication:
            return self._error_response("'medication' required for drug information")

        medication_lower = medication.lower()

        # Check if in our database (stub)
        drug_info = self._get_drug_info(medication_lower)

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "medication_explanation",
                "medication_name": medication,
                "generic_name": drug_info.get("generic_name", ""),
                "brand_names": drug_info.get("brand_names", []),
                "drug_class": drug_info.get("drug_class", ""),
                "mechanism_of_action": drug_info.get("mechanism", ""),
                "common_uses": drug_info.get("uses", []),
                "typical_dosage_range": drug_info.get("dosage_range", ""),
                "administration": drug_info.get("administration", ""),
                "common_side_effects": drug_info.get("side_effects", []),
                "serious_side_effects": drug_info.get("serious_side_effects", []),
                "contraindications": drug_info.get("contraindications", []),
                "pregnancy_category": drug_info.get("pregnancy_category", ""),
                "storage": drug_info.get("storage", ""),
                "disclaimer": self._get_medication_disclaimer()
            },
            confidence=0.85,
            reasoning=f"Medication information provided for {medication}",
            red_flags=[],
            requires_escalation=False
        )

    async def _check_drug_interactions(self, request: AgentRequest) -> AgentResponse:
        """
        Check for drug-drug interactions.

        Required context:
        - medications: List of medication names
        OR
        - new_medication: New drug to check against patient's current medications
        - patient_id: Patient identifier to retrieve current medications
        """
        medications = request.context.get("medications", [])
        new_medication = request.context.get("new_medication")
        patient_id = request.context.get("patient_id")

        if not medications and not new_medication:
            return self._error_response("'medications' or 'new_medication' required")

        # If checking new medication against patient's current meds
        if new_medication and patient_id:
            # In production, retrieve from Health Memory Agent
            # For now, use stub current medications
            current_meds = request.context.get("current_medications", [])
            medications = current_meds + [new_medication]

        # Check all pairs for interactions
        interactions_found = []
        severity_counts = {"major": 0, "moderate": 0, "minor": 0}

        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                interaction = self._check_interaction_pair(
                    med1.lower(),
                    med2.lower()
                )
                if interaction:
                    interactions_found.append(interaction)
                    severity_counts[interaction["severity"]] += 1

        # Determine if escalation needed
        requires_escalation = severity_counts["major"] > 0
        red_flags = [
            f"⚠️ MAJOR DRUG INTERACTION: {interaction['drug1']} + {interaction['drug2']}"
            for interaction in interactions_found
            if interaction["severity"] == "major"
        ]

        # Calculate confidence
        confidence = 0.90 if len(medications) <= 5 else 0.75

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "drug_interaction_check",
                "medications_checked": medications,
                "total_interactions_found": len(interactions_found),
                "severity_breakdown": severity_counts,
                "interactions": interactions_found,
                "recommendation": self._get_interaction_recommendation(severity_counts),
                "disclaimer": "Drug interaction check is not comprehensive. Always consult your pharmacist or healthcare provider."
            },
            confidence=confidence,
            reasoning=f"Checked {len(medications)} medications for interactions",
            red_flags=red_flags,
            requires_escalation=requires_escalation,
            suggested_agents=["health_memory"] if patient_id else []
        )

    async def _check_allergy_safety(self, request: AgentRequest) -> AgentResponse:
        """
        Check medication against patient allergies.

        Required context:
        - medication: Drug to check
        - patient_allergies: List of known allergies
        OR
        - patient_id: To retrieve allergies from Health Memory
        """
        medication = request.context.get("medication")
        if not medication:
            return self._error_response("'medication' required for allergy check")

        # Get patient allergies
        patient_allergies = request.context.get("patient_allergies", [])
        patient_id = request.context.get("patient_id")

        if not patient_allergies and not patient_id:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                data={
                    "error": "Patient allergy information required",
                    "message": "Provide 'patient_allergies' list or 'patient_id' to retrieve from Health Memory"
                },
                confidence=0.0,
                reasoning="Cannot perform allergy check without patient allergy history",
                red_flags=[],
                requires_escalation=False
            )

        # Check for direct allergy match
        medication_lower = medication.lower()
        allergy_warnings = []
        cross_reactivity_warnings = []

        for allergy in patient_allergies:
            allergy_lower = allergy.lower()

            # Direct match
            if allergy_lower in medication_lower or medication_lower in allergy_lower:
                allergy_warnings.append({
                    "type": "DIRECT_ALLERGY",
                    "allergen": allergy,
                    "medication": medication,
                    "severity": "CRITICAL",
                    "message": f"⚠️ CRITICAL: Patient is allergic to {allergy}. DO NOT administer {medication}."
                })

            # Check cross-reactivity
            cross_reactive = self._check_cross_reactivity(medication_lower, allergy_lower)
            if cross_reactive:
                cross_reactivity_warnings.append({
                    "type": "CROSS_REACTIVITY",
                    "allergen": allergy,
                    "medication": medication,
                    "severity": "MAJOR",
                    "message": f"⚠️ WARNING: Patient allergic to {allergy}. {medication} may cause cross-reaction."
                })

        # Determine safety
        all_warnings = allergy_warnings + cross_reactivity_warnings
        is_safe = len(allergy_warnings) == 0

        red_flags = [w["message"] for w in allergy_warnings]

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "allergy_safety_check",
                "medication": medication,
                "patient_allergies": patient_allergies,
                "is_safe": is_safe,
                "direct_allergy_matches": len(allergy_warnings),
                "cross_reactivity_warnings": len(cross_reactivity_warnings),
                "all_warnings": all_warnings,
                "recommendation": self._get_allergy_recommendation(all_warnings),
                "disclaimer": "Allergy check based on known allergies only. Always verify with patient before administration."
            },
            confidence=0.95 if patient_allergies else 0.60,
            reasoning=f"Allergy check completed for {medication}",
            red_flags=red_flags,
            requires_escalation=not is_safe,
            suggested_agents=["health_memory"] if patient_id else []
        )

    async def _provide_dosage_info(self, request: AgentRequest) -> AgentResponse:
        """
        Provide dosage education and administration guidance.

        Required context:
        - medication: Drug name
        - indication: What condition is being treated (optional)
        - patient_context: Age, weight, kidney/liver function (optional)
        """
        medication = request.context.get("medication")
        if not medication:
            return self._error_response("'medication' required for dosage information")

        indication = request.context.get("indication", "general use")
        patient_context = request.context.get("patient_context", {})

        dosage_info = self._get_dosage_info(medication.lower(), indication, patient_context)

        # Check for dose adjustments needed
        warnings = []
        if patient_context.get("kidney_disease"):
            warnings.append("⚠️ Dose adjustment may be needed for kidney disease")
        if patient_context.get("liver_disease"):
            warnings.append("⚠️ Dose adjustment may be needed for liver disease")
        if patient_context.get("age") and patient_context["age"] >= 65:
            warnings.append("⚠️ Elderly patients may require lower doses")

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "dosage_information",
                "medication": medication,
                "indication": indication,
                "typical_adult_dose": dosage_info.get("adult_dose", ""),
                "pediatric_dose": dosage_info.get("pediatric_dose", ""),
                "max_daily_dose": dosage_info.get("max_dose", ""),
                "frequency": dosage_info.get("frequency", ""),
                "administration_instructions": dosage_info.get("instructions", ""),
                "food_interactions": dosage_info.get("food_interactions", ""),
                "missed_dose_guidance": dosage_info.get("missed_dose", ""),
                "warnings": warnings,
                "disclaimer": "Dosage information is general guidance only. Actual dosing must be determined by prescribing healthcare provider based on individual patient factors."
            },
            confidence=0.80,
            reasoning=f"Dosage education provided for {medication}",
            red_flags=warnings if len(warnings) > 0 else [],
            requires_escalation=False
        )

    async def _comprehensive_safety_check(self, request: AgentRequest) -> AgentResponse:
        """
        Comprehensive safety check: interactions + allergies + contraindications.

        Required context:
        - new_medication: Drug being considered
        - patient_id: Patient identifier
        OR
        - patient_allergies: List of allergies
        - current_medications: List of current medications
        - patient_conditions: List of medical conditions
        """
        new_medication = request.context.get("new_medication")
        if not new_medication:
            return self._error_response("'new_medication' required for safety check")

        patient_id = request.context.get("patient_id")
        patient_allergies = request.context.get("patient_allergies", [])
        current_medications = request.context.get("current_medications", [])
        patient_conditions = request.context.get("patient_conditions", [])

        # Perform all checks
        safety_issues = []
        red_flags = []

        # 1. Allergy check
        if patient_allergies:
            allergy_result = await self._check_allergy_safety(AgentRequest(
                message=request.message,
                user_id=request.user_id,
                context={
                    "medication": new_medication,
                    "patient_allergies": patient_allergies
                }
            ))
            if not allergy_result.data.get("is_safe"):
                safety_issues.extend(allergy_result.data.get("all_warnings", []))
                red_flags.extend(allergy_result.red_flags)

        # 2. Drug interaction check
        if current_medications:
            interaction_result = await self._check_drug_interactions(AgentRequest(
                message=request.message,
                user_id=request.user_id,
                context={
                    "new_medication": new_medication,
                    "current_medications": current_medications
                }
            ))
            major_interactions = [
                i for i in interaction_result.data.get("interactions", [])
                if i["severity"] == "major"
            ]
            if major_interactions:
                safety_issues.extend(major_interactions)
                red_flags.extend(interaction_result.red_flags)

        # 3. Contraindication check
        contraindications = self._check_contraindications(
            new_medication.lower(),
            patient_conditions
        )
        if contraindications:
            safety_issues.extend(contraindications)
            red_flags.extend([c["message"] for c in contraindications])

        # Overall safety determination
        is_safe = len(safety_issues) == 0
        severity_level = "UNSAFE" if not is_safe else "SAFE"

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "task": "comprehensive_safety_check",
                "new_medication": new_medication,
                "overall_safety": severity_level,
                "is_safe": is_safe,
                "total_safety_issues": len(safety_issues),
                "safety_issues": safety_issues,
                "recommendation": self._get_comprehensive_recommendation(is_safe, safety_issues),
                "next_steps": [
                    "Consult pharmacist before administering medication",
                    "Review patient chart for complete medication history",
                    "Verify patient allergies directly with patient",
                    "Consider alternative medications if safety concerns present"
                ],
                "disclaimer": "This safety check is based on available information only. Complete medication reconciliation and clinical judgment by healthcare provider is required."
            },
            confidence=0.85 if (patient_allergies and current_medications) else 0.65,
            reasoning=f"Comprehensive safety check for {new_medication}",
            red_flags=red_flags,
            requires_escalation=not is_safe,
            suggested_agents=["health_memory"] if patient_id else []
        )

    def _get_drug_info(self, medication: str) -> Dict[str, Any]:
        """Get drug information (stub implementation)."""
        # In production, query drug database (DrugBank, FDA, etc.)

        # Stub data for common medications
        drug_database = {
            "lisinopril": {
                "generic_name": "Lisinopril",
                "brand_names": ["Prinivil", "Zestril"],
                "drug_class": "ACE Inhibitor",
                "mechanism": "Blocks angiotensin-converting enzyme, reducing blood pressure",
                "uses": ["Hypertension", "Heart failure", "Post-MI cardioprotection"],
                "dosage_range": "5-40mg daily",
                "administration": "Oral, once daily, with or without food",
                "side_effects": ["Dry cough", "Dizziness", "Headache", "Fatigue"],
                "serious_side_effects": ["Angioedema", "Hyperkalemia", "Kidney dysfunction"],
                "contraindications": ["Pregnancy", "Angioedema history", "Bilateral renal artery stenosis"],
                "pregnancy_category": "D (avoid in pregnancy)",
                "storage": "Room temperature, protect from moisture"
            },
            "metformin": {
                "generic_name": "Metformin",
                "brand_names": ["Glucophage", "Fortamet"],
                "drug_class": "Biguanide antidiabetic",
                "mechanism": "Reduces hepatic glucose production, improves insulin sensitivity",
                "uses": ["Type 2 diabetes", "Prediabetes", "PCOS"],
                "dosage_range": "500-2000mg daily in divided doses",
                "administration": "Oral with meals to reduce GI upset",
                "side_effects": ["Nausea", "Diarrhea", "Abdominal discomfort"],
                "serious_side_effects": ["Lactic acidosis (rare)", "Vitamin B12 deficiency"],
                "contraindications": ["Severe kidney disease (eGFR <30)", "Metabolic acidosis"],
                "pregnancy_category": "B",
                "storage": "Room temperature, away from moisture"
            }
        }

        return drug_database.get(medication, {
            "generic_name": medication.title(),
            "brand_names": [],
            "drug_class": "Information not available in database",
            "mechanism": "Consult pharmacist or drug reference",
            "uses": [],
            "dosage_range": "Consult prescribing information",
            "administration": "Follow prescriber instructions",
            "side_effects": [],
            "serious_side_effects": [],
            "contraindications": [],
            "pregnancy_category": "Unknown - consult reference",
            "storage": "Follow package instructions"
        })

    def _check_interaction_pair(self, med1: str, med2: str) -> Optional[Dict[str, Any]]:
        """Check if two medications interact."""
        # Check both directions
        if med1 in self.drug_interactions:
            if med2 in self.drug_interactions[med1]["major_interactions"]:
                return {
                    "drug1": med1,
                    "drug2": med2,
                    "severity": "major",
                    "description": f"{med1} has major interaction with {med2}",
                    "clinical_effect": "Increased risk of adverse effects",
                    "management": "Consider alternative medication or close monitoring"
                }
            elif med2 in self.drug_interactions[med1]["moderate_interactions"]:
                return {
                    "drug1": med1,
                    "drug2": med2,
                    "severity": "moderate",
                    "description": f"{med1} has moderate interaction with {med2}",
                    "clinical_effect": "May require dose adjustment",
                    "management": "Monitor for adverse effects"
                }

        if med2 in self.drug_interactions:
            if med1 in self.drug_interactions[med2]["major_interactions"]:
                return {
                    "drug1": med2,
                    "drug2": med1,
                    "severity": "major",
                    "description": f"{med2} has major interaction with {med1}",
                    "clinical_effect": "Increased risk of adverse effects",
                    "management": "Consider alternative medication or close monitoring"
                }

        return None

    def _check_cross_reactivity(self, medication: str, allergy: str) -> bool:
        """Check if medication could cross-react with known allergy."""
        for allergen, cross_reactive_drugs in self.allergy_cross_reactivity.items():
            if allergen in allergy.lower():
                if any(drug in medication for drug in cross_reactive_drugs):
                    return True
        return False

    def _check_contraindications(
        self,
        medication: str,
        conditions: List[str]
    ) -> List[Dict[str, Any]]:
        """Check if medication is contraindicated for patient conditions."""
        contraindications_found = []

        for condition in conditions:
            condition_lower = condition.lower()
            for contraindicated_condition, drugs in self.contraindications.items():
                if contraindicated_condition in condition_lower:
                    if medication in drugs or any(drug in medication for drug in drugs):
                        contraindications_found.append({
                            "type": "CONTRAINDICATION",
                            "condition": condition,
                            "medication": medication,
                            "severity": "MAJOR",
                            "message": f"⚠️ {medication} is contraindicated in {condition}"
                        })

        return contraindications_found

    def _get_dosage_info(
        self,
        medication: str,
        indication: str,
        patient_context: Dict
    ) -> Dict[str, Any]:
        """Get dosage information (stub)."""
        # In production, query dosing database
        return {
            "adult_dose": "Follow prescriber instructions",
            "pediatric_dose": "Consult pediatric dosing guidelines",
            "max_dose": "Do not exceed prescribed amount",
            "frequency": "As directed by prescriber",
            "instructions": "Take as prescribed. Do not skip doses.",
            "food_interactions": "May take with or without food unless directed otherwise",
            "missed_dose": "Take as soon as remembered unless near next dose. Do not double dose."
        }

    def _get_medication_disclaimer(self) -> str:
        """Get mandatory medication information disclaimer."""
        return (
            "⚠️ MEDICATION INFORMATION DISCLAIMER: This information is for educational "
            "purposes only and does NOT constitute medical advice or a prescription. "
            "Only a licensed healthcare provider can prescribe medications. Always consult "
            "your doctor or pharmacist before starting, stopping, or changing any medication. "
            "Individual responses to medications vary. This system has NO prescribing authority."
        )

    def _get_interaction_recommendation(self, severity_counts: Dict) -> str:
        """Get recommendation based on interaction severity."""
        if severity_counts["major"] > 0:
            return (
                "⚠️ MAJOR DRUG INTERACTIONS DETECTED. Consult pharmacist or prescriber "
                "immediately before administering these medications together. Alternative "
                "medications or dosage adjustments may be necessary."
            )
        elif severity_counts["moderate"] > 0:
            return (
                "Moderate drug interactions detected. Inform healthcare provider. "
                "Monitoring may be required when using these medications together."
            )
        else:
            return "No significant drug interactions detected in database."

    def _get_allergy_recommendation(self, warnings: List[Dict]) -> str:
        """Get recommendation based on allergy warnings."""
        if any(w["severity"] == "CRITICAL" for w in warnings):
            return (
                "🚨 CRITICAL ALLERGY ALERT: DO NOT ADMINISTER. Patient has documented "
                "allergy to this medication. Seek alternative medication immediately."
            )
        elif any(w["severity"] == "MAJOR" for w in warnings):
            return (
                "⚠️ ALLERGY WARNING: Possible cross-reactivity with known allergy. "
                "Consult allergist or healthcare provider before administration."
            )
        else:
            return "No direct allergy matches found."

    def _get_comprehensive_recommendation(
        self,
        is_safe: bool,
        issues: List[Dict]
    ) -> str:
        """Get overall safety recommendation."""
        if not is_safe:
            return (
                "⚠️ SAFETY CONCERNS IDENTIFIED. Do NOT administer medication without "
                "consulting prescriber or pharmacist. Alternative medications should be "
                "considered. Complete medication reconciliation required."
            )
        else:
            return (
                "No immediate safety concerns identified in available data. However, "
                "always verify complete patient history and consult pharmacist before "
                "administering any new medication."
            )

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
            "drug", "medication", "medicine", "prescription", "interaction",
            "allergy", "dosage", "side effects", "contraindication"
        ]

    def get_description(self) -> str:
        return "Medication knowledge: drug interactions, allergy checking, dosage education (NO prescribing authority)"

    def get_confidence_threshold(self) -> float:
        return 0.70
