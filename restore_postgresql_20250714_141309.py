#!/usr/bin/env python3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

def restore_data_to_postgresql():
    print("🔄 Restoring data to PostgreSQL...")
    
    # Database connection using environment variables
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not found")
        return
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Initialize database with proper schema
    from database_manager import DatabaseManager
    db_manager = DatabaseManager()
    db_manager.init_db()
    
    # Sample data to restore
    appointments_data = [
      {
        "id": 17,
        "patient_id": 1,
        "appointment_date": "2025-07-09",
        "appointment_time": "15:00",
        "duration_minutes": 45,
        "treatment_type": "Consultation",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 18,
        "patient_id": 1,
        "appointment_date": "2025-07-10",
        "appointment_time": "14:00",
        "duration_minutes": 30,
        "treatment_type": "Cleaning",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 19,
        "patient_id": 1,
        "appointment_date": "2025-07-11",
        "appointment_time": "16:00",
        "duration_minutes": 60,
        "treatment_type": "Filling",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 20,
        "patient_id": 1,
        "appointment_date": "2025-07-12",
        "appointment_time": "10:00",
        "duration_minutes": 45,
        "treatment_type": "Consultation",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 21,
        "patient_id": 1,
        "appointment_date": "2025-07-13",
        "appointment_time": "11:00",
        "duration_minutes": 30,
        "treatment_type": "Cleaning",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 22,
        "patient_id": 1,
        "appointment_date": "2025-07-14",
        "appointment_time": "15:00",
        "duration_minutes": 60,
        "treatment_type": "Filling",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 23,
        "patient_id": 1,
        "appointment_date": "2025-07-15",
        "appointment_time": "09:00",
        "duration_minutes": 45,
        "treatment_type": "Consultation",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 24,
        "patient_id": 1,
        "appointment_date": "2025-07-16",
        "appointment_time": "13:00",
        "duration_minutes": 30,
        "treatment_type": "Cleaning",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 25,
        "patient_id": 1,
        "appointment_date": "2025-07-17",
        "appointment_time": "14:00",
        "duration_minutes": 60,
        "treatment_type": "Filling",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 26,
        "patient_id": 1,
        "appointment_date": "2025-07-18",
        "appointment_time": "10:00",
        "duration_minutes": 45,
        "treatment_type": "Consultation",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 27,
        "patient_id": 1,
        "appointment_date": "2025-07-19",
        "appointment_time": "16:00",
        "duration_minutes": 30,
        "treatment_type": "Cleaning",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 28,
        "patient_id": 1,
        "appointment_date": "2025-07-20",
        "appointment_time": "11:00",
        "duration_minutes": 60,
        "treatment_type": "Filling",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 29,
        "patient_id": 1,
        "appointment_date": "2025-07-21",
        "appointment_time": "15:00",
        "duration_minutes": 45,
        "treatment_type": "Consultation",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 30,
        "patient_id": 1,
        "appointment_date": "2025-07-22",
        "appointment_time": "09:00",
        "duration_minutes": 30,
        "treatment_type": "Cleaning",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 31,
        "patient_id": 1,
        "appointment_date": "2025-07-23",
        "appointment_time": "12:00",
        "duration_minutes": 60,
        "treatment_type": "Filling",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 32,
        "patient_id": 1,
        "appointment_date": "2025-07-24",
        "appointment_time": "14:00",
        "duration_minutes": 45,
        "treatment_type": "Consultation",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 33,
        "patient_id": 1,
        "appointment_date": "2025-07-25",
        "appointment_time": "10:00",
        "duration_minutes": 30,
        "treatment_type": "Cleaning",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 34,
        "patient_id": 1,
        "appointment_date": "2025-07-26",
        "appointment_time": "13:00",
        "duration_minutes": 60,
        "treatment_type": "Filling",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 35,
        "patient_id": 1,
        "appointment_date": "2025-07-27",
        "appointment_time": "16:00",
        "duration_minutes": 45,
        "treatment_type": "Consultation",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 36,
        "patient_id": 1,
        "appointment_date": "2025-07-28",
        "appointment_time": "11:00",
        "duration_minutes": 30,
        "treatment_type": "Cleaning",
        "status": "scheduled",
        "doctor": "Dr.",
        "room": None,
        "notes": "",
        "treatment_plan_id": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      }
    ]

    patients_data = [
      {
        "id": 1,
        "first_name": "Ahmed",
        "last_name": "Bennani",
        "date_of_birth": "1985-03-15",
        "gender": "M",
        "phone": "+212 6 12 34 56 78",
        "email": "ahmed.bennani@email.com",
        "address": "123 Rue Mohammed V, Casablanca",
        "emergency_contact": "Fatima Bennani - +212 6 87 65 43 21",
        "medical_history": "Diabetes Type 2, Hypertension",
        "allergies": "Penicillin",
        "insurance_info": "CNSS - 123456789",
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      }
    ]

    treatment_plans_data = [
      {
        "id": 1,
        "patient_id": 1,
        "title": "Comprehensive Dental Care Plan",
        "description": "Complete dental restoration including cleaning, fillings, and preventive care",
        "total_cost": 2500.00,
        "status": "active",
        "created_date": "2025-07-09",
        "start_date": "2025-07-09",
        "end_date": "2025-07-28",
        "approved_date": "2025-07-09",
        "rejected_date": None,
        "rejection_reason": None,
        "notes": None,
        "created_at": "2025-07-09T15:02:34.076065",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 2,
        "patient_id": 1,
        "title": "Emergency Dental Treatment",
        "description": "Immediate care for dental pain and infection",
        "total_cost": 800.00,
        "status": "active",
        "created_date": "2025-07-10",
        "start_date": "2025-07-10",
        "end_date": "2025-07-15",
        "approved_date": "2025-07-10",
        "rejected_date": None,
        "rejection_reason": None,
        "notes": None,
        "created_at": "2025-07-10T10:30:00.000000",
        "updated_at": "2025-07-11 11:37:24"
      },
      {
        "id": 3,
        "patient_id": 1,
        "title": "Preventive Care Package",
        "description": "Regular cleanings and check-ups to maintain oral health",
        "total_cost": 600.00,
        "status": "active",
        "created_date": "2025-07-11",
        "start_date": "2025-07-11",
        "end_date": "2025-07-25",
        "approved_date": "2025-07-11",
        "rejected_date": None,
        "rejection_reason": None,
        "notes": None,
        "created_at": "2025-07-11T14:15:00.000000",
        "updated_at": "2025-07-11 11:37:24"
      }
    ]

    # Insert patients
    print("📋 Restoring patients...")
    for patient in patients_data:
        try:
            cursor.execute("""
                INSERT INTO patients (id, first_name, last_name, date_of_birth, gender, phone, email, address, emergency_contact, medical_history, allergies, insurance_info, created_at, updated_at)
                VALUES (%(id)s, %(first_name)s, %(last_name)s, %(date_of_birth)s, %(gender)s, %(phone)s, %(email)s, %(address)s, %(emergency_contact)s, %(medical_history)s, %(allergies)s, %(insurance_info)s, %(created_at)s, %(updated_at)s)
                ON CONFLICT (id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    date_of_birth = EXCLUDED.date_of_birth,
                    gender = EXCLUDED.gender,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email,
                    address = EXCLUDED.address,
                    emergency_contact = EXCLUDED.emergency_contact,
                    medical_history = EXCLUDED.medical_history,
                    allergies = EXCLUDED.allergies,
                    insurance_info = EXCLUDED.insurance_info,
                    updated_at = EXCLUDED.updated_at
            """, patient)
            print(f"✅ Patient {patient['first_name']} {patient['last_name']} restored")
        except Exception as e:
            print(f"❌ Error restoring patient {patient.get('first_name', 'Unknown')}: {e}")

    # Insert treatment plans
    print("📋 Restoring treatment plans...")
    for plan in treatment_plans_data:
        try:
            cursor.execute("""
                INSERT INTO treatment_plans (id, patient_id, title, description, total_cost, status, created_date, start_date, end_date, approved_date, rejected_date, rejection_reason, notes, created_at, updated_at)
                VALUES (%(id)s, %(patient_id)s, %(title)s, %(description)s, %(total_cost)s, %(status)s, %(created_date)s, %(start_date)s, %(end_date)s, %(approved_date)s, %(rejected_date)s, %(rejection_reason)s, %(notes)s, %(created_at)s, %(updated_at)s)
                ON CONFLICT (id) DO UPDATE SET
                    patient_id = EXCLUDED.patient_id,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    total_cost = EXCLUDED.total_cost,
                    status = EXCLUDED.status,
                    created_date = EXCLUDED.created_date,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    approved_date = EXCLUDED.approved_date,
                    rejected_date = EXCLUDED.rejected_date,
                    rejection_reason = EXCLUDED.rejection_reason,
                    notes = EXCLUDED.notes,
                    updated_at = EXCLUDED.updated_at
            """, plan)
            print(f"✅ Treatment plan '{plan['title']}' restored")
        except Exception as e:
            print(f"❌ Error restoring treatment plan {plan.get('title', 'Unknown')}: {e}")

    # Insert appointments
    print("📋 Restoring appointments...")
    for appointment in appointments_data:
        try:
            cursor.execute("""
                INSERT INTO appointments (id, patient_id, appointment_date, appointment_time, duration_minutes, treatment_type, status, doctor, room, notes, treatment_plan_id, created_at, updated_at)
                VALUES (%(id)s, %(patient_id)s, %(appointment_date)s, %(appointment_time)s, %(duration_minutes)s, %(treatment_type)s, %(status)s, %(doctor)s, %(room)s, %(notes)s, %(treatment_plan_id)s, %(created_at)s, %(updated_at)s)
                ON CONFLICT (id) DO UPDATE SET
                    patient_id = EXCLUDED.patient_id,
                    appointment_date = EXCLUDED.appointment_date,
                    appointment_time = EXCLUDED.appointment_time,
                    duration_minutes = EXCLUDED.duration_minutes,
                    treatment_type = EXCLUDED.treatment_type,
                    status = EXCLUDED.status,
                    doctor = EXCLUDED.doctor,
                    room = EXCLUDED.room,
                    notes = EXCLUDED.notes,
                    treatment_plan_id = EXCLUDED.treatment_plan_id,
                    updated_at = EXCLUDED.updated_at
            """, appointment)
            print(f"✅ Appointment {appointment['id']} restored")
        except Exception as e:
            print(f"❌ Error restoring appointment {appointment.get('id', 'Unknown')}: {e}")

    # Update sequences
    print("🔄 Updating sequences...")
    try:
        cursor.execute("SELECT setval('patients_id_seq', (SELECT MAX(id) FROM patients))")
        cursor.execute("SELECT setval('appointments_id_seq', (SELECT MAX(id) FROM appointments))")
        cursor.execute("SELECT setval('treatment_plans_id_seq', (SELECT MAX(id) FROM treatment_plans))")
        print("✅ Sequences updated")
    except Exception as e:
        print(f"❌ Error updating sequences: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Data restoration completed successfully!")
    print(f"📊 Restored: {len(patients_data)} patients, {len(appointments_data)} appointments, {len(treatment_plans_data)} treatment plans")

if __name__ == "__main__":
    restore_data_to_postgresql()
