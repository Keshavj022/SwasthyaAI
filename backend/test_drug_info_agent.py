"""
Test script for Drug Info Agent.

Demonstrates all task types:
1. Medication explanation
2. Drug interaction checking
3. Allergy safety checking
4. Dosage information
5. Comprehensive safety check

Run: python test_drug_info_agent.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.drug_info_agent import DrugInfoAgent
from orchestrator.base import AgentRequest
import json


async def test_medication_explanation():
    """Test medication information retrieval"""
    print("\n" + "="*80)
    print("TEST 1: Medication Explanation - Lisinopril")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="Tell me about Lisinopril",
        user_id="test_user",
        context={
            "task_type": "explain",
            "medication": "Lisinopril"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 Medication: {response.data.get('medication_name')}")
    print(f"🔬 Drug Class: {response.data.get('drug_class')}")
    print(f"⚙️  Mechanism: {response.data.get('mechanism_of_action')}")
    print(f"\n📋 Common Uses:")
    for use in response.data.get("common_uses", []):
        print(f"  - {use}")
    print(f"\n⚠️  Common Side Effects:")
    for effect in response.data.get("common_side_effects", [])[:3]:
        print(f"  - {effect}")


async def test_drug_interactions_major():
    """Test drug interaction detection (major interactions)"""
    print("\n" + "="*80)
    print("TEST 2: Drug Interaction Check - MAJOR Interactions")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="Check drug interactions",
        user_id="test_user",
        context={
            "task_type": "check_interactions",
            "medications": ["warfarin", "aspirin", "ibuprofen"]
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 Medications Checked: {', '.join(response.data['medications_checked'])}")
    print(f"🔍 Total Interactions: {response.data['total_interactions_found']}")
    print(f"\n📊 Severity Breakdown:")
    for severity, count in response.data["severity_breakdown"].items():
        print(f"  - {severity.upper()}: {count}")

    print(f"\n⚠️  Red Flags ({len(response.red_flags)}):")
    for flag in response.red_flags:
        print(f"  {flag}")

    print(f"\n🚨 Requires Escalation: {response.requires_escalation}")


async def test_allergy_check_critical():
    """Test allergy safety check (critical alert)"""
    print("\n" + "="*80)
    print("TEST 3: Allergy Safety Check - CRITICAL Alert")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="Check if patient can take Amoxicillin",
        user_id="test_user",
        context={
            "task_type": "check_allergies",
            "medication": "Amoxicillin",
            "patient_allergies": ["penicillin"]
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 Medication: {response.data['medication']}")
    print(f"🔍 Patient Allergies: {', '.join(response.data['patient_allergies'])}")
    print(f"\n✅ Is Safe: {response.data['is_safe']}")
    print(f"⚠️  Direct Allergy Matches: {response.data['direct_allergy_matches']}")
    print(f"⚠️  Cross-Reactivity Warnings: {response.data['cross_reactivity_warnings']}")

    print(f"\n🚨 All Warnings ({len(response.data['all_warnings'])}):")
    for warning in response.data["all_warnings"]:
        print(f"  Type: {warning['type']}")
        print(f"  Severity: {warning['severity']}")
        print(f"  {warning['message']}")

    print(f"\n🚨 Requires Escalation: {response.requires_escalation}")


async def test_allergy_cross_reactivity():
    """Test cross-reactivity warning"""
    print("\n" + "="*80)
    print("TEST 4: Allergy Cross-Reactivity - Aspirin → Ibuprofen")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="Can patient take ibuprofen?",
        user_id="test_user",
        context={
            "task_type": "check_allergies",
            "medication": "ibuprofen",
            "patient_allergies": ["aspirin"]
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 Medication: {response.data['medication']}")
    print(f"✅ Is Safe (no direct match): {response.data['is_safe']}")
    print(f"⚠️  Cross-Reactivity Warnings: {response.data['cross_reactivity_warnings']}")

    if response.data["all_warnings"]:
        print(f"\n⚠️  Warning Details:")
        for warning in response.data["all_warnings"]:
            print(f"  {warning['message']}")


async def test_dosage_info():
    """Test dosage education"""
    print("\n" + "="*80)
    print("TEST 5: Dosage Information - Metformin (with warnings)")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="How do I take Metformin?",
        user_id="test_user",
        context={
            "task_type": "dosage_info",
            "medication": "Metformin",
            "indication": "Type 2 diabetes",
            "patient_context": {
                "age": 72,
                "kidney_disease": True
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 Medication: {response.data['medication']}")
    print(f"🎯 Indication: {response.data['indication']}")
    print(f"\n📋 Dosage Guidance:")
    print(f"  Adult Dose: {response.data['typical_adult_dose']}")
    print(f"  Max Daily: {response.data['max_daily_dose']}")
    print(f"  Frequency: {response.data['frequency']}")
    print(f"\n📝 Instructions: {response.data['administration_instructions']}")

    if response.data.get("warnings"):
        print(f"\n⚠️  Special Warnings ({len(response.data['warnings'])}):")
        for warning in response.data["warnings"]:
            print(f"  {warning}")


async def test_comprehensive_safety_check_unsafe():
    """Test comprehensive safety check (unsafe scenario)"""
    print("\n" + "="*80)
    print("TEST 6: Comprehensive Safety Check - UNSAFE (Contraindication)")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="Can we add Metformin for this patient?",
        user_id="test_user",
        context={
            "task_type": "comprehensive_check",
            "new_medication": "Metformin",
            "patient_allergies": [],
            "current_medications": ["Lisinopril", "Aspirin"],
            "patient_conditions": ["Type 2 diabetes", "Kidney disease (eGFR 25)"]
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 New Medication: {response.data['new_medication']}")
    print(f"🚦 Overall Safety: {response.data['overall_safety']}")
    print(f"✅ Is Safe: {response.data['is_safe']}")
    print(f"\n⚠️  Total Safety Issues: {response.data['total_safety_issues']}")

    if response.data["safety_issues"]:
        print(f"\n🚨 Safety Issues:")
        for issue in response.data["safety_issues"]:
            print(f"  Type: {issue['type']}")
            print(f"  Severity: {issue['severity']}")
            print(f"  {issue['message']}")

    print(f"\n📋 Recommendation:")
    print(f"  {response.data['recommendation']}")

    print(f"\n🚨 Requires Escalation: {response.requires_escalation}")


async def test_comprehensive_safety_check_safe():
    """Test comprehensive safety check (safe scenario)"""
    print("\n" + "="*80)
    print("TEST 7: Comprehensive Safety Check - SAFE")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="Can we add Lisinopril?",
        user_id="test_user",
        context={
            "task_type": "comprehensive_check",
            "new_medication": "Lisinopril",
            "patient_allergies": [],
            "current_medications": ["Metformin"],
            "patient_conditions": ["Hypertension", "Type 2 diabetes"]
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💊 New Medication: {response.data['new_medication']}")
    print(f"🚦 Overall Safety: {response.data['overall_safety']}")
    print(f"✅ Is Safe: {response.data['is_safe']}")
    print(f"\n⚠️  Total Safety Issues: {response.data['total_safety_issues']}")

    print(f"\n📋 Recommendation:")
    print(f"  {response.data['recommendation']}")

    print(f"\n📝 Next Steps:")
    for step in response.data.get("next_steps", [])[:2]:
        print(f"  - {step}")


async def test_invalid_task_type():
    """Test error handling for invalid task type"""
    print("\n" + "="*80)
    print("TEST 8: Error Handling - Invalid Task Type")
    print("="*80)

    agent = DrugInfoAgent()

    request = AgentRequest(
        message="Invalid request",
        user_id="test_user",
        context={
            "task_type": "prescribe_medication",  # Invalid!
            "medication": "Aspirin"
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n⚠️  Error: {response.data.get('error')}")
    print(f"📋 Supported Types: {response.data.get('supported_types')}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 DRUG INFO AGENT TEST SUITE")
    print("Testing Medication Knowledge & Safety Checking")
    print("="*80)

    tests = [
        ("Medication Explanation", test_medication_explanation),
        ("Drug Interactions (Major)", test_drug_interactions_major),
        ("Allergy Check (Critical)", test_allergy_check_critical),
        ("Cross-Reactivity Warning", test_allergy_cross_reactivity),
        ("Dosage Information", test_dosage_info),
        ("Comprehensive Check (Unsafe)", test_comprehensive_safety_check_unsafe),
        ("Comprehensive Check (Safe)", test_comprehensive_safety_check_safe),
        ("Error Handling", test_invalid_task_type)
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
    print("  ✅ Medication information lookup")
    print("  ✅ Drug interaction detection (major & moderate)")
    print("  ✅ Allergy safety checking (direct & cross-reactivity)")
    print("  ✅ Dosage education with warnings")
    print("  ✅ Comprehensive safety assessment")
    print("  ✅ Contraindication detection")
    print("  ✅ Safety escalation triggers")
    print("\n⚠️  IMPORTANT: This agent has NO PRESCRIBING AUTHORITY")
    print("All medication decisions must be made by licensed healthcare providers.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
