from backend.models import UserInput, TripPlan
from backend.agents.base import BaseAgent

class BudgetAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="BudgetAgent")

    async def run(self, user_input: UserInput, plan: TripPlan) -> TripPlan:
        print(f"[{self.name}] validating budget...")

        plan_summary = []
        for day in plan.days:
            plan_summary.append({
                "day": day.day,
                "activities": day.activities
            })

        system_prompt = (
            "You are an expert Trip Budget Planner. "
            "Your task is to estimate the cost for each day of the trip based on the destination, number of guests, and activities. "
            "You must also provide a total estimated cost and a list of budget alerts if the total exceeds user's budget. "
            "Return the response in this JSON format:\n"
            "{\n"
            "  \"daily_costs\": { \"1\": \"string cost\", \"2\": \"string cost\", ... },\n"
            "  \"total_estimated_cost\": number,\n"
            "  \"alerts\": [\"string alert 1\", \"string alert 2\"]\n"
            "}\n"
            "Values should be in PLN or local currency appropriate for destination. Alerts must be in English. "
            "Example alert: 'Warning: Total cost exceeds budget by 20%'."
        )
        
        user_prompt = (
             f"Destination: {user_input.destination}\n"
             f"Guests: {user_input.guests}\n"
             f"User Budget: {user_input.budget} per person (Total: {user_input.budget * user_input.guests})\n"
             f"Itinerary: {plan_summary}\n"
             "Estimate costs now."
        )

        response_data = self.call_openrouter(system_prompt, user_prompt, json_response=True)
        
        if response_data:
            try:
                daily_costs = response_data.get("daily_costs", {})
                total_est = response_data.get("total_estimated_cost", 0)
                alerts = response_data.get("alerts", [])

                for day in plan.days:
                    day_str = str(day.day)
                    if day_str in daily_costs:
                        day.estimated_cost = str(daily_costs[day_str])
                    else:
                        day.estimated_cost = "Unknown"
                
                plan.total_cost = float(total_est)
                if "alerts" not in plan.metadata:
                    plan.metadata["alerts"] = []
                plan.metadata["alerts"].extend(alerts)
                
                return plan
            except Exception as e:
                print(f"[{self.name}] Error parsing response: {e}")

        return plan
