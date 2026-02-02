# Agent Orchestrator Architecture

## Overview

The **Agent Orchestrator** is the central coordinator for the multi-agent healthcare AI system. It receives user requests, determines intent, routes to appropriate specialized agents, and ensures all outputs pass through safety and audit layers.

## Design Principles

1. **Single Entry Point**: All agent interactions go through the orchestrator
2. **Separation of Concerns**: Each agent has a single, well-defined responsibility
3. **Safety First**: All outputs pass through safety wrapper before returning to user
4. **Auditability**: All interactions are logged for compliance and review
5. **Extensibility**: New agents can be added without modifying core orchestrator logic
6. **Fail-Safe**: If routing fails, escalate to human or return safe default response

---

## Architecture Components

```
User Request
     ↓
[Orchestrator API]
     ↓
[Intent Classifier] ──→ Determines which agent(s) to invoke
     ↓
[Agent Registry] ──→ Looks up agent by capability
     ↓
[Selected Agent] ──→ Executes specialized task
     ↓
[Safety Wrapper] ──→ Applies disclaimers, checks guardrails
     ↓
[Audit Logger] ──→ Records interaction for compliance
     ↓
Response to User
```

---

## 1. Agent Registry

**Purpose**: Centralized catalog of all available agents with their capabilities.

**Responsibilities**:
- Register agents at startup
- Map agent capabilities to agent instances
- Provide lookup by agent name or capability
- Maintain agent metadata (description, confidence thresholds, etc.)

**Design**:
```python
{
    "diagnostic_support": DiagnosticAgent(),
    "triage": TriageAgent(),
    "image_analysis": ImageAnalysisAgent(),
    ...
}
```

---

## 2. Intent Classifier

**Purpose**: Analyze user input and determine which agent(s) should handle the request.

**Current Implementation**: Keyword-based pattern matching
**Future**: Fine-tuned NLP model or LLM-based classification

**Example Classifications**:
- "I have a fever and cough" → `triage` + `diagnostic_support`
- "Can you analyze this X-ray?" → `image_analysis`
- "What are side effects of aspirin?" → `drug_info`
- "Book appointment with cardiologist" → `appointment_scheduling`
- "Emergency! Chest pain!" → `triage` (priority escalation)

**Output**:
```python
{
    "primary_agent": "triage",
    "secondary_agents": ["diagnostic_support"],
    "urgency": "high",
    "confidence": 0.92
}
```

---

## 3. Base Agent Class

**Purpose**: Abstract base class that all agents inherit from.

**Interface**:
```python
class BaseAgent(ABC):
    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Execute agent's specialized task"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass

    @abstractmethod
    def get_confidence_threshold(self) -> float:
        """Minimum confidence to display results"""
        pass
```

**Benefits**:
- Enforces consistent interface across all agents
- Makes agents easily testable and mockable
- Simplifies orchestrator logic (all agents have same API)

---

## 4. Orchestrator Service

**Purpose**: Main coordination logic that ties all components together.

**Workflow**:
1. Receive user request (text, images, audio, etc.)
2. Classify intent → Determine which agent(s) to invoke
3. Validate request → Check for missing data, malformed input
4. Route to agent(s) → Call agent's `process()` method
5. Collect response(s) → Aggregate if multiple agents involved
6. Apply safety wrapper → Inject disclaimers, check guardrails
7. Log to audit trail → Record interaction for compliance
8. Return response → Send back to user

**Error Handling**:
- If intent classification fails → Return "unclear request" message
- If agent execution fails → Log error, return safe fallback response
- If confidence too low → Escalate to human or request more info
- If red flags detected → Trigger emergency escalation protocol

---

## 5. Safety Wrapper

**Purpose**: Apply medical safety boundaries defined in SAFETY_AND_SCOPE.md.

**Responsibilities**:
- Inject appropriate medical disclaimers based on agent type
- Check for prohibited language (definitive claims, prescriptions)
- Detect hallucinations or nonsensical outputs
- Enforce confidence thresholds
- Trigger red-flag escalations
- Prevent scope creep (agents staying within boundaries)

