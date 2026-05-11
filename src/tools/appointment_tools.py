"""
Appointment Tools - Functions for managing appointments.

This file works with the existing Pydantic model-based MockDatabase.
"""

import os
import sys
from typing import Dict, Any
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.database import MockDatabase

try:
    from src.models.database import get_database
except ImportError:
    get_database = None

from src.models.appointment import Appointment, AppointmentStatus

try:
    from src.models.appointment import AppointmentType
except ImportError:
    AppointmentType = None


# =============================================================================
# Helper Functions
# =============================================================================

def _get_db():
    """Use shared database if available, otherwise create MockDatabase."""
    if get_database:
        return get_database()
    return MockDatabase()


def _doctor_name(doctor) -> str:
    """Format doctor name from Doctor object."""
    if not doctor:
        return "Unknown Doctor"

    first = getattr(doctor, "first_name", "")
    last = getattr(doctor, "last_name", "")

    full_name = f"Dr. {first} {last}".strip()
    return full_name if full_name != "Dr." else "Unknown Doctor"


def _specialisation_value(doctor) -> str:
    """Return doctor specialisation as text."""
    spec = getattr(doctor, "specialisation", "Unknown")
    return spec.value if hasattr(spec, "value") else str(spec)


def _status_value(status) -> str:
    """Return appointment status as text."""
    return status.value if hasattr(status, "value") else str(status)


def _get_scheduled_status():
    """Get a valid scheduled/confirmed appointment status."""
    for name in ["SCHEDULED", "CONFIRMED", "BOOKED"]:
        if hasattr(AppointmentStatus, name):
            return getattr(AppointmentStatus, name)

    # Fallback to first enum value if available
    try:
        return list(AppointmentStatus)[0]
    except Exception:
        return "scheduled"


def _get_default_appointment_type():
    """Get a valid default appointment type."""
    if AppointmentType is None:
        return None

    for name in ["CONSULTATION", "GENERAL", "FOLLOW_UP", "CHECKUP"]:
        if hasattr(AppointmentType, name):
            return getattr(AppointmentType, name)

    # Fallback to first enum value
    try:
        return list(AppointmentType)[0]
    except Exception:
        return None


def _parse_time(time_text: str):
    """Parse time from common formats."""
    formats = ["%I:%M %p", "%H:%M", "%I:%M%p"]

    for fmt in formats:
        try:
            return datetime.strptime(time_text.strip(), fmt).time()
        except ValueError:
            continue

    raise ValueError("Invalid time format. Use format like 10:00 AM.")


def _appointment_to_dict(appointment, db=None) -> Dict[str, Any]:
    """Convert Appointment object or dict to dictionary."""
    if isinstance(appointment, dict):
        return appointment

    db = db or _get_db()
    doctor = db.get_doctor(appointment.doctor_id)

    start_time = getattr(appointment, "start_time", None)

    if start_time and hasattr(start_time, "strftime"):
        time_text = start_time.strftime("%I:%M %p")
    else:
        time_text = str(start_time) if start_time else "Unknown time"

    return {
        "appointment_id": appointment.appointment_id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "doctor_name": _doctor_name(doctor),
        "date": str(appointment.appointment_date),
        "time": time_text,
        "reason": getattr(appointment, "reason", "General consultation"),
        "status": _status_value(getattr(appointment, "status", "scheduled"))
    }


# =============================================================================
# Appointment Tool Functions
# =============================================================================

def get_available_slots(doctor_id: str, days_ahead: int = 7) -> Dict[str, Any]:
    """
    Get available appointment slots for a doctor.
    """
    db = _get_db()

    doctor = db.get_doctor(doctor_id)

    if not doctor:
        return {
            "success": False,
            "message": f"Doctor {doctor_id} not found",
            "slots": []
        }

    slots = []
    base_date = datetime.now()

    for day_offset in range(1, days_ahead + 1):
        slot_date = base_date + timedelta(days=day_offset)

        # Skip weekends
        if slot_date.weekday() >= 5:
            continue

        date_str = slot_date.strftime("%Y-%m-%d")

        available_times = [
            "09:00 AM",
            "10:00 AM",
            "11:00 AM",
            "02:00 PM",
            "03:00 PM",
            "04:00 PM"
        ]

        for slot_time in available_times:
            slots.append({
                "date": date_str,
                "time": slot_time,
                "doctor_id": doctor_id,
                "doctor_name": _doctor_name(doctor),
                "available": True
            })

    return {
        "success": True,
        "message": f"Found {len(slots)} available slot(s)",
        "slots": slots[:10]
    }


def book_appointment(
    patient_id: str,
    doctor_id: str,
    date: str,
    time: str,
    reason: str = "General consultation"
) -> Dict[str, Any]:
    """
    Book an appointment for a patient.
    """
    db = _get_db()

    patient = db.get_patient(patient_id)
    if not patient:
        return {
            "success": False,
            "message": f"Patient {patient_id} not found"
        }

    doctor = db.get_doctor(doctor_id)
    if not doctor:
        return {
            "success": False,
            "message": f"Doctor {doctor_id} not found"
        }

    try:
        appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "message": "Invalid date format. Use YYYY-MM-DD."
        }

    try:
        start_time = _parse_time(time)
    except ValueError as e:
        return {
            "success": False,
            "message": str(e)
        }

    end_time = (
        datetime.combine(appointment_date, start_time)
        + timedelta(minutes=30)
    ).time()

    appointment_id = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    status = _get_scheduled_status()
    appointment_type = _get_default_appointment_type()

    appointment_kwargs = {
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "start_time": start_time,
        "end_time": end_time,
        "reason": reason,
        "status": status
    }

    if appointment_type is not None:
        appointment_kwargs["appointment_type"] = appointment_type

    try:
        appointment = Appointment(**appointment_kwargs)
    except Exception as e:
        return {
            "success": False,
            "message": f"Could not create appointment model: {e}"
        }

    if hasattr(db, "create_appointment"):
        created = db.create_appointment(appointment)
    elif hasattr(db, "add_appointment"):
        created = db.add_appointment(appointment)
        if created is None:
            created = appointment
    else:
        return {
            "success": False,
            "message": "Database does not support creating appointments."
        }

    appointment_dict = _appointment_to_dict(created, db)

    return {
        "success": True,
        "message": f"Appointment booked with {_doctor_name(doctor)} on {date} at {time}",
        "appointment": appointment_dict
    }


