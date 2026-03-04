class AgentGenerator:
    def generate_spec(self, memo, version="v1"):
        """
        Generates a Retell Agent Draft Spec JSON based on the Account Memo.
        Ensures fields like agent_name, voice_style, system_prompt, key_variables.
        """
        return {
            "agent_name": "Clara",
            "version": version,
            "voice_style": "Professional and helpful",
            "key_variables": {
                "timezone": memo.get("business_hours", {}).get("timezone", "Unknown"),
                "business_hours": f"{memo.get('business_hours', {}).get('start', 'Unknown')} to {memo.get('business_hours', {}).get('end', 'Unknown')}",
                "address": memo.get("office_address", "Unknown"),
                "emergency_routing": memo.get("emergency_routing_rules", ["Unknown"])[0]
            },
            "system_prompt": f"You are Clara, the 24/7 AI virtual receptionist for {memo.get('company_name', 'this company')}. "
                             f"Your job is to answer calls and assist based on the following rules:\n\n"
                             f"BUSINESS HOURS FLOW:\n1. Greet the caller.\n2. Ask for the purpose.\n3. Collect name and number.\n"
                             f"4. Address their need ({memo.get('non_emergency_routing_rules', 'take a message')} ).\n"
                             f"5. Transfer if necessary. If transfer fails, apologize and promise callback.\n"
                             f"6. Ask if they need anything else, then close.\n\n"
                             f"AFTER HOURS FLOW:\n1. Greet and ask purpose.\n2. Confirm if emergency ({', '.join(memo.get('emergency_definition', []))}).\n"
                             f"3. If emergency, collect name/number/address, then attempt transfer.\n"
                             f"4. If transfer fails, apologize and assure follow-up.\n5. If non-emergency, collect details for next business day.\n"
                             f"6. Ask if anything else, close.",
            "tool_invocation_placeholders": ["transfer_call", "check_schedule"],
            "call_transfer_protocol": memo.get("call_transfer_rules", "Unknown"),
            "fallback_protocol_if_transfer_fails": "Apologize and assure follow up."
        }
