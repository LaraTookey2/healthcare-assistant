"""
Appointment Model - Defines appointment and scheduling data structures

This module contains Pydantic models for appointments, time slots,
and doctor availability.

Based on: Agentic Healthcare Assistant Project Roadmap
Phase 1, Week 2: Data Models
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, time, datetime, timedelta
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class AppointmentStatus(str, Enum):
    """Appointment status options."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
    """Types of appointments."""
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    ANNUAL_CHECKUP = "annual_checkup"
    URGENT = "urgent"
    PROCEDURE = "procedure"
    LAB_WORK = "lab_work"
    VACCINATION = "vaccination"
    TELEHEALTH = "telehealth"


class Specialisation(str, Enum):
    """Doctor specialisations."""
    GENERAL_PRACTICE = "General Practice"
    CARDIOLOGY = "Cardiology"
    DERMATOLOGY = "Dermatology"
    NEUROLOGY = "Neurology"
    ORTHOPEDICS = "Orthopedics"
    PEDIATRICS = "Pediatrics"
    PSYCHIATRY = "Psychiatry"
    ONCOLOGY = "Oncology"
    ENDOCRINOLOGY = "Endocrinology"
    GASTROENTEROLOGY = "Gastroenterology"


class DayOfWeek(str, Enum):
    """Days of the week."""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


# =============================================================================
# SUPPORTING MODELS
# =============================================================================

class TimeSlot(BaseModel):
    """Represents a bookable time slot."""
    slot_id: str = Field(..., description="Unique slot identifier")
    start_time: time = Field(..., description="Slot start time")
    end_time: time = Field(..., description="Slot end time")
    is_available: bool = Field(default=True, description="Whether slot is available")
    
    @property
    def duration_minutes(self) -> int:
        """Calculate slot duration in minutes."""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)
    
    def to_string(self) -> str:
        """Format time slot as string."""
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class DailySchedule(BaseModel):
    """Doctor's schedule for a specific day."""
    day: DayOfWeek = Field(..., description="Day of week")
    start_time: time = Field(..., description="Working hours start")
    end_time: time = Field(..., description="Working hours end")
    slot_duration_minutes: int = Field(default=30, description="Appointment slot duration")
    is_working: bool = Field(default=True, description="Whether doctor works this day")
    
    def generate_slots(self, date_for: date) -> List[TimeSlot]:
        """Generate time slots for this day."""
        if not self.is_working:
            return []
        
        slots = []
        current_time = datetime.combine(date_for, self.start_time)
        end_datetime = datetime.combine(date_for, self.end_time)
        slot_duration = timedelta(minutes=self.slot_duration_minutes)
        slot_num = 1
        
        while current_time + slot_duration <= end_datetime:
            slot_end = current_time + slot_duration
            slots.append(TimeSlot(
                slot_id=f"{date_for.isoformat()}_slot_{slot_num:02d}",
                start_time=current_time.time(),
                end_time=slot_end.time(),
                is_available=True
            ))
            current_time = slot_end
            slot_num += 1
        
        return slots


# =============================================================================
# DOCTOR MODEL
# =============================================================================

class Doctor(BaseModel):
    """
    Doctor model with specialisation and availability.
    """
    doctor_id: str = Field(..., description="Unique doctor identifier")
    first_name: str = Field(..., description="Doctor's first name")
    last_name: str = Field(..., description="Doctor's last name")
    specialisation: Specialisation = Field(..., description="Medical specialisation")
    qualifications: List[str] = Field(default_factory=list, description="Medical qualifications")
    
    # Contact
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    room_number: Optional[str] = Field(None, description="Office room number")
    
    # Schedule
    weekly_schedule: List[DailySchedule] = Field(default_factory=list, description="Weekly availability")
    
    # System Fields
    is_active: bool = Field(default=True)
    accepts_new_patients: bool = Field(default=True)
    
    @property
    def full_name(self) -> str:
        """Get doctor's full name with title."""
        return f"Dr. {self.first_name} {self.last_name}"
    
    def get_working_days(self) -> List[str]:
        """Get list of working days."""
        return [schedule.day.value for schedule in self.weekly_schedule if schedule.is_working]
    
    def get_schedule_for_day(self, day: DayOfWeek) -> Optional[DailySchedule]:
        """Get schedule for a specific day."""
        for schedule in self.weekly_schedule:
            if schedule.day == day:
                return schedule
        return None
    
    def to_summary(self) -> str:
        """Generate a summary string for LLM context."""
        working_days = self.get_working_days()
        return (
            f"{self.full_name}\n"
            f"Specialisation: {self.specialisation.value}\n"
            f"Available: {', '.join(working_days)}\n"
            f"Room: {self.room_number or 'TBC'}"
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "doctor_id": "D001",
                "first_name": "Sarah",
                "last_name": "Smith",
                "specialisation": "Cardiology",
                "qualifications": ["MD", "FRACP"],
                "room_number": "A204"
            }
        }