def cancel_appointment(appointment_id: str) -> Dict[str, Any]:
    """
    Cancel an existing appointment.
    """
    db = _get_db()

    appointment = db.get_appointment(appointment_id)

    if not appointment:
        return {
            "success": False,
            "message": f"Appointment {appointment_id} not found"
        }

    if hasattr(AppointmentStatus, "CANCELLED"):
        appointment.status = AppointmentStatus.CANCELLED
    else:
        appointment.status = "cancelled"

    return {
        "success": True,
        "message": f"Appointment {appointment_id} has been cancelled"
    }


def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_time: str
) -> Dict[str, Any]:
    """
    Reschedule an existing appointment.
    """
    db = _get_db()

    appointment = db.get_appointment(appointment_id)

    if not appointment:
        return {
            "success": False,
            "message": f"Appointment {appointment_id} not found"
        }

    try:
        appointment_date = datetime.strptime(new_date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "message": "Invalid date format. Use YYYY-MM-DD."
        }

    try:
        start_time = _parse_time(new_time)
    except ValueError as e:
        return {
            "success": False,
            "message": str(e)
        }

    end_time = (
        datetime.combine(appointment_date, start_time)
        + timedelta(minutes=30)
    ).time()

    appointment.appointment_date = appointment_date
    appointment.start_time = start_time
    appointment.end_time = end_time

    return {
        "success": True,
        "message": f"Appointment rescheduled to {new_date} at {new_time}",
        "appointment": _appointment_to_dict(appointment, db)
    }


def get_patient_appointments(patient_id: str) -> Dict[str, Any]:
    """
    Get all appointments for a patient.
    """
    db = _get_db()

    appointments = db.get_patient_appointments(patient_id)
    appointment_list = [_appointment_to_dict(apt, db) for apt in appointments]

    return {
        "success": True,
        "message": f"Found {len(appointment_list)} appointment(s)",
        "appointments": appointment_list
    }


def find_doctors_by_specialisation(specialisation: str) -> Dict[str, Any]:
    """
    Find doctors by their specialisation.
    """
    db = _get_db()

    doctors = db.find_doctor_by_specialisation(specialisation)

    doctor_list = []

    for doc in doctors:
        doctor_list.append({
            "doctor_id": doc.doctor_id,
            "name": _doctor_name(doc),
            "specialisation": _specialisation_value(doc)
        })

    if doctor_list:
        return {
            "success": True,
            "message": f"Found {len(doctor_list)} doctor(s) in {specialisation}",
            "doctors": doctor_list
        }

    return {
        "success": False,
        "message": f"No doctors found for specialisation: {specialisation}",
        "doctors": []
    }


def get_all_doctors() -> Dict[str, Any]:
    """
    Get all doctors.
    """
    db = _get_db()

    doctors = db.get_all_doctors()
    doctor_list = []

    for doc in doctors:
        doctor_list.append({
            "doctor_id": doc.doctor_id,
            "name": _doctor_name(doc),
            "specialisation": _specialisation_value(doc)
        })

    return {
        "success": True,
        "message": f"Found {len(doctor_list)} doctor(s)",
        "doctors": doctor_list
    }


# =============================================================================
# Compatibility Aliases
# =============================================================================

def get_doctors_by_specialisation(specialisation: str) -> Dict[str, Any]:
    return find_doctors_by_specialisation(specialisation)


def find_doctor_by_specialisation(specialisation: str) -> Dict[str, Any]:
    return find_doctors_by_specialisation(specialisation)


def check_doctor_availability(doctor_id: str) -> Dict[str, Any]:
    return get_available_slots(doctor_id)


def get_doctor_availability(doctor_id: str, date_range=None) -> Dict[str, Any]:
    return get_available_slots(doctor_id)


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Appointment Tools Test")
    print("=" * 60)

    print("\n👨‍⚕️ Test 1: Find cardiologists")
    result = find_doctors_by_specialisation("Cardiology")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("doctors"):
        print(f"   Found: {result['doctors'][0]}")

    print("\n🕐 Test 2: Get available slots for D001")
    result = get_available_slots("D001")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("slots"):
        print(f"   First slot: {result['slots'][0]}")

    print("\n📝 Test 3: Book appointment")
    result = book_appointment(
        patient_id="P001",
        doctor_id="D001",
        date="2026-05-15",
        time="10:00 AM",
        reason="Follow-up checkup"
    )
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("appointment"):
        print(f"   Appointment: {result['appointment']}")

    print("\n📋 Test 4: Get patient appointments")
    result = get_patient_appointments("P001")
    print(f"   Success: {result['success']}")
    print(f"   Found: {len(result.get('appointments', []))} appointment(s)")

    for apt in result.get("appointments", []):
        print(
            f"   - {apt['date']} at {apt['time']} "
            f"with {apt['doctor_name']} ({apt['status']})"
        )

    print("\n" + "=" * 60)
    print("✅ Appointment tools tests complete!")
    print("=" * 60)