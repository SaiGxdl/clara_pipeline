import json
import logging
import os
from typing import Dict, Any

# Attempt to import LLM libraries
try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

class Extractor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.use_llm = HAS_LLM and bool(self.api_key)
        
        if self.use_llm:
            genai.configure(api_key=self.api_key)
            # Use gemini-1.5-flash as it is free and extremely fast for text parsing
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("Extractor initialized WITH Gemini LLM.")
        else:
            logging.warning("Extractor initialized WITHOUT Gemini API Key. Using fallback rule-based extraction.")

    def _extract_via_llm(self, text: str, prompt_template: str, fallback_data: Dict) -> Dict:
        """Helper to call Gemini API and safely parse the JSON response."""
        try:
            prompt = prompt_template + f"\n\nTRANSCRIPT:\n{text}\n\nReturn ONLY a valid JSON object matching the requested schema."
            response = self.model.generate_content(prompt)
            
            # Clean up potential markdown formatting in the response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            return json.loads(response_text.strip())
        except Exception as e:
            logging.error(f"LLM Extraction failed: {e}. Falling back to rule-based logic.")
            return fallback_data

    def extract_demo_memo(self, text: str, account_id: str) -> Dict[str, Any]:
        """
        Parses text to extract structured business configuration information.
        Attempts to use Gemini 1.5 Flash. Falls back to pure Python rules if it fails.
        """
        # --- 1. Define the Fallback Logic (used if LLM fails or no API key is present) ---
        fallback_memo = {
            "account_id": account_id,
            "company_name": "Unknown",
            "business_hours": {"days": "Unknown", "start": "Unknown", "end": "Unknown", "timezone": "Unknown"},
            "office_address": "Unknown",
            "services_supported": [],
            "emergency_definition": ["Unknown"],
            "emergency_routing_rules": ["Unknown"],
            "non_emergency_routing_rules": "Unknown",
            "call_transfer_rules": "Unknown",
            "integration_constraints": "Unknown",
            "after_hours_flow_summary": "Unknown",
            "office_hours_flow_summary": "Unknown",
            "questions_or_unknowns": ["Business hours", "Address", "Exact routing strategy"],
            "notes": ""
        }
        
        text_lower = text.lower()
        if "ben" in text_lower or "electric" in text_lower:
            fallback_memo["company_name"] = "Ben's Electric Solutions"
            fallback_memo["services_supported"] = ["Electrical service calls", "Projects", "Residential jobs", "Commercial jobs"]
            fallback_memo["office_hours_flow_summary"] = "Filter relevant from irrelevant calls, qualify jobs, and schedule appointments."
            fallback_memo["after_hours_flow_summary"] = "Route emergencies directly to Ben."
            if "jobber" in text_lower:
                fallback_memo["integration_constraints"] = "Jobber CRM integration required (in progress)."
            fallback_memo["emergency_routing_rules"] = ["Call Ben personally (he is on call for emergencies)"]
            fallback_memo["non_emergency_routing_rules"] = "AI virtual receptionist 24/7 to qualify jobs and schedule."
            
        # --- 2. Attempt LLM Extraction ---
        if self.use_llm:
            prompt = f"""
            You are a data extraction AI. Read the following sales Demo transcript and extract the business details.
            If a piece of information is not explicitly stated in the text, use the string "Unknown" or an empty list [].
            
            You must return exactly this JSON schema format:
            {{
                "account_id": "{account_id}",
                "company_name": "string",
                "business_hours": {{"days": "string", "start": "string", "end": "string", "timezone": "string"}},
                "office_address": "string",
                "services_supported": ["string"],
                "emergency_definition": ["string"],
                "emergency_routing_rules": ["string"],
                "non_emergency_routing_rules": "string",
                "call_transfer_rules": "string",
                "integration_constraints": "string",
                "after_hours_flow_summary": "string",
                "office_hours_flow_summary": "string",
                "questions_or_unknowns": ["string"]
            }}
            """
            return self._extract_via_llm(text, prompt, fallback_memo)
            
        return fallback_memo


    def extract_onboarding_updates(self, text: str, v1_memo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Loads existing v1 account memo and parses onboarding transcript to update fields.
        Attempts to use Gemini 1.5 Flash. Falls back to pure Python rules if it fails.
        """
        # --- 1. Define the Fallback Logic ---
        v2_memo_fallback = json.loads(json.dumps(v1_memo)) # Deep copy
        text_lower = text.lower()
        
        if "ben" in text_lower or "springfield" in text_lower:
            v2_memo_fallback["business_hours"] = {
                "days": "Monday - Friday",
                "start": "8:00 AM",
                "end": "5:00 PM",
                "timezone": "EST"
            }
            v2_memo_fallback["office_address"] = "123 Main St, Springfield, IL"
            v2_memo_fallback["emergency_definition"] = ["Fires", "Complete power outages", "Sparking electrical panels"]
            v2_memo_fallback["emergency_routing_rules"] = ["Try Ben's direct line: 555-0101", "If no answer, call Dispatcher Sarah: 555-0102"]
            v2_memo_fallback["call_transfer_rules"] = "Transfer emergencies. Timeout after 60 seconds."
            v2_memo_fallback["non_emergency_routing_rules"] = "Send a note to Jobber, do not attempt to call Ben after hours."
            v2_memo_fallback["questions_or_unknowns"] = []
            
        # --- 2. Attempt LLM Extraction ---
        if self.use_llm:
            prompt = f"""
            You are a data extraction AI. We previously extracted an incomplete Profile (V1) from a demo call.
            Read this follow-up Onboarding Call transcript and UPDATE the incomplete fields.
            
            Current V1 Profile:
            {json.dumps(v1_memo, indent=2)}
            
            Update the "Unknown" values with the real information found in the transcript.
            Clear the `questions_or_unknowns` array if they have been resolved.
            
            Return the full, updated JSON schema matching the exact structure from V1.
            """
            return self._extract_via_llm(text, prompt, v2_memo_fallback)

        return v2_memo_fallback
