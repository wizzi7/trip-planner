from backend.models import CityOverview
from backend.agents.base import BaseAgent

class CityOverviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CityOverviewAgent")

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Generating city overview...")
        
        async with world.lock:
            user_input = world.user_input

        system_prompt = (
            "You are a sophisticated Travel Destination Analyser. "
            "Your goal is to provide a comprehensive and engaging overview of the destination city. "
            "Focus on what makes the city unique, avoiding generic descriptions. "
            "Provide detailed, well-written paragraphs for the history and culture sections (approx 100-150 words each). "
            "Return ONLY a valid JSON object matching the following schema:\n"
            "{\n"
            "  \"city_name\": \"string\",\n"
            "  \"short_description\": \"2-3 sentences summary.\",\n"
            "  \"history_summary\": \"A detailed paragraph explaining the city's past and how it shaped the present.\",\n"
            "  \"cultural_identity\": \"A detailed paragraph describing the local culture, vibe, and what it feels like to be there.\"\n"
            "}\n"
            "Do NOT include markdown formatting."
        )

        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Please generate the City Overview now."
        )

        response_data, usage = self.call_gemini(system_prompt, user_prompt, json_response=True)
        
        async with world.lock:
            world.token_usage[self.name] = usage
            
        if response_data:
            try:
                overview = CityOverview(**response_data)
                async with world.lock:
                    world.city_overview = overview
                self.logger.info("City Overview generated successfully.")
            except Exception as e:
                self.logger.error(f"Failed to parse CityOverview: {e}")
        else:
             self.logger.error("Failed to generate City Overview.")
