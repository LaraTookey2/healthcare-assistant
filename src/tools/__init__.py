 
"""
Tools Package - Agent tools for the Healthcare Assistant

This package contains tools for:
- Appointment management (booking, cancellation, availability)
- Medical records retrieval (patient profiles, history, labs)
- Medical information search (coming soon)
"""

from src.tools.appointment_tools import (
    find_doctors_by_specialisation,
    get_all_doctors,
    get_doctor_availability,
    book_appointment,
    get_patient_appointments,
    cancel_appointment
)

from src.tools.records_tools import (
    get_patient_profile,
    search_patients,
    get_all_patients,
    get_medical_history,
    get_patient_diagnoses,
    get_patient_medications,
    get_patient_lab_results,
    get_patient_summary
)

__all__ = [
    # Appointment Tools
    "find_doctors_by_specialisation",
    "get_all_doctors",
    "get_doctor_availability",
    "book_appointment",
    "get_patient_appointments",
    "cancel_appointment",
    # Records Tools
    "get_patient_profile",
    "search_patients",
    "get_all_patients",
    "get_medical_history",
    "get_patient_diagnoses",
    "get_patient_medications",
    "get_patient_lab_results",
    "get_patient_summary",
]