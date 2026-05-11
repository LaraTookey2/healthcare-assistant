"""
Coordinator Agent - Main orchestrator for the Healthcare Assistant.
This agent:
- Classifies user intent
- Routes requests to specialist agents
- Manages conversation memory
- Formats responses for the user
"""

import os
import sys
import json
import re
from enum import Enum
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.memory.patient_memory import MemoryManager
from src.agents.appointment_agent import AppointmentAgent
from src.agents.records_agent import RecordsAgent
from src.agents.search_agent import SearchAgent

load_dotenv()


class Intent(Enum):
    """Possible user intents."""
    GREETING = "greeting"
    BOOK_APPOINTMENT = "book_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    CONFIRM_APPOINTMENT = "confirm_appointment"
    VIEW_APPOINTMENTS = "view_appointments"
    CHECK_AVAILABILITY = "check_availability"
    VIEW_RECORDS = "view_records"
    VIEW_MEDICATIONS = "view_medications"
    VIEW_LAB_RESULTS = "view_lab_results"
    VIEW_DIAGNOSES = "view_diagnoses"
    GET_PATIENT_SUMMARY = "get_patient_summary"
    SEARCH_MEDICAL_INFO = "search_medical_info"
    HELP = "help"
    UNKNOWN = "unknown"


class CoordinatorAgent:
    """Main coordinator that orchestrates the healthcare assistant."""

    def __init__(self):
        """Initialise the coordinator with LLM and specialist agents."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1
        )
        self.memory = MemoryManager()
        self.appointment_agent = AppointmentAgent()
        self.records_agent = RecordsAgent()
        self.search_agent = SearchAgent()
        self.last_trace = {}

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------
    def _infer_specialisation(self, text: str, parameters: Dict[str, Any]) -> str:
        """Infer medical specialisation from user text or extracted parameters."""
        text_lower = text.lower()
        possible_values = " ".join(
            str(value).lower()
            for value in parameters.values()
            if isinstance(value, str)
        )
        combined = f"{text_lower} {possible_values}"

        if any(word in combined for word in ["cardiologist", "cardiology", "heart", "cardiac"]):
            return "Cardiology"
        if any(word in combined for word in ["nephrologist", "nephrology", "kidney", "renal"]):
            return "Nephrology"
        if any(word in combined for word in ["neurologist", "neurology", "brain", "nerve"]):
            return "Neurology"
        if any(word in combined for word in ["psychiatrist", "psychiatry", "mental health"]):
            return "Psychiatry"
        if any(word in combined for word in ["gp", "general practitioner", "family doctor", "general practice"]):
            return "General Practice"

        return (
            parameters.get("specialisation")
            or parameters.get("specialty")
            or parameters.get("doctor_type")
            or ""
        )

    def _normalise_date(self, text: str, parameters: Dict[str, Any]) -> str:
        """Extract or normalise appointment date."""
        text_lower = text.lower()
        date_value = parameters.get("date")

        if date_value and re.match(r"\d{4}-\d{2}-\d{2}", str(date_value)):
            return str(date_value)

        date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        if date_match:
            return date_match.group(0)

        today = datetime.now().date()
        if "tomorrow" in text_lower:
            return str(today + timedelta(days=1))
        if "today" in text_lower:
            return str(today)

        return ""

    def _normalise_time(self, text: str, parameters: Dict[str, Any]) -> str:
        """Extract appointment time."""
        time_value = parameters.get("time")
        if time_value:
            return (
                str(time_value)
                .upper()
                .replace("AM", " AM")
                .replace("PM", " PM")
                .replace("  ", " ")
                .strip()
            )

        time_match = re.search(
            r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\b",
            text
        )
        if time_match:
            return (
                time_match.group(1)
                .upper()
                .replace("AM", " AM")
                .replace("PM", " PM")
                .replace("  ", " ")
                .strip()
            )

        return ""

    def _extract_reason(self, text: str, parameters: Dict[str, Any]) -> str:
        """Extract reason for appointment."""
        if parameters.get("reason"):
            return parameters["reason"]

        text_lower = text.lower()
        if " for " in text_lower:
            reason = text.split(" for ", 1)[1].strip()
            if reason:
                return reason

        return "General consultation"

    def _extract_appointment_id(self, text: str, parameters: Dict[str, Any]) -> str:
        """Extract appointment ID such as A001 or APT20260501100000."""
        if parameters.get("appointment_id"):
            return str(parameters["appointment_id"]).upper().strip()

        match = re.search(r"\b(?:APT\d+|A\d{3,})\b", text.upper())
        if match:
            return match.group(0)

        return ""

    # -------------------------------------------------------------------------
    # Intent classification
    # -------------------------------------------------------------------------
    def classify_intent(
        self,
        user_message: str,
        context: Dict[str, Any] = None
    ) -> Tuple[Intent, Dict[str, Any]]:
        """
        Classify the user's intent using rule-based checks first,
        then LLM fallback.
        """
        text = user_message.lower().strip()

        # Rule-based overrides
        if text in ["hi", "hello", "hey", "good morning", "good afternoon"]:
            return Intent.GREETING, {"raw_message": user_message}

        if text in ["help", "what can you do", "what can you help with"]:
            return Intent.HELP, {"raw_message": user_message}

        if any(word in text for word in ["confirm", "confirmation", "confirming"]):
            return Intent.CONFIRM_APPOINTMENT, {"raw_message": user_message}

        # Avoid misrouting cancellation policy questions
        if "cancel" in text and "policy" not in text:
            return Intent.CANCEL_APPOINTMENT, {"raw_message": user_message}

        if any(phrase in text for phrase in ["show my appointments", "my appointments", "upcoming appointments"]):
            return Intent.VIEW_APPOINTMENTS, {"raw_message": user_message}

        if any(word in text for word in ["available", "availability", "slots", "free times"]):
            return Intent.CHECK_AVAILABILITY, {"raw_message": user_message}

        if any(word in text for word in ["book", "schedule", "make an appointment"]):
            return Intent.BOOK_APPOINTMENT, {"raw_message": user_message}

        # Patient medication lookup vs medical information search
        if any(word in text for word in ["medication", "medications", "medicine", "prescriptions"]):
            if any(phrase in text for phrase in ["what is", "tell me about", "dosage", "side effect", "how to take"]):
                return Intent.SEARCH_MEDICAL_INFO, {"raw_message": user_message}
            return Intent.VIEW_MEDICATIONS, {"raw_message": user_message}

        if any(word in text for word in ["lab", "labs", "test results", "blood work"]):
            # If it's clearly preparation/info, route to search
            if any(phrase in text for phrase in ["prepare", "preparation", "how do i prepare", "before the test"]):
                return Intent.SEARCH_MEDICAL_INFO, {"raw_message": user_message}
            return Intent.VIEW_LAB_RESULTS, {"raw_message": user_message}

        if any(word in text for word in ["diagnosis", "diagnoses", "conditions", "condition"]):
            return Intent.VIEW_DIAGNOSES, {"raw_message": user_message}

        if any(word in text for word in ["medical history", "records", "health summary", "summary of my health", "visit history"]):
            if "summary" in text:
                return Intent.GET_PATIENT_SUMMARY, {"raw_message": user_message}
            return Intent.VIEW_RECORDS, {"raw_message": user_message}

        # Expanded search routing for RAG pipeline
        if any(phrase in text for phrase in [
            "what is",
            "tell me about",
            "latest treatment",
            "treatment methods",
            "health information",
            "cancellation policy",
            "after hours",
            "billing policy",
            "insurance policy",
            "refill policy",
            "how do i prepare",
            "blood test",
            "telehealth",
            "vaccination",
            "vaccine",
            "referral process",
            "dosage",
            "side effects",
            "symptoms of",
            "causes of"
        ]):
            return Intent.SEARCH_MEDICAL_INFO, {"raw_message": user_message}

        classification_prompt = f"""
