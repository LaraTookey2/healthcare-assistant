# src/agents/search_agent.py
"""
Search Agent - Retrieves trusted medical information using RAG pipeline.

Components:
- MedlinePlus API for trusted medical content
- Local knowledge base for clinic-specific information (policies, procedures)
- Query processing and enhancement
- Response synthesis with source attribution
"""

import re
import html
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class SearchCategory(Enum):
    """Categories of searchable healthcare information."""
    MEDICAL_CONDITION = "medical_condition"
    DRUG_INFORMATION = "drug_information"
    CLINIC_POLICY = "clinic_policy"
    PROCEDURES = "procedures"
    GENERAL = "general"


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    content: str
    url: str
    source: str
    category: SearchCategory
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class LocalKnowledgeBase:
    """
    Local knowledge base for clinic-specific information.
    This supplements MedlinePlus with internal policies and procedures.
    """
    
    def __init__(self):
        self.documents = self._load_clinic_knowledge()
    
    def _load_clinic_knowledge(self) -> List[Dict[str, Any]]:
        """Load clinic-specific knowledge base."""
        return [
            # Appointment Policies
            {
                "id": "pol_001",
                "title": "Appointment Cancellation Policy",
                "content": "Patients must cancel appointments at least 24 hours in advance. "
                          "Cancellations within 24 hours may incur a $50 fee. "
                          "Emergency situations are exempt from this policy. "
                          "To cancel, call the clinic or use the patient portal.",
                "category": SearchCategory.CLINIC_POLICY,
                "keywords": ["cancel", "cancellation", "appointment", "fee", "24 hours", "reschedule"]
            },
            {
                "id": "pol_002",
                "title": "New Patient Registration",
                "content": "New patients should arrive 15 minutes early to complete registration. "
                          "Please bring: valid ID, insurance card, list of current medications, "
                          "and any relevant medical records. Registration forms are also available "
                          "online through the patient portal.",
                "category": SearchCategory.CLINIC_POLICY,
                "keywords": ["new patient", "registration", "first visit", "documents", "insurance"]
            },
            {
                "id": "pol_003",
                "title": "Prescription Refill Policy",
                "content": "Prescription refill requests require 48-72 hours to process. "
                          "Request refills through the patient portal, by phone, or through your pharmacy. "
                          "Controlled substances require an in-person appointment for refills. "
                          "Ensure you request refills before running out of medication.",
                "category": SearchCategory.CLINIC_POLICY,
                "keywords": ["prescription", "refill", "medication", "pharmacy", "controlled"]
            },
            {
                "id": "pol_004",
                "title": "After-Hours Care",
                "content": "For medical emergencies, call 111 or go to the nearest emergency department. "
                          "For urgent but non-emergency issues after hours, our nurse hotline is available "
                          "at 0800-HEALTH. Leave a message for non-urgent matters and we'll respond "
                          "the next business day.",
                "category": SearchCategory.CLINIC_POLICY,
                "keywords": ["after hours", "emergency", "urgent", "night", "weekend", "hotline"]
            },
            
            # Procedures
            {
                "id": "proc_001",
                "title": "Blood Test Preparation",
                "content": "Fasting blood tests require 8-12 hours without food (water is permitted). "
                          "Avoid alcohol for 24 hours before the test. Continue taking regular medications "
                          "unless instructed otherwise. Inform the nurse of any blood-thinning medications. "
                          "Results are typically available within 2-3 business days.",
                "category": SearchCategory.PROCEDURES,
                "keywords": ["blood test", "fasting", "laboratory", "lab", "preparation", "results"]
            },
            {
                "id": "proc_002",
                "title": "Vaccination Appointments",
                "content": "Vaccination appointments are 15-30 minutes. Please inform staff of any allergies "
                          "or previous vaccine reactions. You will be monitored for 15 minutes after vaccination. "
                          "Bring your vaccination record or immunisation booklet. "
                          "Flu vaccines are available seasonally without appointment.",
                "category": SearchCategory.PROCEDURES,
                "keywords": ["vaccine", "vaccination", "immunisation", "flu shot", "injection", "allergy"]
            },
            {
                "id": "proc_003",
                "title": "Telehealth Consultations",
                "content": "Telehealth appointments are available for suitable consultations. "
                          "You'll receive a link via email 30 minutes before your appointment. "
                          "Ensure you have a stable internet connection and a private space. "
                          "Have your medications and any relevant documents ready. "
                          "Technical issues? Call the clinic to convert to a phone consultation.",
                "category": SearchCategory.PROCEDURES,
                "keywords": ["telehealth", "video", "online", "virtual", "remote", "consultation"]
            },
            
            # Common Drug Information (supplements MedlinePlus)
            {
                "id": "drug_001",
                "title": "Paracetamol Guidelines",
                "content": "Paracetamol (acetaminophen) is used for pain and fever. "
                          "Adult dose: 500-1000mg every 4-6 hours, maximum 4000mg daily. "
                          "Do not exceed recommended dose - risk of liver damage. "
                          "Avoid alcohol while taking paracetamol. Check other medications for paracetamol content "
                          "to avoid accidental overdose.",
                "category": SearchCategory.DRUG_INFORMATION,
                "keywords": ["paracetamol", "acetaminophen", "panadol", "pain", "fever", "liver"]
            },
            {
                "id": "drug_002",
                "title": "Ibuprofen Guidelines",
                "content": "Ibuprofen is an anti-inflammatory for pain, inflammation, and fever. "
                          "Adult dose: 200-400mg every 4-6 hours, maximum 1200mg daily (over the counter). "
                          "Take with food to reduce stomach irritation. "
                          "Avoid if you have kidney problems, heart conditions, or stomach ulcers. "
                          "Not recommended during pregnancy.",
                "category": SearchCategory.DRUG_INFORMATION,
                "keywords": ["ibuprofen", "nurofen", "anti-inflammatory", "nsaid", "pain", "inflammation"]
            },
        ]
    
    def search(self, query: str, category: Optional[SearchCategory] = None, top_k: int = 3) -> List[SearchResult]:
        """Search local knowledge base."""
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        results = []
        
        for doc in self.documents:
            # Filter by category if specified
            if category and doc["category"] != category:
                continue
            
            # Calculate relevance score based on keyword matching
            keywords = set(doc["keywords"])
            title_words = set(doc["title"].lower().split())
            content_words = set(doc["content"].lower().split())
            
            # Score based on matches
            keyword_matches = len(query_terms & keywords)
            title_matches = len(query_terms & title_words)
            content_matches = len(query_terms & content_words)
            
            relevance_score = (keyword_matches * 0.4) + (title_matches * 0.3) + (content_matches * 0.1)
            
            # Boost for exact phrase matches
            if query_lower in doc["content"].lower():
                relevance_score += 0.3
            if query_lower in doc["title"].lower():
                relevance_score += 0.4
            
            if relevance_score > 0.1:
                results.append(SearchResult(
                    title=doc["title"],
                    content=doc["content"],
                    url="",  # Internal documents don't have URLs
                    source="Clinic Knowledge Base",
                    category=doc["category"],
                    relevance_score=min(relevance_score, 1.0),
                    metadata={"id": doc["id"]}
                ))
        
        # Sort by relevance and return top_k
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]


