from typing import List
from backend.models import UserInput, TripDay
from backend.agents.base import BaseAgent

class TransportationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TransportationAgent")

    async def run(self, user_input: UserInput, plan_days: List[TripDay]) -> List[TripDay]:
        print(f"[{self.name}] Optimizing transport...")

        plan_summary = []
        for day in plan_days:
            plan_summary.append({
                "day": day.day,
                "activities": day.activities
            })

        system_prompt = (
            "You are an expert Transport Planner. "
            "Analyze the itinerary activities and suggest the best mode of transport for each day. "
            "Consider the user's preferred transport mode. "
            "Return a JSON object: { \"daily_transport\": { \"1\": \"string recommendation in English\", \"2\": \"...\" } }"
        )
        
        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Preferred Transport: {user_input.transport}\n"
            f"Itinerary: {plan_summary}\n"
        )

        response_data = self.call_openrouter(system_prompt, user_prompt, json_response=True)
        
        if response_data:
            transport_map = response_data.get("daily_transport", {})
            for day in plan_days:
                rec = transport_map.get(str(day.day), "Standard Transport")
                day.summary += f" [Transport: {rec}]"
        
        return plan_days
