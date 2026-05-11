"""
Appointment Agent - Handles all appointment-related tasks

Based on: Agentic Healthcare Assistant Project Roadmap [2]
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.tools.appointment_tools import (
    get_available_slots,
    book_appointment,
    cancel_appointment,
    get_patient_appointments,
    find_doctors_by_specialisation
)


class AppointmentAgent:
    """
    Specialist agent for handling appointment operations.
    
    Capabilities:
    - Find doctors by specialisation
    - Check available appointment slots
    - Book new appointments
    - Cancel existing appointments
    - List patient appointments
    """
    
    def __init__(self):
        """Initialise the appointment agent."""
        self.name = "AppointmentAgent"
    
    def process(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process an appointment-related request.
        
        Args:
            request: Dict containing 'action' and 'parameters'
            context: Optional context with patient info
            
        Returns:
            Dict with success status, message, and data
        """
        action = request.get("action", "").lower()
        params = request.get("parameters", {})
        context = context or {}
        
        patient_id = context.get("patient_id") or params.get("patient_id", "P001")
        
        # Route to appropriate handler - with multiple aliases for each action
        
        # === LIST/VIEW APPOINTMENTS ===
        if action in ["get_appointments", "list", "view", "view_appointments", "show_appointments", "my_appointments"]:
            return self._handle_get_appointments(patient_id)
        
        # === GET AVAILABLE SLOTS ===
        elif action in ["get_slots", "get_available_slots", "check_availability", "availability", "slots", "available"]:
            doctor_id = params.get("doctor_id", "D001")
            return self._handle_get_slots(doctor_id)
        
        # === BOOK APPOINTMENT ===
        elif action in ["book", "book_appointment", "schedule", "make_appointment", "create"]:
            return self._handle_book_appointment(patient_id, params)
        
        # === CANCEL APPOINTMENT ===
        elif action in ["cancel", "cancel_appointment", "delete", "remove"]:
            appointment_id = params.get("appointment_id")
            return self._handle_cancel_appointment(appointment_id)
        
        # === FIND DOCTOR ===
        elif action in ["find_doctor", "find_doctors", "search_doctor", "get_doctor", "doctor"]:
            specialisation = params.get("specialisation") or params.get("specialty")
            return self._handle_find_doctor(specialisation)
        
        # === UNKNOWN ACTION ===
        else:
            return {
                "success": False,
                "message": f"Unknown action: {action}",
                "agent": self.name,
                "available_actions": [
                    "list", "get_slots", "book", "cancel", "find_doctor"
                ]
            }
    
    def _handle_get_appointments(self, patient_id: str) -> Dict[str, Any]:
        """Get all appointments for a patient."""
        result = get_patient_appointments(patient_id)
        
        if result["success"]:
            appointments = result.get("appointments", [])
            if appointments:
                formatted = []
                for apt in appointments:
                    formatted.append({
                        "appointment_id": apt.get("appointment_id"),
                        "date": apt.get("date"),
                        "time": apt.get("time"),
                        "doctor": apt.get("doctor_name", "Doctor"),
                        "status": apt.get("status", "confirmed"),
                        "formatted": f"{apt.get('date')} at {apt.get('time')} - {apt.get('doctor_name', 'Doctor')} ({apt.get('status', 'confirmed')})"
                    })
                return {
                    "success": True,
                    "message": f"Found {len(appointments)} appointment(s)",
                    "data": {"appointments": formatted},
                    "agent": self.name
                }
            else:
                return {
                    "success": True,
                    "message": "No upcoming appointments found",
                    "data": {"appointments": []},
                    "agent": self.name
                }
        
        return {
            "success": False,
            "message": result.get("message", "Failed to retrieve appointments"),
            "agent": self.name
        }
    
    def _handle_get_slots(self, doctor_id: str) -> Dict[str, Any]:
        """Get available slots for a doctor."""
        result = get_available_slots(doctor_id)
        
        if result["success"]:
            slots = result.get("slots", [])
            if slots:
                formatted_slots = []
                for slot in slots[:5]:  # Show max 5 slots
                    formatted_slots.append({
                        "date": slot.get("date"),
                        "time": slot.get("time"),
                        "formatted": f"{slot.get('date')} at {slot.get('time')}"
                    })
                return {
                    "success": True,
                    "message": f"Found {len(slots)} available slot(s)",
                    "data": {
                        "doctor_id": doctor_id,
                        "slots": formatted_slots
                    },
                    "agent": self.name
                }
            else:
                return {
                    "success": True,
                    "message": "No available slots found for this doctor",
                    "data": {"slots": []},
                    "agent": self.name
                }
        
        return {
            "success": False,
            "message": result.get("message", "Failed to get slots"),
            "agent": self.name
        }
    
    def _handle_book_appointment(self, patient_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Book an appointment."""
        doctor_id = params.get("doctor_id")
        date = params.get("date")
        time = params.get("time")
        reason = params.get("reason", "General consultation")
        
        # Validate required parameters
        if not doctor_id:
            return {
                "success": False,
                "message": "Please specify a doctor for the appointment",
                "agent": self.name
            }
        
        if not date or not time:
            # Get next available slot
            slots_result = get_available_slots(doctor_id)
            if slots_result["success"] and slots_result.get("slots"):
                slot = slots_result["slots"][0]
                date = slot.get("date")
                time = slot.get("time")
            else:
                return {
                    "success": False,
                    "message": "Please specify a date and time, or let me check availability first",
                    "agent": self.name
                }
        
        result = book_appointment(patient_id, doctor_id, date, time, reason)
        
        if result["success"]:
            apt = result.get("appointment", {})
            return {
                "success": True,
                "message": f"Appointment booked successfully for {date} at {time}",
                "data": {
                    "appointment_id": apt.get("appointment_id"),
                    "date": date,
                    "time": time,
                    "doctor_id": doctor_id
                },
                "agent": self.name
            }
        
        return {
            "success": False,
            "message": result.get("message", "Failed to book appointment"),
            "agent": self.name
        }
    
    def _handle_cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Cancel an appointment."""
        if not appointment_id:
            return {
                "success": False,
                "message": "Please specify which appointment to cancel",
                "agent": self.name
            }
        
        result = cancel_appointment(appointment_id)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Appointment {appointment_id} has been cancelled",
                "agent": self.name
            }
        
        return {
            "success": False,
            "message": result.get("message", "Failed to cancel appointment"),
            "agent": self.name
        }
    
    def _handle_find_doctor(self, specialisation: str) -> Dict[str, Any]:
        """Find doctors by specialisation."""
        if not specialisation:
            return {
                "success": False,
                "message": "Please specify a specialisation (e.g., Cardiology, Neurology)",
                "agent": self.name
            }
        
        result = find_doctors_by_specialisation(specialisation)
        
        if result["success"]:
            doctors = result.get("doctors", [])
            if doctors:
                formatted = []
                for doc in doctors:
                    formatted.append({
                        "doctor_id": doc.get("doctor_id"),
                        "name": doc.get("name"),
                        "specialisation": doc.get("specialisation")
                    })
                return {
                    "success": True,
                    "message": f"Found {len(doctors)} doctor(s)",
                    "data": {"doctors": formatted},
                    "agent": self.name
                }
        
        return {
            "success": False,
            "message": f"No doctors found for {specialisation}",
            "agent": self.name
        }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("📅 Appointment Agent Test")
    print("=" * 60)
    
    agent = AppointmentAgent()
    context = {"patient_id": "P001"}
    
    # Test 1: List appointments
    print("\n📋 Test 1: List appointments")
    result = agent.process({"action": "list", "parameters": {}}, context)
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    
    # Test 2: Find doctor
    print("\n👨‍⚕️ Test 2: Find cardiologist")
    result = agent.process({
        "action": "find_doctor",
        "parameters": {"specialisation": "Cardiology"}
    }, context)
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("data", {}).get("doctors"):
        print(f"   Doctor: {result['data']['doctors'][0]}")
    
    # Test 3: Get slots
    print("\n🕐 Test 3: Get available slots")
    result = agent.process({
        "action": "get_slots",
        "parameters": {"doctor_id": "D001"}
    }, context)
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("data", {}).get("slots"):
        print(f"   First slot: {result['data']['slots'][0]}")
    
    # Test 4: Book appointment
    print("\n📝 Test 4: Book appointment")
    result = agent.process({
        "action": "book",
        "parameters": {
            "doctor_id": "D001",
            "date": "2026-05-10",
            "time": "10:00 AM",
            "reason": "Follow-up"
        }
    }, context)
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    
    print("\n" + "=" * 60)
    print("✅ Appointment Agent tests complete!")
    print("=" * 60)