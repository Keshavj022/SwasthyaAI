"""
Nearby Doctors & Referral Agent

This agent helps patients find nearby doctors and generates referral recommendations.
It is NOT a medical AI agent - it provides directory/referral services only.

Responsibilities:
1. Specialty matching (patient condition → appropriate specialist)
2. Local directory search (cached doctor database)
3. Referral explanation (why this specialist is recommended)
4. Filter by location, insurance, availability

Key Features:
- Offline-first cached doctor directory
- Condition-to-specialty matching
- Distance-based sorting (zip code proximity)
- Insurance verification
- Accepting new patients filter
- Referral letter generation

Safety Notes:
- This agent does NOT provide medical advice or diagnoses
- Referrals should be approved by primary care physician
- Patient's insurance coverage should be verified
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
import math


class NearbyDoctorsAgent(BaseAgent):
    """
    Handles doctor search, specialty matching, and referral recommendations.

    This is a DIRECTORY/REFERRAL agent, not a medical AI agent.
    """

    def __init__(self):
        super().__init__()
        self.name = "nearby_doctors"

        # Condition-to-specialty mapping
        self.condition_specialty_map = {
            # Cardiovascular
            "chest pain": ["cardiology", "emergency_medicine"],
            "heart palpitations": ["cardiology"],
            "high blood pressure": ["cardiology", "internal_medicine"],
            "heart disease": ["cardiology"],

            # Dermatology
            "skin rash": ["dermatology", "family_medicine"],
            "acne": ["dermatology"],
            "mole": ["dermatology"],
            "eczema": ["dermatology"],

            # Orthopedics
            "back pain": ["orthopedics", "physical_medicine"],
            "joint pain": ["orthopedics", "rheumatology"],
            "fracture": ["orthopedics", "emergency_medicine"],
            "arthritis": ["rheumatology", "orthopedics"],

            # Neurology
            "headache": ["neurology", "family_medicine"],
            "migraine": ["neurology"],
            "seizure": ["neurology", "emergency_medicine"],
            "numbness": ["neurology"],

            # Gastroenterology
            "stomach pain": ["gastroenterology", "internal_medicine"],
            "acid reflux": ["gastroenterology"],
            "constipation": ["gastroenterology", "family_medicine"],

            # Endocrinology
            "diabetes": ["endocrinology", "internal_medicine"],
            "thyroid": ["endocrinology"],

            # Pulmonology
            "asthma": ["pulmonology", "allergy_immunology"],
            "copd": ["pulmonology"],
            "shortness of breath": ["pulmonology", "cardiology"],

            # Mental Health
            "depression": ["psychiatry", "psychology"],
            "anxiety": ["psychiatry", "psychology"],

            # Pediatrics
            "child checkup": ["pediatrics"],
            "child development": ["pediatrics"],
        }
        
        # Database dependency
        from database import SessionLocal
        self.db = SessionLocal()
        
        # Seed mock data into DB if empty (for transition)
        self._seed_doctors_if_empty()

        # Zip code coordinates (for distance calculation)
        # In production, use a real geocoding service
        self.zip_coordinates = {
            "10001": {"lat": 40.7506, "lon": -73.9971},
            "10002": {"lat": 40.7156, "lon": -73.9862},
            "10003": {"lat": 40.7316, "lon": -73.9895},
            "94102": {"lat": 37.7790, "lon": -122.4177},
            "94103": {"lat": 37.7723, "lon": -122.4127}
        }
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
            
    def _seed_doctors_if_empty(self):
        """Seed doctor data into SQLite if table is empty"""
        from models.directory import Doctor
        if self.db.query(Doctor).count() > 0:
            return
            
        doctors_data = [
            # NYC
            {
                "doctor_id": "doc_001", "name": "Dr. Sarah Johnson", "specialty": "cardiology",
                "zip_code": "10001", "credentials": "MD, FACC", "address": "123 Medical Plaza, New York, NY 10001",
                "phone": "(212) 555-0101", "rating": 4.8, "years_experience": 15,
                "insurance_accepted": ["BlueCross", "Aetna", "UnitedHealthcare", "Medicare"],
                "hospital_affiliations": ["NYU Langone Health"]
            },
            {
                "doctor_id": "doc_002", "name": "Dr. Michael Chen", "specialty": "dermatology",
                "zip_code": "10001", "credentials": "MD, FAAD", "address": "456 Health Center, New York, NY 10001",
                "phone": "(212) 555-0102", "rating": 4.9, "years_experience": 12,
                "insurance_accepted": ["Aetna", "Cigna", "Medicare"],
                "hospital_affiliations": ["Mount Sinai"]
            },
            {
                "doctor_id": "doc_003", "name": "Dr. Emily Rodriguez", "specialty": "pediatrics",
                "zip_code": "10001", "credentials": "MD, FAAP", "address": "789 Children's Clinic, New York, NY 10001",
                "phone": "(212) 555-0103", "rating": 4.7, "years_experience": 10,
                "accepting_new_patients": False,
                "insurance_accepted": ["BlueCross", "UnitedHealthcare"],
                "hospital_affiliations": ["Children's Hospital"]
            },
            # SF
            {
                "doctor_id": "doc_006", "name": "Dr. David Kim", "specialty": "gastroenterology",
                "zip_code": "94102", "credentials": "MD, FACG", "address": "111 GI Specialists, San Francisco, CA 94102",
                "phone": "(415) 555-0201", "rating": 4.7, "years_experience": 11,
                "insurance_accepted": ["Kaiser", "BlueCross", "Aetna"],
                "hospital_affiliations": ["UCSF Medical Center"]
            }
        ]
        
        for data in doctors_data:
            self.db.add(Doctor(**data))
        self.db.commit()

    def get_capabilities(self) -> List[str]:
        """Return keywords that trigger this agent."""
        return [
            "find doctor", "nearby doctor", "specialist", "referral",
            "recommend doctor", "cardiologist", "dermatologist",
            "neurologist", "orthopedist", "pediatrician",
            "accepting new patients", "insurance accepted"
        ]

    def get_description(self) -> str:
        """Return agent description."""
        return "Nearby doctors search and referral recommendations - finds specialists, checks availability, and generates referral explanations"

    def get_confidence_threshold(self) -> float:
        """Minimum confidence to activate this agent."""
        return 0.65

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process nearby doctor and referral requests.

        Supported tasks:
        - search_by_specialty: Find doctors by specialty
        - search_by_condition: Find appropriate specialists for a condition
        - generate_referral: Create referral explanation
        - check_insurance: Check which doctors accept specific insurance
        """

        task = request.context.get("task", "search_by_condition")

        if task == "search_by_specialty":
            return await self._search_by_specialty(request)
        elif task == "search_by_condition":
            return await self._search_by_condition(request)
        elif task == "generate_referral":
            return await self._generate_referral(request)
        elif task == "check_insurance":
            return await self._check_insurance(request)
        else:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={
                    "error": f"Unknown task: {task}",
                    "supported_tasks": [
                        "search_by_specialty",
                        "search_by_condition",
                        "generate_referral",
                        "check_insurance"
                    ]
                },
                reasoning="Task not recognized"
            )

    async def _search_by_specialty(self, request: AgentRequest) -> AgentResponse:
        """Search for doctors by specialty."""

        specialty = request.context.get("specialty", "").lower()
        patient_zip = request.context.get("patient_zip")
        insurance = request.context.get("insurance")
        accepting_new = request.context.get("accepting_new_patients", True)
        max_distance = request.context.get("max_distance_miles", 10)

        if not specialty:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={
                    "error": "Specialty is required",
                    "available_specialties": self._get_all_specialties()
                },
                reasoning="Missing required parameter"
            )

        if not patient_zip:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={"error": "Patient zip code is required"},
                reasoning="Missing required parameter"
            )

        # Search nearby zip codes
        doctors = self._search_doctors(
            specialty=specialty,
            patient_zip=patient_zip,
            insurance=insurance,
            accepting_new=accepting_new,
            max_distance=max_distance
        )

        if not doctors:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=True,
                confidence=0.6,
                data={
                    "message": f"No {specialty} doctors found matching your criteria",
                    "suggestions": [
                        "Try expanding search radius",
                        "Try different insurance plan",
                        "Check for doctors not currently accepting new patients"
                    ],
                    "doctors": []
                },
                reasoning=f"No doctors found for {specialty}"
            )

        return AgentResponse(
            agent_name="nearby_doctors",
            success=True,
            confidence=0.95,
            data={
                "doctors": doctors,
                "count": len(doctors),
                "search_criteria": {
                    "specialty": specialty,
                    "patient_zip": patient_zip,
                    "insurance": insurance,
                    "accepting_new_patients": accepting_new,
                    "max_distance_miles": max_distance
                }
            },
            reasoning=f"Found {len(doctors)} {specialty} doctors",
            suggested_agents=["appointment"]
        )

    async def _search_by_condition(self, request: AgentRequest) -> AgentResponse:
        """Search for appropriate specialists based on medical condition."""

        condition = request.context.get("condition", "").lower()
        patient_zip = request.context.get("patient_zip")
        insurance = request.context.get("insurance")
        accepting_new = request.context.get("accepting_new_patients", True)

        if not condition:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={"error": "Medical condition is required"},
                reasoning="Missing required parameter"
            )

        if not patient_zip:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={"error": "Patient zip code is required"},
                reasoning="Missing required parameter"
            )

        # Map condition to specialties
        recommended_specialties = self._get_specialties_for_condition(condition)

        if not recommended_specialties:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=True,
                confidence=0.5,
                data={
                    "message": f"No specific specialty match for '{condition}'",
                    "recommendation": "Consider starting with family medicine or internal medicine",
                    "suggested_specialties": ["family_medicine", "internal_medicine"],
                    "doctors": []
                },
                reasoning="No specialty mapping found for condition",
                suggested_agents=["communication"]
            )

        # Search for doctors in recommended specialties
        all_doctors = []
        for specialty in recommended_specialties:
            doctors = self._search_doctors(
                specialty=specialty,
                patient_zip=patient_zip,
                insurance=insurance,
                accepting_new=accepting_new,
                max_distance=10
            )
            all_doctors.extend(doctors)

        # Sort by relevance (primary specialty first, then by rating)
        primary_specialty = recommended_specialties[0]
        all_doctors.sort(
            key=lambda d: (
                d["specialty"] != primary_specialty,  # Primary specialty first
                -d["rating"],  # Then by rating (descending)
                d["distance_miles"]  # Then by distance (ascending)
            )
        )

        return AgentResponse(
            agent_name="nearby_doctors",
            success=True,
            confidence=0.90,
            data={
                "condition": condition,
                "recommended_specialties": recommended_specialties,
                "primary_specialty": primary_specialty,
                "doctors": all_doctors[:10],  # Top 10 matches
                "total_found": len(all_doctors),
                "matching_explanation": self._explain_specialty_match(condition, recommended_specialties)
            },
            reasoning=f"Found {len(all_doctors)} doctors for {condition}",
            suggested_agents=["appointment", "communication"]
        )

    async def _generate_referral(self, request: AgentRequest) -> AgentResponse:
        """Generate referral explanation and letter."""

        patient_name = request.context.get("patient_name", "Patient")
        condition = request.context.get("condition")
        doctor_id = request.context.get("doctor_id")
        referring_doctor = request.context.get("referring_doctor", "Primary Care Physician")
        urgency = request.context.get("urgency", "routine")  # routine, urgent, emergency

        if not condition or not doctor_id:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={"error": "Condition and doctor_id are required"},
                reasoning="Missing required parameters"
            )

        # Find doctor in directory
        doctor = self._find_doctor_by_id(doctor_id)

        if not doctor:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={"error": f"Doctor not found: {doctor_id}"},
                reasoning="Invalid doctor ID"
            )

        # Generate referral letter
        referral_letter = self._create_referral_letter(
            patient_name=patient_name,
            condition=condition,
            doctor=doctor,
            referring_doctor=referring_doctor,
            urgency=urgency
        )

        # Generate explanation
        explanation = self._explain_referral(condition, doctor)

        return AgentResponse(
            agent_name="nearby_doctors",
            success=True,
            confidence=1.0,
            data={
                "referral_letter": referral_letter,
                "explanation": explanation,
                "doctor_info": doctor,
                "next_steps": [
                    f"Schedule appointment with {doctor['name']}",
                    "Bring referral letter to first visit",
                    "Bring insurance card and ID",
                    "Prepare list of current medications",
                    "Write down questions for the specialist"
                ]
            },
            reasoning="Generated referral successfully",
            suggested_agents=["appointment"]
        )

    async def _check_insurance(self, request: AgentRequest) -> AgentResponse:
        """Check which doctors accept specific insurance."""
        from models.directory import Doctor

        insurance = request.context.get("insurance")
        specialty = request.context.get("specialty")
        patient_zip = request.context.get("patient_zip")

        if not insurance:
            return AgentResponse(
                agent_name="nearby_doctors",
                success=False,
                confidence=0.0,
                data={"error": "Insurance provider is required"},
                reasoning="Missing required parameter"
            )

        # Search all doctors
        query = self.db.query(Doctor)
        
        # Filter by specialty if provided (database side)
        if specialty:
            query = query.filter(Doctor.specialty == specialty.lower())
            
        all_doctors_db = query.all()
        
        # Filter by insurance (Python side due to JSON storage) and distance
        matching_doctors = []
        for doctor in all_doctors_db:
            if doctor.insurance_accepted and insurance in doctor.insurance_accepted:
                doc_dict = {
                    "doctor_id": doctor.doctor_id,
                    "name": doctor.name,
                    "specialty": doctor.specialty,
                    "address": doctor.address,
                    "phone": doctor.phone,
                    "insurance_accepted": doctor.insurance_accepted,
                    "rating": doctor.rating
                }
                
                if patient_zip:
                    # Basic zip code distance if coordinates available
                    # For robust geo search, would use postgis
                    doc_dict["distance_miles"] = self._calculate_distance(patient_zip, doctor.zip_code)
                
                matching_doctors.append(doc_dict)

        # Sort by distance if patient_zip provided
        if patient_zip:
            matching_doctors.sort(key=lambda d: d.get("distance_miles", 999))

        return AgentResponse(
            agent_name="nearby_doctors",
            success=True,
            confidence=1.0,
            data={
                "insurance": insurance,
                "doctors_accepting": matching_doctors,
                "count": len(matching_doctors),
                "specialty_filter": specialty
            },
            reasoning=f"Found {len(matching_doctors)} doctors accepting {insurance}"
        )

    def _search_doctors(
        self,
        specialty: str,
        patient_zip: str,
        insurance: Optional[str] = None,
        accepting_new: bool = True,
        max_distance: float = 10
    ) -> List[Dict]:
        """Search doctor directory with filters."""
        from models.directory import Doctor

        results = []
        
        # Get all doctors with specialty
        # In production this would be a geospatial query
        query = self.db.query(Doctor).filter(Doctor.specialty == specialty)
        
        if accepting_new:
            query = query.filter(Doctor.accepting_new_patients == True)
            
        candidates = query.all()

        # Filter by distance and insurance
        for doctor in candidates:
            # Calculate distance
            distance = self._calculate_distance(patient_zip, doctor.zip_code)

            if distance > max_distance:
                continue

            # Filter by insurance
            if insurance and (not doctor.insurance_accepted or insurance not in doctor.insurance_accepted):
                continue

            # Add doctor to results
            doctor_dict = {
                "doctor_id": doctor.doctor_id,
                "name": doctor.name,
                "specialty": doctor.specialty,
                "credentials": doctor.credentials,
                "address": doctor.address,
                "phone": doctor.phone,
                "rating": doctor.rating,
                "accepting_new_patients": doctor.accepting_new_patients,
                "insurance_accepted": doctor.insurance_accepted,
                "distance_miles": round(distance, 1),
                "hospital_affiliations": doctor.hospital_affiliations
            }
            results.append(doctor_dict)

        # Sort by distance, then rating
        results.sort(key=lambda d: (d["distance_miles"], -d["rating"]))

        return results

    def _calculate_distance(self, zip1: str, zip2: str) -> float:
        """Calculate distance between two zip codes in miles."""

        if zip1 not in self.zip_coordinates or zip2 not in self.zip_coordinates:
            return 999.0  # Unknown distance

        coords1 = self.zip_coordinates[zip1]
        coords2 = self.zip_coordinates[zip2]

        # Haversine formula
        lat1, lon1 = math.radians(coords1["lat"]), math.radians(coords1["lon"])
        lat2, lon2 = math.radians(coords2["lat"]), math.radians(coords2["lon"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Radius of Earth in miles
        radius_miles = 3959

        return radius_miles * c

    def _get_specialties_for_condition(self, condition: str) -> List[str]:
        """Map medical condition to appropriate specialties."""

        condition_lower = condition.lower()

        # Direct match
        if condition_lower in self.condition_specialty_map:
            return self.condition_specialty_map[condition_lower]

        # Partial match (keyword search)
        for condition_key, specialties in self.condition_specialty_map.items():
            if condition_key in condition_lower or condition_lower in condition_key:
                return specialties

        return []

    def _get_all_specialties(self) -> List[str]:
        """Get list of all available specialties."""
        from models.directory import Doctor
        
        # Get unique specialties from DB
        specialties = self.db.query(Doctor.specialty).distinct().all()
        return sorted([s[0] for s in specialties])

    def _find_doctor_by_id(self, doctor_id: str) -> Optional[Dict]:
        """Find doctor by ID in directory."""
        from models.directory import Doctor
        
        doctor = self.db.query(Doctor).filter(Doctor.doctor_id == doctor_id).first()
        
        if not doctor:
            return None
            
        return {
            "doctor_id": doctor.doctor_id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "credentials": doctor.credentials,
            "address": doctor.address,
            "phone": doctor.phone,
            "rating": doctor.rating,
            "years_experience": doctor.years_experience,
            "hospital_affiliations": doctor.hospital_affiliations
        }

    def _create_referral_letter(
        self,
        patient_name: str,
        condition: str,
        doctor: Dict,
        referring_doctor: str,
        urgency: str
    ) -> str:
        """Generate referral letter."""

        urgency_text = {
            "routine": "at your earliest convenience",
            "urgent": "within the next 1-2 weeks",
            "emergency": "URGENTLY - within 24-48 hours"
        }.get(urgency, "at your earliest convenience")

        letter = f"""
MEDICAL REFERRAL

Date: {datetime.now().strftime("%B %d, %Y")}

To: {doctor['name']}, {doctor['credentials']}
    {doctor['specialty'].title()}
    {doctor['address']}
    Phone: {doctor['phone']}

From: {referring_doctor}

Re: {patient_name}

Dear {doctor['name']},

I am referring the above patient to your care for evaluation and management of {condition}.

Please see this patient {urgency_text}.

The patient has been informed that they may need to schedule an appointment directly with your office. Please contact me if you need any additional information.

Thank you for your assistance in caring for this patient.

Sincerely,
{referring_doctor}

---
PATIENT INSTRUCTIONS:
1. Call {doctor['phone']} to schedule an appointment
2. Mention this referral when calling
3. Bring this letter to your first visit
4. Bring your insurance card and photo ID
5. Prepare a list of current medications
"""

        return letter.strip()

    def _explain_referral(self, condition: str, doctor: Dict) -> str:
        """Explain why this referral is appropriate."""

        specialty = doctor["specialty"].replace("_", " ").title()

        explanations = {
            "cardiology": f"{specialty} specialists focus on heart and cardiovascular conditions. They have advanced training in diagnosing and treating {condition}.",
            "dermatology": f"{specialty} specialists are experts in skin conditions. They can properly diagnose and treat {condition}.",
            "orthopedics": f"{specialty} specialists focus on bones, joints, and muscles. They are best equipped to evaluate and treat {condition}.",
            "neurology": f"{specialty} specialists focus on the nervous system. They have specialized training to diagnose and manage {condition}.",
            "gastroenterology": f"{specialty} specialists focus on digestive system disorders. They can provide expert care for {condition}.",
            "endocrinology": f"{specialty} specialists focus on hormonal and metabolic conditions. They are experts in managing {condition}.",
            "pulmonology": f"{specialty} specialists focus on lung and respiratory conditions. They can provide specialized care for {condition}.",
            "psychiatry": f"{specialty} specialists focus on mental health conditions. They can provide expert evaluation and treatment for {condition}."
        }

        base_explanation = explanations.get(
            doctor["specialty"],
            f"{specialty} specialists have advanced training in conditions like {condition}."
        )

        return f"{base_explanation}\n\nDr. {doctor['name']} has {doctor['years_experience']} years of experience and is affiliated with {', '.join(doctor['hospital_affiliations'])}."

    def _explain_specialty_match(self, condition: str, specialties: List[str]) -> str:
        """Explain why these specialties match the condition."""

        primary = specialties[0].replace("_", " ").title()

        if len(specialties) == 1:
            return f"{primary} is the most appropriate specialty for {condition}."
        else:
            others = ", ".join([s.replace("_", " ").title() for s in specialties[1:]])
            return f"{primary} is the primary recommended specialty for {condition}. {others} may also be appropriate depending on the specific situation."
