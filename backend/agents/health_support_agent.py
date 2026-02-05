"""
AI Health Support / Daily Update Agent

This agent provides:
- Daily wellness check-ins
- Chronic condition tracking and monitoring
- Medication and appointment reminders
- Symptom tracking over time
- Health goal tracking (exercise, diet, sleep)
- Non-intrusive messaging and support
- Integration with Health Memory Agent for personalized care

This is an administrative support tool, NOT medical AI.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from orchestrator.base import BaseAgent, AgentRequest, AgentResponse


class HealthSupportAgent(BaseAgent):
    """
    Agent for daily health check-ins, condition tracking, and reminders.
    Provides non-intrusive support for chronic condition management.
    """

    def __init__(self):
        super().__init__()
        self.name = "health_support"
        
        # Database dependency
        from database import SessionLocal
        self.db = SessionLocal()

        # Chronic conditions with monitoring parameters
        self.condition_parameters = {
            "diabetes": {
                "metrics": ["blood_sugar", "carb_intake", "insulin_dose"],
                "frequency": "daily",
                "thresholds": {"blood_sugar_low": 70, "blood_sugar_high": 180}
            },
            "hypertension": {
                "metrics": ["blood_pressure_systolic", "blood_pressure_diastolic", "sodium_intake"],
                "frequency": "daily",
                "thresholds": {"blood_pressure_systolic_high": 140, "blood_pressure_diastolic_high": 90}
            },
            "asthma": {
                "metrics": ["peak_flow", "inhaler_use", "symptoms"],
                "frequency": "daily",
                "thresholds": {"peak_flow_low": 300}
            },
            "heart_disease": {
                "metrics": ["heart_rate", "chest_pain", "shortness_of_breath", "exercise_tolerance"],
                "frequency": "daily",
                "thresholds": {"heart_rate_high": 100, "heart_rate_low": 50}
            },
            "copd": {
                "metrics": ["oxygen_saturation", "shortness_of_breath", "cough", "sputum"],
                "frequency": "daily",
                "thresholds": {"oxygen_sat_low": 90}
            },
            "arthritis": {
                "metrics": ["pain_level", "stiffness", "mobility", "medication_taken"],
                "frequency": "daily",
                "thresholds": {"pain_level_high": 7}
            }
        }

        # Health goals categories
        self.goal_categories = {
            "exercise": ["steps", "minutes", "workouts"],
            "diet": ["calories", "water_intake", "vegetables", "fruits"],
            "sleep": ["hours", "quality"],
            "medication_adherence": ["doses_taken", "doses_missed"],
            "mental_health": ["mood", "stress_level", "meditation"]
        }
    
    def __del__(self):
        """Cleanup database session"""
        if hasattr(self, 'db'):
            self.db.close()

    def _initialize_sample_data(self):
        """Initialize sample reminders and goals"""
        # Sample medication reminders
        self.reminders = [
            {
                "id": "rem_001",
                "user_id": "patient_001",
                "type": "medication",
                "medication": "Metformin",
                "dosage": "500mg",
                "frequency": "twice_daily",
                "times": ["08:00", "20:00"],
                "condition": "diabetes",
                "active": True
            },
            {
                "id": "rem_002",
                "user_id": "patient_002",
                "type": "medication",
                "medication": "Lisinopril",
                "dosage": "10mg",
                "frequency": "once_daily",
                "times": ["09:00"],
                "condition": "hypertension",
                "active": True
            },
            {
                "id": "rem_003",
                "user_id": "patient_001",
                "type": "appointment",
                "description": "Follow-up with Dr. Smith",
                "date": "2024-02-15",
                "time": "14:00",
                "specialty": "endocrinology",
                "active": True
            }
        ]

        # Sample health goals
        self.health_goals = [
            {
                "id": "goal_001",
                "user_id": "patient_001",
                "category": "exercise",
                "goal_type": "steps",
                "target": 10000,
                "frequency": "daily",
                "progress": [],
                "start_date": "2024-02-01",
                "active": True
            },
            {
                "id": "goal_002",
                "user_id": "patient_002",
                "category": "diet",
                "goal_type": "sodium_intake",
                "target": 2000,  # mg per day
                "frequency": "daily",
                "progress": [],
                "start_date": "2024-02-01",
                "active": True
            }
        ]

        # Sample condition tracking
        self.condition_tracking = [
            {
                "id": "track_001",
                "user_id": "patient_001",
                "condition": "diabetes",
                "date": "2024-02-10",
                "metrics": {
                    "blood_sugar": 125,
                    "carb_intake": 180,
                    "insulin_dose": 10
                },
                "notes": "Felt good today"
            }
        ]

    def get_capabilities(self) -> List[str]:
        """Define what this agent can handle"""
        return [
            "daily check-in", "check in", "wellness check",
            "track condition", "log symptoms", "how am i doing",
            "medication reminder", "appointment reminder", "reminders",
            "health goals", "track progress", "exercise goal",
            "blood sugar", "blood pressure", "symptoms",
            "diabetes tracking", "hypertension tracking",
            "chronic condition", "condition monitoring",
            "daily update", "health update", "feeling today"
        ]

    def get_description(self) -> str:
        """Describe the agent's purpose"""
        return (
            "AI Health Support Agent: Daily wellness check-ins, chronic condition "
            "tracking, medication/appointment reminders, symptom logging, and health "
            "goal tracking. Provides non-intrusive support for ongoing health management."
        )

    def get_confidence_threshold(self) -> float:
        """Set confidence threshold for routing"""
        return 0.65

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Main processing method. Routes to specific handlers based on task.

        Supported tasks:
        - daily_check_in: Morning wellness check
        - track_condition: Log chronic condition metrics
        - get_reminders: Fetch due reminders
        - log_symptoms: Record symptoms
        - track_goal: Update health goal progress
        - get_summary: Get health summary
        - schedule_reminder: Create new reminder
        """
        task = request.context.get("task", "daily_check_in")

        if task == "daily_check_in":
            return await self._daily_check_in(request)
        elif task == "track_condition":
            return await self._track_condition(request)
        elif task == "get_reminders":
            return await self._get_reminders(request)
        elif task == "log_symptoms":
            return await self._log_symptoms(request)
        elif task == "track_goal":
            return await self._track_goal(request)
        elif task == "get_summary":
            return await self._get_health_summary(request)
        elif task == "schedule_reminder":
            return await self._schedule_reminder(request)
        else:
            return AgentResponse(
                agent_name="health_support",
                success=False,
                data={"error": f"Unknown task: {task}"},
                confidence=0.3,
                reasoning="Task not recognized"
            )

    async def _daily_check_in(self, request: AgentRequest) -> AgentResponse:
        """
        Perform daily wellness check-in.

        Expected context:
        - mood: User's mood (1-10 scale)
        - energy_level: Energy level (1-10 scale)
        - sleep_hours: Hours of sleep
        - pain_level: Pain level if applicable (1-10 scale)
        - symptoms: List of any symptoms
        """
        user_id = request.user_id

        # Get context
        mood = request.context.get("mood")
        energy_level = request.context.get("energy_level")
        sleep_hours = request.context.get("sleep_hours")
        pain_level = request.context.get("pain_level", 0)
        symptoms = request.context.get("symptoms", [])

        from models.health_monitoring import CheckIn
        
        # Create check-in record
        check_in = CheckIn(
            user_id=user_id,
            date=datetime.now().date(),
            time=datetime.now().strftime("%H:%M"),
            mood=mood,
            energy_level=energy_level,
            sleep_hours=sleep_hours,
            pain_level=pain_level,
            symptoms=symptoms
        )
        
        self.db.add(check_in)
        self.db.commit()
        self.db.refresh(check_in)
        
        # Convert to dict for response
        check_in_data = {
            "id": check_in.id,
            "user_id": check_in.user_id,
            "date": check_in.date.isoformat(),
            "time": check_in.time,
            "mood": check_in.mood,
            "energy_level": check_in.energy_level,
            "sleep_hours": check_in.sleep_hours,
            "pain_level": check_in.pain_level,
            "symptoms": check_in.symptoms,
            "timestamp": check_in.timestamp.isoformat()
        }

        # Generate personalized response
        response_message = self._generate_check_in_response(check_in_data)

        # Check if we need to alert (concerning symptoms)
        alerts = []
        if pain_level and pain_level >= 8:
            alerts.append("High pain level detected. Consider consulting with your healthcare provider.")
        if sleep_hours and sleep_hours < 4:
            alerts.append("Insufficient sleep detected. Poor sleep can affect your health.")
        if symptoms and any(s in ["chest pain", "severe headache", "difficulty breathing"] for s in symptoms):
            alerts.append("ALERT: Concerning symptom detected. Please seek immediate medical attention.")

        # Get today's reminders
        today_reminders = self._get_due_reminders_for_user(user_id)

        return AgentResponse(
            agent_name="health_support",
            success=True,
            data={
                "check_in": check_in_data,
                "alerts": alerts,
                "reminders_today": today_reminders,
                "encouragement": self._get_encouragement(check_in_data),
                "message": response_message
            },
            confidence=0.95,
            reasoning="Daily check-in completed successfully"
        )

    def _generate_check_in_response(self, check_in: Dict[str, Any]) -> str:
        """Generate personalized response based on check-in data"""
        mood = check_in.get("mood")
        energy = check_in.get("energy_level")
        sleep = check_in.get("sleep_hours")

        messages = ["Good morning! Thanks for checking in."]

        if mood and mood >= 7:
            messages.append("It's great to see you're feeling positive today!")
        elif mood and mood <= 4:
            messages.append("I notice you're not feeling your best. Remember, it's okay to have off days.")

        if energy and energy >= 7:
            messages.append("Your energy levels look good!")
        elif energy and energy <= 4:
            messages.append("Your energy seems low. Make sure to take breaks and stay hydrated.")

        if sleep and sleep >= 7:
            messages.append("Good sleep quality!")
        elif sleep and sleep < 6:
            messages.append("You might benefit from more rest tonight.")

        return " ".join(messages)

    def _get_encouragement(self, check_in: Dict[str, Any]) -> str:
        """Generate encouraging message"""
        encouragements = [
            "You're doing great by staying on top of your health!",
            "Keep up the good work with your daily check-ins!",
            "Every day is a step toward better health!",
            "Your commitment to tracking your health is admirable!",
            "Remember, small steps lead to big improvements!"
        ]

        from models.health_monitoring import CheckIn
        
        # Simple rotation based on check-in count
        count = self.db.query(CheckIn).filter(CheckIn.user_id == check_in.get("user_id")).count()
        index = count % len(encouragements)
        return encouragements[index]

    async def _track_condition(self, request: AgentRequest) -> AgentResponse:
        """
        Track chronic condition metrics.

        Expected context:
        - condition: Name of condition (diabetes, hypertension, etc.)
        - metrics: Dict of metric values
        - notes: Optional notes
        """
        user_id = request.user_id
        condition = request.context.get("condition", "").lower()
        metrics = request.context.get("metrics", {})
        notes = request.context.get("notes", "")

        if not condition:
            return AgentResponse(
                agent_name="health_support",
                success=False,
                data={"error": "Please specify which condition you'd like to track."},
                confidence=0.5,
                reasoning="No condition specified"
            )

        if condition not in self.condition_parameters:
            return AgentResponse(
                agent_name="health_support",
                success=False,
                data={
                    "error": f"Condition '{condition}' not recognized.",
                    "supported_conditions": list(self.condition_parameters.keys())
                },
                confidence=0.5,
                reasoning="Unknown condition type"
            )

        # Get expected metrics for this condition
        expected_metrics = self.condition_parameters[condition]["metrics"]
        thresholds = self.condition_parameters[condition].get("thresholds", {})

        from models.health_monitoring import ConditionLog
        
        # Create tracking record
        tracking_record = ConditionLog(
            user_id=user_id,
            condition=condition,
            date=datetime.now().date(),
            time=datetime.now().strftime("%H:%M"),
            metrics=metrics,
            notes=notes
        )
        
        self.db.add(tracking_record)
        self.db.commit()
        self.db.refresh(tracking_record)
        
        # Convert to dict
        tracking_data = {
            "id": tracking_record.id,
            "user_id": tracking_record.user_id,
            "condition": tracking_record.condition,
            "date": tracking_record.date.isoformat(),
            "time": tracking_record.time,
            "metrics": tracking_record.metrics,
            "notes": tracking_record.notes,
            "timestamp": tracking_record.timestamp.isoformat()
        }

        # Check against thresholds
        alerts = []
        for threshold_key, threshold_value in thresholds.items():
            # Extract metric name and direction from threshold key
            # e.g., "blood_sugar_high" -> metric="blood_sugar", direction="high"
            parts = threshold_key.rsplit("_", 1)
            if len(parts) == 2:
                metric_name, direction = parts
                actual_value = metrics.get(metric_name)

                if actual_value is not None:
                    if direction == "high" and actual_value > threshold_value:
                        alerts.append(f"{metric_name.replace('_', ' ').title()} is above recommended level ({actual_value} > {threshold_value})")
                    elif direction == "low" and actual_value < threshold_value:
                        alerts.append(f"{metric_name.replace('_', ' ').title()} is below recommended level ({actual_value} < {threshold_value})")

        # Get recent trend (last 7 days)
        from models.health_monitoring import ConditionLog
        from datetime import timedelta
        
        cutoff_date = datetime.now().date() - timedelta(days=7)
        recent_logs_query = self.db.query(ConditionLog).filter(
            ConditionLog.user_id == user_id,
            ConditionLog.condition == condition,
            ConditionLog.date >= cutoff_date
        ).all()
        
        recent_logs = [
            {
                "metrics": log.metrics,
                "date": log.date.isoformat()
            } for log in recent_logs_query
        ]

        trend_analysis = self._analyze_trend(recent_logs, condition)

        return AgentResponse(
            agent_name="health_support",
            success=True,
            data={
                "tracking_record": tracking_record,
                "alerts": alerts,
                "trend_analysis": trend_analysis,
                "expected_metrics": expected_metrics,
                "recommendation": self._get_condition_recommendation(condition, metrics, alerts),
                "message": f"Successfully logged {condition} metrics."
            },
            confidence=0.92,
            reasoning="Condition tracking completed"
        )

    def _analyze_trend(self, logs: List[Dict[str, Any]], condition: str) -> Dict[str, Any]:
        """Analyze trend in condition metrics over time"""
        if len(logs) < 2:
            return {"status": "insufficient_data", "message": "Need more data points for trend analysis"}

        # Get primary metric for this condition
        primary_metric = self.condition_parameters[condition]["metrics"][0]

        values = []
        dates = []
        for log in logs:
            if primary_metric in log["metrics"]:
                values.append(log["metrics"][primary_metric])
                dates.append(log["date"])

        if len(values) < 2:
            return {"status": "insufficient_data", "message": "Need more data points for trend analysis"}

        # Simple trend calculation
        avg_first_half = sum(values[:len(values)//2]) / len(values[:len(values)//2])
        avg_second_half = sum(values[len(values)//2:]) / len(values[len(values)//2:])

        if avg_second_half > avg_first_half * 1.1:
            trend = "increasing"
        elif avg_second_half < avg_first_half * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "status": "analyzed",
            "metric": primary_metric,
            "trend": trend,
            "average_recent": round(avg_second_half, 1),
            "data_points": len(values),
            "date_range": f"{dates[0]} to {dates[-1]}"
        }

    def _get_condition_recommendation(self, condition: str, metrics: Dict[str, Any], alerts: List[str]) -> str:
        """Generate recommendation based on condition and metrics"""
        if alerts:
            return "Please consult with your healthcare provider about the alerts mentioned above."

        recommendations = {
            "diabetes": "Continue monitoring your blood sugar levels. Maintain a balanced diet and regular exercise routine.",
            "hypertension": "Keep tracking your blood pressure daily. Remember to limit sodium intake and stay active.",
            "asthma": "Monitor your peak flow regularly. Keep your rescue inhaler accessible.",
            "heart_disease": "Track your heart rate and symptoms. Follow your medication schedule strictly.",
            "copd": "Monitor oxygen saturation daily. Practice breathing exercises as recommended.",
            "arthritis": "Continue tracking pain levels. Gentle exercise can help maintain mobility."
        }

        return recommendations.get(condition, "Continue monitoring your condition as recommended by your healthcare provider.")

    async def _get_reminders(self, request: AgentRequest) -> AgentResponse:
        """
        Get reminders for a user.

        Expected context:
        - reminder_type: "medication" or "appointment" or "all"
        - date: Optional date (defaults to today)
        """
        user_id = request.user_id
        reminder_type = request.context.get("reminder_type", "all")
        date_str = request.context.get("date", datetime.now().strftime("%Y-%m-%d"))

        from models.health_monitoring import Reminder
        
        # Get reminders for user
        user_reminders = self.db.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.active == True
        ).all()

        # Filter by type (in memory filtering is fine for now, or update query)
        if reminder_type != "all":
            user_reminders = [r for r in user_reminders if r.type == reminder_type]

        # Format reminders for today
        today_reminders = []
        upcoming_reminders = []

        for reminder in user_reminders:
            if reminder["type"] == "medication":
                # Check if any doses are due today
                for time in reminder["times"]:
                    today_reminders.append({
                        "id": reminder["id"],
                        "type": "medication",
                        "medication": reminder["medication"],
                        "dosage": reminder["dosage"],
                        "time": time,
                        "condition": reminder.get("condition", ""),
                        "status": "due"
                    })
            elif reminder["type"] == "appointment":
                # Check if appointment is today or upcoming
                appt_date = reminder["date"]
                if appt_date == date_str:
                    today_reminders.append({
                        "id": reminder["id"],
                        "type": "appointment",
                        "description": reminder["description"],
                        "date": reminder["date"],
                        "time": reminder["time"],
                        "specialty": reminder.get("specialty", ""),
                        "status": "today"
                    })
                elif appt_date > date_str:
                    upcoming_reminders.append({
                        "id": reminder["id"],
                        "type": "appointment",
                        "description": reminder["description"],
                        "date": reminder["date"],
                        "time": reminder["time"],
                        "specialty": reminder.get("specialty", ""),
                        "status": "upcoming"
                    })

        message = f"You have {len(today_reminders)} reminder(s) for today"
        if upcoming_reminders:
            message += f" and {len(upcoming_reminders)} upcoming appointment(s)"

        return AgentResponse(
            agent_name="health_support",
            success=True,
            data={
                "today_reminders": today_reminders,
                "upcoming_reminders": upcoming_reminders,
                "count_today": len(today_reminders),
                "count_upcoming": len(upcoming_reminders),
                "message": message
            },
            confidence=0.95,
            reasoning="Retrieved user reminders"
        )

    def _get_due_reminders_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Helper to get due reminders for a user"""
        from models.health_monitoring import Reminder
        
        current_time = datetime.now()
        current_date = current_time.date()  # Compare date objects

        due_reminders = []
        user_reminders = self.db.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.active == True
        ).all()

        for reminder in user_reminders:
            if reminder.type == "medication":
                # Check times - simplified logic
                if reminder.times:
                    for time in reminder.times:
                        due_reminders.append({
                            "medication": reminder.medication,
                            "dosage": reminder.dosage,
                            "time": time
                        })
            elif reminder.type == "appointment" and reminder.date == current_date:
                due_reminders.append({
                    "appointment": reminder.description,
                    "time": reminder.time
                })

        return due_reminders

    async def _log_symptoms(self, request: AgentRequest) -> AgentResponse:
        """
        Log symptoms reported by user.

        Expected context:
        - symptoms: List of symptoms or single symptom string
        - severity: Severity level (1-10)
        - duration: How long symptoms have been present
        - notes: Additional notes
        """
        user_id = request.user_id
        symptoms_input = request.context.get("symptoms", [])
        severity = request.context.get("severity", 5)
        duration = request.context.get("duration", "")
        notes = request.context.get("notes", "")

        # Normalize symptoms to list
        if isinstance(symptoms_input, str):
            symptoms = [symptoms_input]
        else:
            symptoms = symptoms_input

        # Create symptom log
        symptom_log = {
            "id": f"symptom_{len(self.symptom_logs) + 1:03d}",
            "user_id": user_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "symptoms": symptoms,
            "severity": severity,
            "duration": duration,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }

        self.symptom_logs.append(symptom_log)

        # Check for concerning symptoms
        concerning_symptoms = [
            "chest pain", "severe headache", "difficulty breathing",
            "sudden vision changes", "severe abdominal pain",
            "confusion", "severe dizziness", "loss of consciousness"
        ]

        alerts = []
        escalate = False

        for symptom in symptoms:
            if any(concerning in symptom.lower() for concerning in concerning_symptoms):
                alerts.append(f"ALERT: '{symptom}' may require immediate medical attention.")
                escalate = True

        if severity >= 8:
            alerts.append(f"High severity level ({severity}/10) reported.")
            escalate = True

        recommendation = "Continue monitoring your symptoms."
        if escalate:
            recommendation = "Based on your symptoms, we recommend seeking medical attention. Consider contacting your healthcare provider or visiting urgent care."

        return AgentResponse(
            agent_name="health_support",
            success=True,
            data={
                "symptom_log": symptom_log,
                "alerts": alerts,
                "escalate_to_triage": escalate,
                "recommendation": recommendation,
                "message": f"Logged {len(symptoms)} symptom(s)."
            },
            confidence=0.90,
            reasoning="Symptom logging completed" if not escalate else "Symptoms require escalation"
        )

    async def _track_goal(self, request: AgentRequest) -> AgentResponse:
        """
        Track progress on health goals.

        Expected context:
        - goal_id: ID of the goal to update
        - value: Progress value (steps, calories, hours, etc.)
        - date: Date of progress (defaults to today)
        """
        user_id = request.user_id
        goal_id = request.context.get("goal_id")
        value = request.context.get("value")
        date_str = request.context.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not goal_id:
            # List user's active goals
            user_goals = [g for g in self.health_goals if g["user_id"] == user_id and g.get("active", True)]
            return AgentResponse(
                agent_name="health_support",
                success=True,
                data={
                    "goals": user_goals,
                    "count": len(user_goals),
                    "message": "Please specify goal_id to track progress"
                },
                confidence=0.85,
                reasoning="Listing active goals for user"
            )

        # Find the goal
        goal = None
        for g in self.health_goals:
            if g["id"] == goal_id and g["user_id"] == user_id:
                goal = g
                break

        if not goal:
            return AgentResponse(
                agent_name="health_support",
                success=False,
                data={"error": f"Goal {goal_id} not found for user {user_id}."},
                confidence=0.7,
                reasoning="Goal not found"
            )

        if value is None:
            return AgentResponse(
                agent_name="health_support",
                success=False,
                data={"error": "Please provide a value to track."},
                confidence=0.7,
                reasoning="Missing value parameter"
            )

        # Add progress entry
        progress_entry = {
            "date": date_str,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

        goal["progress"].append(progress_entry)

        # Calculate progress statistics
        target = goal["target"]
        achievement_rate = (value / target) * 100 if target > 0 else 0

        # Get recent progress (last 7 days)
        recent_progress = goal["progress"][-7:]
        avg_progress = sum(p["value"] for p in recent_progress) / len(recent_progress) if recent_progress else 0

        status = "on_track"
        if achievement_rate >= 100:
            status = "goal_met"
            message = f"Congratulations! You've met your {goal['goal_type']} goal for today!"
        elif achievement_rate >= 80:
            status = "almost_there"
            message = f"You're almost there! {achievement_rate:.0f}% of your goal achieved."
        elif achievement_rate >= 50:
            status = "on_track"
            message = f"Good progress! You're at {achievement_rate:.0f}% of your goal."
        else:
            status = "needs_effort"
            message = f"You're at {achievement_rate:.0f}% of your goal. Keep going!"

        return AgentResponse(
            agent_name="health_support",
            success=True,
            data={
                "goal": goal,
                "progress_entry": progress_entry,
                "achievement_rate": round(achievement_rate, 1),
                "status": status,
                "average_recent": round(avg_progress, 1),
                "streak_days": len(recent_progress),
                "message": message
            },
            confidence=0.95,
            reasoning="Goal progress tracked"
        )

    async def _get_health_summary(self, request: AgentRequest) -> AgentResponse:
        """
        Get comprehensive health summary for user.

        Expected context:
        - period: "today", "week", "month"
        """
        user_id = request.user_id
        period = request.context.get("period", "today")

        # Calculate date range
        end_date = datetime.now()
        if period == "today":
            start_date = end_date
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Gather data for period
        check_ins_period = [
            c for c in self.check_ins
            if c["user_id"] == user_id and start_str <= c["date"] <= end_str
        ]

        condition_logs_period = [
            c for c in self.condition_tracking
            if c["user_id"] == user_id and start_str <= c["date"] <= end_str
        ]

        symptom_logs_period = [
            s for s in self.symptom_logs
            if s["user_id"] == user_id and start_str <= s["date"] <= end_str
        ]

        user_goals = [g for g in self.health_goals if g["user_id"] == user_id and g.get("active", True)]

        # Calculate averages
        avg_mood = None
        avg_energy = None
        avg_sleep = None

        if check_ins_period:
            moods = [c["mood"] for c in check_ins_period if c.get("mood")]
            energies = [c["energy_level"] for c in check_ins_period if c.get("energy_level")]
            sleeps = [c["sleep_hours"] for c in check_ins_period if c.get("sleep_hours")]

            avg_mood = round(sum(moods) / len(moods), 1) if moods else None
            avg_energy = round(sum(energies) / len(energies), 1) if energies else None
            avg_sleep = round(sum(sleeps) / len(sleeps), 1) if sleeps else None

        # Generate summary message
        summary_parts = [f"Health summary for the past {period}:"]

        if avg_mood:
            summary_parts.append(f"Average mood: {avg_mood}/10")
        if avg_energy:
            summary_parts.append(f"Average energy: {avg_energy}/10")
        if avg_sleep:
            summary_parts.append(f"Average sleep: {avg_sleep} hours")

        summary_parts.append(f"Check-ins completed: {len(check_ins_period)}")
        summary_parts.append(f"Condition logs: {len(condition_logs_period)}")

        if symptom_logs_period:
            summary_parts.append(f"Symptoms reported: {len(symptom_logs_period)}")

        return AgentResponse(
            agent_name="health_support",
            success=True,
            data={
                "period": period,
                "date_range": f"{start_str} to {end_str}",
                "check_ins": len(check_ins_period),
                "condition_logs": len(condition_logs_period),
                "symptom_logs": len(symptom_logs_period),
                "averages": {
                    "mood": avg_mood,
                    "energy": avg_energy,
                    "sleep": avg_sleep
                },
                "active_goals": len(user_goals),
                "detailed_check_ins": check_ins_period[-5:],  # Last 5 check-ins
                "recent_symptoms": symptom_logs_period[-5:],  # Last 5 symptom logs
                "message": " | ".join(summary_parts)
            },
            confidence=0.93,
            reasoning="Health summary generated"
        )

    async def _schedule_reminder(self, request: AgentRequest) -> AgentResponse:
        """
        Schedule a new reminder.

        Expected context:
        - reminder_type: "medication" or "appointment"
        - For medication: medication, dosage, frequency, times
        - For appointment: description, date, time, specialty
        """
        user_id = request.user_id
        reminder_type = request.context.get("reminder_type")

        if not reminder_type or reminder_type not in ["medication", "appointment"]:
            return AgentResponse(
                agent_name="health_support",
                success=False,
                data={"error": "Please specify reminder_type as 'medication' or 'appointment'."},
                confidence=0.6,
                reasoning="Invalid reminder type"
            )

        reminder_id = f"rem_{len(self.reminders) + 1:03d}"

        if reminder_type == "medication":
            medication = request.context.get("medication")
            dosage = request.context.get("dosage")
            frequency = request.context.get("frequency", "once_daily")
            times = request.context.get("times", [])
            condition = request.context.get("condition", "")

            if not medication or not dosage or not times:
                return AgentResponse(
                    agent_name="health_support",
                    success=False,
                    data={"error": "Please provide medication, dosage, and times for medication reminder."},
                    confidence=0.6,
                    reasoning="Missing required medication reminder fields"
                )

            reminder = {
                "id": reminder_id,
                "user_id": user_id,
                "type": "medication",
                "medication": medication,
                "dosage": dosage,
                "frequency": frequency,
                "times": times,
                "condition": condition,
                "active": True,
                "created_at": datetime.now().isoformat()
            }

            message = f"Medication reminder set for {medication} ({dosage}) at {', '.join(times)}."

        else:  # appointment
            description = request.context.get("description")
            date = request.context.get("date")
            time = request.context.get("time")
            specialty = request.context.get("specialty", "")

            if not description or not date or not time:
                return AgentResponse(
                    agent_name="health_support",
                    success=False,
                    data={"error": "Please provide description, date, and time for appointment reminder."},
                    confidence=0.6,
                    reasoning="Missing required appointment reminder fields"
                )

            reminder = {
                "id": reminder_id,
                "user_id": user_id,
                "type": "appointment",
                "description": description,
                "date": date,
                "time": time,
                "specialty": specialty,
                "active": True,
                "created_at": datetime.now().isoformat()
            }

            message = f"Appointment reminder set for {description} on {date} at {time}."

        self.reminders.append(reminder)

        return AgentResponse(
            agent_name="health_support",
            success=True,
            data={
                "reminder": reminder,
                "reminder_id": reminder_id,
                "message": message
            },
            confidence=0.92,
            reasoning="Reminder scheduled successfully"
        )