# =============================================================================
# APPOINTMENT MODEL
# =============================================================================

class Appointment(BaseModel):
    """
    Complete appointment model.
    """
    appointment_id: str = Field(..., description="Unique appointment identifier")
    
    # Participants
    patient_id: str = Field(..., description="Patient ID")
    doctor_id: str = Field(..., description="Doctor ID")
    
    # Timing
    appointment_date: date = Field(..., description="Appointment date")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    
    # Details
    appointment_type: AppointmentType = Field(default=AppointmentType.CONSULTATION)
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    reason: str = Field(default="", description="Reason for visit")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # System Fields
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Who created the appointment")
    
    # Reminders
    reminder_sent: bool = Field(default=False)
    reminder_date: Optional[datetime] = Field(None)
    
    @property
    def duration_minutes(self) -> int:
        """Calculate appointment duration in minutes."""
        start_dt = datetime.combine(self.appointment_date, self.start_time)
        end_dt = datetime.combine(self.appointment_date, self.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)
    
    @property
    def is_upcoming(self) -> bool:
        """Check if appointment is in the future."""
        now = datetime.now()
        appt_datetime = datetime.combine(self.appointment_date, self.start_time)
        return appt_datetime > now
    
    @property
    def is_today(self) -> bool:
        """Check if appointment is today."""
        return self.appointment_date == date.today()
    
    def can_cancel(self) -> bool:
        """Check if appointment can be cancelled (24h notice)."""
        if self.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            return False
        appt_datetime = datetime.combine(self.appointment_date, self.start_time)
        return datetime.now() + timedelta(hours=24) < appt_datetime
    
    def to_summary(self) -> str:
        """Generate a summary string for LLM context."""
        return (
            f"Appointment {self.appointment_id}\n"
            f"Date: {self.appointment_date.strftime('%A, %d %B %Y')}\n"
            f"Time: {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}\n"
            f"Type: {self.appointment_type.value}\n"
            f"Status: {self.status.value}\n"
            f"Reason: {self.reason or 'Not specified'}"
        )
    
    class Config:
        json_schema_extra = {
            "example": {
                "appointment_id": "A001",
                "patient_id": "P001",
                "doctor_id": "D001",
                "appointment_date": "2026-05-05",
                "start_time": "10:00",
                "end_time": "10:30",
                "appointment_type": "consultation",
                "status": "scheduled",
                "reason": "Annual cardiac checkup"
            }
        }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("📅 APPOINTMENT MODEL TEST")
    print("=" * 60)
    
    # Create a test doctor
    doctor = Doctor(
        doctor_id="D001",
        first_name="Sarah",
        last_name="Smith",
        specialisation=Specialisation.CARDIOLOGY,
        qualifications=["MD", "FRACP", "PhD"],
        room_number="A204",
        weekly_schedule=[
            DailySchedule(day=DayOfWeek.MONDAY, start_time=time(9, 0), end_time=time(16, 0)),
            DailySchedule(day=DayOfWeek.WEDNESDAY, start_time=time(9, 0), end_time=time(16, 0)),
            DailySchedule(day=DayOfWeek.FRIDAY, start_time=time(9, 0), end_time=time(14, 0)),
        ]
    )
    
    print(f"\n👨‍⚕️ Doctor created:")
    print(doctor.to_summary())
    print(f"Working days: {doctor.get_working_days()}")
    
    # Generate time slots for Monday
    monday_schedule = doctor.get_schedule_for_day(DayOfWeek.MONDAY)
    if monday_schedule:
        slots = monday_schedule.generate_slots(date(2026, 5, 4))  # A Monday
        print(f"\n📆 Available slots for Monday: {len(slots)}")
        for slot in slots[:3]:  # Show first 3
            print(f"   • {slot.to_string()}")
        print(f"   ... and {len(slots) - 3} more")
    
    # Create a test appointment
    appointment = Appointment(
        appointment_id="A001",
        patient_id="P001",
        doctor_id="D001",
        appointment_date=date(2026, 5, 4),
        start_time=time(10, 0),
        end_time=time(10, 30),
        appointment_type=AppointmentType.CONSULTATION,
        reason="Annual cardiac checkup"
    )
    
    print(f"\n📋 Appointment created:")
    print(appointment.to_summary())
    print(f"Can cancel: {appointment.can_cancel()}")
    
    print("\n" + "=" * 60)
    print("✅ Appointment model test complete!")
    print("=" * 60)