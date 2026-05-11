"""
Coordinator Agent - Central orchestrator for the Healthcare Assistant
Integrates with Appointment and Records agents for real functionality
"""

import os
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Import specialist agents
from src.agents.appointment_agent import AppointmentAgent
from src.agents.records_agent import RecordsAgent

# Import memory manager
from src.memory.patient_memory import MemoryManager

load_dotenv()


class Intent(Enum):
    """Classification of user intents"""
    BOOK_APPOINTMENT = "book_appointment"
    CHECK_AVAILABILITY = "check_availability"
    CANCEL_APPOINTMENT = "cancel_appointment"
    VIEW_APPOINTMENTS = "view_appointments"
    GET_MEDICAL_HISTORY = "get_medical_history"
    GET_PATIENT_INFO = "get_patient_info"
    GET_MEDICATIONS = "get_medications"
    GET_LAB_RESULTS = "get_lab_results"
    SEARCH_MEDICAL_INFO = "search_medical_info"
    GENERAL_QUERY = "general_query"
    GREETING = "greeting"
    UNKNOWN = "unknown"


@dataclass
class Task:
    """Represents a decomposed task"""
    intent: Intent
    parameters: Dict[str, Any]
    priority: int = 1
    status: str = "pending"


class CoordinatorAgent:
    """
    Central coordinator that orchestrates all healthcare assistant tasks.
    Routes requests to appropriate specialist agents.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1
        )
        
        # Initialise specialist agents
        self.appointment_agent = AppointmentAgent()
        self.records_agent = RecordsAgent()
        
        # Initialise memory
        self.memory = MemoryManager()
        
        # Intent classification prompt
        self.classification_prompt = """You are an intent classifier for a healthcare assistant.
Analyse the user's message and classify it into ONE of these intents:

- BOOK_APPOINTMENT: User wants to schedule a medical appointment
- CHECK_AVAILABILITY: User wants to check doctor availability
- CANCEL_APPOINTMENT: User wants to cancel an appointment
- VIEW_APPOINTMENTS: User wants to see their appointments
- GET_MEDICAL_HISTORY: User wants to see their medical history or records
- GET_PATIENT_INFO: User wants patient profile information
- GET_MEDICATIONS: User wants to know about their medications
- GET_LAB_RESULTS: User wants to see lab test results
- SEARCH_MEDICAL_INFO: User wants information about diseases, treatments, symptoms
- GENERAL_QUERY: General healthcare question
- GREETING: User is greeting or saying hello
- UNKNOWN: Cannot determine intent

Also extract relevant parameters like:
- doctor_name or specialisation
- date or time preferences
- patient_id (if mentioned)
- symptoms or conditions mentioned

