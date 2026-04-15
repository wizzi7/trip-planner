from backend.agents.base import BaseAgent
import os

class BudgetAgent(BaseAgent):
    def __init__(self, llm_provider=None, model_name=None):
        super().__init__(name="BudgetAgent", llm_provider=llm_provider, model_name=model_name)

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Monitoring budget...")
        
        while True:
            await bus.subscribe("cost_updated")
            await bus.clear("cost_updated")
            
            self.logger.info("Validating budget...")
            
            async with world.lock:
                plan_days = [d.model_copy() for d in world.days] if world.days is not None else None
                user_input = world.user_input
                culinary_section = world.culinary_section

            # Wait for plan days to be populated
            if plan_days is None:
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
            
            if os.environ.get("ENABLE_BUDGET", "true").lower() == "false":
                self.logger.info("Budget Agent disabled by ENABLE_BUDGET flag. Skipping calculation.")
                async with world.lock:
                    world.total_cost = 0.0
                    if "alerts" not in world.constraints:
                        world.constraints["alerts"] = []
                await bus.emit("plan_stable")
                return

            plan_summary = []
            for day in plan_days:
                activities_summary = [f"{act.name} ({act.duration})" for act in day.activities]
                plan_summary.append({
                    "day": day.day,
                    "activities": activities_summary
                })

            system_prompt = (
                "You are an expert Trip Budget Planner. "
                "Your task is to estimate the TOTAL cost for each day of the trip. "
                "You MUST include ALL of the following cost categories in your estimate for EACH day:\n"
                "  1. FOOD & DINING — breakfast, lunch, dinner, and drinks/snacks based on the culinary venue price ranges provided below.\n"
                "  2. ACTIVITIES & ATTRACTIONS — entrance fees, tours, tickets based on the itinerary.\n"
                "  3. LOCAL TRANSPORT — getting around the city based on the mobility info provided.\n"
                "The daily cost should be the SUM of all three categories above, multiplied by the number of guests.\n"
                "You must also provide a total estimated cost and a list of budget alerts if the total exceeds the user's budget. "
                "Return the response in this JSON format:\n"
                "{\n"
                "  \"daily_costs\": { \"1\": \"string cost\", \"2\": \"string cost\", ... },\n"
                "  \"total_estimated_cost\": number,\n"
                "  \"alerts\": [\"string alert 1\", \"string alert 2\"]\n"
                "}\n"
                "CRITICAL: 'total_estimated_cost' MUST be a raw number (integer or float) WITHOUT any currency symbols or text (e.g., 540, not '540 PLN'). "
                "Daily costs should be formatted strings with currency. Alerts must be in English. "
                "Example alert: 'Warning: Total cost exceeds budget by 20%'.\n"
                "CRITICAL: Do NOT underestimate food costs. Use the actual venue price ranges provided to calculate realistic meal expenses."
            )

            mobility_info = "Transport Info: N/A"
            if mobility_section:
                mobility_info = (
                    f"Public Transport: {mobility_section.public_transport.price_level if mobility_section.public_transport else 'N/A'}. "
                    f"Typical Taxi: {mobility_section.taxis.typical_pricing_level if mobility_section.taxis else 'N/A'}. "
                    f"Cheapest Option: {mobility_section.quick_recommendations.cheapest if mobility_section.quick_recommendations else 'N/A'}"
                )

            food_cost_info = "Food Cost Info: N/A"
            if culinary_section:
                price_samples = []
                for label, venues in [
                    ("Traditional restaurants", culinary_section.venues_traditional),
                    ("Cafes", culinary_section.venues_cafes),
                    ("Bars", culinary_section.venues_bars),
                ]:
                    if venues:
                        ranges = [v.price_range for v in venues if v.price_range and v.price_range != "N/A"]
                        if ranges:
                            price_samples.append(f"  {label}: {', '.join(ranges[:4])}")
                for label, dishes in [
                    ("Main dishes", culinary_section.main_dishes),
                    ("Soups", culinary_section.soups),
                    ("Desserts", culinary_section.desserts),
                    ("Drinks", culinary_section.drinks),
                ]:
                    if dishes:
                        ranges = [d.price_range for d in dishes if d.price_range and d.price_range != "N/A"]
                        if ranges:
                            price_samples.append(f"  {label}: {', '.join(ranges[:4])}")

                if price_samples:
                    food_cost_info = (
                        "Food & Dining Price Ranges (per person per meal):\n"
                        + "\n".join(price_samples)
                        + "\nAssume each guest eats 3 meals per day (breakfast, lunch, dinner) plus drinks/snacks. "
                        "Use the ACTUAL price ranges above to estimate daily food costs — do NOT guess low."
                    )

            user_prompt = (
                 f"Destination: {user_input.destination}\n"
                 f"Guests: {user_input.guests}\n"
                 f"User Budget: {user_input.budget} per person (Total: {user_input.budget * user_input.guests})\n"
                 f"Mobility Costs Context: {mobility_info}\n"
                 f"{food_cost_info}\n"
                 f"Itinerary: {plan_summary}\n"
                 "Estimate costs now. Remember to include food, activities, and transport for each day."
            )

            response_data, usage = self.call_llm(system_prompt, user_prompt, json_response=True)
            
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
