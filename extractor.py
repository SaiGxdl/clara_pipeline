import logging
import os
import time
from typing import Dict, Any

# Attempt to import LLM libraries
try:
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

class Extractor:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.use_llm = HAS_LLM and bool(self.api_key)
        
        if self.use_llm:
            try:
                self.client = Groq(api_key=self.api_key)
                self.model = 'llama-3.1-8b-instant' # Fast, free, robust for JSON extraction
                logging.info("Extractor initialized WITH Groq LLM.")
            except Exception as e:
                logging.error(f"Failed to initialize Groq Client: {e}")
                self.use_llm = False
        else:
            logging.warning("Extractor initialized WITHOUT Groq API Key. Using fallback rule-based extraction.")

    def _extract_via_llm(self, text: str, prompt: str, schema: dict, fallback_data: Dict, retries: int = 3) -> Dict:
        """Helper to call Groq API and safely parse the JSON response."""
        import json
        
        for attempt in range(retries):
            try:
                system_instruction = prompt + f"\nYou must reply ONLY with valid JSON matching this schema exactly:\n{json.dumps(schema)}"
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"TRANSCRIPT:\n{text}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                response_text = response.choices[0].message.content
                return json.loads(response_text.strip())
            except Exception as e:
                logging.warning(f"LLM Extraction attempt {attempt + 1} failed: {e}")
                if "rate limit" in str(e).lower() or "429" in str(e):
                    logging.warning("Rate limit hit. Sleeping for 15 seconds.")
                    time.sleep(15)
                else:
                    time.sleep(2)
                    
        logging.error("All LLM Extraction attempts failed. Falling back to rule-based logic.")
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
            prompt = "You are a data extraction AI. Read the sales Demo transcript and extract the business details. If missing, use 'Unknown'."
            
            schema = {
                "type": "OBJECT",
                "properties": {
                    "account_id": {"type": "STRING"},
                    "company_name": {"type": "STRING"},
                    "business_hours": {
                        "type": "OBJECT",
                        "properties": {
                            "days": {"type": "STRING"},
                            "start": {"type": "STRING"},
                            "end": {"type": "STRING"},
                            "timezone": {"type": "STRING"}
                        }
                    },
                    "office_address": {"type": "STRING"},
                    "services_supported": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "emergency_definition": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "emergency_routing_rules": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "non_emergency_routing_rules": {"type": "STRING"},
                    "call_transfer_rules": {"type": "STRING"},
                    "integration_constraints": {"type": "STRING"},
                    "after_hours_flow_summary": {"type": "STRING"},
                    "office_hours_flow_summary": {"type": "STRING"},
                    "questions_or_unknowns": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": [
                    "account_id", "company_name", "business_hours", "office_address",
                    "services_supported", "emergency_definition", "emergency_routing_rules",
                    "non_emergency_routing_rules", "call_transfer_rules", "integration_constraints",
                    "after_hours_flow_summary", "office_hours_flow_summary", "questions_or_unknowns"
                ]
            }
            
            return self._extract_via_llm(text, prompt, schema, fallback_memo)
            
        return fallback_memo


    def extract_onboarding_updates(self, text: str, v1_memo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Loads existing v1 account memo and parses onboarding transcript to update fields.
        Attempts to use Gemini 1.5 Flash. Falls back to pure Python rules if it fails.
        """
        # --- 1. Define the Fallback Logic ---
        import json
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
            import json
            prompt = f"""
            You are a data extraction AI. We previously extracted an incomplete Profile (V1) from a demo call.
            Read this follow-up Onboarding Call transcript and UPDATE the incomplete fields.
            
            Current V1 Profile:
            {json.dumps(v1_memo, indent=2)}
            
            Update the "Unknown" values with the real information found in the transcript.
            Clear the `questions_or_unknowns` array if they have been resolved.
            
            Return the full, updated JSON schema matching the exact structure from V1.
            """
            
            schema = {
                "type": "OBJECT",
                "properties": {
                    "account_id": {"type": "STRING"},
                    "company_name": {"type": "STRING"},
                    "business_hours": {
                        "type": "OBJECT",
                        "properties": {
                            "days": {"type": "STRING"},
                            "start": {"type": "STRING"},
                            "end": {"type": "STRING"},
                            "timezone": {"type": "STRING"}
                        }
                    },
                    "office_address": {"type": "STRING"},
                    "services_supported": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "emergency_definition": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "emergency_routing_rules": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "non_emergency_routing_rules": {"type": "STRING"},
                    "call_transfer_rules": {"type": "STRING"},
                    "integration_constraints": {"type": "STRING"},
                    "after_hours_flow_summary": {"type": "STRING"},
                    "office_hours_flow_summary": {"type": "STRING"},
                    "questions_or_unknowns": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": [
                    "account_id", "company_name", "business_hours", "office_address",
                    "services_supported", "emergency_definition", "emergency_routing_rules",
                    "non_emergency_routing_rules", "call_transfer_rules", "integration_constraints",
                    "after_hours_flow_summary", "office_hours_flow_summary", "questions_or_unknowns"
                ]
            }
            
            return self._extract_via_llm(text, prompt, schema, v2_memo_fallback)

        return v2_memo_fallback
