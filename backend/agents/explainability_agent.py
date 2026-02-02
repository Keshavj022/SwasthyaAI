"""
Explainability & Audit Agent - Makes AI decisions transparent and reviewable.

Responsibilities:
- Generate human-readable reasoning summaries
- Extract decision factors and alternatives
- Calculate explainability scores
- Format audit trails for clinician review

This agent wraps OTHER agents' outputs to enhance explainability.
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from typing import List, Dict, Any


class ExplainabilityAgent(BaseAgent):
    """
    Enhances AI outputs with human-readable explanations and reasoning.
    """

    def __init__(self):
        super().__init__()
        self.name = "explainability"

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        This agent is not directly invoked by users.
        It's used by the orchestrator to enhance other agents' outputs.

        For direct queries, return information about explainability.
        """
        return AgentResponse(
            success=True,
            agent_name=self.name,
            data={
                "message": "Explainability Agent - Enhances AI transparency",
                "purpose": "Makes AI decisions understandable and auditable",
                "features": [
                    "Human-readable reasoning summaries",
                    "Decision factor extraction",
                    "Alternative consideration tracking",
                    "Explainability scoring"
                ],
                "note": "This agent enhances outputs from other agents rather than responding to direct queries."
            },
            confidence=1.0,
            reasoning="Explainability agent information",
            red_flags=[],
            requires_escalation=False
        )

    def explain_agent_response(
        self,
        agent_response: AgentResponse,
        agent_type: str
    ) -> Dict[str, Any]:
        """
        Generate explainability metadata for any agent's response.

        Args:
            agent_response: The original agent response to explain
            agent_type: Type of agent (triage, diagnostic, etc.)

        Returns:
            Dict with reasoning_summary, decision_factors, alternatives, explainability_score
        """
        # Generate human-readable summary
        reasoning_summary = self._generate_reasoning_summary(agent_response, agent_type)

        # Extract decision factors
        decision_factors = self._extract_decision_factors(agent_response, agent_type)

        # Identify alternative considerations
        alternatives = self._identify_alternatives(agent_response, agent_type)

        # Calculate explainability score
        explainability_score = self._calculate_explainability_score(
            agent_response,
            decision_factors,
            alternatives
        )

        return {
            "reasoning_summary": reasoning_summary,
            "decision_factors": decision_factors,
            "alternative_considerations": alternatives,
            "explainability_score": explainability_score
        }

    def _generate_reasoning_summary(
        self,
        response: AgentResponse,
        agent_type: str
    ) -> str:
        """
        Generate human-readable reasoning summary.

        Example outputs:
        - "Emergency triage recommended immediate care based on cardiac symptoms (chest pain, arm radiation) which are classic indicators of potential myocardial infarction."
        - "Differential diagnosis suggests viral URI (70% confidence) based on fever and cough pattern, with pneumonia as alternative consideration (60%)."
        """
        if agent_type == "triage":
            return self._explain_triage(response)
        elif agent_type == "diagnostic_support":
            return self._explain_diagnostic(response)
        elif agent_type == "image_analysis":
            return self._explain_image_analysis(response)
        elif agent_type == "drug_info":
            return self._explain_drug_info(response)
        else:
            return self._generic_explanation(response)

    def _explain_triage(self, response: AgentResponse) -> str:
        """Generate reasoning summary for triage decisions"""
        data = response.data
        urgency = data.get("urgency_level", "UNKNOWN")
        red_flags = response.red_flags

        if urgency == "EMERGENCY":
            red_flag_desc = ", ".join(red_flags) if red_flags else "emergency indicators"
            return (
                f"EMERGENCY triage classification triggered by detection of {red_flag_desc}. "
                f"These symptoms match patterns associated with life-threatening conditions "
                f"requiring immediate medical evaluation. System confidence: {int(response.confidence * 100)}%."
            )
        elif urgency == "URGENT":
            return (
                f"URGENT triage classification based on symptom severity and pattern. "
                f"While not immediately life-threatening, symptoms warrant prompt medical "
                f"evaluation within 24 hours to prevent complications. "
                f"Confidence: {int(response.confidence * 100)}%."
            )
        else:
            return (
                f"ROUTINE triage classification - no immediate red flags detected. "
                f"Symptoms can be evaluated during standard clinic visit. Patient advised "
                f"to monitor for worsening and seek urgent care if condition changes. "
                f"Confidence: {int(response.confidence * 100)}%."
            )

    def _explain_diagnostic(self, response: AgentResponse) -> str:
        """Generate reasoning summary for diagnostic support"""
        data = response.data
        differential = data.get("differential_diagnosis", [])

        if not differential:
            return "Insufficient symptom information to generate differential diagnosis."

        top_condition = differential[0]
        condition_name = (
            top_condition.get("condition") if isinstance(top_condition, dict)
            else top_condition
        )

        num_alternatives = len(differential) - 1

        return (
            f"Differential diagnosis analysis suggests '{condition_name}' as most likely "
            f"explanation based on symptom pattern matching (confidence: {int(response.confidence * 100)}%). "
            f"{num_alternatives} alternative condition(s) considered. "
            f"Clinical correlation with physical exam, labs, and imaging required for "
            f"definitive diagnosis. This is decision support only, not a final diagnosis."
        )

    def _explain_image_analysis(self, response: AgentResponse) -> str:
        """Generate reasoning summary for image analysis"""
        data = response.data
        findings = data.get("findings", {})

        if isinstance(findings, dict):
            regions = findings.get("regions_of_interest", [])
            if regions:
                return (
                    f"AI image analysis identified {len(regions)} region(s) of interest "
                    f"requiring radiologist review. Findings are preliminary and must be "
                    f"confirmed by qualified radiologist. Confidence: {int(response.confidence * 100)}%."
                )

        return (
            f"Image analysis completed with confidence {int(response.confidence * 100)}%. "
            f"All AI-generated findings require validation by qualified radiologist. "
            f"This is a screening tool, not a diagnostic interpretation."
        )

    def _explain_drug_info(self, response: AgentResponse) -> str:
        """Generate reasoning summary for drug information"""
        data = response.data
        drug_name = data.get("drug_name", "medication")

        return (
            f"Drug information retrieved for {drug_name} from local medical database. "
            f"Information includes uses, side effects, and known interactions. "
            f"This is educational information only - NOT a prescription or dosage recommendation. "
            f"Always consult pharmacist or prescribing physician for personalized advice."
        )

    def _generic_explanation(self, response: AgentResponse) -> str:
        """Generic explanation for other agent types"""
        return (
            f"AI agent '{response.agent_name}' processed request with "
            f"{int(response.confidence * 100)}% confidence. "
            f"{response.reasoning or 'No detailed reasoning available.'}"
        )

    def _extract_decision_factors(
        self,
        response: AgentResponse,
        agent_type: str
    ) -> List[Dict[str, Any]]:
        """
        Extract key factors that influenced the decision.

        Returns list of factors with importance weights.
        """
        factors = []

        # Confidence level is always a factor
        factors.append({
            "factor": "AI Confidence Score",
            "value": f"{int(response.confidence * 100)}%",
            "importance": "high" if response.confidence >= 0.7 else "moderate",
            "description": f"Model confidence in prediction: {response.get_confidence_level().value}"
        })

        # Red flags (if any)
        if response.red_flags:
            factors.append({
                "factor": "Red Flags Detected",
                "value": len(response.red_flags),
                "importance": "critical",
                "description": f"Emergency indicators: {', '.join(response.red_flags[:3])}"
            })

        # Agent-specific factors
        data = response.data

        if agent_type == "triage":
            urgency = data.get("urgency_level", "UNKNOWN")
            factors.append({
                "factor": "Urgency Classification",
                "value": urgency,
                "importance": "critical" if urgency == "EMERGENCY" else "high",
                "description": f"Triage level determined: {urgency}"
            })

        elif agent_type == "diagnostic_support":
            symptoms = data.get("detected_symptoms", [])
            if symptoms:
                factors.append({
                    "factor": "Symptoms Analyzed",
                    "value": len(symptoms),
                    "importance": "high",
                    "description": f"Symptoms: {', '.join(symptoms[:5])}"
                })

        elif agent_type == "drug_info":
            interactions = data.get("known_interactions", [])
            if interactions:
                factors.append({
                    "factor": "Drug Interactions",
                    "value": len(interactions),
                    "importance": "high",
                    "description": f"Known interactions with: {', '.join(interactions[:3])}"
                })

        return factors

    def _identify_alternatives(
        self,
        response: AgentResponse,
        agent_type: str
    ) -> List[str]:
        """
        Identify alternative considerations or courses of action.
        """
        alternatives = []
        data = response.data

        if agent_type == "diagnostic_support":
            differential = data.get("differential_diagnosis", [])
            # List all conditions except the top one
            for i, condition in enumerate(differential[1:4], 1):  # Top 3 alternatives
                if isinstance(condition, dict):
                    cond_name = condition.get("condition", "Unknown")
                    conf = condition.get("confidence", 0)
                    alternatives.append(f"{cond_name} ({int(conf * 100)}% confidence)")
                else:
                    alternatives.append(str(condition))

        elif agent_type == "triage":
            urgency = data.get("urgency_level", "UNKNOWN")
            if urgency == "ROUTINE":
                alternatives.append("Urgent care visit if symptoms worsen")
                alternatives.append("Telemedicine consultation if preferred")
            elif urgency == "URGENT":
                alternatives.append("Emergency department if condition deteriorates")

        elif agent_type == "image_analysis":
            alternatives.append("Second opinion from specialist radiologist")
            alternatives.append("Additional imaging modalities if clinically indicated")

        return alternatives

    def _calculate_explainability_score(
        self,
        response: AgentResponse,
        decision_factors: List[Dict],
        alternatives: List[str]
    ) -> int:
        """
        Calculate how explainable/transparent this decision is (0-100).

        Factors:
        - Has reasoning provided?
        - Clear decision factors?
        - Alternatives considered?
        - Confidence appropriate?
        """
        score = 50  # Base score

        # Bonus for reasoning
        if response.reasoning and len(response.reasoning) > 20:
            score += 20

        # Bonus for multiple decision factors
        if len(decision_factors) >= 2:
            score += 10
        if len(decision_factors) >= 4:
            score += 5

        # Bonus for considering alternatives
        if len(alternatives) >= 1:
            score += 10
        if len(alternatives) >= 3:
            score += 5

        # Penalty for very low confidence without explanation
        if response.confidence < 0.3 and not response.reasoning:
            score -= 20

        # Bonus for high confidence with reasoning
        if response.confidence >= 0.8 and response.reasoning:
            score += 10

        return max(0, min(100, score))  # Clamp to 0-100

    def format_audit_summary(self, audit_entry: Dict[str, Any]) -> str:
        """
        Format audit log entry as human-readable summary for clinician review.

        Args:
            audit_entry: Full audit log entry dict

        Returns:
            Human-readable summary text
        """
        summary_lines = []

        # Header
        timestamp = audit_entry.get("timestamp", "Unknown time")
        agent = audit_entry.get("agent_name", "Unknown agent")
        summary_lines.append(f"=== AI Decision Audit Summary ===")
        summary_lines.append(f"Time: {timestamp}")
        summary_lines.append(f"Agent: {agent.upper()}")
        summary_lines.append("")

        # User query (de-identified)
        input_data = audit_entry.get("input_data", {})
        message = input_data.get("message", "No message")
        summary_lines.append(f"Query: {message[:200]}...")
        summary_lines.append("")

        # AI Decision
        output_data = audit_entry.get("output_data", {})
        confidence = audit_entry.get("confidence_score", 0)
        summary_lines.append(f"AI Confidence: {confidence}%")
        summary_lines.append("")

        # Reasoning
        reasoning = audit_entry.get("reasoning_summary", "No reasoning available")
        summary_lines.append(f"Reasoning:")
        summary_lines.append(f"  {reasoning}")
        summary_lines.append("")

        # Decision Factors
        factors = audit_entry.get("decision_factors", [])
        if factors:
            summary_lines.append(f"Key Decision Factors:")
            for factor in factors:
                importance = factor.get("importance", 'unknown')
                factor_name = factor.get("factor", 'Unknown')
                value = factor.get("value", '')
                summary_lines.append(f"  [{importance.upper()}] {factor_name}: {value}")
            summary_lines.append("")

        # Alternatives
        alternatives = audit_entry.get("alternative_considerations", [])
        if alternatives:
            summary_lines.append(f"Alternatives Considered:")
            for alt in alternatives:
                summary_lines.append(f"  - {alt}")
            summary_lines.append("")

        # Safety flags
        escalation = audit_entry.get("escalation_triggered")
        if escalation:
            summary_lines.append(f"⚠️ ESCALATION: {escalation}")
            summary_lines.append("")

        # Clinician override
        override = audit_entry.get("clinician_override")
        if override:
            summary_lines.append(f"📝 Clinician Override Recorded")
            summary_lines.append("")

        # Explainability score
        explain_score = audit_entry.get("explainability_score", 0)
        summary_lines.append(f"Explainability Score: {explain_score}/100")

        return "\n".join(summary_lines)

    def get_capabilities(self) -> List[str]:
        return ["explain", "why", "reasoning", "audit", "review decision"]

    def get_description(self) -> str:
        return "Generates human-readable explanations and reasoning summaries for AI decisions"

    def get_confidence_threshold(self) -> float:
        return 0.70
