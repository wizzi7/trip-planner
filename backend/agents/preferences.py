from backend.agents.base import BaseAgent

class PreferencesAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PreferencesAgent")

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info(f"Extracting constraints for {world.user_input.destination}")
        
        system_prompt = (
            "You are an expert Travel Analyst. Extract key constraints from user input. "
            "Return JSON: { \"interest_tags\": [], \"dietary_restrictions\": [], \"accessibility\": \"string\" }"
        )
        
        user_prompt = (
            f"Destination: {world.user_input.destination}\n"
            f"Extra Req: {world.user_input.extra_req}\n"
            f"Interests: {world.user_input.interests}\n"
            f"Pace: {world.user_input.pace}\n"
            f"Guests: {world.user_input.guests}\n"
        )

        constraints, usage = self.call_gemini(system_prompt, user_prompt, json_response=True)
        
        async with world.lock:
             world.token_usage[self.name] = usage
        
        if not constraints:
            constraints = {"interest_tags": [], "dietary_restrictions": []}
            
        self.logger.info(f"Extracted: {constraints}")
        
        async with world.lock:
            world.constraints = constraints
            
        await bus.emit("constraints_ready")
