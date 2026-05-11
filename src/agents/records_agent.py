"""
Records Agent - Handles patient record retrieval and management

This agent uses real tools to:
- Retrieve patient profiles
- Get medical history
- View diagnoses, medications, and lab results
- Generate patient summaries

Based on: Agentic Healthcare Assistant Project Roadmap [2]
"""

from typing import Dict, Any, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.tools.records_tools import (
    get_patient_profile,
    search_patients,
    get_all_patients,
    get_medical_history,
    get_patient_diagnoses,
    get_patient_medications,
    get_patient_lab_results,
    get_patient_summary
)


class RecordsAgent:
    """
    Agent responsible for medical records tasks.
    
    Capabilities:
    - Retrieve patient profiles
    - Search for patients
    - Get medical history
    - View diagnoses, medications, lab results
    - Generate comprehensive patient summaries
    """
    
    def __init__(self):
        self.name = "Records Agent"
        self.tools = {
            "profile": get_patient_profile,
            "search": search_patients,
            "all_patients": get_all_patients,
            "history": get_medical_history,
            "diagnoses": get_patient_diagnoses,
            "medications": get_patient_medications,
            "labs": get_patient_lab_results,
            "summary": get_patient_summary
        }
    
    def process(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a records-related task.
        
        Args:
            task: Task details from coordinator including:
                - action: The action to perform
                - parameters: Action-specific parameters
            context: Additional context (patient_id, conversation history)
        
        Returns:
            Response dictionary with results
        """
        action = task.get("action", "").lower()
        params = task.get("parameters", {})
        context = context or {}
        
        # Get patient_id from context if not in params
        patient_id = params.get("patient_id") or context.get("patient_id")
        
        try:
            # Route to appropriate handler
            # UPDATED: Added more action name variants for compatibility with Coordinator
            if action in ["profile", "get_profile", "patient_info", "patient_details", 
                          "get_patient_profile", "get_patient_info"]:
                return self._get_profile(patient_id)
            
            elif action in ["search", "search_patient", "find_patient", "search_patients"]:
                return self._search_patients(params)
            
            elif action in ["list_patients", "all_patients", "show_patients", "get_all_patients"]:
                return self._list_all_patients()
            
            elif action in ["history", "medical_history", "records", "past_records",
                            "get_medical_history", "get_history", "get_records"]:
                return self._get_history(patient_id, params)
            
            elif action in ["diagnoses", "conditions", "get_diagnoses", 
                            "get_conditions", "get_patient_diagnoses"]:
                return self._get_diagnoses(patient_id, params)
            
            elif action in ["medications", "meds", "prescriptions", "get_medications",
                            "get_meds", "get_prescriptions", "get_current_medications",
                            "current_medications"]:
                return self._get_medications(patient_id, params)
            
            elif action in ["labs", "lab_results", "test_results", "get_labs",
                            "get_lab_results", "get_test_results", "get_patient_lab_results"]:
                return self._get_lab_results(patient_id, params)
            
            elif action in ["summary", "patient_summary", "overview", "full_summary",
                            "get_summary", "get_patient_summary", "get_full_summary"]:
                return self._get_summary(patient_id)
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}",
                    "available_actions": [
                        "profile/get_patient_profile", 
                        "search/search_patients", 
                        "history/get_medical_history", 
                        "diagnoses/get_diagnoses",
                        "medications/get_medications", 
                        "labs/get_lab_results", 
                        "summary/get_patient_summary"
                    ]
                }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing records request: {str(e)}",
                "error": str(e)
            }
    
    def _get_profile(self, patient_id: Optional[str]) -> Dict[str, Any]:
        """Get patient profile."""
        if not patient_id:
            return {
                "success": False,
                "message": "Please specify which patient's profile to retrieve.",
                "hint": "Provide a patient_id (e.g., P001) or search by name."
            }
        
        result = get_patient_profile(patient_id)
        
        response = {
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
        
        if result.success:
            response["follow_up"] = "Would you like to see their medical history, medications, or lab results?"
        
        return response
    
    def _search_patients(self, params: Dict) -> Dict[str, Any]:
        """Search for patients by name."""
        name = params.get("name") or params.get("query") or params.get("search")
        
        if not name:
            return {
                "success": False,
                "message": "Please provide a name to search for.",
                "hint": "Example: search for 'Smith' or 'John'"
            }
        
        result = search_patients(name)
        
        response = {
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
        
        if result.success and result.data.get("patients"):
            response["follow_up"] = "Which patient would you like more information about?"
        
        return response
    
    def _list_all_patients(self) -> Dict[str, Any]:
        """List all patients."""
        result = get_all_patients()
        
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data,
            "follow_up": "Which patient would you like to view?"
        }
    
    def _get_history(self, patient_id: Optional[str], params: Dict) -> Dict[str, Any]:
        """Get patient's medical history."""
        if not patient_id:
            return {
                "success": False,
                "message": "Please specify which patient's history to retrieve.",
                "hint": "Provide a patient_id (e.g., P001)"
            }
        
        limit = params.get("limit", 5)
        result = get_medical_history(patient_id, limit)
        
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
    
    def _get_diagnoses(self, patient_id: Optional[str], params: Dict) -> Dict[str, Any]:
        """Get patient's diagnoses."""
        if not patient_id:
            return {
                "success": False,
                "message": "Please specify which patient's diagnoses to retrieve.",
                "hint": "Provide a patient_id (e.g., P001)"
            }
        
        active_only = params.get("active_only", True)
        result = get_patient_diagnoses(patient_id, active_only)
        
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
    
    def _get_medications(self, patient_id: Optional[str], params: Dict) -> Dict[str, Any]:
        """Get patient's medications."""
        if not patient_id:
            return {
                "success": False,
                "message": "Please specify which patient's medications to retrieve.",
                "hint": "Provide a patient_id (e.g., P001)"
            }
        
        active_only = params.get("active_only", True)
        result = get_patient_medications(patient_id, active_only)
        
        return {
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
    
    def _get_lab_results(self, patient_id: Optional[str], params: Dict) -> Dict[str, Any]:
        """Get patient's lab results."""
        if not patient_id:
            return {
                "success": False,
                "message": "Please specify which patient's lab results to retrieve.",
                "hint": "Provide a patient_id (e.g., P001)"
            }
        
        limit = params.get("limit", 10)
        result = get_patient_lab_results(patient_id, limit)
        
        response = {
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
        
        # Highlight if there are abnormal results
        if result.data and result.data.get("abnormal_count", 0) > 0:
            response["alert"] = f"⚠️ {result.data['abnormal_count']} abnormal result(s) detected"
        
        return response
    
    def _get_summary(self, patient_id: Optional[str]) -> Dict[str, Any]:
        """Get comprehensive patient summary."""
        if not patient_id:
            return {
                "success": False,
                "message": "Please specify which patient's summary to generate.",
                "hint": "Provide a patient_id (e.g., P001)"
            }
        
        result = get_patient_summary(patient_id)
        
        response = {
            "success": result.success,
            "message": result.message,
            "data": result.data
        }
        
        # Add alerts if present
        if result.data:
            alerts = result.data.get("alerts", {})
            if alerts.get("allergies") or alerts.get("critical_alerts"):
                response["alert"] = "⚠️ This patient has allergies or critical alerts - please review!"
        
        return response


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 RECORDS AGENT TEST")
    print("=" * 60)
    
    agent = RecordsAgent()
    
    # Test 1: Get patient profile (using Coordinator-style action name)
    print("\n👤 Test 1: Getting patient profile for P001...")
    result = agent.process({
        "action": "get_patient_profile",  # Coordinator-style name
        "parameters": {}
    }, context={"patient_id": "P001"})
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("data"):
        print(f"   Name: {result['data'].get('name')}")
        print(f"   Allergies: {result['data'].get('allergies')}")
    
    # Test 2: Search patients
    print("\n🔍 Test 2: Searching for 'Williams'...")
    result = agent.process({
        "action": "search",
        "parameters": {"name": "Williams"}
    })
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    
    # Test 3: Get medical history (using Coordinator-style action name)
    print("\n📋 Test 3: Getting medical history for P001...")
    result = agent.process({
        "action": "get_medical_history",  # Coordinator-style name
        "parameters": {"limit": 3}
    }, context={"patient_id": "P001"})
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    
    # Test 4: Get medications (using Coordinator-style action name)
    print("\n💊 Test 4: Getting medications for P001...")
    result = agent.process({
        "action": "get_medications",  # Coordinator-style name
        "parameters": {}
    }, context={"patient_id": "P001"})
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("data", {}).get("medications"):
        for med in result["data"]["medications"][:3]:
            print(f"   • {med.get('summary', med.get('name', 'Unknown'))}")
    
    # Test 5: Get lab results (using Coordinator-style action name)
    print("\n🧪 Test 5: Getting lab results for P001...")
    result = agent.process({
        "action": "get_lab_results",  # Coordinator-style name
        "parameters": {}
    }, context={"patient_id": "P001"})
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result.get("alert"):
        print(f"   {result['alert']}")
    
    # Test 6: Get comprehensive summary
    print("\n📊 Test 6: Getting full summary for P001...")
    result = agent.process({
        "action": "get_summary",
        "parameters": {}
    }, context={"patient_id": "P001"})
    print(f"   Success: {result['success']}")
    if result.get("alert"):
        print(f"   {result['alert']}")
    if result.get("data", {}).get("full_text_summary"):
        print(f"\n   {result['data']['full_text_summary'][:300]}...")
    
    print("\n" + "=" * 60)
    print("✅ Records agent test complete!")
    print("=" * 60)