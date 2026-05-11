 
"""
Models Package - Data models for the Healthcare Assistant

This package contains Pydantic models for:
- Patient data
- Appointments and scheduling
- Medical records
- Mock database for testing
"""

from src.models.patient import (
    Patient,
    ContactInfo,
    MedicalAlert,
    Insurance,
    Gender,
    BloodType
)

from src.models.appointment import (
    Doctor,
    Appointment,
    TimeSlot,
    DailySchedule,
    Specialisation,
    DayOfWeek,
    AppointmentType,
    AppointmentStatus
)

from src.models.medical_record import (
    MedicalRecord,
    Diagnosis,
    Medication,
    LabResult,
    VitalSigns,
    RecordType,
    RecordStatus,
    LabResultStatus,
    MedicationStatus
)

__all__ = [
    # Patient
    "Patient",
    "ContactInfo",
    "MedicalAlert",
    "Insurance",
    "Gender",
    "BloodType",
    # Appointment
    "Doctor",
    "Appointment",
    "TimeSlot",
    "DailySchedule",
    "Specialisation",
    "DayOfWeek",
    "AppointmentType",
    "AppointmentStatus",
    # Medical Record
    "MedicalRecord",
    "Diagnosis",
    "Medication",
    "LabResult",
    "VitalSigns",
    "RecordType",
    "RecordStatus",
    "LabResultStatus",
    "MedicationStatus",
    # Database
]