from backend.agents.base import BaseAgent

class BudgetAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="BudgetAgent")

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Monitoring budget...")
        
        while True:
            await bus.subscribe("cost_updated")
            await bus.clear("cost_updated")
            
            self.logger.info("Validating budget...")
            
            async with world.lock:
                plan_days = [d.model_copy() for d in world.days]
                user_input = world.user_input
                culinary_section = world.culinary_section

            # Wait for plan days to be populated
            if not plan_days:
                 self.logger.info("No days yet, waiting...")
                 continue

            # Wait for Transport Agent (Mobility Guide)
            mobility_section = world.mobility_section
            if mobility_section is None:
                 self.logger.info("Waiting for mobility guide...")
                 continue

            # Wait for Gastronomy Agent
            if culinary_section is None:
                 self.logger.info("Waiting for culinary agent...")
                 continue

            plan_summary = []
            for day in plan_days:
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
                "CRITICAL: 'total_estimated_cost' MUST be a raw number (integer or float) WITHOUT any currency symbols or text (e.g., 540, not '540 PLN'). "
                "Daily costs should be formatted strings with currency. Alerts must be in English. "
                "Example alert: 'Warning: Total cost exceeds budget by 20%'."
            )
            
            mobility_info = "Transport Info: N/A"
            if mobility_section:
                mobility_info = (
                    f"Public Transport: {mobility_section.public_transport.price_level if mobility_section.public_transport else 'N/A'}. "
                    f"Typical Taxi: {mobility_section.taxis.typical_pricing_level if mobility_section.taxis else 'N/A'}. "
                    f"Cheapest Option: {mobility_section.quick_recommendations.cheapest if mobility_section.quick_recommendations else 'N/A'}"
                )

            user_prompt = (
                 f"Destination: {user_input.destination}\n"
                 f"Guests: {user_input.guests}\n"
                 f"User Budget: {user_input.budget} per person (Total: {user_input.budget * user_input.guests})\n"
                 f"Mobility Costs Context: {mobility_info}\n"
                 f"Itinerary: {plan_summary}\n"
                 "Estimate costs now."
            )

            response_data, usage = self.call_gemini(system_prompt, user_prompt, json_response=True)
            
            async with world.lock:
                 world.token_usage[self.name] = usage
            
            async with world.lock:
                 if response_data:
                    try:
                        daily_costs = response_data.get("daily_costs", {})
                        total_est = response_data.get("total_estimated_cost", 0)
                        alerts = response_data.get("alerts", [])

                        for day in world.days:
                            day_str = str(day.day)
                            if day_str in daily_costs:
                                day.estimated_cost = str(daily_costs[day_str])
                        
                        world.total_cost = float(total_est)
                        if "alerts" not in world.constraints:
                             world.constraints["alerts"] = []
                        world.constraints["alerts"] = alerts

                        self.logger.info(f"Cost updated: {world.total_cost}. Alerts: {alerts}")
                        await bus.emit("plan_stable")
                        return

                    except Exception as e:
                        self.logger.error(f"Error parsing response: {e}")

            await bus.emit("plan_stable")
            return