**Example Output Transformation**:
```python
# Before safety wrapper
"The patient likely has pneumonia based on symptoms."

# After safety wrapper
"⚠️ DIFFERENTIAL DIAGNOSIS SUPPORT
Possible condition: Pneumonia
Confidence: 68% 🟡 Moderate
Based on: fever, cough, chest discomfort

This is NOT a definitive diagnosis. Many conditions share similar
presentations. Consult a healthcare provider for evaluation."
```

---

## 6. Audit Logger

**Purpose**: Record all AI interactions for compliance, accountability, and future improvement.

**Logged Data** (per SAFETY_AND_SCOPE.md §7.2):
- Timestamp
- User ID (clinician or patient)
- Agent invoked
- Input data (de-identified)
- Output generated
- Confidence score
- Escalations triggered
- Clinician override actions (if any)

**Storage**: SQLite `audit_logs` table (already defined in models/system.py)

---

## Agent Catalog

### Core Agents (Implemented as Stubs)

| Agent Name | Capability Keywords | Purpose |
|------------|-------------------|---------|
| **Triage Agent** | `emergency`, `urgent`, `pain`, `symptoms` | Classify urgency, detect red flags |
| **Diagnostic Support Agent** | `diagnosis`, `condition`, `disease`, `symptoms` | Suggest differential diagnoses |
| **Image Analysis Agent** | `xray`, `scan`, `image`, `ct`, `mri` | Analyze medical images |
| **Drug Info Agent** | `medication`, `drug`, `prescription`, `interaction` | Drug information and interactions |
| **Communication Agent** | `explain`, `what is`, `tell me about` | Doctor-patient communication |
| **Voice Agent** | `transcribe`, `voice`, `speech` | Speech-to-text for hands-free |
| **Appointment Agent** | `appointment`, `schedule`, `book`, `availability` | Scheduling and calendar |
| **Referral Agent** | `specialist`, `referral`, `find doctor` | Find nearby doctors |
| **Health Memory Agent** | `history`, `past`, `previous`, `records` | Retrieve patient medical history |
| **Document Vault Agent** | `upload`, `store`, `retrieve`, `document` | Manage medical documents |
| **Daily Support Agent** | `reminder`, `check-in`, `track`, `monitor` | Daily health tracking |
| **Safety Agent** | (Always invoked) | Guardrails and safety checks |
| **Explainability Agent** | `why`, `explain decision`, `reasoning` | Explain AI outputs |

---

## Request/Response Flow

### Example 1: Simple Triage Request

**User Input**:
```json
{
    "user_id": "patient_123",
    "message": "I have a fever of 102°F and a bad cough for 3 days",
    "context": {
        "user_type": "patient",
        "age": 34,
        "gender": "F"
    }
}
```

**Orchestrator Processing**:
1. Intent Classifier → `triage` (confidence: 0.95)
2. Agent Registry → Lookup `TriageAgent`
3. Agent Execution → TriageAgent.process()
4. Agent Response:
   ```python
   {
       "urgency": "routine",
       "recommendation": "Schedule clinic visit within 24-48 hours",
       "red_flags": [],
       "confidence": 0.78
   }
   ```
5. Safety Wrapper → Inject disclaimer
6. Audit Logger → Log interaction
7. Return to User

**Final Response**:
```json
{
    "success": true,
    "agent": "triage",
    "response": {
        "urgency_level": "Routine (non-urgent)",
        "recommendation": "We recommend scheduling a clinic visit within 24-48 hours for evaluation.",
        "confidence": "78% (Moderate)",
        "reasoning": "Fever and cough are common symptoms that may indicate various conditions including viral infections, bacterial infections, or other respiratory illnesses.",
        "next_steps": [
            "Monitor temperature",
            "Stay hydrated",
            "Rest",
            "Contact clinic for appointment"
        ],
        "disclaimer": "⚠️ EMERGENCY ASSESSMENT\nThis triage suggestion is based on symptom patterns and is NOT a substitute for clinical judgment. When in doubt, seek immediate medical attention."
    },
    "audit_id": "audit_20260131_00123"
}
```

