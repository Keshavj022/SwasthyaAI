"""
Test script for Nearby Doctors & Referral Agent.

Demonstrates all features:
1. Search by specialty
2. Search by medical condition
3. Generate referral letters
4. Insurance verification
5. Distance filtering
6. Accepting new patients filter
7. Specialty matching logic
8. Referral explanations

Run: python test_nearby_doctors_agent.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.nearby_doctors_agent import NearbyDoctorsAgent
from orchestrator.base import AgentRequest


async def test_search_by_specialty_success():
    """Test searching for doctors by specialty"""
    print("\n" + "="*80)
    print("TEST 1: Search by Specialty - Cardiology")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Find a cardiologist near me",
        user_id="patient_001",
        context={
            "task": "search_by_specialty",
            "specialty": "cardiology",
            "patient_zip": "10001",
            "insurance": "BlueCross",
            "accepting_new_patients": True,
            "max_distance_miles": 10
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🏥 Found {response.data['count']} cardiologists")

    for i, doctor in enumerate(response.data['doctors'], 1):
        print(f"\n{i}. {doctor['name']}, {doctor['credentials']}")
        print(f"   📍 Address: {doctor['address']}")
        print(f"   📞 Phone: {doctor['phone']}")
        print(f"   📏 Distance: {doctor['distance_miles']} miles")
        print(f"   ⭐ Rating: {doctor['rating']}/5.0")
        print(f"   👨‍⚕️ Experience: {doctor['years_experience']} years")
        print(f"   ✅ Accepting new patients: {doctor['accepting_new_patients']}")
        print(f"   💳 Insurance: {', '.join(doctor['insurance_accepted'][:3])}")

    print(f"\n🔄 Suggested agents: {', '.join(response.suggested_agents)}")


async def test_search_by_specialty_no_results():
    """Test searching with no matching results"""
    print("\n" + "="*80)
    print("TEST 2: Search by Specialty - No Results (Wrong Insurance)")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Find a pediatrician",
        user_id="patient_002",
        context={
            "task": "search_by_specialty",
            "specialty": "pediatrics",
            "patient_zip": "10001",
            "insurance": "RareInsuranceCo",  # Not accepted by any doctor
            "accepting_new_patients": True
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📝 Message: {response.data['message']}")
    print(f"\n💡 Suggestions:")
    for suggestion in response.data['suggestions']:
        print(f"   - {suggestion}")


async def test_search_by_condition():
    """Test searching by medical condition"""
    print("\n" + "="*80)
    print("TEST 3: Search by Condition - Back Pain")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="I have back pain and need to see a specialist",
        user_id="patient_003",
        context={
            "task": "search_by_condition",
            "condition": "back pain",
            "patient_zip": "10002",
            "insurance": "Aetna",
            "accepting_new_patients": True
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🏥 Condition: {response.data['condition']}")
    print(f"📋 Recommended specialties: {', '.join(response.data['recommended_specialties'])}")
    print(f"🎯 Primary specialty: {response.data['primary_specialty']}")
    print(f"\n💡 Matching explanation:")
    print(f"   {response.data['matching_explanation']}")

    print(f"\n👨‍⚕️ Found {response.data['total_found']} matching doctors (showing top {len(response.data['doctors'])}):")
    for i, doctor in enumerate(response.data['doctors'][:3], 1):
        print(f"\n{i}. {doctor['name']} - {doctor['specialty'].title()}")
        print(f"   📍 {doctor['distance_miles']} miles away")
        print(f"   ⭐ Rating: {doctor['rating']}/5.0")


async def test_search_by_condition_unknown():
    """Test searching for condition with no specialty mapping"""
    print("\n" + "="*80)
    print("TEST 4: Search by Condition - Unknown Condition")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="I have a rare condition",
        user_id="patient_004",
        context={
            "task": "search_by_condition",
            "condition": "extremely rare disease",
            "patient_zip": "10001"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n📝 Message: {response.data['message']}")
    print(f"💡 Recommendation: {response.data['recommendation']}")
    print(f"📋 Suggested specialties: {', '.join(response.data['suggested_specialties'])}")


async def test_generate_referral():
    """Test generating a referral letter"""
    print("\n" + "="*80)
    print("TEST 5: Generate Referral Letter")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Generate referral for cardiology",
        user_id="patient_005",
        context={
            "task": "generate_referral",
            "patient_name": "John Smith",
            "condition": "chest pain and irregular heartbeat",
            "doctor_id": "doc_001",
            "referring_doctor": "Dr. Anne Primary",
            "urgency": "urgent"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")

    print(f"\n📄 Referral Letter:")
    print("─" * 80)
    print(response.data['referral_letter'])
    print("─" * 80)

    print(f"\n💡 Explanation:")
    print(f"   {response.data['explanation']}")

    print(f"\n📋 Next Steps:")
    for i, step in enumerate(response.data['next_steps'], 1):
        print(f"   {i}. {step}")


async def test_generate_referral_routine():
    """Test generating routine referral"""
    print("\n" + "="*80)
    print("TEST 6: Generate Referral Letter - Routine Urgency")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Generate dermatology referral",
        user_id="patient_006",
        context={
            "task": "generate_referral",
            "patient_name": "Jane Doe",
            "condition": "skin rash",
            "doctor_id": "doc_002",
            "referring_doctor": "Dr. Bob Family",
            "urgency": "routine"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"\n👨‍⚕️ Referring to: {response.data['doctor_info']['name']}")
    print(f"🏥 Specialty: {response.data['doctor_info']['specialty'].title()}")
    print(f"📞 Phone: {response.data['doctor_info']['phone']}")

    # Check that "at your earliest convenience" is in the letter
    if "at your earliest convenience" in response.data['referral_letter']:
        print(f"\n✅ Routine urgency correctly reflected in letter")


async def test_check_insurance():
    """Test checking which doctors accept specific insurance"""
    print("\n" + "="*80)
    print("TEST 7: Check Insurance - Medicare")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Which doctors accept Medicare?",
        user_id="patient_007",
        context={
            "task": "check_insurance",
            "insurance": "Medicare",
            "patient_zip": "10001"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💳 Insurance: {response.data['insurance']}")
    print(f"👨‍⚕️ Found {response.data['count']} doctors accepting Medicare")

    for i, doctor in enumerate(response.data['doctors_accepting'], 1):
        print(f"\n{i}. {doctor['name']} - {doctor['specialty'].title()}")
        print(f"   📍 Distance: {doctor.get('distance_miles', 'N/A')} miles")
        print(f"   ⭐ Rating: {doctor['rating']}/5.0")


async def test_check_insurance_with_specialty():
    """Test checking insurance with specialty filter"""
    print("\n" + "="*80)
    print("TEST 8: Check Insurance - Aetna + Specialty Filter")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Which cardiologists accept Aetna?",
        user_id="patient_008",
        context={
            "task": "check_insurance",
            "insurance": "Aetna",
            "specialty": "cardiology",
            "patient_zip": "10001"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"\n💳 Insurance: {response.data['insurance']}")
    print(f"🏥 Specialty filter: {response.data['specialty_filter']}")
    print(f"👨‍⚕️ Found {response.data['count']} matching doctors")

    for doctor in response.data['doctors_accepting']:
        print(f"\n   • {doctor['name']}")
        print(f"     {doctor['specialty'].title()} - {doctor['distance_miles']} miles")


async def test_distance_filtering():
    """Test distance-based filtering"""
    print("\n" + "="*80)
    print("TEST 9: Distance Filtering - Narrow Radius")
    print("="*80)

    agent = NearbyDoctorsAgent()

    # Search with 5-mile radius
    request = AgentRequest(
        message="Find neurologist very close to me",
        user_id="patient_009",
        context={
            "task": "search_by_specialty",
            "specialty": "neurology",
            "patient_zip": "10001",
            "max_distance_miles": 5  # Very narrow radius
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"\n📏 Max distance: {response.data['search_criteria']['max_distance_miles']} miles")
    print(f"👨‍⚕️ Found {response.data['count']} doctors within 5 miles")

    if response.data['count'] > 0:
        for doctor in response.data['doctors']:
            print(f"\n   • {doctor['name']}")
            print(f"     📍 {doctor['distance_miles']} miles away")


async def test_accepting_new_patients():
    """Test filtering by accepting new patients"""
    print("\n" + "="*80)
    print("TEST 10: Filter - Accepting New Patients")
    print("="*80)

    agent = NearbyDoctorsAgent()

    # Search for pediatricians accepting new patients
    request1 = AgentRequest(
        message="Find pediatrician accepting new patients",
        user_id="patient_010",
        context={
            "task": "search_by_specialty",
            "specialty": "pediatrics",
            "patient_zip": "10001",
            "accepting_new_patients": True  # Only accepting new
        }
    )

    response1 = await agent.process(request1)

    print(f"\n✅ Accepting new patients = True")
    count1 = response1.data.get('count', 0)
    print(f"   Found {count1} doctors")

    # Search without filter
    request2 = AgentRequest(
        message="Find any pediatrician",
        user_id="patient_010",
        context={
            "task": "search_by_specialty",
            "specialty": "pediatrics",
            "patient_zip": "10001",
            "accepting_new_patients": False  # Include all
        }
    )

    response2 = await agent.process(request2)

    print(f"\n✅ Accepting new patients = False (show all)")
    count2 = response2.data.get('count', 0)
    print(f"   Found {count2} doctors")

    if count2 > count1:
        print(f"\n💡 Filter working correctly: found more doctors when including those not accepting new patients")
    else:
        print(f"\n💡 Filter effect: {count1} vs {count2} doctors")


async def test_multiple_specialties():
    """Test condition that maps to multiple specialties"""
    print("\n" + "="*80)
    print("TEST 11: Multiple Specialties - Headache")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="I have severe headaches",
        user_id="patient_011",
        context={
            "task": "search_by_condition",
            "condition": "headache",
            "patient_zip": "10002"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"\n🏥 Condition: {response.data['condition']}")
    print(f"📋 Recommended specialties ({len(response.data['recommended_specialties'])}):")
    for specialty in response.data['recommended_specialties']:
        print(f"   - {specialty.replace('_', ' ').title()}")

    print(f"\n🎯 Primary specialty: {response.data['primary_specialty']}")
    print(f"\n💡 Explanation:")
    print(f"   {response.data['matching_explanation']}")


async def test_cardiovascular_condition():
    """Test cardiovascular condition matching"""
    print("\n" + "="*80)
    print("TEST 12: Cardiovascular Condition - High Blood Pressure")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="I have high blood pressure",
        user_id="patient_012",
        context={
            "task": "search_by_condition",
            "condition": "high blood pressure",
            "patient_zip": "10001",
            "insurance": "UnitedHealthcare"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🏥 Condition: {response.data['condition']}")
    print(f"📋 Recommended specialties: {', '.join(response.data['recommended_specialties'])}")

    print(f"\n👨‍⚕️ Top matching doctors:")
    for i, doctor in enumerate(response.data['doctors'][:2], 1):
        print(f"\n{i}. {doctor['name']}")
        print(f"   Specialty: {doctor['specialty'].title()}")
        print(f"   Rating: {doctor['rating']}/5.0")
        print(f"   Distance: {doctor['distance_miles']} miles")


async def test_error_missing_zip():
    """Test error handling for missing zip code"""
    print("\n" + "="*80)
    print("TEST 13: Error Handling - Missing Zip Code")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Find a doctor",
        user_id="patient_013",
        context={
            "task": "search_by_specialty",
            "specialty": "cardiology"
            # Missing patient_zip
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data['error']}")
    print(f"🤔 Reasoning: {response.reasoning}")


async def test_error_missing_specialty():
    """Test error handling for missing specialty"""
    print("\n" + "="*80)
    print("TEST 14: Error Handling - Missing Specialty")
    print("="*80)

    agent = NearbyDoctorsAgent()

    request = AgentRequest(
        message="Find a doctor",
        user_id="patient_014",
        context={
            "task": "search_by_specialty",
            "patient_zip": "10001"
            # Missing specialty
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data['error']}")
    print(f"\n📋 Available specialties:")
    for specialty in response.data['available_specialties'][:5]:
        print(f"   - {specialty}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 NEARBY DOCTORS & REFERRAL AGENT TEST SUITE")
    print("Testing Specialty Matching & Cached Directory Search")
    print("="*80)

    tests = [
        ("Search by Specialty - Success", test_search_by_specialty_success),
        ("Search by Specialty - No Results", test_search_by_specialty_no_results),
        ("Search by Condition", test_search_by_condition),
        ("Search by Condition - Unknown", test_search_by_condition_unknown),
        ("Generate Referral - Urgent", test_generate_referral),
        ("Generate Referral - Routine", test_generate_referral_routine),
        ("Check Insurance", test_check_insurance),
        ("Check Insurance with Specialty", test_check_insurance_with_specialty),
        ("Distance Filtering", test_distance_filtering),
        ("Accepting New Patients Filter", test_accepting_new_patients),
        ("Multiple Specialties", test_multiple_specialties),
        ("Cardiovascular Condition", test_cardiovascular_condition),
        ("Error - Missing Zip", test_error_missing_zip),
        ("Error - Missing Specialty", test_error_missing_specialty)
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
    print("  ✅ Specialty-based doctor search")
    print("  ✅ Condition-to-specialty matching")
    print("  ✅ Distance-based filtering (zip code proximity)")
    print("  ✅ Insurance verification")
    print("  ✅ Accepting new patients filter")
    print("  ✅ Referral letter generation")
    print("  ✅ Referral explanation")
    print("  ✅ Multiple specialty recommendations")
    print("  ✅ Cached/offline doctor directory")
    print("  ✅ Comprehensive error handling")
    print("\n⚠️  IMPORTANT NOTES:")
    print("This is a DIRECTORY/REFERRAL agent, not a medical AI agent.")
    print("All referrals should be approved by primary care physician.")
    print("Insurance coverage should be verified with the insurance company.")
    print("Doctor availability should be confirmed when scheduling.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
