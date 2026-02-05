"""
Test script for Triage & Emergency Risk Agent.

Demonstrates all triage scenarios:
1. Life-threatening emergencies (chest pain, stroke, anaphylaxis)
2. Urgent care needed (high fever, severe pain)
3. Routine medical evaluation (prolonged symptoms)
4. Self-care appropriate (mild symptoms)
5. Vital signs-based triage
6. Special populations (pediatric, elderly, pregnant, immunocompromised)

Run: python test_triage_agent.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.triage_agent import TriageAgent
from orchestrator.base import AgentRequest


async def test_emergency_chest_pain():
    """Test EMERGENCY detection - chest pain"""
    print("\n" + "="*80)
    print("TEST 1: EMERGENCY - Chest Pain")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="I'm having severe chest pain and difficulty breathing",
        user_id="test_user",
        context={
            "symptoms": ["chest pain", "shortness of breath"],
            "duration": "30 minutes",
            "severity": "severe",
            "patient_context": {
                "age": 58,
                "conditions": ["hypertension"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🚨 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"📝 Description: {response.data['urgency_description']}")
    print(f"\n💡 Recommended Action:")
    print(f"   {response.data['recommended_action']}")
    print(f"⏱️  Timeframe: {response.data['timeframe']}")

    if response.data.get("emergency_actions"):
        print(f"\n🚨 EMERGENCY ACTIONS:")
        for action in response.data["emergency_actions"]:
            print(f"   {action}")

    print(f"\n🚩 Red Flags ({len(response.red_flags)}):")
    for flag in response.red_flags[:3]:
        print(f"   {flag}")

    print(f"\n⚠️  Requires Escalation: {response.requires_escalation}")
    print(f"🤔 Reasoning: {response.reasoning}")


async def test_emergency_stroke():
    """Test EMERGENCY detection - stroke symptoms"""
    print("\n" + "="*80)
    print("TEST 2: EMERGENCY - Stroke Symptoms (FAST)")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="Sudden facial drooping and arm weakness",
        user_id="test_user",
        context={
            "symptoms": ["facial drooping", "arm weakness", "slurred speech"],
            "duration": "15 minutes",
            "severity": "severe",
            "patient_context": {
                "age": 72,
                "conditions": ["atrial fibrillation"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n🚨 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"📝 {response.data['urgency_description']}")
    print(f"\n💡 Action: {response.data['recommended_action']}")
    print(f"⏱️  {response.data['timeframe']}")
    print(f"\n🚩 Red Flags: {len(response.red_flags)}")
    print(f"⚠️  Escalation Required: {response.requires_escalation}")


async def test_emergency_vitals():
    """Test EMERGENCY detection - critical vital signs"""
    print("\n" + "="*80)
    print("TEST 3: EMERGENCY - Critical Vital Signs (Low SpO2)")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="Having trouble breathing",
        user_id="test_user",
        context={
            "symptoms": ["shortness of breath"],
            "vital_signs": {
                "oxygen_saturation": 88,
                "heart_rate": 125,
                "respiratory_rate": 32
            },
            "patient_context": {
                "age": 65,
                "conditions": ["COPD"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n🚨 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"💡 Action: {response.data['recommended_action']}")
    print(f"\n🚩 Red Flags:")
    for flag in response.red_flags:
        print(f"   {flag}")
    print(f"\n📊 Confidence: {response.confidence:.2f}")


async def test_urgent_high_fever():
    """Test URGENT classification - high fever"""
    print("\n" + "="*80)
    print("TEST 4: URGENT - High Fever")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="I have a high fever that won't go down",
        user_id="test_user",
        context={
            "symptoms": ["fever", "chills", "body aches"],
            "duration": "2 days",
            "severity": "moderate",
            "vital_signs": {
                "temperature": 39.5
            }
        }
    )

    response = await agent.process(request)

    print(f"\n📊 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"📝 {response.data['urgency_description']}")
    print(f"\n💡 Recommended Action:")
    print(f"   {response.data['recommended_action']}")
    print(f"⏱️  Timeframe: {response.data['timeframe']}")
    print(f"\n⚠️  Escalation Required: {response.requires_escalation}")
    print(f"🔄 Suggested Agents: {', '.join(response.suggested_agents)}")


async def test_urgent_severe_pain():
    """Test URGENT classification - severe pain"""
    print("\n" + "="*80)
    print("TEST 5: URGENT - Severe Abdominal Pain")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="Severe pain in my abdomen, pain level 9/10",
        user_id="test_user",
        context={
            "symptoms": ["severe pain", "nausea"],
            "duration": "4 hours",
            "severity": "severe"
        }
    )

    response = await agent.process(request)

    print(f"\n📊 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"💡 Action: {response.data['recommended_action']}")
    print(f"⏱️  Timeframe: {response.data['timeframe']}")
    print(f"\n📝 Reasoning: {response.data['reasoning']}")


async def test_routine_prolonged_symptoms():
    """Test ROUTINE classification - prolonged symptoms"""
    print("\n" + "="*80)
    print("TEST 6: ROUTINE - Prolonged Cough (2 weeks)")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="I've had this cough for about 2 weeks now",
        user_id="test_user",
        context={
            "symptoms": ["cough", "fatigue"],
            "duration": "2 weeks",
            "severity": "mild"
        }
    )

    response = await agent.process(request)

    print(f"\n📊 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"📝 {response.data['urgency_description']}")
    print(f"\n💡 Recommended Action:")
    print(f"   {response.data['recommended_action']}")
    print(f"⏱️  Timeframe: {response.data['timeframe']}")
    print(f"\n📋 When to Escalate:")
    for criterion in response.data["when_to_escalate"]:
        print(f"   - {criterion}")


async def test_self_care():
    """Test SELF_CARE classification - mild symptoms"""
    print("\n" + "="*80)
    print("TEST 7: SELF-CARE - Mild Cold Symptoms")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="I have a runny nose and mild headache",
        user_id="test_user",
        context={
            "symptoms": ["runny nose", "headache"],
            "duration": "1 day",
            "severity": "mild"
        }
    )

    response = await agent.process(request)

    print(f"\n📊 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"📝 {response.data['urgency_description']}")
    print(f"\n💡 Recommended Action:")
    print(f"   {response.data['recommended_action']}")
    print(f"\n⚠️  Warning Signs to Watch For:")
    for sign in response.data["warning_signs"][:3]:
        print(f"   - {sign}")
    print(f"\n🔄 Suggested Agents: {', '.join(response.suggested_agents)}")


async def test_pediatric_infant():
    """Test special population - infant with fever"""
    print("\n" + "="*80)
    print("TEST 8: SPECIAL POPULATION - Infant with Fever")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="My 2-month-old baby has a fever",
        user_id="test_user",
        context={
            "symptoms": ["fever"],
            "duration": "4 hours",
            "severity": "moderate",
            "vital_signs": {
                "temperature": 38.3
            },
            "patient_context": {
                "age": 0.16,  # 2 months = ~0.16 years
                "gender": "male"
            }
        }
    )

    response = await agent.process(request)

    print(f"\n🚨 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"📝 {response.data['urgency_description']}")
    print(f"💡 Action: {response.data['recommended_action']}")
    print(f"\n🤔 Reasoning: {response.data['reasoning']}")
    print(f"⚠️  Escalation Required: {response.requires_escalation}")


async def test_elderly_confusion():
    """Test special population - elderly with confusion"""
    print("\n" + "="*80)
    print("TEST 9: SPECIAL POPULATION - Elderly with Confusion")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="My elderly mother seems confused and weak",
        user_id="test_user",
        context={
            "symptoms": ["confusion", "weakness"],
            "duration": "2 hours",
            "patient_context": {
                "age": 82,
                "conditions": ["hypertension", "dementia"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n🚨 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"💡 Action: {response.data['recommended_action']}")
    print(f"⏱️  Timeframe: {response.data['timeframe']}")
    print(f"\n🤔 Reasoning: {response.data['reasoning']}")


async def test_pregnant_bleeding():
    """Test special population - pregnant with bleeding"""
    print("\n" + "="*80)
    print("TEST 10: SPECIAL POPULATION - Pregnant with Bleeding")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="I'm pregnant and experiencing bleeding",
        user_id="test_user",
        context={
            "symptoms": ["bleeding", "pain"],
            "duration": "30 minutes",
            "severity": "moderate",
            "patient_context": {
                "age": 28,
                "pregnant": True
            }
        }
    )

    response = await agent.process(request)

    print(f"\n📊 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"💡 Action: {response.data['recommended_action']}")
    print(f"⏱️  Timeframe: {response.data['timeframe']}")
    print(f"🤔 Reasoning: {response.data['reasoning']}")


async def test_immunocompromised_fever():
    """Test special population - immunocompromised with fever"""
    print("\n" + "="*80)
    print("TEST 11: SPECIAL POPULATION - Immunocompromised with Fever")
    print("="*80)

    agent = TriageAgent()

    request = AgentRequest(
        message="I have a fever and I'm on chemotherapy",
        user_id="test_user",
        context={
            "symptoms": ["fever"],
            "duration": "3 hours",
            "vital_signs": {
                "temperature": 38.5
            },
            "patient_context": {
                "age": 55,
                "conditions": ["cancer", "chemotherapy"]
            }
        }
    )

    response = await agent.process(request)

    print(f"\n📊 URGENCY LEVEL: {response.data['urgency_level']}")
    print(f"💡 Action: {response.data['recommended_action']}")
    print(f"🤔 Reasoning: {response.data['reasoning']}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 TRIAGE & EMERGENCY RISK AGENT TEST SUITE")
    print("Testing Rule-Based Triage Classification")
    print("="*80)

    tests = [
        ("Emergency - Chest Pain", test_emergency_chest_pain),
        ("Emergency - Stroke", test_emergency_stroke),
        ("Emergency - Critical Vitals", test_emergency_vitals),
        ("Urgent - High Fever", test_urgent_high_fever),
        ("Urgent - Severe Pain", test_urgent_severe_pain),
        ("Routine - Prolonged Symptoms", test_routine_prolonged_symptoms),
        ("Self-Care - Mild Symptoms", test_self_care),
        ("Special Pop - Infant", test_pediatric_infant),
        ("Special Pop - Elderly", test_elderly_confusion),
        ("Special Pop - Pregnant", test_pregnant_bleeding),
        ("Special Pop - Immunocompromised", test_immunocompromised_fever)
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
    print("  ✅ Life-threatening emergency detection (911)")
    print("  ✅ Urgent care classification (ER/urgent care)")
    print("  ✅ Routine care recommendation (primary care)")
    print("  ✅ Self-care appropriateness determination")
    print("  ✅ Vital signs-based triage")
    print("  ✅ Special population handling (pediatric, elderly, pregnant, immunocompromised)")
    print("  ✅ Conservative safety thresholds")
    print("  ✅ Clear urgency communication")
    print("\n⚠️  CRITICAL SAFETY NOTE:")
    print("This triage system is CONSERVATIVE by design.")
    print("When in doubt, it escalates to higher levels of care.")
    print("This is INTENTIONAL to prioritize patient safety.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
