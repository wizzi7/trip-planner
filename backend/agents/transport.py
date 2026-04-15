from backend.agents.base import BaseAgent
from backend.models import MobilitySection
import os

class TransportationAgent(BaseAgent):
    def __init__(self, llm_provider=None, model_name=None):
        super().__init__(name="TransportationAgent", llm_provider=llm_provider, model_name=model_name)

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Waiting for itinerary...")
        await bus.subscribe("days_planned")

        if os.environ.get("ENABLE_TRANSPORT", "true").lower() == "false":
            self.logger.info("Transportation Agent disabled by ENABLE_TRANSPORT flag.")
            async with world.lock:
                world.mobility_section = MobilitySection()
            await bus.emit("cost_updated")
            return

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
            "Structure the response as a JSON object matching the following structure EXACTLY. "
            "IMPORTANT: "
            "1. 'ticket_types', 'approximate_prices', 'price_range', 'usage_guide', 'routes', 'cost_level', 'tourist_vs_commuter', 'parking_difficulty', 'notes' MUST be single STRINGS (summaries), NOT lists or objects. "
            "2. 'available_options', 'useful_apps', 'available_apps', 'best_areas', 'providers', 'cautions', 'avoid' MUST be LISTS of STRINGS. "
            "3. Do NOT invent new fields. "
            
            "{ "
            "  \"public_transport\": { \"available_options\": [\"Metro\", \"Bus\"], \"ticket_types\": \"e.g. Single ticket (€2), 24h pass (€8)...\", \"approximate_prices\": \"e.g. €2-10 depends on zones\", \"coverage_quality\": \"...\", \"useful_apps\": [\"Citymapper\", \"Google Maps\"], \"best_use_cases\": \"...\", \"price_level\": \"💸 Cheap\", \"website_url\": \"https://...\" }, "
            "  \"taxis\": { \"available_apps\": [\"Uber\", \"Bolt\"], \"typical_pricing_level\": \"💸💸 Moderate\", \"safety_notes\": \"...\", \"when_to_use\": \"...\" }, "
            "  \"walking\": { \"is_walkable\": true, \"best_areas\": [\"Old Town\", \"River Bank\"] }, "
            "  \"bikes\": { \"available\": true, \"providers\": [\"Lime\", \"Tier\"], \"price_range\": \"e.g. €1 unlock + €0.20/min\", \"convenience\": \"...\", \"cautions\": [\"Wear helmet\", \"Ride on road\"] }, "
            "  \"ferries\": { \"is_relevant\": false, \"routes\": \"e.g. Line A to B...\", \"cost_level\": \"...\", \"tourist_vs_commuter\": \"...\" }, "
            "  \"car_rental\": { \"recommended\": false, \"parking_difficulty\": \"...\", \"notes\": \"...\" }, "
            "  \"quick_recommendations\": { \"best_overall\": \"...\", \"cheapest\": \"...\", \"most_convenient\": \"...\", \"avoid\": [\"Rush hour\", \"Unlicensed taxis\"] } "
            "}"
        )
        
        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Total Trip Budget: {user_input.budget * user_input.guests} (for {user_input.guests} guests, {user_input.budget} per person). CRITICAL: Highlight economical transport options to ensure the trip stays within this strict budget!\n"
            "Please provide the City Mobility Guide."
        )

        response_data, usage = self.call_llm(system_prompt, user_prompt, json_response=True, max_tokens=4000)
        
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
             async with world.lock:
                 world.mobility_section = MobilitySection(
                     public_transport=None,
                     taxis=None,
                     walking=None,
                     bikes=None,
                     ferries=None,
                     car_rental=None,
                     quick_recommendations=None
                 )
            
        await bus.emit("cost_updated")
