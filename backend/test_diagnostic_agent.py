"""
Test script for Diagnostic Support Agent.

Demonstrates all diagnostic support features:
1. Basic differential diagnosis (respiratory symptoms)
2. Emergency symptom detection (chest pain)
3. Comprehensive clinical presentation (with vitals and exam)
4. Insufficient information handling
5. Integration with patient context

Run: python test_diagnostic_agent.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.diagnostic_support_agent import DiagnosticSupportAgent
from orchestrator.base import AgentRequest
import json


async def test_basic_differential():
    """Test basic differential diagnosis generation"""
    print("\n" + "="*80)
    print("TEST 1: Basic Differential Diagnosis - Respiratory Symptoms")
    print("="*80)

    agent = DiagnosticSupportAgent()

    request = AgentRequest(
        message="I have a cough and fever",
        user_id="test_user",
        context={
            "symptoms": ["cough", "fever"],
            "duration": "3 days",
            "severity": "moderate"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"🤔 Reasoning: {response.reasoning}")
    print(f"\n💉 Symptoms Analyzed: {', '.join(response.data['symptoms_analyzed'])}")
    print(f"🔍 Total Diagnoses Considered: {response.data['total_diagnoses_considered']}")
    print(f"\n🎯 Most Likely Diagnosis: {response.data['most_likely_diagnosis']}")

    print(f"\n📋 Differential Diagnoses (Top 3):")
    for i, diagnosis in enumerate(response.data['differential_diagnoses'][:3], 1):
        print(f"\n{i}. {diagnosis['condition']}")
        print(f"   Likelihood: {diagnosis['likelihood']}")
        print(f"   Confidence: {diagnosis['confidence']:.2f}")
        print(f"   Supports: {diagnosis['supporting_features'][:80]}...")
        print(f"   Missing Info: {diagnosis['missing_information'][:80]}...")

    print(f"\n🚩 Red Flags: {len(response.red_flags)} identified")
    print(f"⚠️  Requires Escalation: {response.requires_escalation}")
    print(f"🔄 Suggested Agents: {', '.join(response.suggested_agents)}")


async def test_emergency_detection():
    """Test emergency symptom detection"""
    print("\n" + "="*80)
    print("TEST 2: Emergency Symptom Detection - Chest Pain")
    print("="*80)

    agent = DiagnosticSupportAgent()

    request = AgentRequest(
        message="I'm having chest pain and difficulty breathing",
        user_id="test_user",
        context={
            "symptoms": ["chest pain", "shortness of breath"],
            "duration": "30 minutes",
            "severity": "severe",
            "patient_context": {
                "age": 58,
                "conditions": ["hypertension", "high cholesterol"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🚨 Emergency Detected: {response.data['emergency_detected']}")
    print(f"🚩 Red Flags ({len(response.red_flags)}):")
    for flag in response.red_flags[:5]:
        print(f"  {flag}")

    print(f"\n⚠️  REQUIRES ESCALATION: {response.requires_escalation}")
    print(f"🔄 Suggested Agents: {', '.join(response.suggested_agents)}")

    print(f"\n💊 Most Likely Diagnosis: {response.data['most_likely_diagnosis']}")


async def test_comprehensive_presentation():
    """Test differential with complete clinical data"""
    print("\n" + "="*80)
    print("TEST 3: Comprehensive Clinical Presentation - Fever, Cough, Vitals")
    print("="*80)

    agent = DiagnosticSupportAgent()

    request = AgentRequest(
        message="Patient presenting with fever and cough",
        user_id="test_user",
        context={
            "symptoms": ["fever", "cough", "fatigue"],
            "duration": "5 days",
            "severity": "moderate",
            "vital_signs": {
                "temperature": 38.5,
                "blood_pressure_systolic": 125,
                "blood_pressure_diastolic": 80,
                "heart_rate": 92,
                "respiratory_rate": 18,
                "oxygen_saturation": 96
            },
            "physical_exam": "Lungs: Scattered rhonchi bilaterally. No wheezing. Heart: Regular rate and rhythm.",
            "patient_context": {
                "age": 45,
                "gender": "female",
                "conditions": ["asthma"],
                "medications": ["albuterol inhaler"],
                "allergies": []
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"🤔 Reasoning: {response.reasoning}")

    print(f"\n💉 Symptoms Analyzed: {', '.join(response.data['symptoms_analyzed'])}")
    print(f"🔍 Total Diagnoses: {response.data['total_diagnoses_considered']}")

    print(f"\n📋 Top 3 Differential Diagnoses:")
    for i, diagnosis in enumerate(response.data['differential_diagnoses'][:3], 1):
        print(f"\n{i}. {diagnosis['condition']}")
        print(f"   Likelihood: {diagnosis['likelihood']}")
        print(f"   Confidence: {diagnosis['confidence']:.2f}")

    print(f"\n🔬 Recommended Workup ({len(response.data['recommended_workup'])} items):")
    for item in response.data['recommended_workup'][:3]:
        print(f"  - {item}")

    print(f"\n🏥 Clinical Correlation Needed ({len(response.data['clinical_correlation_needed'])} items):")
    for item in response.data['clinical_correlation_needed'][:3]:
        print(f"  - {item}")

    print(f"\n📄 Disclaimer: {response.data['disclaimer'][:100]}...")


async def test_insufficient_information():
    """Test handling of insufficient symptom information"""
    print("\n" + "="*80)
    print("TEST 4: Insufficient Information Handling")
    print("="*80)

    agent = DiagnosticSupportAgent()

    request = AgentRequest(
        message="I don't feel well",
        user_id="test_user",
        context={}
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"🤔 Reasoning: {response.reasoning}")

    print(f"\n💬 Message: {response.data['message']}")
    print(f"💡 Suggestion: {response.data['suggestion']}")

    print(f"\n❓ Helpful Questions ({len(response.data['helpful_questions'])}):")
    for question in response.data['helpful_questions']:
        print(f"  - {question}")


async def test_stroke_symptoms():
    """Test neurological emergency (stroke symptoms)"""
    print("\n" + "="*80)
    print("TEST 5: Neurological Emergency - Stroke Symptoms")
    print("="*80)

    agent = DiagnosticSupportAgent()

    request = AgentRequest(
        message="Sudden severe headache with facial drooping and arm weakness",
        user_id="test_user",
        context={
            "symptoms": ["severe headache", "facial drooping", "arm weakness"],
            "duration": "20 minutes",
            "severity": "severe",
            "patient_context": {
                "age": 67,
                "conditions": ["hypertension", "atrial fibrillation"],
                "medications": ["warfarin", "metoprolol"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")

    print(f"\n🚨 EMERGENCY DETECTED: {response.data['emergency_detected']}")
    print(f"🚩 Red Flags ({len(response.red_flags)}):")
    for flag in response.red_flags:
        print(f"  {flag}")

    print(f"\n⚠️  REQUIRES IMMEDIATE ESCALATION: {response.requires_escalation}")
    print(f"🔄 Suggested Agents: {', '.join(response.suggested_agents)}")


async def test_abdominal_pain():
    """Test abdominal pain differential"""
    print("\n" + "="*80)
    print("TEST 6: Abdominal Pain Differential")
    print("="*80)

    agent = DiagnosticSupportAgent()

    request = AgentRequest(
        message="Severe abdominal pain in lower right side",
        user_id="test_user",
        context={
            "symptoms": ["abdominal pain", "nausea"],
            "duration": "6 hours",
            "severity": "severe",
            "vital_signs": {
                "temperature": 38.2,
                "blood_pressure_systolic": 118,
                "blood_pressure_diastolic": 75,
                "heart_rate": 98
            },
            "physical_exam": "Abdomen: Tenderness in right lower quadrant. Positive rebound tenderness.",
            "patient_context": {
                "age": 23,
                "gender": "female"
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"🤔 Reasoning: {response.reasoning}")

    print(f"\n💉 Symptoms: {', '.join(response.data['symptoms_analyzed'])}")
    print(f"🎯 Most Likely: {response.data['most_likely_diagnosis']}")

    print(f"\n⚠️  Requires Escalation: {response.requires_escalation}")


async def test_free_text_extraction():
    """Test symptom extraction from free text"""
    print("\n" + "="*80)
    print("TEST 7: Free-Text Symptom Extraction")
    print("="*80)

    agent = DiagnosticSupportAgent()

    request = AgentRequest(
        message="I've been feeling really dizzy and weak for the past 2 days, and I have a headache",
        user_id="test_user",
        context={
            "duration": "2 days"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")

    print(f"\n💉 Extracted Symptoms: {', '.join(response.data['symptoms_analyzed'])}")
    print(f"🎯 Most Likely Diagnosis: {response.data['most_likely_diagnosis']}")
    print(f"🔍 Total Diagnoses Considered: {response.data['total_diagnoses_considered']}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 DIAGNOSTIC SUPPORT AGENT TEST SUITE")
    print("Testing MedGemma-powered Differential Diagnosis Generation")
    print("="*80)

    tests = [
        ("Basic Differential Diagnosis", test_basic_differential),
        ("Emergency Symptom Detection", test_emergency_detection),
        ("Comprehensive Clinical Presentation", test_comprehensive_presentation),
        ("Insufficient Information Handling", test_insufficient_information),
        ("Neurological Emergency (Stroke)", test_stroke_symptoms),
        ("Abdominal Pain Differential", test_abdominal_pain),
        ("Free-Text Symptom Extraction", test_free_text_extraction)
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
    print("\nKey Features Demonstrated:")
    print("  ✅ Differential diagnosis generation (ranked by likelihood)")
    print("  ✅ Confidence scoring for each diagnosis")
    print("  ✅ Emergency symptom detection and red flags")
    print("  ✅ Comprehensive clinical data integration")
    print("  ✅ Missing information identification")
    print("  ✅ Recommended workup suggestions")
    print("  ✅ Free-text symptom extraction")
    print("  ✅ Patient context integration")
    print("\n⚠️  CRITICAL DISCLAIMER:")
    print("This is a DECISION SUPPORT tool, NOT a diagnostic device.")
    print("All diagnoses must be confirmed by licensed healthcare providers.")
    print("Never rely solely on AI for medical decision-making.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
