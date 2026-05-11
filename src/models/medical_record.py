"""
Medical Record Model - Defines medical history and record data structures

This module contains Pydantic models for medical records, diagnoses,
lab results, medications, and clinical notes.

Based on: Agentic Healthcare Assistant Project Roadmap
Phase 1, Week 2: Data Models
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class RecordType(str, Enum):
    """Types of medical records."""
    CONSULTATION = "consultation"
    DIAGNOSIS = "diagnosis"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    PROCEDURE = "procedure"
    IMAGING = "imaging"
    VACCINATION = "vaccination"
    REFERRAL = "referral"
    DISCHARGE_SUMMARY = "discharge_summary"
    CLINICAL_NOTE = "clinical_note"


class RecordStatus(str, Enum):
    """Status of medical record."""
    DRAFT = "draft"
    FINAL = "final"
    AMENDED = "amended"
    CANCELLED = "cancelled"


class LabResultStatus(str, Enum):
    """Status of lab result values."""
    NORMAL = "normal"
    ABNORMAL_LOW = "abnormal_low"
    ABNORMAL_HIGH = "abnormal_high"
    CRITICAL = "critical"
    PENDING = "pending"


class MedicationStatus(str, Enum):
    """Status of medication."""
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    ON_HOLD = "on_hold"


# =============================================================================
# SUPPORTING MODELS
# =============================================================================

class Diagnosis(BaseModel):
    """Medical diagnosis model."""
    diagnosis_id: str = Field(..., description="Unique diagnosis identifier")
    code: Optional[str] = Field(None, description="ICD-10 code")
    name: str = Field(..., description="Diagnosis name")
    description: Optional[str] = Field(None, description="Detailed description")
    diagnosed_date: date = Field(..., description="Date of diagnosis")
    diagnosed_by: str = Field(..., description="Doctor ID who made diagnosis")
    is_chronic: bool = Field(default=False, description="Whether condition is chronic")
    is_active: bool = Field(default=True, description="Whether condition is currently active")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    def to_summary(self) -> str:
        """Generate summary string."""
        status = "Active" if self.is_active else "Resolved"
        chronic = " (Chronic)" if self.is_chronic else ""
        return f"{self.name}{chronic} - {status} (Diagnosed: {self.diagnosed_date})"


class LabResult(BaseModel):
    """Laboratory test result model."""
    result_id: str = Field(..., description="Unique result identifier")
    test_name: str = Field(..., description="Name of the test")
    test_code: Optional[str] = Field(None, description="Test code")
    value: str = Field(..., description="Result value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Normal reference range")
    status: LabResultStatus = Field(default=LabResultStatus.NORMAL)
    test_date: date = Field(..., description="Date test was performed")
    result_date: date = Field(..., description="Date results available")
    performed_by: Optional[str] = Field(None, description="Lab or technician")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    def to_summary(self) -> str:
        """Generate summary string."""
        status_icon = {
            LabResultStatus.NORMAL: "✅",
            LabResultStatus.ABNORMAL_LOW: "⬇️",
            LabResultStatus.ABNORMAL_HIGH: "⬆️",
            LabResultStatus.CRITICAL: "🚨",
            LabResultStatus.PENDING: "⏳"
        }
        icon = status_icon.get(self.status, "")
        unit_str = f" {self.unit}" if self.unit else ""
        ref_str = f" (Ref: {self.reference_range})" if self.reference_range else ""
        return f"{icon} {self.test_name}: {self.value}{unit_str}{ref_str}"


class Medication(BaseModel):
    """Medication/prescription model."""
    medication_id: str = Field(..., description="Unique medication identifier")
    name: str = Field(..., description="Medication name")
    dosage: str = Field(..., description="Dosage (e.g., '500mg')")
    frequency: str = Field(..., description="How often (e.g., 'twice daily')")
    route: str = Field(default="oral", description="Route of administration")
    prescribed_date: date = Field(..., description="Date prescribed")
    prescribed_by: str = Field(..., description="Prescribing doctor ID")
    start_date: date = Field(..., description="Start date")
    end_date: Optional[date] = Field(None, description="End date if applicable")
    status: MedicationStatus = Field(default=MedicationStatus.ACTIVE)
    reason: Optional[str] = Field(None, description="Reason for medication")
    instructions: Optional[str] = Field(None, description="Special instructions")
    refills_remaining: int = Field(default=0, description="Number of refills remaining")
    
    @property
    def is_active(self) -> bool:
        """Check if medication is currently active."""
        if self.status != MedicationStatus.ACTIVE:
            return False
        if self.end_date and self.end_date < date.today():
            return False
        return True
    
    def to_summary(self) -> str:
        """Generate summary string."""
        status_str = f" ({self.status.value})" if self.status != MedicationStatus.ACTIVE else ""
        return f"{self.name} {self.dosage} - {self.frequency}{status_str}"


class VitalSigns(BaseModel):
    """Vital signs measurement."""
    recorded_at: datetime = Field(default_factory=datetime.now)
    blood_pressure_systolic: Optional[int] = Field(None, description="Systolic BP (mmHg)")
    blood_pressure_diastolic: Optional[int] = Field(None, description="Diastolic BP (mmHg)")
    heart_rate: Optional[int] = Field(None, description="Heart rate (bpm)")
    temperature: Optional[float] = Field(None, description="Temperature (°C)")
    respiratory_rate: Optional[int] = Field(None, description="Respiratory rate (breaths/min)")
    oxygen_saturation: Optional[int] = Field(None, description="SpO2 (%)")
    weight: Optional[float] = Field(None, description="Weight (kg)")
    height: Optional[float] = Field(None, description="Height (cm)")
    
    @property
    def blood_pressure(self) -> Optional[str]:
        """Get blood pressure as string."""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic} mmHg"
        return None
    
    @property
    def bmi(self) -> Optional[float]:
        """Calculate BMI if height and weight available."""
        if self.weight and self.height:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 1)
        return None
    
    def to_summary(self) -> str:
        """Generate summary string."""
        parts = []
        if self.blood_pressure:
            parts.append(f"BP: {self.blood_pressure}")
        if self.heart_rate:
            parts.append(f"HR: {self.heart_rate} bpm")
        if self.temperature:
            parts.append(f"Temp: {self.temperature}°C")
        if self.oxygen_saturation:
            parts.append(f"SpO2: {self.oxygen_saturation}%")
        return " | ".join(parts) if parts else "No vitals recorded"


# =============================================================================
# MAIN MEDICAL RECORD MODEL
# =============================================================================

class MedicalRecord(BaseModel):
    """
    Complete medical record model.
    
    This is the primary model for medical records in the Healthcare Assistant.
    """
    record_id: str = Field(..., description="Unique record identifier")
    patient_id: str = Field(..., description="Patient ID")
    
    # Record Info
    record_type: RecordType = Field(..., description="Type of record")
    status: RecordStatus = Field(default=RecordStatus.FINAL)
    
    # Timing
    encounter_date: date = Field(..., description="Date of encounter")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Provider
    doctor_id: str = Field(..., description="Attending doctor ID")
    department: Optional[str] = Field(None, description="Department")
    facility: Optional[str] = Field(None, description="Healthcare facility")
    
    # Clinical Content
    chief_complaint: Optional[str] = Field(None, description="Main reason for visit")
    history_of_present_illness: Optional[str] = Field(None, description="HPI narrative")
    assessment: Optional[str] = Field(None, description="Clinical assessment")
    plan: Optional[str] = Field(None, description="Treatment plan")
    
    # Associated Data
    diagnoses: List[Diagnosis] = Field(default_factory=list)
    medications: List[Medication] = Field(default_factory=list)
    lab_results: List[LabResult] = Field(default_factory=list)
    vital_signs: Optional[VitalSigns] = Field(None)
    
    # Notes
    clinical_notes: Optional[str] = Field(None, description="Free-text clinical notes")
    follow_up_instructions: Optional[str] = Field(None, description="Follow-up instructions")
    
    def get_active_diagnoses(self) -> List[Diagnosis]:
        """Get all active diagnoses."""
        return [d for d in self.diagnoses if d.is_active]
    
    def get_active_medications(self) -> List[Medication]:
        """Get all active medications."""
        return [m for m in self.medications if m.is_active]
    
    def get_abnormal_labs(self) -> List[LabResult]:
        """Get all abnormal lab results."""
        abnormal_statuses = [LabResultStatus.ABNORMAL_LOW, LabResultStatus.ABNORMAL_HIGH, LabResultStatus.CRITICAL]
        return [r for r in self.lab_results if r.status in abnormal_statuses]
    
    def to_summary(self) -> str:
        """Generate a comprehensive summary for LLM context."""
        parts = [
            f"Medical Record: {self.record_id}",
            f"Date: {self.encounter_date.strftime('%d %B %Y')}",
            f"Type: {self.record_type.value}",
        ]
        
        if self.chief_complaint:
            parts.append(f"Chief Complaint: {self.chief_complaint}")
        
        if self.assessment:
            parts.append(f"Assessment: {self.assessment}")
        
        if self.diagnoses:
            active_dx = self.get_active_diagnoses()
            if active_dx:
                dx_list = ", ".join([d.name for d in active_dx])
                parts.append(f"Active Diagnoses: {dx_list}")
        
        if self.medications:
            active_meds = self.get_active_medications()
            if active_meds:
                med_list = ", ".join([m.name for m in active_meds])
                parts.append(f"Current Medications: {med_list}")
        
        abnormal_labs = self.get_abnormal_labs()
        if abnormal_labs:
            lab_list = ", ".join([r.test_name for r in abnormal_labs])
            parts.append(f"⚠️ Abnormal Labs: {lab_list}")
        
        if self.vital_signs:
            parts.append(f"Vitals: {self.vital_signs.to_summary()}")
        
        if self.plan:
            parts.append(f"Plan: {self.plan}")
        
        return "\n".join(parts)
    
    class Config:
        json_schema_extra = {
            "example": {
                "record_id": "R001",
                "patient_id": "P001",
                "record_type": "consultation",
                "encounter_date": "2026-04-15",
                "doctor_id": "D001",
                "chief_complaint": "Chest pain and shortness of breath",
                "assessment": "Stable angina, well-controlled hypertension",
                "plan": "Continue current medications, follow up in 3 months"
            }
        }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 MEDICAL RECORD MODEL TEST")
    print("=" * 60)
    
    # Create a test medical record
    record = MedicalRecord(
        record_id="R001",
        patient_id="P001",
        record_type=RecordType.CONSULTATION,
        encounter_date=date(2026, 4, 15),
        doctor_id="D001",
        department="Cardiology",
        chief_complaint="Chest pain and shortness of breath during exertion",
        assessment="Stable angina pectoris. Hypertension well-controlled on current medication.",
        plan="Continue current medications. Lifestyle modifications advised. Follow up in 3 months.",
        diagnoses=[
            Diagnosis(
                diagnosis_id="DX001",
                code="I20.9",
                name="Angina Pectoris",
                diagnosed_date=date(2025, 6, 10),
                diagnosed_by="D001",
                is_chronic=True,
                is_active=True
            ),
            Diagnosis(
                diagnosis_id="DX002",
                code="I10",
                name="Essential Hypertension",
                diagnosed_date=date(2020, 3, 15),
                diagnosed_by="D002",
                is_chronic=True,
                is_active=True
            )
        ],
        medications=[
            Medication(
                medication_id="MED001",
                name="Aspirin",
                dosage="100mg",
                frequency="once daily",
                prescribed_date=date(2025, 6, 10),
                prescribed_by="D001",
                start_date=date(2025, 6, 10),
                reason="Antiplatelet therapy for angina"
            ),
            Medication(
                medication_id="MED002",
                name="Lisinopril",
                dosage="10mg",
                frequency="once daily",
                prescribed_date=date(2020, 3, 15),
                prescribed_by="D002",
                start_date=date(2020, 3, 15),
                reason="Hypertension management"
            )
        ],
        lab_results=[
            LabResult(
                result_id="LAB001",
                test_name="Total Cholesterol",
                value="5.8",
                unit="mmol/L",
                reference_range="< 5.0",
                status=LabResultStatus.ABNORMAL_HIGH,
                test_date=date(2026, 4, 14),
                result_date=date(2026, 4, 15)
            ),
            LabResult(
                result_id="LAB002",
                test_name="HbA1c",
                value="5.4",
                unit="%",
                reference_range="< 5.7",
                status=LabResultStatus.NORMAL,
                test_date=date(2026, 4, 14),
                result_date=date(2026, 4, 15)
            )
        ],
        vital_signs=VitalSigns(
            blood_pressure_systolic=135,
            blood_pressure_diastolic=85,
            heart_rate=72,
            temperature=36.8,
            oxygen_saturation=98,
            weight=78.5,
            height=175
        ),
        follow_up_instructions="Return in 3 months. Call if chest pain worsens or occurs at rest."
    )
    
    print(f"\n📋 Medical Record created:")
    print("-" * 40)
    print(record.to_summary())
    
    print(f"\n📊 Statistics:")
    print(f"   Active diagnoses: {len(record.get_active_diagnoses())}")
    print(f"   Active medications: {len(record.get_active_medications())}")
    print(f"   Abnormal labs: {len(record.get_abnormal_labs())}")
    print(f"   BMI: {record.vital_signs.bmi}")
    
    print("\n" + "=" * 60)
    print("✅ Medical record model test complete!")
    print("=" * 60)