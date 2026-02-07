from typing import List
from backend.models import TripDay
from backend.agents.base import BaseAgent
from datetime import datetime, timedelta

class AttractionsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AttractionsAgent")

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Waiting for constraints...")
        await bus.subscribe("constraints_ready")
        
        async with world.lock:
            user_input = world.user_input
            constraints = world.constraints
        
        self.logger.info(f"Generating itinerary for {user_input.destination} with constraints {constraints}")

        system_prompt = (
            "You are an expert Travel Agent specializing in creating personalized daily itineraries. "
            "Your goal is to suggest a full day of activities (STRICTLY minimum 10 items) for each day based on the user's destination, budget, and interests. "
            "You MUST distribute the attractions logically: "
            "1. Maintain historical and thematic coherence where possible. "
            "2. Minimize distances between attractions within the same day (group them geographically). "
            "3. Arrange attractions in a realistic order (morning to evening). "
            "If you run out of major attractions, include smaller sights, parks, monuments, viewpoints, or walking routes to reach the count of 10. "
            "Focus strictly on sightseeing and attractions, NOT food/restaurants (another agent handles that). "
            "For 'duration': use minutes for times under 1 hour (e.g. '20 min', '45 min'). Use hours for 1 hour or more (e.g. '1h', '1.5h'). "
            "You MUST return the valid JSON array of objects, where each object represents a day. "
            "The JSON schema for each day is: "
            "{\n"
            "  \"day\": integer,\n"
            "  \"date\": \"YYYY-MM-DD\",\n"
            "  \"theme\": \"string (short theme of the day)\",\n"
            "  \"summary\": \"string (short summary of the day)\",\n"
            "  \"activities\": [\n"
            "    {\"name\": \"Attraction Name\", \"description\": \"One sentence on why it's important.\", \"duration\": \"string (e.g. '1.5h' or '45 min')\"},\n"
            "    ...\n"
            "  ],\n"
            "  \"estimated_cost\": \"string (estimated cost range)\"\n"
            "}\n"
            "Do NOT include any markdown formatting (like ```json), just the raw JSON string."
        )

        try:
            start_date = datetime.strptime(user_input.arrival.split(' ')[0], "%Y-%m-%d")
            end_date = datetime.strptime(user_input.departure.split(' ')[0], "%Y-%m-%d")
            num_days = (end_date - start_date).days + 1
        except Exception as e:
            self.logger.error(f"Date parsing error: {e}. Defaulting to 3 days.")
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

        parsed_days, usage = self.call_gemini(system_prompt, user_prompt, json_response=True)
        
        async with world.lock:
             world.token_usage[self.name] = usage
        
        trip_days = []
        if parsed_days:
            try:
                for d in parsed_days:
                    trip_days.append(TripDay(**d))
            except Exception as e:
                 self.logger.error(f"Parsing Error: {e}")
                 trip_days = self._fallback_response()
        else:
            trip_days = self._fallback_response()
            
        async with world.lock:
            world.days = trip_days
            
        await bus.emit("days_planned")

    def _fallback_response(self) -> List[TripDay]:
        self.logger.warning("Using fallback response.")
        return []
