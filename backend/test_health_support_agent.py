"""
Test suite for Health Support Agent

Tests cover:
- Daily check-ins
- Chronic condition tracking
- Medication and appointment reminders
- Symptom logging
- Health goal tracking
- Health summaries
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.health_support_agent import HealthSupportAgent
from orchestrator.base import AgentRequest


@pytest.fixture
def agent():
    """Create a fresh agent instance for each test"""
    return HealthSupportAgent()


@pytest.mark.asyncio
async def test_daily_check_in_positive(agent):
    """TEST 1: Daily check-in with positive mood and good sleep"""
    request = AgentRequest(
        message="Good morning check-in",
        user_id="patient_001",
        context={
            "task": "daily_check_in",
            "mood": 8,
            "energy_level": 7,
            "sleep_hours": 8,
            "pain_level": 2,
            "symptoms": []
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert response.agent_name == "health_support"
    assert "check_in" in response.data
    assert response.data["check_in"]["mood"] == 8
    assert response.data["check_in"]["energy_level"] == 7
    assert response.data["check_in"]["sleep_hours"] == 8
    assert len(response.data.get("alerts", [])) == 0  # No alerts for positive check-in
    assert "encouragement" in response.data
    print(f"✓ TEST 1 PASSED: {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_daily_check_in_with_alerts(agent):
    """TEST 2: Daily check-in with concerning symptoms triggers alerts"""
    request = AgentRequest(
        message="Not feeling well today",
        user_id="patient_002",
        context={
            "task": "daily_check_in",
            "mood": 4,
            "energy_level": 3,
            "sleep_hours": 3,
            "pain_level": 9,
            "symptoms": ["chest pain"]
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert response.agent_name == "health_support"
    assert "alerts" in response.data
    assert len(response.data["alerts"]) >= 2  # Should have alerts for pain and symptoms
    # Check for high pain alert
    assert any("pain" in alert.lower() for alert in response.data["alerts"])
    # Check for concerning symptom alert
    assert any("chest pain" in alert.lower() or "immediate" in alert.lower() for alert in response.data["alerts"])
    print(f"✓ TEST 2 PASSED: Alerts generated - {response.data['alerts']}")


@pytest.mark.asyncio
async def test_track_diabetes_condition(agent):
    """TEST 3: Track diabetes with normal values"""
    request = AgentRequest(
        message="Log my blood sugar",
        user_id="patient_001",
        context={
            "task": "track_condition",
            "condition": "diabetes",
            "metrics": {
                "blood_sugar": 120,
                "carb_intake": 150,
                "insulin_dose": 8
            },
            "notes": "Feeling good after breakfast"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert response.agent_name == "health_support"
    assert "tracking_record" in response.data
    assert response.data["tracking_record"]["condition"] == "diabetes"
    assert response.data["tracking_record"]["metrics"]["blood_sugar"] == 120
    assert len(response.data.get("alerts", [])) == 0  # No alerts for normal values
    assert "recommendation" in response.data
    print(f"✓ TEST 3 PASSED: {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_track_diabetes_high_blood_sugar(agent):
    """TEST 4: Track diabetes with high blood sugar triggers alert"""
    request = AgentRequest(
        message="Log my blood sugar",
        user_id="patient_003",
        context={
            "task": "track_condition",
            "condition": "diabetes",
            "metrics": {
                "blood_sugar": 250,  # High value
                "carb_intake": 200,
                "insulin_dose": 10
            }
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "alerts" in response.data
    assert len(response.data["alerts"]) > 0
    # Should alert about high blood sugar
    assert any("blood" in alert.lower() and "sugar" in alert.lower() for alert in response.data["alerts"])
    print(f"✓ TEST 4 PASSED: High blood sugar alert - {response.data['alerts']}")


@pytest.mark.asyncio
async def test_track_hypertension(agent):
    """TEST 5: Track hypertension with elevated BP triggers alert"""
    request = AgentRequest(
        message="Log my blood pressure",
        user_id="patient_002",
        context={
            "task": "track_condition",
            "condition": "hypertension",
            "metrics": {
                "blood_pressure_systolic": 150,  # High
                "blood_pressure_diastolic": 95,   # High
                "sodium_intake": 2500
            }
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "alerts" in response.data
    assert len(response.data["alerts"]) >= 1  # Should alert for high BP
    print(f"✓ TEST 5 PASSED: Hypertension tracking - {response.data['alerts']}")


@pytest.mark.asyncio
async def test_track_unknown_condition(agent):
    """TEST 6: Tracking unknown condition returns error"""
    request = AgentRequest(
        message="Log my condition",
        user_id="patient_001",
        context={
            "task": "track_condition",
            "condition": "unknown_disease",
            "metrics": {"value": 100}
        }
    )

    response = await agent.process(request)

    assert response.success == False
    assert "not recognized" in response.data.get("message", response.data.get("error", "")).lower()
    print(f"✓ TEST 6 PASSED: Unknown condition rejected - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_get_reminders_for_user(agent):
    """TEST 7: Get all reminders for a user"""
    request = AgentRequest(
        message="What are my reminders?",
        user_id="patient_001",
        context={
            "task": "get_reminders",
            "reminder_type": "all"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "today_reminders" in response.data
    assert "count_today" in response.data
    # patient_001 should have medication and appointment reminders
    assert response.data["count_today"] >= 2
    print(f"✓ TEST 7 PASSED: {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_get_medication_reminders_only(agent):
    """TEST 8: Get only medication reminders"""
    request = AgentRequest(
        message="What medications do I need to take?",
        user_id="patient_002",
        context={
            "task": "get_reminders",
            "reminder_type": "medication"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "today_reminders" in response.data
    # All today reminders should be medication type
    for reminder in response.data["today_reminders"]:
        assert reminder["type"] == "medication"
    print(f"✓ TEST 8 PASSED: Medication reminders only - {len(response.data['today_reminders'])} found")


@pytest.mark.asyncio
async def test_log_mild_symptoms(agent):
    """TEST 9: Log mild symptoms with no escalation"""
    request = AgentRequest(
        message="I have a headache",
        user_id="patient_001",
        context={
            "task": "log_symptoms",
            "symptoms": ["headache"],
            "severity": 4,
            "duration": "2 hours"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "symptom_log" in response.data
    assert response.data["symptom_log"]["symptoms"] == ["headache"]
    assert response.data["symptom_log"]["severity"] == 4
    assert response.data["escalate_to_triage"] == False
    print(f"✓ TEST 9 PASSED: Mild symptom logged without escalation")


@pytest.mark.asyncio
async def test_log_severe_symptoms_escalates(agent):
    """TEST 10: Log severe symptoms triggers escalation"""
    request = AgentRequest(
        message="I have severe chest pain",
        user_id="patient_002",
        context={
            "task": "log_symptoms",
            "symptoms": ["chest pain", "shortness of breath"],
            "severity": 9,
            "duration": "30 minutes"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "symptom_log" in response.data
    assert response.data["escalate_to_triage"] == True
    assert len(response.data["alerts"]) >= 2  # Alert for chest pain and high severity
    assert "immediate" in response.data["recommendation"].lower() or "medical attention" in response.data["recommendation"].lower()
    print(f"✓ TEST 10 PASSED: Severe symptoms escalated - {response.data['alerts']}")


@pytest.mark.asyncio
async def test_track_goal_progress(agent):
    """TEST 11: Track progress on existing goal"""
    request = AgentRequest(
        message="I walked 8000 steps today",
        user_id="patient_001",
        context={
            "task": "track_goal",
            "goal_id": "goal_001",  # Steps goal with target 10000
            "value": 8000
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "goal" in response.data
    assert "achievement_rate" in response.data
    assert response.data["achievement_rate"] == 80.0  # 8000/10000 = 80%
    assert response.data["status"] == "almost_there"
    print(f"✓ TEST 11 PASSED: Goal progress tracked - {response.data['achievement_rate']}% achieved")


@pytest.mark.asyncio
async def test_track_goal_exceeded(agent):
    """TEST 12: Track progress that exceeds goal"""
    request = AgentRequest(
        message="I walked 12000 steps today!",
        user_id="patient_001",
        context={
            "task": "track_goal",
            "goal_id": "goal_001",
            "value": 12000
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert response.data["achievement_rate"] == 120.0
    assert response.data["status"] == "goal_met"
    assert "congratulations" in response.data.get("message", response.data.get("error", "")).lower() or "met your" in response.data.get("message", response.data.get("error", "")).lower()
    print(f"✓ TEST 12 PASSED: Goal exceeded - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_track_goal_without_goal_id_lists_goals(agent):
    """TEST 13: Calling track_goal without goal_id returns list of goals"""
    request = AgentRequest(
        message="Show my health goals",
        user_id="patient_001",
        context={
            "task": "track_goal"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "goals" in response.data
    assert len(response.data["goals"]) > 0
    assert "specify goal_id" in response.data["message"].lower()
    print(f"✓ TEST 13 PASSED: Listed {len(response.data['goals'])} active goals")


@pytest.mark.asyncio
async def test_track_invalid_goal(agent):
    """TEST 14: Tracking non-existent goal returns error"""
    request = AgentRequest(
        message="Track my goal",
        user_id="patient_999",
        context={
            "task": "track_goal",
            "goal_id": "invalid_goal",
            "value": 100
        }
    )

    response = await agent.process(request)

    assert response.success == False
    assert "not found" in response.data.get("message", response.data.get("error", "")).lower()
    print(f"✓ TEST 14 PASSED: Invalid goal rejected - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_get_health_summary_today(agent):
    """TEST 15: Get health summary for today"""
    # First, create some check-in data
    check_in_request = AgentRequest(
        message="Morning check-in",
        user_id="patient_summary_test",
        context={
            "task": "daily_check_in",
            "mood": 7,
            "energy_level": 6,
            "sleep_hours": 7
        }
    )
    await agent.process(check_in_request)

    # Now get summary
    summary_request = AgentRequest(
        message="Show my health summary",
        user_id="patient_summary_test",
        context={
            "task": "get_summary",
            "period": "today"
        }
    )

    response = await agent.process(summary_request)

    assert response.success == True
    assert "check_ins" in response.data
    assert "averages" in response.data
    assert response.data["check_ins"] >= 1
    print(f"✓ TEST 15 PASSED: Health summary retrieved - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_get_health_summary_week(agent):
    """TEST 16: Get health summary for the week"""
    request = AgentRequest(
        message="Show my weekly health summary",
        user_id="patient_001",
        context={
            "task": "get_summary",
            "period": "week"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "date_range" in response.data
    assert "averages" in response.data
    assert response.data["period"] == "week"
    print(f"✓ TEST 16 PASSED: Weekly summary - {response.data['date_range']}")


@pytest.mark.asyncio
async def test_schedule_medication_reminder(agent):
    """TEST 17: Schedule a new medication reminder"""
    request = AgentRequest(
        message="Remind me to take my medication",
        user_id="patient_new",
        context={
            "task": "schedule_reminder",
            "reminder_type": "medication",
            "medication": "Aspirin",
            "dosage": "81mg",
            "frequency": "once_daily",
            "times": ["09:00"],
            "condition": "heart_disease"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "reminder" in response.data
    assert response.data["reminder"]["medication"] == "Aspirin"
    assert response.data["reminder"]["dosage"] == "81mg"
    assert response.data["reminder"]["times"] == ["09:00"]
    assert "reminder_id" in response.data
    print(f"✓ TEST 17 PASSED: Medication reminder created - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_schedule_appointment_reminder(agent):
    """TEST 18: Schedule a new appointment reminder"""
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    request = AgentRequest(
        message="Remind me about my appointment",
        user_id="patient_new",
        context={
            "task": "schedule_reminder",
            "reminder_type": "appointment",
            "description": "Cardiology follow-up",
            "date": future_date,
            "time": "14:30",
            "specialty": "cardiology"
        }
    )

    response = await agent.process(request)

    assert response.success == True
    assert "reminder" in response.data
    assert response.data["reminder"]["description"] == "Cardiology follow-up"
    assert response.data["reminder"]["date"] == future_date
    assert response.data["reminder"]["specialty"] == "cardiology"
    print(f"✓ TEST 18 PASSED: Appointment reminder created - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_schedule_reminder_missing_info(agent):
    """TEST 19: Scheduling reminder without required info fails"""
    request = AgentRequest(
        message="Remind me",
        user_id="patient_001",
        context={
            "task": "schedule_reminder",
            "reminder_type": "medication"
            # Missing medication, dosage, times
        }
    )

    response = await agent.process(request)

    assert response.success == False
    assert "provide" in response.data.get("message", response.data.get("error", "")).lower()
    print(f"✓ TEST 19 PASSED: Incomplete reminder rejected - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_schedule_reminder_invalid_type(agent):
    """TEST 20: Scheduling reminder with invalid type fails"""
    request = AgentRequest(
        message="Remind me",
        user_id="patient_001",
        context={
            "task": "schedule_reminder",
            "reminder_type": "invalid_type"
        }
    )

    response = await agent.process(request)

    assert response.success == False
    assert "medication" in response.data.get("message", response.data.get("error", "")).lower() or "appointment" in response.data.get("message", response.data.get("error", "")).lower()
    print(f"✓ TEST 20 PASSED: Invalid reminder type rejected - {response.data.get("message", response.data.get("error", ""))}")


@pytest.mark.asyncio
async def test_condition_tracking_with_trend_analysis(agent):
    """TEST 21: Multiple condition logs enable trend analysis"""
    user_id = "patient_trend_test"

    # Log multiple diabetes readings over time
    for i, blood_sugar in enumerate([140, 135, 130, 125, 120, 115, 110]):
        request = AgentRequest(
            message="Log blood sugar",
            user_id=user_id,
            context={
                "task": "track_condition",
                "condition": "diabetes",
                "metrics": {
                    "blood_sugar": blood_sugar,
                    "carb_intake": 150,
                    "insulin_dose": 8
                }
            }
        )
        await agent.process(request)

    # Get the last response which should have trend analysis
    final_request = AgentRequest(
        message="Log blood sugar",
        user_id=user_id,
        context={
            "task": "track_condition",
            "condition": "diabetes",
            "metrics": {
                "blood_sugar": 105,
                "carb_intake": 140,
                "insulin_dose": 8
            }
        }
    )

    response = await agent.process(final_request)

    assert response.success == True
    assert "trend_analysis" in response.data
    assert response.data["trend_analysis"]["status"] == "analyzed"
    assert response.data["trend_analysis"]["trend"] == "decreasing"  # Blood sugar is going down
    print(f"✓ TEST 21 PASSED: Trend analysis - {response.data['trend_analysis']['trend']} trend detected")


@pytest.mark.asyncio
async def test_unknown_task(agent):
    """TEST 22: Unknown task returns error"""
    request = AgentRequest(
        message="Do something",
        user_id="patient_001",
        context={
            "task": "unknown_task"
        }
    )

    response = await agent.process(request)

    assert response.success == False
    assert "unknown task" in response.data.get("message", response.data.get("error", "")).lower()
    print(f"✓ TEST 22 PASSED: Unknown task rejected - {response.data.get("message", response.data.get("error", ""))}")


if __name__ == "__main__":
    print("=" * 70)
    print("HEALTH SUPPORT AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\nRunning all tests...\n")

    # Run pytest programmatically
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))
