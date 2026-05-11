"""
Patient Model - Defines patient data structures

This module contains Pydantic models for patient information,
contact details, and medical alerts.

Based on: Agentic Healthcare Assistant Project Roadmap
Phase 1, Week 2: Data Models
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class Gender(str, Enum):
    """Patient gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class BloodType(str, Enum):
    """Blood type options."""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    UNKNOWN = "unknown"


# =============================================================================
# SUPPORTING MODELS
# =============================================================================

class ContactInfo(BaseModel):
    """Patient contact information."""
    phone: str = Field(..., description="Primary phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Home address")
    emergency_contact_name: Optional[str] = Field(None, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, description="Emergency contact phone")


class MedicalAlert(BaseModel):
    """Medical alert for patient safety."""
    alert_type: str = Field(..., description="Type of alert (allergy, condition, etc.)")
    description: str = Field(..., description="Alert description")
    severity: str = Field(default="moderate", description="Severity: low, moderate, high, critical")
    created_at: datetime = Field(default_factory=datetime.now)


class Insurance(BaseModel):
    """Patient insurance information."""
    provider: str = Field(..., description="Insurance provider name")
    policy_number: str = Field(..., description="Policy number")
    group_number: Optional[str] = Field(None, description="Group number")
    valid_until: Optional[date] = Field(None, description="Policy expiration date")


# =============================================================================
# MAIN PATIENT MODEL
# =============================================================================

class Patient(BaseModel):
    """
    Complete patient model with all relevant information.
    
    This is the primary model for patient data in the Healthcare Assistant.
    """
    # Identification
    patient_id: str = Field(..., description="Unique patient identifier")
    
    # Personal Information
    first_name: str = Field(..., description="Patient's first name")
    last_name: str = Field(..., description="Patient's last name")
    date_of_birth: date = Field(..., description="Date of birth")
    gender: Gender = Field(default=Gender.PREFER_NOT_TO_SAY)
    blood_type: BloodType = Field(default=BloodType.UNKNOWN)
    
    # Contact
    contact: ContactInfo = Field(..., description="Contact information")
    
    # Medical Information
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    chronic_conditions: List[str] = Field(default_factory=list, description="Chronic conditions")
    current_medications: List[str] = Field(default_factory=list, description="Current medications")
    medical_alerts: List[MedicalAlert] = Field(default_factory=list, description="Active medical alerts")
    
    # Insurance
    insurance: Optional[Insurance] = Field(None, description="Insurance information")
    
    # Preferences
    preferred_doctor_id: Optional[str] = Field(None, description="Preferred doctor ID")
    preferred_appointment_time: Optional[str] = Field(None, description="Preferred time: morning, afternoon, evening")
    preferred_contact_method: str = Field(default="phone", description="Preferred contact: phone, email, sms")
    
    # System Fields
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)
    
    @property
    def full_name(self) -> str:
        """Get patient's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        """Calculate patient's age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def has_allergy(self, substance: str) -> bool:
        """Check if patient has a specific allergy."""
        return any(substance.lower() in allergy.lower() for allergy in self.allergies)
    
    def get_critical_alerts(self) -> List[MedicalAlert]:
        """Get all critical medical alerts."""
        return [alert for alert in self.medical_alerts if alert.severity == "critical"]
    
    def to_summary(self) -> str:
        """Generate a summary string for LLM context."""
        summary_parts = [
            f"Patient: {self.full_name} (ID: {self.patient_id})",
            f"Age: {self.age}, Gender: {self.gender.value}",
            f"Blood Type: {self.blood_type.value}",
        ]
        
        if self.allergies:
            summary_parts.append(f"⚠️ Allergies: {', '.join(self.allergies)}")
        
        if self.chronic_conditions:
            summary_parts.append(f"Conditions: {', '.join(self.chronic_conditions)}")
        
        if self.current_medications:
            summary_parts.append(f"Medications: {', '.join(self.current_medications)}")
        
        critical_alerts = self.get_critical_alerts()
        if critical_alerts:
            alerts_str = ", ".join([a.description for a in critical_alerts])
            summary_parts.append(f"🚨 Critical Alerts: {alerts_str}")
        
        return "\n".join(summary_parts)
    
    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "P001",
                "first_name": "John",
                "last_name": "Smith",
                "date_of_birth": "1985-03-15",
                "gender": "male",
                "blood_type": "O+",
                "contact": {
                    "phone": "+64 21 123 4567",
                    "email": "john.smith@email.com"
                },
                "allergies": ["Penicillin", "Peanuts"],
                "chronic_conditions": ["Type 2 Diabetes", "Hypertension"],
                "current_medications": ["Metformin 500mg", "Lisinopril 10mg"]
            }
        }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("📋 PATIENT MODEL TEST")
    print("=" * 60)
    
    # Create a test patient
    patient = Patient(
        patient_id="P001",
        first_name="John",
        last_name="Smith",
        date_of_birth=date(1985, 3, 15),
        gender=Gender.MALE,
        blood_type=BloodType.O_POSITIVE,
        contact=ContactInfo(
            phone="+64 21 123 4567",
            email="john.smith@email.com",
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
        ]
    )
    
    print(f"\n✅ Patient created successfully!")
    print(f"\n{patient.to_summary()}")
    print(f"\n📊 Has penicillin allergy: {patient.has_allergy('penicillin')}")
    print(f"📊 Critical alerts: {len(patient.get_critical_alerts())}")
    
    print("\n" + "=" * 60)
    print("✅ Patient model test complete!")
    print("=" * 60)