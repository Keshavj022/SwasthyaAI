"""
Test script for Communication Agent with MedGemma prompts.

This script demonstrates how to use the Communication Agent for various tasks:
- Medical Q&A
- Text simplification
- Visit summaries
- Lab results explanation
- Medication information
- Symptom assessment

Run: python test_communication_agent.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.communication_agent import CommunicationAgent
from orchestrator.base import AgentRequest
import json


async def test_medical_qa():
    """Test Medical Q&A functionality"""
    print("\n" + "="*80)
    print("TEST 1: Medical Q&A - High Blood Pressure Question")
    print("="*80)

    agent = CommunicationAgent()

    request = AgentRequest(
        message="What causes high blood pressure?",
        user_id="test_user",
        session_id="test_session",
        context={
            "task_type": "qa",
            "question": "What causes high blood pressure?",
            "patient_context": {
                "age": 52,
                "conditions": ["obesity", "prediabetes"],
                "medications": []
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"🤔 Reasoning: {response.reasoning}")
    print(f"\n📝 Response Data:")
    print(json.dumps(response.data, indent=2))
    print(f"\n🚩 Red Flags: {response.red_flags}")
    print(f"⚠️  Requires Escalation: {response.requires_escalation}")


async def test_simplify():
    """Test medical text simplification"""
    print("\n" + "="*80)
    print("TEST 2: Simplify Medical Text - COPD Exacerbation")
    print("="*80)

    agent = CommunicationAgent()

    medical_text = """Patient presents with acute exacerbation of chronic obstructive
    pulmonary disease (COPD) secondary to community-acquired pneumonia. Commenced on
    broad-spectrum antibiotics, bronchodilators, and corticosteroids. SpO2 on room air
    88%, improved to 94% on 2L O2 via nasal cannula."""

    request = AgentRequest(
        message="Explain this in simple terms",
        user_id="test_user",
        session_id="test_session",
        context={
            "task_type": "simplify",
            "medical_text": medical_text,
            "reading_level": "8th grade"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n📝 Simplified Explanation:")
    print(response.data.get("simplified_explanation", "N/A"))


async def test_visit_summary():
    """Test visit summary generation"""
    print("\n" + "="*80)
    print("TEST 3: Visit Summary - Cough and Fatigue")
    print("="*80)

    agent = CommunicationAgent()

    visit_data = {
        "chief_complaint": "Persistent cough for 2 weeks",
        "vitals": {
            "temperature": 37.8,
            "blood_pressure_systolic": 128,
            "blood_pressure_diastolic": 82,
            "heart_rate": 88,
            "oxygen_saturation": 96
        },
        "symptoms": ["cough", "fatigue", "night sweats"],
        "physical_exam_findings": "Lungs: Scattered rhonchi bilaterally. Heart: Regular rate and rhythm.",
        "assessment": "Likely acute bronchitis vs. atypical pneumonia.",
        "plan": "Azithromycin 500mg x 5 days. Supportive care. CXR ordered. Follow-up in 1 week.",
        "prescriptions": [
            {"medication": "Azithromycin", "dosage": "500mg daily"}
        ]
    }

    request = AgentRequest(
        message="Generate visit summary",
        user_id="test_user",
        session_id="test_session",
        context={
            "task_type": "visit_summary",
            "visit_data": visit_data,
            "audience": "patient"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n📋 Visit Summary:")
    print(response.data.get("visit_summary", "N/A")[:300] + "...")


async def test_lab_results():
    """Test lab results explanation"""
    print("\n" + "="*80)
    print("TEST 4: Lab Results - Prediabetes Panel")
    print("="*80)

    agent = CommunicationAgent()

    lab_results = [
        {
            "test_name": "Hemoglobin A1c",
            "result_value": "6.8",
            "result_unit": "%",
            "reference_range": "<5.7%",
            "flag": "high"
        },
        {
            "test_name": "Fasting Glucose",
            "result_value": "118",
            "result_unit": "mg/dL",
            "reference_range": "70-99 mg/dL",
            "flag": "high"
        },
        {
            "test_name": "Total Cholesterol",
            "result_value": "215",
            "result_unit": "mg/dL",
            "reference_range": "<200 mg/dL",
            "flag": "high"
        }
    ]

    request = AgentRequest(
        message="Explain my lab results",
        user_id="test_user",
        session_id="test_session",
        context={
            "task_type": "lab_results",
            "lab_results": lab_results,
            "patient_context": {
                "age": 55,
                "conditions": ["obesity"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🧪 Lab Results Summary:")
    print(response.data.get("overall_summary", "N/A")[:300] + "...")
    print(f"\n⚠️  Critical Values: {response.data.get('critical_values_count', 0)}")


async def test_medication():
    """Test medication explanation"""
    print("\n" + "="*80)
    print("TEST 5: Medication Information - Lisinopril")
    print("="*80)

    agent = CommunicationAgent()

    medication = {
        "medication_name": "Lisinopril",
        "dosage": "10mg",
        "frequency": "once daily",
        "indication": "High blood pressure"
    }

    request = AgentRequest(
        message="Tell me about my new medication",
        user_id="test_user",
        session_id="test_session",
        context={
            "task_type": "medication",
            "medication": medication,
            "patient_context": {
                "age": 58,
                "allergies": [],
                "medications": ["atorvastatin 20mg"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 What It Does:")
    print(response.data.get("what_it_does", "N/A")[:300] + "...")
    print(f"\n📋 How to Take:")
    print(response.data.get("how_to_take_it", "N/A")[:200] + "...")


async def test_symptoms_routine():
    """Test symptom assessment - routine case"""
    print("\n" + "="*80)
    print("TEST 6: Symptom Assessment - Headache (Routine)")
    print("="*80)

    agent = CommunicationAgent()

    request = AgentRequest(
        message="I have a headache and feel tired",
        user_id="test_user",
        session_id="test_session",
        context={
            "task_type": "symptoms",
            "symptoms": ["headache", "fatigue"],
            "duration": "2 days",
            "severity": "moderate",
            "patient_context": {
                "age": 34
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🚦 Urgency Level: {response.data.get('urgency_level')}")
    print(f"🚩 Red Flags: {response.red_flags}")
    print(f"⚠️  Requires Escalation: {response.requires_escalation}")
    print(f"\n💡 Self-Care Suggestions:")
    for suggestion in response.data.get("self_care_suggestions", [])[:3]:
        print(f"  - {suggestion}")


async def test_symptoms_emergency():
    """Test symptom assessment - emergency case"""
    print("\n" + "="*80)
    print("TEST 7: Symptom Assessment - Chest Pain (EMERGENCY)")
    print("="*80)

    agent = CommunicationAgent()

    request = AgentRequest(
        message="I'm having chest pain and shortness of breath",
        user_id="test_user",
        session_id="test_session",
        context={
            "task_type": "symptoms",
            "symptoms": ["chest pain", "shortness of breath"],
            "duration": "15 minutes",
            "severity": "severe",
            "patient_context": {
                "age": 62,
                "conditions": ["hypertension", "high cholesterol"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🚨 Urgency Level: {response.data.get('urgency_level')}")
    print(f"🚩 Red Flags ({len(response.red_flags)}):")
    for flag in response.red_flags:
        print(f"  {flag}")
    print(f"\n⚠️  REQUIRES ESCALATION: {response.requires_escalation}")
    print(f"🏥 Suggested Agents: {response.suggested_agents}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 COMMUNICATION AGENT TEST SUITE")
    print("Testing MedGemma-powered Doctor-Patient Communication")
    print("="*80)

    tests = [
        ("Medical Q&A", test_medical_qa),
        ("Text Simplification", test_simplify),
        ("Visit Summary", test_visit_summary),
        ("Lab Results", test_lab_results),
        ("Medication Info", test_medication),
        ("Symptoms (Routine)", test_symptoms_routine),
        ("Symptoms (Emergency)", test_symptoms_emergency)
    ]

    for test_name, test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("✅ TEST SUITE COMPLETE")
    print("="*80)
    print("\nNote: Current implementation uses stub responses.")
    print("To integrate real MedGemma model, see COMMUNICATION_AGENT_EXAMPLES.md")
    print("Integration options: Ollama, HuggingFace, vLLM, or Remote API")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