---

### Example 2: Emergency Escalation

**User Input**:
```json
{
    "user_id": "patient_456",
    "message": "Severe chest pain radiating to left arm, sweating, shortness of breath"
}
```

**Orchestrator Processing**:
1. Intent Classifier → `triage` (confidence: 0.99, **urgency: emergency**)
2. Agent Execution → TriageAgent.process()
3. Agent Response:
   ```python
   {
       "urgency": "EMERGENCY",
       "red_flags": ["chest_pain_cardiac", "radiation_to_arm", "diaphoresis"],
       "recommendation": "CALL EMERGENCY SERVICES IMMEDIATELY",
       "confidence": 1.0
   }
   ```
4. Safety Wrapper → Emergency escalation protocol triggered
5. Audit Logger → Log critical event

**Final Response**:
```json
{
    "success": true,
    "agent": "triage",
    "emergency": true,
    "response": {
        "urgency_level": "🚨 EMERGENCY",
        "warning": "🚨 EMERGENCY INDICATORS DETECTED 🚨",
        "action_required": "CALL EMERGENCY SERVICES (911) IMMEDIATELY or go to nearest emergency department",
        "red_flags_detected": [
            "Chest pain with radiation (possible cardiac event)",
            "Diaphoresis (sweating) with chest pain",
            "Shortness of breath with cardiac symptoms"
        ],
        "do_not_delay": "This situation requires immediate medical attention. Do not wait.",
        "disclaimer": "This is a potentially life-threatening emergency. Seek immediate medical care."
    }
}
```

---

### Example 3: Multi-Agent Coordination

**User Input**:
```json
{
    "user_id": "doctor_789",
    "message": "Patient presents with persistent cough, fever, and fatigue. Chest X-ray attached.",
    "attachments": ["xray_chest_lateral.jpg"],
    "context": {
        "user_type": "clinician"
    }
}
```

**Orchestrator Processing**:
1. Intent Classifier → `diagnostic_support` + `image_analysis` (multi-agent)
2. Parallel Execution:
   - DiagnosticSupportAgent.process() → Differential diagnosis based on symptoms
   - ImageAnalysisAgent.process() → Analyze chest X-ray
3. Aggregate Responses
4. Safety Wrapper → Apply both diagnostic + image disclaimers
5. Return combined response

**Final Response**:
```json
{
    "success": true,
    "agents": ["diagnostic_support", "image_analysis"],
    "response": {
        "diagnostic_suggestions": {
            "top_conditions": [
                {
                    "condition": "Community-acquired pneumonia",
                    "confidence": "72%",
                    "reasoning": "Matches 5/6 key symptoms: persistent cough, fever, fatigue, chest findings"
                },
                {
                    "condition": "Viral upper respiratory infection",
                    "confidence": "65%",
                    "reasoning": "Common presentation, symptom duration consistent"
                }
            ]
        },
        "image_findings": {
            "findings": "Possible infiltrate in right lower lobe",
            "confidence": "68%",
            "requires_radiologist_review": true,
            "regions_of_interest": ["RLL"]
        },
        "disclaimers": [
            "⚠️ DIFFERENTIAL DIAGNOSIS SUPPORT: This is NOT a definitive diagnosis...",
            "⚠️ IMAGE ANALYSIS SUPPORT: This AI-generated finding requires radiologist review..."
        ]
    }
}
```

---

## API Endpoints

### POST /api/orchestrator/query
**Purpose**: Main endpoint for all agent interactions

**Request**:
```json
{
    "user_id": "string",
    "message": "string",
    "attachments": ["file_ids"],
    "context": {
        "user_type": "patient|clinician|admin",
        "session_id": "string",
        "language": "en"
    }
}
```

