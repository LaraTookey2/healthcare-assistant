"""
Records Tools - Tools for managing patient medical records

These tools allow the Records Agent to:
- Retrieve patient profiles
- Get medical history
- View diagnoses, medications, and lab results
- Add new medical records

Based on: Agentic Healthcare Assistant Project Roadmap [2]
Phase 2: EHR Integration Tools
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.database import get_database
from src.models.patient import Patient
from src.models.medical_record import (
    MedicalRecord, Diagnosis, Medication, LabResult,
    RecordType, LabResultStatus
)


# =============================================================================
# TOOL RESPONSE MODEL
# =============================================================================

class ToolResponse(BaseModel):
    """Standard response from tools."""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


# =============================================================================
# PATIENT PROFILE TOOLS
# =============================================================================

def get_patient_profile(patient_id: str) -> ToolResponse:
    """
    Get complete patient profile including demographics, allergies, and conditions.
    
    Args:
        patient_id: The patient's ID (e.g., "P001")
    
    Returns:
        ToolResponse with patient profile data
    """
    db = get_database()
    patient = db.get_patient(patient_id)
    
    if not patient:
        return ToolResponse(
            success=False,
            message=f"Patient with ID '{patient_id}' not found",
            data=None
        )
    
    # Get critical alerts
    critical_alerts = [
        {"type": alert.alert_type, "description": alert.description, "severity": alert.severity}
        for alert in patient.get_critical_alerts()
    ]
    
    profile = {
        "patient_id": patient.patient_id,
        "name": patient.full_name,
        "age": patient.age,
        "date_of_birth": patient.date_of_birth.strftime("%d %B %Y"),
        "gender": patient.gender.value,
        "blood_type": patient.blood_type.value,
        "contact": {
            "phone": patient.contact.phone,
            "email": patient.contact.email,
            "address": patient.contact.address
        },
        "emergency_contact": {
            "name": patient.contact.emergency_contact_name,
            "phone": patient.contact.emergency_contact_phone
        },
        "allergies": patient.allergies,
        "chronic_conditions": patient.chronic_conditions,
        "current_medications": patient.current_medications,
        "critical_alerts": critical_alerts,
        "preferences": {
            "preferred_doctor": patient.preferred_doctor_id,
            "preferred_time": patient.preferred_appointment_time,
            "contact_method": patient.preferred_contact_method
        }
    }
    
    return ToolResponse(
        success=True,
        message=f"Retrieved profile for {patient.full_name}",
        data=profile
    )


def search_patients(name: str) -> ToolResponse:
    """
    Search for patients by name.
    
    Args:
        name: Patient name to search for (first or last name)
    
    Returns:
        ToolResponse with matching patients
    """
    db = get_database()
    patients = db.search_patients(name)
    
    if not patients:
        return ToolResponse(
            success=False,
            message=f"No patients found matching '{name}'",
            data=None
        )
    
    patient_list = [
        {
            "patient_id": p.patient_id,
            "name": p.full_name,
            "age": p.age,
            "phone": p.contact.phone
        }
        for p in patients
    ]
    
    return ToolResponse(
        success=True,
        message=f"Found {len(patients)} patient(s) matching '{name}'",
        data={"patients": patient_list}
    )


def get_all_patients() -> ToolResponse:
    """
    Get a list of all patients in the system.
    
    Returns:
        ToolResponse with all patients
    """
    db = get_database()
    patients = db.get_all_patients()
    
    patient_list = [
        {
            "patient_id": p.patient_id,
            "name": p.full_name,
            "age": p.age,
            "conditions": p.chronic_conditions[:2] if p.chronic_conditions else []
        }
        for p in patients
    ]
    
    return ToolResponse(
        success=True,
        message=f"Found {len(patients)} patients",
        data={"patients": patient_list}
    )


# =============================================================================
# MEDICAL HISTORY TOOLS
# =============================================================================

def get_medical_history(patient_id: str, limit: int = 5) -> ToolResponse:
    """
    Get patient's medical history (recent records).
    
    Args:
        patient_id: The patient's ID
        limit: Maximum number of records to return
    
    Returns:
        ToolResponse with medical history
    """
    db = get_database()
    
    patient = db.get_patient(patient_id)
    if not patient:
        return ToolResponse(
            success=False,
            message=f"Patient with ID '{patient_id}' not found",
            data=None
        )
    
    records = db.get_patient_records(patient_id)
    
    if not records:
        return ToolResponse(
            success=True,
            message=f"No medical records found for {patient.full_name}",
            data={"records": []}
        )
    
    # Sort by date, most recent first
    records = sorted(records, key=lambda r: r.encounter_date, reverse=True)[:limit]
    
    record_list = []
    for record in records:
        doctor = db.get_doctor(record.doctor_id)
        record_list.append({
            "record_id": record.record_id,
            "date": record.encounter_date.strftime("%d %B %Y"),
            "type": record.record_type.value,
            "doctor": doctor.full_name if doctor else "Unknown",
            "chief_complaint": record.chief_complaint,
            "assessment": record.assessment,
            "plan": record.plan
        })
    
    return ToolResponse(
        success=True,
        message=f"Retrieved {len(record_list)} medical record(s) for {patient.full_name}",
        data={
            "patient": patient.full_name,
            "records": record_list
        }
    )


def get_patient_diagnoses(patient_id: str, active_only: bool = True) -> ToolResponse:
    """
    Get all diagnoses for a patient.
    
    Args:
        patient_id: The patient's ID
        active_only: If True, only return active diagnoses
    
    Returns:
        ToolResponse with diagnoses list
    """
    db = get_database()
    
    patient = db.get_patient(patient_id)
    if not patient:
        return ToolResponse(
            success=False,
            message=f"Patient with ID '{patient_id}' not found",
            data=None
        )
    
    diagnoses = db.get_patient_diagnoses(patient_id)
    
    if active_only:
        diagnoses = [d for d in diagnoses if d.is_active]
    
    if not diagnoses:
        return ToolResponse(
            success=True,
            message=f"No {'active ' if active_only else ''}diagnoses found for {patient.full_name}",
            data={"diagnoses": []}
        )
    
    diagnosis_list = [
        {
            "diagnosis_id": d.diagnosis_id,
            "name": d.name,
            "code": d.code,
            "diagnosed_date": d.diagnosed_date.strftime("%d %B %Y"),
            "is_chronic": d.is_chronic,
            "is_active": d.is_active,
            "summary": d.to_summary()
        }
        for d in diagnoses
    ]
    
    return ToolResponse(
        success=True,
        message=f"Found {len(diagnosis_list)} {'active ' if active_only else ''}diagnosis(es) for {patient.full_name}",
        data={
            "patient": patient.full_name,
            "diagnoses": diagnosis_list
        }
    )


def get_patient_medications(patient_id: str, active_only: bool = True) -> ToolResponse:
    """
    Get all medications for a patient.
    
    Args:
        patient_id: The patient's ID
        active_only: If True, only return active medications
    
    Returns:
        ToolResponse with medications list
    """
    db = get_database()
    
    patient = db.get_patient(patient_id)
    if not patient:
        return ToolResponse(
            success=False,
            message=f"Patient with ID '{patient_id}' not found",
            data=None
        )
    
    medications = db.get_patient_medications(patient_id)
    
    if active_only:
        medications = [m for m in medications if m.is_active]
    
    if not medications:
        return ToolResponse(
            success=True,
            message=f"No {'active ' if active_only else ''}medications found for {patient.full_name}",
            data={"medications": []}
        )
    
    medication_list = [
        {
            "medication_id": m.medication_id,
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "route": m.route,
            "reason": m.reason,
            "prescribed_date": m.prescribed_date.strftime("%d %B %Y"),
            "status": m.status.value,
            "summary": m.to_summary()
        }
        for m in medications
    ]
    
    return ToolResponse(
        success=True,
        message=f"Found {len(medication_list)} {'active ' if active_only else ''}medication(s) for {patient.full_name}",
        data={
            "patient": patient.full_name,
            "medications": medication_list
        }
    )


def get_patient_lab_results(patient_id: str, limit: int = 10) -> ToolResponse:
    """
    Get recent lab results for a patient.
    
    Args:
        patient_id: The patient's ID
        limit: Maximum number of results to return
    
    Returns:
        ToolResponse with lab results
    """
    db = get_database()
    
    patient = db.get_patient(patient_id)
    if not patient:
        return ToolResponse(
            success=False,
            message=f"Patient with ID '{patient_id}' not found",
            data=None
        )
    
    results = db.get_patient_lab_results(patient_id)
    
    if not results:
        return ToolResponse(
            success=True,
            message=f"No lab results found for {patient.full_name}",
            data={"lab_results": []}
        )
    
    # Sort by date, most recent first
    results = sorted(results, key=lambda r: r.result_date, reverse=True)[:limit]
    
    result_list = [
        {
            "result_id": r.result_id,
            "test_name": r.test_name,
            "value": r.value,
            "unit": r.unit,
            "reference_range": r.reference_range,
            "status": r.status.value,
            "test_date": r.test_date.strftime("%d %B %Y"),
            "summary": r.to_summary()
        }
        for r in results
    ]
    
    # Highlight abnormal results
    abnormal = [r for r in results if r.status in [LabResultStatus.ABNORMAL_HIGH, LabResultStatus.ABNORMAL_LOW, LabResultStatus.CRITICAL]]
    
    return ToolResponse(
        success=True,
        message=f"Found {len(result_list)} lab result(s) for {patient.full_name}" + 
                (f" ({len(abnormal)} abnormal)" if abnormal else ""),
        data={
            "patient": patient.full_name,
            "lab_results": result_list,
            "abnormal_count": len(abnormal)
        }
    )


def get_patient_summary(patient_id: str) -> ToolResponse:
    """
    Get a comprehensive summary of a patient's current health status.
    
    This includes: profile, active conditions, current medications, recent labs, and alerts.
    
    Args:
        patient_id: The patient's ID
    
    Returns:
        ToolResponse with comprehensive patient summary
    """
    db = get_database()
    
    patient = db.get_patient(patient_id)
    if not patient:
        return ToolResponse(
            success=False,
            message=f"Patient with ID '{patient_id}' not found",
            data=None
        )
    
    # Gather all information
    diagnoses = db.get_patient_diagnoses(patient_id)
    active_diagnoses = [d for d in diagnoses if d.is_active]
    
    medications = db.get_patient_medications(patient_id)
    active_medications = [m for m in medications if m.is_active]
    
    lab_results = db.get_patient_lab_results(patient_id)
    recent_labs = sorted(lab_results, key=lambda r: r.result_date, reverse=True)[:5] if lab_results else []
    
    upcoming_appointments = db.get_upcoming_appointments(patient_id)
    
    summary = {
        "patient": {
            "id": patient.patient_id,
            "name": patient.full_name,
            "age": patient.age,
            "blood_type": patient.blood_type.value
        },
        "alerts": {
            "allergies": patient.allergies,
            "critical_alerts": [a.description for a in patient.get_critical_alerts()]
        },
        "active_conditions": [d.name for d in active_diagnoses],
        "current_medications": [m.to_summary() for m in active_medications],
        "recent_lab_highlights": [
            r.to_summary() for r in recent_labs 
            if r.status in [LabResultStatus.ABNORMAL_HIGH, LabResultStatus.ABNORMAL_LOW, LabResultStatus.CRITICAL]
        ],
        "upcoming_appointments": len(upcoming_appointments),
        "full_text_summary": patient.to_summary()
    }
    
    return ToolResponse(
        success=True,
        message=f"Generated comprehensive summary for {patient.full_name}",
        data=summary
    )


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 RECORDS TOOLS TEST")
    print("=" * 60)
    
    # Test 1: Get patient profile
    print("\n👤 Test 1: Getting patient profile for P001...")
    result = get_patient_profile("P001")
    print(f"   Success: {result.success}")
    if result.data:
        print(f"   Name: {result.data['name']}")
        print(f"   Age: {result.data['age']}")
        print(f"   Allergies: {result.data['allergies']}")
        print(f"   Conditions: {result.data['chronic_conditions']}")
    
    # Test 2: Search patients
    print("\n🔍 Test 2: Searching for patients named 'Smith'...")
    result = search_patients("Smith")
    print(f"   Message: {result.message}")
    if result.data:
        for p in result.data.get("patients", []):
            print(f"   • {p['name']} (ID: {p['patient_id']})")
    
    # Test 3: Get medical history
    print("\n📋 Test 3: Getting medical history for P001...")
    result = get_medical_history("P001")
    print(f"   Message: {result.message}")
    if result.data:
        for record in result.data.get("records", []):
            print(f"   • {record['date']} - {record['type']}: {record['chief_complaint']}")
    
    # Test 4: Get diagnoses
    print("\n🩺 Test 4: Getting diagnoses for P001...")
    result = get_patient_diagnoses("P001")
    print(f"   Message: {result.message}")
    if result.data:
        for dx in result.data.get("diagnoses", []):
            print(f"   • {dx['summary']}")
    
    # Test 5: Get medications
    print("\n💊 Test 5: Getting medications for P001...")
    result = get_patient_medications("P001")
    print(f"   Message: {result.message}")
    if result.data:
        for med in result.data.get("medications", []):
            print(f"   • {med['summary']}")
    
    # Test 6: Get lab results
    print("\n🧪 Test 6: Getting lab results for P001...")
    result = get_patient_lab_results("P001")
    print(f"   Message: {result.message}")
    if result.data:
        for lab in result.data.get("lab_results", []):
            print(f"   • {lab['summary']}")
    
    # Test 7: Get patient summary
    print("\n📊 Test 7: Getting comprehensive summary for P001...")
    result = get_patient_summary("P001")
    print(f"   Success: {result.success}")
    if result.data:
        print(f"\n   {result.data['full_text_summary']}")
    
    print("\n" + "=" * 60)
    print("✅ Records tools test complete!")
    print("=" * 60)