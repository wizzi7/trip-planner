from typing import Dict, Any
from backend.models import UserInput
from backend.agents.base import BaseAgent

class PreferencesAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PreferencesAgent")

    async def run(self, user_input: UserInput) -> Dict[str, Any]:
        print(f"[{self.name}] Extracting constraints for {user_input.destination}")
        
        system_prompt = (
            "You are an expert Travel Analyst. Extract key constraints from user input. "
            "Return JSON: { \"interest_tags\": [], \"dietary_restrictions\": [], \"accessibility\": \"string\" }"
        )
        
        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Extra Req: {user_input.extra_req}\n"
            f"Pace: {user_input.pace}\n"
            f"Guests: {user_input.guests}\n"
        )

        constraints = self.call_openrouter(system_prompt, user_prompt, json_response=True)
        
        if constraints:
            print(f"[{self.name}] Extracted: {constraints}")
            return constraints

        return {"interest_tags": [], "dietary_restrictions": []}
