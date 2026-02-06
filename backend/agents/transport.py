from backend.agents.base import BaseAgent
from backend.models import MobilitySection

class TransportationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TransportationAgent")

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Waiting for itinerary...")
        await bus.subscribe("days_planned")

        async with world.lock:
             user_input = world.user_input

        self.logger.info("Generating City Mobility Guide...")

        system_prompt = (
            "You are an expert City Mobility Guide. "
            "Your goal is to provide a comprehensive, practical transportation guide for the trip destination. "
            "This guide is NOT tied to specific days. "
            "It must cover: Public Transport, Ride-Hailing, Walking, Bikes/Scooters, and optionally Ferries and Car Rental. "
            "Include specific details like ticket prices, app names, and qualitative cost levels (Cheap, Moderate, Expensive). "
            "For 'public_transport', include a valid 'website_url' to the official transport authority or ticket info page. "
            "For 'ticket_types', list common options (e.g., 'Single ticket', '24h pass'). "
            "For 'approximate_prices', give concrete examples in LOCAL CURRENCY. "
            "For 'ride_hailing', ALWAYS include Bolt, Uber, Free Now, and Local Taxis if available. "
            "Structure the response as a JSON object matching the following structure: "
            "{ "
            "  \"public_transport\": { \"available_options\": [\"Metro\", \"Bus\"], \"ticket_types\": \"...\", \"approximate_prices\": \"...\", \"coverage_quality\": \"...\", \"useful_apps\": [\"...\"], \"best_use_cases\": \"...\", \"price_level\": \"💸 Cheap\", \"website_url\": \"https://...\" }, "
            "  \"taxis\": { \"available_apps\": [\"Uber\", \"Bolt\"], \"typical_pricing_level\": \"💸💸 Moderate\", \"safety_notes\": \"...\", \"when_to_use\": \"...\" }, "
            "  \"walking\": { \"is_walkable\": true, \"best_areas\": \"...\" }, "
            "  \"bikes\": { \"available\": true, \"providers\": [\"Lime\", \"Tier\"], \"price_range\": \"...\", \"convenience\": \"...\", \"cautions\": \"...\" }, "
            "  \"ferries\": { \"is_relevant\": false, \"routes\": \"...\", \"cost_level\": \"...\", \"tourist_vs_commuter\": \"...\" }, "
            "  \"car_rental\": { \"recommended\": false, \"parking_difficulty\": \"...\", \"notes\": \"...\" }, "
            "  \"quick_recommendations\": { \"best_overall\": \"...\", \"cheapest\": \"...\", \"most_convenient\": \"...\", \"avoid\": \"...\" } "
            "}"
        )
        
        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Budget Per Person: {user_input.budget}\n"
            "Please provide the City Mobility Guide."
        )

        response_data, usage = self.call_openrouter(system_prompt, user_prompt, json_response=True, max_tokens=2000)
        
        async with world.lock:
             world.token_usage[self.name] = usage
        
        if response_data:
            self.logger.info(f"Raw Mobility Response: {response_data}")
            try:
                mobility_section = MobilitySection(**response_data)
                async with world.lock:
                    world.mobility_section = mobility_section
                self.logger.info("Mobility section generated successfully.")
            except Exception as e:
                self.logger.error(f"Failed to parse mobility section: {e}")
                self.logger.error(f"Problematic data: {response_data}")
        else:
             self.logger.warning("Failed to generate mobility section.")
            
        await bus.emit("cost_updated")