class QueryProcessor:
    """Processes and enhances user queries."""
    
    def __init__(self):
        self.query_prefixes = [
            "what is ", "what are ", "tell me about ", "explain ",
            "search medical information about ", "medical information about ",
            "symptoms of ", "what are symptoms of ", "what are the symptoms of ",
            "treatment for ", "what is the treatment for ",
            "causes of ", "what causes ", "how to ", "how do i ",
            "can i ", "should i ", "is it safe to ",
            "what is the policy for ", "policy on ", "policy for ",
        ]
        
        self.medical_synonyms = {
            "hypertension": "high blood pressure",
            "high blood pressure": "high blood pressure",
            "high cholesterol": "cholesterol",
            "type 2 diabetes": "diabetes",
            "diabetes mellitus": "diabetes",
            "heart attack": "myocardial infarction",
            "stroke": "cerebrovascular accident",
        }
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process and analyse the query."""
        original = query
        query_lower = query.lower().strip()
        
        # Remove common prefixes
        cleaned = query_lower
        for prefix in self.query_prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned.replace(prefix, "", 1).strip()
                break
        
        # Remove trailing punctuation
        cleaned = cleaned.strip(" ?.,!")
        
        # Apply synonyms
        normalised = self.medical_synonyms.get(cleaned, cleaned)
        
        # Detect intent and category
        intent = self._detect_intent(query_lower)
        category = self._detect_category(query_lower)
        
        return {
            "original_query": original,
            "cleaned_query": cleaned,
            "normalised_query": normalised,
            "intent": intent,
            "suggested_category": category,
            "search_terms": normalised
        }
    
    def _detect_intent(self, query: str) -> str:
        """Detect the intent behind the query."""
        if any(word in query for word in ["policy", "cancel", "appointment", "refill", "hours"]):
            return "policy_inquiry"
        elif any(word in query for word in ["how to prepare", "before", "preparation"]):
            return "procedure_inquiry"
        elif any(word in query for word in ["medication", "drug", "dosage", "take"]):
            return "drug_inquiry"
        elif any(word in query for word in ["symptom", "treatment", "cause", "diagnosis"]):
            return "medical_inquiry"
        else:
            return "general"
    
    def _detect_category(self, query: str) -> Optional[SearchCategory]:
        """Suggest a search category based on query content."""
        if any(word in query for word in ["policy", "cancel", "appointment", "hours", "registration"]):
            return SearchCategory.CLINIC_POLICY
        elif any(word in query for word in ["procedure", "prepare", "test", "vaccination"]):
            return SearchCategory.PROCEDURES
        elif any(word in query for word in ["medication", "drug", "medicine", "dosage", "paracetamol", "ibuprofen"]):
            return SearchCategory.DRUG_INFORMATION
        else:
            return SearchCategory.MEDICAL_CONDITION


class SearchAgent:
    """
    Medical information search agent using RAG pipeline.
    
    Combines:
    - MedlinePlus API for trusted medical content
    - Local knowledge base for clinic-specific information
    """
    
    def __init__(self):
        """Initialise the search agent."""
        self.name = "SearchAgent"
        self.medline_url = "https://wsearch.nlm.nih.gov/ws/query"
        self.local_kb = LocalKnowledgeBase()
        self.query_processor = QueryProcessor()
    
    def process(self, request: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a medical search request.
        
        Args:
            request: Request containing parameters with query
            context: Optional context from coordinator
            
        Returns:
            Response dict with search results
        """
        params = request.get("parameters", {})
        query = params.get("query", "")
        search_type = params.get("search_type", "auto")  # auto, medical, policy, local
        
        if not query:
            return {
                "success": False,
                "message": "Please provide a medical topic or question to search for.",
                "agent": self.name
            }
        
        # Process the query
        query_analysis = self.query_processor.process(query)
        search_terms = query_analysis["normalised_query"]
        intent = query_analysis["intent"]
        category = query_analysis["suggested_category"]
        
        # Determine search strategy based on intent
        if search_type == "auto":
            if intent == "policy_inquiry":
                return self._search_local_only(search_terms, SearchCategory.CLINIC_POLICY, query)
            elif intent == "procedure_inquiry":
                return self._search_combined(search_terms, query, SearchCategory.PROCEDURES)
            elif intent == "drug_inquiry":
                return self._search_combined(search_terms, query, SearchCategory.DRUG_INFORMATION)
            else:
                return self._search_combined(search_terms, query, category)
        elif search_type == "medical":
            return self._search_medline(search_terms)
        elif search_type == "policy" or search_type == "local":
            return self._search_local_only(search_terms, category, query)
        else:
            return self._search_combined(search_terms, query, category)
    
    def _search_combined(self, search_terms: str, original_query: str, 
                         category: Optional[SearchCategory] = None) -> Dict[str, Any]:
        """Search both MedlinePlus and local knowledge base."""
        all_results = []
        sources_used = []
        
        # Search local knowledge base first
        local_results = self.local_kb.search(search_terms, category=category, top_k=2)
        if local_results:
            sources_used.append("Clinic Knowledge Base")
            for result in local_results:
                all_results.append({
                    "title": result.title,
                    "snippet": result.content,
                    "url": result.url or "Internal Document",
                    "source": result.source,
                    "relevance": result.relevance_score
                })
        
        # Search MedlinePlus for medical conditions
        medline_response = self._search_medline(search_terms)
        if medline_response.get("success") and medline_response.get("data", {}).get("results"):
            sources_used.append("MedlinePlus")
            for result in medline_response["data"]["results"]:
                all_results.append({
                    "title": result["title"],
                    "snippet": result["snippet"],
                    "url": result["url"],
                    "source": result["source"],
                    "relevance": 0.8  # MedlinePlus results are authoritative
                })
        
        if not all_results:
            return {
                "success": False,
                "message": f"No results found for '{original_query}'. Try rephrasing your question.",
                "agent": self.name
            }
        
        # Sort by relevance
        all_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(all_results)} result(s) for '{original_query}'.",
            "data": {
                "query": original_query,
                "search_terms": search_terms,
                "results": all_results[:5],  # Return top 5
                "sources_searched": sources_used
            },
            "agent": self.name
        }
    
    def _search_local_only(self, search_terms: str, category: Optional[SearchCategory],
                           original_query: str) -> Dict[str, Any]:
        """Search only the local knowledge base."""
        results = self.local_kb.search(search_terms, category=category, top_k=3)
        
        if not results:
            return {
                "success": False,
                "message": f"No clinic information found for '{original_query}'. "
                          "Try asking about appointments, policies, or procedures.",
                "agent": self.name
            }
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.title,
                "snippet": result.content,
                "url": "Internal Document",
                "source": result.source
            })
        
        return {
            "success": True,
            "message": f"Found {len(results)} clinic information result(s).",
            "data": {
                "query": original_query,
                "results": formatted_results,
                "sources_searched": ["Clinic Knowledge Base"]
            },
            "agent": self.name
        }
    
    def _search_medline(self, query: str) -> Dict[str, Any]:
        """Search MedlinePlus health topics."""
        params = {
            "db": "healthTopics",
            "term": query,
            "retmax": 3
        }
        
        try:
            response = requests.get(self.medline_url, params=params, timeout=10)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "Medical search timed out. Please try again.",
                "agent": self.name
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Medical search failed: {str(e)}",
                "agent": self.name
            }
        
        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            return {
                "success": False,
                "message": "Could not parse medical search results.",
                "agent": self.name
            }
        
        results = []
        for document in root.findall(".//document"):
            title = ""
            url = ""
            snippet = ""
            
            for content in document.findall("content"):
                name = content.attrib.get("name", "")
                if name == "title":
                    title = content.text or ""
                elif name == "url":
                    url = content.text or ""
                elif name == "FullSummary":
                    snippet = content.text or ""
            
            clean_title = self._clean_html(title)
            clean_snippet = self._clean_html(snippet)
            
            if clean_title:
                results.append({
                    "title": clean_title,
                    "url": url,
                    "snippet": clean_snippet[:700] if clean_snippet else "No summary available.",
                    "source": "MedlinePlus"
                })
        
        if not results:
            return {
                "success": False,
                "message": f"No MedlinePlus results found for '{query}'.",
                "agent": self.name
            }
        
        return {
            "success": True,
            "message": f"Found {len(results)} MedlinePlus result(s) for '{query}'.",
            "data": {
                "query": query,
                "results": results,
                "sources_searched": ["MedlinePlus"]
            },
            "agent": self.name
        }
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text."""
        if not text:
            return "No summary available."
        
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    
    # Convenience methods for specific search types
    def search_policy(self, topic: str) -> Dict[str, Any]:
        """Search clinic policies."""
        return self.process({
            "parameters": {
                "query": topic,
                "search_type": "policy"
            }
        })
    
    def search_medical(self, condition: str) -> Dict[str, Any]:
        """Search medical conditions via MedlinePlus."""
        return self.process({
            "parameters": {
                "query": condition,
                "search_type": "medical"
            }
        })
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for coordinator."""
        return {
            "agent": self.name,
            "capabilities": [
                "search_medical_conditions",
                "search_drug_information",
                "search_clinic_policies",
                "search_procedures",
                "answer_health_questions"
            ],
            "supported_intents": [
                "medical_inquiry",
                "drug_inquiry",
                "policy_inquiry",
                "procedure_inquiry",
                "general"
            ]
        }


if __name__ == "__main__":
    agent = SearchAgent()
    
    print("=" * 60)
    print("SEARCH AGENT TEST")
    print("=" * 60)
    
    # Test cases
    test_queries = [
        {"query": "Tell me about hypertension"},
        {"query": "What is the cancellation policy?"},
        {"query": "How do I prepare for a blood test?"},
        {"query": "Paracetamol dosage"},
        {"query": "diabetes symptoms"},
        {"query": "after hours care"},
    ]
    
    for test in test_queries:
        print(f"\n📝 Query: {test['query']}")
        print("-" * 40)
        
        result = agent.process({"parameters": test})
        
        print(f"✅ Success: {result['success']}")
        print(f"💬 Message: {result['message']}")
        
        if result.get("data"):
            data = result["data"]
            print(f"🔍 Sources: {data.get('sources_searched', [])}")
            
            for i, res in enumerate(data.get("results", [])[:2], 1):
                print(f"\n   Result {i}: {res['title']}")
                print(f"   Source: {res['source']}")
                snippet = res['snippet'][:150] + "..." if len(res['snippet']) > 150 else res['snippet']
                print(f"   Snippet: {snippet}")
        
        print("=" * 60)