Respond in this exact format:
INTENT: <intent_name>
PARAMETERS: <json_dict_of_parameters>
CONFIDENCE: <high/medium/low>
"""

    def classify_intent(self, user_message: str, context: Dict[str, Any] = None) -> tuple[Intent, Dict[str, Any]]:
        """Classify user intent and extract parameters"""
        
        context_info = ""
        if context:
            if context.get("patient_id"):
                context_info += f"\nCurrent patient ID: {context['patient_id']}"
            if context.get("last_intent"):
                context_info += f"\nPrevious intent: {context['last_intent']}"
        
        messages = [
            SystemMessage(content=self.classification_prompt),
            HumanMessage(content=f"Context: {context_info}\n\nUser message: {user_message}")
        ]
        
        response = self.llm.invoke(messages)
        response_text = response.content
        
        # Parse response
        intent = Intent.UNKNOWN
        parameters = {}
        
        for line in response_text.split('\n'):
            if line.startswith('INTENT:'):
                intent_str = line.replace('INTENT:', '').strip().upper()
                try:
                    intent = Intent[intent_str]
                except KeyError:
                    intent = Intent.UNKNOWN
            elif line.startswith('PARAMETERS:'):
                param_str = line.replace('PARAMETERS:', '').strip()
                try:
                    import json
                    parameters = json.loads(param_str)
                except:
                    parameters = {}
        
        return intent, parameters
    
        def route_to_agent(self, intent: Intent, parameters: Dict[str, Any],
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Route the request to the appropriate specialist agent"""
        
        patient_id = context.get("patient_id", "P001")
        
        # Appointment-related intents
        if intent == Intent.BOOK_APPOINTMENT:
            # First find doctor if specialisation given
            specialisation = parameters.get("specialisation") or parameters.get("specialty") or parameters.get("doctor_type")
            
            # Also check for common terms in raw parameters
            if not specialisation:
                for key, value in parameters.items():
                    if isinstance(value, str) and value.lower() in ["cardiologist", "cardiology", "heart"]:
                        specialisation = "Cardiology"
                        break
                    elif isinstance(value, str) and value.lower() in ["neurologist", "neurology"]:
                        specialisation = "Neurology"
                        break
                    elif isinstance(value, str) and value.lower() in ["psychiatrist", "psychiatry", "mental health"]:
                        specialisation = "Psychiatry"
                        break
                    elif isinstance(value, str) and value.lower() in ["gp", "general", "family doctor"]:
                        specialisation = "General Practice"
                        break
            
            if specialisation:
                doctor_result = self.appointment_agent.process({
                    "action": "find_doctor",
                    "parameters": {"specialisation": specialisation}
                })
                if doctor_result.get("success") and doctor_result.get("data", {}).get("doctors"):
                    doctor = doctor_result["data"]["doctors"][0]
                    parameters["doctor_id"] = doctor["doctor_id"]
                    return {
                        "success": True,
                        "message": f"I found Dr. {doctor['name']} ({doctor['specialisation']}). Would you like me to check their available slots?",
                        "data": {
                            "doctor": doctor,
                            "next_step": "check_availability"
                        },
                        "agent": "appointment"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I couldn't find a {specialisation} specialist. Would you like to see all available doctors?",
                        "agent": "appointment"
                    }
            else:
                return {
                    "success": False,
                    "message": "Please specify a doctor or specialisation (e.g., cardiologist, neurologist, psychiatrist).",
                    "agent": "appointment"
                }
        
        elif intent == Intent.CHECK_AVAILABILITY:
            doctor_id = parameters.get("doctor_id", "D001")
            return self.appointment_agent.process({
                "action": "get_slots",
                "parameters": {"doctor_id": doctor_id}
            }, context)
        
        elif intent == Intent.CANCEL_APPOINTMENT:
            return self.appointment_agent.process({
                "action": "cancel",
                "parameters": parameters
            }, context)
        
        elif intent == Intent.VIEW_APPOINTMENTS:
            return self.appointment_agent.process({
                "action": "list",
                "parameters": {"patient_id": patient_id}
            }, context)
        
        # Records-related intents
        elif intent == Intent.VIEW_RECORDS:
            return self.records_agent.process({
                "action": "get_medical_history",
                "parameters": parameters
            }, context)
        
        elif intent == Intent.VIEW_MEDICATIONS:
            return self.records_agent.process({
                "action": "get_medications",
                "parameters": parameters
            }, context)
        
        elif intent == Intent.VIEW_LAB_RESULTS:
            return self.records_agent.process({
                "action": "get_lab_results",
                "parameters": parameters
            }, context)
        
        elif intent == Intent.VIEW_DIAGNOSES:
            return self.records_agent.process({
                "action": "get_diagnoses",
                "parameters": parameters
            }, context)
        
        elif intent == Intent.GET_PATIENT_SUMMARY:
            return self.records_agent.process({
                "action": "get_summary",
                "parameters": parameters
            }, context)
        
        # Search/Information intents
        elif intent == Intent.SEARCH_MEDICAL_INFO:
            return {
                "success": True,
                "message": "Medical search functionality coming soon. For now, please consult your healthcare provider for medical information.",
                "agent": "search"
            }
        
        # Greeting
        elif intent == Intent.GREETING:
            patient_context = self.memory.get_patient_context(patient_id)
            name = patient_context.name if patient_context else "there"
            return {
                "success": True,
                "message": f"Hello {name}! I'm your Healthcare Assistant. I can help you with:\n"
                          f"• 📅 Booking appointments\n"
                          f"• 📋 Viewing your medical records\n"
                          f"• 💊 Checking your medications\n"
                          f"• 🧪 Reviewing lab results\n"
                          f"• ❓ Answering health questions\n\n"
                          f"How can I assist you today?",
                "agent": "coordinator"
            }
        
        # Help
        elif intent == Intent.HELP:
            return {
                "success": True,
                "message": "Here's what I can help you with:\n\n"
                          "**Appointments:**\n"
                          "• 'Book an appointment with a cardiologist'\n"
                          "• 'Show my appointments'\n"
                          "• 'Cancel my appointment'\n\n"
                          "**Medical Records:**\n"
                          "• 'Show my medical history'\n"
                          "• 'What are my current medications?'\n"
                          "• 'Show my lab results'\n"
                          "• 'Give me a summary of my health'\n\n"
                          "Just type your request naturally!",
                "agent": "coordinator"
            }
        
        # Unknown
        else:
            return {
                "success": False,
                "message": "I'm not sure how to help with that. Try asking about:\n"
                          "• Booking or viewing appointments\n"
                          "• Your medical records or medications\n"
                          "• Lab results\n\n"
                          "Or type 'help' for more options.",
                "agent": "coordinator"
            }
    
    def generate_response(self, result: Dict[str, Any], intent: Intent) -> str:
        """Generate a natural language response from agent results"""
        
        if not result.get("success"):
            return f"I'm sorry, {result.get('message', 'something went wrong.')}"
        
        # If there's already a formatted message, use it
        if result.get("agent") == "coordinator":
            return result.get("message", "")
        
        # Format based on intent and data
        data = result.get("data", {})
        message = result.get("message", "")
        
        if intent == Intent.BOOK_APPOINTMENT:
            if data.get("appointment_id"):
                return (f"✅ Great news! Your appointment has been booked.\n\n"
                       f"📋 **Appointment Details:**\n"
                       f"• Appointment ID: {data.get('appointment_id')}\n"
                       f"• Doctor: {data.get('doctor_name', 'Your doctor')}\n"
                       f"• Date: {data.get('date')}\n"
                       f"• Time: {data.get('time')}\n"
                       f"• Reason: {data.get('reason', 'Consultation')}\n\n"
                       f"Is there anything else I can help you with?")
        
        elif intent == Intent.CHECK_AVAILABILITY:
            slots = data.get("slots", [])
            if slots:
                slot_list = "\n".join([f"• {s['date']} at {s['start_time']}" for s in slots[:5]])
                return (f"📅 Here are the available slots:\n\n{slot_list}\n\n"
                       f"Would you like me to book one of these?")
        
        elif intent == Intent.VIEW_APPOINTMENTS:
            appointments = data.get("appointments", [])
            if appointments:
                appt_list = "\n".join([
                    f"• {a.get('date')} at {a.get('time')} - {a.get('doctor_name', 'Doctor')} ({a.get('status')})"
                    for a in appointments
                ])
                return f"📋 Your appointments:\n\n{appt_list}"
            return "You don't have any upcoming appointments."
        
        elif intent == Intent.GET_PATIENT_INFO:
            return (f"👤 **Patient Profile:**\n"
                   f"• Name: {data.get('name')}\n"
                   f"• Date of Birth: {data.get('date_of_birth')}\n"
                   f"• Blood Type: {data.get('blood_type')}\n"
                   f"• Allergies: {', '.join(data.get('allergies', ['None']))}\n"
                   f"• Emergency Contact: {data.get('emergency_contact', {}).get('name', 'N/A')}")
        
        elif intent == Intent.GET_MEDICATIONS:
            medications = data.get("medications", [])
            if medications:
                med_list = "\n".join([
                    f"• {m.get('name')} {m.get('dosage')} - {m.get('frequency')}"
                    for m in medications
                ])
                return f"💊 **Current Medications:**\n\n{med_list}"
            return "No current medications on record."
        
        elif intent == Intent.GET_LAB_RESULTS:
            results = data.get("lab_results", [])
            if results:
                lab_list = "\n".join([
                    f"• {r.get('test_name')}: {r.get('value')} {r.get('unit')} "
                    f"{'⚠️' if r.get('abnormal') else '✓'}"
                    for r in results[:5]
                ])
                abnormal = data.get("abnormal_count", 0)
                warning = f"\n\n⚠️ {abnormal} result(s) flagged for review." if abnormal > 0 else ""
                return f"🔬 **Recent Lab Results:**\n\n{lab_list}{warning}"
            return "No recent lab results on record."
        
        elif intent == Intent.GET_MEDICAL_HISTORY:
            records = data.get("records", [])
            if records:
                history_list = "\n".join([
                    f"• {r.get('date')}: {r.get('diagnosis')} - {r.get('doctor_name')}"
                    for r in records[:5]
                ])
                return f"📋 **Medical History:**\n\n{history_list}"
            return "No medical history records found."
        
        # Default: return the message
        return message if message else "Request processed successfully."
    
    def chat(self, user_message: str, patient_id: str = "P001") -> str:
        """
        Main entry point for conversation.
        Processes user message and returns natural language response.
        """
        
        # Get conversation context from memory
        conversation_id = f"conv_{patient_id}"
        history = self.memory.get_conversation_history(conversation_id)
        
        context = {
            "patient_id": patient_id,
            "conversation_history": history[-5:] if history else [],  # Last 5 exchanges
            "last_intent": history[-1].get("intent") if history else None
        }
        
        # Add user message to memory
        self.memory.add_to_conversation(conversation_id, {
            "role": "user",
            "content": user_message
        })
        
        # Classify intent
        intent, parameters = self.classify_intent(user_message, context)
        
        # Route to appropriate agent
        result = self.route_to_agent(intent, parameters, context)
        
        # Generate natural response
        response = self.generate_response(result, intent)
        
        # Save response and intent to memory
        self.memory.add_to_conversation(conversation_id, {
            "role": "assistant",
            "content": response,
            "intent": intent.value
        })
        
        return response


# ============================================
# Interactive Test
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 Healthcare Assistant - Interactive Test")
    print("=" * 60)
    print("\nInitialising...")
    
    coordinator = CoordinatorAgent()
    patient_id = "P001"  # John Smith
    
    print(f"\n✅ Ready! You are logged in as Patient {patient_id}")
    print("Type 'quit' to exit\n")
    print("-" * 60)
    
    # Test conversations
    test_messages = [
        "Hello!",
        "What are my current medications?",
        "Can I see my lab results?",
        "I need to book an appointment with a cardiologist",
        "Show me my appointments",
    ]
    
    print("\n🧪 Running automated tests...\n")
    
    for msg in test_messages:
        print(f"👤 You: {msg}")
        response = coordinator.chat(msg, patient_id)
        print(f"🤖 Assistant: {response}")
        print("-" * 60)
    
    # Interactive mode
    print("\n💬 Entering interactive mode...")
    print("Type your questions or 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Take care of your health!")
                break
            if not user_input:
                continue
                
            response = coordinator.chat(user_input, patient_id)
            print(f"🤖 Assistant: {response}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")