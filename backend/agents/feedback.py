from typing import Dict, Any, Tuple
from backend.models import UserInput, TripPlan
from backend.agents.base import BaseAgent

class FeedbackAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="FeedbackAgent")

    async def run(self, current_plan: TripPlan, user_input: UserInput, feedback: str) -> Tuple[UserInput, Dict[str, Any]]:
        print(f"[{self.name}] Analyzing feedback: {feedback}")
        
        system_prompt = (
            "You are a Travel Feedback Analyst. "
            "Decide how to modify UserInput based on feedback. "
            "Return JSON: { \"budget_modifier\": float (1.0 = same), \"pace_override\": \"string or null\", \"rerun_agents\": [\"list\"] }"
        )
        
        user_prompt = (
            f"Original Budget: {user_input.budget}\n"
            f"Original Pace: {user_input.pace}\n"
            f"Feedback: {feedback}\n"
        )
        
        analysis = self.call_openrouter(system_prompt, user_prompt, json_response=True)
        updated_input = user_input.copy()
        directives = {}

        if analysis:
            if "budget_modifier" in analysis and analysis["budget_modifier"] != 1.0:
                updated_input.budget = updated_input.budget * analysis["budget_modifier"]
            if "pace_override" in analysis and analysis["pace_override"]:
                updated_input.pace = analysis["pace_override"]
            
            directives["rerun"] = analysis.get("rerun_agents", ["AttractionsAgent"])
        
        return updated_input, directives
