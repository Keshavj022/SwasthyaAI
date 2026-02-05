"""
Seed Demo Data Script

Populates the database with realistic demo data for judge demonstrations.
Run this script before the demo to ensure all agents have data to work with.

Usage:
    python seed_demo_data.py
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

# Import models (you'll need to adjust based on actual model locations)
# For now, we'll use raw SQL to be independent of model definitions


def get_database_connection():
    """Create database connection"""
    engine = create_engine(DATABASE_URL.replace('+aiosqlite', ''))
    return engine


def seed_patients(conn):
    """Seed demo patient data"""
    print("Seeding patients...")

    patients = [
        {
            "patient_id": "demo_patient_001",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1975-06-15",
            "gender": "male",
            "email": "john.doe@example.com",
            "phone": "555-0101",
            "address": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62701",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "555-0102",
            "insurance_provider": "Blue Cross",
            "insurance_policy_number": "BC123456789",
            "created_at": datetime.now().isoformat()
        },
        {
            "patient_id": "demo_patient_002",
            "first_name": "Maria",
            "last_name": "Garcia",
            "date_of_birth": "1988-03-22",
            "gender": "female",
            "email": "maria.garcia@example.com",
            "phone": "555-0103",
            "address": "456 Oak Ave",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62702",
            "emergency_contact_name": "Carlos Garcia",
            "emergency_contact_phone": "555-0104",
            "insurance_provider": "Aetna",
            "insurance_policy_number": "AE987654321",
            "created_at": datetime.now().isoformat()
        },
        {
            "patient_id": "demo_patient_003",
            "first_name": "Robert",
            "last_name": "Johnson",
            "date_of_birth": "1955-11-08",
            "gender": "male",
            "email": "robert.j@example.com",
            "phone": "555-0105",
            "address": "789 Pine Rd",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62703",
            "emergency_contact_name": "Sarah Johnson",
            "emergency_contact_phone": "555-0106",
            "insurance_provider": "Medicare",
            "insurance_policy_number": "MC456789012",
            "created_at": datetime.now().isoformat()
        },
        {
            "patient_id": "demo_patient_emergency",
            "first_name": "Michael",
            "last_name": "Thompson",
            "date_of_birth": "1970-09-14",
            "gender": "male",
            "email": "michael.t@example.com",
            "phone": "555-0107",
            "address": "321 Elm St",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62704",
            "emergency_contact_name": "Linda Thompson",
            "emergency_contact_phone": "555-0108",
            "insurance_provider": "United Healthcare",
            "insurance_policy_number": "UH789012345",
            "created_at": datetime.now().isoformat()
        },
        {
            "patient_id": "demo_patient_diabetes",
            "first_name": "Lisa",
            "last_name": "Anderson",
            "date_of_birth": "1982-04-30",
            "gender": "female",
            "email": "lisa.a@example.com",
            "phone": "555-0109",
            "address": "654 Maple Dr",
            "city": "Springfield",
            "state": "IL",
            "zip_code": "62705",
            "emergency_contact_name": "Tom Anderson",
            "emergency_contact_phone": "555-0110",
            "insurance_provider": "Cigna",
            "insurance_policy_number": "CG234567890",
            "created_at": datetime.now().isoformat()
        }
    ]

    try:
        # Try to create patients table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                insurance_provider TEXT,
                insurance_policy_number TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """))
        conn.commit()

        # Insert patients
        for patient in patients:
            try:
                conn.execute(text("""
                    INSERT OR REPLACE INTO patients
                    (patient_id, first_name, last_name, date_of_birth, gender, email, phone,
                     address, city, state, zip_code, emergency_contact_name, emergency_contact_phone,
                     insurance_provider, insurance_policy_number, created_at)
                    VALUES
                    (:patient_id, :first_name, :last_name, :date_of_birth, :gender, :email, :phone,
                     :address, :city, :state, :zip_code, :emergency_contact_name, :emergency_contact_phone,
                     :insurance_provider, :insurance_policy_number, :created_at)
                """), patient)
            except Exception as e:
                print(f"Warning: Could not insert patient {patient['patient_id']}: {e}")

        conn.commit()
        print(f"✓ Seeded {len(patients)} patients")
    except Exception as e:
        print(f"Error seeding patients: {e}")


