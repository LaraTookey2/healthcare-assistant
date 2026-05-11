"""
Mock Database - Provides sample data for testing

This module creates a mock database with sample patients, doctors,
appointments, and medical records for development and testing.

Based on: Agentic Healthcare Assistant Project Roadmap
Phase 1, Week 2: Mock EHR/Patient Database
"""

from typing import Dict, List, Optional
from datetime import date, time, datetime, timedelta
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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

# =============================================================================
# MOCK DATABASE CLASS
# =============================================================================

class MockDatabase:
    """
    Mock database for healthcare assistant testing.
    
    Provides in-memory storage for:
    - Patients
    - Doctors
    - Appointments
    - Medical Records
    """
    
    def __init__(self):
        """Initialise the mock database with sample data."""
        self.patients: Dict[str, Patient] = {}
        self.doctors: Dict[str, Doctor] = {}
        self.appointments: Dict[str, Appointment] = {}
        self.medical_records: Dict[str, MedicalRecord] = {}
        
        # Populate with sample data
        self._create_sample_doctors()
        self._create_sample_patients()
        self._create_sample_appointments()
        self._create_sample_records()
    
    # -------------------------------------------------------------------------
    # Sample Data Creation
    # -------------------------------------------------------------------------
    
    def _create_sample_doctors(self):
        """Create sample doctors."""
        doctors = [
            Doctor(
                doctor_id="D001",
                first_name="Sarah",
                last_name="Smith",
                specialisation=Specialisation.CARDIOLOGY,
                qualifications=["MD", "FRACP", "PhD"],
                email="s.smith@hospital.nz",
                phone="+64 9 123 4001",
                room_number="A204",
                weekly_schedule=[
                    DailySchedule(day=DayOfWeek.MONDAY, start_time=time(9, 0), end_time=time(16, 0)),
                    DailySchedule(day=DayOfWeek.WEDNESDAY, start_time=time(9, 0), end_time=time(16, 0)),
                    DailySchedule(day=DayOfWeek.FRIDAY, start_time=time(9, 0), end_time=time(14, 0)),
                ]
            ),
            Doctor(
                doctor_id="D002",
                first_name="Michael",
                last_name="Johnson",
                specialisation=Specialisation.GENERAL_PRACTICE,
                qualifications=["MB ChB", "FRNZCGP"],
                email="m.johnson@hospital.nz",
                phone="+64 9 123 4002",
                room_number="B105",
                weekly_schedule=[
                    DailySchedule(day=DayOfWeek.MONDAY, start_time=time(8, 0), end_time=time(17, 0)),
                    DailySchedule(day=DayOfWeek.TUESDAY, start_time=time(8, 0), end_time=time(17, 0)),
                    DailySchedule(day=DayOfWeek.WEDNESDAY, start_time=time(8, 0), end_time=time(17, 0)),
                    DailySchedule(day=DayOfWeek.THURSDAY, start_time=time(8, 0), end_time=time(17, 0)),
                    DailySchedule(day=DayOfWeek.FRIDAY, start_time=time(8, 0), end_time=time(15, 0)),
                ]
            ),
            Doctor(
                doctor_id="D003",
                first_name="Priya",
                last_name="Patel",
                specialisation=Specialisation.DERMATOLOGY,
                qualifications=["MD", "FACD"],
                email="p.patel@hospital.nz",
                phone="+64 9 123 4003",
                room_number="C301",
                weekly_schedule=[
                    DailySchedule(day=DayOfWeek.TUESDAY, start_time=time(10, 0), end_time=time(15, 0)),
                    DailySchedule(day=DayOfWeek.THURSDAY, start_time=time(10, 0), end_time=time(15, 0)),
                ]
            ),
            Doctor(
                doctor_id="D004",
                first_name="James",
                last_name="Williams",
                specialisation=Specialisation.NEUROLOGY,
                qualifications=["MD", "FRACP"],
                email="j.williams@hospital.nz",
                phone="+64 9 123 4004",
                room_number="A310",
                weekly_schedule=[
                    DailySchedule(day=DayOfWeek.WEDNESDAY, start_time=time(9, 0), end_time=time(14, 0)),
                    DailySchedule(day=DayOfWeek.FRIDAY, start_time=time(9, 0), end_time=time(14, 0)),
                ]
            ),
            Doctor(
                doctor_id="D005",
                first_name="Emma",
                last_name="Chen",
                specialisation=Specialisation.ENDOCRINOLOGY,
                qualifications=["MD", "PhD", "FRACP"],
                email="e.chen@hospital.nz",
                phone="+64 9 123 4005",
                room_number="B208",
                weekly_schedule=[
                    DailySchedule(day=DayOfWeek.MONDAY, start_time=time(9, 0), end_time=time(15, 0)),
                    DailySchedule(day=DayOfWeek.TUESDAY, start_time=time(9, 0), end_time=time(15, 0)),
                    DailySchedule(day=DayOfWeek.THURSDAY, start_time=time(9, 0), end_time=time(15, 0)),
                ]
            ),
        ]
        
        for doctor in doctors:
            self.doctors[doctor.doctor_id] = doctor
    
    def _create_sample_patients(self):
        """Create sample patients."""
        patients = [
            Patient(
                patient_id="P001",
                first_name="Sarah",
                last_name="Johnson",
                date_of_birth=date(1985, 3, 15),
                gender=Gender.FEMALE,
                blood_type=BloodType.O_POSITIVE,
                contact=ContactInfo(
                    phone="+64 21 123 4567",
                    email="sarah.johnson@email.com",
                    address="123 Queen Street, Auckland 1010",
                    emergency_contact_name="Jane Smith",
                    emergency_contact_phone="+64 21 987 6543"
                ),
                allergies=["Penicillin", "Peanuts"],
                chronic_conditions=["Type 2 Diabetes", "Hypertension"],
                current_medications=["Metformin 500mg", "Lisinopril 10mg"],
                medical_alerts=[
                    MedicalAlert(
                        alert_type="allergy",
                        description="Severe penicillin allergy - anaphylaxis risk",
                        severity="critical"
                    )
                ],
                preferred_doctor_id="D002",
                preferred_appointment_time="morning"
            ),
            Patient(
                patient_id="P002",
                first_name="Sarah",
                last_name="Williams",
                date_of_birth=date(1990, 7, 22),
                gender=Gender.FEMALE,
                blood_type=BloodType.A_POSITIVE,
                contact=ContactInfo(
                    phone="+64 22 234 5678",
                    email="sarah.williams@email.com",
                    address="456 Victoria Street, Wellington 6011"
                ),
                allergies=["Latex"],
                chronic_conditions=["Asthma"],
                current_medications=["Ventolin inhaler PRN"],
                preferred_doctor_id="D001",
                preferred_appointment_time="afternoon"
            ),
            Patient(
                patient_id="P003",
                first_name="David",
                last_name="Brown",
                date_of_birth=date(1978, 11, 8),
                gender=Gender.MALE,
                blood_type=BloodType.B_NEGATIVE,
                contact=ContactInfo(
                    phone="+64 27 345 6789",
                    email="david.brown@email.com",
                    address="789 Colombo Street, Christchurch 8011"
                ),
                allergies=[],
                chronic_conditions=["Coronary Artery Disease", "Hyperlipidemia"],
                current_medications=["Aspirin 100mg", "Atorvastatin 40mg", "Metoprolol 50mg"],
                preferred_doctor_id="D001",
                preferred_appointment_time="morning"
            ),
        ]
        
        for patient in patients:
            self.patients[patient.patient_id] = patient
    
    def _create_sample_appointments(self):
        """Create sample appointments."""
        # Get next Monday
        today = date.today()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        
        appointments = [
            Appointment(
                appointment_id="A001",
                patient_id="P001",
                doctor_id="D002",
                appointment_date=next_monday,
                start_time=time(9, 0),
                end_time=time(9, 30),
                appointment_type=AppointmentType.FOLLOW_UP,
                status=AppointmentStatus.CONFIRMED,
                reason="Diabetes management follow-up"
            ),
            Appointment(
                appointment_id="A002",
                patient_id="P003",
                doctor_id="D001",
                appointment_date=next_monday,
                start_time=time(10, 0),
                end_time=time(10, 30),
                appointment_type=AppointmentType.CONSULTATION,
                status=AppointmentStatus.SCHEDULED,
                reason="Cardiac assessment"
            ),
            Appointment(
                appointment_id="A003",
                patient_id="P002",
                doctor_id="D003",
                appointment_date=next_monday + timedelta(days=1),  # Tuesday
                start_time=time(11, 0),
                end_time=time(11, 30),
                appointment_type=AppointmentType.CONSULTATION,
                status=AppointmentStatus.SCHEDULED,
                reason="Skin rash evaluation"
            ),
        ]
        
        for appt in appointments:
            self.appointments[appt.appointment_id] = appt
    
    def _create_sample_records(self):
        """Create sample medical records."""
        records = [
            MedicalRecord(
                record_id="R001",
                patient_id="P001",
                record_type=RecordType.CONSULTATION,
                encounter_date=date(2026, 4, 15),
                doctor_id="D002",
                department="General Practice",
                chief_complaint="Routine diabetes check-up",
                assessment="Type 2 Diabetes - well controlled on current medication. HbA1c within target.",
                plan="Continue Metformin 500mg. Recheck HbA1c in 3 months.",
                diagnoses=[
                    Diagnosis(
                        diagnosis_id="DX001",
                        code="E11.9",
                        name="Type 2 Diabetes Mellitus",
                        diagnosed_date=date(2020, 5, 10),
                        diagnosed_by="D002",
                        is_chronic=True,
                        is_active=True
                    )
                ],
                medications=[
                    Medication(
                        medication_id="MED001",
                        name="Metformin",
                        dosage="500mg",
                        frequency="twice daily",
                        prescribed_date=date(2020, 5, 10),
                        prescribed_by="D002",
                        start_date=date(2020, 5, 10),
                        reason="Type 2 Diabetes management"
                    )
                ],
                lab_results=[
                    LabResult(
                        result_id="LAB001",
                        test_name="HbA1c",
                        value="6.2",
                        unit="%",
                        reference_range="< 7.0",
                        status=LabResultStatus.NORMAL,
                        test_date=date(2026, 4, 14),
                        result_date=date(2026, 4, 15)
                    ),
                    LabResult(
                        result_id="LAB002",
                        test_name="Fasting Glucose",
                        value="6.8",
                        unit="mmol/L",
                        reference_range="3.9 - 6.1",
                        status=LabResultStatus.ABNORMAL_HIGH,
                        test_date=date(2026, 4, 14),
                        result_date=date(2026, 4, 15)
                    )
                ],
                vital_signs=VitalSigns(
                    blood_pressure_systolic=128,
                    blood_pressure_diastolic=82,
                    heart_rate=76,
                    weight=82.5,
                    height=178
                ),
                follow_up_instructions="Return in 3 months for HbA1c recheck."
            ),
            MedicalRecord(
                record_id="R002",
                patient_id="P003",
                record_type=RecordType.CONSULTATION,
                encounter_date=date(2026, 4, 10),
                doctor_id="D001",
                department="Cardiology",
                chief_complaint="Chest discomfort with exertion",
                assessment="Stable angina. Good response to current medications.",
                plan="Continue current therapy. Stress test in 2 weeks.",
                diagnoses=[
                    Diagnosis(
                        diagnosis_id="DX003",
                        code="I20.9",
                        name="Angina Pectoris",
                        diagnosed_date=date(2024, 8, 15),
                        diagnosed_by="D001",
                        is_chronic=True,
                        is_active=True
                    ),
                    Diagnosis(
                        diagnosis_id="DX004",
                        code="I25.10",
                        name="Coronary Artery Disease",
                        diagnosed_date=date(2024, 8, 15),
                        diagnosed_by="D001",
                        is_chronic=True,
                        is_active=True
                    )
                ],
                vital_signs=VitalSigns(
                    blood_pressure_systolic=142,
                    blood_pressure_diastolic=88,
                    heart_rate=68,
                    oxygen_saturation=97
                )
            ),
        ]
        
        for record in records:
            self.medical_records[record.record_id] = record
    
    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------
    
    # Patient Methods
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        return self.patients.get(patient_id)
    
    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        return list(self.patients.values())
    
    def search_patients(self, name: str) -> List[Patient]:
        """Search patients by name."""
        name_lower = name.lower()
        return [
            p for p in self.patients.values()
            if name_lower in p.first_name.lower() or name_lower in p.last_name.lower()
        ]
    
    # Doctor Methods
    def get_doctor(self, doctor_id: str) -> Optional[Doctor]:
        """Get doctor by ID."""
        return self.doctors.get(doctor_id)
    
    def get_all_doctors(self) -> List[Doctor]:
        """Get all doctors."""
        return list(self.doctors.values())
    
    def get_doctors_by_specialisation(self, spec: Specialisation) -> List[Doctor]:
        """Get doctors by specialisation."""
        return [d for d in self.doctors.values() if d.specialisation == spec]
    
    def find_doctor_by_specialisation(self, specialisation_name: str) -> List[Doctor]:
        """Find doctors by specialisation name (fuzzy match)."""
        spec_lower = specialisation_name.lower()
        return [
            d for d in self.doctors.values()
            if spec_lower in d.specialisation.value.lower()
        ]
    
    # Appointment Methods
    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get appointment by ID."""
        return self.appointments.get(appointment_id)
    
    def get_patient_appointments(self, patient_id: str) -> List[Appointment]:
        """Get all appointments for a patient."""
        return [a for a in self.appointments.values() if a.patient_id == patient_id]
    
    def get_doctor_appointments(self, doctor_id: str, date_filter: Optional[date] = None) -> List[Appointment]:
        """Get all appointments for a doctor, optionally filtered by date."""
        appts = [a for a in self.appointments.values() if a.doctor_id == doctor_id]
        if date_filter:
            appts = [a for a in appts if a.appointment_date == date_filter]
        return appts
    
    def get_upcoming_appointments(self, patient_id: str) -> List[Appointment]:
        """Get upcoming appointments for a patient."""
        today = date.today()
        return [
            a for a in self.appointments.values()
            if a.patient_id == patient_id and a.appointment_date >= today
            and a.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED]
        ]
    
    def create_appointment(self, appointment: Appointment) -> Appointment:
        """Create a new appointment."""
        self.appointments[appointment.appointment_id] = appointment
        return appointment
    
    # Medical Record Methods
    def get_medical_record(self, record_id: str) -> Optional[MedicalRecord]:
        """Get medical record by ID."""
        return self.medical_records.get(record_id)
    
    def get_patient_records(self, patient_id: str) -> List[MedicalRecord]:
        """Get all medical records for a patient."""
        return [r for r in self.medical_records.values() if r.patient_id == patient_id]
    
    def get_patient_diagnoses(self, patient_id: str) -> List[Diagnosis]:
        """Get all diagnoses for a patient across all records."""
        diagnoses = []
        for record in self.get_patient_records(patient_id):
            diagnoses.extend(record.diagnoses)
        return diagnoses
    
    def get_patient_medications(self, patient_id: str) -> List[Medication]:
        """Get all medications for a patient across all records."""
        medications = []
        for record in self.get_patient_records(patient_id):
            medications.extend(record.medications)
        return medications
    
    def get_patient_lab_results(self, patient_id: str) -> List[LabResult]:
        """Get all lab results for a patient across all records."""
        results = []
        for record in self.get_patient_records(patient_id):
            results.extend(record.lab_results)
        return results


# =============================================================================
# GLOBAL DATABASE INSTANCE
# =============================================================================

_database: Optional[MockDatabase] = None

def get_database() -> MockDatabase:
    """
    Get the global database instance.
    
    Returns:
        MockDatabase: The singleton database instance
    """
    global _database
    if _database is None:
        _database = MockDatabase()
    return _database


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🗄️ MOCK DATABASE TEST")
    print("=" * 60)
    
    db = get_database()
    
    # Test patients
    print(f"\n👥 Patients: {len(db.get_all_patients())}")
    for p in db.get_all_patients():
        print(f"   • {p.full_name} ({p.patient_id}) - Age: {p.age}")
    
    # Test doctors
    print(f"\n👨‍⚕️ Doctors: {len(db.get_all_doctors())}")
    for d in db.get_all_doctors():
        print(f"   • {d.full_name} - {d.specialisation.value}")
    
    # Test finding cardiologist
    print(f"\n🔍 Searching for cardiologist...")
    cardiologists = db.find_doctor_by_specialisation("cardio")
    for d in cardiologists:
        print(f"   • Found: {d.full_name}")
    
    # Test appointments
    print(f"\n📅 Appointments: {len(db.appointments)}")
    for a in db.appointments.values():
        patient = db.get_patient(a.patient_id)
        doctor = db.get_doctor(a.doctor_id)
        print(f"   • {patient.full_name} with {doctor.full_name} on {a.appointment_date}")
    
    # Test patient records
    print(f"\n📋 Medical Records for P001:")
    records = db.get_patient_records("P001")
    for r in records:
        print(f"   • {r.record_type.value} on {r.encounter_date}")
    
    # Test patient summary
    print(f"\n📊 Patient P001 Summary:")
    patient = db.get_patient("P001")
    print(patient.to_summary())
    
    print("\n" + "=" * 60)
    print("✅ Mock database test complete!")
    print("=" * 60)