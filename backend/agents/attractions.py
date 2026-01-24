from typing import Dict, Any, List
from backend.models import UserInput, TripDay
from backend.agents.base import BaseAgent
from datetime import datetime, timedelta

class AttractionsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AttractionsAgent")

    async def run(self, user_input: UserInput, constraints: Dict[str, Any]) -> List[TripDay]:
        print(f"[{self.name}] Generating itinerary for {user_input.destination} with constraints {constraints}")

        system_prompt = (
            "You are an expert Travel Agent specializing in creating personalized daily itineraries. "
            "Your goal is to suggest minimal but high-quality attractions for each day based on the user's destination, budget, and interests. "
            "You MUST return the valid JSON array of objects, where each object represents a day. "
            "The JSON schema for each day is: "
            "{\n"
            "  \"day\": integer,\n"
            "  \"date\": \"YYYY-MM-DD\",\n"
            "  \"theme\": \"string (short theme of the day)\",\n"
            "  \"summary\": \"string (short summary of the day)\",\n"
            "  \"activities\": [\"string (activity 1)\", \"string (activity 2)\", ...],\n"
            "  \"estimated_cost\": \"string (estimated cost range)\"\n"
            "}\n"
            "Do NOT include any markdown formatting (like ```json), just the raw JSON string."
        )

        try:
            start_date = datetime.strptime(user_input.arrival.split(' ')[0], "%Y-%m-%d")
            end_date = datetime.strptime(user_input.departure.split(' ')[0], "%Y-%m-%d")
            num_days = (end_date - start_date).days + 1
        except Exception as e:
            print(f"[{self.name}] Date parsing error: {e}. Defaulting to 3 days.")
            num_days = 3
            start_date = datetime.now()

        dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
        
        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Trip Dates: {dates[0]} to {dates[-1]} ({num_days} days)\n"
            f"Budget: {user_input.budget}\n"
            f"Interests/Constraints: {constraints}\n"
            f"Please generate a {num_days}-day itinerary. Return ONLY the JSON array."
        )

        parsed_days = self.call_openrouter(system_prompt, user_prompt, json_response=True)
        
        if parsed_days:
            try:
                trip_days = []
                for d in parsed_days:
                    trip_days.append(TripDay(**d))
                return trip_days
            except Exception as e:
                 print(f"[{self.name}] Parsing Error: {e}")

        return self._fallback_response()

    def _fallback_response(self) -> List[TripDay]:
        print(f"[{self.name}] Using fallback response.")
        return []
