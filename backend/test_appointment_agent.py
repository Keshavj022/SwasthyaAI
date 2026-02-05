"""
Test script for Appointment & Hospital Operations Agent.

Demonstrates all scheduling features:
1. Appointment booking with conflict detection
2. Doctor availability checking
3. Appointment rescheduling
4. Appointment cancellation
5. Listing patient appointments
6. Follow-up scheduling
7. Clinic hours enforcement
8. Multi-specialty support
9. Error handling

Run: python test_appointment_agent.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.appointment_agent import AppointmentAgent
from orchestrator.base import AgentRequest


async def test_book_appointment_success():
    """Test successful appointment booking"""
    print("\n" + "="*80)
    print("TEST 1: Book Appointment - Success")
    print("="*80)

    agent = AppointmentAgent()

    # Book appointment 4 days from now (Wednesday) at 10:00 AM
    future_date = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="I'd like to schedule an appointment with a family doctor",
        user_id="patient_001",
        context={
            "task": "book_appointment",
            "specialty": "family_medicine",
            "appointment_type": "routine_checkup",
            "preferred_date": future_date,
            "preferred_time": "10:00",
            "reason": "Annual physical examination"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n📝 Confirmation: {response.data['confirmation_message']}")
    print(f"\n👨‍⚕️ Doctor: {response.data['appointment']['doctor_name']}")
    print(f"📅 Date: {response.data['appointment_details']['date']}")
    print(f"⏰ Time: {response.data['appointment_details']['time']}")
    print(f"⏱️  Duration: {response.data['appointment_details']['duration']}")
    print(f"🏥 Type: {response.data['appointment_details']['type']}")
    print(f"📋 Appointment ID: {response.data['appointment']['appointment_id']}")

    if response.data['preparation_required']:
        print(f"\n⚠️  Preparation required for this appointment type")

    print(f"\n💡 Reminder: {response.data['reminder']}")


async def test_book_appointment_conflict():
    """Test appointment booking with scheduling conflict"""
    print("\n" + "="*80)
    print("TEST 2: Book Appointment - Conflict Detection")
    print("="*80)

    agent = AppointmentAgent()

    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    # Book first appointment
    request1 = AgentRequest(
        message="Book appointment",
        user_id="patient_002",
        context={
            "task": "book_appointment",
            "doctor_id": "doctor_001",
            "appointment_type": "initial_consultation",
            "preferred_date": future_date,
            "preferred_time": "14:00",
            "reason": "New patient consultation"
        }
    )

    response1 = await agent.process(request1)
    print(f"\n✅ First appointment booked: {response1.success}")
    print(f"   Time: {response1.data['appointment']['time']} - {response1.data['appointment']['end_time']}")

    # Try to book overlapping appointment
    request2 = AgentRequest(
        message="Book appointment",
        user_id="patient_003",
        context={
            "task": "book_appointment",
            "doctor_id": "doctor_001",
            "appointment_type": "routine_checkup",
            "preferred_date": future_date,
            "preferred_time": "14:15",  # Overlaps with first appointment
            "reason": "Follow-up visit"
        }
    )

    response2 = await agent.process(request2)

    print(f"\n❌ Second appointment (conflict): {response2.success}")
    print(f"⚠️  Error: {response2.data['error']}")
    print(f"🔄 Conflict with: {response2.data['conflict_with']['time']}")
    print(f"\n💡 Suggestion: {response2.data['suggestion']}")
    print(f"📅 Next available: {response2.data['next_available_slot']['date']} at {response2.data['next_available_slot']['time']}")


async def test_book_outside_clinic_hours():
    """Test booking outside clinic operating hours"""
    print("\n" + "="*80)
    print("TEST 3: Book Appointment - Outside Clinic Hours")
    print("="*80)

    agent = AppointmentAgent()

    future_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="Book late evening appointment",
        user_id="patient_004",
        context={
            "task": "book_appointment",
            "specialty": "cardiology",
            "appointment_type": "follow_up",
            "preferred_date": future_date,
            "preferred_time": "20:00",  # After clinic closes
            "reason": "Follow-up consultation"
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"⚠️  Error: {response.data['error']}")
    print(f"🕐 Clinic hours: {response.data['clinic_hours']}")
    print(f"🕐 Requested time: {response.data['requested_time']}")


async def test_book_on_closed_day():
    """Test booking on day clinic is closed"""
    print("\n" + "="*80)
    print("TEST 4: Book Appointment - Clinic Closed (Sunday)")
    print("="*80)

    agent = AppointmentAgent()

    # Find next Sunday
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7
    next_sunday = (today + timedelta(days=days_until_sunday)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="Book Sunday appointment",
        user_id="patient_005",
        context={
            "task": "book_appointment",
            "specialty": "pediatrics",
            "appointment_type": "routine_checkup",
            "preferred_date": next_sunday,
            "preferred_time": "10:00",
            "reason": "Child checkup"
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data['error']}")
    print(f"\n💡 Suggestion: {response.data['suggestion']}")
    print(f"📅 Open days: {', '.join(response.data['open_days'])}")


async def test_check_availability():
    """Test checking doctor availability"""
    print("\n" + "="*80)
    print("TEST 5: Check Doctor Availability")
    print("="*80)

    agent = AppointmentAgent()

    # Check availability for specific date
    check_date = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="Check availability for cardiology",
        user_id="patient_006",
        context={
            "task": "check_availability",
            "specialty": "cardiology",
            "date": check_date
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Total doctors available: {response.data['total_doctors']}")

    for doc_id, availability in response.data['availability'].items():
        print(f"\n👨‍⚕️ {availability['doctor_name']}")
        print(f"   Specialty: {availability['specialty']}")
        print(f"   Date: {availability['date']}")
        print(f"   Available slots ({len(availability['available_slots'])}): {', '.join(availability['available_slots'][:5])}...")


async def test_check_availability_general():
    """Test checking doctor availability without specific date"""
    print("\n" + "="*80)
    print("TEST 6: Check Doctor Availability - General")
    print("="*80)

    agent = AppointmentAgent()

    request = AgentRequest(
        message="When is Dr. Johnson available?",
        user_id="patient_007",
        context={
            "task": "check_availability",
            "doctor_id": "doctor_001"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")

    for doc_id, availability in response.data['availability'].items():
        print(f"\n👨‍⚕️ {availability['doctor_name']}")
        print(f"   Specialty: {availability['specialty']}")
        print(f"   Available days: {', '.join(availability['available_days'])}")


async def test_reschedule_appointment():
    """Test rescheduling an appointment"""
    print("\n" + "="*80)
    print("TEST 7: Reschedule Appointment")
    print("="*80)

    agent = AppointmentAgent()

    # Book original appointment (use +11 days to avoid Sunday)
    original_date = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d")

    book_request = AgentRequest(
        message="Book appointment",
        user_id="patient_008",
        context={
            "task": "book_appointment",
            "specialty": "internal_medicine",
            "appointment_type": "follow_up",
            "preferred_date": original_date,
            "preferred_time": "11:00",
            "reason": "Follow-up visit"
        }
    )

    booking = await agent.process(book_request)
    appointment_id = booking.data['appointment']['appointment_id']

    print(f"\n✅ Original appointment booked:")
    print(f"   Appointment ID: {appointment_id}")
    print(f"   Date: {original_date}")
    print(f"   Time: 11:00")

    # Reschedule to different date (use +15 days - Tuesday)
    new_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")

    reschedule_request = AgentRequest(
        message="Reschedule my appointment",
        user_id="patient_008",
        context={
            "task": "reschedule",
            "appointment_id": appointment_id,
            "new_date": new_date,
            "new_time": "15:00"
        }
    )

    response = await agent.process(reschedule_request)

    print(f"\n✅ Rescheduled: {response.success}")
    print(f"📝 Message: {response.data['message']}")
    print(f"\n📅 Old appointment:")
    print(f"   Date: {response.data['old_appointment']['date']}")
    print(f"   Time: {response.data['old_appointment']['time']}")
    print(f"\n📅 New appointment:")
    print(f"   Date: {response.data['new_appointment']['date']}")
    print(f"   Time: {response.data['new_appointment']['time']}")


async def test_cancel_appointment():
    """Test cancelling an appointment"""
    print("\n" + "="*80)
    print("TEST 8: Cancel Appointment")
    print("="*80)

    agent = AppointmentAgent()

    # Book appointment first
    future_date = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")

    book_request = AgentRequest(
        message="Book appointment",
        user_id="patient_009",
        context={
            "task": "book_appointment",
            "doctor_id": "doctor_003",
            "appointment_type": "routine_checkup",
            "preferred_date": future_date,
            "preferred_time": "09:30",
            "reason": "Annual checkup"
        }
    )

    booking = await agent.process(book_request)
    appointment_id = booking.data['appointment']['appointment_id']

    print(f"\n✅ Appointment booked: {appointment_id}")

    # Cancel it
    cancel_request = AgentRequest(
        message="Cancel my appointment",
        user_id="patient_009",
        context={
            "task": "cancel",
            "appointment_id": appointment_id,
            "reason": "Schedule conflict"
        }
    )

    response = await agent.process(cancel_request)

    print(f"\n✅ Cancelled: {response.success}")
    print(f"📝 Message: {response.data['message']}")
    print(f"💳 Refund policy: {response.data['refund_policy']}")
    print(f"❌ Status: {response.data['cancelled_appointment']['status']}")
    print(f"📋 Cancellation reason: {response.data['cancelled_appointment']['cancellation_reason']}")


async def test_list_appointments():
    """Test listing patient's appointments"""
    print("\n" + "="*80)
    print("TEST 9: List Patient Appointments")
    print("="*80)

    agent = AppointmentAgent()

    # Book multiple appointments for same patient
    patient_id = "patient_010"

    # Upcoming appointment 1
    date1 = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    request1 = AgentRequest(
        message="Book appointment",
        user_id=patient_id,
        context={
            "task": "book_appointment",
            "specialty": "family_medicine",
            "appointment_type": "routine_checkup",
            "preferred_date": date1,
            "preferred_time": "10:00",
            "reason": "Regular checkup"
        }
    )
    await agent.process(request1)

    # Upcoming appointment 2
    date2 = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    request2 = AgentRequest(
        message="Book appointment",
        user_id=patient_id,
        context={
            "task": "book_appointment",
            "specialty": "cardiology",
            "appointment_type": "follow_up",
            "preferred_date": date2,
            "preferred_time": "14:30",
            "reason": "Cardiology follow-up"
        }
    )
    await agent.process(request2)

    # List all appointments
    list_request = AgentRequest(
        message="Show my appointments",
        user_id=patient_id,
        context={
            "task": "list_appointments",
            "status": "all"
        }
    )

    response = await agent.process(list_request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Total appointments: {response.data['total_appointments']}")
    print(f"📅 Upcoming: {response.data['upcoming_count']}")
    print(f"📜 Past: {response.data['past_count']}")

    print(f"\n📅 Upcoming Appointments:")
    for appt in response.data['upcoming_appointments']:
        print(f"\n   Appointment ID: {appt['appointment_id']}")
        print(f"   Doctor: {appt['doctor_name']}")
        print(f"   Date: {appt['date']} at {appt['time']}")
        print(f"   Type: {appt['appointment_type']}")
        print(f"   Reason: {appt['reason']}")


async def test_schedule_followup():
    """Test scheduling follow-up appointment"""
    print("\n" + "="*80)
    print("TEST 10: Schedule Follow-up Appointment")
    print("="*80)

    agent = AppointmentAgent()

    # Book original appointment (representing a completed visit)
    # Use a date 9 days out (Wednesday - doctor_001 available)
    original_date = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")

    original_request = AgentRequest(
        message="Book appointment",
        user_id="patient_011",
        context={
            "task": "book_appointment",
            "doctor_id": "doctor_001",  # Changed to doctor_001 (more available days)
            "appointment_type": "initial_consultation",
            "preferred_date": original_date,
            "preferred_time": "10:00",
            "reason": "Initial consultation"
        }
    )

    original = await agent.process(original_request)
    original_id = original.data['appointment']['appointment_id']

    print(f"\n✅ Original appointment booked:")
    print(f"   ID: {original_id}")
    print(f"   Date: {original_date}")

    # Schedule follow-up 2 weeks later
    followup_request = AgentRequest(
        message="Schedule follow-up",
        user_id="patient_011",
        context={
            "task": "schedule_followup",
            "original_appointment_id": original_id,
            "followup_weeks": 2,
            "preferred_time": "14:00"
        }
    )

    response = await agent.process(followup_request)

    print(f"\n✅ Follow-up scheduled: {response.success}")
    if response.success:
        print(f"📅 Follow-up date: {response.data['appointment']['date']}")
        print(f"⏰ Follow-up time: {response.data['appointment']['time']}")
        print(f"👨‍⚕️ Same doctor: {response.data['appointment']['doctor_name']}")
        print(f"📋 Type: {response.data['appointment']['appointment_type']}")


async def test_error_invalid_date():
    """Test error handling for invalid date format"""
    print("\n" + "="*80)
    print("TEST 11: Error Handling - Invalid Date Format")
    print("="*80)

    agent = AppointmentAgent()

    request = AgentRequest(
        message="Book appointment",
        user_id="patient_012",
        context={
            "task": "book_appointment",
            "specialty": "family_medicine",
            "appointment_type": "routine_checkup",
            "preferred_date": "tomorrow",  # Invalid format
            "preferred_time": "10:00",
            "reason": "Checkup"
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data['error']}")
    print(f"💡 Expected format: {response.data['expected_format']}")
    print(f"📝 Example: {response.data['example']}")


async def test_error_past_appointment():
    """Test error handling for past date"""
    print("\n" + "="*80)
    print("TEST 12: Error Handling - Past Date")
    print("="*80)

    agent = AppointmentAgent()

    past_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="Book appointment",
        user_id="patient_013",
        context={
            "task": "book_appointment",
            "specialty": "pediatrics",
            "appointment_type": "routine_checkup",
            "preferred_date": past_date,
            "preferred_time": "10:00",
            "reason": "Checkup"
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data['error']}")
    print(f"🤔 Reasoning: {response.reasoning}")


async def test_urgent_care_appointment():
    """Test booking urgent care (same-day) appointment"""
    print("\n" + "="*80)
    print("TEST 13: Urgent Care - Same-Day Appointment")
    print("="*80)

    agent = AppointmentAgent()

    # Book for today or tomorrow (whichever is a valid weekday)
    now = datetime.now()
    # Use tomorrow to ensure it's definitely in the future
    urgent_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="I need to see a doctor urgently",
        user_id="patient_014",
        context={
            "task": "book_appointment",
            "specialty": "family_medicine",
            "appointment_type": "urgent_care",
            "preferred_date": urgent_date,
            "preferred_time": "15:00",
            "reason": "Urgent: persistent fever and cough"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    if response.success:
        print(f"📊 Confidence: {response.confidence:.2f}")
        print(f"🚨 Type: {response.data['appointment']['appointment_type']}")
        print(f"⏱️  Duration: {response.data['appointment_details']['duration']}")
        print(f"📅 Urgent appointment: {response.data['appointment']['date']}")
        print(f"⏰ Time: {response.data['appointment']['time']}")
    else:
        print(f"❌ Could not book urgent appointment")
        print(f"⚠️  {response.data.get('error', 'Time slot unavailable')}")


async def test_telemedicine_appointment():
    """Test booking telemedicine (virtual) appointment"""
    print("\n" + "="*80)
    print("TEST 14: Telemedicine - Virtual Consultation")
    print("="*80)

    agent = AppointmentAgent()

    # Use +11 days to get to Friday (doctor_001 is available on Friday)
    future_date = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="Schedule virtual appointment",
        user_id="patient_015",
        context={
            "task": "book_appointment",
            "doctor_id": "doctor_001",
            "appointment_type": "telemedicine",
            "preferred_date": future_date,
            "preferred_time": "16:00",
            "reason": "Virtual consultation for prescription refill"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"💻 Type: {response.data['appointment']['appointment_type']}")
    print(f"⏱️  Duration: {response.data['appointment_details']['duration']} (shorter for virtual)")
    print(f"📅 Date: {response.data['appointment']['date']}")
    print(f"⏰ Time: {response.data['appointment']['time']}")
    print(f"🏥 Location: {response.data['appointment_details']['location']}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 APPOINTMENT & HOSPITAL OPERATIONS AGENT TEST SUITE")
    print("Testing Offline Scheduling with Conflict Detection")
    print("="*80)

    tests = [
        ("Book Appointment - Success", test_book_appointment_success),
        ("Book Appointment - Conflict", test_book_appointment_conflict),
        ("Book Outside Clinic Hours", test_book_outside_clinic_hours),
        ("Book on Closed Day", test_book_on_closed_day),
        ("Check Availability - Specific Date", test_check_availability),
        ("Check Availability - General", test_check_availability_general),
        ("Reschedule Appointment", test_reschedule_appointment),
        ("Cancel Appointment", test_cancel_appointment),
        ("List Appointments", test_list_appointments),
        ("Schedule Follow-up", test_schedule_followup),
        ("Error - Invalid Date", test_error_invalid_date),
        ("Error - Past Date", test_error_past_appointment),
        ("Urgent Care - Same Day", test_urgent_care_appointment),
        ("Telemedicine - Virtual", test_telemedicine_appointment)
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
    print("  ✅ Offline appointment scheduling (no internet required)")
    print("  ✅ Automatic conflict detection (prevents double-booking)")
    print("  ✅ Duration-based scheduling (different appointment types)")
    print("  ✅ Clinic hours enforcement (no bookings outside hours)")
    print("  ✅ Doctor availability checking by specialty")
    print("  ✅ Appointment rescheduling with conflict handling")
    print("  ✅ Appointment cancellation with refund policy")
    print("  ✅ Patient appointment history listing")
    print("  ✅ Automated follow-up scheduling")
    print("  ✅ Multi-specialty support (9 specialties)")
    print("  ✅ 6 appointment types (consultation, follow-up, urgent, telemedicine, etc.)")
    print("  ✅ Next available slot suggestions on conflicts")
    print("  ✅ Comprehensive error handling")
    print("\n⚠️  IMPORTANT NOTES:")
    print("This is an ADMINISTRATIVE agent, not a medical AI agent.")
    print("All appointments are subject to clinic confirmation.")
    print("Emergency cases should be directed to 911 or Triage Agent first.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
