from typing import List
from backend.models import UserInput, TripDay
from backend.agents.base import BaseAgent

class GastronomyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="GastronomyAgent")

    async def run(self, user_input: UserInput, plan_days: List[TripDay]) -> List[TripDay]:
        print(f"[{self.name}] Finding culinary experiences...")

        plan_context = []
        for day in plan_days:
            plan_context.append({
                "day": day.day,
                "activities": day.activities
            })

        system_prompt = (
            "You are an expert Culinary Guide and Food Critic. "
            "Your goal is to suggest specific dining venues for each day of the trip, complementing the daily itinerary. "
            "You MUST suggest a specific venue or dish type for: Breakfast, Lunch, Dinner, and a Snack/Coffee break. "
            "Return a JSON object where keys are day numbers (as strings) and values are objects containing 'breakfast', 'lunch', 'dinner', 'snack'. "
            "Example JSON structure: "
            "{ \"1\": { \"breakfast\": \"Cafe name/desc\", \"lunch\": \"...\", \"dinner\": \"...\", \"snack\": \"...\" }, \"2\": ... }"
        )

        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Budget: {user_input.budget}\n"
            f"Dietary/Extra Requirements: {user_input.extra_req}\n"
            f"Itinerary Context: {plan_context}\n"
            "Please provide gastronomy recommendations for each day."
        )

        response_data = self.call_openrouter(system_prompt, user_prompt, json_response=True)

        if response_data:
            for day in plan_days:
                day_meals = response_data.get(str(day.day), {})
                day.meals = {
                    "breakfast": day_meals.get("breakfast", "Local Breakfast Spot"),
                    "lunch": day_meals.get("lunch", "Local Lunch Spot"),
                    "dinner": day_meals.get("dinner", "Local Dinner Spot"),
                    "snack": day_meals.get("snack", "Local Snack/Cafe")
                }
        else:
             print(f"[{self.name}] Failed to generate meals, using defaults.")
             for day in plan_days:
                day.meals = {
                    "breakfast": "Hotel Breakfast or Local Cafe",
                    "lunch": "City Center Restaurant",
                    "dinner": "Traditional Local Restaurant",
                    "snack": "Street Food or Cafe"
                }

        return plan_days