def seed_chronic_conditions(conn):
    """Seed chronic conditions for demo patients"""
    print("Seeding chronic conditions...")

    conditions = [
        {
            "patient_id": "demo_patient_diabetes",
            "condition": "Type 2 Diabetes",
            "diagnosed_date": "2018-05-15",
            "severity": "moderate",
            "status": "active",
            "notes": "Managed with Metformin and lifestyle changes"
        },
        {
            "patient_id": "demo_patient_003",
            "condition": "Hypertension",
            "diagnosed_date": "2012-03-20",
            "severity": "moderate",
            "status": "active",
            "notes": "Controlled with Lisinopril 10mg daily"
        },
        {
            "patient_id": "demo_patient_003",
            "condition": "Hyperlipidemia",
            "diagnosed_date": "2015-08-10",
            "severity": "mild",
            "status": "active",
            "notes": "Managed with Atorvastatin and diet"
        },
        {
            "patient_id": "demo_patient_emergency",
            "condition": "Coronary Artery Disease",
            "diagnosed_date": "2019-11-05",
            "severity": "severe",
            "status": "active",
            "notes": "History of MI, on dual antiplatelet therapy"
        }
    ]

    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chronic_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                condition TEXT NOT NULL,
                diagnosed_date TEXT,
                severity TEXT,
                status TEXT,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """))
        conn.commit()

        for condition in conditions:
            condition['created_at'] = datetime.now().isoformat()
            try:
                conn.execute(text("""
                    INSERT INTO chronic_conditions
                    (patient_id, condition, diagnosed_date, severity, status, notes, created_at)
                    VALUES
                    (:patient_id, :condition, :diagnosed_date, :severity, :status, :notes, :created_at)
                """), condition)
            except Exception as e:
                print(f"Warning: Could not insert condition: {e}")

        conn.commit()
        print(f"✓ Seeded {len(conditions)} chronic conditions")
    except Exception as e:
        print(f"Error seeding chronic conditions: {e}")


def seed_medications(conn):
    """Seed current medications for demo patients"""
    print("Seeding medications...")

    medications = [
        {
            "patient_id": "demo_patient_diabetes",
            "medication_name": "Metformin",
            "dosage": "500mg",
            "frequency": "twice daily",
            "route": "oral",
            "start_date": "2018-05-15",
            "prescribing_doctor": "Dr. Emily Chen",
            "purpose": "Type 2 Diabetes management",
            "active": True
        },
        {
            "patient_id": "demo_patient_003",
            "medication_name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "once daily",
            "route": "oral",
            "start_date": "2012-03-20",
            "prescribing_doctor": "Dr. Robert Wilson",
            "purpose": "Hypertension control",
            "active": True
        },
        {
            "patient_id": "demo_patient_003",
            "medication_name": "Atorvastatin",
            "dosage": "20mg",
            "frequency": "once daily at bedtime",
            "route": "oral",
            "start_date": "2015-08-10",
            "prescribing_doctor": "Dr. Robert Wilson",
            "purpose": "Cholesterol management",
            "active": True
        },
        {
            "patient_id": "demo_patient_emergency",
            "medication_name": "Aspirin",
            "dosage": "81mg",
            "frequency": "once daily",
            "route": "oral",
            "start_date": "2019-11-05",
            "prescribing_doctor": "Dr. Sarah Martinez",
            "purpose": "Antiplatelet therapy post-MI",
            "active": True
        },
        {
            "patient_id": "demo_patient_emergency",
            "medication_name": "Clopidogrel",
            "dosage": "75mg",
            "frequency": "once daily",
            "route": "oral",
            "start_date": "2019-11-05",
            "prescribing_doctor": "Dr. Sarah Martinez",
            "purpose": "Dual antiplatelet therapy post-MI",
            "active": True
        }
    ]

    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                medication_name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                route TEXT,
                start_date TEXT,
                end_date TEXT,
                prescribing_doctor TEXT,
                purpose TEXT,
                active BOOLEAN,
                created_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """))
        conn.commit()

        for medication in medications:
            medication['created_at'] = datetime.now().isoformat()
            try:
                conn.execute(text("""
                    INSERT INTO medications
                    (patient_id, medication_name, dosage, frequency, route, start_date,
                     prescribing_doctor, purpose, active, created_at)
                    VALUES
                    (:patient_id, :medication_name, :dosage, :frequency, :route, :start_date,
                     :prescribing_doctor, :purpose, :active, :created_at)
                """), medication)
            except Exception as e:
                print(f"Warning: Could not insert medication: {e}")

        conn.commit()
        print(f"✓ Seeded {len(medications)} medications")
    except Exception as e:
        print(f"Error seeding medications: {e}")


