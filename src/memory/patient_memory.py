"""
Patient Memory Module - Manages conversation history and patient context

Based on: Agentic Healthcare Assistant Project Roadmap [2]
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ConversationMemory:
    """Stores conversation history for a session."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_recent(self, n: int = 10) -> List[Dict[str, str]]:
        """Get the n most recent messages."""
        return self.messages[-n:]
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []


@dataclass
class PatientContext:
    """Stores patient-specific context information."""
    patient_id: str
    name: str
    allergies: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    last_visit: Optional[str] = None


class MemoryManager:
    """
    Singleton manager for patient memory and conversation history.
    
    Handles:
    - Short-term conversation memory
    - Patient context storage
    - Memory retrieval and updates
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
        self._patient_contexts: Dict[str, PatientContext] = {}
        self._initialized = True
        
        # Load mock patient data
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock patient context for testing."""
        # Patient P001 - Sarah
        self._patient_contexts["P001"] = PatientContext(
            patient_id="P001",
            name="Sarah Johnson",
            allergies=["Penicillin", "Sulfa drugs"],
            current_medications=["Lisinopril 10mg", "Metformin 500mg"],
            conditions=["Type 2 Diabetes", "Hypertension"],
            preferences={"preferred_doctor": "D001", "language": "English"},
            last_visit="2024-03-15"
        )
        
        # Patient P002 - Michael
        self._patient_contexts["P002"] = PatientContext(
            patient_id="P002",
            name="Michael Chen",
            allergies=["Latex"],
            current_medications=["Atorvastatin 20mg"],
            conditions=["High Cholesterol"],
            preferences={"preferred_time": "morning"},
            last_visit="2024-02-28"
        )
        
        # Patient P003 - Emily
        self._patient_contexts["P003"] = PatientContext(
            patient_id="P003",
            name="Emily Williams",
            allergies=[],
            current_medications=["Sertraline 50mg", "Vitamin D"],
            conditions=["Anxiety", "Vitamin D Deficiency"],
            preferences={"contact_method": "email"},
            last_visit="2024-03-01"
        )
    
    def add_to_conversation(self, patient_id: str, role: str, content: str):
        """
        Add a message to the conversation history.
        
        Args:
            patient_id: The patient's ID
            role: Either 'user' or 'assistant'
            content: The message content
        """
        if patient_id not in self._conversations:
            self._conversations[patient_id] = []
        
        self._conversations[patient_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages to prevent memory overflow
        if len(self._conversations[patient_id]) > 20:
            self._conversations[patient_id] = self._conversations[patient_id][-20:]
    
    def get_conversation_history(self, patient_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get recent conversation history for a patient.
        
        Args:
            patient_id: The patient's ID
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        if patient_id not in self._conversations:
            return []
        return self._conversations[patient_id][-limit:]
    
    def get_patient_context(self, patient_id: str) -> Optional[PatientContext]:
        """
        Get the context for a specific patient.
        
        Args:
            patient_id: The patient's ID
            
        Returns:
            PatientContext or None if not found
        """
        return self._patient_contexts.get(patient_id)
    
    def update_patient_context(self, patient_id: str, **kwargs):
        """
        Update patient context with new information.
        
        Args:
            patient_id: The patient's ID
            **kwargs: Fields to update
        """
        if patient_id in self._patient_contexts:
            context = self._patient_contexts[patient_id]
            for key, value in kwargs.items():
                if hasattr(context, key):
                    setattr(context, key, value)
    
    def clear_conversation(self, patient_id: str):
        """Clear conversation history for a patient."""
        if patient_id in self._conversations:
            self._conversations[patient_id] = []
    
    def get_context_summary(self, patient_id: str) -> str:
        """
        Get a text summary of patient context for LLM prompts.
        
        Args:
            patient_id: The patient's ID
            
        Returns:
            Formatted context string
        """
        context = self.get_patient_context(patient_id)
        if not context:
            return "No patient context available."
        
        summary = f"""
Patient: {context.name} (ID: {context.patient_id})
Allergies: {', '.join(context.allergies) if context.allergies else 'None known'}
Current Medications: {', '.join(context.current_medications) if context.current_medications else 'None'}
Conditions: {', '.join(context.conditions) if context.conditions else 'None'}
Last Visit: {context.last_visit or 'Unknown'}
"""
        return summary.strip()


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🧠 Memory Manager Test")
    print("=" * 50)
    
    # Get singleton instance
    memory = MemoryManager()
    
    # Test patient context
    print("\n📋 Patient Context for P001:")
    context = memory.get_patient_context("P001")
    if context:
        print(f"   Name: {context.name}")
        print(f"   Allergies: {context.allergies}")
        print(f"   Medications: {context.current_medications}")
    
    # Test conversation memory
    print("\n💬 Testing conversation memory...")
    memory.add_to_conversation("P001", "user", "Hello, I need to book an appointment")
    memory.add_to_conversation("P001", "assistant", "I'd be happy to help you book an appointment!")
    memory.add_to_conversation("P001", "user", "I need to see a cardiologist")
    
    history = memory.get_conversation_history("P001")
    print(f"   Conversation has {len(history)} messages")
    for msg in history:
        print(f"   [{msg['role']}]: {msg['content'][:50]}...")
    
    # Test context summary
    print("\n📝 Context Summary:")
    print(memory.get_context_summary("P001"))
    
    print("\n" + "=" * 50)
    print("✅ Memory manager test complete!")
    print("=" * 50)