**Response**:
```json
{
    "success": boolean,
    "agent": "string",
    "response": object,
    "confidence": float,
    "audit_id": "string",
    "emergency": boolean (optional),
    "timestamp": "ISO8601"
}
```

---

### GET /api/orchestrator/agents
**Purpose**: List all available agents and their capabilities

**Response**:
```json
{
    "agents": [
        {
            "name": "triage",
            "description": "Emergency triage and urgency classification",
            "capabilities": ["emergency", "urgent", "symptoms"],
            "status": "active"
        },
        ...
    ]
}
```

---

### GET /api/orchestrator/audit/{audit_id}
**Purpose**: Retrieve audit log for a specific interaction

**Response**:
```json
{
    "audit_id": "string",
    "timestamp": "ISO8601",
    "user_id": "string",
    "agent": "string",
    "input": object,
    "output": object,
    "confidence": float,
    "escalations": []
}
```

---

## Extensibility

### Adding a New Agent

1. **Create agent class** inheriting from `BaseAgent`
2. **Implement required methods**: `process()`, `get_capabilities()`, `get_confidence_threshold()`
3. **Register in agent registry** (add to `agents/__init__.py`)
4. **Update intent classifier** with new capability keywords
5. **Test with mock data**

**Example**:
```python
# backend/agents/nutrition_agent.py
from orchestrator.base import BaseAgent, AgentRequest, AgentResponse

class NutritionAgent(BaseAgent):
    def get_capabilities(self) -> List[str]:
        return ["nutrition", "diet", "calories", "meal plan"]

    async def process(self, request: AgentRequest) -> AgentResponse:
        # Implementation here
        return AgentResponse(
            success=True,
            data={"meal_plan": "..."},
            confidence=0.85
        )

    def get_confidence_threshold(self) -> float:
        return 0.60
```

---

## Testing Strategy

### Unit Tests
- Test each agent in isolation with mock inputs
- Test intent classifier with various queries
- Test safety wrapper with prohibited language

### Integration Tests
- Test full orchestrator flow from request to response
- Test multi-agent coordination
- Test emergency escalation paths

### Safety Tests
- Verify red-flag detection (100% recall required)
- Verify disclaimer injection
- Verify confidence threshold enforcement

---

## Performance Considerations

### Current Design (MVP)
- **Synchronous** execution (one agent at a time)
- **In-memory** agent registry
- **Simple** keyword-based intent classification

### Future Optimizations
- **Async/parallel** agent execution for multi-agent requests
- **Caching** for frequently accessed medical knowledge
- **ML-based** intent classification (faster + more accurate)
- **Load balancing** for high-traffic scenarios

---

## Security Considerations

1. **Input Validation**: Sanitize all user inputs before passing to agents
2. **Rate Limiting**: Prevent abuse of orchestrator API
3. **Authentication**: Verify user identity before logging to audit trail
4. **De-identification**: Remove PII from audit logs where possible
5. **Access Control**: Different agents available based on user role

---

## Compliance

The orchestrator enforces:
- **SAFETY_AND_SCOPE.md** boundaries via Safety Wrapper
- **Audit logging** per §7.2 (all interactions recorded)
- **Confidence thresholds** per §6 (minimum scores enforced)
- **Emergency escalation** per §5 (red flags trigger immediate alerts)
- **Explainability** per §7 (all outputs include reasoning)

---

## Summary

The Agent Orchestrator provides:
- ✅ Single, unified interface for all agent interactions
- ✅ Intelligent routing based on intent classification
- ✅ Safety-first design with mandatory guardrails
- ✅ Complete auditability and explainability
- ✅ Extensible architecture for adding new agents
- ✅ Offline-first (no external dependencies)

**Next Steps**:
1. Implement stub agents with mock responses
2. Test orchestrator with example queries
3. Integrate with frontend UI
4. Replace stubs with real medical AI models