def seed_allergies(conn):
    """Seed patient allergies"""
    print("Seeding allergies...")

    allergies = [
        {
            "patient_id": "demo_patient_001",
            "allergen": "Penicillin",
            "allergen_type": "medication",
            "reaction": "Rash and hives",
            "severity": "moderate",
            "onset_date": "1995-06-01"
        },
        {
            "patient_id": "demo_patient_002",
            "allergen": "Latex",
            "allergen_type": "environmental",
            "reaction": "Contact dermatitis",
            "severity": "mild",
            "onset_date": "2010-02-15"
        },
        {
            "patient_id": "demo_patient_003",
            "allergen": "Sulfa drugs",
            "allergen_type": "medication",
            "reaction": "Severe rash and difficulty breathing",
            "severity": "severe",
            "onset_date": "2008-11-20"
        }
    ]

    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS allergies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                allergen TEXT NOT NULL,
                allergen_type TEXT,
                reaction TEXT,
                severity TEXT,
                onset_date TEXT,
                created_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """))
        conn.commit()

        for allergy in allergies:
            allergy['created_at'] = datetime.now().isoformat()
            try:
                conn.execute(text("""
                    INSERT INTO allergies
                    (patient_id, allergen, allergen_type, reaction, severity, onset_date, created_at)
                    VALUES
                    (:patient_id, :allergen, :allergen_type, :reaction, :severity, :onset_date, :created_at)
                """), allergy)
            except Exception as e:
                print(f"Warning: Could not insert allergy: {e}")

        conn.commit()
        print(f"✓ Seeded {len(allergies)} allergies")
    except Exception as e:
        print(f"Error seeding allergies: {e}")


def seed_appointments(conn):
    """Seed sample appointments"""
    print("Seeding appointments...")

    # Create appointments for next 2 weeks
    base_date = datetime.now()
    appointments = []

    # Demo appointment 1: Upcoming routine checkup
    appointments.append({
        "appointment_id": "appt_demo_001",
        "patient_id": "demo_patient_001",
        "doctor_id": "doctor_001",
        "doctor_name": "Dr. Emily Chen",
        "specialty": "family_medicine",
        "appointment_type": "routine_checkup",
        "date": (base_date + timedelta(days=7)).strftime("%Y-%m-%d"),
        "time": "10:00",
        "duration_minutes": 30,
        "reason": "Annual physical exam",
        "status": "scheduled"
    })

    # Demo appointment 2: Follow-up for diabetes
    appointments.append({
        "appointment_id": "appt_demo_002",
        "patient_id": "demo_patient_diabetes",
        "doctor_id": "doctor_003",
        "doctor_name": "Dr. James Lee",
        "specialty": "endocrinology",
        "appointment_type": "follow_up",
        "date": (base_date + timedelta(days=10)).strftime("%Y-%m-%d"),
        "time": "14:00",
        "duration_minutes": 45,
        "reason": "Diabetes management follow-up",
        "status": "scheduled"
    })

    # Demo appointment 3: Cardiology consultation
    appointments.append({
        "appointment_id": "appt_demo_003",
        "patient_id": "demo_patient_emergency",
        "doctor_id": "doctor_002",
        "doctor_name": "Dr. Sarah Martinez",
        "specialty": "cardiology",
        "appointment_type": "consultation",
        "date": (base_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        "time": "09:00",
        "duration_minutes": 60,
        "reason": "Chest pain evaluation",
        "status": "scheduled"
    })

    # Past appointments (for history)
    appointments.append({
        "appointment_id": "appt_demo_004",
        "patient_id": "demo_patient_001",
        "doctor_id": "doctor_001",
        "doctor_name": "Dr. Emily Chen",
        "specialty": "family_medicine",
        "appointment_type": "routine_checkup",
        "date": (base_date - timedelta(days=30)).strftime("%Y-%m-%d"),
        "time": "11:00",
        "duration_minutes": 30,
        "reason": "Flu symptoms",
        "status": "completed"
    })

    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                doctor_id TEXT,
                doctor_name TEXT,
                specialty TEXT,
                appointment_type TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                duration_minutes INTEGER,
                reason TEXT,
                status TEXT,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        """))
        conn.commit()

        for appt in appointments:
            appt['created_at'] = datetime.now().isoformat()
            try:
                conn.execute(text("""
                    INSERT OR REPLACE INTO appointments
                    (appointment_id, patient_id, doctor_id, doctor_name, specialty, appointment_type,
                     date, time, duration_minutes, reason, status, created_at)
                    VALUES
                    (:appointment_id, :patient_id, :doctor_id, :doctor_name, :specialty, :appointment_type,
                     :date, :time, :duration_minutes, :reason, :status, :created_at)
                """), appt)
            except Exception as e:
                print(f"Warning: Could not insert appointment: {e}")

        conn.commit()
        print(f"✓ Seeded {len(appointments)} appointments")
    except Exception as e:
        print(f"Error seeding appointments: {e}")