Classify the following user message into one of these intents:
- GREETING
- BOOK_APPOINTMENT
- CANCEL_APPOINTMENT
- CONFIRM_APPOINTMENT
- VIEW_APPOINTMENTS
- CHECK_AVAILABILITY
- VIEW_RECORDS
- VIEW_MEDICATIONS
- VIEW_LAB_RESULTS
- VIEW_DIAGNOSES
- GET_PATIENT_SUMMARY
- SEARCH_MEDICAL_INFO
- HELP
- UNKNOWN

Extract relevant parameters:
- doctor_name
- specialisation
- date
- time
- reason
- appointment_id

User message: "{user_message}"

Respond in this exact format:
INTENT: <intent_name>
PARAMETERS: {{"key": "value"}}
"""
        try:
            response = self.llm.invoke(classification_prompt)
            response_text = response.content
        except Exception:
            return Intent.UNKNOWN, {"raw_message": user_message}

        intent = Intent.UNKNOWN
        parameters = {"raw_message": user_message}

        for line in response_text.split("\n"):
            if line.startswith("INTENT:"):
                intent_str = line.replace("INTENT:", "").strip().upper()
                try:
                    intent = Intent[intent_str]
                except KeyError:
                    intent = Intent.UNKNOWN
            elif line.startswith("PARAMETERS:"):
                param_str = line.replace("PARAMETERS:", "").strip()
                try:
                    parsed = json.loads(param_str)
                    if isinstance(parsed, dict):
                        parameters.update(parsed)
                except Exception:
                    pass

        return intent, parameters

    # -------------------------------------------------------------------------
    # Routing
    # -------------------------------------------------------------------------
    def route_to_agent(
        self,
        intent: Intent,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route the request to the appropriate specialist agent."""
        patient_id = context.get("patient_id", "P001")
        raw_message = parameters.get("raw_message", "")

        # ---------------------------------------------------------------------
        # Appointment booking
        # ---------------------------------------------------------------------
        if intent == Intent.BOOK_APPOINTMENT:
            specialisation = self._infer_specialisation(raw_message, parameters)
            date_value = self._normalise_date(raw_message, parameters)
            time_value = self._normalise_time(raw_message, parameters)
            reason = self._extract_reason(raw_message, parameters)

            if not specialisation and not parameters.get("doctor_id"):
                return {
                    "success": False,
                    "message": (
                        "Please specify a doctor or specialisation, such as "
                        "cardiologist, neurologist, nephrologist, or psychiatrist."
                    ),
                    "agent": "appointment"
                }

            doctor_id = parameters.get("doctor_id")
            doctor = None

            if not doctor_id:
                doctor_result = self.appointment_agent.process({
                    "action": "find_doctor",
                    "parameters": {
                        "specialisation": specialisation
                    }
                }, context)

                if not doctor_result.get("success"):
                    return doctor_result

                doctors = doctor_result.get("data", {}).get("doctors", [])
                if not doctors:
                    return {
                        "success": False,
                        "message": f"I couldn't find a doctor for {specialisation}.",
                        "agent": "appointment"
                    }

                doctor = doctors[0]
                doctor_id = doctor["doctor_id"]

            if date_value and time_value:
                return self.appointment_agent.process({
                    "action": "book",
                    "parameters": {
                        "patient_id": patient_id,
                        "doctor_id": doctor_id,
                        "date": date_value,
                        "time": time_value,
                        "reason": reason
                    }
                }, context)

            slots_result = self.appointment_agent.process({
                "action": "get_slots",
                "parameters": {
                    "doctor_id": doctor_id
                }
            }, context)

            if doctor:
                slots_result["data"] = slots_result.get("data", {})
                slots_result["data"]["doctor"] = doctor

            return slots_result

        # ---------------------------------------------------------------------
        # Availability
        # ---------------------------------------------------------------------
        if intent == Intent.CHECK_AVAILABILITY:
            specialisation = self._infer_specialisation(raw_message, parameters)
            doctor_id = parameters.get("doctor_id")

            if not doctor_id and specialisation:
                doctor_result = self.appointment_agent.process({
                    "action": "find_doctor",
                    "parameters": {
                        "specialisation": specialisation
                    }
                }, context)
                doctors = doctor_result.get("data", {}).get("doctors", [])
                if doctors:
                    doctor_id = doctors[0]["doctor_id"]

            if not doctor_id:
                doctor_id = "D001"

            return self.appointment_agent.process({
                "action": "get_slots",
                "parameters": {
                    "doctor_id": doctor_id
                }
            }, context)

        # ---------------------------------------------------------------------
        # Confirmation or cancellation
        # ---------------------------------------------------------------------
        if intent == Intent.CONFIRM_APPOINTMENT:
            appointment_id = self._extract_appointment_id(raw_message, parameters)
            if not appointment_id:
                return {
                    "success": False,
                    "message": "Please provide the appointment ID to confirm, for example: Confirm appointment A001.",
                    "agent": "appointment"
                }
            return {
                "success": True,
                "message": f"Appointment {appointment_id} is confirmed/scheduled in your appointment list.",
                "agent": "appointment"
            }

        if intent == Intent.CANCEL_APPOINTMENT:
            appointment_id = self._extract_appointment_id(raw_message, parameters)
            if not appointment_id:
                return {
                    "success": False,
                    "message": (
                        "Please provide the appointment ID to cancel. "
                        "For example: Cancel appointment A001."
                    ),
                    "agent": "appointment"
                }
            return self.appointment_agent.process({
                "action": "cancel",
                "parameters": {
                    "appointment_id": appointment_id
                }
            }, context)

        # ---------------------------------------------------------------------
        # View appointments
        # ---------------------------------------------------------------------
        if intent == Intent.VIEW_APPOINTMENTS:
            return self.appointment_agent.process({
                "action": "list",
                "parameters": {
                    "patient_id": patient_id
                }
            }, context)

        # ---------------------------------------------------------------------
        # Records
        # ---------------------------------------------------------------------
        if intent == Intent.VIEW_RECORDS:
            return self.records_agent.process({
                "action": "get_medical_history",
                "parameters": {
                    **parameters,
                    "patient_id": patient_id
                }
            }, context)

        if intent == Intent.VIEW_MEDICATIONS:
            return self.records_agent.process({
                "action": "get_medications",
                "parameters": {
                    **parameters,
                    "patient_id": patient_id
                }
            }, context)

        if intent == Intent.VIEW_LAB_RESULTS:
            return self.records_agent.process({
                "action": "get_lab_results",
                "parameters": {
                    **parameters,
                    "patient_id": patient_id
                }
            }, context)

        if intent == Intent.VIEW_DIAGNOSES:
            return self.records_agent.process({
                "action": "get_diagnoses",
                "parameters": {
                    **parameters,
                    "patient_id": patient_id
                }
            }, context)

        if intent == Intent.GET_PATIENT_SUMMARY:
            return self.records_agent.process({
                "action": "get_summary",
                "parameters": {
                    **parameters,
                    "patient_id": patient_id
                }
            }, context)

        # ---------------------------------------------------------------------
        # Search/info
        # ---------------------------------------------------------------------
        if intent == Intent.SEARCH_MEDICAL_INFO:
            return self.search_agent.process({
                "action": "search",
                "parameters": {
                    "query": raw_message,
                    "search_type": "auto"
                }
            }, context)

        # ---------------------------------------------------------------------
        # Greeting/help
        # ---------------------------------------------------------------------
        if intent == Intent.GREETING:
            patient_context = self.memory.get_patient_context(patient_id)
            name = patient_context.name if patient_context else "there"
            return {
                "success": True,
                "message": (
                    f"Hello {name}! I'm your Healthcare Assistant. I can help you with:\n"
                    f"• 📅 Booking appointments\n"
                    f"• 📋 Viewing your medical records\n"
                    f"• 💊 Checking your medications\n"
                    f"• 🧪 Reviewing lab results\n"
                    f"• ❓ Answering health questions\n"
                    f"• 🔎 Searching trusted medical and clinic information\n\n"
                    f"How can I assist you today?"
                ),
                "agent": "coordinator"
            }

        if intent == Intent.HELP:
            return {
                "success": True,
                "message": (
                    "Here's what I can help you with:\n\n"
                    "**Appointments:**\n"
                    "• Book an appointment with a cardiologist\n"
                    "• Book me with a cardiologist tomorrow at 10:00 AM for chest pain follow-up\n"
                    "• Show my appointments\n"
                    "• Cancel appointment A001\n\n"
                    "**Medical Records:**\n"
                    "• Show my medical history\n"
                    "• What are my current medications?\n"
                    "• Show my lab results\n"
                    "• Give me a summary of my health\n\n"
                    "**Medical and Clinic Search:**\n"
                    "• What is diabetes?\n"
                    "• Tell me about hypertension\n"
                    "• What is the cancellation policy?\n"
                    "• How do I prepare for a blood test?\n"
                    "• What are the after hours care options?\n"
                    "• How does telehealth work?"
                ),
                "agent": "coordinator"
            }

        return {
            "success": False,
            "message": (
                "I'm not sure how to help with that. Try asking about:\n"
                "• Booking or viewing appointments\n"
                "• Your medical records or medications\n"
                "• Lab results\n"
                "• Medical or clinic information\n\n"
                "Or type 'help' for more options."
            ),
            "agent": "coordinator"
        }

    # -------------------------------------------------------------------------
    # Response formatting
    # -------------------------------------------------------------------------
    def format_response(self, result: Dict[str, Any]) -> str:
        """Format the agent result into a user-friendly response."""
        if not result.get("success", False):
            return f"I'm sorry, {result.get('message', 'something went wrong.')}"

        message = result.get("message", "")
        data = result.get("data", {})

        if "appointments" in data:
            appointments = data["appointments"]
            if appointments:
                formatted = "📅 Your appointments:\n"
                for apt in appointments:
                    formatted += (
                        f"\n• ID: {apt.get('appointment_id', 'Unknown')} — "
                        f"{apt.get('date', 'Unknown date')} at "
                        f"{apt.get('time', 'Unknown time')} — "
                        f"{apt.get('doctor_name', apt.get('doctor', 'Doctor'))} "
                        f"({apt.get('status', 'confirmed')})"
                    )
                return formatted
            return "📅 You have no upcoming appointments."

        if "slots" in data:
            slots = data["slots"]
            if slots:
                doctor_name = slots[0].get("doctor_name", "the doctor")
                formatted = f"🕐 Available slots for {doctor_name}:\n"
                for slot in slots[:5]:
                    formatted += f"\n• {slot.get('date')} at {slot.get('time')}"
                formatted += (
                    "\n\nTo book, say: "
                    "Book this appointment on YYYY-MM-DD at HH:MM AM/PM."
                )
                return formatted
            return "🕐 No available slots found."

        if "medications" in data:
            medications = data["medications"]
            if medications:
                formatted = "💊 **Current Medications:**\n"
                for med in medications:
                    formatted += f"\n• {med.get('summary', med.get('name', 'Unknown'))}"
                return formatted
            return "💊 No current medications on file."

        if "lab_results" in data:
            labs = data.get("lab_results", [])
            if labs:
                formatted = "🧪 **Recent Lab Results:**\n"
                for lab in labs[:5]:
                    status = "⚠️" if lab.get("is_abnormal") else "✅"
                    formatted += (
                        f"\n{status} {lab.get('test_name', 'Unknown')}: "
                        f"{lab.get('value', 'N/A')} {lab.get('unit', '')}"
                    )
                if result.get("alert"):
                    formatted += f"\n\n{result['alert']}"
                return formatted
            return "🧪 No lab results on file."

        if "diagnoses" in data:
            diagnoses = data.get("diagnoses", [])
            if diagnoses:
                formatted = "🏥 **Current Diagnoses:**\n"
                for diag in diagnoses:
                    formatted += (
                        f"\n• {diag.get('name', 'Unknown')} "
                        f"({diag.get('status', 'active')})"
                    )
                return formatted
            return "🏥 No diagnoses on file."

        if "doctor" in data:
            doctor = data["doctor"]
            return (
                f"👨‍⚕️ Found: {doctor.get('name', 'Unknown')} — "
                f"{doctor.get('specialisation', 'Specialist')}"
            )

        if "full_text_summary" in data:
            return f"📋 **Patient Summary:**\n\n{data['full_text_summary']}"

        if "results" in data:
            results = data["results"]
            sources = data.get("sources_searched", [])
            formatted = f"🔎 **Search results for:** {data.get('query', 'your query')}\n"

            if sources:
                formatted += f"*Sources searched: {', '.join(sources)}*\n"

            for item in results:
                formatted += (
                    f"\n### {item.get('title', 'Untitled')}\n"
                    f"**Source:** {item.get('source', 'Trusted medical source')}\n\n"
                    f"{item.get('snippet', 'No summary available.')}\n"
                )

                url = item.get("url", "")
                if url:
                    formatted += f"\nLink: {url}\n"

            formatted += (
                "\n⚠️ This is general health information only. "
                "Please consult a healthcare professional for medical advice."
            )
            return formatted

        return message

    # -------------------------------------------------------------------------
    # Main process
    # -------------------------------------------------------------------------
    def process(self, user_message: str, patient_id: str = "P001") -> str:
        """Main entry point."""
        context = {
            "patient_id": patient_id,
            "conversation_history": self.memory.get_conversation_history(patient_id)
        }

        self.memory.add_to_conversation(patient_id, "user", user_message)
        intent, parameters = self.classify_intent(user_message, context)
        result = self.route_to_agent(intent, parameters, context)

        self.last_trace = {
            "intent": intent.value,
            "parameters": parameters,
            "agent": result.get("agent", "unknown"),
            "success": result.get("success", False),
            "message": result.get("message", "")
        }

        response = self.format_response(result)
        self.memory.add_to_conversation(patient_id, "assistant", response)
        return response


# =============================================================================
# Interactive Test
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🏥 Healthcare Assistant - Interactive Test")
    print("=" * 60)

    print("\nInitialising...")
    coordinator = CoordinatorAgent()
    patient_id = "P001"

    print(f"✅ Ready! You are logged in as Patient {patient_id}")
    print("Type 'quit' to exit")
    print("-" * 60)

    print("\n🧪 Running automated tests...\n")

    test_messages = [
        "Hello!",
        "What are my current medications?",
        "Can I see my lab results?",
        "I need to book an appointment with a cardiologist",
        "Show me my appointments",
        "What is the cancellation policy?",
        "How do I prepare for a blood test?",
        "Tell me about hypertension"
    ]

    for msg in test_messages:
        print(f"🗣 You: {msg}")
        response = coordinator.process(msg, patient_id)
        print(f"🤖 Assistant: {response}")
        print("-" * 60)

    print("\n⚫ Entering interactive mode...")
    print("Type your questions or 'quit' to exit\n")

    while True:
        try:
            user_input = input("🗣 You: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye! Take care of your health!")
                break

            if not user_input:
                continue

            response = coordinator.process(user_input, patient_id)
            print(f"🤖 Assistant: {response}")
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("-" * 60)