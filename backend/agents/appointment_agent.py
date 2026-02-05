"""
Appointment & Hospital Operations Agent

This agent handles appointment scheduling, doctor availability, and follow-ups.
It is NOT a medical AI agent - it provides administrative/operational support.

Responsibilities:
1. Appointment booking with conflict detection
2. Doctor availability checking
3. Follow-up appointment scheduling
4. Appointment rescheduling/cancellation
5. Patient appointment history

Key Features:
- Offline-first scheduling (local database only)
- Automatic conflict detection (prevents double-booking)
- Duration-based scheduling (different appointment types)
- Working hours enforcement
- Multi-specialty support
- Urgent care prioritization

Safety Notes:
- This agent does NOT provide medical advice or diagnoses
- All appointments must be confirmed by clinic staff
- Emergency cases should be directed to Triage Agent first
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from orchestrator.base import BaseAgent, AgentRequest, AgentResponse


class AppointmentAgent(BaseAgent):
    """
    Handles appointment scheduling and hospital operations.

    This is an ADMINISTRATIVE agent, not a medical AI agent.
    """

    def __init__(self):
        super().__init__()

        # Appointment types with standard durations (minutes)
        self.appointment_types = {
            "initial_consultation": {
                "duration": 60,
                "description": "First visit with new doctor",
                "requires_prep": True
            },
            "follow_up": {
                "duration": 30,
                "description": "Follow-up visit after treatment",
                "requires_prep": False
            },
            "routine_checkup": {
                "duration": 30,
                "description": "Annual physical or routine exam",
                "requires_prep": True
            },
            "urgent_care": {
                "duration": 45,
                "description": "Same-day urgent medical issue",
                "requires_prep": False
            },
            "procedure": {
                "duration": 90,
                "description": "Minor procedure or diagnostic test",
                "requires_prep": True
            },
            "telemedicine": {
                "duration": 20,
                "description": "Virtual consultation",
                "requires_prep": False
            }
        }

        # Clinic operating hours (24-hour format)
        self.clinic_hours = {
            "monday": {"open": "08:00", "close": "18:00"},
            "tuesday": {"open": "08:00", "close": "18:00"},
            "wednesday": {"open": "08:00", "close": "18:00"},
            "thursday": {"open": "08:00", "close": "18:00"},
            "friday": {"open": "08:00", "close": "17:00"},
            "saturday": {"open": "09:00", "close": "13:00"},
            "sunday": {"open": None, "close": None}  # Closed
        }

        # Doctor specialties
        self.specialties = [
            "family_medicine", "internal_medicine", "pediatrics",
            "cardiology", "dermatology", "orthopedics",
            "neurology", "psychiatry", "obstetrics_gynecology"
        ]

        # Mock doctor database (in production, this would be from DB)
        self.doctors = {
            "doctor_001": {
                "name": "Dr. Sarah Johnson",
                "specialty": "family_medicine",
                "available_days": ["monday", "tuesday", "wednesday", "friday"]
            },
            "doctor_002": {
                "name": "Dr. Michael Chen",
                "specialty": "cardiology",
                "available_days": ["monday", "wednesday", "thursday", "friday"]
            },
            "doctor_003": {
                "name": "Dr. Emily Rodriguez",
                "specialty": "pediatrics",
                "available_days": ["tuesday", "wednesday", "thursday", "saturday"]
            },
            "doctor_004": {
                "name": "Dr. James Wilson",
                "specialty": "internal_medicine",
                "available_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            }
        }

        # Mock appointment database (in production, this would be SQLite)
        self.appointments = []

    def get_capabilities(self) -> List[str]:
        """Return keywords that trigger this agent."""
        return [
            "appointment", "schedule", "book", "availability",
            "reschedule", "cancel", "follow-up", "available",
            "doctor available", "clinic hours", "telemedicine",
            "virtual appointment", "urgent care"
        ]

    def get_description(self) -> str:
        """Return agent description."""
        return "Appointment scheduling and hospital operations - handles booking, cancellations, doctor availability, and follow-ups"

    def get_confidence_threshold(self) -> float:
        """Minimum confidence to activate this agent."""
        return 0.70

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process appointment-related requests.

        Supported tasks:
        - book_appointment: Schedule a new appointment
        - check_availability: Check doctor availability
        - reschedule: Change appointment date/time
        - cancel: Cancel an appointment
        - list_appointments: Get patient's appointments
        - schedule_followup: Schedule follow-up after visit
        """

        task = request.context.get("task", "book_appointment")

        if task == "book_appointment":
            return await self._book_appointment(request)
        elif task == "check_availability":
            return await self._check_availability(request)
        elif task == "reschedule":
            return await self._reschedule_appointment(request)
        elif task == "cancel":
            return await self._cancel_appointment(request)
        elif task == "list_appointments":
            return await self._list_appointments(request)
        elif task == "schedule_followup":
            return await self._schedule_followup(request)
        else:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={
                    "error": f"Unknown task: {task}",
                    "supported_tasks": [
                        "book_appointment",
                        "check_availability",
                        "reschedule",
                        "cancel",
                        "list_appointments",
                        "schedule_followup"
                    ]
                },
                reasoning="Task not recognized"
            )

    async def _book_appointment(self, request: AgentRequest) -> AgentResponse:
        """Book a new appointment with conflict detection."""

        patient_id = request.user_id
        doctor_id = request.context.get("doctor_id")
        specialty = request.context.get("specialty")
        appointment_type = request.context.get("appointment_type", "routine_checkup")
        preferred_date = request.context.get("preferred_date")  # YYYY-MM-DD
        preferred_time = request.context.get("preferred_time")  # HH:MM
        reason = request.context.get("reason", "")

        # Validation
        if not doctor_id and not specialty:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={
                    "error": "Must specify either doctor_id or specialty",
                    "available_specialties": self.specialties
                },
                reasoning="Missing required parameters"
            )

        if appointment_type not in self.appointment_types:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={
                    "error": f"Unknown appointment type: {appointment_type}",
                    "available_types": list(self.appointment_types.keys())
                },
                reasoning="Invalid appointment type"
            )

        # Find doctor if only specialty specified
        if not doctor_id and specialty:
            available_doctors = [
                (doc_id, doc_info)
                for doc_id, doc_info in self.doctors.items()
                if doc_info["specialty"] == specialty
            ]

            if not available_doctors:
                return AgentResponse(agent_name="appointment", 
                    success=False,
                    confidence=0.0,
                    data={
                        "error": f"No doctors available for specialty: {specialty}",
                        "available_specialties": list(set(
                            doc["specialty"] for doc in self.doctors.values()
                        ))
                    },
                    reasoning="No doctors found for requested specialty"
                )

            # Pick first available doctor
            doctor_id, doctor_info = available_doctors[0]
        else:
            doctor_info = self.doctors.get(doctor_id)
            if not doctor_info:
                return AgentResponse(agent_name="appointment", 
                    success=False,
                    confidence=0.0,
                    data={"error": f"Doctor not found: {doctor_id}"},
                    reasoning="Invalid doctor ID"
                )

        # Parse date/time
        try:
            appointment_datetime = datetime.strptime(
                f"{preferred_date} {preferred_time}",
                "%Y-%m-%d %H:%M"
            )
        except (ValueError, TypeError):
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={
                    "error": "Invalid date/time format",
                    "expected_format": "Date: YYYY-MM-DD, Time: HH:MM",
                    "example": "Date: 2026-02-10, Time: 14:30"
                },
                reasoning="Date/time parsing failed"
            )

        # Check if appointment is in the past
        if appointment_datetime < datetime.now():
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": "Cannot book appointments in the past"},
                reasoning="Past date requested"
            )

        # Check if clinic is open
        day_of_week = appointment_datetime.strftime("%A").lower()
        clinic_schedule = self.clinic_hours.get(day_of_week)

        if not clinic_schedule["open"]:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.5,
                data={
                    "error": f"Clinic is closed on {day_of_week.title()}",
                    "suggestion": "Please choose a different day",
                    "open_days": [
                        day for day, hours in self.clinic_hours.items()
                        if hours["open"]
                    ]
                },
                reasoning="Clinic closed on requested day"
            )

        # Check if time is within clinic hours
        appointment_time_str = appointment_datetime.strftime("%H:%M")
        if not self._is_within_clinic_hours(appointment_time_str, clinic_schedule):
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.5,
                data={
                    "error": "Appointment time outside clinic hours",
                    "clinic_hours": f"{clinic_schedule['open']} - {clinic_schedule['close']}",
                    "requested_time": appointment_time_str
                },
                reasoning="Requested time outside operating hours"
            )

        # Check doctor availability for that day
        if day_of_week not in doctor_info["available_days"]:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.5,
                data={
                    "error": f"{doctor_info['name']} is not available on {day_of_week.title()}",
                    "doctor_available_days": doctor_info["available_days"],
                    "suggestion": "Try a different day or different doctor"
                },
                reasoning="Doctor not available on requested day"
            )

        # Check for conflicts (double-booking)
        duration = self.appointment_types[appointment_type]["duration"]
        appointment_end = appointment_datetime + timedelta(minutes=duration)

        conflict = self._check_conflict(doctor_id, appointment_datetime, appointment_end)
        if conflict:
            # Find next available slot
            next_slot = self._find_next_available_slot(
                doctor_id,
                appointment_datetime,
                duration
            )

            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.5,
                data={
                    "error": "Time slot already booked",
                    "conflict_with": conflict,
                    "next_available_slot": next_slot,
                    "suggestion": f"Next available: {next_slot['date']} at {next_slot['time']}"
                },
                reasoning="Scheduling conflict detected",
                suggested_agents=[]
            )

        # Book the appointment
        appointment_id = f"appt_{len(self.appointments) + 1:06d}"
        appointment = {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor_info["name"],
            "specialty": doctor_info["specialty"],
            "appointment_type": appointment_type,
            "date": preferred_date,
            "time": preferred_time,
            "duration_minutes": duration,
            "reason": reason,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "end_time": appointment_end.strftime("%H:%M")
        }

        self.appointments.append(appointment)

        return AgentResponse(agent_name="appointment", 
            success=True,
            confidence=1.0,
            data={
                "appointment": appointment,
                "confirmation_message": f"Appointment booked with {doctor_info['name']}",
                "appointment_details": {
                    "date": preferred_date,
                    "time": f"{preferred_time} - {appointment['end_time']}",
                    "duration": f"{duration} minutes",
                    "type": appointment_type,
                    "location": "Main Clinic"
                },
                "preparation_required": self.appointment_types[appointment_type]["requires_prep"],
                "reminder": "You will receive a reminder 24 hours before your appointment"
            },
            reasoning=f"Successfully scheduled {appointment_type} appointment",
            suggested_agents=[]
        )

    async def _check_availability(self, request: AgentRequest) -> AgentResponse:
        """Check doctor availability for a given date/time range."""

        doctor_id = request.context.get("doctor_id")
        specialty = request.context.get("specialty")
        date = request.context.get("date")  # YYYY-MM-DD

        if not doctor_id and not specialty:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": "Must specify either doctor_id or specialty"},
                reasoning="Missing required parameters"
            )

        # Filter doctors
        if doctor_id:
            doctors_to_check = {doctor_id: self.doctors[doctor_id]} if doctor_id in self.doctors else {}
        else:
            doctors_to_check = {
                doc_id: doc_info
                for doc_id, doc_info in self.doctors.items()
                if doc_info["specialty"] == specialty
            }

        if not doctors_to_check:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": "No doctors found"},
                reasoning="No matching doctors"
            )

        # Get available slots
        availability = {}

        for doc_id, doc_info in doctors_to_check.items():
            if date:
                # Specific date
                slots = self._get_available_slots(doc_id, date)
                availability[doc_id] = {
                    "doctor_name": doc_info["name"],
                    "specialty": doc_info["specialty"],
                    "date": date,
                    "available_slots": slots
                }
            else:
                # Next 7 days
                availability[doc_id] = {
                    "doctor_name": doc_info["name"],
                    "specialty": doc_info["specialty"],
                    "available_days": doc_info["available_days"]
                }

        return AgentResponse(agent_name="appointment", 
            success=True,
            confidence=1.0,
            data={
                "availability": availability,
                "total_doctors": len(availability)
            },
            reasoning="Successfully retrieved availability",
            suggested_agents=[]
        )

    async def _reschedule_appointment(self, request: AgentRequest) -> AgentResponse:
        """Reschedule an existing appointment."""

        appointment_id = request.context.get("appointment_id")
        new_date = request.context.get("new_date")
        new_time = request.context.get("new_time")

        # Find appointment
        appointment = next(
            (appt for appt in self.appointments if appt["appointment_id"] == appointment_id),
            None
        )

        if not appointment:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": f"Appointment not found: {appointment_id}"},
                reasoning="Invalid appointment ID"
            )

        if appointment["status"] == "cancelled":
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": "Cannot reschedule a cancelled appointment"},
                reasoning="Appointment already cancelled"
            )

        # Cancel old appointment and book new one
        old_date = appointment["date"]
        old_time = appointment["time"]

        appointment["status"] = "rescheduled"

        # Book new appointment
        new_request = AgentRequest(
            message=f"Reschedule from {old_date} {old_time}",
            user_id=request.user_id,
            context={
                "task": "book_appointment",
                "doctor_id": appointment["doctor_id"],
                "appointment_type": appointment["appointment_type"],
                "preferred_date": new_date,
                "preferred_time": new_time,
                "reason": appointment["reason"]
            }
        )

        booking_result = await self._book_appointment(new_request)

        if booking_result.success:
            return AgentResponse(agent_name="appointment", 
                success=True,
                confidence=1.0,
                data={
                    "message": "Appointment rescheduled successfully",
                    "old_appointment": {
                        "date": old_date,
                        "time": old_time
                    },
                    "new_appointment": booking_result.data["appointment"]
                },
                reasoning="Successfully rescheduled appointment",
                suggested_agents=[]
            )
        else:
            # Restore old appointment if rescheduling failed
            appointment["status"] = "scheduled"
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={
                    "error": "Could not reschedule to requested time",
                    "details": booking_result.data,
                    "original_appointment_restored": True
                },
                reasoning="Rescheduling failed - time slot not available"
            )

    async def _cancel_appointment(self, request: AgentRequest) -> AgentResponse:
        """Cancel an appointment."""

        appointment_id = request.context.get("appointment_id")
        reason = request.context.get("reason", "Patient requested cancellation")

        appointment = next(
            (appt for appt in self.appointments if appt["appointment_id"] == appointment_id),
            None
        )

        if not appointment:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": f"Appointment not found: {appointment_id}"},
                reasoning="Invalid appointment ID"
            )

        if appointment["status"] == "cancelled":
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": "Appointment already cancelled"},
                reasoning="Appointment already cancelled"
            )

        appointment["status"] = "cancelled"
        appointment["cancellation_reason"] = reason
        appointment["cancelled_at"] = datetime.now().isoformat()

        return AgentResponse(agent_name="appointment", 
            success=True,
            confidence=1.0,
            data={
                "message": "Appointment cancelled successfully",
                "cancelled_appointment": appointment,
                "refund_policy": "Cancellations made 24+ hours in advance are fully refundable"
            },
            reasoning="Successfully cancelled appointment",
            suggested_agents=[]
        )

    async def _list_appointments(self, request: AgentRequest) -> AgentResponse:
        """List patient's appointments."""

        patient_id = request.user_id
        status_filter = request.context.get("status", "all")  # all, scheduled, cancelled, completed

        patient_appointments = [
            appt for appt in self.appointments
            if appt["patient_id"] == patient_id
        ]

        if status_filter != "all":
            patient_appointments = [
                appt for appt in patient_appointments
                if appt["status"] == status_filter
            ]

        # Sort by date/time
        patient_appointments.sort(
            key=lambda x: datetime.strptime(f"{x['date']} {x['time']}", "%Y-%m-%d %H:%M")
        )

        # Separate upcoming and past
        now = datetime.now()
        upcoming = []
        past = []

        for appt in patient_appointments:
            appt_dt = datetime.strptime(f"{appt['date']} {appt['time']}", "%Y-%m-%d %H:%M")
            if appt_dt >= now and appt["status"] == "scheduled":
                upcoming.append(appt)
            else:
                past.append(appt)

        return AgentResponse(agent_name="appointment", 
            success=True,
            confidence=1.0,
            data={
                "upcoming_appointments": upcoming,
                "past_appointments": past,
                "total_appointments": len(patient_appointments),
                "upcoming_count": len(upcoming),
                "past_count": len(past)
            },
            reasoning=f"Retrieved {len(patient_appointments)} appointments",
            suggested_agents=[]
        )

    async def _schedule_followup(self, request: AgentRequest) -> AgentResponse:
        """Schedule a follow-up appointment after a visit."""

        original_appointment_id = request.context.get("original_appointment_id")
        followup_weeks = request.context.get("followup_weeks", 2)  # Default 2 weeks
        preferred_time = request.context.get("preferred_time", "10:00")

        # Find original appointment
        original = next(
            (appt for appt in self.appointments if appt["appointment_id"] == original_appointment_id),
            None
        )

        if not original:
            return AgentResponse(agent_name="appointment", 
                success=False,
                confidence=0.0,
                data={"error": "Original appointment not found"},
                reasoning="Invalid appointment ID"
            )

        # Calculate follow-up date
        original_date = datetime.strptime(original["date"], "%Y-%m-%d")
        followup_date = original_date + timedelta(weeks=followup_weeks)

        # Book follow-up
        followup_request = AgentRequest(
            message=f"Schedule follow-up for {original_appointment_id}",
            user_id=request.user_id,
            context={
                "task": "book_appointment",
                "doctor_id": original["doctor_id"],
                "appointment_type": "follow_up",
                "preferred_date": followup_date.strftime("%Y-%m-%d"),
                "preferred_time": preferred_time,
                "reason": f"Follow-up for appointment {original_appointment_id}"
            }
        )

        return await self._book_appointment(followup_request)

    def _is_within_clinic_hours(self, time_str: str, clinic_schedule: Dict) -> bool:
        """Check if time is within clinic operating hours."""
        time = datetime.strptime(time_str, "%H:%M").time()
        open_time = datetime.strptime(clinic_schedule["open"], "%H:%M").time()
        close_time = datetime.strptime(clinic_schedule["close"], "%H:%M").time()

        return open_time <= time < close_time

    def _check_conflict(
        self,
        doctor_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[Dict]:
        """Check if there's a scheduling conflict."""

        for appt in self.appointments:
            if appt["doctor_id"] != doctor_id:
                continue

            if appt["status"] != "scheduled":
                continue

            appt_start = datetime.strptime(
                f"{appt['date']} {appt['time']}",
                "%Y-%m-%d %H:%M"
            )
            appt_end = appt_start + timedelta(minutes=appt["duration_minutes"])

            # Check for overlap
            if (start_time < appt_end) and (end_time > appt_start):
                return {
                    "appointment_id": appt["appointment_id"],
                    "time": f"{appt['time']} - {appt['end_time']}",
                    "patient_id": appt["patient_id"]
                }

        return None

    def _find_next_available_slot(
        self,
        doctor_id: str,
        from_datetime: datetime,
        duration_minutes: int
    ) -> Dict[str, str]:
        """Find next available time slot for doctor."""

        # Start from requested time
        current = from_datetime
        max_search_days = 14

        for _ in range(max_search_days):
            day_of_week = current.strftime("%A").lower()
            doctor_info = self.doctors[doctor_id]

            # Check if doctor works this day
            if day_of_week in doctor_info["available_days"]:
                clinic_schedule = self.clinic_hours[day_of_week]

                if clinic_schedule["open"]:
                    # Check slots in 30-minute increments
                    slot_time = datetime.strptime(
                        f"{current.strftime('%Y-%m-%d')} {clinic_schedule['open']}",
                        "%Y-%m-%d %H:%M"
                    )
                    close_time = datetime.strptime(
                        f"{current.strftime('%Y-%m-%d')} {clinic_schedule['close']}",
                        "%Y-%m-%d %H:%M"
                    )

                    while slot_time + timedelta(minutes=duration_minutes) <= close_time:
                        end_time = slot_time + timedelta(minutes=duration_minutes)

                        if not self._check_conflict(doctor_id, slot_time, end_time):
                            return {
                                "date": slot_time.strftime("%Y-%m-%d"),
                                "time": slot_time.strftime("%H:%M")
                            }

                        slot_time += timedelta(minutes=30)

            # Move to next day
            current += timedelta(days=1)

        # No slots found in next 14 days
        return {
            "date": "Not available",
            "time": "Please call clinic"
        }

    def _get_available_slots(self, doctor_id: str, date: str) -> List[str]:
        """Get all available time slots for a doctor on a specific date."""

        target_date = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = target_date.strftime("%A").lower()

        doctor_info = self.doctors[doctor_id]

        # Check if doctor works this day
        if day_of_week not in doctor_info["available_days"]:
            return []

        clinic_schedule = self.clinic_hours[day_of_week]
        if not clinic_schedule["open"]:
            return []

        # Generate 30-minute slots
        available_slots = []
        slot_time = datetime.strptime(f"{date} {clinic_schedule['open']}", "%Y-%m-%d %H:%M")
        close_time = datetime.strptime(f"{date} {clinic_schedule['close']}", "%Y-%m-%d %H:%M")

        while slot_time + timedelta(minutes=30) <= close_time:
            end_time = slot_time + timedelta(minutes=30)

            if not self._check_conflict(doctor_id, slot_time, end_time):
                available_slots.append(slot_time.strftime("%H:%M"))

            slot_time += timedelta(minutes=30)

        return available_slots