def seed_system_data(conn):
    """Seed system health and audit log tables"""
    print("Seeding system tables...")

    try:
        # System health table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS system_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                database_status TEXT,
                offline_mode TEXT,
                timestamp TEXT NOT NULL
            )
        """))

        # Audit logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                agent_name TEXT,
                request_type TEXT,
                confidence_score REAL,
                request_data TEXT,
                response_data TEXT,
                timestamp TEXT NOT NULL,
                session_id TEXT
            )
        """))

        conn.commit()
        print("✓ Seeded system tables")
    except Exception as e:
        print(f"Error seeding system tables: {e}")


def verify_seed_data(conn):
    """Verify that data was seeded successfully"""
    print("\n" + "="*70)
    print("VERIFYING SEED DATA")
    print("="*70)

    try:
        # Count patients
        result = conn.execute(text("SELECT COUNT(*) FROM patients"))
        patient_count = result.fetchone()[0]
        print(f"✓ Patients: {patient_count}")

        # Count appointments
        result = conn.execute(text("SELECT COUNT(*) FROM appointments"))
        appt_count = result.fetchone()[0]
        print(f"✓ Appointments: {appt_count}")

        # Count medications
        result = conn.execute(text("SELECT COUNT(*) FROM medications"))
        med_count = result.fetchone()[0]
        print(f"✓ Medications: {med_count}")

        # Count allergies
        result = conn.execute(text("SELECT COUNT(*) FROM allergies"))
        allergy_count = result.fetchone()[0]
        print(f"✓ Allergies: {allergy_count}")

        # Count chronic conditions
        result = conn.execute(text("SELECT COUNT(*) FROM chronic_conditions"))
        condition_count = result.fetchone()[0]
        print(f"✓ Chronic Conditions: {condition_count}")

        print("\n" + "="*70)
        print("✅ SEED DATA VERIFICATION COMPLETE")
        print("="*70)
        print("\nDemo data successfully populated!")
        print("You can now run the demo with realistic patient data.")
        print("\nNext steps:")
        print("1. Start backend: cd backend && python main.py")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Disconnect internet")
        print("4. Run demo using DEMO_SCRIPT.md")
        print()

    except Exception as e:
        print(f"Error verifying seed data: {e}")


def main():
    """Main seed data function"""
    print("="*70)
    print("HOSPITAL AI SYSTEM - DEMO DATA SEEDER")
    print("="*70)
    print()

    try:
        # Create database connection
        engine = get_database_connection()
        conn = engine.connect()

        print("✓ Connected to database\n")

        # Seed all data
        seed_system_data(conn)
        seed_patients(conn)
        seed_chronic_conditions(conn)
        seed_medications(conn)
        seed_allergies(conn)
        seed_appointments(conn)

        # Verify
        verify_seed_data(conn)

        conn.close()

    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        print("\nMake sure:")
        print("1. You're in the backend/ directory")
        print("2. The database directory exists: ../database/")
        print("3. You have write permissions")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
