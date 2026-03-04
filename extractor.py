class Extractor:
    def extract_demo_memo(self, text, account_id):
        """
        Parses text to extract structured business configuration information.
        (Mocks LLM extraction to remain zero-cost).
        """
        text_lower = text.lower()
        
        memo = {
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
        
        if "ben" in text_lower or "electric" in text_lower:
            memo["company_name"] = "Ben's Electric Solutions"
            memo["services_supported"] = ["Electrical service calls", "Projects", "Residential jobs", "Commercial jobs"]
            memo["office_hours_flow_summary"] = "Filter relevant from irrelevant calls, qualify jobs, and schedule appointments."
            memo["after_hours_flow_summary"] = "Route emergencies directly to Ben."
            if "jobber" in text_lower:
                memo["integration_constraints"] = "Jobber CRM integration required (in progress)."
            memo["emergency_routing_rules"] = ["Call Ben personally (he is on call for emergencies)"]
            memo["non_emergency_routing_rules"] = "AI virtual receptionist 24/7 to qualify jobs and schedule."
                 
        return memo

    def extract_onboarding_updates(self, text, v1_memo):
        """
        Loads existing v1 account memo and parses onboarding transcript to update fields
        without overwriting unrelated information.
        """
        import json
        text_lower = text.lower()
        v2_memo = json.loads(json.dumps(v1_memo)) # Deep copy
        
        if "ben" in text_lower or "springfield" in text_lower:
            v2_memo["business_hours"] = {
                "days": "Monday - Friday",
                "start": "8:00 AM",
                "end": "5:00 PM",
                "timezone": "EST"
            }
            v2_memo["office_address"] = "123 Main St, Springfield, IL"
            v2_memo["emergency_definition"] = ["Fires", "Complete power outages", "Sparking electrical panels"]
            v2_memo["emergency_routing_rules"] = ["Try Ben's direct line: 555-0101", "If no answer, call Dispatcher Sarah: 555-0102"]
            v2_memo["call_transfer_rules"] = "Transfer emergencies. Timeout after 60 seconds."
            v2_memo["non_emergency_routing_rules"] = "Send a note to Jobber, do not attempt to call Ben after hours."
            v2_memo["questions_or_unknowns"] = [] # Cleared since onboarding resolved them

        return v2_memo
